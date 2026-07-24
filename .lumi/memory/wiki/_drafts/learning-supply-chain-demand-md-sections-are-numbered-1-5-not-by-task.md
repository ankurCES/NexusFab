---
created_at: 2026-07-23T15:06:11.327600+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: supply-chain-demand.md sections are numbered 1-5, not by task
source: memory_save_learning
---
# supply-chain-demand.md sections are numbered 1-5, not by task

The research doc `docs/research/supply-chain-demand.md` uses a continuous section numbering scheme across multiple research tasks:

- **§1–2**: Demand forecasting methods, FMCG seasonality, promotion effects, accuracy benchmarks, sensing vs planning
- **§3**: Multi-plant allocation optimization (MILP formulation, transport matrix, changeover costs)
- **§4**: Capacity planning & network inventory (OEE model, safety stock, MEIO, solver selection)
- **§5**: Raw material management (BOM per plant, supplier lead times, substitution rules, disruption scenarios, holding costs)

Each section cross-references `demand.py` functions and seed data by line number. When extending the doc, maintain the numbering — don't restart at §1 or insert between existing sections. The placeholder pattern is `<!-- Sections X–Y to be added by other research tasks -->`. Sections 1–5 are now complete; future work should go into §6+ or as subsections.
