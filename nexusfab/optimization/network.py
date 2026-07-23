"""Multi-plant network optimization.

Capacity balancing, inter-plant transfer planning, network-wide
KPI aggregation, and flow graph across the 5-plant network.
"""

from dataclasses import dataclass, field
from datetime import datetime

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.optimization.rerouting import _transport_cost


# ── Transport model ──
# ponytail: pallet-based costs ($50-$500/pallet), 20 pallets/truck min
PALLETS_PER_TRUCK = 20
TONS_PER_PALLET = 1.0


def transport_cost_pallet(from_plant: str, to_plant: str) -> dict:
    """Pallet-level transport cost and lead time between two plants.

    Returns dict with cost_per_pallet ($50-$500), lead_time_hours (4-48),
    and min_pallets (full truck = 20).
    """
    if from_plant == to_plant:
        return {"cost_per_pallet": 0.0, "lead_time_hours": 0.0, "min_pallets": 0}
    p1, p2 = get_plant(from_plant), get_plant(to_plant)
    if not p1 or not p2:
        return {"cost_per_pallet": 500.0, "lead_time_hours": 48.0, "min_pallets": PALLETS_PER_TRUCK}
    dist = ((p1.lat - p2.lat) ** 2 + (p1.lon - p2.lon) ** 2) ** 0.5
    # Scale to $50-$500/pallet range; max dist across US plants ~50 degrees
    cost = max(50.0, min(500.0, 50.0 + dist * 10.0))
    hours = max(4.0, min(48.0, 4.0 + dist * 1.0))
    return {
        "cost_per_pallet": round(cost, 2),
        "lead_time_hours": round(hours, 1),
        "min_pallets": PALLETS_PER_TRUCK,
    }


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
    pallets: int = 0
    cost_per_pallet: float = 0.0

    def to_dict(self) -> dict:
        return {
            "from": self.from_plant,
            "to": self.to_plant,
            "category": self.product_category,
            "tons": round(self.transfer_tons, 1),
            "pallets": self.pallets,
            "transport_cost": round(self.transport_cost, 2),
            "transport_hours": self.transport_hours,
            "cost_per_ton": round(self.cost_per_ton, 2),
            "cost_per_pallet": round(self.cost_per_pallet, 2),
        }


@dataclass
class NetworkFlowEdge:
    """One directed edge in the plant-to-plant flow graph."""
    source: str
    target: str
    flow_tons: float
    cost: float
    lead_time_hours: float
    pallets: int
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "flow_tons": round(self.flow_tons, 1),
            "cost": round(self.cost, 2),
            "lead_time_hours": self.lead_time_hours,
            "pallets": self.pallets,
            "active": self.active,
        }


@dataclass
class NetworkFlowNode:
    """One node (plant) in the flow graph."""
    id: str
    name: str
    lat: float
    lon: float
    category: str
    capacity_tons: float
    utilization: float
    status: str = "normal"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "category": self.category,
            "capacity_tons": round(self.capacity_tons, 1),
            "utilization": round(self.utilization, 4),
            "status": self.status,
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
    flow_nodes: list[NetworkFlowNode] = field(default_factory=list)
    flow_edges: list[NetworkFlowEdge] = field(default_factory=list)

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
            "flow_graph": {
                "nodes": [n.to_dict() for n in self.flow_nodes],
                "edges": [e.to_dict() for e in self.flow_edges],
            },
        }


# ponytail: OEE targets from seed, utilization randomized per call
_DEFAULT_UTILIZATIONS = {
    "PLT-001": 0.72,
    "PLT-002": 0.68,
    "PLT-003": 0.58,
    "PLT-004": 0.75,
    "PLT-005": 0.62,
}

_UTIL_THRESHOLD_OVER = 0.80
_UTIL_THRESHOLD_UNDER = 0.60


def _build_flow_graph(
    plants_cap: list[PlantCapacity],
    transfers: list[TransferOption],
    utilizations: dict[str, float],
) -> tuple[list[NetworkFlowNode], list[NetworkFlowEdge]]:
    """Build flow graph nodes + edges from plant capacities and transfers."""
    nodes = []
    for pc in plants_cap:
        plant = get_plant(pc.plant_id)
        status = "overloaded" if pc.current_utilization > _UTIL_THRESHOLD_OVER else (
            "underloaded" if pc.current_utilization < _UTIL_THRESHOLD_UNDER else "normal"
        )
        nodes.append(NetworkFlowNode(
            id=pc.plant_id,
            name=pc.plant_name,
            lat=plant.lat if plant else 0.0,
            lon=plant.lon if plant else 0.0,
            category=pc.category,
            capacity_tons=pc.total_capacity_tons,
            utilization=pc.current_utilization,
            status=status,
        ))

    edges = []
    for t in transfers:
        edges.append(NetworkFlowEdge(
            source=t.from_plant,
            target=t.to_plant,
            flow_tons=t.transfer_tons,
            cost=t.transport_cost,
            lead_time_hours=t.transport_hours,
            pallets=t.pallets,
        ))

    # Add potential (inactive) edges for all plant pairs not already active
    active_pairs = {(e.source, e.target) for e in edges}
    for p1 in plants_cap:
        for p2 in plants_cap:
            if p1.plant_id != p2.plant_id and (p1.plant_id, p2.plant_id) not in active_pairs:
                tc = transport_cost_pallet(p1.plant_id, p2.plant_id)
                edges.append(NetworkFlowEdge(
                    source=p1.plant_id,
                    target=p2.plant_id,
                    flow_tons=0.0,
                    cost=0.0,
                    lead_time_hours=tc["lead_time_hours"],
                    pallets=0,
                    active=False,
                ))

    return nodes, edges


