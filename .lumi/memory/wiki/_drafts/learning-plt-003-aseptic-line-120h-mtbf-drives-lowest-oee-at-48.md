---
created_at: 2026-07-23T15:16:11.429567+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: PLT-003 aseptic line (120h MTBF) drives lowest OEE at 48%
source: memory_save_learning
---
# PLT-003 aseptic line (120h MTBF) drives lowest OEE at 48%

In `nexusfab/seed/plants.py`, PLT-003 (NexDairy-North) carries the lowest `starting_oee` in the fleet (0.48) for a specific structural reason: PLT-003-L3 (ASEPTIC line) has a FILLER with MTBF of only 120 hours — the shortest in the entire 5-plant network — combined with a mandatory CIP cycle every 8 hours (FDA/FSMA aseptic requirement). That 8-hour CIP cadence alone costs ~23% of weekly scheduled hours before any unplanned breakdown is counted.

**Pattern to remember**: when diagnosing why a simulated plant's OEE is anomalously low, check two things in `plants.py`: (1) the MTBF on the FILLER equipment for wet/aseptic lines — it is always the bottleneck, not the MIXER or CONVEYOR; and (2) the line type's CIP frequency from the research doc (`docs/research/production-operations.md`, §1.3). ASEPTIC lines need CIP every 8 h (90–150 min each), UHT every 8–12 h, versus PET_BOTTLING only every 24 h.

**Why it matters**: a future agent setting OEE targets or sizing capacity headroom for PLT-003 must not treat it as comparable to PLT-001 (water, 62%) or PLT-004 (pet food, 60%). PLT-003's 48% is structurally caused by line type, not operator performance — pushing it above ~72% requires either CIP-time reduction (clean-in-place chemistry upgrades) or a second aseptic filler to run in parallel, not just PdM on existing equipment.
