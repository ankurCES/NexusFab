"""Spare parts inventory API — GET /api/spares/{plant_id}, GET /api/spares/alerts, POST /api/spares/reorder."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.api.schemas.spares import AlertsResponse, PoolingResponse, ReorderResponse, SparesReport
from nexusfab.optimization.spare_parts import (
    analyze_inventory,
    cross_plant_pooling,
    generate_alerts,
    generate_reorder,
)

router = APIRouter(prefix="/api/spares", tags=["Maintenance"])


class ReorderRequest(BaseModel):
    plant_id: str | None = None
    parts: list[str] | None = Field(default=None, description="Filter to specific part names")
    service_level: float = Field(default=0.95, ge=0.95, le=0.99)


# Static paths first — FastAPI matches in registration order
@router.get("/alerts", response_model=AlertsResponse, summary="Active spare parts alerts — stockouts and critical low-stock items")
async def get_alerts(plant_id: str | None = None):
    alerts = generate_alerts(plant_id)
    return {
        "total_alerts": len(alerts),
        "critical": sum(1 for a in alerts if a.severity == "critical"),
        "warning": sum(1 for a in alerts if a.severity == "warning"),
        "alerts": [a.to_dict() for a in alerts],
    }


@router.get("/pooling", response_model=PoolingResponse, summary="Cross-plant spare parts pooling candidates — potential inventory reductions")
async def get_pooling(service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    candidates = cross_plant_pooling(service_level)
    return {
        "total_candidates": len(candidates),
        "total_savings_units": sum(c.savings_units for c in candidates),
        "candidates": [c.to_dict() for c in candidates],
    }


@router.post("/reorder", response_model=ReorderResponse, summary="Generate reorder actions based on EOQ and safety stock calculations")
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


@router.get("/status/{plant_id}", response_model=SparesReport, summary="Full spare parts status with days-to-stockout for a plant")
async def get_spares_status(plant_id: str, service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    report = analyze_inventory(plant_id=plant_id, service_level=service_level)
    parts = []
    for p in report.parts:
        d = p.to_dict()
        daily = p.annual_demand / 365.0 if p.annual_demand > 0 else 0.001
        d["days_to_stockout"] = round(p.qty_on_hand / daily, 1)
        parts.append(d)
    return {**report.to_dict(), "parts": parts}


# Path param routes last
@router.get("/", response_model=SparesReport, summary="Spare parts inventory analysis across all plants")
async def get_all_spares(service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    report = analyze_inventory(service_level=service_level)
    return report.to_dict()


@router.get("/{plant_id}", response_model=SparesReport, summary="Spare parts inventory analysis for a specific plant")
async def get_plant_spares(plant_id: str, service_level: float = 0.95):
    service_level = max(0.95, min(0.99, service_level))
    report = analyze_inventory(plant_id=plant_id, service_level=service_level)
    return report.to_dict()
