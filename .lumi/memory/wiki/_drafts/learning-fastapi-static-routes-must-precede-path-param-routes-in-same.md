---
created_at: 2026-07-23T14:19:37.612992+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: FastAPI static routes must precede path-param routes in same router
source: memory_save_learning
---
# FastAPI static routes must precede path-param routes in same router

In `nexusfab/api/routers/spares.py`, the `/api/spares/alerts` and `/api/spares/pooling` GET routes must be registered **before** `/api/spares/{plant_id}` — FastAPI matches routes in registration order, and a `{plant_id}` path param will swallow `alerts` and `pooling` as literal plant IDs if it comes first.

This is a classic FastAPI gotcha when mixing static segments and path parameters under the same prefix. The fix is route ordering (static first, parameterized last), not path validation or regex constraints.

Also notable: the `spare_parts.py` optimization module uses a `_service_level_for_class()` function that bumps A-class parts +4% and B-class +2% above the base service level (capped at 0.99). This means at base=0.95, A parts already hit 0.99 — so comparing safety stock totals between SL=0.95 and SL=0.99 at the per-plant level can show zero difference if most parts are A-class. The z-score math is correct; the apparent "no difference" is just integer rounding on small demand quantities. Future tests should use high-demand synthetic inputs (e.g., `_safety_stock(100.0, 28, sl)`) to verify the service-level gradient.
