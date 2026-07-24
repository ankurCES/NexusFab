---
created_at: 2026-07-23T16:17:10.722649+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Workforce schedule uses precomputed hourly change points, not per-minute
source: memory_save_learning
---
# Workforce schedule uses precomputed hourly change points, not per-minute

The SimPy workforce integration in `nexusfab/simulation/workforce_sim.py` precomputes a `list[tuple[float, float]]` schedule of `(sim_minute, workforce_factor)` at hourly granularity via `build_workforce_schedule()`. A lightweight `_workforce_driver` process in `runner.py` steps through these change points, setting `ProductionLine.workforce_factor` at each boundary.

This design was chosen over per-minute callbacks because:
- 672 change points (4 weeks) is trivial vs 40,320 per-minute checks
- The schedule is plant-level (shared across all lines), computed once before sim start
- `workforce_factor` on `ProductionLine` is a plain mutable float — `_produce()` reads it every minute-tick, so the effect is smooth enough

Key integration points:
- `line_model.py`: `workforce_factor` defaults to 1.0; `_produce()` multiplies `speed_factor * workforce_factor` for units; stops line (`downtime_short_staffed`) when factor ≤ 0
- `runner.py`: `run_single_line()` accepts optional `workforce_schedule`, sets initial factor before `line.start()` to avoid first-tick race
- `workforce_sim.py`: `run_plant_with_workforce()` orchestrates roster → absenteeism → schedule → `run_plant()`

The `_consecutive_days_for_crew` helper does an O(14 × roster) scan per hour — ponytail-tagged for upgrade if profiling flags it.
