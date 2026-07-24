---
created_at: 2026-07-23T14:35:19.739037+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: HACCP CCPs must cover all line types or compliance % drops to zero
source: memory_save_learning
---
# HACCP CCPs must cover all line types or compliance % drops to zero

The `HACCP_CCPS` dict in `nexusfab/optimization/regulatory.py` maps line types to their critical control points. If a plant's lines (e.g. PLT-002's MOULDING/ENROBING/WRAPPING) aren't in this dict, `generate_compliance_report()` produces zero CCP readings for that plant, which makes `ccp_compliance_pct` either 0.0% or undefined — both wrong.

Initially only UHT_FILLING, ASEPTIC, RETORT_CANNING, and POWDER_PACKING had entries. PLT-002 (confectionery) and PLT-005 (prepared foods) got no CCP coverage at all, which broke the self-check assertion (`ccp_compliance_pct > 80`). Fixed by adding CCP entries for MOULDING, ENROBING, MIXING_COOKING, and EXTRUSION.

**Lesson**: When adding a new line type to `nexusfab/seed/plants.py`, also add its HACCP CCPs to the `HACCP_CCPS` dict in `regulatory.py`, or every compliance report for that plant will silently report zero CCP compliance. A future improvement would be to assert at import time that every line type in PLANTS has at least one CCP entry.
