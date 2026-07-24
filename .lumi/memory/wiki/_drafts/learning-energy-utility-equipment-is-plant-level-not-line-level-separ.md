---
created_at: 2026-07-23T16:43:56.420423+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Energy utility equipment is plant-level, not line-level — separate mapping needed
source: memory_save_learning
---
# Energy utility equipment is plant-level, not line-level — separate mapping needed

In `nexusfab/optimization/energy.py`, line-level equipment (FILLER, MIXER, etc.) lives on `PlantSeed.lines[].equipment` and gets iterated via the plant seed data. But plant-level utilities (COMPRESSOR, REFRIGERATION, CIP_HEATER, HVAC, SPRAY_DRYER, COOLING_TOWER, VACUUM_PUMP, BOILER) are **not** in the line/equipment hierarchy — they're shared infrastructure.

These are tracked in a separate `_PLANT_UTILITIES` dict mapping `plant_id → {equipment_type: count}`. Their kW rates go into the same `_ENERGY_RATES` dict as line equipment, but they're consumed differently:

- `load_profile_hourly()` sums them separately from line equipment
- BOILER is gas-only (MMBtu/hr in `_GAS_CONSUMPTION`), contributes 0 electric kW — the `.get(t, 0)` on `_ENERGY_RATES` handles this naturally since BOILER has no entry there
- HVAC is split out for weather-dependent seasonal modulation via `_HVAC_SEASONAL`

If a future task adds utility equipment to the `PlantSeed` data model (making them first-class in the seed hierarchy), `_PLANT_UTILITIES` should be retired and `load_profile_hourly` refactored to pull from the unified source. Until then, any new utility type needs entries in both `_ENERGY_RATES` (or `_GAS_CONSUMPTION` for gas-only) **and** `_PLANT_UTILITIES` per plant.
