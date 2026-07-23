"""Demand planning API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexusfab.optimization.demand import generate_demand_plan
from nexusfab.seed.plants import get_plant

router = APIRouter(prefix="/api/demand", tags=["demand"])


class DemandPlanRequest(BaseModel):
    plant_id: str | None = None
    horizon_weeks: int = Field(default=12, ge=1, le=52)
    seed: int = 42
    target_mape: float = Field(default=0.35, ge=0.05, le=0.60)
    service_level: float = Field(default=0.95, ge=0.80, le=0.99)
    lead_time_weeks: float = Field(default=2.0, ge=0.5, le=12.0)


@router.get("/forecast/{plant_id}")
async def get_forecast(plant_id: str, weeks: int = 12):
    if not get_plant(plant_id):
        raise HTTPException(404, f"Plant {plant_id} not found")
    plan = generate_demand_plan(plant_id=plant_id, horizon_weeks=weeks)
    return plan.to_dict()


@router.post("/plan")
async def create_demand_plan(req: DemandPlanRequest):
    if req.plant_id and not get_plant(req.plant_id):
        raise HTTPException(404, f"Plant {req.plant_id} not found")
    plan = generate_demand_plan(
        plant_id=req.plant_id,
        horizon_weeks=req.horizon_weeks,
        seed=req.seed,
        target_mape=req.target_mape,
        service_level=req.service_level,
        lead_time_weeks=req.lead_time_weeks,
    )
    return plan.to_dict()
