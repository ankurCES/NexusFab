from typing import Any

from pydantic import BaseModel, ConfigDict


class SparesReport(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "parts": [], "total_parts": 24, "critical_parts": 3}},
    )
    plant_id: str | None = None


class AlertsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"total_alerts": 5, "critical": 2, "warning": 3, "alerts": []}},
    )
    total_alerts: int
    critical: int
    warning: int
    alerts: list[Any]


class PoolingResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"total_candidates": 8, "total_savings_units": 42, "candidates": []}},
    )
    total_candidates: int
    total_savings_units: int
    candidates: list[Any]


class ReorderResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"total_actions": 6, "total_cost": 14500.0, "urgent": 2, "actions": []}},
    )
    total_actions: int
    total_cost: float
    urgent: int
    actions: list[Any]
