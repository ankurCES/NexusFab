---
created_at: 2026-07-23T15:08:43.258533+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'PdM ML ladder: Weibull first, LSTM only if RMSE > 20% of mean RUL'
source: memory_save_learning
---
# PdM ML ladder: Weibull first, LSTM only if RMSE > 20% of mean RUL

Documented in `docs/research/maintenance-spare-parts.md` §6.5.2.

**Pattern:** For Remaining Useful Life (RUL) estimation, the right ladder is:
1. **Weibull AFT** (`lifelines.WeibullAFTFitter`) — fits with only 50–200 historical failure events, produces a full probability distribution over RUL, no GPU needed, interpretable to maintenance engineers.
2. **LSTM** (2-layer, sliding 168-step window) — only graduate to this when you have >1 year of continuous sensor data AND Weibull RMSE exceeds 20% of mean RUL.
3. **ONNX export** for both: frozen model → `onnxruntime` keeps edge inference < 5 ms on CPU without GPU.

**Why it matters:** Teams routinely start with LSTM because it sounds more "AI", then find they don't have enough labeled run-to-failure data to train it and end up with overfit garbage. Weibull with covariates (vib_rms, bearing_temp, run_hours, load_factor) outperforms LSTM on sparse industrial datasets.

**Anomaly detection ladder:** Isolation Forest (train on 30-day normal window, contamination=0.02) before Autoencoder. Graduate to Autoencoder only when IF false-positive rate > 5%.

**Failure mode classification:** Random Forest with `class_weight='balanced'` handles class imbalance without SMOTE overhead. Feature importance output doubles as sensor-selection guidance for sparse deployments. Target: macro-F1 > 0.85 before considering XGBoost.

**OPC-UA tag count anchor:** 20-asset plant → ~400–800 published tags at 100 ms–1 s scan rates; edge aggregation cuts cloud ingest to ~20 MB/day from ~2 GB/day raw.
