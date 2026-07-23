from typing import Any

from pydantic import BaseModel, ConfigDict


class OEEResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"line": "LINE_A", "oee": 0.782, "availability": 0.91, "performance": 0.87, "quality": 0.99, "units_produced": 8500}},
    )


class PlantOEE(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "plant_name": "Alpha Dairy", "plant_oee": 0.782, "lines": [], "total_units": 45000, "total_failures": 12}},
    )
    plant_id: str
    plant_name: str
    plant_oee: float
    total_units: int
    total_failures: int
    lines: list[Any]


class DashboardResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"network_oee": 0.779, "plant_count": 5, "plants": []}},
    )
    network_oee: float
    plant_count: int
    plants: list[Any]


class DowntimeParetoEntry(BaseModel):
    line: str
    cause: str
    minutes: float


class DowntimeParetoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"plant_id": "PLANT01", "pareto": [{"line": "LINE_A", "cause": "mechanical", "minutes": 142.5}]}},
    )
    plant_id: str
    pareto: list[DowntimeParetoEntry]


class PlantListItem(BaseModel):
    id: str
    name: str
    location: str
    category: str
    capacity_tons_per_day: float
    line_count: int
    lat: float
    lon: float


class LineListItem(BaseModel):
    name: str
    line_type: str
    speed_units_per_min: float
    equipment_count: int
