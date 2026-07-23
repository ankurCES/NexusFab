"""Simulation API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexusfab.api.schemas.simulation import ScenarioRunResult, SimulationResult
from nexusfab.seed.plants import get_plant
from nexusfab.simulation.runner import _line_config_from_seed, run_plant, run_single_line
from nexusfab.simulation.scenarios import get_scenario, list_scenarios

router = APIRouter(prefix="/api/simulate", tags=["Simulation"])


class SimulateRequest(BaseModel):
    plant_id: str
    line_name: str | None = None
    duration_hours: float = Field(default=168.0, ge=1, le=8760)
    seed: int = 42


class ScenarioRunRequest(BaseModel):
    scenario_id: str
    seed: int | None = None


@router.post("/run", response_model=SimulationResult, summary="Run discrete-event simulation for a plant or single line")
async def run_simulation(req: SimulateRequest):
    plant = get_plant(req.plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {req.plant_id} not found")

    if req.line_name:
        line_seed = next((l for l in plant.lines if l.name == req.line_name), None)
        if not line_seed:
            raise HTTPException(404, f"Line {req.line_name} not found in {req.plant_id}")
        cfg = _line_config_from_seed(line_seed, plant.category)
        lr = run_single_line(cfg, req.duration_hours, req.seed)
        return {
            "type": "single_line",
            "line": lr.line_name,
            "oee": round(lr.oee, 4),
            "availability": round(lr.availability, 4),
            "performance": round(lr.performance, 4),
            "quality": round(lr.quality, 4),
            "units_produced": lr.metrics.units_produced,
            "failures": lr.metrics.failures,
            "downtime_minutes": round(lr.metrics.total_downtime, 1),
            "event_count": len(lr.events),
        }

    result = run_plant(req.plant_id, req.duration_hours, req.seed)
    return result.to_dict()


@router.post("/scenario", response_model=ScenarioRunResult, summary="Run a seeded what-if scenario")
async def run_scenario(req: ScenarioRunRequest):
    scenario = get_scenario(req.scenario_id)
    if not scenario:
        raise HTTPException(404, f"Scenario {req.scenario_id} not found")

    seed = req.seed if req.seed is not None else scenario.seed
    lines = [scenario.line_name] if scenario.line_name else None
    result = run_plant(scenario.plant_id, scenario.duration_hours, seed, lines)
    return {
        "scenario": scenario.id,
        "scenario_name": scenario.name,
        "description": scenario.description,
        **result.to_dict(),
    }


@router.get("/scenarios", response_model=list[ScenarioRunResult], summary="List all available simulation scenarios")
async def get_scenarios():
    return list_scenarios()
