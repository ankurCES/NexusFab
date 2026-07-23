"""Seeded simulation scenarios (SIM-001 through SIM-010)."""

from dataclasses import dataclass

@dataclass
class ScenarioConfig:
    id: str
    name: str
    description: str
    plant_id: str
    line_name: str | None = None
    duration_hours: float = 168.0
    seed: int = 42
    # Injection params
    force_failure_at_hour: float | None = None
    failure_equipment: str | None = None
    demand_multiplier: float = 1.0
    cip_duration_multiplier: float = 1.0
    energy_rate_multiplier: float = 1.0
    workforce_availability: float = 1.0

SCENARIOS: list[ScenarioConfig] = [
    ScenarioConfig(
        id="SIM-001",
        name="Bottling Line Filler Failure",
        description="PLT-001-L3 filler failure at t=100hrs → reroute to PLT-001-L5 (same format)",
        plant_id="PLT-001", line_name="PLT-001-L3",
        force_failure_at_hour=100.0, failure_equipment="PLT001-L3-FIL",
        seed=1001,
    ),
    ScenarioConfig(
        id="SIM-002",
        name="Confectionery Line Down During Holiday Peak",
        description="KitKat moulding line down during high demand → cross-plant rerouting",
        plant_id="PLT-002", line_name="PLT-002-L1",
        force_failure_at_hour=48.0, failure_equipment="PLT002-L1-FIL",
        demand_multiplier=4.0, seed=1002,
    ),
    ScenarioConfig(
        id="SIM-003",
        name="Dairy CIP Overrun",
        description="CIP takes 2x expected time → schedule reoptimization",
        plant_id="PLT-003", line_name="PLT-003-L1",
        cip_duration_multiplier=2.0, seed=1003,
    ),
    ScenarioConfig(
        id="SIM-004",
        name="Spare Part Stockout (Filler Seal)",
        description="Filler seal inventory hits zero, 5-day lead time → temp shutdown",
        plant_id="PLT-001", line_name="PLT-001-L2",
        force_failure_at_hour=72.0, failure_equipment="PLT001-L2-FIL",
        seed=1004,
    ),
    ScenarioConfig(
        id="SIM-005",
        name="Demand Spike (Promotional Event)",
        description="3x normal demand across all PLT-001 lines",
        plant_id="PLT-001",
        demand_multiplier=3.0, seed=1005,
    ),
    ScenarioConfig(
        id="SIM-006",
        name="Raw Material Shortage (Cocoa)",
        description="Cocoa supplier delay 4 weeks → confectionery production impact",
        plant_id="PLT-002",
        seed=1006, duration_hours=672.0,  # 4 weeks
    ),
    ScenarioConfig(
        id="SIM-007",
        name="Allergen Cross-Contamination Risk",
        description="Wrong allergen sequencing detected → emergency CIP + schedule correction",
        plant_id="PLT-002", line_name="PLT-002-L3",
        cip_duration_multiplier=1.5, seed=1007,
    ),
    ScenarioConfig(
        id="SIM-008",
        name="Energy Price Spike",
        description="2x peak energy rate → shift energy-intensive ops to off-peak",
        plant_id="PLT-003",
        energy_rate_multiplier=2.0, seed=1008,
    ),
    ScenarioConfig(
        id="SIM-009",
        name="Workforce Shortage (Flu Season)",
        description="15% workforce absent → cross-training deployment + overtime",
        plant_id="PLT-004",
        workforce_availability=0.85, seed=1009,
    ),
    ScenarioConfig(
        id="SIM-010",
        name="Quality Excursion (Fill Weight Drift)",
        description="Sensor detects fill weight drift → line slowdown + recalibration",
        plant_id="PLT-001", line_name="PLT-001-L1",
        seed=1010,
    ),
]

def get_scenario(scenario_id: str) -> ScenarioConfig | None:
    return next((s for s in SCENARIOS if s.id == scenario_id), None)

def list_scenarios() -> list[dict]:
    return [
        {"id": s.id, "name": s.name, "description": s.description, "plant_id": s.plant_id}
        for s in SCENARIOS
    ]
