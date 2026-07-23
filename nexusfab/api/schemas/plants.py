from pydantic import BaseModel, ConfigDict


class LineInfo(BaseModel):
    id: str
    name: str
    line_type: str
    speed_units_per_min: float
    status: str


class PlantSummary(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"id": "PLANT01", "name": "Alpha Dairy", "location": "Manchester", "category": "DAIRY", "capacity_tons_per_day": 120.0, "status": "active", "line_count": 4}},
    )
    id: str
    name: str
    location: str
    category: str
    capacity_tons_per_day: float
    status: str
    line_count: int


class PlantDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"id": "PLANT01", "name": "Alpha Dairy", "location": "Manchester", "category": "DAIRY", "capacity_tons_per_day": 120.0, "status": "active", "line_count": 4, "lines": []}},
    )
    id: str
    name: str
    location: str
    category: str
    capacity_tons_per_day: float
    status: str
    line_count: int | None = None
    lines: list[LineInfo] | None = None
