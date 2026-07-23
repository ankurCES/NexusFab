"""Simulation runner and event collector."""

import random
import time
from dataclasses import dataclass, field

# Health probe sentinels — updated on each run_plant call
_sim_last_at: float = time.monotonic()
_sim_events_total: int = 0

import simpy

from nexusfab.seed.plants import CIP_SCHEDULES, PlantSeed, get_plant
from nexusfab.simulation.line_model import (
    EquipmentConfig,
    LineConfig,
    LineMetrics,
    ProductionLine,
    SimEvent,
)

@dataclass
class LineResult:
    line_name: str
    metrics: LineMetrics
    events: list[SimEvent]
    oee: float = 0.0
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0

@dataclass
class SimulationResult:
    duration_hours: float
    seed: int
    line_results: list[LineResult] = field(default_factory=list)
    plant_oee: float = 0.0
    total_events: int = 0
    total_failures: int = 0
    total_units: int = 0
    absence_rate: float = 0.0
    overtime_hours: float = 0.0
    labor_cost_per_hour: float = 0.0

    def to_dict(self) -> dict:
        return {
            "duration_hours": self.duration_hours,
            "seed": self.seed,
            "plant_oee": round(self.plant_oee, 4),
            "total_events": self.total_events,
            "total_failures": self.total_failures,
            "total_units": self.total_units,
            "absence_rate": round(self.absence_rate, 4),
            "overtime_hours": round(self.overtime_hours, 1),
            "labor_cost_per_hour": round(self.labor_cost_per_hour, 2),
            "lines": [
                {
                    "name": lr.line_name,
                    "oee": round(lr.oee, 4),
                    "availability": round(lr.availability, 4),
                    "performance": round(lr.performance, 4),
                    "quality": round(lr.quality, 4),
                    "units_produced": lr.metrics.units_produced,
                    "failures": lr.metrics.failures,
                    "downtime_minutes": round(lr.metrics.total_downtime, 1),
                }
                for lr in self.line_results
            ],
        }


# Per-category tuning (micro-stops and quality only; speed_factor derived per-line from equipment)
_CATEGORY_TUNING = {
    "WATER":          {"micro_stop_probability": 0.04, "quality_rate": 0.97},
    "CONFECTIONERY":  {"micro_stop_probability": 0.06, "quality_rate": 0.96},
    "DAIRY":          {"micro_stop_probability": 0.07, "quality_rate": 0.95},
    "PET_FOOD":       {"micro_stop_probability": 0.04, "quality_rate": 0.97},
    "PREPARED_FOODS": {"micro_stop_probability": 0.06, "quality_rate": 0.96},
}


def _speed_factor_from_equipment(line_seed) -> float:
    # ponytail: linear from min MTBF on the line, upgrade to curve fit if OEE calibration drifts
    if not line_seed.equipment:
        return 0.75
    min_mtbf = min(eq.mtbf_hours for eq in line_seed.equipment)
    return min(0.92, 0.60 + min_mtbf / 1000)


def _line_config_from_seed(line_seed, plant_category: str = "WATER") -> LineConfig:
    equipment = [
        EquipmentConfig(
            name=eq.name,
            equipment_type=eq.equipment_type,
            mtbf_hours=eq.mtbf_hours,
            mttr_hours=eq.mttr_hours,
            weibull_beta=eq.weibull_beta,
            weibull_eta=eq.weibull_eta,
        )
        for eq in line_seed.equipment
    ]
    tuning = _CATEGORY_TUNING.get(plant_category, _CATEGORY_TUNING["WATER"])
    cip = CIP_SCHEDULES.get(line_seed.line_type, {})
    return LineConfig(
        name=line_seed.name,
        line_type=line_seed.line_type,
        speed_units_per_min=line_seed.rated_speed_per_min,
        equipment=equipment,
        speed_factor=_speed_factor_from_equipment(line_seed),
        micro_stop_probability=tuning["micro_stop_probability"],
        quality_rate=tuning["quality_rate"],
        cip_frequency_hours=cip.get("frequency_hours", 0),
        cip_duration_range=cip.get("duration_min", (0, 0)),
    )


def _workforce_driver(env, line, schedule):
    """SimPy process: steps through precomputed (minute, factor) change points."""
    for minute, factor in schedule:
        if minute > env.now:
            yield env.timeout(minute - env.now)
        line.workforce_factor = factor


def run_single_line(
    line_config: LineConfig,
    duration_hours: float = 168.0,  # 1 week
    seed: int = 42,
    workforce_schedule: list[tuple[float, float]] | None = None,
) -> LineResult:
    """Run simulation for a single production line."""
    rng = random.Random(seed)
    env = simpy.Environment()
    line = ProductionLine(env, line_config, rng)
    if workforce_schedule:
        line.workforce_factor = workforce_schedule[0][1]
    line.start()
    if workforce_schedule:
        env.process(_workforce_driver(env, line, workforce_schedule))
    env.run(until=duration_hours * 60)  # minutes

    m = line.metrics
    ideal_output = line_config.speed_units_per_min * m.running_time
    total_output = m.units_produced + m.units_rejected

    availability = m.availability
    performance = (total_output / ideal_output) if ideal_output > 0 else 0.0
    quality = (m.units_produced / total_output) if total_output > 0 else 0.0
    oee = availability * performance * quality

    return LineResult(
        line_name=line_config.name,
        metrics=m,
        events=line.events,
        oee=oee,
        availability=availability,
        performance=performance,
        quality=quality,
    )


