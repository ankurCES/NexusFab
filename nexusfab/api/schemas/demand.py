from typing import Any

from pydantic import BaseModel, ConfigDict


class DemandPlan(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "horizon_weeks": 12, "forecasts": [], "total_demand_units": 480000, "mape": 0.28, "service_level": 0.95}},
    )
    plant_id: str | None = None
    horizon_weeks: int | None = None
