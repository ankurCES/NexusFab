---
created_at: 2026-07-23T17:11:01.385052+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Production Gantt: changeover blocks are end-to-start gaps, not metadata fields'
source: memory_save_learning
---
# Production Gantt: changeover blocks are end-to-start gaps, not metadata fields

When building the production Gantt chart from `generate_schedule()` output (`nexusfab/optimization/scheduling.py`), changeover blocks must be inferred from the **time gap** between consecutive runs on the same line — not from `ScheduledRun.changeover_minutes` alone.

Concrete pattern in `nexusfab/api/routers/production.py`:
```python
if i > 0:
    prev = runs[i - 1]
    gap_start = prev.end_time
    gap_end = r.start_time       # scheduler parks start_time AFTER changeover
    if gap_end > gap_start:      # gap only exists when SKUs differ
        _, cip_type = get_changeover_info(prev.sku, r.sku)
        blocks.append({"type": "changeover", "cip_type": cip_type, ...})
```

Key facts:
- `ScheduledRun.start_time` is the production start (changeover already completed); the gap `[prev.end_time, r.start_time]` IS the changeover window.
- Same-SKU consecutive runs have no gap — `gap_end == gap_start`, so the `if gap_end > gap_start` guard is essential to avoid zero-width changeover blocks.
- CIP type comes from `get_changeover_info(from_sku, to_sku)` in `nexusfab/seed/products.py`, returning one of `none`, `rinse`, `standard`, `allergen`, `deep_clean`.
- CONFECTIONERY (PLT-002) is the best demo plant for the optimizer — allergen-tier asymmetry yields ~38% changeover reduction vs WATER/DAIRY where all products share one tier.

If you instead treat `changeover_minutes` as a duration to subtract from `start_time`, you create a phantom production-start offset that double-counts the changeover window.
