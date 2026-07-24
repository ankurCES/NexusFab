---
created_at: 2026-07-23T16:15:24.364412+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CP-SAT circuit constraint needs depot node to model open Hamiltonian path
source: memory_save_learning
---
# CP-SAT circuit constraint needs depot node to model open Hamiltonian path

**Pattern**: `model.AddCircuit()` enforces a Hamiltonian *circuit* (must return to start). For production sequencing (open path, not a loop), inject a depot node (index `n`) with zero-cost arcs to/from every real node, then constrain exactly one `depot_out` and one `depot_in` active. This converts circuit → path without adding fake products to the sequence.

**File**: `nexusfab/optimization/sequencing.py` — `optimize_sequence()` and `_extract_sequence()`.

**Key detail**: After solving, the start node is identified as the unique real node with no real-node predecessor in `nxt` dict (only the depot points to it). The naive approach of checking `depot_out` variables requires passing them through to the extraction function; the `has_predecessor` set trick is cleaner.

**Allergen penalty embedding**: Rather than adding precedence constraints (which can make the model infeasible when allergen order conflicts with due dates), allergen tier regressions are embedded as `+ALLERGEN_VIOLATION_COST` (90 min full-CIP equivalent) directly in the arc cost. This keeps the model always feasible while still strongly discouraging tier regressions. Violations are counted post-solve via `_build_solution()`.

**SMED integration**: Effective changeover = raw × 0.60 (internal only). The 40% external fraction runs in parallel with the last 30 min of the prior batch and is excluded from the makespan calculation. Applied uniformly post-solve — no CP-SAT variable needed.

**Why it matters**: Forgetting the depot-node trick causes `AddCircuit` to produce a sequence that loops back (last product → first product changeover counted), inflating total_changeover_min by one arc and producing wrong makespan estimates.
