---
created_at: 2026-07-23T16:09:54.343921+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Rerouting score: changeover normalized within candidate set, not globally'
source: memory_save_learning
---
# Rerouting score: changeover normalized within candidate set, not globally

In `nexusfab/optimization/rerouting.py`, the 4-component scoring uses **within-candidate-set normalization** for changeover cost (second pass), but absolute scores for compatibility, capacity, and quality risk:

- `compat_score`: absolute — 1.0 if direct compat partner (per `LINE_COMPAT_PARTNERS`), 0.5 if same plant, 0.2 cross-plant.
- `capacity_score`: absolute — `1.0 - utilization`.
- `quality_score`: absolute — `1.0 - risk_rate / 0.10` (research doc §3.3.3 scale).
- `changeover_score`: **relative** — `1.0 - (changeover_min / max_changeover_min across candidates)`. When only one candidate exists, this normalizes to 0.0, which is correct (no cheaper option exists to compare against).

**Why it matters**: If you add a fifth absolute score here (e.g. SLA risk), it will look correct but silently break when there's only one candidate — the composite score will drop, tripping assertions that expect a minimum threshold. Stick to the two-pass pattern: first collect candidates with raw values, then normalize the relative components in a second loop before computing composite.

`LINE_COMPAT_PARTNERS` is the canonical intra-plant compatibility matrix derived from research doc §2.1–2.5. Any new plant or line added to `nexusfab/seed/plants.py` must also get an entry here or it will score 0.2 (cross-plant default) for all rerouting decisions, even when it's a same-plant partner.

Weights live in `_WEIGHTS_NORMAL` / `_WEIGHTS_CRITICAL` dicts (not constants) so urgency="critical" can shift capacity weight from 30% to 40% without touching the formula.
