---
created_at: 2026-07-23T15:53:39.587086+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: EquipmentSeed uses Weibull η derived from target MTBF, not raw MTBF
source: memory_save_learning
---
# EquipmentSeed uses Weibull η derived from target MTBF, not raw MTBF

`nexusfab/seed/plants.py` `EquipmentSeed` stores `weibull_beta` and `weibull_eta`, with `mtbf_hours` as a computed property (`η·Γ(1+1/β)`). The `_e()` helper accepts a target MTBF and reverse-derives η: `η = mtbf / Γ(1+1/β)`, where β comes from the per-type `WEIBULL_BY_TYPE` dict.

**Why this matters:** A hook reformats `_e()` calls to drop the MTBF argument and use type-level Weibull defaults. This erases per-equipment MTBF differentiation (e.g., PLT-003-L3 filler at 120h vs PLT-001-L4 filler at 200h). If you see `_e()` with only 4 args `(name, type, mttr, pos)`, the per-instance MTBF data is gone — restore it by keeping the 5-arg form `(name, type, mtbf, mttr, pos)`.

**Runner coupling:** `nexusfab/simulation/runner.py` `_speed_factor_from_equipment()` computes per-line speed factor from `min(eq.mtbf_hours)` across the line's equipment. If all equipment of a type shares the same η (no per-instance override), every line with a filler bottleneck gets the same speed factor, which defeats the purpose of per-line OEE calibration.
