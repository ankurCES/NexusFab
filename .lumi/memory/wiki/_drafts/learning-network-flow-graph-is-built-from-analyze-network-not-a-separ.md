---
created_at: 2026-07-23T14:27:22.826814+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Network flow graph is built from analyze_network, not a separate query
source: memory_save_learning
---
# Network flow graph is built from analyze_network, not a separate query

The `analyze_network()` function in `nexusfab/optimization/network.py` now returns a `flow_graph` dict (nodes + edges) embedded in the `NetworkReport.to_dict()` output. The flow graph is **not** a separate data source — it's derived from the same plant capacities and transfer suggestions already computed during analysis. `_build_flow_graph()` builds nodes from `PlantCapacity` objects (with lat/lon from seed data) and edges from `TransferOption` objects, plus inactive edges for all other plant pairs.

Key design decisions:
- **Pallet-based transport model** lives in `transport_cost_pallet()` (same file), scaling $50–$500/pallet based on lat/lon distance. The old `_transport_cost()` in `rerouting.py` is kept untouched — it's per-truck and used by the rerouting module.
- **Minimum transfer = full truck** (`PALLETS_PER_TRUCK = 20`). Transfers below this are filtered out in `analyze_network()`.
- **`balance_network()`** redistributes a failed plant's load proportionally to remaining plants' available capacity, capped at 0.95.
- **`run_network()`** in `simulation/runner.py` runs all 5 plants sequentially (not async — simpy is synchronous) and derives utilization as `min(oee + 0.15, 0.95)`.
- Frontend flow graph is pure SVG in `Network.tsx` (`NetworkFlowGraph` component) — no extra dependency. Positions derived from plant lat/lon.
