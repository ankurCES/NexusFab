---
created_at: 2026-07-23T16:36:12.169012+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Demand charges need startup inrush modeling to hit realistic %
source: memory_save_learning
---
# Demand charges need startup inrush modeling to hit realistic %

In `nexusfab/optimization/energy.py`, demand charges ($$/kW/month on peak 15-min interval) only reach the research-grounded 30–50% of total electric bill when you model **motor startup inrush** — not just steady-state kW draw.

`_STARTUP_MULT` dict maps equipment type to inrush factor (1.2–2.5×). `_estimate_peak_demand_kw()` sums per-line startup draws × 1.15 demand factor. Without this, PLT-003 (CA, $22/kW PG&E) demand charge is ~20% of bill — realistic plants hit 30–50% because simultaneous CIP-restart spikes set the billing demand for the entire month.

The `staggered=True` path in `_estimate_peak_demand_kw()` models the optimization lever: restart only one line at a time, reducing peak from all-line-inrush to max-single-line-inrush + others-at-steady-state. For PLT-003 this drops 651→470 kW, saving ~$4K/month in demand charges alone.

Key: `calculate_monthly_bill()` is the full-picture function (energy + demand + CPP + PF penalty + gas). `optimize_energy_schedule()` handles TOU shifting + demand staggering but not CPP/PF/gas.
