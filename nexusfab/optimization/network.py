"""Multi-plant network optimization.

Capacity balancing, inter-plant transfer planning, network-wide
KPI aggregation, and flow graph across the 5-plant network.
"""

import time as _time
from dataclasses import dataclass, field
from datetime import datetime

from nexusfab.seed.plants import PLANTS, WEEKLY_PLANNED_DOWNTIME, get_plant


# ── Transport model ──
# Research-backed matrix from docs/research/supply-chain-demand.md §3.3
PALLETS_PER_TRUCK = 20
TONS_PER_PALLET = 1.0
COLD_CHAIN_SURCHARGE_PCT = 0.40  # +40% for dairy (PLT-003); range 35-50%, use midpoint

# (cost_per_pallet_usd, transit_hours) — symmetric, keyed as frozenset
_TRANSPORT_MATRIX: dict[frozenset[str], tuple[float, float]] = {
    frozenset({"PLT-001", "PLT-002"}): (180.0, 14.0),
    frozenset({"PLT-001", "PLT-003"}): (250.0, 20.0),
    frozenset({"PLT-001", "PLT-004"}): (140.0, 13.0),
    frozenset({"PLT-001", "PLT-005"}): (460.0, 42.0),
    frozenset({"PLT-002", "PLT-003"}): (110.0, 7.0),
    frozenset({"PLT-002", "PLT-004"}): (130.0, 11.0),
    frozenset({"PLT-002", "PLT-005"}): (310.0, 30.0),
    frozenset({"PLT-003", "PLT-004"}): (210.0, 18.0),
    frozenset({"PLT-003", "PLT-005"}): (270.0, 26.0),
    frozenset({"PLT-004", "PLT-005"}): (370.0, 34.0),
}
_FALLBACK_COST = (500.0, 48.0)


def _is_dairy_route(from_plant: str, to_plant: str) -> bool:
    """True if either endpoint is the dairy plant (PLT-003)."""
    p1, p2 = get_plant(from_plant), get_plant(to_plant)
    return (p1 and p1.category == "DAIRY") or (p2 and p2.category == "DAIRY")


