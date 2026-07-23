"""Line failure rerouting decision engine.

Multi-criteria scoring per docs/research/production-operations.md §3–4.
4-component weighted score replaces greedy cost-only sort.
"""

from dataclasses import dataclass, field
from enum import Enum

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import PRODUCTS, get_product

# ── Cost parameters ($/hour or $/event) ─────────────────────────────────────
DOWNTIME_COST_PER_HOUR = 15_000.0
CHANGEOVER_COST_PER_HOUR = 2_000.0
SLA_PENALTY_PER_HOUR_LATE = 5_000.0

# Scoring weights; urgency="critical" upweights capacity over compatibility
_WEIGHTS_NORMAL   = {"compat": 0.40, "capacity": 0.30, "changeover": 0.20, "quality": 0.10}
_WEIGHTS_CRITICAL = {"compat": 0.30, "capacity": 0.40, "changeover": 0.20, "quality": 0.10}

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

# Intra-plant rerouting compatibility partners (research doc §2.1–2.5)
# Direct partners get max compatibility score; other same-plant lines get partial credit.
LINE_COMPAT_PARTNERS: dict[str, list[str]] = {
    # PLT-001: L1↔L2 (PET sizes), L3 standalone (glass), L4 standalone (cans)
    "PLT-001-L1": ["PLT-001-L2"],  "PLT-001-L2": ["PLT-001-L1"],
    "PLT-001-L3": [],              "PLT-001-L4": [],
    # PLT-002: L1↔L2 (chocolate), L3 standalone (wrapping only)
    "PLT-002-L1": ["PLT-002-L2"],  "PLT-002-L2": ["PLT-002-L1"],
    "PLT-002-L3": [],
    # PLT-003: L1↔L3 (liquid dairy), L2 standalone (powder)
    "PLT-003-L1": ["PLT-003-L3"],  "PLT-003-L3": ["PLT-003-L1"],
    "PLT-003-L2": [],
    # PLT-004: L1↔L2 (kibble), L3↔L4 (wet/coating)
    "PLT-004-L1": ["PLT-004-L2"],  "PLT-004-L2": ["PLT-004-L1"],
    "PLT-004-L3": ["PLT-004-L4"],  "PLT-004-L4": ["PLT-004-L3"],
    # PLT-005: L1↔L2 (sauces), L3 standalone (noodles)
    "PLT-005-L1": ["PLT-005-L2"],  "PLT-005-L2": ["PLT-005-L1"],
    "PLT-005-L3": [],
}

# ponytail: precompute allergen capability per plant from product catalog
_PLANT_ALLERGENS: dict[str, set[str]] = {}
for _p in PRODUCTS:
    _PLANT_ALLERGENS.setdefault(_p.plant_id, set()).update(_p.allergens)


# ── Domain types ─────────────────────────────────────────────────────────────

class RerouteReason(Enum):
    EQUIPMENT_FAILURE   = "equipment_failure"    # unplanned downtime >30 min
    QUALITY_DEVIATION   = "quality_deviation"    # CCP violation, off-spec batch
    DEMAND_SURGE        = "demand_surge"         # >120% of planned volume
    PLANNED_MAINTENANCE = "planned_maintenance"


@dataclass
class ReroutingKPIs:
    """Accumulated KPIs across rerouting events in a simulation run."""
    total_reroutes: int = 0
    total_downtime_events: int = 0
    total_changeover_penalty: float = 0.0
    volume_recovered_units: float = 0.0
    volume_lost_units: float = 0.0

    @property
    def frequency(self) -> int:
        return self.total_reroutes

    @property
    def avg_changeover_penalty(self) -> float:
        return self.total_changeover_penalty / self.total_reroutes if self.total_reroutes else 0.0

    @property
    def volume_recovered_pct(self) -> float:
        total = self.volume_recovered_units + self.volume_lost_units
        return 100.0 * self.volume_recovered_units / total if total else 0.0

    def to_dict(self) -> dict:
        return {
            "total_reroutes": self.total_reroutes,
            "total_downtime_events": self.total_downtime_events,
            "frequency": self.frequency,
            "avg_changeover_penalty": round(self.avg_changeover_penalty, 2),
            "volume_recovered_pct": round(self.volume_recovered_pct, 2),
        }


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
    # multi-criteria score components (0–1 each; higher = better)
    compat_score: float = 0.0
    capacity_score: float = 0.0
    changeover_score: float = 0.0  # populated in second pass (needs max across candidates)
    quality_score: float = 0.0
    composite_score: float = 0.0

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
            "composite_score": round(self.composite_score, 4),
            "score_breakdown": {
                "compat": round(self.compat_score, 3),
                "capacity": round(self.capacity_score, 3),
                "changeover": round(self.changeover_score, 3),
                "quality": round(self.quality_score, 3),
            },
        }


