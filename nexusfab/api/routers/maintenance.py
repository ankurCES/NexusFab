"""Maintenance + spare parts API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.maintenance import generate_maintenance_schedule
from nexusfab.optimization.spare_parts import analyze_inventory

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class MaintenanceRequest(BaseModel):
    plant_id: str | None = None
    horizon_days: int = Field(default=30, ge=1, le=365)


class InventoryRequest(BaseModel):
    plant_id: str | None = None


@router.post("/schedule")
async def get_maintenance_schedule(req: MaintenanceRequest):
    schedule = generate_maintenance_schedule(
        plant_id=req.plant_id,
        horizon_days=req.horizon_days,
    )
    return schedule.to_dict()


@router.get("/schedule/{plant_id}")
async def get_plant_maintenance(plant_id: str, horizon_days: int = 30):
    schedule = generate_maintenance_schedule(plant_id=plant_id, horizon_days=horizon_days)
    return schedule.to_dict()


@router.post("/inventory")
async def get_inventory_analysis(req: InventoryRequest):
    report = analyze_inventory(plant_id=req.plant_id)
    return report.to_dict()


@router.get("/inventory/{plant_id}")
async def get_plant_inventory(plant_id: str):
    report = analyze_inventory(plant_id=plant_id)
    return report.to_dict()


@router.get("/inventory")
async def get_all_inventory():
    report = analyze_inventory()
    return report.to_dict()
