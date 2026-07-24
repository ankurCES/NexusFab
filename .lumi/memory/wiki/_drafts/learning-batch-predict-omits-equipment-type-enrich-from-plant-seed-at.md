---
created_at: 2026-07-23T17:34:51.028884+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: batch_predict() omits equipment_type — enrich from plant seed at API layer
source: memory_save_learning
---
# batch_predict() omits equipment_type — enrich from plant seed at API layer

When calling `nexusfab.optimization.predictive_maintenance.batch_predict(plant_id)`, the returned dicts contain only `equipment_name`, `rul_hours`, `health_index`, `anomaly_score`, `alert_level`, `confidence`, and `top_features` — **no `equipment_type` field**. Any UI component that renders an equipment type abbreviation (e.g. `e.equipment_type.slice(0,3)`) will crash with `Cannot read properties of undefined (reading 'slice')`.

Fix: in the FastAPI endpoint, build a lookup dict from plant seed data and call `r.setdefault("equipment_type", ...)` before returning:

```python
plant = get_plant(plant_id)
if plant:
    equip_types = {e.name: e.equipment_type for ln in plant.lines for e in ln.equipment}
    for r in results:
        r.setdefault("equipment_type", equip_types.get(r["equipment_name"], "UNKNOWN"))
```

This pattern applies any time `batch_predict` output feeds a UI component that needs equipment metadata — always enrich at the endpoint, not in the frontend. The same approach can be used for line assignment, install_date, or any other plant-seed field missing from the ML output dict.
