# Food Manufacturing Regulatory Compliance Research

> Research synthesis for NexusFab production scheduling optimizer.
> Sections 1–2: Nestlé factory network & NCE/TPM compliance modeling.
> Sections 3–4: Food safety regulatory frameworks & allergen management.

**Date:** 2026-07-23
**Scope:** Food & beverage manufacturing (Nestlé case study basis)

---

## Section 1 — Simulated Plant Profiles (Nestlé-Aligned)

Five plants modeled after real Nestlé product categories and plausible factory locations.
Each profile maps to an existing `PlantSeed` in `nexusfab/seed/plants.py` (PLT-001 through PLT-005).

### 1.1 PLT-001 — NexWater-East (Water Bottling)

| Attribute | Value |
|---|---|
| **Location basis** | Northeastern US — modeled on Nestlé Waters sites in PA/CT corridor |
| **Product category** | WATER (still & sparkling, Perrier/S.Pellegrino style) |
| **Production lines** | 4 — 2× PET bottling, 1× glass bottling, 1× canning |
| **Operating pattern** | 24/7 continuous (3 shifts × 8 hr) |
| **Annual production** | ~510,000 tonnes (1,400 t/day × 365 days × ~0.80 uptime) |
| **Workforce** | ~320 (120 operators, 40 maintenance, 30 QA, 20 warehouse, 110 support/admin) |
| **Notes** | High-speed lines; dominant cost driver is energy for blowing/filling. Glass line slower but premium margin. Nestlé divested some water brands (2021) but retains premium portfolio. |

### 1.2 PLT-002 — NexConfec-Central (Confectionery)

| Attribute | Value |
|---|---|
| **Location basis** | US Midwest — modeled on KitKat/confectionery operations (e.g., Bloomington, IL corridor) |
| **Product category** | CONFECTIONERY (moulded chocolate, enrobed bars, wrapped count lines) |
| **Production lines** | 3 — 1× moulding, 1× enrobing, 1× wrapping |
| **Operating pattern** | 5-day, 2 shifts (Mon–Fri, 16 hr/day); seasonal 24/7 Oct–Dec |
| **Annual production** | ~26,000 tonnes (140 t/day × 260 days × ~0.72 uptime) |
| **Workforce** | ~280 (100 operators, 35 maintenance, 25 QA, 15 warehouse, 105 support/admin) |
| **Notes** | Temperature-critical — chocolate tempering requires ±0.5°C. Make/pack integrated; moulding and wrapping on same floor. Highest changeover frequency due to SKU count. |

### 1.3 PLT-003 — NexDairy-North (Dairy / Nutrition)

| Attribute | Value |
|---|---|
| **Location basis** | Upper Midwest — modeled on dairy/nutrition sites (WI/MN dairy belt) |
| **Product category** | DAIRY (UHT milk, powdered milk/Nido-style, aseptic nutrition) |
| **Production lines** | 3 — 1× UHT filling, 1× powder packing, 1× aseptic |
| **Operating pattern** | 24/7 continuous (milk intake cannot stop; raw material perishable) |
| **Annual production** | ~160,000 tonnes (550 t/day × 365 × ~0.80 uptime) |
| **Workforce** | ~450 (160 operators, 55 maintenance, 45 QA/lab, 25 warehouse, 165 support/admin) |
| **Notes** | Highest HACCP complexity — 3 CCPs per line minimum. CIP/SIP cycles dominate downtime. Powder line includes spray dryer (120–350 kWh). Aseptic has strictest cleanroom requirements. Lowest starting OEE (0.48) — typical for dairy with frequent CIP. |

### 1.4 PLT-004 — NexPet-South (Pet Food)

