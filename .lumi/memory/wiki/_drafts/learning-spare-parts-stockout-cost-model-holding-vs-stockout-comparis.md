---
created_at: 2026-07-23T15:05:44.844650+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'Spare parts stockout cost model: holding vs stockout comparison pattern'
source: memory_save_learning
---
# Spare parts stockout cost model: holding vs stockout comparison pattern

In `docs/research/maintenance-spare-parts.md` (Section 4), the cost model establishes a concrete decision rule for whether to stock a spare locally: compare annual holding cost (`unit_cost × 0.25`) against expected annual stockout cost (`P_stockout × demand_events/yr × (downtime_$/hr × MTTR + emergency_premium`)).

Key numbers anchored to food manufacturing reality:
- Holding rate: **25%/yr** (capital + space + insurance + deterioration)
- High-speed packaging downtime: **$8,000–$20,000/hr**
- Batch processing downtime: **$3,000–$8,000/hr**

The criticality score formula (`(downtime_cost × MTTR × P_failure) / (unit_cost × holding_rate)`) maps directly to the ABC-XYZ stock policy in Section 1: score > 10 → always-in-stock insurance spare, 3–10 → ROP-based, < 3 → order-on-fail.

The vendor lead time table (Section 5) codifies the practical decision boundary: any part with expedited lead time > 3 days **and** failure cost > $5,000/hr should be stocked on-site. OEM-specific/single-source parts (spray dryer atomizers, extruder barrels) have 12–24 week import lead times — these are the AZ insurance spares that justify 1-unit on-shelf regardless of usage frequency.

Future agents extending the maintenance optimizer should wire these cost parameters into the `maintenance/` module — specifically the stockout cost and criticality score as inputs to the spare parts optimizer, not just the ROP reorder trigger.
