---
created_at: 2026-07-23T17:27:33.986104+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'SSE streaming endpoint: declare literal-segment routes before param routes at same depth'
source: memory_save_learning
---
# SSE streaming endpoint: declare literal-segment routes before param routes at same depth

In `nexusfab/api/routers/sensors.py`, the SSE route `/api/sensors/stream/{plant_id}` and the history route `/api/sensors/{equipment_id}/history` both sit at path depth 3 under `/api/sensors/`. FastAPI matches routes in declaration order for paths at the same depth, so **the stream route must be declared first** — before any route like `/{plant_id}/{line_id}` — otherwise a URL like `/api/sensors/stream/PLT-001` would match `{equipment_id}/history` or `{plant_id}/{line_id}` incorrectly.

Concretely: in `router.routes`, `stream/{plant_id}` appears first and FastAPI prefers literal path segments (`stream`) over path parameters, but only when the literal-route is registered first.

The same applies to `/api/sensors/{plant_id}/{line_id}/equipment` vs `/api/sensors/{plant_id}/{line_id}/{equipment_id}` — `equipment` (literal at position 4) must be declared before the all-parameter variant or FastAPI won't match the literal.

**Pattern**: when mixing literal + parametric routes at the same path depth in a FastAPI router with no shared prefix, always declare the most-specific (most literals) routes first.

**What would break without this**: `/api/sensors/stream/PLT-001` would 404 (wrong path param match), breaking the `EventSource` in `Sensors.tsx` (`useEffect` that opens `new EventSource('/api/sensors/stream/${plant}')`) and killing the live indicator.
