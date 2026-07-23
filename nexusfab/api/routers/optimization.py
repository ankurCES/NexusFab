"""Scheduling + rerouting API endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexusfab.api.schemas.optimization import RerouteResult, ScheduleResult
from nexusfab.optimization.rerouting import suggest_reroute
from nexusfab.optimization.scheduling import (
    ProductionOrder,
    generate_sample_orders,
    generate_schedule,
)

router = APIRouter(prefix="/api/optimize", tags=["Production"])


class ScheduleRequest(BaseModel):
    plant_id: str
    n_orders: int = Field(default=20, ge=1, le=200)
    horizon_hours: float = Field(default=168.0, ge=1, le=8760)
    seed: int = 42


class CustomScheduleRequest(BaseModel):
    plant_id: str
    orders: list[dict]
    horizon_hours: float = Field(default=168.0, ge=1, le=8760)


class RerouteRequest(BaseModel):
    plant_id: str
    line_name: str
    product_sku: str
    failure_duration_hours: float = Field(default=8.0, ge=0.5, le=720)
    utilizations: dict[str, float] | None = None


@router.post("/schedule", response_model=ScheduleResult, summary="Generate production schedule from sample orders")
async def create_schedule(req: ScheduleRequest):
    orders = generate_sample_orders(req.plant_id, req.n_orders, req.seed)
    if not orders:
        raise HTTPException(404, f"No products for plant {req.plant_id}")
    result = generate_schedule(req.plant_id, orders, horizon_hours=req.horizon_hours)
    return result.to_dict()


@router.post("/schedule/custom", response_model=ScheduleResult, summary="Generate production schedule from custom orders")
async def create_custom_schedule(req: CustomScheduleRequest):
    orders = []
    for o in req.orders:
        orders.append(ProductionOrder(
            order_id=o["order_id"],
            sku=o["sku"],
            quantity=o["quantity"],
            due_date=datetime.fromisoformat(o["due_date"]),
            priority=o.get("priority", 1),
        ))
    result = generate_schedule(req.plant_id, orders, horizon_hours=req.horizon_hours)
    return result.to_dict()


@router.post("/reroute", response_model=RerouteResult, summary="Suggest alternative lines when a line fails — considers network capacity and transport cost")
async def suggest_line_reroute(req: RerouteRequest):
    try:
        result = suggest_reroute(
            line_name=req.line_name,
            plant_id=req.plant_id,
            product_sku=req.product_sku,
            failure_duration_hours=req.failure_duration_hours,
            current_utilizations=req.utilizations,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result.to_dict()
