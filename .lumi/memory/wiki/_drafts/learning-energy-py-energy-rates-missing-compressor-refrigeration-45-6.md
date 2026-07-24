---
created_at: 2026-07-23T14:51:56.889786+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: energy.py _ENERGY_RATES missing compressor/refrigeration — 45-60% of plant load
source: memory_save_learning
---
# energy.py _ENERGY_RATES missing compressor/refrigeration — 45-60% of plant load

## Finding

`nexusfab/optimization/energy.py` `_ENERGY_RATES` (lines 14–24) models 9 equipment types but omits the two largest consumers in dairy and pet food plants: **compressed-air compressors** (~110 kWh/hr) and **refrigeration/chiller banks** (~140 kWh/hr). These two types collectively account for 45–60% of plant energy in PLT-003 (dairy) and PLT-004 (pet food).

## Gap

Without these types, `analyze_energy()` and `optimize_energy_schedule()` will underestimate total plant kWh and produce `kwh_per_ton` values well below the research-validated range (dairy: 60–120 kWh/t). The off-peak shift savings calculation in `optimize_energy_schedule()` also misses refrigeration, which is the most practical DR/shift candidate (can reduce compressor setpoint 1–2°C for 30 min without food safety impact).

## Recommended additions to `_ENERGY_RATES`

```python
"COMPRESSOR":   110.0,
"REFRIGERATION": 140.0,
"CIP_HEATER":    55.0,
"HVAC":          35.0,
"EXTRUDER":      70.0,
```

## Second gap: demand charges not modelled

`_ENERGY_COSTS` charges only per-kWh. Industrial bills carry demand charges ($8–$22/kW/month) that represent 30–50% of actual cost. The biggest optimization lever — staggering equipment startups to avoid 15-min peak intervals — is invisible in the current model. Research doc: `docs/research/energy-workforce-simulation.md`, Section 2.3.
