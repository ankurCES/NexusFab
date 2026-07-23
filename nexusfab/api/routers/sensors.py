"""Sensor readings, history, and SSE streaming endpoints."""
from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from nexusfab.api.schemas.sensors import EquipmentHealth, EquipmentItem, EquipmentReadingsResponse, SensorHistory
from nexusfab.optimization.predictive_maintenance import batch_predict
from nexusfab.seed.plants import PLANTS, get_plant
# ponytail: importing private names from sensor_stream; add public API if reuse grows
from nexusfab.simulation.sensor_stream import _SENSOR_SETS, _TYPE_MAP, SensorStream

router = APIRouter(tags=["Sensors"])


def _specs_for_type(equipment_type: str) -> dict[str, tuple[float, float, str]]:
    """Return {suffix: (setpoint, sigma, unit)} for an equipment type."""
    key = _TYPE_MAP.get(equipment_type.upper())
    if not key:
        return {}
    return {s.suffix: (s.setpoint, s.sigma, s.unit) for s in _SENSOR_SETS[key]}


def _status(value: float, setpoint: float, sigma: float) -> str:
    dev = abs(value - setpoint)
    if dev > 3 * sigma:
        return "alarm"
    if dev > 2 * sigma:
        return "warning"
    return "normal"


# ── Declare static-segment routes before parametric ones at the same depth ──

@router.get("/api/sensors/stream/{plant_id}", response_class=StreamingResponse, summary="Live SSE sensor stream for all lines in a plant", tags=["Sensors"])
async def stream_sensors(plant_id: str):
    """SSE endpoint — emits live sensor readings every 2s for all lines."""
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")

    async def gen():
        while True:
            readings: dict[str, dict] = {}
            for line in plant.lines:
                try:
                    ss = SensorStream(plant, line.name, batch_size=500, sample_rate_hz=1.0)
                    for batch in ss.stream(1.0):
                        for r in batch:
                            readings[r["tag"]] = r
                except Exception:
                    pass
            payload = json.dumps({
                "plant_id": plant_id,
                "timestamp": time.time(),
                "readings": list(readings.values()),
            })
            yield f"data: {payload}\n\n"
            await asyncio.sleep(2.0)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/sensors/{plant_id}/{line_id}/equipment", response_model=list[EquipmentItem], summary="List equipment on a production line")
async def list_equipment(plant_id: str, line_id: str):
    """List equipment names and types for a line."""
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")
    line = next((l for l in plant.lines if l.name == line_id), None)
    if not line:
        raise HTTPException(404, f"Line {line_id} not found in {plant_id}")
    return [{"name": e.name, "type": e.equipment_type} for e in line.equipment]


@router.get("/api/sensors/{plant_id}/{line_id}/{equipment_id}", response_model=EquipmentReadingsResponse, summary="Current sensor readings for one equipment")
async def get_current_readings(plant_id: str, line_id: str, equipment_id: str):
    """Current sensor readings for one equipment — run 2s of stream, take last per tag."""
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")
    line = next((l for l in plant.lines if l.name == line_id), None)
    if not line:
        raise HTTPException(404, f"Line {line_id} not found")
    equip = next((e for e in line.equipment if e.name == equipment_id), None)
    if not equip:
        raise HTTPException(404, f"Equipment {equipment_id} not found")

    ss = SensorStream(plant, line_id, batch_size=500, sample_rate_hz=1.0)
    latest: dict[str, dict] = {}
    for batch in ss.stream(2.0):
        for r in batch:
            parts = r["tag"].split(".")
            if len(parts) >= 3 and parts[2] == equipment_id:
                latest[r["tag"]] = r

    specs = _specs_for_type(equip.equipment_type)
    readings = []
    for tag, r in latest.items():
        suffix = tag.split(".")[-1]
        setpoint, sigma, unit = specs.get(suffix, (r["value"], r["value"] * 0.05 or 0.1, r["unit"]))
        readings.append({
            "tag": tag,
            "sensor_type": suffix,
            "value": r["value"],
            "unit": unit,
            "setpoint": setpoint,
            "sigma": sigma,
            "quality": r["quality"],
            "status": _status(r["value"], setpoint, sigma),
        })

    return {
        "plant_id": plant_id,
        "line_id": line_id,
        "equipment_id": equipment_id,
        "equipment_type": equip.equipment_type,
        "timestamp": time.time(),
        "readings": readings,
    }


@router.get("/api/sensors/{equipment_id}/history", response_model=SensorHistory, summary="Time-series sensor history for one equipment")
async def get_sensor_history(equipment_id: str, hours: int = 24):
    """Time-series sensor history for one equipment, sampled at 5–60 min intervals."""
    target_plant = target_line = target_equip = None
    for plant in PLANTS:
        for line in plant.lines:
            for equip in line.equipment:
                if equip.name == equipment_id:
                    target_plant, target_line, target_equip = plant, line, equip
                    break

    if not target_plant:
        raise HTTPException(404, f"Equipment {equipment_id} not found")

    # Downsample based on window size to keep response manageable
    if hours >= 720:
        sample_hz = 1.0 / 3600.0   # 1 per hour → 720 pts
    elif hours >= 168:
        sample_hz = 1.0 / 1800.0   # 1 per 30 min → 336 pts
    else:
        sample_hz = 1.0 / 300.0    # 1 per 5 min → 288 pts

    duration = float(hours * 3600)
    start_wall = time.time() - duration

    ss = SensorStream(target_plant, target_line.name, batch_size=2000, sample_rate_hz=sample_hz)
    by_tag: dict[str, dict] = {}

    for batch in ss.stream(duration):
        for r in batch:
            parts = r["tag"].split(".")
            if len(parts) >= 3 and parts[2] == equipment_id:
                tag = r["tag"]
                if tag not in by_tag:
                    by_tag[tag] = {"unit": r["unit"], "data": []}
                by_tag[tag]["data"].append({
                    "ts": round(start_wall + r["timestamp"], 3),
                    "value": r["value"],
                    "quality": r["quality"],
                })

    specs = _specs_for_type(target_equip.equipment_type)
    series = []
    failure_events = []

    for tag, info in by_tag.items():
        suffix = tag.split(".")[-1]
        setpoint, sigma, _ = specs.get(suffix, (0.0, 1.0, ""))
        for pt in info["data"]:
            dev = round(min(1.0, abs(pt["value"] - setpoint) / max(sigma * 3, 1e-9)), 3) if setpoint else 0.0
            pt["deviation"] = dev
            if pt["quality"] == "BAD":
                failure_events.append({"timestamp": pt["ts"], "tag": tag, "type": "bad_quality"})
        series.append({
            "tag": tag,
            "sensor_type": suffix,
            "unit": info["unit"],
            "setpoint": setpoint,
            "sigma": sigma,
            "data": info["data"],
        })

    return {
        "equipment_id": equipment_id,
        "equipment_type": target_equip.equipment_type,
        "hours": hours,
        "series": series,
        "failure_events": failure_events[:10],
    }


@router.get("/api/maintenance/health/{plant_id}", response_model=EquipmentHealth, summary="Equipment health index and RUL per plant", tags=["Maintenance"])
async def get_health_summary(plant_id: str):
    """Equipment health summary — health index, RUL, alert level per equipment."""
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")
    return {"plant_id": plant_id, "equipment": batch_predict(plant_id)}
