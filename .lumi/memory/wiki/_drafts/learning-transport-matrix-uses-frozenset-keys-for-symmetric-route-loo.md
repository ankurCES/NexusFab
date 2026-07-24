---
created_at: 2026-07-23T15:57:16.852990+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Transport matrix uses frozenset keys for symmetric route lookup
source: memory_save_learning
---
# Transport matrix uses frozenset keys for symmetric route lookup

The transport cost model in `nexusfab/optimization/network.py` uses `frozenset({from_plant, to_plant})` as dict keys in `_TRANSPORT_MATRIX` so that route lookups are symmetric — `PLT-001→PLT-003` and `PLT-003→PLT-001` hit the same entry without storing both directions.

Cold-chain surcharge logic (`COLD_CHAIN_SURCHARGE_PCT = 0.40`) is applied in `transport_cost_pallet()` when *either* `product_category == "DAIRY"` **or** either endpoint's plant category is `DAIRY` (checked via `_is_dairy_route()` → `get_plant().category`). This means any route touching PLT-003 auto-flags cold chain even if the caller doesn't pass a product category — important for the flow-graph inactive edges in `_build_flow_graph()` where product_category isn't known.

The `analyze_network()` transfer loop enforces FTL minimum (20 pallets) by rounding up both pallet count and transfer tonnage. Previous code skipped sub-FTL transfers entirely; the new code always emits at least a full truck, which changes downstream cost calculations.

The self-check at `__main__` verifies the exact matrix values ($460 for PLT-001↔005, $350 for PLT-003→001 dairy = $250 × 1.40) and the cold_chain flag. If the surcharge percentage or matrix values change, update both the constant and the assertions.
