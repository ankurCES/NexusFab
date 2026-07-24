---
created_at: 2026-07-23T15:11:04.587545+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Changeover sequencing: allergen tier as hard TSP precedence constraint'
source: memory_save_learning
---
# Changeover sequencing: allergen tier as hard TSP precedence constraint

In `docs/research/production-operations.md` §5.4, changeover sequencing is modeled as Asymmetric TSP (ATSP) because the changeover matrix is non-symmetric — going from a nut-milk to plain water costs 120 min (full CIP) while the reverse costs only 90 min.

The critical wrinkle: allergen tier (0=allergen-free → 4=nut/peanut) must be implemented as a **hard arc prohibition** in OR-Tools, not a soft penalty. Any route that runs a higher-allergen tier before a lower-allergen tier forces a full CIP + micro-swab verification before the low-allergen product can be released — a regulatory (FSMA/HACCP) requirement, not a preference.

In the OR-Tools skeleton, this is done by calling `routing.NextVar(i).RemoveValue(j)` for every pair where `allergen_tier[j] < allergen_tier[i]`. Flavor and color violations are soft (add penalty arcs), allergen is hard (remove arcs entirely).

Practical payoff: on a 15-SKU beverage line, optimized sequencing cuts full CIP cycles from 2.8 to 1.0 per shift, saving ~81 min/shift (~18% of available time). The nearest-neighbor heuristic (eligible = SKUs with tier ≥ current) provides a <50 ms fallback for real-time re-sequencing when orders are inserted mid-shift.

Solver fit: OR-Tools TSP for ≤40 SKUs, nearest-neighbor+2-opt for 41–100, genetic algorithm for >100 SKUs in campaign planning.