@dataclass
class RerouteResult:
    failed_line: str
    failed_plant: str
    failure_duration_hours: float
    product_sku: str
    reason: RerouteReason = RerouteReason.EQUIPMENT_FAILURE
    candidates: list[RerouteCandidate] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "failed_line": self.failed_line,
            "failed_plant": self.failed_plant,
            "failure_duration_hours": self.failure_duration_hours,
            "product_sku": self.product_sku,
            "reason": self.reason.value,
            "candidates_count": len(self.candidates),
            "recommendation": self.recommendation,
            "top_3": [c.to_dict() for c in self.candidates[:3]],
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _transport_cost(from_plant: str, to_plant: str) -> tuple[float, float]:
    """Return (cost, hours) for inter-plant transport. Uses lat/lon distance estimate."""
    if from_plant == to_plant:
        return (0.0, 0.0)
    p1 = get_plant(from_plant)
    p2 = get_plant(to_plant)
    if not p1 or not p2:
        return (5000.0, 24.0)
    dist = ((p1.lat - p2.lat) ** 2 + (p1.lon - p2.lon) ** 2) ** 0.5
    cost = 500.0 + dist * 100   # $500 base + $100/degree
    hours = 4.0 + dist * 1.5    # 4h base + 1.5h/degree
    return (round(cost, 2), round(hours, 1))


def _compat_score(failed_line: str, candidate_line: str, same_plant: bool) -> float:
    """Compatibility score 0–1: direct partner=1.0, same-plant=0.5, cross-plant=0.2."""
    partners = LINE_COMPAT_PARTNERS.get(failed_line, [])
    if candidate_line in partners:
        return 1.0
    if same_plant:
        return 0.5
    return 0.2


def _quality_risk_rate(failed_line: str, candidate_line: str, same_plant: bool) -> float:
    """Quality risk rate (0–0.10) per research doc §3.3.3.

    Direct compat partner: 0.5% (standard CIP), cross-plant first run: 1.0%.
    Returns as a fraction (0.005, 0.01, etc.).
    """
    if candidate_line in LINE_COMPAT_PARTNERS.get(failed_line, []):
        return 0.005   # standard CIP, established line–SKU pair
    if same_plant:
        return 0.005   # same plant, non-partner: still standard CIP
    return 0.010       # cross-plant first run: 1%


# ── Core decision engine ─────────────────────────────────────────────────────

