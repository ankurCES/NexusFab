from typing import Any

from pydantic import BaseModel, ConfigDict


class SensorReading(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"tag": "PLANT01.LINE_A.FILLER01.temp", "sensor_type": "temp", "value": 72.3, "unit": "°C", "setpoint": 72.0, "sigma": 0.5, "quality": "GOOD", "status": "normal"}},
    )
    tag: str
    sensor_type: str
    value: float
    unit: str
    setpoint: float
    sigma: float
    quality: str
    status: str


class EquipmentItem(BaseModel):
    name: str
    type: str


class EquipmentReadingsResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "line_id": "LINE_A", "equipment_id": "FILLER01", "equipment_type": "FILLER", "timestamp": 1720000000.0, "readings": []}},
    )
    plant_id: str
    line_id: str
    equipment_id: str
    equipment_type: str
    timestamp: float
    readings: list[SensorReading]


class SensorDataPoint(BaseModel):
    ts: float
    value: float
    quality: str
    deviation: float | None = None


class SensorSeries(BaseModel):
    tag: str
    sensor_type: str
    unit: str
    setpoint: float
    sigma: float
    data: list[SensorDataPoint]


class SensorHistory(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"equipment_id": "FILLER01", "equipment_type": "FILLER", "hours": 24, "series": [], "failure_events": []}},
    )
    equipment_id: str
    equipment_type: str
    hours: int
    series: list[SensorSeries]
    failure_events: list[Any]


class EquipmentHealth(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "equipment": [{"equipment": "FILLER01", "equipment_type": "FILLER", "health_index": 0.82, "rul_hours": 320.0, "alert_level": "GREEN"}]}},
    )
    plant_id: str
    equipment: list[Any]
