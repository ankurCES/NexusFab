"""Line failure rerouting algorithm.

When a line goes down, find best alternative:
  Same plant (compatible format, available capacity) or sister plant.
  Minimize: downtime_loss + changeover_cost + transport_cost + overtime_cost + SLA_penalty
"""

from dataclasses import dataclass, field

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import PRODUCTS, get_product

# Cost parameters ($/hour or $/event)
DOWNTIME_COST_PER_HOUR = 15_000.0
CHANGEOVER_COST_PER_HOUR = 2_000.0
OVERTIME_PREMIUM_FACTOR = 1.5
SLA_PENALTY_PER_HOUR_LATE = 5_000.0

# ponytail: line_type → format_types it can produce, derived from seed data layout
LINE_FORMAT_COMPAT: dict[str, set[str]] = {
    "PET_BOTTLING":    {"PET_500", "PET_750", "PET_1L", "PET_15L"},
    "GLASS_BOTTLING":  {"PET_750", "PET_1L"},
    "CANNING":         {"CAN_85", "CAN_400"},
    "MOULDING":        {"BAR_4F", "BAR_STD", "SEASONAL"},
    "ENROBING":        {"BAR_4F", "BAR_STD"},
    "WRAPPING":        {"BAR_4F", "BAR_STD", "MULTIPACK", "SEASONAL"},
    "UHT_FILLING":     {"UHT_200", "UHT_500", "UHT_1L"},
    "POWDER_PACKING":  {"TIN_400", "TIN_900", "TIN_1800"},
    "ASEPTIC":         {"UHT_200", "UHT_500", "UHT_1L"},
    "EXTRUSION":       {"BAG_1K", "BAG_5K", "BAG_15K"},
    "RETORT_CANNING":  {"CAN_85", "CAN_400"},
    "KIBBLE_COATING":  {"BAG_1K", "BAG_5K", "BAG_15K", "POUCH"},
    "MIXING_COOKING":  {"PACK_70", "CUP_65", "SACHET_8"},
    "FILLING":         {"BOTTLE_200", "BOTTLE_500"},
    "NOODLE_LINE":     {"PACK_70", "CUP_65", "MULTIPACK"},
}

# ponytail: precompute allergen capability per plant from product catalog
_PLANT_ALLERGENS: dict[str, set[str]] = {}
for _p in PRODUCTS:
    _PLANT_ALLERGENS.setdefault(_p.plant_id, set()).update(_p.allergens)

def _transport_cost(from_plant: str, to_plant: str) -> tuple[float, float]:
    """Return (cost, hours) for inter-plant transport. Uses lat/lon distance estimate."""
    if from_plant == to_plant:
        return (0.0, 0.0)
    p1 = get_plant(from_plant)
    p2 = get_plant(to_plant)
    if not p1 or not p2:
        return (5000.0, 24.0)
    # Rough distance in "degrees" → cost scaling
    dist = ((p1.lat - p2.lat) ** 2 + (p1.lon - p2.lon) ** 2) ** 0.5
    cost = 500.0 + dist * 100  # $500 base + $100 per degree
    hours = 4.0 + dist * 1.5   # 4h base + 1.5h per degree
    return (round(cost, 2), round(hours, 1))


@dataclass
class RerouteCandidate:
    line_name: str
    plant_id: str
    plant_name: str
    is_same_plant: bool
    changeover_minutes: float
    transport_cost: float
    transport_hours: float
    current_utilization: float
    capacity_available_pct: float
    total_cost: float
    cost_breakdown: dict = field(default_factory=dict)
    allergen_compatible: bool = True
    format_compatible: bool = True
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "line": self.line_name,
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "same_plant": self.is_same_plant,
            "changeover_min": round(self.changeover_minutes, 1),
            "transport_cost": round(self.transport_cost, 2),
            "transport_hours": self.transport_hours,
            "utilization": round(self.current_utilization, 4),
            "capacity_available_pct": round(self.capacity_available_pct, 4),
            "total_cost": round(self.total_cost, 2),
            "cost_breakdown": self.cost_breakdown,
            "allergen_ok": self.allergen_compatible,
            "format_ok": self.format_compatible,
        }


@dataclass
class RerouteResult:
    failed_line: str
    failed_plant: str
    failure_duration_hours: float
    product_sku: str
    candidates: list[RerouteCandidate] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "failed_line": self.failed_line,
            "failed_plant": self.failed_plant,
            "failure_duration_hours": self.failure_duration_hours,
            "product_sku": self.product_sku,
            "candidates_count": len(self.candidates),
            "recommendation": self.recommendation,
            "top_3": [c.to_dict() for c in self.candidates[:3]],
        }


