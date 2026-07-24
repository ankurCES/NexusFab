---
created_at: 2026-07-23T14:39:18.455920+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Energy optimization uses post-sim overlay, not simpy injection
source: memory_save_learning
---
# Energy optimization uses post-sim overlay, not simpy injection

The scenario runner in `nexusfab/simulation/runner.py::run_scenario()` applies scenario config overlays (force failure, demand multiplier, CIP multiplier, energy rate) as **post-simulation adjustments** to the `SimulationResult`, not by injecting them into the simpy environment. This means:

- `force_failure_at_hour` adds downtime penalty after the sim completes, not by triggering a simpy event at that hour. The failure downtime is distributed across line results.
- `cip_duration_multiplier` only affects lines that already have CIP downtime from the base sim — if no CIP events fired, the multiplier produces zero extra minutes.
- `demand_multiplier` computes a capacity gap from base units, not by changing production targets mid-sim.

**Why this matters**: If a future agent needs _precise_ scenario injection (e.g., "filler fails at exactly hour 100 and repair takes X"), they'd need to modify the simpy `EquipmentProcess._lifecycle()` to accept an injection schedule. The current approach is a deliberate ponytail shortcut — good enough for what-if comparison dashboards, not for exact event replay.

**Files**: `nexusfab/simulation/runner.py` (function `run_scenario`), `nexusfab/simulation/scenarios.py` (ScenarioConfig dataclass), `nexusfab/api/routers/energy_scenarios.py` (API surface).
