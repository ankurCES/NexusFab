"""Workforce scheduling + energy + regulatory compliance API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.api.schemas.energy import EnergyReport
from nexusfab.api.schemas.workforce import AllergenCheckResult, WorkforceReport
from nexusfab.optimization.energy import analyze_energy
from nexusfab.optimization.regulatory import (
    check_allergen_sequence,
    generate_compliance_report,
)
from nexusfab.optimization.workforce import generate_workforce

router = APIRouter()


class WorkforceRequest(BaseModel):
    plant_id: str | None = None


class EnergyRequest(BaseModel):
    plant_id: str | None = None
    period_days: int = Field(default=30, ge=1, le=365)
    utilization: float = Field(default=0.65, ge=0.1, le=1.0)


# ── Workforce ──


@router.get("/api/workforce/{plant_id}", response_model=WorkforceReport, tags=["Workforce"], summary="Workforce schedule and labor cost for a specific plant")
async def get_plant_workforce(plant_id: str):
    report = generate_workforce(plant_id=plant_id)
    return report.to_dict()


@router.get("/api/workforce", response_model=WorkforceReport, tags=["Workforce"], summary="Workforce schedule and labor cost across all plants")
async def get_all_workforce():
    report = generate_workforce()
    return report.to_dict()


# ── Energy ──


@router.get("/api/energy/{plant_id}", response_model=EnergyReport, tags=["Energy"], summary="Energy consumption, cost, and CO₂ for a specific plant")
async def get_plant_energy(plant_id: str, days: int = 30):
    report = analyze_energy(plant_id=plant_id, period_days=days)
    return report.to_dict()


@router.get("/api/energy", response_model=EnergyReport, tags=["Energy"], summary="Energy consumption, cost, and CO₂ across all plants")
async def get_all_energy(days: int = 30):
    report = analyze_energy(period_days=days)
    return report.to_dict()


@router.post("/api/energy/analyze", response_model=EnergyReport, tags=["Energy"], summary="Energy analysis with custom period and utilization parameters")
async def analyze_energy_custom(req: EnergyRequest):
    report = analyze_energy(
        plant_id=req.plant_id,
        period_days=req.period_days,
        utilization=req.utilization,
    )
    return report.to_dict()


# ── Regulatory compliance ──


@router.get("/api/compliance/{plant_id}", response_model=WorkforceReport, tags=["Compliance"], summary="Regulatory compliance report — shift adherence and workforce rules")
async def get_plant_compliance(plant_id: str, days: int = 7):
    report = generate_compliance_report(plant_id=plant_id, days=days)
    return report.to_dict()


@router.get("/api/compliance", response_model=WorkforceReport, tags=["Compliance"], summary="Regulatory compliance report across all plants")
async def get_all_compliance(days: int = 7):
    report = generate_compliance_report(days=days)
    return report.to_dict()


@router.get("/api/compliance/allergen-check", response_model=AllergenCheckResult, tags=["Compliance"], summary="Check allergen conflict and required CIP class for an SKU-to-SKU changeover")
async def allergen_check(from_sku: str, to_sku: str):
    result = check_allergen_sequence(from_sku, to_sku)
    return result.to_dict()
