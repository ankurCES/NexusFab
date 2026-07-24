---
created_at: 2026-07-23T16:06:38.504932+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Crew rotation cycles need cycle_len divisible by crew count
source: memory_save_learning
---
# Crew rotation cycles need cycle_len divisible by crew count

In `nexusfab/simulation/workforce_sim.py`, each plant's shift rotation is modelled as a repeating cycle of `ShiftType` enums. Crew N's day-index into the cycle is offset by `crew * (cycle_len // crews)`. This only gives correct 24/7 coverage when `cycle_len % crews == 0`:

- 3×8h continental, 4 crews → 8-day cycle (DD AA NN OO), offset 2
- 2×12h pitman, 3 crews → 6-day cycle (D12 D12 N12 N12 O O), offset 2
- 3×8h+swing, 5 crews → 10-day cycle (DD AA NN AA OO), offset 2
- 2×12h dupont, 4 crews → 8-day cycle (D12 D12 O O N12 N12 O O), offset 2

If a future contributor adds a new plant with, say, a 7-day cycle and 4 crews, the integer division truncates the offset and crews pile onto the same shifts, creating both double-coverage windows and uncovered gaps. The `find_coverage_gaps()` function would catch it at roster-generation time, but the root cause would be non-obvious.

The `_CYCLE_*` module-level lists are the canonical patterns. New patterns should be validated: `assert len(cycle) % crews == 0` before adding to `PLANT_SCHEDULES`. The `__main__` self-check covers all existing plants but does not enforce the divisibility invariant programmatically — add an assertion in `generate_shift_roster` if more plants arrive.
