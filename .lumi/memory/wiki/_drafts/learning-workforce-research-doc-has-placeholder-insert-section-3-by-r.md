---
created_at: 2026-07-23T14:55:59.400111+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Workforce research doc has placeholder — insert Section 3 by replacing it
source: memory_save_learning
---
# Workforce research doc has placeholder — insert Section 3 by replacing it

The file `docs/research/energy-workforce-simulation.md` already existed with Sections 1–2 and a stub line:

```
*Sections 3 (Workforce scheduling) added separately. Sections 4–5 below.*
```

Any agent tasked with adding Section 3 must target that exact placeholder string via `Edit` (old_string match), not append to EOF — the file has Sections 4+ after the placeholder. Appending blindly would land Section 3 after Section 4, breaking document order.

Key research facts encoded in Section 3:
- `skill_flexibility_index < 1.2` is the warning threshold for scheduling gaps (target ≥ 1.4).
- `absenteeism_rate` default is 0.065 with a 12-element `seasonal_multipliers` array; December multiplier 1.4× creates the worst-case staffing scenario.
- `labor_cost_per_hour()` formula in §3.5.3 is the canonical cost function — ON_COST_FACTOR 1.30, OT_MULTIPLIER 1.5 (2.0× only for >60h/BH).
- 12-h Pitman pattern is cheapest per productive hour for 24/7 operations (~£20.98 vs £21.43 for continental 4-crew).
- Min L2+ operator per CCP line is a hard compliance constraint — absence means line halt, not degraded operation.
