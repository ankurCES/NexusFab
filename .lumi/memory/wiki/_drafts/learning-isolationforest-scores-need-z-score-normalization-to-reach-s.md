---
created_at: 2026-07-23T16:53:41.460457+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: IsolationForest scores need z-score normalization to reach spec-defined [-1,1] range
source: memory_save_learning
---
# IsolationForest scores need z-score normalization to reach spec-defined [-1,1] range

**Problem**: sklearn `IsolationForest.decision_function()` returns raw scores in a narrow ±0.2 range (not [-1, 1]). If you try to map those raw scores directly to a health index — e.g. `clip((score + 0.5)/1.0, 0, 1)` — all alert levels collapse to the same zone because the score range is too compressed.

**Solution**: After training, store the training-score mean and std. At inference time, z-score the 20-window rolling mean against those stats, then clamp to [-1, 1]:

```python
z = (rolling_mean - score_mean) / (2.0 * score_std)
anomaly_score = clip(z, -1.0, 1.0)
health = clip((anomaly_score + 1.0) / 1.5, 0.0, 1.0)
```

This gives `anomaly_score ≈ 0` for healthy operation (rolling mean near training mean), and `anomaly_score → -1` when the rolling mean drops >2σ below training mean. The spec threshold at -0.5 corresponds to 1σ below mean — reasonable for scheduling maintenance.

**Complementary fix**: After `fit()`, seed `_score_history` with `[score_mean] * HEALTH_WINDOW`. This prevents the cold-start problem where the first `predict_rul()` call has only 1 sample in the rolling window and produces a noisy/RED result.

**Demo sizing**: With Weibull η=600h, the healthy health index (~0.667) gives RUL ≈ 348h (firmly GREEN), giving enough margin that natural rolling-mean variance during healthy operation doesn't produce false YELLOW readings.

**File**: `nexusfab/optimization/predictive_maintenance.py`. Task: sprint `6b7dabcc`.
