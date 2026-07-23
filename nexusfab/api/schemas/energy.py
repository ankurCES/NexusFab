from typing import Any

from pydantic import BaseModel, ConfigDict


class EnergyReport(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "period_days": 30, "total_kwh": 84000.0, "total_cost": 12600.0, "total_co2_kg": 37800.0, "kwh_per_ton": 700.0}},
    )
    plant_id: str | None = None
    period_days: int | None = None
    total_kwh: float | None = None
    total_cost: float | None = None
    total_co2_kg: float | None = None
    kwh_per_ton: float | None = None


class EnergyOptimizeResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "baseline_cost": 12600.0, "optimized_cost": 10800.0, "savings_pct": 14.3, "schedule": []}},
    )