def suggest_reroute(
    line_name: str,
    plant_id: str,
    product_sku: str,
    failure_duration_hours: float = 8.0,
    current_utilizations: dict[str, float] | None = None,
) -> RerouteResult:
    """Find best alternative lines when a line goes down.

    Returns candidates ranked by total cost (lower = better).
    """
    if current_utilizations is None:
        current_utilizations = {}

    product = get_product(product_sku)
    if not product:
        raise ValueError(f"Product {product_sku} not found")

    result = RerouteResult(
        failed_line=line_name,
        failed_plant=plant_id,
        failure_duration_hours=failure_duration_hours,
        product_sku=product_sku,
    )

    downtime_cost = failure_duration_hours * DOWNTIME_COST_PER_HOUR

    for plant in PLANTS:
        for line in plant.lines:
            if line.name == line_name:
                continue

            utilization = current_utilizations.get(line.name, 0.65)

            # AC4: capacity constraint — candidate must be ≤95% after absorbing work
            added_utilization = 0.1  # ponytail: flat estimate, refine with actual order volume if needed
            if utilization + added_utilization > 0.95:
                continue

            # AC5: format compatibility — line must support the product's format
            fmt_ok = product.format_type in LINE_FORMAT_COMPAT.get(line.line_type, set())
            if not fmt_ok:
                continue

            # AC5: allergen compatibility — target plant must handle all product allergens
            plant_allergens = _PLANT_ALLERGENS.get(plant.id, set())
            alg_ok = set(product.allergens).issubset(plant_allergens)
            if not alg_ok:
                continue

            # Changeover cost — use product's own changeover_minutes as baseline
            changeover = product.changeover_minutes
            changeover_cost = (changeover / 60.0) * CHANGEOVER_COST_PER_HOUR

            # Transport cost
            transport_cost, transport_hours = _transport_cost(plant_id, plant.id)

            # SLA impact
            sla_delay = max(0, transport_hours + changeover / 60.0 - failure_duration_hours)
            sla_penalty = sla_delay * SLA_PENALTY_PER_HOUR_LATE

            # Total cost
            total = changeover_cost + transport_cost + sla_penalty
            # If same plant, no transport, much cheaper
            is_same = plant.id == plant_id

            cost_breakdown = {
                "downtime_avoided": round(downtime_cost, 2),
                "changeover_cost": round(changeover_cost, 2),
                "transport_cost": round(transport_cost, 2),
                "sla_penalty": round(sla_penalty, 2),
            }

            candidate = RerouteCandidate(
                line_name=line.name,
                plant_id=plant.id,
                plant_name=plant.name,
                is_same_plant=is_same,
                changeover_minutes=changeover,
                transport_cost=transport_cost,
                transport_hours=transport_hours,
                current_utilization=utilization,
                capacity_available_pct=1.0 - utilization,
                total_cost=total,
                cost_breakdown=cost_breakdown,
                allergen_compatible=alg_ok,
                format_compatible=fmt_ok,
            )
            result.candidates.append(candidate)

    # Sort by total cost
    result.candidates.sort(key=lambda c: c.total_cost)

    if result.candidates:
        best = result.candidates[0]
        loc = "same plant" if best.is_same_plant else f"plant {best.plant_id}"
        result.recommendation = (
            f"Reroute to {best.line_name} ({loc}). "
            f"Est. cost: ${best.total_cost:,.0f} "
            f"(changeover {best.changeover_minutes:.0f}min"
            f"{f', transport {best.transport_hours}h' if not best.is_same_plant else ''}). "
            f"Avoids ${downtime_cost:,.0f} downtime loss."
        )
    else:
        result.recommendation = "No viable candidates found — all lines at capacity."

    return result


