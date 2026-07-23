from typing import Any

from pydantic import BaseModel, ConfigDict


class MaintenancePrediction(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "equipment": [], "summary": {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 10}}},
    )
    plant_id: str
    equipment: list[Any]
    summary: dict[str, int]


class MaintenanceSchedule(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "horizon_days": 30, "tasks": [], "total_tasks": 12, "grouped_tasks": 8}},
    )
    plant_id: str | None = None
    horizon_days: int | None = None


class FailureEventEntry(BaseModel):
    date: str
    equipment: str
    equipment_type: str
    line: str
    failure_mode: str
    severity: str
    mttr_hours: float
    cost: int


class WeeklyCount(BaseModel):
    week: str
    failures: int


class FailureHistory(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"plant_id": "PLANT01", "days": 90, "total_events": 47, "events": [], "by_week": [{"week": "W1", "failures": 3}]}},
    )
    plant_id: str
    days: int
    total_events: int
    events: list[FailureEventEntry]
    by_week: list[WeeklyCount]