def transport_cost_pallet(from_plant: str, to_plant: str, product_category: str | None = None) -> dict:
    """Pallet-level transport cost and lead time between two plants.

    Returns dict with cost_per_pallet, lead_time_hours, min_pallets,
    and cold_chain bool.  Applies cold-chain surcharge when
    product_category is DAIRY or route involves PLT-003.
    """
    if from_plant == to_plant:
        return {"cost_per_pallet": 0.0, "lead_time_hours": 0.0, "min_pallets": 0, "cold_chain": False}

    key = frozenset({from_plant, to_plant})
    cost, hours = _TRANSPORT_MATRIX.get(key, _FALLBACK_COST)

    dairy = (product_category == "DAIRY") or _is_dairy_route(from_plant, to_plant)
    if dairy:
        cost *= (1.0 + COLD_CHAIN_SURCHARGE_PCT)

    return {
        "cost_per_pallet": round(cost, 2),
        "lead_time_hours": hours,
        "min_pallets": PALLETS_PER_TRUCK,
        "cold_chain": dairy,
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
            tc = transport_cost_pallet(o.plant_id, u.plant_id, product_category=o.category)
            transfer_tons = min(
                o.total_capacity_tons * (o.current_utilization - 0.75),
                u.available_capacity_tons * 0.5,
            )
            # FTL minimum: 20 pallets per shipment
            pallets = max(PALLETS_PER_TRUCK, int(transfer_tons / TONS_PER_PALLET))
            transfer_tons = max(transfer_tons, PALLETS_PER_TRUCK * TONS_PER_PALLET)
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


# ── MILP Multi-Plant Allocation ──────────────────────────────────────────────
# Research basis: docs/research/supply-chain-demand.md §3

_OT_RATE = 150.0  # $/hr overtime premium (PLT-004 max 16h/wk policy)

# Variable production cost ($/unit) — research §5.5 COGS ratios
_VAR_COST: dict[str, float] = {
    "WATER": 0.04, "CONFECTIONERY": 0.18,
    "DAIRY": 0.12, "PET_FOOD": 0.08, "PREPARED_FOODS": 0.10,
}
# Holding cost ($/unit/week) — midpoint of §5.5 storage regime ranges
_HOLD_COST: dict[str, float] = {
    "WATER": 0.003, "CONFECTIONERY": 0.004,
    "DAIRY": 0.008, "PET_FOOD": 0.005, "PREPARED_FOODS": 0.007,
}


@dataclass
class AllocationProblem:
    """Input problem for MILP multi-plant allocation."""
    n_periods: int
    skus: list[str]
    lines: list[str]
    plants: list[str]
    line_plant: dict[str, str]        # line_name -> plant_id
    sku_plant: dict[str, str]         # sku -> plant_id (home plant = compatible plant)
    sku_category: dict[str, str]      # sku -> category
    line_speed_uph: dict[str, float]  # line_name -> units/hour
    base_hours: dict[str, float]      # line_name -> OEE-adjusted available hrs/week
    plant_n_lines: dict[str, int]     # plant_id -> line count
    demand: dict[tuple[str, int], float]   # (sku, period) -> units
    safety_stock: dict[str, float]         # sku -> units
    init_inv: dict[str, float]             # sku -> starting inventory units
    min_batch: dict[str, int]              # sku -> units_per_batch
    var_cost: dict[str, float]             # sku -> $/unit
    hold_cost: dict[str, float]            # sku -> $/unit/week
    ot_rate: float = _OT_RATE
    max_ot_hours: float = 16.0             # cap per plant per week (PLT-004 rule)


@dataclass
class AllocationPlan:
    """Output from MILP solve: production assignments + cost breakdown."""
    status: str                                          # OPTIMAL | FEASIBLE | INFEASIBLE
    objective: float                                     # total optimized cost $
    greedy_cost: float                                   # baseline greedy cost $
    gap_pct: float                                       # MIP optimality gap %
    solve_time_sec: float
    production: dict[tuple[str, str, int], float]        # (sku, line, period) -> units
    inventory: dict[tuple[str, int], float]              # (sku, period) -> units
    overtime: dict[tuple[str, int], float]               # (plant_id, period) -> hours
    production_cost: float
    inventory_cost: float
    overtime_cost: float
    transport_summary: list[dict]
    line_utilization: dict[str, float]                   # line -> avg utilization

    def savings_pct(self) -> float:
        if self.greedy_cost <= 0:
            return 0.0
        return (self.greedy_cost - self.objective) / self.greedy_cost * 100.0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "objective_usd": round(self.objective, 2),
            "greedy_usd": round(self.greedy_cost, 2),
            "savings_pct": round(self.savings_pct(), 2),
            "gap_pct": round(self.gap_pct, 2),
            "solve_time_sec": round(self.solve_time_sec, 3),
            "cost_breakdown": {
                "production": round(self.production_cost, 2),
                "inventory": round(self.inventory_cost, 2),
                "overtime": round(self.overtime_cost, 2),
            },
            "line_utilization": {k: round(v, 4) for k, v in self.line_utilization.items()},
            "transport": self.transport_summary,
        }


def build_allocation_problem(
    n_periods: int = 4,
    base_date: datetime | None = None,
    seed: int = 42,
) -> AllocationProblem:
    """Build AllocationProblem from plant/line/product/demand seed data."""
    from nexusfab.optimization.demand import generate_demand_plan
    from nexusfab.seed.products import PRODUCTS

    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)

    skus = [p.sku for p in PRODUCTS]
    lines = [ln.name for pl in PLANTS for ln in pl.lines]
    plants_list = [pl.id for pl in PLANTS]

    line_plant = {ln.name: pl.id for pl in PLANTS for ln in pl.lines}
    sku_plant = {p.sku: p.plant_id for p in PRODUCTS}
    sku_category = {p.sku: p.category for p in PRODUCTS}
    plant_n_lines = {pl.id: len(pl.lines) for pl in PLANTS}

    # OEE-adjusted available hours per line/week (168h × (1-DT%) × OEE)
    base_hours: dict[str, float] = {}
    for pl in PLANTS:
        dt = WEEKLY_PLANNED_DOWNTIME.get(pl.id, 0.0)
        avail = (168.0 - dt) * pl.starting_oee
        for ln in pl.lines:
            base_hours[ln.name] = avail

    line_speed_uph = {
        ln.name: ln.rated_speed_per_min * 60.0
        for pl in PLANTS for ln in pl.lines
    }

    demand: dict[tuple[str, int], float] = {}
    safety_stock: dict[str, float] = {}
    init_inv: dict[str, float] = {}

    for pl in PLANTS:
        dp = generate_demand_plan(
            plant_id=pl.id,
            horizon_weeks=n_periods,
            base_date=base_date,
            seed=seed,
        )
        by_sku: dict[str, list] = {}
        for f in dp.forecasts:
            by_sku.setdefault(f.sku, []).append(f)
        for sku, flist in by_sku.items():
            flist.sort(key=lambda f: f.period_start)
            for t, f in enumerate(flist[:n_periods], start=1):
                demand[(sku, t)] = float(f.forecast_units)
            if sku not in safety_stock:
                ss = float(flist[0].safety_stock_units) if flist else 0.0
                safety_stock[sku] = ss
                init_inv[sku] = ss * 1.5   # start above safety stock for slack

    for sku in skus:
        for t in range(1, n_periods + 1):
            demand.setdefault((sku, t), 0.0)
        safety_stock.setdefault(sku, 0.0)
        init_inv.setdefault(sku, 0.0)

    return AllocationProblem(
        n_periods=n_periods,
        skus=skus,
        lines=lines,
        plants=plants_list,
        line_plant=line_plant,
        sku_plant=sku_plant,
        sku_category=sku_category,
        line_speed_uph=line_speed_uph,
        base_hours=base_hours,
        plant_n_lines=plant_n_lines,
        demand=demand,
        safety_stock=safety_stock,
        init_inv=init_inv,
        min_batch={p.sku: p.units_per_batch for p in PRODUCTS},
        var_cost={p.sku: _VAR_COST.get(p.category, 0.08) for p in PRODUCTS},
        hold_cost={p.sku: _HOLD_COST.get(p.category, 0.005) for p in PRODUCTS},
    )