def analyze_network(
    utilizations: dict[str, float] | None = None,
    oee_values: dict[str, float] | None = None,
) -> NetworkReport:
    """Analyze capacity across plant network, suggest transfers, build flow graph."""
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

    bottleneck = max(report.plants, key=lambda p: p.current_utilization)
    report.bottleneck_plant = bottleneck.plant_id

    # Suggest transfers from over-utilized to under-utilized (pallet-based)
    over = [p for p in report.plants if p.current_utilization > _UTIL_THRESHOLD_OVER]
    under = [p for p in report.plants if p.current_utilization < _UTIL_THRESHOLD_UNDER]

    for o in over:
        for u in under:
            tc = transport_cost_pallet(o.plant_id, u.plant_id)
            transfer_tons = min(
                o.total_capacity_tons * (o.current_utilization - 0.75),
                u.available_capacity_tons * 0.5,
            )
            if transfer_tons < PALLETS_PER_TRUCK * TONS_PER_PALLET:
                continue  # minimum full truck
            pallets = max(PALLETS_PER_TRUCK, int(transfer_tons / TONS_PER_PALLET))
            total_cost = pallets * tc["cost_per_pallet"]
            report.transfers.append(TransferOption(
                from_plant=o.plant_id,
                to_plant=u.plant_id,
                product_category=o.category,
                transfer_tons=transfer_tons,
                transport_cost=total_cost,
                transport_hours=tc["lead_time_hours"],
                cost_per_ton=total_cost / transfer_tons if transfer_tons > 0 else 0,
                pallets=pallets,
                cost_per_pallet=tc["cost_per_pallet"],
            ))

    report.flow_nodes, report.flow_edges = _build_flow_graph(
        report.plants, report.transfers, utilizations,
    )

    return report


def balance_network(
    utilizations: dict[str, float],
    failed_plant: str | None = None,
) -> NetworkReport:
    """Load-balance across network during peaks or failures.

    If failed_plant is set, its utilization is zeroed and load distributed.
    """
    utils = utilizations.copy()
    if failed_plant and failed_plant in utils:
        failed_load = utils[failed_plant]
        utils[failed_plant] = 0.0
        # Distribute failed plant's load proportionally to remaining plants' available capacity
        remaining = {pid: u for pid, u in utils.items() if pid != failed_plant and u < 0.95}
        total_available = sum(1.0 - u for u in remaining.values())
        if total_available > 0:
            for pid in remaining:
                share = (1.0 - remaining[pid]) / total_available
                utils[pid] = min(0.95, utils[pid] + failed_load * share)

    return analyze_network(utilizations=utils)


if __name__ == "__main__":
    r = analyze_network()
    d = r.to_dict()
    print(f"Network: {d['plant_count']} plants, {d['network_capacity_tons']:.0f} tons/day")
    print(f"Avg util: {d['avg_utilization']:.1%}, OEE: {d['avg_oee']:.1%}")
    print(f"Bottleneck: {d['bottleneck']}")
    print(f"Transfers: {len(d['suggested_transfers'])}")
    assert d["plant_count"] == 5
    assert d["network_capacity_tons"] > 0

    # Flow graph
    fg = d["flow_graph"]
    assert len(fg["nodes"]) == 5
    assert len(fg["edges"]) > 0
    for n in fg["nodes"]:
        assert n["lat"] != 0.0
        assert n["status"] in ("normal", "overloaded", "underloaded")
    print(f"Flow graph: {len(fg['nodes'])} nodes, {len(fg['edges'])} edges")

    # Pallet-based transport
    tc = transport_cost_pallet("PLT-001", "PLT-005")
    assert 50.0 <= tc["cost_per_pallet"] <= 500.0
    assert 4.0 <= tc["lead_time_hours"] <= 48.0
    assert tc["min_pallets"] == PALLETS_PER_TRUCK
    print(f"PLT-001→PLT-005: ${tc['cost_per_pallet']}/pallet, {tc['lead_time_hours']}h, min {tc['min_pallets']} pallets")

    # Load balancing with plant failure
    r2 = balance_network(
        {"PLT-001": 0.85, "PLT-002": 0.70, "PLT-003": 0.50, "PLT-004": 0.60, "PLT-005": 0.55},
        failed_plant="PLT-001",
    )
    d2 = r2.to_dict()
    failed_node = next(p for p in d2["plants"] if p["plant_id"] == "PLT-001")
    assert failed_node["utilization"] == 0.0
    remaining_avg = sum(p["utilization"] for p in d2["plants"] if p["plant_id"] != "PLT-001") / 4
    assert remaining_avg > 0.55, "Load should be redistributed"
    print(f"After PLT-001 failure: remaining avg util {remaining_avg:.1%}")

    print("PASS")
