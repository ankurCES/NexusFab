---
created_at: 2026-07-23T15:02:41.459923+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Network allocation MILP is ~136K vars — CP-SAT handles it, skip Gurobi
source: memory_save_learning
---
# Network allocation MILP is ~136K vars — CP-SAT handles it, skip Gurobi

The multi-plant allocation problem for NexusFab's 5-plant × 17-line × ~50-SKU × 12-period network sizes to ~136,000 variables (~114K continuous + ~22K binary for changeovers, batch minimums, and ship-or-not decisions) with ~150K constraints. This is a medium-scale MILP.

**Key finding:** OR-Tools CP-SAT solves this in 30–120s on 8 workers, well within a weekly planning cycle. It's already a dependency — `nexusfab/optimization/rerouting.py` uses CP-SAT with `NewOptionalIntervalVar` for rerouting. The same optional-interval pattern works for changeover modeling in the allocation problem.

**Why it matters:** Adding Gurobi was considered but rejected — it only saves 10–90s per solve for this problem size and introduces commercial license management. PuLP/CBC is adequate for LP relaxation (Phase 2 prototyping, 5–15s) but too slow for the full MILP (60–300s vs CP-SAT's 30–120s).

**Scaling ceiling:** At 52-week horizon (~590K vars), CP-SAT needs 5–15 min — use rolling horizon (solve 12 weeks, advance 4, re-solve). Daily granularity (~1.1M vars) requires rolling horizon mandatory.

**CP-SAT gotcha:** All variables must be integer. Multiply continuous quantities by 100 (centitones) for 2-decimal precision. This is the same scaling pattern already in `rerouting.py`.

Files: `docs/research/supply-chain-demand.md` §3–4, `nexusfab/optimization/network.py`, `nexusfab/optimization/rerouting.py`.