def _greedy_cost(prob: AllocationProblem) -> float:
    """Greedy baseline: produce to demand each period, OT when capacity exceeded."""
    total = 0.0
    periods = range(1, prob.n_periods + 1)

    # Production + holding costs at demand level
    for (sku, t), d in prob.demand.items():
        if d > 0:
            total += d * prob.var_cost[sku]
    for sku, ss in prob.safety_stock.items():
        total += ss * prob.hold_cost[sku] * prob.n_periods

    # OT when peak demand exceeds regular capacity
    for pl_id in prob.plants:
        pl_lines = [l for l in prob.lines if prob.line_plant[l] == pl_id]
        if not pl_lines:
            continue
        pl_skus = [s for s in prob.skus if prob.sku_plant[s] == pl_id]
        total_base_cap = sum(prob.base_hours[l] for l in pl_lines)
        avg_speed = sum(prob.line_speed_uph[l] for l in pl_lines) / len(pl_lines)
        for t in periods:
            total_dem = sum(prob.demand.get((s, t), 0.0) for s in pl_skus)
            hours_needed = total_dem / avg_speed if avg_speed > 0 else 0.0
            if hours_needed > total_base_cap:
                ot = min(hours_needed - total_base_cap, prob.max_ot_hours)
                total += ot * prob.ot_rate

    return total


