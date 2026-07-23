from typing import Any

from pydantic import BaseModel, ConfigDict


class TrendPoint(BaseModel):
    date: str
    score: float


class ComplianceScore(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"plant_id": "PLANT01", "score": 94.2, "food_safety_score": 96.1, "allergen_score": 93.5, "documentation_score": 92.8, "trend": []}},
    )
    plant_id: str
    score: float
    food_safety_score: float
    allergen_score: float
    documentation_score: float
    trend: list[TrendPoint]


class CCPStatus(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "ccps": [{"id": "CCP-PLANT01-PST", "name": "Pasteurisation Temp", "parameter": "Temperature", "unit": "°C", "current_value": 76.3, "status": "PASS", "compliance_rate_30d": 98.5}]}},
    )
    plant_id: str
    ccps: list[Any]


class AllergenMatrix(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "allergens": ["GLUTEN", "DAIRY", "NUTS"], "products": []}},
    )
    plant_id: str
    allergens: list[str]
    products: list[Any]


class CIPEvent(BaseModel):
    id: str
    line: str
    line_type: str
    type: str
    status: str
    scheduled_start: str
    actual_start: str | None = None
    duration_minutes: int
    is_uht_aseptic: bool
    hard_deadline: str | None = None


class CIPSchedule(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"plant_id": "PLANT01", "events": [{"id": "CIP-PLANT01-LINE_A-0001", "line": "LINE_A", "type": "FULL_CIP", "status": "completed", "duration_minutes": 75}]}},
    )
    plant_id: str
    events: list[CIPEvent]
