---
created_at: 2026-07-23T15:46:28.413203+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: HACCP_CCPS dict missing 7 of 14 line types — blocks compliance
source: memory_save_learning
---
# HACCP_CCPS dict missing 7 of 14 line types — blocks compliance

The `HACCP_CCPS` dict in `nexusfab/optimization/regulatory.py` originally covered only 8 of 15 unique line types (UHT_FILLING, ASEPTIC, RETORT_CANNING, POWDER_PACKING, MOULDING, ENROBING, MIXING_COOKING, EXTRUSION). The 7 missing types — PET_BOTTLING, GLASS_BOTTLING, CANNING, WRAPPING, KIBBLE_COATING, FILLING, NOODLE_LINE — caused `generate_compliance_report()` to produce zero CCP readings for those lines, since it does `HACCP_CCPS.get(line.line_type, [])`.

This matters because any downstream consumer (dashboards, compliance audits, scheduling constraints) that checks CCP compliance percentage will see 0% for plants whose lines lack entries — PLT-001 (Water) had zero CCPs entirely.

The canonical CCP definitions live in `docs/research/nestle-compliance.md` §3.1.1 (17 CCPs across 14 line types). CANNING (PLT-001-L4) is the 15th line type not in the research doc; it was given CCP-W4 mirroring GLASS_BOTTLING's rinse temp CCP for 100% coverage. The self-check in `__main__` now asserts every line type in `PLANTS` has ≥1 CCP entry, so future additions to `plants.py` will fail fast if CCPs aren't added in parallel.
