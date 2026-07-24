---
created_at: 2026-07-23T14:54:04.174617+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CP-SAT optional intervals are the rerouting primitive, not CBC MIP
source: memory_save_learning
---
# CP-SAT optional intervals are the rerouting primitive, not CBC MIP

When a NexusFab production line breaks down and a job must move to an alternate machine, the correct solver primitive is **OR-Tools CP-SAT `NewOptionalIntervalVar`** with a `BoolVar` presence literal — not a PuLP/CBC MIP with big-M binary variables.

Pattern (from `docs/research/energy-workforce-simulation.md`, Section 4.3):
```python
presence_a = model.NewBoolVar(f"presence_a_{job_id}_{task_id}")
presence_b = model.NewBoolVar(f"presence_b_{job_id}_{task_id}")
model.Add(presence_a + presence_b == 1)
interval_a = model.NewOptionalIntervalVar(start, dur_a, end, presence_a, "iv_a")
interval_b = model.NewOptionalIntervalVar(start, dur_b, end, presence_b, "iv_b")
```

To lock out a broken machine: force its presence literals to 0 and re-solve. CP-SAT re-solves a 20-job, 5-machine instance in seconds (with `max_time_in_seconds=30` and 8 workers).

**Why it matters:** PuLP/CBC handles blending LPs and single-plant lot-sizing fine (< 500 binary vars), but degrades badly on pure scheduling MIPs. CP-SAT uses constraint propagation + clause learning and is purpose-built for combinatorial scheduling — it consistently beats CBC at equivalent problem sizes. The decision rule: LP/blending → PuLP+HiGHS; scheduling MIP → CP-SAT.

**Also noted:** SimPy `PreemptiveResource` is needed only if breakdown *interrupts* an active job mid-run. For most food-plant lines (complete the batch, then go down), a regular `Resource` with `_capacity = 0` trick suffices and avoids the interrupt-handling complexity.
