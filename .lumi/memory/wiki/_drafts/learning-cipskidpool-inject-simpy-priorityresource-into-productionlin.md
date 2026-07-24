---
created_at: 2026-07-23T16:22:58.937329+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'CIPSkidPool: inject SimPy PriorityResource into ProductionLine, not global'
source: memory_save_learning
---
# CIPSkidPool: inject SimPy PriorityResource into ProductionLine, not global

**Pattern**: `CIPSkidPool` wraps `simpy.PriorityResource` and is injected into `ProductionLine.__init__` as an optional arg (`cip_pool=None`). Lines call `pool.skid_for(line_type)` to get either the dedicated (UHT/ASEPTIC) or shared resource, then do a normal `yield req` inside `_cip()`.

**File**: `nexusfab/simulation/line_model.py`

**Key decisions**:
1. `PriorityResource` (not `Resource`) is required so UHT hard-deadline CIPs (`priority=1`) jump the shared queue ahead of scheduled (`2`) and changeover (`3`) CIPs.
2. PLT-003's dedicated skid is a *second* `PriorityResource(capacity=1)` stored alongside `self.shared`. `skid_for()` routes UHT/ASEPTIC lines there and everything else to shared — no special-casing elsewhere.
3. `pool.hours_in_use` is accumulated *inside* `_cip()` after `yield timeout`, so it only counts actual CIP time (not queue wait). `utilization()` divides by `(shared.capacity + dedicated_capacity) * sim_hours`.
4. Food-safety violation fires when `env.now - _last_cip_end > 12h*60` **after** the skid is granted (not when requested) — that's when the product is actually exposed beyond limit.
5. `cip_queue_wait_total` / `cip_queue_count` live on `LineMetrics`; aggregate KPI is computed post-sim. PLT-002 (1 skid, 3 lines, 8h interval) produces ~52 min average wait — well above the 15 min target, which is the expected result for that config and serves as a contention stress test.

**Why it matters**: injecting the pool (vs. a global) keeps line tests fully independent — pass `cip_pool=None` and the old behavior is preserved exactly. All 41 existing tests continue to pass unchanged.
