---
created_at: 2026-07-23T15:59:15.462503+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Demand plan lead times keyed by category bottleneck material
source: memory_save_learning
---
# Demand plan lead times keyed by category bottleneck material

`nexusfab/optimization/demand.py` now uses per-category lead times instead of a flat `lead_time_weeks=2.0`. The mapping chain is:

1. `RAW_MATERIAL_LEAD_TIMES` dict — 10 materials with `domestic_days`, `import_days`, `storage` regime (from `supply-chain-demand.md` §5.2)
2. `_CATEGORY_BOTTLENECK` dict — maps each plant category (WATER, CONFECTIONERY, etc.) to its slowest raw material
3. `_material_lead_time_weeks(category)` — resolves the chain, preferring domestic sourcing unless import-only (e.g. cocoa)

Key values: WATER→pet_preforms (1.5w), CONFECTIONERY→cocoa (10w, import-only), DAIRY→tetra_pak (3.5w), PET_FOOD→vitamin_premix (3.5w), PREPARED_FOODS→spice_blend (1.5w).

`HOLDING_COSTS` dict maps storage regimes (ambient/cool/chilled/frozen) to `(min, max)` $/pallet/week ranges.

Each `DemandForecast` now carries `lead_time_days` and `primary_material` fields so downstream consumers (safety stock, network optimization) can reason about per-product supply chain timing without re-deriving the mapping.

The `lead_time_weeks` parameter on `generate_demand_plan()` is preserved as a fallback for categories not in `_CATEGORY_BOTTLENECK` — callers don't break.
