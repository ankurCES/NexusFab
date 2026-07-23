"""Network + demand planning API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.demand import generate_demand_plan
from nexusfab.optimization.network import (
    analyze_network,
    balance_network,
    transport_cost_pallet,
)
from nexusfab.simulation.runner import run_network

router = APIRouter(prefix="/api/network", tags=["network"])


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


@router.get("/status")
async def get_network_status():
    report = analyze_network()
    return report.to_dict()


@router.post("/analyze")
async def analyze_network_custom(req: NetworkRequest):
    report = analyze_network(
        utilizations=req.utilizations,
        oee_values=req.oee_values,
    )
    return report.to_dict()


@router.get("/flow")
async def get_flow_graph():
    """Flow graph with nodes (plants) and edges (transfer routes)."""
    report = analyze_network()
    return report.to_dict()["flow_graph"]


@router.post("/balance")
async def balance_load(req: BalanceRequest):
    """Load-balance network; optionally simulate a plant failure."""
    report = balance_network(req.utilizations, req.failed_plant)
    return report.to_dict()


@router.post("/simulate")
async def simulate_network(req: SimNetworkRequest):
    """Run simulation across all plants, return network-level results + derived utilizations."""
    result = run_network(req.duration_hours, req.seed, req.plant_ids)
    report = analyze_network(utilizations=result["utilizations"])
    return {
        "simulation": result,
        "network_analysis": report.to_dict(),
    }


@router.get("/transport/{from_plant}/{to_plant}")
async def get_transport_cost(from_plant: str, to_plant: str):
    """Pallet-level transport cost between two plants."""
    return transport_cost_pallet(from_plant, to_plant)


@router.post("/demand")
async def get_demand_plan(req: DemandRequest):
    plan = generate_demand_plan(
        plant_id=req.plant_id,
        horizon_weeks=req.horizon_weeks,
        seed=req.seed,
    )
    return plan.to_dict()


@router.get("/demand/{plant_id}")
async def get_plant_demand(plant_id: str, weeks: int = 12):
    plan = generate_demand_plan(plant_id=plant_id, horizon_weeks=weeks)
    return plan.to_dict()
