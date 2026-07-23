"""Workforce scheduling + energy + regulatory compliance API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.energy import analyze_energy
from nexusfab.optimization.regulatory import (
    check_allergen_sequence,
    generate_compliance_report,
)
from nexusfab.optimization.workforce import generate_workforce

router = APIRouter(tags=["workforce-energy"])


class WorkforceRequest(BaseModel):
    plant_id: str | None = None


class EnergyRequest(BaseModel):
    plant_id: str | None = None
    period_days: int = Field(default=30, ge=1, le=365)
    utilization: float = Field(default=0.65, ge=0.1, le=1.0)


# ── Workforce ──


@router.get("/api/workforce/{plant_id}")
async def get_plant_workforce(plant_id: str):
    report = generate_workforce(plant_id=plant_id)
    return report.to_dict()


@router.get("/api/workforce")
async def get_all_workforce():
    report = generate_workforce()
    return report.to_dict()


# ── Energy ──


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


# ── Regulatory compliance ──


@router.get("/api/compliance/{plant_id}")
async def get_plant_compliance(plant_id: str, days: int = 7):
    report = generate_compliance_report(plant_id=plant_id, days=days)
    return report.to_dict()


@router.get("/api/compliance")
async def get_all_compliance(days: int = 7):
    report = generate_compliance_report(days=days)
    return report.to_dict()


@router.get("/api/compliance/allergen-check")
async def allergen_check(from_sku: str, to_sku: str):
    result = check_allergen_sequence(from_sku, to_sku)
    return result.to_dict()
