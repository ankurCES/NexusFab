---
created_at: 2026-07-23T14:25:54.692703+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Demand endpoints live in both /api/network and /api/demand routers
source: memory_save_learning
---
# Demand endpoints live in both /api/network and /api/demand routers

The original demand forecast endpoints (`POST /api/network/demand`, `GET /api/network/demand/{plant_id}`) were added inside `nexusfab/api/routers/network.py` alongside the network-analysis routes. The P4 task added a dedicated `nexusfab/api/routers/demand.py` router with `GET /api/demand/forecast/{plant_id}` and `POST /api/demand/plan` — these expose the enhanced `generate_demand_plan()` with MAPE, safety stock, and MTS/MTO parameters.

Both sets of endpoints call `nexusfab.optimization.demand.generate_demand_plan()`, but the `/api/network/demand` routes use the old 2-param signature (plant_id + horizon_weeks) while `/api/demand/plan` exposes all six params (target_mape, service_level, lead_time_weeks). The old network routes still work because the new params have defaults — but a future cleanup should remove the duplicates from `network.py` to avoid confusion.

Key files:
- `nexusfab/optimization/demand.py` — core logic, `_SEASONALITY` constants, `_safety_stock()`, `_fulfillment_type()`
- `nexusfab/api/routers/demand.py` — new dedicated router
- `nexusfab/api/routers/network.py` — still has legacy demand endpoints
- `nexusfab/api/router.py` — demand_router registered before network_router (static routes before path-param routes per FastAPI convention)
