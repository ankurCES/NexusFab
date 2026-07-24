---
created_at: 2026-07-23T15:50:23.248499+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: EquipmentSeed.mtbf_hours is now a computed property from Weibull β/η
source: memory_save_learning
---
# EquipmentSeed.mtbf_hours is now a computed property from Weibull β/η

`EquipmentSeed` in `nexusfab/seed/plants.py` no longer stores `mtbf_hours` as a plain field — it's a `@property` computed via `η·Γ(1 + 1/β)` from `weibull_beta` and `weibull_eta`. The `WEIBULL_BY_TYPE` dict maps 9 equipment types to (β, η) tuples sourced from `docs/research/maintenance-spare-parts.md` §1.

**Downstream consumers that call `eq.mtbf_hours`** (`maintenance.py`, `spare_parts.py`, `runner.py`, DB seeding) still work transparently since properties look like attributes. But any code that tries to **set** `mtbf_hours` on an `EquipmentSeed` instance will fail — it's read-only.

`line_model.py`'s `EquipmentConfig` has `weibull_eta: float | None = None`. When `None`, `time_to_failure()` derives η from `mtbf_hours` (backward compat for tests/ad-hoc configs). When set, it uses η directly — which is the path taken by `runner.py._line_config_from_seed()`.

Key parameterization note: Python's `random.weibullvariate(alpha, beta)` takes alpha=scale=η, beta=shape=β. The old code computed η from MTBF; the new code passes η through from the seed. Both produce Weibull-distributed TTF, but the new path avoids the Γ-function round-trip.
