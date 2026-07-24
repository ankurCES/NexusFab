---
created_at: 2026-07-23T16:06:52.437879+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CIP class requirements keyed by allergen tier pair, not product pair
source: memory_save_learning
---
# CIP class requirements keyed by allergen tier pair, not product pair

The 5-tier CIP class system in `nexusfab/seed/products.py` uses `CIP_CLASS_REQUIREMENTS[(from_tier, to_tier)]` — a 5×5 matrix of `(cip_class, duration_min, validation_method)` tuples — to determine CIP requirements for allergen transitions. This is **separate from** the per-plant changeover matrices `_CHANGEOVER_MATRICES` which are keyed by product tier strings like `("nut_choc", "plain_choc")`.

Key design decisions:
- `compute_allergen_tier(allergens)` derives tier from max severity in `ALLERGEN_TIER_MAP` — no stored field to go stale.
- `ProductSeed.allergen_tier` is computed via `__post_init__`, always consistent with `allergens` list.
- `_CIP_VALIDATION_TIME` dict adds LFD (15 min) and ELISA (30 min) hold times on top of changeover matrix durations in `get_changeover_info()`.
- `check_allergen_sequence()` in `regulatory.py` uses the tier-based lookup, NOT the old ad-hoc severity sum formula.

Gotcha: the changeover matrices already encode CIP type in their entries (e.g. `("nut_choc", "plain_choc"): (120.0, CIP_DEEP_CLEAN)`). The validation time is added ON TOP in `get_changeover_info()`. So `nut→plain` = 120 (matrix) + 30 (ELISA hold) = 150 min total. Don't double-count by also adding CIP duration from `CIP_CLASS_REQUIREMENTS`.