def score_rerouting_candidates(
    failed_line: str,
    product_sku: str,
    plant_id: str,
    urgency: str = "normal",
    current_utilizations: dict[str, float] | None = None,
) -> list[RerouteCandidate]:
    """Evaluate and rank alternative lines by 4-component weighted score.

    Returns candidates sorted DESC by composite_score (higher = better).
    Applies hard gates first (format, allergen, capacity) then scores.
    """
    if current_utilizations is None:
        current_utilizations = {}

    product = get_product(product_sku)
    if not product:
        raise ValueError(f"Product {product_sku} not found")

    weights = _WEIGHTS_CRITICAL if urgency == "critical" else _WEIGHTS_NORMAL

    candidates: list[RerouteCandidate] = []

    for plant in PLANTS:
        for line in plant.lines:
            if line.name == failed_line:
                continue

            utilization = current_utilizations.get(line.name, 0.65)

            # Hard gate: capacity
            if utilization + 0.10 > 0.95:   # ponytail: 0.10 flat load estimate
                continue

            # Hard gate: format compatibility
            if product.format_type not in LINE_FORMAT_COMPAT.get(line.line_type, set()):
                continue

            # Hard gate: allergen compatibility
            plant_allergens = _PLANT_ALLERGENS.get(plant.id, set())
            if not set(product.allergens).issubset(plant_allergens):
                # Cross-plant: only allow if same category (no cross-category)
                if plant.id != plant_id:
                    continue
                # Same plant with allergen gap: skip
                continue

            is_same = plant.id == plant_id
            changeover = product.changeover_minutes
            changeover_cost = (changeover / 60.0) * CHANGEOVER_COST_PER_HOUR
            transport_cost, transport_hours = _transport_cost(plant_id, plant.id)
            sla_delay = max(0.0, transport_hours + changeover / 60.0)
            sla_penalty = sla_delay * SLA_PENALTY_PER_HOUR_LATE
            total_cost = changeover_cost + transport_cost + sla_penalty

            risk_rate = _quality_risk_rate(failed_line, line.name, is_same)

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
                total_cost=round(total_cost, 2),
                cost_breakdown={
                    "changeover_cost": round(changeover_cost, 2),
                    "transport_cost": round(transport_cost, 2),
                    "sla_penalty": round(sla_penalty, 2),
                },
                allergen_compatible=True,
                format_compatible=True,
                compat_score=_compat_score(failed_line, line.name, is_same),
                capacity_score=1.0 - utilization,
                quality_score=1.0 - min(risk_rate / 0.10, 1.0),
            )
            candidates.append(candidate)

    if not candidates:
        return candidates

    # Second pass: normalize changeover_cost across candidate set → changeover_score
    max_co = max(c.changeover_minutes for c in candidates)
    for c in candidates:
        c.changeover_score = 1.0 - (c.changeover_minutes / max_co if max_co > 0 else 0.0)
        c.composite_score = (
            weights["compat"]     * c.compat_score
            + weights["capacity"] * c.capacity_score
            + weights["changeover"] * c.changeover_score
            + weights["quality"]  * c.quality_score
        )

    # Sort DESC: higher composite_score = better
    candidates.sort(key=lambda c: c.composite_score, reverse=True)

    # Tie-break rule (research §3.4.4): same-plant preferred over cross-plant within ±0.02
    if len(candidates) >= 2:
        top = candidates[0]
        runner = candidates[1]
        if (not top.is_same_plant and runner.is_same_plant
                and abs(top.composite_score - runner.composite_score) <= 0.02):
            candidates[0], candidates[1] = runner, top

    return candidates


def execute_rerouting(
    source_line: str,
    target_line: str,
    product_sku: str,
    quantity: float,
) -> dict:
    """Execute a rerouting decision; return operational parameters.

    Args:
        source_line: failed line name
        target_line: chosen reroute destination
        product_sku: SKU being rerouted
        quantity: units to reroute

    Returns:
        {changeover_time, additional_cost, quality_risk_score}
    """
    product = get_product(product_sku)
    if not product:
        raise ValueError(f"Product {product_sku} not found")

    # Resolve target plant
    target_plant_id = target_line.rsplit("-", 1)[0]  # "PLT-001-L2" → "PLT-001"
    target_plant_id = "-".join(target_line.split("-")[:2])  # "PLT-001"
    source_plant_id = "-".join(source_line.split("-")[:2])

    transport_cost, transport_hours = _transport_cost(source_plant_id, target_plant_id)
    is_same = source_plant_id == target_plant_id
    changeover_minutes = product.changeover_minutes
    changeover_cost = (changeover_minutes / 60.0) * CHANGEOVER_COST_PER_HOUR

    risk_rate = _quality_risk_rate(source_line, target_line, is_same)
    unit_value = 5.0  # ponytail: $5/unit default, refine per SKU if needed
    quality_risk_cost = quantity * unit_value * risk_rate

    additional_cost = round(changeover_cost + transport_cost + quality_risk_cost, 2)

    return {
        "changeover_time": changeover_minutes,
        "additional_cost": additional_cost,
        "quality_risk_score": round(risk_rate, 4),
        "transport_hours": transport_hours,
        "cost_breakdown": {
            "changeover": round(changeover_cost, 2),
            "transport": round(transport_cost, 2),
            "quality_risk": round(quality_risk_cost, 2),
        },
    }


