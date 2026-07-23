"""Workforce + energy API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.energy import analyze_energy
from nexusfab.optimization.workforce import generate_workforce

router = APIRouter(tags=["workforce-energy"])


class WorkforceRequest(BaseModel):
    plant_id: str | None = None


class EnergyRequest(BaseModel):
    plant_id: str | None = None
    period_days: int = Field(default=30, ge=1, le=365)
    utilization: float = Field(default=0.65, ge=0.1, le=1.0)


@router.get("/api/workforce/{plant_id}")
async def get_plant_workforce(plant_id: str):
    report = generate_workforce(plant_id=plant_id)
    return report.to_dict()


@router.get("/api/workforce")
async def get_all_workforce():
    report = generate_workforce()
    return report.to_dict()


@router.get("/api/energy/{plant_id}")
async def get_plant_energy(plant_id: str, days: int = 30):
    report = analyze_energy(plant_id=plant_id, period_days=days)
    return report.to_dict()


@router.get("/api/energy")
async def get_all_energy(days: int = 30):
    report = analyze_energy(period_days=days)
    return report.to_dict()


@router.post("/api/energy/analyze")
async def analyze_energy_custom(req: EnergyRequest):
    report = analyze_energy(
        plant_id=req.plant_id,
        period_days=req.period_days,
        utilization=req.utilization,
    )
    return report.to_dict()
