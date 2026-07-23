"""Network + demand planning API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.api.schemas.network import AllocationPlan, NetworkAnalysis, NetworkFlow, TransportCost
from nexusfab.optimization.demand import generate_demand_plan
from nexusfab.optimization.network import (
    analyze_network,
    balance_network,
    transport_cost_pallet,
)
from nexusfab.simulation.runner import run_network

router = APIRouter(prefix="/api/network", tags=["Network"])


class NetworkRequest(BaseModel):
    utilizations: dict[str, float] | None = None
    oee_values: dict[str, float] | None = None


class DemandRequest(BaseModel):
    plant_id: str | None = None
    horizon_weeks: int = Field(default=12, ge=1, le=52)
    seed: int = 42


class BalanceRequest(BaseModel):
    utilizations: dict[str, float]
    failed_plant: str | None = None


class SimNetworkRequest(BaseModel):
    duration_hours: float = Field(default=168.0, ge=1, le=8760)
    seed: int = 42
    plant_ids: list[str] | None = None


@router.get("/status", response_model=NetworkAnalysis, summary="Current network status — utilization, OEE, and transfer analysis across all plants")
async def get_network_status():
    report = analyze_network()
    return report.to_dict()


@router.post("/analyze", response_model=NetworkAnalysis, summary="Network analysis with custom utilization and OEE overrides")
async def analyze_network_custom(req: NetworkRequest):
    report = analyze_network(
        utilizations=req.utilizations,
        oee_values=req.oee_values,
    )
    return report.to_dict()


@router.get("/flow", response_model=NetworkAnalysis, summary="Flow graph with nodes (plants) and edges (transfer routes)")
async def get_flow_graph():
    """Flow graph with nodes (plants) and edges (transfer routes)."""
    report = analyze_network()
    return report.to_dict()["flow_graph"]


@router.post("/balance", response_model=NetworkAnalysis, summary="Load-balance network; optionally simulate a plant failure")
async def balance_load(req: BalanceRequest):
    """Load-balance network; optionally simulate a plant failure."""
    report = balance_network(req.utilizations, req.failed_plant)
    return report.to_dict()


@router.post("/simulate", response_model=NetworkAnalysis, summary="Run simulation across all plants and return network-level results")
async def simulate_network(req: SimNetworkRequest):
    """Run simulation across all plants, return network-level results + derived utilizations."""
    result = run_network(req.duration_hours, req.seed, req.plant_ids)
    report = analyze_network(utilizations=result["utilizations"])
    return {
        "simulation": result,
        "network_analysis": report.to_dict(),
    }


@router.get("/transport/{from_plant}/{to_plant}", response_model=TransportCost, summary="Pallet-level transport cost between two plants")
async def get_transport_cost(from_plant: str, to_plant: str):
    """Pallet-level transport cost between two plants."""
    return transport_cost_pallet(from_plant, to_plant)


@router.post("/demand", response_model=NetworkAnalysis, summary="Generate demand forecast plan for a plant or network")
async def get_demand_plan(req: DemandRequest):
    plan = generate_demand_plan(
        plant_id=req.plant_id,
        horizon_weeks=req.horizon_weeks,
        seed=req.seed,
    )
    return plan.to_dict()


@router.get("/demand/{plant_id}", response_model=NetworkAnalysis, summary="Demand forecast for a specific plant")
async def get_plant_demand(plant_id: str, weeks: int = 12):
    plan = generate_demand_plan(plant_id=plant_id, horizon_weeks=weeks)
    return plan.to_dict()


@router.get("/flows", response_model=NetworkFlow, summary="All inter-plant routes with volume, cost, transit time, cold chain flag")
async def get_interplant_flows():
    """All inter-plant routes with volume, cost, transit time, cold chain flag."""
    from nexusfab.seed.plants import PLANTS as _PLANTS

    report = analyze_network()
    plant_ids = [p.plant_id for p in report.plants]

    active_map: dict[frozenset, object] = {}
    for t in report.transfers:
        active_map[frozenset({t.from_plant, t.to_plant})] = t

    flows = []
    for i, p1 in enumerate(plant_ids):
        for p2 in plant_ids[i + 1 :]:
            key = frozenset({p1, p2})
            tc = transport_cost_pallet(p1, p2)
            t = active_map.get(key)
            flows.append({
                "route": f"{p1}→{p2}",
                "from_plant": p1,
                "to_plant": p2,
                "volume_tons": round(t.transfer_tons, 1) if t else 0.0,  # type: ignore[union-attr]
                "cost_usd": round(t.transport_cost, 2) if t else 0.0,  # type: ignore[union-attr]
                "transit_hours": tc["lead_time_hours"],
                "cold_chain": tc["cold_chain"],
                "cost_per_pallet": tc["cost_per_pallet"],
                "active": t is not None,
            })

    total_monthly = round(sum(f["cost_usd"] for f in flows) * 4.33, 2)
    return {
        "flows": flows,
        "total_monthly_cost_usd": total_monthly,
        "active_routes": sum(1 for f in flows if f["active"]),
    }


@router.get("/allocation", response_model=AllocationPlan, summary="Product × plant allocation grid with line capacity details")
async def get_allocation_grid():
    """Product × plant allocation grid (current greedy + per-plant line details)."""
    from nexusfab.seed.plants import PLANTS as _PLANTS
    from nexusfab.seed.products import PRODUCTS

    report = analyze_network()
    plant_summary: dict[str, dict] = {}
    for pc in report.plants:
        pl = next((p for p in _PLANTS if p.id == pc.plant_id), None)
        total_speed = sum(l.rated_speed_per_min for l in pl.lines) if pl else 0
        lines = []
        if pl:
            for l in pl.lines:
                lines.append({
                    "name": l.name,
                    "speed_upm": l.rated_speed_per_min,
                    "pct": round(l.rated_speed_per_min / total_speed * 100, 1) if total_speed > 0 else 0,
                })
        plant_summary[pc.plant_id] = {
            "utilization": round(pc.current_utilization * 100, 1),
            "oee": round(pc.avg_oee * 100, 1),
            "target_oee": round(pl.target_oee * 100, 1) if pl else 78.0,
            "capacity_tons": pc.total_capacity_tons,
            "available_tons": round(pc.available_capacity_tons, 1),
            "lines": lines,
        }

    demand_by_sku: dict[str, float] = {}
    for pl in _PLANTS:
        dp = generate_demand_plan(plant_id=pl.id, horizon_weeks=4)
        for f in dp.forecasts:
            demand_by_sku.setdefault(f.sku, 0.0)
            demand_by_sku[f.sku] += f.forecast_units / 4

    products_out = [
        {"sku": p.sku, "name": p.name, "category": p.category, "home_plant": p.plant_id}
        for p in PRODUCTS
    ]
    plant_ids = [p.plant_id for p in report.plants]

    # Current = greedy: 100% to home plant
    allocation: dict[str, dict[str, dict]] = {}
    for p in PRODUCTS:
        d = demand_by_sku.get(p.sku, 0.0)
        allocation[p.sku] = {
            pl_id: {"volume": round(d) if pl_id == p.plant_id else 0, "pct": 100.0 if pl_id == p.plant_id else 0.0}
            for pl_id in plant_ids
        }

    return {
        "products": products_out,
        "plants": plant_ids,
        "allocation": allocation,
        "plant_summary": plant_summary,
    }


@router.get("/optimize", response_model=AllocationPlan, summary="Run MILP 4-week allocation and return plan vs greedy baseline")
async def get_milp_optimize():
    """Run MILP 4-week allocation and return plan vs greedy baseline."""
    from nexusfab.optimization.network import build_allocation_problem, solve_milp

    prob = build_allocation_problem(n_periods=4)
    plan = solve_milp(prob, time_limit_sec=30)
    result = plan.to_dict()

    # Aggregate MILP production by (sku, plant) for the allocation grid
    alloc: dict[str, dict[str, float]] = {}
    for (s, l, t), units in plan.production.items():
        pl = prob.line_plant[l]
        alloc.setdefault(s, {}).setdefault(pl, 0.0)
        alloc[s][pl] += units

    demand_by_sku: dict[str, float] = {}
    for (s, t), d in prob.demand.items():
        demand_by_sku.setdefault(s, 0.0)
        demand_by_sku[s] += d / prob.n_periods

    result["allocation_by_plant"] = {
        s: {
            pl: {
                "volume": round(v),
                "pct": round(v / demand_by_sku[s] * 100, 1) if demand_by_sku.get(s, 0) > 0 else 0.0,
            }
            for pl, v in pl_map.items()
        }
        for s, pl_map in alloc.items()
    }
    return result
