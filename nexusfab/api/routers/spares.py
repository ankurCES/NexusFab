"""Spare parts inventory API — GET /api/spares/{plant_id}, GET /api/spares/alerts, POST /api/spares/reorder."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.optimization.spare_parts import (
    analyze_inventory,
    cross_plant_pooling,
    generate_alerts,
    generate_reorder,
)

router = APIRouter(prefix="/api/spares", tags=["spares"])


class ReorderRequest(BaseModel):
    plant_id: str | None = None
    parts: list[str] | None = Field(default=None, description="Filter to specific part names")
    service_level: float = Field(default=0.95, ge=0.95, le=0.99)


# Static paths first — FastAPI matches in registration order
@router.get("/alerts")
async def get_alerts(plant_id: str | None = None):
    alerts = generate_alerts(plant_id)
    return {
        "total_alerts": len(alerts),
        "critical": sum(1 for a in alerts if a.severity == "critical"),
        "warning": sum(1 for a in alerts if a.severity == "warning"),
        "alerts": [a.to_dict() for a in alerts],
    }


@router.get("/pooling")
async def get_pooling(service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    candidates = cross_plant_pooling(service_level)
    return {
        "total_candidates": len(candidates),
        "total_savings_units": sum(c.savings_units for c in candidates),
        "candidates": [c.to_dict() for c in candidates],
    }


@router.post("/reorder")
async def post_reorder(req: ReorderRequest):
    actions = generate_reorder(
        plant_id=req.plant_id,
        parts_filter=req.parts,
        service_level=req.service_level,
    )
    return {
        "total_actions": len(actions),
        "total_cost": round(sum(a.total_cost for a in actions), 2),
        "urgent": sum(1 for a in actions if a.priority == "urgent"),
        "actions": [a.to_dict() for a in actions],
    }


# Path param routes last
@router.get("/")
async def get_all_spares(service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    report = analyze_inventory(service_level=service_level)
    return report.to_dict()


@router.get("/{plant_id}")
async def get_plant_spares(plant_id: str, service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    report = analyze_inventory(plant_id=plant_id, service_level=service_level)
    return report.to_dict()
