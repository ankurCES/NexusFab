---
created_at: 2026-07-23T16:45:33.320792+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'ABC-XYZ spare parts: percentile ABC needs two-pass _build_parts'
source: memory_save_learning
---
# ABC-XYZ spare parts: percentile ABC needs two-pass _build_parts

**Pattern:** `_abc_classify_list()` in `nexusfab/optimization/spare_parts.py` does percentile-based ABC (top 20% item count = A, next 30% = B, bottom 50% = C). This requires a **two-pass** approach in `_build_parts`: collect all (equipment_type, part_name, annual_demand) in Pass 1, call `_abc_classify_list(annual_values)` to get labels, then compute SS/EOQ/ROP in Pass 2 using the assigned class.

**Why it matters:** The old single-pass used hardcoded absolute thresholds (`annual_value > 5000 → A`). Absolute thresholds silently mis-classify as the catalog grows or cost ranges change — a $6,000 motor spare and a $5,100 gasket set both land in A even if motors are the only true A item. Percentile ranking is catalog-invariant.

**XYZ formula:** `_xyz_classify(cv)` — CV < 0.5 = X, 0.5–1.0 = Y, ≥ 1.0 = Z. CV values per part type are embedded in `_GENERIC_CATALOG` (`SparePartsCatalog.cv`), and per equipment type in `_EQUIPMENT_CV`. Motors/Drives (CV=1.4) and Pump Assemblies (CV=1.1) land in Z, bearings (CV=0.45) in X.

**Safety stock formula** upgraded from the simplified `z × σ × √(LT/365)` to the full research §3.2 formula: `z × sqrt(LT × σ_d² + d_avg² × σ_LT²)`, implemented in `_safety_stock(d_avg_daily, lead_time_days, sl, cv)`. The old formula was dimensionally inconsistent (mixing annual sigma with sqrt of fractional years).

**Policy SS multiplier:** `_SS_POLICY_MULT` applies `AZ → 3×` safety stock (critical buffer), `BZ/CZ → 0` (order-on-demand). Managed in `_apply_policy_ss(ss, abc_xyz)`.

**Cross-plant pooling** retains `_abc_simple()` with absolute thresholds — it only needs a coarse "is this worth pooling?" filter, not the full relative ranking.
