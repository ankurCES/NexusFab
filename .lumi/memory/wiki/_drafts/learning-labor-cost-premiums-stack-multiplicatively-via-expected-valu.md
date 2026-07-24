---
created_at: 2026-07-23T16:24:28.890204+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Labor cost premiums stack multiplicatively via expected-value factoring
source: memory_save_learning
---
# Labor cost premiums stack multiplicatively via expected-value factoring

When computing labor costs with multiple independent premium categories (shift differential, weekend/holiday, overtime), the stacking is multiplicative: a Sunday night OT hour costs `base × 1.10 × 1.25 × 1.50`. Rather than enumerating all 36 combinations or running Monte Carlo, the total factors cleanly because the categories are independent:

```
total = base_sum × E[shift] × E[day] × E[ot]
```

where each `E[x]` is the weighted average multiplier for that category (e.g., `E[shift] = 2/3 × 1.0 + 1/3 × 1.10`). This is O(1) per role, exact, and makes premium attribution straightforward as marginal removals.

Implemented in `nexusfab/optimization/workforce.py:calculate_labor_cost()`. The `PLANT_COL` dict applies cost-of-living adjustments that scale linearly with the burdened rate — the CA/SC ratio should exactly equal `1.15/0.88 ≈ 1.307`, which the `__main__` self-check asserts.

`labor_cost_per_hour` is derived as `total / (period_days × 24)` and is injected into `SimulationResult` via `nexusfab/simulation/runner.py:run_plant()` (lazy import to avoid circular deps).
