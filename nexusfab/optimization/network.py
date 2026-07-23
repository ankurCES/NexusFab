"""Multi-plant network optimization.

Capacity balancing, inter-plant transfer planning, and network-wide
KPI aggregation across the 5-plant manufacturing network.
"""

from dataclasses import dataclass, field
from datetime import datetime

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import get_products_for_plant
from nexusfab.optimization.rerouting import _transport_cost


@dataclass
class PlantCapacity:
    plant_id: str
    plant_name: str
    category: str
    total_capacity_tons: float
    current_utilization: float
    available_capacity_tons: float
    line_count: int
    equipment_count: int
    avg_oee: float

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "name": self.plant_name,
            "category": self.category,
            "capacity_tons": round(self.total_capacity_tons, 1),
            "utilization": round(self.current_utilization, 4),
            "available_tons": round(self.available_capacity_tons, 1),
            "lines": self.line_count,
            "equipment": self.equipment_count,
            "avg_oee": round(self.avg_oee, 4),
        }


@dataclass
class TransferOption:
    from_plant: str
    to_plant: str
    product_category: str
    transfer_tons: float
    transport_cost: float
    transport_hours: float
    cost_per_ton: float

    def to_dict(self) -> dict:
        return {
            "from": self.from_plant,
            "to": self.to_plant,
            "category": self.product_category,
            "tons": round(self.transfer_tons, 1),
            "transport_cost": round(self.transport_cost, 2),
            "transport_hours": self.transport_hours,
            "cost_per_ton": round(self.cost_per_ton, 2),
        }


@dataclass
class NetworkReport:
    timestamp: str
    plants: list[PlantCapacity] = field(default_factory=list)
    transfers: list[TransferOption] = field(default_factory=list)
    total_network_capacity: float = 0.0
    avg_network_utilization: float = 0.0
    avg_network_oee: float = 0.0
    bottleneck_plant: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "network_capacity_tons": round(self.total_network_capacity, 1),
            "avg_utilization": round(self.avg_network_utilization, 4),
            "avg_oee": round(self.avg_network_oee, 4),
            "bottleneck": self.bottleneck_plant,
            "plant_count": len(self.plants),
            "plants": [p.to_dict() for p in self.plants],
            "suggested_transfers": [t.to_dict() for t in self.transfers],
        }


# ponytail: OEE targets from seed, utilization randomized per call
_DEFAULT_UTILIZATIONS = {
    "PLT-001": 0.72,
    "PLT-002": 0.68,
    "PLT-003": 0.58,
    "PLT-004": 0.75,
    "PLT-005": 0.62,
}


def analyze_network(
    utilizations: dict[str, float] | None = None,
    oee_values: dict[str, float] | None = None,
) -> NetworkReport:
    """Analyze capacity across plant network, suggest transfers."""
    if utilizations is None:
        utilizations = _DEFAULT_UTILIZATIONS.copy()
    if oee_values is None:
        oee_values = {p.id: p.starting_oee for p in PLANTS}

    report = NetworkReport(
        timestamp=datetime(2026, 7, 23, 0, 0, 0).isoformat(),
    )

    for plant in PLANTS:
        util = utilizations.get(plant.id, 0.65)
        oee = oee_values.get(plant.id, plant.starting_oee)
        eq_count = sum(len(l.equipment) for l in plant.lines)

        cap = PlantCapacity(
            plant_id=plant.id,
            plant_name=plant.name,
            category=plant.category,
            total_capacity_tons=plant.capacity_tons_per_day,
            current_utilization=util,
            available_capacity_tons=plant.capacity_tons_per_day * (1 - util),
            line_count=len(plant.lines),
            equipment_count=eq_count,
            avg_oee=oee,
        )
        report.plants.append(cap)

    report.total_network_capacity = sum(p.total_capacity_tons for p in report.plants)
    report.avg_network_utilization = (
        sum(p.current_utilization for p in report.plants) / len(report.plants)
    )
    report.avg_network_oee = (
        sum(p.avg_oee for p in report.plants) / len(report.plants)
    )

    # Bottleneck = highest utilization
    bottleneck = max(report.plants, key=lambda p: p.current_utilization)
    report.bottleneck_plant = bottleneck.plant_id

    # Suggest transfers from over-utilized to under-utilized
    over = [p for p in report.plants if p.current_utilization > 0.80]
    under = [p for p in report.plants if p.current_utilization < 0.60]

    for o in over:
        for u in under:
            cost, hours = _transport_cost(o.plant_id, u.plant_id)
            transfer_tons = min(
                o.total_capacity_tons * (o.current_utilization - 0.75),
                u.available_capacity_tons * 0.5,
            )
            if transfer_tons > 0:
                report.transfers.append(TransferOption(
                    from_plant=o.plant_id,
                    to_plant=u.plant_id,
                    product_category=o.category,
                    transfer_tons=transfer_tons,
                    transport_cost=cost * (transfer_tons / 20),  # per truckload
                    transport_hours=hours,
                    cost_per_ton=cost / 20 if transfer_tons > 0 else 0,
                ))

    return report


if __name__ == "__main__":
    r = analyze_network()
    d = r.to_dict()
    print(f"Network: {d['plant_count']} plants, {d['network_capacity_tons']:.0f} tons/day")
    print(f"Avg util: {d['avg_utilization']:.1%}, OEE: {d['avg_oee']:.1%}")
    print(f"Bottleneck: {d['bottleneck']}")
    print(f"Transfers: {len(d['suggested_transfers'])}")
    assert d['plant_count'] == 5
    assert d['network_capacity_tons'] > 0
    print("PASS")
