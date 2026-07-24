---
created_at: 2026-07-23T17:37:40.659024+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CIP_SCHEDULES must include CANNING or line-type completeness tests fail
source: memory_save_learning
---
# CIP_SCHEDULES must include CANNING or line-type completeness tests fail

When writing tests that assert all production line types have a CIP schedule (`CIP_SCHEDULES` in `nexusfab/seed/plants.py`), the `CANNING` line type (PLT-001-L4) was absent from the dict even though it appears in the PLANTS seed. This caused `test_cip_schedules.py` to fail immediately.

**Fix**: added `"CANNING": {"frequency_hours": 24, "duration_min": (45, 60), "trigger": "time"}` to `CIP_SCHEDULES`. CANNING is a water-bottling can line — no allergen or UHT constraint, so 24h interval mirrors GLASS_BOTTLING.

**Pattern to watch**: `CIP_SCHEDULES` is a manually maintained dict keyed by `line_type` strings. When a new line type is added to `PLANTS`, it must also be added here — there is no runtime enforcement. A guard like `assert set(CIP_SCHEDULES) >= {l.line_type for p in PLANTS for l in p.lines}` at module bottom would catch this automatically.

**Also found**: pre-existing `tests/test_spare_parts.py` imported `_abc_classify` which had been renamed to `_abc_simple` (single-value) and `_abc_classify_list` (batch). Fixed the test to use `_abc_simple(annual_value)` directly. The function signature changed from `(value, qty)` → `(annual_value)` — callers must pre-multiply.
