"""Maintenance + spare parts API endpoints."""

import hashlib
import random
from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexusfab.api.schemas.maintenance import FailureHistory, MaintenancePrediction, MaintenanceSchedule
from nexusfab.optimization.maintenance import (
    generate_maintenance_schedule,
    optimize_maintenance_groups,
)
from nexusfab.optimization.predictive_maintenance import batch_predict
from nexusfab.optimization.spare_parts import analyze_inventory
from nexusfab.seed.plants import get_plant

_FAILURE_MODES: dict[str, list[str]] = {
    "FILLER": ["valve_leak", "nozzle_clog", "piston_seal_failure"],
    "CAPPER": ["torque_fault", "chuck_slip", "cap_sensor_error"],
    "LABELER": ["print_head_jam", "label_misalign", "sensor_fault"],
    "CONVEYOR": ["belt_slip", "motor_overtemp", "bearing_failure"],
    "MIXER": ["seal_leak", "bearing_wear", "motor_fault"],
    "PACKAGING": ["seal_bar_fault", "film_tension", "cutter_wear"],
    "PASTEURIZER": ["temp_deviation", "flow_fault", "valve_leak"],
    "HOMOGENIZER": ["pressure_fault", "valve_wear", "seal_failure"],
    "DRYER": ["temp_overshoot", "belt_wear", "blower_fault"],
}
_MTTR_RANGE: dict[str, tuple[float, float]] = {
    "minor": (0.5, 4.0), "major": (4.0, 24.0), "critical": (8.0, 72.0),
}
_COST_RANGE: dict[str, tuple[int, int]] = {
    "minor": (200, 2000), "major": (2000, 20000), "critical": (10000, 80000),
}

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


class MaintenanceRequest(BaseModel):
    plant_id: str | None = None
    horizon_days: int = Field(default=30, ge=1, le=365)


class OptimizeRequest(BaseModel):
    plant_id: str | None = None
    horizon_days: int = Field(default=30, ge=1, le=365)
    pull_forward_days: float = Field(default=7.0, ge=1.0, le=30.0)


class InventoryRequest(BaseModel):
    plant_id: str | None = None


@router.post("/schedule", response_model=MaintenanceSchedule, summary="Generate maintenance schedule for a plant or all plants")
async def get_maintenance_schedule(req: MaintenanceRequest):
    schedule = generate_maintenance_schedule(
        plant_id=req.plant_id,
        horizon_days=req.horizon_days,
    )
    return schedule.to_dict()


@router.get("/schedule/{plant_id}", response_model=MaintenanceSchedule, summary="Get maintenance schedule for a specific plant")
async def get_plant_maintenance(plant_id: str, horizon_days: int = 30):
    schedule = generate_maintenance_schedule(plant_id=plant_id, horizon_days=horizon_days)
    return schedule.to_dict()


@router.post("/optimize", response_model=MaintenanceSchedule, summary="Optimize maintenance schedule by grouping tasks to minimize downtime")
async def optimize_schedule(req: OptimizeRequest):
    result = optimize_maintenance_groups(
        plant_id=req.plant_id,
        horizon_days=req.horizon_days,
        pull_forward_days=req.pull_forward_days,
    )
    return result.to_dict()


@router.post("/inventory", response_model=MaintenanceSchedule, summary="Analyze spare parts inventory — ABC-XYZ classification and reorder points")
async def get_inventory_analysis(req: InventoryRequest):
    report = analyze_inventory(plant_id=req.plant_id)
    return report.to_dict()


@router.get("/inventory/{plant_id}", response_model=MaintenanceSchedule, summary="Spare parts inventory analysis for a specific plant")
async def get_plant_inventory(plant_id: str):
    report = analyze_inventory(plant_id=plant_id)
    return report.to_dict()


@router.get("/inventory", response_model=MaintenanceSchedule, summary="Spare parts inventory analysis across all plants")
async def get_all_inventory():
    report = analyze_inventory()
    return report.to_dict()


@router.get("/predictions/{plant_id}", response_model=MaintenancePrediction, summary="ML-based failure predictions with RUL and alert levels")
async def get_predictions(plant_id: str):
    results = batch_predict(plant_id)
    return {
        "plant_id": plant_id,
        "equipment": results,
        "summary": {
            "RED": sum(1 for r in results if r["alert_level"] == "RED"),
            "ORANGE": sum(1 for r in results if r["alert_level"] == "ORANGE"),
            "YELLOW": sum(1 for r in results if r["alert_level"] == "YELLOW"),
            "GREEN": sum(1 for r in results if r["alert_level"] == "GREEN"),
        },
    }


@router.get("/history/{plant_id}", response_model=FailureHistory, summary="Historical failure events with severity and cost breakdown")
async def get_failure_history(plant_id: str, days: int = 90):
    plant = get_plant(plant_id)
    if plant is None:
        return {"plant_id": plant_id, "days": days, "total_events": 0, "events": [], "by_week": []}

    seed = int(hashlib.md5(plant_id.encode()).hexdigest()[:8], 16) % (2**31)
    rng = random.Random(seed)
    equip_list = [(e, ln.name) for ln in plant.lines for e in ln.equipment]

    events: list[dict] = []
    now = datetime.now()
    start = now - timedelta(days=days)
    n_weeks = days // 7

    for week in range(n_weeks):
        for _ in range(rng.randint(1, 4)):
            equip, line_name = rng.choice(equip_list)
            dt = start + timedelta(days=week * 7 + rng.randint(0, 6))
            r = rng.random()
            sev = "minor" if r < 0.5 else ("major" if r < 0.85 else "critical")
            modes = _FAILURE_MODES.get(equip.equipment_type, ["general_fault"])
            mttr_lo, mttr_hi = _MTTR_RANGE[sev]
            cost_lo, cost_hi = _COST_RANGE[sev]
            events.append({
                "date": dt.strftime("%Y-%m-%d"),
                "equipment": equip.name,
                "equipment_type": equip.equipment_type,
                "line": line_name,
                "failure_mode": rng.choice(modes),
                "severity": sev,
                "mttr_hours": round(rng.uniform(mttr_lo, mttr_hi), 1),
                "cost": int(rng.uniform(cost_lo, cost_hi)),
            })

    events.sort(key=lambda e: e["date"], reverse=True)

    by_week_map: dict[int, int] = {}
    for e in events:
        dt = datetime.strptime(e["date"], "%Y-%m-%d")
        wk = (dt - start).days // 7
        by_week_map[wk] = by_week_map.get(wk, 0) + 1

    return {
        "plant_id": plant_id,
        "days": days,
        "total_events": len(events),
        "events": events,
        "by_week": [{"week": f"W{i+1}", "failures": by_week_map.get(i, 0)} for i in range(n_weeks)],
    }
