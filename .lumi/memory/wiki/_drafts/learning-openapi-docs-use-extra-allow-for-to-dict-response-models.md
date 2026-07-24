---
created_at: 2026-07-23T17:43:56.184758+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'OpenAPI docs: use extra=''allow'' for .to_dict() response models'
source: memory_save_learning
---
# OpenAPI docs: use extra='allow' for .to_dict() response models

When adding `response_model` to FastAPI endpoints that return `obj.to_dict()` from complex optimization/simulation objects, use `model_config = ConfigDict(extra='allow')` on the Pydantic model. Without it, FastAPI strips any field not declared in the model, silently breaking responses. This pattern works for all endpoints where the full `.to_dict()` shape is unknown or variable — declare only the known key fields and let extra fields pass through. Applied across all 14 schema files in `nexusfab/api/schemas/`.

Concrete example from `nexusfab/api/schemas/maintenance.py`:
```python
class MaintenanceSchedule(BaseModel):
    model_config = ConfigDict(extra="allow")
    plant_id: str | None = None
    horizon_days: int | None = None
    # actual .to_dict() returns 20+ more fields — extra='allow' passes them all
```

Counter-pattern: for endpoints with fully known response shapes (e.g. `LivenessResponse`, `ProductionKPIs`), declare all fields strictly without `extra='allow'` so OpenAPI shows complete documentation.

Also: SSE streaming endpoints cannot use `response_model` — use `response_class=StreamingResponse` instead so FastAPI/OpenAPI records the response type without attempting JSON serialization.
