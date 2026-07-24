---
created_at: 2026-07-23T15:00:00.788447+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: demand.py lead_time_weeks=2.0 default is flat — needs per-category override
source: memory_save_learning
---
# demand.py lead_time_weeks=2.0 default is flat — needs per-category override

`nexusfab/optimization/demand.py` has a single `lead_time_weeks: float = 2.0` parameter used for all safety stock calculations (line ~102 in `DemandConfig`, consumed by `_safety_stock()` at line ~135). This flat default is wrong for the NexusFab 5-plant network:

- **Raw milk (PLT-003 DAIRY)** needs ~0 weeks (daily collection, 72h shelf life)
- **Imported cocoa/hazelnuts (PLT-002 CONFECTIONERY)** need 8–12 weeks
- **Vitamin premix (PLT-004 PET_FOOD)** needs 8–12 weeks from specialty importers
- **PET preforms (PLT-001 WATER)** need 1–2 weeks local, 4–6 weeks imported

Using 2.0 weeks uniformly **under-buffers** imported ingredients (stockout risk) and **over-buffers** perishables (waste/carrying cost). The fix is a per-`category` lead-time lookup table that `generate_demand_plan()` consults instead of the flat default. The research tables in `docs/research/supply-chain-demand.md` §5.2 provide the values.

Also: `SIM-006` in `nexusfab/simulation/scenarios.py` is the only supply-side disruption scenario. The `ScenarioConfig` dataclass lacks a generic `supply_disruption` field — extending it would let any material/plant combination be tested without adding new one-off scenarios.