def suggest_reroute(
    line_name: str,
    plant_id: str,
    product_sku: str,
    failure_duration_hours: float = 8.0,
    current_utilizations: dict[str, float] | None = None,
    reason: RerouteReason = RerouteReason.EQUIPMENT_FAILURE,
) -> RerouteResult:
    """Find best alternative lines when a line goes down.

    Backward-compat wrapper over score_rerouting_candidates().
    Returns candidates ranked by composite_score DESC.
    """
    candidates = score_rerouting_candidates(
        failed_line=line_name,
        product_sku=product_sku,
        plant_id=plant_id,
        current_utilizations=current_utilizations,
    )

    result = RerouteResult(
        failed_line=line_name,
        failed_plant=plant_id,
        failure_duration_hours=failure_duration_hours,
        product_sku=product_sku,
        reason=reason,
        candidates=candidates,
    )

    downtime_cost = failure_duration_hours * DOWNTIME_COST_PER_HOUR

    if candidates:
        best = candidates[0]
        loc = "same plant" if best.is_same_plant else f"plant {best.plant_id}"
        result.recommendation = (
            f"Reroute to {best.line_name} ({loc}). "
            f"Score: {best.composite_score:.3f} "
            f"(changeover {best.changeover_minutes:.0f}min"
            f"{f', transport {best.transport_hours}h' if not best.is_same_plant else ''}). "
            f"Avoids ${downtime_cost:,.0f} downtime loss."
        )
    else:
        result.recommendation = "No viable candidates — all lines at capacity or incompatible."

    return result


# ── SimPy integration ────────────────────────────────────────────────────────

def simpy_reroute_handler(env, line_name: str, plant_id: str, product_sku: str,
                          downtime_hours: float, kpis: ReroutingKPIs | None = None,
                          current_utilizations: dict[str, float] | None = None):
    """SimPy generator: triggered on failure event; evaluates reroute options.

    Usage in a SimPy process:
        yield from simpy_reroute_handler(env, "PLT-001-L1", "PLT-001",
                                         "WAT-500S", downtime_hours=2.0, kpis=kpis)
    """
    if kpis is not None:
        kpis.total_downtime_events += 1

    # Only reroute for unplanned failures >30 min
    if downtime_hours * 60 < 30:
        yield env.timeout(0)
        return

    candidates = score_rerouting_candidates(
        failed_line=line_name,
        product_sku=product_sku,
        plant_id=plant_id,
        current_utilizations=current_utilizations,
    )

    product = get_product(product_sku)
    units_per_hour = (product.units_per_batch / 8.0) if product else 1000.0
    recoverable = units_per_hour * downtime_hours

    if candidates:
        best = candidates[0]
        if kpis is not None:
            kpis.total_reroutes += 1
            kpis.total_changeover_penalty += (best.changeover_minutes / 60.0) * CHANGEOVER_COST_PER_HOUR
            # Volume recovered after changeover penalty
            changeover_hours = best.changeover_minutes / 60.0
            recovered = max(0.0, recoverable - units_per_hour * changeover_hours)
            kpis.volume_recovered_units += recovered
        # Yield changeover time so SimPy timeline advances correctly
        yield env.timeout(best.changeover_minutes / 60.0)
    else:
        if kpis is not None:
            kpis.volume_lost_units += recoverable
        yield env.timeout(0)


