from typing import Any

from pydantic import BaseModel, ConfigDict


class ScheduleResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "runs": [], "total_changeover_minutes": 320.0}},
    )


class RerouteResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "line_name": "LINE_A", "product_sku": "SKU001", "alternative_lines": [], "recommendation": "Reroute to LINE_B"}},
    )
