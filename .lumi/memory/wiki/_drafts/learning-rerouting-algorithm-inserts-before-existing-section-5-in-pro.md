---
created_at: 2026-07-23T15:14:15.396414+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Rerouting algorithm inserts before existing section 5 in production-operations.md
source: memory_save_learning
---
# Rerouting algorithm inserts before existing section 5 in production-operations.md

When adding sections 3–4 (Line Rerouting Decision Algorithm + ISA-95 mapping) to `docs/research/production-operations.md`, the file already contained section 5 (Changeover Optimization & SMED). The correct insertion point was immediately before the `## 5.` heading — use `Edit` with `old_string = "## 5. Changeover Optimization & SMED Analysis"` and prepend the new content so section numbering stays coherent.

Key structural decisions anchored to existing code:
- Transport cost table (`C_transport`) and plant-pair distances sourced from `simulation/network.py` — any update there must propagate here.
- CIP class lookup (`cip_class(prev_sku, incoming_sku)`) is the same matrix defined in section 5.1; the rerouting section (§3.2.3) explicitly cross-references it rather than duplicating.
- Scoring weights default `{cost: 0.40, time: 0.25, quality: 0.20, util: 0.15}` — configurable per plant; the comment in §3.4.1 points owners to `simulation/network.py` or MES config as the authoritative location.
- Cross-plant reroute approval threshold is £5 k–£20 k for planner alert, anything cross-plant auto-escalates to L4 ERP (§4.3). These thresholds are in the doc, not yet in code — a future implementation task must wire them into the CP-SAT scheduler or a rules engine in `optimization/`.
- ISA-95 data flows use OPC-UA (L2↔L3) and REST/OData B2MML (L3↔L4) — consistent with the plant historian architecture assumed elsewhere in this project.