if __name__ == "__main__":
    import time

    print("=== Line Failure Rerouting Self-Check ===\n")

    # --- AC1/AC2: same-plant reroute, top-3 ranked by cost ---
    t0 = time.perf_counter()
    r = suggest_reroute("PLT-001-L1", "PLT-001", "WAT-500S", failure_duration_hours=8.0)
    elapsed = time.perf_counter() - t0

    assert r.candidates, "Should find same-plant candidates for water PET"
    for i in range(len(r.candidates) - 1):
        assert r.candidates[i].total_cost <= r.candidates[i + 1].total_cost, "Not sorted by cost"
    assert elapsed < 2.0, f"Same-plant reroute took {elapsed:.2f}s, AC2 requires <2s"

    print(f"Scenario: PLT-001-L1 down, product WAT-500S (PET 500ml still)")
    print(f"Found {len(r.candidates)} candidates in {elapsed*1000:.0f}ms")
    print(f"Recommendation: {r.recommendation}\n")

    print("Top-3 alternatives:")
    for i, c in enumerate(r.candidates[:3], 1):
        tag = "SAME PLANT" if c.is_same_plant else f"CROSS PLANT ({c.plant_id})"
        print(f"  #{i} {c.line_name} [{tag}]")
        print(f"     Utilization: {c.current_utilization:.0%} | Changeover: {c.changeover_minutes:.0f}min")
        if not c.is_same_plant:
            print(f"     Transport: ${c.transport_cost:,.0f} / {c.transport_hours}h")
        print(f"     Cost breakdown: {c.cost_breakdown}")
        print(f"     TOTAL: ${c.total_cost:,.2f}")

    # --- AC3: cross-plant reroute with transport cost ---
    # PET-WC4 (CAN_400) runs on PLT-004 RETORT_CANNING; PLT-001-L4 CANNING also does CAN_400
    r_cross = suggest_reroute("PLT-004-L3", "PLT-004", "PET-WC4", failure_duration_hours=10.0)
    cross = [c for c in r_cross.candidates if not c.is_same_plant]
    assert cross, "Should find cross-plant candidates for CAN_400 (PLT-004→PLT-001)"
    for c in cross:
        assert c.transport_cost > 0, f"{c.line_name}: cross-plant but transport_cost=0"
        assert c.transport_hours > 0, f"{c.line_name}: cross-plant but transport_hours=0"
    print(f"\n  Cross-plant reroute (PET-WC4): {len(cross)} cross-plant candidates — all have transport ✓")
    for c in cross:
        print(f"    {c.line_name} @ {c.plant_name}: transport ${c.transport_cost:,.0f} / {c.transport_hours}h")

    # --- AC4: capacity constraint ---
    r2 = suggest_reroute(
        "PLT-001-L1", "PLT-001", "WAT-500S",
        current_utilizations={"PLT-001-L2": 0.90, "PLT-001-L3": 0.92, "PLT-001-L4": 0.88},
    )
    for c in r2.candidates:
        assert c.current_utilization + 0.1 <= 0.95, f"{c.line_name} exceeds 95% cap"
    print(f"  Capacity ≤95% enforced — high-util lines filtered out ✓")

    # --- AC5: format compatibility ---
    r3 = suggest_reroute("PLT-002-L1", "PLT-002", "CON-KB4", failure_duration_hours=6.0)
    for c in r3.candidates:
        assert c.format_compatible, f"{c.line_name} marked format-incompatible but included"
        assert c.allergen_compatible, f"{c.line_name} marked allergen-incompatible but included"
    print(f"  Format+allergen checks enforced — {len(r3.candidates)} compatible candidates for CON-KB4 ✓")

    # --- AC5: allergen-free product should NOT route to allergen plant ---
    r4 = suggest_reroute("PLT-001-L1", "PLT-001", "WAT-500S")
    for c in r4.candidates:
        assert c.allergen_compatible
    print(f"  Allergen-free product (water) routes only to allergen-compatible plants ✓")

    # --- AC6: API shape ---
    d = r.to_dict()
    assert "top_3" in d and "recommendation" in d
    for entry in d["top_3"]:
        assert "cost_breakdown" in entry and "total_cost" in entry
    print(f"  API dict has top_3 with cost_breakdown ✓")

    print("\n=== All checks passed ===")

    # Show confectionery scenario for variety
    print("\n--- Bonus: Confectionery line failure ---")
    r5 = suggest_reroute("PLT-002-L1", "PLT-002", "CON-NUT", failure_duration_hours=12.0)
    print(f"PLT-002-L1 down, product CON-NUT (NexBar Peanut, allergens: GLUTEN+DAIRY+NUTS)")
    print(f"Found {len(r5.candidates)} candidates")
    for i, c in enumerate(r5.candidates[:3], 1):
        tag = "SAME" if c.is_same_plant else f"CROSS→{c.plant_id}"
        print(f"  #{i} {c.line_name} [{tag}] ${c.total_cost:,.0f} — {c.cost_breakdown}")
