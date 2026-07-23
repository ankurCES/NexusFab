from typing import Any

from pydantic import BaseModel, ConfigDict


class ProductionSchedule(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "days": 7, "start": "2026-07-23T06:00:00", "end": "2026-07-30T06:00:00", "horizon_hours": 168.0, "total_changeover_minutes": 420.5, "lines": []}},
    )
    plant_id: str
    days: int
    start: str
    end: str
    horizon_hours: float
    total_changeover_minutes: float
    lines: list[Any]


class SequencingSolution(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "line_id": "PLANT01-L1", "products": [], "fifo": {"sequence": [], "total_changeover_min": 360.0}, "optimized": {"sequence": [], "total_changeover_min": 288.0}, "changeover_reduction_min": 72.0, "changeover_reduction_pct": 20.0}},
    )
    plant_id: str
    line_id: str
    products: list[Any]
    fifo: Any
    optimized: Any
    changeover_reduction_min: float
    changeover_reduction_pct: float


class ChangeoverEntry(BaseModel):
    from_sku: str
    to_sku: str
    minutes: float
    cip_type: str
    asymmetric: bool


class ChangeoverMatrix(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_category": "DAIRY", "products": [], "matrix": [], "asymmetric_pairs": []}},
    )
    plant_category: str
    products: list[Any]
    matrix: list[ChangeoverEntry]
    asymmetric_pairs: list[Any]


class LineKPI(BaseModel):
    line: str
    oee: float
    availability: float
    performance: float
    quality: float
    right_first_time: float
    changeover_pct: float
    units_produced: int
    units_target: int


class ProductionKPIs(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"plant_id": "PLANT01", "plant_name": "Alpha Dairy", "duration_hours": 168.0, "plant_oee": 0.782, "total_units": 45000, "lines": []}},
    )
    plant_id: str
    plant_name: str
    duration_hours: float
    plant_oee: float
    total_units: int
    lines: list[LineKPI]
