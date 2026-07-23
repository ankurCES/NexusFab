"""Network + demand planning API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.demand import generate_demand_plan
from nexusfab.optimization.network import analyze_network

router = APIRouter(prefix="/api/network", tags=["network"])


class NetworkRequest(BaseModel):
    utilizations: dict[str, float] | None = None
    oee_values: dict[str, float] | None = None


class DemandRequest(BaseModel):
    plant_id: str | None = None
    horizon_weeks: int = Field(default=12, ge=1, le=52)
    seed: int = 42


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
