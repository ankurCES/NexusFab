from typing import Any

from pydantic import BaseModel, ConfigDict


class LivenessResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})
    status: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"status": "ready", "checks": {"db": {"ok": True}, "migrations": {"ok": True, "current": "abc123", "head": "abc123"}}}},
    )
    status: str
    checks: dict[str, Any]


class DetailedHealthResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"status": "ok", "uptime_seconds": 3600.0, "db_pool": {}, "simulation": {"status": "running"}, "plants": [], "memory": {"rss_mb": 128.4}, "last_error": None, "error_count": 0}},
    )
    status: str
    uptime_seconds: float | None = None
    db_pool: dict[str, Any] | None = None
    simulation: dict[str, Any] | None = None
    plants: list[Any] | None = None
    memory: dict[str, Any] | None = None
    last_error: Any = None
    error_count: int | None = None


class ErrorsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"errors": [{"ts": 1720000000.0, "method": "GET", "path": "/api/plants", "status": 404, "detail": "Not found"}], "total_buffered": 1}},
    )
    errors: list[Any]
    total_buffered: int
