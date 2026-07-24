---
created_at: 2026-07-23T16:36:01.629700+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: MILP min-batch BIG_M must exceed max line throughput per period
source: memory_save_learning
---
# MILP min-batch BIG_M must exceed max line throughput per period

In `nexusfab/optimization/network.py` → `solve_milp()`, the min-batch activation constraint pairs:
- `x[s,l,t] >= min_batch[s] * w[s,l,t]`
- `x[s,l,t] <= BIG_M * w[s,l,t]`

BIG_M must be **at least as large as the maximum possible production per (line, period)**, not just `max(min_batch) * N`. For NexusFab, the fastest line runs at 700 units/min (PLT-001-L4 CANNING = 42,000 uph). Over a full 168h week that's ~7M units. Using `max(min_batch) * 50 = 1.5M` would be **too small** and silently tighten the feasible region.

**Pattern used:**
```python
BIG_M = max(prob.line_speed_uph.values()) * 168.0 * 1.5   # ~10.6M units
```

**Why it matters:** A BIG_M that's too tight acts as an implicit capacity cap on the production variable, causing the solver to under-produce or return INFEASIBLE even when demand is satisfiable. The solver won't warn you — it just finds a wrong (tighter) optimum.

**Related:** The inventory balance equality constraint uses `init_inv[sku] = safety_stock * 1.5` as a starting buffer so period-1 demand can be met from inventory without forcing expensive OT. Without this buffer, the model may declare INFEASIBLE for high-demand opening periods.

**Outcome:** With correct BIG_M, the 34-SKU × 17-line × 4-period MILP (464 binary vars) solves to OPTIMAL in ~0.7s via CBC, achieving 12.9% cost reduction vs greedy baseline (within the 8-15% target range).
