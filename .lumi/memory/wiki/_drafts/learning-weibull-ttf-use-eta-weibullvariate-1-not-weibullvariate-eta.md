---
created_at: 2026-07-23T16:04:10.602393+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Weibull TTF: use eta*weibullvariate(1,β), not weibullvariate(eta,β)'
source: memory_save_learning
---
# Weibull TTF: use eta*weibullvariate(1,β), not weibullvariate(eta,β)

In `nexusfab/simulation/failure_generator.py`, time-to-failure is computed as:

```python
eq.weibull_eta * random.weibullvariate(1, eq.weibull_beta)
```

**Why not `random.weibullvariate(eta, beta)` directly?** Python's `random.weibullvariate(alpha, beta)` returns `alpha * (-ln(U))^(1/beta)`, so both forms are mathematically equivalent — but the explicit `eta * weibullvariate(1, beta)` makes the scale parameter visible and matches the formula in the task spec and `plants.py` comments (`η·Γ(1+1/β)` for MTBF). Using the direct form (`weibullvariate(eta, beta)`) works but obscures the connection to the seed data parameters.

**Renewal process after repair**: the heap-based generator re-schedules the *next* failure starting from `t + mttr`, not from `t`. This means the simulation correctly models a renewal process (each TBF is iid from the Weibull) rather than an aging process. If you switch to a non-renewal / imperfect repair model (e.g., NHPP), the heap logic changes significantly.

**Statistical check caveat**: the `__main__` self-check verifies `second_half_count >= first_half_count` for β>1 equipment over 1000h. With seed=42 this passes (9/13), but individual pieces of equipment with high η (rare failures) can flip due to stochastic variance with <5 events — the assert allows up to 50% failure to stay robust. Do not tighten the threshold without extending the simulation horizon to ≥5000h.

**Files**: `nexusfab/simulation/failure_generator.py`, `nexusfab/seed/plants.py` (EquipmentSeed with weibull_beta/weibull_eta fields).
