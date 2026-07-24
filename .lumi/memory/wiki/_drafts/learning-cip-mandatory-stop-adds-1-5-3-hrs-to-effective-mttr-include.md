---
created_at: 2026-07-23T15:11:58.172819+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: CIP-mandatory stop adds 1.5–3 hrs to effective MTTR — include in cascade models
source: memory_save_learning
---
# CIP-mandatory stop adds 1.5–3 hrs to effective MTTR — include in cascade models

When modelling failure cascades in food plant simulation (`docs/research/maintenance-spare-parts.md`, Section 2.3), any unplanned stop upstream of a CIP-mandatory asset (UHT sterilizer, rotary/linear filler, CIP skid) must add 1.5–3 hrs to effective MTTR because food safety regulations require a validated CIP cycle before product can re-enter. This is not captured by raw MTBF/MTTR figures alone.

**Concrete pattern:** If the simulation engine (e.g. the SimPy-based plant sim in `backend/`) uses `equipment.mttr` directly as repair duration, it will underestimate downtime by 30–100% for any asset with a mandatory CIP-before-restart requirement. The fix: tag equipment records with a `cip_required_on_restart: true` flag and add `cip_duration_hrs` (1.5–3.0 range) to the effective repair time in the cascade resolver.

**Also worth pinning:** Pet food extruders (twin-screw) have anomalously low MTBF (400–700 hrs, Weibull β≈3.0) due to abrasive meat meal and bone dust. Their screw/barrel wear-out is the dominant reliability risk in pet food lines and drives a disproportionate share of spare parts spend — extruder screws/barrels have 12–20 week import lead times and must be stocked as insurance spares.
