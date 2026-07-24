---
created_at: 2026-07-23T17:07:39.394015+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Compliance allergen matrix: MAY_CONTAIN is plant-level cross-contamination, not line-level'
source: memory_save_learning
---
# Compliance allergen matrix: MAY_CONTAIN is plant-level cross-contamination, not line-level

In `nexusfab/api/routers/compliance.py` (`get_allergens`), the allergen matrix uses a **plant-level** cross-contamination model: if _any_ product at the plant contains allergen X, then every other product at that plant that doesn't explicitly contain X is marked "MAY CONTAIN" rather than "FREE". This mirrors real HACCP practice — shared lines, shared air, shared cleaning cycles mean all products share the risk.

The key set is built once:
```python
plant_allergen_set: set[str] = set()
for prod in plant_products:
    plant_allergen_set.update(prod.allergens)
```

Then per-product per-allergen:
- `CONTAINS` if explicitly in `prod.allergens`  
- `MAY_CONTAIN` if in `plant_allergen_set` (but not prod's own list)
- `FREE` only if the whole plant is free of that allergen

**Why it matters:** PLT-004 (Pet Food) and PLT-001 (Water) produce allergen-free products, so they get all `FREE` — that's correct. PLT-002 (Confectionery) has NUTS products alongside DAIRY-only products, so even `CON-AER` (Dairy only) shows `MAY_CONTAIN` for GLUTEN, NUTS, EGGS. Without this model, the allergen matrix would be misleading and could fail a HACCP audit.

The CIP changeover class (`CLASS_A/B/C`) is derived from `prod.allergen_tier` deltas — see `nexusfab/seed/products.py` `ALLERGEN_TIER_MAP` for tier assignments. Going high→low tier or allergen→clean always requires CLASS_A (full CIP).
