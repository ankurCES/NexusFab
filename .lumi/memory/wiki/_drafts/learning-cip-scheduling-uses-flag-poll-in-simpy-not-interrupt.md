---
created_at: 2026-07-23T15:57:44.131210+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CIP scheduling uses flag-poll in SimPy, not interrupt
source: memory_save_learning
---
# CIP scheduling uses flag-poll in SimPy, not interrupt

The CIP scheduling in `nexusfab/simulation/line_model.py` uses a **flag-poll pattern** rather than SimPy process interrupts. A `_cip_scheduler` process sets `self._cip_due = True` at the configured `cip_frequency_hours` interval, and the `_produce` loop checks this flag at the top of each 1-minute tick.

**Why this matters:** SimPy interrupts (`process.interrupt()`) require try/except handling in the target process and complicate the failure-repair flow already in `_produce`. The flag approach keeps the production loop's yield chain simple — CIP is handled before the next failure check, introducing at most ~1 minute of scheduling jitter. For hard-constraint lines (UHT ≤ 12h, ASEPTIC ≤ 8h), the nominal frequency is set below the ceiling (10h and 8h respectively), so the 1-min jitter is negligible.

**Key files:**
- `nexusfab/seed/plants.py`: `CIP_SCHEDULES` dict — 14 line types with `frequency_hours`, `duration_min` range, and `trigger` reason
- `nexusfab/simulation/line_model.py`: `LineConfig.cip_frequency_hours` / `cip_duration_range`, `_cip_scheduler()`, `_do_scheduled_cip()`, and the flag check in `_produce`
- `nexusfab/simulation/runner.py`: `_line_config_from_seed` wires `CIP_SCHEDULES` into `LineConfig`

**Gotcha:** CIP event counts in a 168h sim are slightly below `168 / freq` because CIP duration itself consumes sim time, pushing the next trigger later. Tests use `expected - 1` tolerance for this reason.