| Attribute | Value |
|---|---|
| **Location basis** | US Southeast — modeled on Purina manufacturing (GA/NC corridor) |
| **Product category** | PET_FOOD (dry kibble, wet/retort canned, coated treats) |
| **Production lines** | 4 — 2× extrusion (dry), 1× retort canning (wet), 1× kibble coating |
| **Operating pattern** | 24/7 continuous (Purina sites run 24/7; pet food is Nestlé's largest division by revenue) |
| **Annual production** | ~122,000 tonnes (420 t/day × 365 × ~0.80 uptime) |
| **Workforce** | ~380 (140 operators, 45 maintenance, 30 QA, 25 warehouse, 140 support/admin) |
| **Notes** | Extrusion is energy-intensive (twin-screw 55–90 kWh) with high dryer loads. Retort canning has longest cycle time. Pet food is ~30% of Nestlé Group revenue — strategic priority. |

### 1.5 PLT-005 — NexPrepared-West (Prepared Foods)

| Attribute | Value |
|---|---|
| **Location basis** | US West Coast — modeled on Maggi/prepared foods operations (Southern CA) |
| **Product category** | PREPARED_FOODS (sauces, seasonings, instant noodles) |
| **Production lines** | 3 — 1× mixing/cooking, 1× filling, 1× noodle line |
| **Operating pattern** | 5-day, 3 shifts (Mon–Fri, 24 hr/day); weekend maintenance windows |
| **Annual production** | ~42,000 tonnes (220 t/day × 260 × ~0.73 uptime) |
| **Workforce** | ~250 (90 operators, 30 maintenance, 25 QA, 20 warehouse, 85 support/admin) |
| **Notes** | Highest recipe variety — 50+ SKUs. Noodle line has specialized sheeting/cutting equipment. Make/pack split: cooking is process-controlled, packing is discrete. |

### 1.6 Network Summary

| Plant | Category | Lines | Pattern | Annual Tonnes | Workforce | Starting OEE |
|---|---|---|---|---|---|---|
| PLT-001 | WATER | 4 | 24/7 | ~510,000 | 320 | 0.62 |
| PLT-002 | CONFECTIONERY | 3 | 5-day 2-shift | ~26,000 | 280 | 0.55 |
| PLT-003 | DAIRY | 3 | 24/7 | ~160,000 | 450 | 0.48 |
| PLT-004 | PET_FOOD | 4 | 24/7 | ~122,000 | 380 | 0.60 |
| PLT-005 | PREPARED_FOODS | 3 | 5-day 3-shift | ~42,000 | 250 | 0.52 |
| **Total** | | **17** | | **~860,000** | **1,680** | |

### 1.7 Alignment with Nestlé Global Footprint

Real Nestlé operates **335 factories in 75 countries** with ~271,000 employees (2025 Annual Report). The 5-plant NexusFab network is a scaled simulation (~0.6% of workforce, 5 of Nestlé's main product categories). Production volumes are calibrated to mid-size single-site US operations within each category.

---

## Section 2 — Nestlé Continuous Excellence (NCE) & TPM Framework

### 2.1 NCE Program Overview

Nestlé Continuous Excellence (NCE), introduced in **2008**, integrates Lean, TPM, and Six Sigma company-wide. By 2010 it was deployed in 300+ factories, generating **CHF 1.5 billion in annual savings**.

**The 3Cs** — NCE's stated objectives:
1. **Delight the Consumer** — quality and innovation
2. **Deliver Competitive Advantage** — cost and speed
3. **Excel in Compliance** — safety, regulatory, sustainability

**Three foundation pillars:**
- **NIMS** (Nestlé Integrated Management System) — health, safety, quality processes
- **Leadership Development** — coaching, empowerment, succession planning
- **Goal Alignment** — business priorities cascaded to individual objectives

### 2.2 TPM Pillars

NCE's TPM implementation follows 8 pillars aligned with JIPM (Japan Institute of Plant Maintenance), adapted to food manufacturing:

| # | Pillar | Abbr | Scope |
|---|---|---|---|
| 1 | **Focused Improvement** | FI | Cross-functional teams eliminating chronic losses via Kaizen, DMAIC, loss-tree analysis |
| 2 | **Autonomous Maintenance** | AM | Operators own cleaning, inspection, lubrication; 7-step progression to full self-management |
| 3 | **Planned Maintenance** | PM | Time/condition-based preventive maintenance; spare parts optimization; CMMS integration |
| 4 | **Quality Maintenance** | QM | Zero-defect conditions; process parameter control; HACCP integration at equipment level |
| 5 | **Early Equipment Management** | EEM | Lifecycle cost analysis; vertical startup targets; design-for-maintainability |
| 6 | **Training & Education** | E&T | Skill matrices, multi-skilling, one-point lessons (OPLs); competency gap closure |
| 7 | **Safety, Health & Environment** | SHE | Zero-accident culture; behavioral safety observations; environmental compliance |
| 8 | **Office TPM** | OTPM | Administrative loss reduction; information flow optimization; support-function efficiency |

### 2.3 KPI Targets per Pillar

Targets are representative of NCE benchmarks from public case studies and industry TPM standards. Internal targets vary by maturity phase.

| Pillar | Primary KPIs | Phase 0–1 Target | Phase 2–3 Target | World-Class (Phase 4) |
|---|---|---|---|---|
| **FI** | OEE, cost savings, Kaizen events | OEE ≥ 65%, 2+ Kaizen/line/yr | OEE ≥ 78%, 6+ Kaizen/line/yr | OEE ≥ 85%, continuous Kaizen culture |
| **AM** | AM step, operator defects/mo, cleaning time | Step 1–3, 5+ tags/operator/mo | Step 4–5, 15+ tags, CIL stable | Step 6–7, self-managed teams |
| **PM** | PM compliance %, MTBF, MTTR, breakdown rate | PM ≥ 80%, breakdowns < 5% | PM ≥ 92%, MTBF +30% vs baseline | PM ≥ 98%, predictive dominant |
| **QM** | Defect ppm, complaints, first-pass yield | < 5,000 ppm, complaints −30% | < 1,000 ppm, complaints −60% | < 100 ppm, zero complaints target |
| **EEM** | Vertical startup time, LCC accuracy | LCC on all new projects, startup < 6 mo | Startup < 3 mo, 90% MP feedback | Startup < 1 mo, full lifecycle model |
| **E&T** | Skill matrix coverage, training hr/yr, multi-skill % | 80% mapped, 40 hr/yr | 95% mapped, 60 hr/yr, 30% multi-skilled | 100% mapped, 80+ hr/yr, 70% multi-skilled |
| **SHE** | LTIR, near-miss reports, env incidents | LTIR < 2.0, near-miss active | LTIR < 0.5, behavioral audits | LTIR < 0.1, zero accidents sustained |
| **OTPM** | Admin lead time, info accuracy, support cost | Processes mapped, 20% waste cut | 50% lead time reduction, digital workflows | Fully integrated digital ops |

### 2.4 Maturity Assessment Levels

NCE TPM maturity follows **5 phases (Phase 0–4)** across **13 steps (Step 0–12)**. Progression takes **2–10 years** per factory. Assessment is gate-based with regular re-audits.

| Phase | Steps | Name | Description | Typical Duration |
|---|---|---|---|---|
| **Phase 0** | 0–2 | **Preparation** | TPM decision announced; promotion organization created; basic policy & goals set; master plan drafted | 3–6 months |
| **Phase 1** | 3–5 | **Foundation** | SHE pillar launched; reliability pillars (AM, PM, FI, E&T) active on model lines; initial loss analysis | 6–18 months |
| **Phase 2** | 6–8 | **Expansion** | All lines active; QM and EEM pillars launched; measurable OEE gains | 1–3 years |
| **Phase 3** | 9–10 | **Integration** | All 8 pillars active and integrated; OTPM launched; gains sustained 12+ months | 1–2 years |
| **Phase 4** | 11–12 | **World Class** | Self-sustaining culture; benchmark performance; JIPM award eligibility | Ongoing |

**Gate assessment criteria:**
- Concrete waste/loss elimination evidence (not just activity)
- Performance improvement vs. baseline (OEE, cost, safety, quality)
- Sustainability of gains (minimum 6-month sustain)
- Employee engagement (participation rates, suggestion counts)
- Horizontal deployment (learnings shared across lines/plants)

### 2.5 NCE Pilot Results (Public Data)

From published case studies, pilot factories achieved:
- Consumer complaints: **30% reduction**
- Conversion costs: **9% decrease**
- Operational efficiency: **90% achievement**
- Safety: **zero lost-time accidents** in pilot sites

### 2.6 Nestlé Factory Classification

**By product group** (primary axis — determines technology, regulatory regime, skill mix):
- Beverages (water, coffee/Nescafé, Nespresso capsules)
- Dairy & Nutrition (UHT, powder, infant formula)
- Confectionery (chocolate, sugar, biscuits)
- Pet Care (dry kibble, wet food, treats)
- Prepared Foods & Cooking Aids (Maggi, frozen, culinary)
- Health Science (medical nutrition, supplements)

**By geography** (3 management zones):
- Zone Americas (AMS) — 54 US + 13 Brazil + 11 Mexico + others
- Zone EMENA — 13 Germany, 12 France, 7 Italy + others
- Zone AOA — 8 India, 6 China, 6 Indonesia + others

**By strategic importance:**
- **Global flagship** — highest-volume, most-automated benchmark sites (JIPM award candidates)
- **Regional hub** — serves multiple markets; has make + pack capability
- **Local/satellite** — single-market, often pack-only or single-category

**Make/pack split vs. integrated:**
- Historically separated: "make" (process manufacturing) managed by process engineers; "pack" (discrete packaging) by Packaging Engineering.
- Current direction: **integrated make-and-pack** with unified MES. Internal guidelines mandate filling/packing line integration.
- Digital twin technology deployed for end-to-end make-and-pack flow modeling.

### 2.7 Public Data — Nestlé Annual Report 2025

| Metric | Value |
|---|---|
| Factories worldwide | 335 in 75 countries |
| Employees | ~271,000 |
| Annual sales | CHF 89.5 billion |
| R&D investment | CHF 1.7 billion / 22 locations / 4,000 staff |
| Billionaire brands | 30+ |
| Products sold in | 185 countries |
| Organic growth (2025) | 2.8% (Zone Americas) |

### 2.8 Sustainability Targets Impacting Operations

| Area | 2025 Achievement | 2030 Target | Operational Impact |
|---|---|---|---|
| **GHG emissions** | −24.5% vs 2018 baseline | −50% vs 2018; net zero by 2050 | Renewable electricity at 98.6%; 100% target by 2026 |
| **Water usage** | −2.9M m³; −2.0M m³ in stressed areas | Continued reduction; AWS certification expansion | Factory-level withdrawal monitoring; exec compensation KPI |
| **Zero waste to landfill** | 92% of sites achieved | 100% of sites | Waste sorting, recycling, energy recovery at all sites |
| **Virgin plastic** | −28% vs 2018; 87% recyclable packaging | 100% recyclable/reusable | Packaging line changeovers for new materials; rPET |
| **Regenerative agriculture** | 27.6% of key ingredients | 50% by 2030 | Supplier qualification; traceability in raw material intake |

### 2.9 Sources

- [Nestlé Annual Report 2025](https://www.nestle.com/investors/annual-report)
- [Nestlé at a Glance](https://www.nestle.com/about/overview)
- [Full-Year Results 2025](https://www.nestle.com/media/pressreleases/allpressreleases/full-year-results-2025)
- [NCE Program — BusinessMeta](https://businessmeta.home.blog/2024/12/03/how-nestles-continuous-excellence-program-transformed-global-operations/)
- [NCE — European Financial Review](https://www.europeanfinancialreview.com/nestle-continuous-excellence-lessons-for-driving-performance-improvement/)
- [NCE TPM Reference Guide — Scribd](https://www.scribd.com/document/896664363/NCE-Nestle)
- [NCE Case Study — IMD](https://www.imd.org/research-knowledge/strategy/case-studies/nestle-continuous-excellence-operations-and-beyond/)
- [Sustainability Targets vs Achievements — GreentechLead](https://greentechlead.com/sustainability/nestle-2025-sustainability-targets-vs-achievements-highlight-climate-progress-and-circularity-gaps-52855)
- [Nestlé Sustainability 2026 — Sustainability Magazine](https://sustainabilitymag.com/news/what-is-nestles-sustainability-focus-in-2026)
- [Water Management — Nestlé Global](https://www.nestle.com/sustainability/water/sustainable-water-efficiency-operations)
- [Nestlé Packaging Strategy — Packaging World](https://www.packworld.com/trends/controls-machine-components/article/13348093/nestl-makes-packaging-a-strategic-priority)

---

## Section 3 — Food Safety Regulatory Frameworks

### 3.1 HACCP (Hazard Analysis Critical Control Points)

HACCP is the mandatory food safety management system (Codex Alimentarius, 1993; 21 CFR 120/123 in the US; EC Regulation 852/2004 in the EU). It requires manufacturers to identify biological, chemical, and physical hazards at every process step and establish Critical Control Points (CCPs) where those hazards can be prevented, eliminated, or reduced to safe levels.

#### 3.1.1 CCPs by Plant Type

Each NexusFab plant type has process-specific CCPs. The table below maps to the `HACCP_CCPS` dict in `nexusfab/optimization/regulatory.py`.

| Plant Type | Line Type | CCP | Parameter | Critical Limits | Monitoring Freq |
|---|---|---|---|---|---|
| **Water** (PLT-001) | PET_BOTTLING | CCP-W1 | Ozone concentration | 0.2–0.4 mg/L | Continuous |
| | PET_BOTTLING | CCP-W2 | UV dose (254 nm) | ≥ 40 mJ/cm² | Continuous |
| | GLASS_BOTTLING | CCP-W3 | Bottle rinse temp | ≥ 82°C | Every 15 min |
| **Confectionery** (PLT-002) | MOULDING | CCP-07 | Tempering temp | 29–33°C | Every 10 min |
| | ENROBING | CCP-08 | Enrobing temp | 30–34°C | Every 10 min |
| | WRAPPING | CCP-C3 | Metal detection | ≤ 0.5 ppm | Every unit |
| **Dairy** (PLT-003) | UHT_FILLING | CCP-01 | Pasteurization temp | 135–145°C | Every 5 min |
| | UHT_FILLING | CCP-02 | Hold time | ≥ 3.5 sec | Every 5 min |
| | ASEPTIC | CCP-03 | Sterilization temp | 140–150°C | Every 3 min |
| | POWDER_PACKING | CCP-06 | Metal detection | ≤ 0.5 ppm | Every 1 min |
| **Pet Food** (PLT-004) | EXTRUSION | CCP-10 | Extrusion temp | 130–155°C | Every 5 min |
| | RETORT_CANNING | CCP-04 | Retort temp | 118–130°C | Every 5 min |
| | RETORT_CANNING | CCP-05 | Retort pressure | 0.95–1.15 bar | Every 5 min |
| | KIBBLE_COATING | CCP-P4 | Moisture activity (aw) | ≤ 0.65 | Every 30 min |
| **Prepared Foods** (PLT-005) | MIXING_COOKING | CCP-09 | Cooking temp | 90–100°C | Every 5 min |
| | FILLING | CCP-F2 | Fill temp (hot-fill) | ≥ 85°C | Every 5 min |
| | NOODLE_LINE | CCP-N3 | Frying oil temp | 140–160°C | Every 5 min |

#### 3.1.2 Scheduling Impact of CCPs

CCPs constrain production scheduling in three ways:

1. **Hold-and-release times.** When a CCP reading deviates from critical limits, the batch enters a hold status. The `HoldRelease` dataclass in `regulatory.py` models this. Typical hold durations:
   - Micro hold (routine sampling): 24–72 hours for dairy/UHT, 48 hours for pet food canning.
   - Deviation hold (out-of-spec CCP): 2–48 hours pending QA review. The simulation uses 80/15/5 split (release/rework/destroy).
   - Positive-release (infant formula, medical nutrition): 100% of batches held until lab results clear — not modeled in NexusFab but relevant for dairy plants producing infant formula.

   **Scheduling implication:** Hold batches occupy warehouse buffer space. The scheduler must account for ~3–5% of daily output being in hold status, requiring buffer tank/silo availability between the production line and shipping dock.

2. **Temperature monitoring windows.** CCPs like pasteurization (CCP-01) require continuous monitoring. If the monitoring instrument goes offline, production must stop within the corrective action time limit (typically 1–15 minutes). This creates unplanned downtime that the scheduler should model as a stochastic interruption — currently handled by the `in_spec` probability in `generate_compliance_report()` (97% in-spec rate).

3. **Testing intervals and line stoppages.** Metal detection CCPs (CCP-06, CCP-C3) require periodic verification with test pieces. The line pauses for 30–60 seconds every 1–4 hours. Retort CCPs require thermocouple calibration at start of shift (15–20 min). These micro-stoppages reduce effective OEE by 1–3%.

#### 3.1.3 Gaps in Current Implementation

The `HACCP_CCPS` dict in `regulatory.py` is missing entries for several line types: `PET_BOTTLING`, `GLASS_BOTTLING`, `CANNING`, `WRAPPING`, `KIBBLE_COATING`, `FILLING`, `NOODLE_LINE`. Per the existing learning note, any plant whose lines lack CCP entries will report 0% CCP compliance. These should be added to match the table above.

---

### 3.2 FSSC 22000

FSSC 22000 (Food Safety System Certification, based on ISO 22000 + sector-specific PRPs from ISO/TS 22002-1) is the dominant GFSI-benchmarked certification scheme for food manufacturers. Nestlé mandates FSSC 22000 across all factories.

#### 3.2.1 Prerequisite Programs (PRPs) Affecting Scheduling

PRPs are baseline conditions that must be maintained regardless of what is being produced. Key PRPs with scheduling impact:

| PRP Category | ISO/TS 22002-1 Clause | Scheduling Constraint |
|---|---|---|
| **Cleaning & sanitation** | Clause 11 | Minimum cleaning frequency per line type. Dairy UHT lines: CIP every 18–24 hours of continuous production. Pet food extrusion: dry clean every shift change. |
| **Pest control** | Clause 12 | Monthly fumigation windows: 4–8 hours, full plant or zone shutdown. Schedule around low-demand periods. |
| **Water quality** | Clause 6 | Water plant (PLT-001): daily micro testing of source water. Positive result → 4–6 hour line shutdown for investigation. |
| **Maintenance** | Clause 8 | Preventive maintenance must not compromise food safety. Post-maintenance CIP required if equipment was opened. Adds 45–75 min to maintenance downtime. |
| **Personnel hygiene** | Clause 13 | Shift changeovers include 15-min hygiene transition. High-care zones (dairy, infant) require gowning rooms — creates a bottleneck at shift boundaries. |

#### 3.2.2 Operational PRPs (OPRPs)

OPRPs are control measures for significant hazards that are not managed at CCPs. Unlike PRPs, OPRPs require monitoring and corrective actions similar to CCPs but with more flexibility.

| OPRP | Applies To | Monitoring | Scheduling Impact |
|---|---|---|---|
| Allergen cleaning verification | All multi-allergen lines | ATP swab + visual + allergen-specific ELISA/LFD after each allergen CIP | Results take 15–30 min for rapid LFD, 4–8 hours for ELISA. Line cannot start next product until verification passes. |
| Foreign body control | All lines | X-ray / metal detector checks at defined intervals | 30–60 sec micro-stops per check cycle. Detector failure = line stop until repaired. |
| Environmental monitoring | Dairy, pet food | Air/surface sampling in production zones weekly | Positive Listeria finding → zone shutdown (8–24 hours) for deep clean. Stochastic event. |
| Temperature control (storage) | Dairy, prepared foods | Warehouse ambient monitoring | Not a line constraint, but affects finished-goods throughput if cold storage is at capacity. |

#### 3.2.3 Audit Impact on Line Availability

FSSC 22000 requires:
- **Announced surveillance audits**: 1/year, 2–3 days. Lines may run during audit but must be available for inspector walkthrough. Reduce changeover activity during audit days to minimize complexity.
- **Unannounced audits**: 1 per 3-year certification cycle. No scheduling preparation possible — the plant must always be audit-ready.
- **Internal audits**: quarterly per FSSC 22000 requirements. Each internal audit covers 2–3 lines for 4–6 hours. The line runs but QA staff are diverted.

**Net scheduling impact:** ~6–10 days/year of reduced flexibility per plant due to audits.

---

### 3.3 GMP (Good Manufacturing Practice)

GMP requirements (21 CFR 110/117 in the US; EC 2023/2006 and 852/2004 in the EU) establish baseline facility, equipment, personnel, and documentation standards.

#### 3.3.1 Facility & Equipment Requirements

| Requirement | Scheduling Constraint |
|---|---|
| Equipment must be cleanable and in good repair | Post-maintenance verification (functionality + cleanliness) adds 30–60 min before production restart |
| Separate zones for raw, in-process, and finished goods | Material flow routing limits which lines can run concurrently if shared corridors exist |
| Adequate lighting (540 lux at inspection points) | Night shifts in older facilities may need lighting checks at shift start |
| Temperature-controlled zones for sensitive ingredients | Ingredient staging time limited to 2–4 hours outside cold storage — constrains batch start windows |

#### 3.3.2 Personnel & Documentation

- **Training records:** Every operator must have documented training for each line they work. The workforce scheduler (`nexusfab/optimization/workforce.py`) should enforce skill-certification constraints — an operator without CCP-monitoring training cannot be assigned to a CCP-monitored line.
- **Batch records:** Every batch requires a completed production record before release. Documentation review takes 15–30 min per batch by QA. This is a downstream bottleneck, not a line constraint, but it affects how many batches can be released per shift.
- **Changeover documentation:** Each changeover must be documented with before/after inspection, CIP records, and line clearance verification. This adds 10–15 min of documentation time on top of physical changeover time.

#### 3.3.3 Impact on Changeover Procedures

GMP requires formal line clearance between products. The changeover procedure (already modeled in `nexusfab/seed/products.py` via `CHANGEOVER_MATRIX`) must include:

1. **Line clearance** (visual inspection for previous product residue): 5–10 min
2. **Documentation** (record previous batch end, changeover start, inspections): 10–15 min
3. **Physical changeover** (format parts, labels, packaging materials): varies by format change — 15–120 min per `changeover_minutes` in product seed data
4. **CIP if required** (allergen transition or time-based): 45–120 min per `CIP_TYPES` in `regulatory.py`
5. **Post-CIP verification** (ATP swab, visual, allergen test): 15–30 min
6. **First-article inspection** (QA approves first units off line): 10–20 min

Total changeover including GMP overhead: **physical time × 1.3–1.6** depending on whether CIP and allergen verification are needed. The current `get_changeover_time()` function in `products.py` accounts for the physical + CIP portion but not the documentation/verification overhead.

---

## Section 4 — Allergen Management & CIP Protocols

### 4.1 Regulatory Allergen Lists

#### 4.1.1 EU Big 14 Allergens (Regulation EU 1169/2011)

1. Cereals containing gluten (wheat, rye, barley, oats, spelt, kamut)
2. Crustaceans
3. Eggs
4. Fish
5. Peanuts
6. Soybeans
7. Milk (including lactose)
8. Nuts (almonds, hazelnuts, walnuts, cashews, pecans, Brazil nuts, pistachios, macadamia)
9. Celery
10. Mustard
11. Sesame seeds
12. Sulphur dioxide / sulphites (> 10 mg/kg)
13. Lupin
14. Molluscs

#### 4.1.2 US Big 9 Allergens (FALCPA 2004 + FASTER Act 2021)

1. Milk
2. Eggs
3. Fish
4. Crustacean shellfish
5. Tree nuts
6. Peanuts
7. Wheat
8. Soybeans
9. Sesame

#### 4.1.3 NexusFab Allergen Coverage

The current product catalog uses 4 allergens: `GLUTEN`, `DAIRY`, `NUTS`, `SOY`. Mapped to regulatory lists:

| NexusFab Code | EU Big 14 | US Big 9 | Plants Affected |
|---|---|---|---|
| `GLUTEN` | #1 (cereals w/ gluten) | #7 (wheat) | PLT-002 (confectionery), PLT-005 (prepared) |
| `DAIRY` | #7 (milk) | #1 (milk) | PLT-002 (confectionery), PLT-003 (dairy) |
| `NUTS` | #8 (tree nuts) / #5 (peanuts) | #5 (tree nuts) / #6 (peanuts) | PLT-002 (confectionery) |
| `SOY` | #6 (soybeans) | #8 (soybeans) | PLT-005 (prepared foods) |

PLT-001 (water) and PLT-004 (pet food) have no allergen-containing products in the current catalog. Pet food is exempt from human allergen labeling but cross-contamination matters for dual-use facilities.

---

### 4.2 Allergen Sequencing Rules

The fundamental principle: **schedule non-allergen products first, then allergen-containing products, ordered by increasing allergen severity.** This minimizes CIP events and cross-contact risk.

#### 4.2.1 Transition Types & Required Cleaning

| Transition | Cleaning Required | Duration | Example |
|---|---|---|---|
| **Same allergen profile → same** | Dry clean or none | 0–15 min | CON-KB4 → CON-KBD (both GLUTEN+DAIRY) |
| **No allergen → allergen** | Dry clean (dedicated line) or standard CIP (shared line) | 15–45 min | WAT-500S → DAI-L2 (introducing DAIRY) |
| **Lower allergen → higher allergen** | Standard CIP | 45 min | CON-KB4 (GLUTEN+DAIRY) → CON-NUT (GLUTEN+DAIRY+NUTS) |
| **Higher allergen → lower allergen** | Full allergen CIP + verification | 75–90 min | CON-NUT → CON-AER (removing NUTS+GLUTEN, keeping DAIRY) |
| **Allergen → no allergen** | Deep clean CIP + ELISA verification | 90–120 min | CON-NUT → non-allergen product |
| **Nut-containing → nut-free** | Full wet CIP + validated allergen-specific test | 90 min | CON-NUT → CON-KB4 (highest risk transition) |

The `check_allergen_sequence()` function in `regulatory.py` implements a simplified version: CIP required when new allergens are introduced (forward transition) and 90-min full CIP for reverse transitions (allergen → non-allergen). The `ALLERGEN_SEVERITY` dict drives CIP duration scaling: `base 30 min + 15 min × severity` per new allergen.

#### 4.2.2 Optimal Sequencing Algorithm

The CP-SAT solver in `scheduling.py` enforces a hard constraint: all non-allergen orders are sequenced before allergen orders on each line (`pos[non_allergen] < pos[allergen]`). Within allergen-containing products, the solver minimizes changeover cost which implicitly clusters same-allergen-profile products.

**Ideal production sequence per line (single shift):**

```
non-allergen → SOY-only → GLUTEN-only → DAIRY-only → GLUTEN+DAIRY → GLUTEN+DAIRY+NUTS
     ↑              ↑           ↑            ↑              ↑               ↑
   no clean     dry clean   dry clean    std CIP        dry clean      std CIP
                 (15 min)    (15 min)    (45 min)       (0–15 min)     (45 min)
```

Running in this order requires only 2 CIP events instead of up to 5 if random-ordered.

#### 4.2.3 Allergen Matrix by Plant Type

**PLT-002 (Confectionery)** — the most complex allergen plant:

| From ↓ / To → | CON-AER (DAIRY) | CON-KB4 (GL+DA) | CON-KBD (GL+DA) | CON-KBW (GL+DA) | CON-NUT (GL+DA+NU) | CON-MP8 (GL+DA) | CON-QST (GL+DA+NU) |
|---|---|---|---|---|---|---|---|
| CON-AER | — | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) |
| CON-KB4 | Full CIP (75m) | — | Dry (15m) | Dry (15m) | Std CIP (45m) | Dry (15m) | Std CIP (45m) |
| CON-NUT | Full CIP (90m) | Full CIP (75m) | Full CIP (75m) | Full CIP (75m) | — | Full CIP (75m) | Dry (15m) |

**PLT-005 (Prepared Foods):**

| From ↓ / To → | PRE-S8 (none) | PRE-SC5 (none) | PRE-N70 (GL+SOY) | PRE-SC2 (SOY+GL) | PRE-N5P (GL+SOY) | PRE-CUP (GL+SOY) |
|---|---|---|---|---|---|---|
| PRE-S8 (none) | — | Dry (15m) | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) | Std CIP (45m) |
| PRE-N70 (GL+SOY) | Deep CIP (120m) | Deep CIP (120m) | — | Dry (15m) | Dry (15m) | Dry (15m) |

**PLT-003 (Dairy):** All products contain DAIRY only. No allergen transitions within the plant — standard time-based CIP only (every 18–24 hours).

**PLT-001 (Water), PLT-004 (Pet Food):** No allergen-containing products. CIP is hygiene-driven, not allergen-driven.

---

### 4.3 CIP (Clean-in-Place) Protocols

CIP is the automated cleaning of equipment internals without disassembly. The `CIP_TYPES` dict in `regulatory.py` defines three tiers.

#### 4.3.1 CIP Stages & Durations

**Standard CIP (45 min total):**

| Stage | Duration | Temp | Chemical | Concentration | Purpose |
|---|---|---|---|---|---|
| 1. Pre-rinse | 5 min | Ambient | Water | — | Remove gross soil |
| 2. Caustic wash | 15 min | 70–80°C | NaOH (caustic soda) | 1.0–2.0% w/v | Dissolve proteins, fats |
| 3. Intermediate rinse | 5 min | Ambient | Water | — | Remove caustic residue |
| 4. Acid wash | 10 min | 60–70°C | Phosphoric or nitric acid | 0.5–1.0% w/v | Remove mineral scale |
| 5. Final rinse | 5 min | Ambient | Water | — | Remove acid residue |
| 6. Sanitize | 5 min | Ambient | Peracetic acid | 0.1–0.2% | Kill residual microorganisms |

**Allergen CIP (75 min total):**

All stages above plus:

| Additional Stage | Duration | Chemical | Purpose |
|---|---|---|---|
| 7. Allergen rinse | 15 min | Dedicated allergen-removal surfactant | Break down allergen proteins (e.g., casein, gluten) |
| 8. Verification hold | 15 min | — | Wait for rapid allergen test (lateral flow device) result before line release |

**Deep Clean CIP (120 min total):**

All stages above plus:

| Additional Stage | Duration | Chemical | Purpose |
|---|---|---|---|
| 9. Enzymatic wash | 20 min | Protease/lipase enzyme blend | Break down baked-on or heat-denatured allergen residues |
| 10. Extended hot rinse | 10 min | Water at 85°C+ | Thermal sanitization of dead legs and valve cavities |

#### 4.3.2 Resource Consumption per CIP Cycle

| Resource | Standard (45m) | Allergen (75m) | Deep Clean (120m) |
|---|---|---|---|
| Water | 3,000–5,000 L | 5,000–8,000 L | 8,000–12,000 L |
| Caustic (NaOH) | 15–30 kg | 15–30 kg | 25–40 kg |
| Acid | 8–15 kg | 8–15 kg | 12–20 kg |
| Sanitizer | 2–4 L | 2–4 L | 3–6 L |
| Allergen surfactant | — | 5–10 L | 5–10 L |
| Enzyme blend | — | — | 3–5 L |
| Steam (for heating) | 200–400 kg | 300–600 kg | 500–900 kg |
| Electricity | 15–25 kWh | 25–40 kWh | 40–60 kWh |

#### 4.3.3 CIP Scheduling Windows

CIP events should be scheduled considering:

1. **Mandatory triggers:**
   - Allergen transition (per allergen matrix in §4.2)
   - Maximum continuous production time exceeded (18–24h for dairy UHT, 48–72h for water, 12–16h for pet food wet)
   - CCP deviation requiring corrective action
   - Post-maintenance when equipment internals were exposed

2. **Preferred scheduling windows:**
   - Between shifts (reduce impact on OEE — CIP during shift handover overlap)
   - Before weekend/holiday shutdown (combine with planned maintenance)
   - After longest production run to batch CIP with natural break

3. **CIP system constraints:**
   - Most plants have 1–2 CIP skids shared across lines. Only 1–2 lines can CIP simultaneously.
   - CIP supply tank capacity limits back-to-back CIP runs — 30-min recovery time between cycles for chemical preparation.
   - Wastewater treatment capacity may limit CIP frequency (esp. caustic wash effluent).

4. **Interaction with `nexusfab/simulation/line_model.py`:**
   - Line status enum includes `CIP` as a discrete state (`nexusfab/models/enums.py:LineStatus.CIP`).
   - The scheduler should model CIP as a non-preemptible block on the line timeline, similar to `CHANGEOVER` but longer.
   - CIP records generated in `regulatory.py` track `triggered_by` as `"allergen_transition"`, `"scheduled"`, or `"deviation"`.

#### 4.3.4 CIP Validation & Line Release

After every CIP, before the line can resume production:

| Validation Step | Duration | Method | Pass Criteria |
|---|---|---|---|
| Visual inspection | 5 min | Operator visual | No visible residue, correct reassembly |
| ATP bioluminescence | 5 min | Swab + luminometer | < 10 RLU (relative light units) at critical points |
| Allergen rapid test (if allergen CIP) | 15–30 min | Lateral flow device (LFD) | Below LOD for target allergen(s) |
| Allergen ELISA (if nut transition) | 4–8 hours | Lab ELISA | < 2.5 ppm for target allergen |
| Conductivity check | 2 min | Inline sensor | Final rinse water conductivity ≤ source water + 10 μS/cm |
| pH check | 2 min | Inline sensor | Final rinse pH within 6.5–7.5 |

The `CIPRecord.validated` boolean in `regulatory.py` currently models this as a single pass/fail with 95% pass rate. The 5% failure rate triggers re-CIP, adding 45–120 min to the schedule.

---

### 4.4 Implementation Recommendations for NexusFab

Based on this research, the following gaps should be addressed in the optimizer:

1. **Expand `HACCP_CCPS`** to cover all 14 line types (7 currently missing — see §3.1.3).
2. **Add GMP overhead multiplier** to `get_changeover_time()`: documentation + verification adds ~30% to physical changeover time.
3. **Model CIP skid contention**: shared CIP resources mean only 1–2 lines per plant can CIP simultaneously. The scheduler should treat CIP skids as a shared resource with capacity constraints.
4. **Expand allergen set**: the current 4 allergens (`GLUTEN`, `DAIRY`, `NUTS`, `SOY`) cover the major risk profiles, but adding `EGGS` and `SESAME` would align with both EU Big 14 and US Big 9 for dairy and prepared food plants.
5. **Add time-based CIP triggers**: currently CIP is only triggered by allergen transitions. Dairy UHT lines need mandatory CIP every 18–24h of production regardless of allergen profile.
6. **Model CIP validation time**: the 15–30 min verification hold after allergen CIP is not currently included in the changeover timeline.

---

*Compiled for NexusFab production scheduling optimizer. Sources: Codex Alimentarius HACCP guidelines (CAC/RCP 1-1969 Rev. 4), ISO 22000:2018, ISO/TS 22002-1:2009, FSSC 22000 v6, EU Regulation 1169/2011, US FALCPA 2004, FASTER Act 2021, 21 CFR 117, industry CIP engineering references.*