# ── Self-check ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time

    print("=== Rerouting Decision Engine Self-Check ===\n")

    # ── Scenario: PLT-001-L1 failure; expect L2 as primary reroute ────────────
    t0 = time.perf_counter()
    candidates = score_rerouting_candidates("PLT-001-L1", "WAT-500S", "PLT-001")
    elapsed = time.perf_counter() - t0

    assert candidates, "Should find candidates for PLT-001-L1 PET water failure"
    assert elapsed < 2.0, f"Scoring took {elapsed:.2f}s, must be <2s"

    top = candidates[0]
    assert top.line_name == "PLT-001-L2", (
        f"Expected PLT-001-L2 as primary reroute target, got {top.line_name}. "
        f"Scores: {[(c.line_name, round(c.composite_score, 3)) for c in candidates[:3]]}"
    )
    assert top.compat_score == 1.0, f"Direct partner must have compat_score=1.0, got {top.compat_score}"
    print(f"PLT-001-L1 failure → top candidate: {top.line_name} "
          f"(score={top.composite_score:.3f}) ✓  [{elapsed*1000:.0f}ms]")
    print(f"  compat={top.compat_score:.2f}  capacity={top.capacity_score:.2f}  "
          f"changeover={top.changeover_score:.2f}  quality={top.quality_score:.2f}")
    print(f"  changeover: {top.changeover_minutes:.0f}min, "
          f"cost breakdown: {top.cost_breakdown}")

    # Verify ranking: all candidates sorted DESC
    for i in range(len(candidates) - 1):
        assert candidates[i].composite_score >= candidates[i + 1].composite_score, \
            f"Not sorted DESC at index {i}"
    print(f"  {len(candidates)} candidates ranked DESC by composite_score ✓\n")

    # ── execute_rerouting: verify shape and changeover cost ──────────────────
    result = execute_rerouting("PLT-001-L1", "PLT-001-L2", "WAT-500S", quantity=12000)
    assert "changeover_time" in result and "additional_cost" in result and "quality_risk_score" in result
    assert result["changeover_time"] == 20.0, f"WAT-500S changeover should be 20 min, got {result['changeover_time']}"
    expected_co_cost = (20.0 / 60.0) * CHANGEOVER_COST_PER_HOUR
    assert abs(result["cost_breakdown"]["changeover"] - expected_co_cost) < 0.01, \
        f"Changeover cost mismatch: {result['cost_breakdown']['changeover']} vs {expected_co_cost}"
    print(f"execute_rerouting PLT-001-L1→L2 WAT-500S ✓")
    print(f"  changeover_time={result['changeover_time']}min  "
          f"additional_cost=${result['additional_cost']:,.2f}  "
          f"quality_risk={result['quality_risk_score']:.4f}")
    print(f"  breakdown: {result['cost_breakdown']}\n")

    # ── KPI tracking via SimPy handler ───────────────────────────────────────
    try:
        import simpy
        kpis = ReroutingKPIs()
        env = simpy.Environment()

        def _run(env):
            yield from simpy_reroute_handler(env, "PLT-001-L1", "PLT-001", "WAT-500S",
                                             downtime_hours=2.0, kpis=kpis)

        env.process(_run(env))
        env.run()
        assert kpis.total_reroutes == 1, f"Expected 1 reroute, got {kpis.total_reroutes}"
        assert kpis.avg_changeover_penalty > 0
        print(f"SimPy handler KPIs: {kpis.to_dict()} ✓")
    except ImportError:
        print("SimPy not installed — skipping SimPy integration check")

    # ── Backward-compat suggest_reroute ──────────────────────────────────────
    r = suggest_reroute("PLT-001-L1", "PLT-001", "WAT-500S")
    assert r.candidates[0].line_name == "PLT-001-L2"
    d = r.to_dict()
    assert "top_3" in d and "recommendation" in d
    print(f"suggest_reroute backward-compat ✓  — {r.recommendation[:80]}...")

    # ── Urgency weights: critical should still prefer L2 for PLT-001-L1 ──────
    crit = score_rerouting_candidates("PLT-001-L1", "WAT-500S", "PLT-001", urgency="critical")
    assert crit and crit[0].line_name == "PLT-001-L2", "Critical urgency should still prefer L2"
    print(f"urgency='critical' still selects PLT-001-L2 ✓")

    # ── Cross-plant reroute: cross-plant candidates have transport cost ────────
    r_cross = suggest_reroute("PLT-004-L3", "PLT-004", "PET-WC4", failure_duration_hours=10.0)
    cross = [c for c in r_cross.candidates if not c.is_same_plant]
    for c in cross:
        assert c.transport_cost > 0, f"{c.line_name}: cross-plant but transport_cost=0"
    if cross:
        print(f"Cross-plant reroute (PET-WC4): {len(cross)} cross-plant candidates with transport ✓")

    # ── Capacity gate ─────────────────────────────────────────────────────────
    r2 = score_rerouting_candidates(
        "PLT-001-L1", "WAT-500S", "PLT-001",
        current_utilizations={"PLT-001-L2": 0.90, "PLT-001-L3": 0.92, "PLT-001-L4": 0.88},
    )
    for c in r2:
        assert c.current_utilization + 0.10 <= 0.95, f"{c.line_name} exceeds 95% cap"
    print(f"Capacity ≤95% gate enforced — over-utilised same-plant lines excluded ✓")

    print("\n=== All checks passed ===")
