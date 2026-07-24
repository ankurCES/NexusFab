---
created_at: 2026-07-23T14:18:00.317193+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Maintenance scheduler uses deterministic sensor sim via md5 hash
source: memory_save_learning
---
# Maintenance scheduler uses deterministic sensor sim via md5 hash

`nexusfab/optimization/maintenance.py` simulates equipment condition sensors (vibration, temperature, current) using `_deterministic_float()` — an md5 hash of `"{equipment_name}:{hours:.1f}:{salt}"` mapped to a float range. This avoids `random.Random` so the same inputs always produce the same readings, which matters because:

- The `__main__` self-check uses assertions on action counts and types; non-determinism would make those flaky.
- The API returns consistent results across calls with the same parameters (no cache-busting surprises for the frontend).
- The existing pattern in `scheduling.py` uses `random.Random(seed)` for sample order generation, but that only works when there's an explicit seed parameter. The maintenance scheduler has no natural seed — it's called with `(plant_id, horizon_days, usage_hours)` — so hashing the equipment identity is the simpler path.

The wear model is `hours_since_pm / mtbf` raised to a power (1.5 for vibration, 1.8 for temperature, 2.0 for current). ISO 10816 thresholds are split into two tiers: Class II `(2.8, 7.1)` for small equipment (fillers, cappers, labelers, packaging) and Class III `(4.5, 11.2)` for large rigid equipment (conveyors, mixers, pasteurizers, homogenizers, dryers). These live in `_VIBRATION_THRESHOLDS`.

The PM grouping in `optimize_maintenance_groups()` uses greedy anchor-and-pull: earliest PM on a line anchors a group, anything within `pull_forward_days` (default 7) joins it. Group duration = `max(individual durations)` since techs work in parallel. This is the function behind `POST /api/maintenance/optimize`.
