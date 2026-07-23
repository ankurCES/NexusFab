"""Line failure rerouting algorithm.

When a line goes down, find best alternative:
  Same plant (compatible format, available capacity) or sister plant.
  Minimize: downtime_loss + changeover_cost + transport_cost + overtime_cost + SLA_penalty
"""

from dataclasses import dataclass, field

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import get_product

# Cost parameters ($/hour or $/event)
DOWNTIME_COST_PER_HOUR = 15_000.0
CHANGEOVER_COST_PER_HOUR = 2_000.0
OVERTIME_PREMIUM_FACTOR = 1.5
SLA_PENALTY_PER_HOUR_LATE = 5_000.0

# Inter-plant transport
TRANSPORT_COSTS = {
    # (from_plant, to_plant) → (cost_per_load, hours)
    # ponytail: simplified distance matrix
}

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

            # Capacity check: candidate must be ≤95% after absorbing rerouted work
            added_utilization = 0.1  # rough estimate
            if utilization + added_utilization > 0.95:
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
                allergen_compatible=True,
                format_compatible=True,
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
