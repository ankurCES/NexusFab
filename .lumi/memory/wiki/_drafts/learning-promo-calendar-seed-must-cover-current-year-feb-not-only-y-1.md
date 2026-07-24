---
created_at: 2026-07-23T16:23:40.603506+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Promo calendar seed must cover current-year Feb, not only y+1
source: memory_save_learning
---
# Promo calendar seed must cover current-year Feb, not only y+1

When building `PromotionCalendar.seed(base_year)` in `nexusfab/optimization/demand.py`, the Super Bowl promotion was initially seeded only at `datetime(y+1, 2, 1)` (next Feb). For a 12-month window starting Jan `y`, this left the current February uncovered — the event never fired in the chart.

**Fix**: seed *both* `datetime(y, 2, 1)` and `datetime(y+1, 2, 1)` so the calendar is self-contained for any 12-month window anchored at Jan 1 of `base_year`. Events outside the active `generate_demand_plan` horizon are simply ignored because `is_active()` guards on the exact week range.

**Pattern applies broadly**: any annual event (Super Bowl, summer campaigns, fiscal-year promos) that recurs in February must be included for the current year too — not just "next year". The `_PLANT_CATEGORY` module-level dict (also new in this task, keyed off `PLANTS`) avoids repeated list scans inside `apply_promotions`; it's the right idiom for any hot-path category lookup derived from seed data.

**Ramp shapes** in `PromotionEvent.ramp_factor()`: NPL uses hard breakpoints (20%→60%→100%); seasonal uses linear edge-ramps capped at 4 weeks. Both ramp shapes are conditioned on `promo_type` — adding a new type requires a new branch here.

**Pre-build units** are computed as `weekly_forecast × lift_pct / pre_build_weeks`, stored on `DemandForecast.pre_build_units` (additive across overlapping events). They represent extra production needed *before* the promo window to build inventory — consumers should sum `forecast_units + pre_build_units` for production scheduling.
