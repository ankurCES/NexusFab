from typing import Any

from pydantic import BaseModel, ConfigDict


class SimulationResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "plant_oee": 0.782, "total_units": 45000, "total_failures": 12, "line_results": [], "impact": {}}},
    )
    plant_id: str | None = None
    plant_oee: float | None = None
    total_units: int | None = None
    total_failures: int | None = None


class ScenarioSummary(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"id": "PEAK_DEMAND", "name": "Peak Demand Surge", "description": "...", "plant_id": "PLANT01", "duration_hours": 168.0}},
    )


class ScenarioRunResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"scenario": "PEAK_DEMAND", "scenario_name": "Peak Demand Surge", "plant_oee": 0.74, "total_units": 42000}},
    )
    scenario: str | None = None
    scenario_name: str | None = None
