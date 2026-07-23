"""Energy optimization, scenario builder, and analytics API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexusfab.api.schemas.energy import EnergyOptimizeResult, EnergyReport
from nexusfab.api.schemas.simulation import ScenarioRunResult, SimulationResult
from nexusfab.optimization.energy import analyze_energy, optimize_energy_schedule
from nexusfab.seed.plants import PLANTS
from nexusfab.simulation.runner import run_network, run_plant, run_scenario
from nexusfab.simulation.scenarios import (
    ScenarioConfig,
    get_scenario,
    list_scenarios,
)

router = APIRouter()


# ── Energy optimization ──


class EnergyOptimizeRequest(BaseModel):
    plant_id: str | None = None
    period_days: int = Field(default=30, ge=1, le=365)
    utilization: float = Field(default=0.65, ge=0.1, le=1.0)


@router.post("/api/energy/optimize", response_model=EnergyOptimizeResult, tags=["Energy"], summary="Optimize energy schedule — peak shaving and off-peak load shifting")
async def optimize_energy(req: EnergyOptimizeRequest):
    result = optimize_energy_schedule(
        plant_id=req.plant_id,
        period_days=req.period_days,
        utilization=req.utilization,
    )
    return result.to_dict()


# ── Scenario builder ──


class ScenarioRunRequest(BaseModel):
    scenario_id: str


class CustomScenarioRequest(BaseModel):
    name: str = "Custom Scenario"
    plant_id: str
    line_name: str | None = None
    duration_hours: float = Field(default=168.0, ge=1, le=8760)
    seed: int = 42
    force_failure_at_hour: float | None = None
    failure_equipment: str | None = None
    demand_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)
    cip_duration_multiplier: float = Field(default=1.0, ge=0.5, le=5.0)
    energy_rate_multiplier: float = Field(default=1.0, ge=0.5, le=5.0)
    workforce_availability: float = Field(default=1.0, ge=0.1, le=1.0)


@router.get("/api/scenarios", response_model=list[ScenarioRunResult], tags=["Simulation"], summary="List all seeded what-if scenarios")
async def get_all_scenarios():
    return list_scenarios()


@router.post("/api/scenarios/run", response_model=SimulationResult, tags=["Simulation"], summary="Run a seeded scenario by ID")
async def run_seeded_scenario(req: ScenarioRunRequest):
    scenario = get_scenario(req.scenario_id)
    if not scenario:
        raise HTTPException(404, f"Scenario {req.scenario_id} not found")
    return run_scenario(scenario)


@router.post("/api/scenarios/custom", response_model=SimulationResult, tags=["Simulation"], summary="Run a fully parameterized custom what-if scenario")
async def run_custom_scenario(req: CustomScenarioRequest):
    from nexusfab.seed.plants import get_plant

    if not get_plant(req.plant_id):
        raise HTTPException(404, f"Plant {req.plant_id} not found")
    scenario = ScenarioConfig(
        id="CUSTOM",
        name=req.name,
        description=f"Custom what-if: {req.name}",
        plant_id=req.plant_id,
        line_name=req.line_name,
        duration_hours=req.duration_hours,
        seed=req.seed,
        force_failure_at_hour=req.force_failure_at_hour,
        failure_equipment=req.failure_equipment,
        demand_multiplier=req.demand_multiplier,
        cip_duration_multiplier=req.cip_duration_multiplier,
        energy_rate_multiplier=req.energy_rate_multiplier,
        workforce_availability=req.workforce_availability,
    )
    return run_scenario(scenario)


@router.post("/api/scenarios/run-all", response_model=SimulationResult, tags=["Simulation"], summary="Run all seeded scenarios and return a summary table")
async def run_all_scenarios():
    """Run all 10 seeded scenarios and return summary results."""
    from nexusfab.simulation.scenarios import SCENARIOS

    results = []
    for sc in SCENARIOS:
        r = run_scenario(sc)
        results.append({
            "scenario_id": sc.id,
            "scenario_name": sc.name,
            "plant_id": sc.plant_id,
            "plant_oee": r["plant_oee"],
            "total_units": r["total_units"],
            "total_failures": r["total_failures"],
            "impact": r["impact"],
        })
    return {"count": len(results), "results": results}


# ── Analytics / KPI trending ──


class KpiRequest(BaseModel):
    plant_id: str | None = None
    periods: int = Field(default=6, ge=2, le=24)
    period_hours: float = Field(default=168.0, ge=24, le=720)


@router.post("/api/analytics/kpi", response_model=SimulationResult, tags=["Production"], summary="KPI trends over multiple periods — OEE, energy, waste, OTIF")
async def get_kpi_trending(req: KpiRequest):
    """Generate KPI trends over multiple periods for OEE, energy, production."""
    trending = []
    for i in range(req.periods):
        seed = 42 + i * 7

        if req.plant_id:
            sim = run_plant(req.plant_id, req.period_hours, seed)
            oee = sim.plant_oee
            units = sim.total_units
            failures = sim.total_failures
            energy = analyze_energy(req.plant_id, period_days=int(req.period_hours / 24), seed=seed)
        else:
            net = run_network(req.period_hours, seed)
            oee = net["network_oee"]
            units = net["total_units"]
            failures = net["total_failures"]
            energy = analyze_energy(period_days=int(req.period_hours / 24), seed=seed)

        ed = energy.to_dict()
        # ponytail: OTIF is derived from OEE as proxy, real OTIF needs order tracking
        otif = min(0.98, oee + 0.15)
        waste_pct = (1 - oee) * 0.3  # rough waste proxy

        trending.append({
            "period": i + 1,
            "oee": round(oee, 4),
            "otif": round(otif, 4),
            "waste_pct": round(waste_pct, 4),
            "total_units": units,
            "failures": failures,
            "energy_kwh": ed["total_kwh"],
            "energy_cost": ed["total_cost"],
            "energy_co2_kg": ed["total_co2_kg"],
            "kwh_per_ton": ed["kwh_per_ton"],
        })

    return {
        "plant_id": req.plant_id or "network",
        "periods": req.periods,
        "period_hours": req.period_hours,
        "trending": trending,
    }
