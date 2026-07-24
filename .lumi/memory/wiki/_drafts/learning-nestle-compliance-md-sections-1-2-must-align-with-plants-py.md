---
created_at: 2026-07-23T15:01:08.114432+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: nestle-compliance.md sections 1-2 must align with plants.py seed IDs
source: memory_save_learning
---
# nestle-compliance.md sections 1-2 must align with plants.py seed IDs

The research document `docs/research/nestle-compliance.md` now has sections 1–2 (Nestlé factory network profiles and NCE/TPM framework) prepended before the existing sections 3–4 (HACCP/allergen/CIP).

**Critical alignment constraint:** Each plant profile in Section 1 (PLT-001 through PLT-005) maps 1:1 to the `PlantSeed` entries in `nexusfab/seed/plants.py`. The annual production volumes, workforce sizes, and operating patterns in the research doc are derived from the `capacity_tons_per_day` field in `plants.py` combined with uptime assumptions (0.72–0.80 depending on category). If someone changes `capacity_tons_per_day` or adds/removes plants in `plants.py`, the research doc section 1.6 summary table goes stale.

**NCE maturity phases (Section 2.4):** The 5-phase / 13-step model (Phase 0–4, Step 0–12) is from Nestlé's public TPM Reference Guide (Sep 2008). The `starting_oee` values in `plants.py` (0.48–0.62) correspond roughly to Phase 0–1 performance; the `target_oee` values (0.72–0.80) correspond to Phase 2–3. If an NCE module is built, these OEE bands should be the phase-transition thresholds, not arbitrary numbers.

**Factory classification:** Nestlé uses 3 tiers (global flagship → regional hub → local/satellite). The 5 NexusFab plants are all "regional hub" equivalents — single-market, integrated make+pack. This matters if network optimization ever models plant strategic priority for production allocation.