def solve_milp(prob: AllocationProblem, time_limit_sec: int = 60) -> AllocationPlan:
    """Solve multi-plant allocation MILP with OR-Tools CBC backend.

    Decision variables: x[sku,line,t] production units, w[sku,line,t] binary
    activation, inv[sku,t] inventory, ot[plant,t] overtime hours.
    """
    from ortools.linear_solver import pywraplp

    t0 = _time.perf_counter()
    solver = pywraplp.Solver.CreateSolver("CBC")
    solver.set_time_limit(time_limit_sec * 1000)  # ms

    periods = list(range(1, prob.n_periods + 1))
    compatible = frozenset(
        (s, l)
        for s in prob.skus
        for l in prob.lines
        if prob.sku_plant[s] == prob.line_plant[l]
    )
    # BIG_M ≥ max possible production per line per period (speed × full week)
    BIG_M = max(prob.line_speed_uph.values()) * 168.0 * 1.5
    INF = solver.infinity()

    # ── Decision variables ────────────────────────────────────────────────────
    x = {
        (s, l, t): solver.NumVar(0.0, INF, f"x_{s}_{l}_{t}")
        for s, l in compatible
        for t in periods
    }
    w = {  # binary: 1 if any production of sku s on line l in period t
        (s, l, t): solver.IntVar(0, 1, f"w_{s}_{l}_{t}")
        for s, l in compatible
        for t in periods
    }
    inv = {  # end-of-period inventory ≥ safety_stock
        (s, t): solver.NumVar(prob.safety_stock.get(s, 0.0), INF, f"inv_{s}_{t}")
        for s in prob.skus
        for t in periods
    }
    ot = {  # overtime hours per plant per period
        (pl, t): solver.NumVar(0.0, prob.max_ot_hours, f"ot_{pl}_{t}")
        for pl in prob.plants
        for t in periods
    }

    # ── Objective ─────────────────────────────────────────────────────────────
    obj = solver.Objective()
    obj.SetMinimization()
    for (s, l, t), var in x.items():
        obj.SetCoefficient(var, prob.var_cost[s])
    for (s, t), var in inv.items():
        obj.SetCoefficient(var, prob.hold_cost[s])
    for (pl, t), var in ot.items():
        obj.SetCoefficient(var, prob.ot_rate)

    # ── Inventory balance: inv[s,t] = inv[s,t-1] + Σ_l x[s,l,t] - demand[s,t]
    for s in prob.skus:
        lines_s = [l for l in prob.lines if (s, l) in compatible]
        for t in periods:
            d = prob.demand.get((s, t), 0.0)
            if t == 1:
                rhs = prob.init_inv.get(s, 0.0) - d
                ct = solver.Constraint(rhs, rhs)
                ct.SetCoefficient(inv[s, 1], 1.0)
                for l in lines_s:
                    ct.SetCoefficient(x[s, l, 1], -1.0)
            else:
                ct = solver.Constraint(-d, -d)
                ct.SetCoefficient(inv[s, t], 1.0)
                ct.SetCoefficient(inv[s, t - 1], -1.0)
                for l in lines_s:
                    ct.SetCoefficient(x[s, l, t], -1.0)

    # ── Line capacity: Σ_s x[s,l,t]/speed - ot[pl,t]/n_lines ≤ base_hours[l]
    for l in prob.lines:
        pl = prob.line_plant[l]
        spd = prob.line_speed_uph[l]
        n = prob.plant_n_lines[pl]
        base = prob.base_hours[l]
        for t in periods:
            ct = solver.Constraint(-INF, base)
            for s in prob.skus:
                if (s, l) in compatible:
                    ct.SetCoefficient(x[s, l, t], 1.0 / spd)
            ct.SetCoefficient(ot[pl, t], -1.0 / n)  # OT shared across plant lines

    # ── Min-batch: x ≥ min_batch×w  AND  x ≤ BIG_M×w
    for s, l in compatible:
        mb = float(prob.min_batch[s])
        for t in periods:
            ct1 = solver.Constraint(0.0, INF)
            ct1.SetCoefficient(x[s, l, t], 1.0)
            ct1.SetCoefficient(w[s, l, t], -mb)
            ct2 = solver.Constraint(-INF, 0.0)
            ct2.SetCoefficient(x[s, l, t], 1.0)
            ct2.SetCoefficient(w[s, l, t], -BIG_M)

    # ── Solve ─────────────────────────────────────────────────────────────────
    result = solver.Solve()
    elapsed = _time.perf_counter() - t0

    _STATUS = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
    }
    status = _STATUS.get(result, "UNKNOWN")
    feasible = result in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)

    obj_val = solver.Objective().Value() if feasible else 0.0
    gap_pct = 0.0
    if feasible and obj_val > 0:
        try:
            best_bound = solver.Objective().BestBound()
            gap_pct = abs(obj_val - best_bound) / obj_val * 100.0
        except Exception:
            pass  # BestBound not available for LP relaxation

    # ── Extract solution ───────────────────────────────────────────────────────
    production: dict[tuple[str, str, int], float] = {}
    production_cost = 0.0
    if feasible:
        for (s, l, t), var in x.items():
            v = var.solution_value()
            if v > 0.5:
                production[s, l, t] = round(v)
                production_cost += v * prob.var_cost[s]

    inventory_vals: dict[tuple[str, int], float] = {}
    inventory_cost = 0.0
    if feasible:
        for (s, t), var in inv.items():
            v = var.solution_value()
            inventory_vals[s, t] = round(v)
            inventory_cost += v * prob.hold_cost[s]

    overtime_vals: dict[tuple[str, int], float] = {}
    overtime_cost = 0.0
    if feasible:
        for (pl, t), var in ot.items():
            v = var.solution_value()
            if v > 0.01:
                overtime_vals[pl, t] = round(v, 2)
                overtime_cost += v * prob.ot_rate

    # Line utilization: avg hours used / base hours over all periods
    line_util: dict[str, float] = {}
    for l in prob.lines:
        spd = prob.line_speed_uph[l]
        base = prob.base_hours[l]
        total_h = sum(
            production.get((s, l, t), 0.0) / spd
            for s in prob.skus
            for t in periods
            if (s, l) in compatible
        )
        line_util[l] = round(total_h / (base * prob.n_periods), 4) if base > 0 else 0.0

    network = analyze_network()
    transport_summary = [t.to_dict() for t in network.transfers]

    return AllocationPlan(
        status=status,
        objective=round(obj_val, 2),
        greedy_cost=round(_greedy_cost(prob), 2),
        gap_pct=round(gap_pct, 2),
        solve_time_sec=round(elapsed, 3),
        production=production,
        inventory=inventory_vals,
        overtime=overtime_vals,
        production_cost=round(production_cost, 2),
        inventory_cost=round(inventory_cost, 2),
        overtime_cost=round(overtime_cost, 2),
        transport_summary=transport_summary,
        line_utilization=line_util,
    )


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

    # Research-backed transport matrix
    tc = transport_cost_pallet("PLT-001", "PLT-005")
    assert tc["cost_per_pallet"] == 460.0, f"PLT-001↔005 ambient should be $460, got {tc['cost_per_pallet']}"
    assert tc["lead_time_hours"] == 42.0
    assert tc["min_pallets"] == PALLETS_PER_TRUCK
    assert not tc["cold_chain"]
    print(f"PLT-001→PLT-005: ${tc['cost_per_pallet']}/pallet, {tc['lead_time_hours']}h")

    # Cold chain: PLT-003→PLT-001 dairy should be +40% vs ambient $250
    tc_dairy = transport_cost_pallet("PLT-003", "PLT-001", product_category="DAIRY")
    expected_dairy = round(250.0 * 1.40, 2)
    assert tc_dairy["cost_per_pallet"] == expected_dairy, f"Dairy surcharge: expected ${expected_dairy}, got ${tc_dairy['cost_per_pallet']}"
    assert tc_dairy["cold_chain"]
    print(f"PLT-003→PLT-001 (dairy): ${tc_dairy['cost_per_pallet']}/pallet (+40% cold chain)")

    # Ambient route touching PLT-003 still gets cold chain (dairy plant)
    tc_ambient_003 = transport_cost_pallet("PLT-003", "PLT-002")
    assert tc_ambient_003["cold_chain"], "PLT-003 route should always flag cold_chain"
    print(f"PLT-003→PLT-002 (auto cold chain): ${tc_ambient_003['cost_per_pallet']}/pallet")

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

    # ── MILP: 4-week demand allocation across all 5 plants ──────────────────
    print("\n── MILP Multi-Plant Allocation (4-week horizon) ──")
    prob = build_allocation_problem(n_periods=4)
    plan = solve_milp(prob, time_limit_sec=60)
    pd = plan.to_dict()

    print(f"Status:      {pd['status']}  (gap {pd['gap_pct']:.2f}%, solved in {pd['solve_time_sec']:.3f}s)")
    print(f"MILP cost:   ${pd['objective_usd']:>12,.2f}")
    print(f"Greedy cost: ${pd['greedy_usd']:>12,.2f}")
    print(f"Savings:     {pd['savings_pct']:.1f}%")
    print(f"Breakdown:   production ${pd['cost_breakdown']['production']:,.2f}"
          f"  inventory ${pd['cost_breakdown']['inventory']:,.2f}"
          f"  overtime ${pd['cost_breakdown']['overtime']:,.2f}")

    # Line utilization
    print("\nLine utilization:")
    for line, util in sorted(pd["line_utilization"].items()):
        bar = "█" * int(util * 20)
        print(f"  {line:20s} {util:5.1%}  {bar}")

    # Assertions
    assert pd["status"] in ("OPTIMAL", "FEASIBLE"), f"Solver failed: {pd['status']}"
    assert pd["objective_usd"] > 0, "Objective must be positive"
    assert pd["greedy_usd"] >= pd["objective_usd"], "MILP must not exceed greedy cost"
    assert 0.0 <= pd["savings_pct"] <= 100.0, f"Unexpected savings: {pd['savings_pct']}"
    assert pd["cost_breakdown"]["production"] > 0, "Production cost must be positive"
    # All lines should have non-negative utilization
    assert all(v >= 0 for v in pd["line_utilization"].values())

    print("\nPASS")