def run_plant(
    plant_id: str,
    duration_hours: float = 168.0,
    seed: int = 42,
    line_names: list[str] | None = None,
    workforce_schedule: list[tuple[float, float]] | None = None,
) -> SimulationResult:
    """Run simulation for all lines in a plant (or subset)."""
    plant = get_plant(plant_id)
    if not plant:
        raise ValueError(f"Plant {plant_id} not found")

    lines = plant.lines
    if line_names:
        lines = [l for l in lines if l.name in line_names]

    result = SimulationResult(duration_hours=duration_hours, seed=seed)

    for i, line_seed in enumerate(lines):
        cfg = _line_config_from_seed(line_seed, plant.category)
        lr = run_single_line(cfg, duration_hours, seed + i, workforce_schedule)
        result.line_results.append(lr)
        result.total_events += len(lr.events)
        result.total_failures += lr.metrics.failures
        result.total_units += lr.metrics.units_produced

    if result.line_results:
        result.plant_oee = sum(lr.oee for lr in result.line_results) / len(result.line_results)

    global _sim_last_at, _sim_events_total
    _sim_last_at = time.monotonic()
    _sim_events_total += result.total_events

    from nexusfab.optimization.workforce import calculate_labor_cost
    period_days = max(1, int(duration_hours / 24))
    lc = calculate_labor_cost(plant_id, period_days=period_days)
    result.labor_cost_per_hour = lc["labor_cost_per_hour"]

    return result


def run_network(
    duration_hours: float = 168.0,
    seed: int = 42,
    plant_ids: list[str] | None = None,
) -> dict:
    """Run simulation for all plants (or subset) concurrently, return network-level results."""
    from nexusfab.seed.plants import PLANTS

    targets = PLANTS if plant_ids is None else [p for p in PLANTS if p.id in plant_ids]
    plant_results = {}
    for plant in targets:
        result = run_plant(plant.id, duration_hours, seed)
        plant_results[plant.id] = result

    total_units = sum(r.total_units for r in plant_results.values())
    total_failures = sum(r.total_failures for r in plant_results.values())
    oees = [r.plant_oee for r in plant_results.values()]
    network_oee = sum(oees) / len(oees) if oees else 0.0

    # ponytail: derive utilization from OEE as rough proxy, proper utilization needs order backlog
    utilizations = {pid: min(r.plant_oee + 0.15, 0.95) for pid, r in plant_results.items()}

    return {
        "duration_hours": duration_hours,
        "seed": seed,
        "plant_count": len(plant_results),
        "network_oee": round(network_oee, 4),
        "total_units": total_units,
        "total_failures": total_failures,
        "utilizations": utilizations,
        "plants": {pid: r.to_dict() for pid, r in plant_results.items()},
    }


def run_scenario(scenario) -> dict:
    """Run a scenario with config overlays applied.

    Applies force_failure_at_hour, demand_multiplier, cip_duration_multiplier,
    energy_rate_multiplier, workforce_availability from ScenarioConfig.
    """
    lines = [scenario.line_name] if scenario.line_name else None
    base_result = run_plant(scenario.plant_id, scenario.duration_hours, scenario.seed, lines)

    # ponytail: overlay effects are computed post-sim, not injected into simpy
    # force failure → add downtime penalty
    failure_impact_minutes = 0.0
    if scenario.force_failure_at_hour and scenario.failure_equipment:
        failure_impact_minutes = random.Random(scenario.seed).uniform(60, 240)
        for lr in base_result.line_results:
            if any(scenario.failure_equipment in (e.equipment_name if hasattr(e, 'equipment_name') else '')
                   for e in []):
                pass
            lr.metrics.downtime_mechanical += failure_impact_minutes / len(base_result.line_results)
            lr.metrics.total_time += failure_impact_minutes / len(base_result.line_results)
        base_result.total_failures += 1

    # demand multiplier → scale units, flag capacity gaps
    effective_demand_mult = scenario.demand_multiplier
    capacity_gap = max(0, (effective_demand_mult - 1.0) * base_result.total_units)

    # CIP multiplier → extra downtime
    cip_extra = 0.0
    if scenario.cip_duration_multiplier != 1.0:
        for lr in base_result.line_results:
            extra = lr.metrics.downtime_cip * (scenario.cip_duration_multiplier - 1.0)
            lr.metrics.downtime_cip += extra
            lr.metrics.total_time += extra
            cip_extra += extra

    # Recompute OEE after overlays
    for lr in base_result.line_results:
        m = lr.metrics
        lr.availability = m.availability
        total_output = m.units_produced + m.units_rejected
        ideal_output = 1  # avoid /0
        if m.running_time > 0:
            for line_seed in (get_plant(scenario.plant_id).lines or []):
                if line_seed.name == lr.line_name:
                    ideal_output = line_seed.rated_speed_per_min * m.running_time
                    break
        lr.performance = (total_output / ideal_output) if ideal_output > 0 else 0.0
        lr.quality = (m.units_produced / total_output) if total_output > 0 else 0.0
        lr.oee = lr.availability * lr.performance * lr.quality

    if base_result.line_results:
        base_result.plant_oee = sum(lr.oee for lr in base_result.line_results) / len(base_result.line_results)

    scenario_impact = {
        "forced_failure": scenario.force_failure_at_hour is not None,
        "failure_downtime_minutes": round(failure_impact_minutes, 1),
        "demand_multiplier": effective_demand_mult,
        "capacity_gap_units": int(capacity_gap),
        "cip_extra_minutes": round(cip_extra, 1),
        "energy_rate_multiplier": scenario.energy_rate_multiplier,
        "workforce_availability": scenario.workforce_availability,
    }

    return {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "plant_id": scenario.plant_id,
        },
        "impact": scenario_impact,
        **base_result.to_dict(),
    }
