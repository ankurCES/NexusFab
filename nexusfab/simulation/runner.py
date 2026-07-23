"""Simulation runner and event collector."""

import random
from dataclasses import dataclass, field

import simpy

from nexusfab.seed.plants import PlantSeed, get_plant
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

    def to_dict(self) -> dict:
        return {
            "duration_hours": self.duration_hours,
            "seed": self.seed,
            "plant_oee": round(self.plant_oee, 4),
            "total_events": self.total_events,
            "total_failures": self.total_failures,
            "total_units": self.total_units,
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


def _line_config_from_seed(line_seed) -> LineConfig:
    equipment = [
        EquipmentConfig(
            name=eq.name,
            equipment_type=eq.equipment_type,
            mtbf_hours=eq.mtbf_hours,
            mttr_hours=eq.mttr_hours,
        )
        for eq in line_seed.equipment
    ]
    return LineConfig(
        name=line_seed.name,
        line_type=line_seed.line_type,
        speed_units_per_min=line_seed.speed_units_per_min,
        equipment=equipment,
    )


def run_single_line(
    line_config: LineConfig,
    duration_hours: float = 168.0,  # 1 week
    seed: int = 42,
) -> LineResult:
    """Run simulation for a single production line."""
    rng = random.Random(seed)
    env = simpy.Environment()
    line = ProductionLine(env, line_config, rng)
    line.start()
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
        cfg = _line_config_from_seed(line_seed)
        lr = run_single_line(cfg, duration_hours, seed + i)
        result.line_results.append(lr)
        result.total_events += len(lr.events)
        result.total_failures += lr.metrics.failures
        result.total_units += lr.metrics.units_produced

    if result.line_results:
        result.plant_oee = sum(lr.oee for lr in result.line_results) / len(result.line_results)

    return result


# ponytail: scenario injection is dict-based config overlay, added in scenarios.py
