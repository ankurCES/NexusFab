# Production Operations Research

## 1. OEE Benchmarks by Product Type

OEE = Availability × Performance × Quality. Percentages are of scheduled
production time (planned downtime already removed before calculating Availability).

### 1.1 World-Class vs Typical Ranges

| Product Type | Availability% | Performance% | Quality% | **OEE%** | Notes |
|---|---|---|---|---|---|
| **Water bottling** — world-class | 93–96 | 93–96 | 99.5–99.9 | **87–92** | High-speed PET; minimal changeover |
| **Water bottling** — typical | 82–90 | 80–90 | 98–99.5 | **60–73** | PLT-001 seed: 62% → target 80% |
| **Confectionery** — world-class | 88–92 | 88–92 | 98.5–99.5 | **76–84** | Enrobing & wrapping lines |
| **Confectionery** — typical | 72–82 | 70–82 | 97–99 | **50–63** | PLT-002 seed: 55% → target 78% |
| **Dairy UHT** — world-class | 86–90 | 88–92 | 99–99.8 | **75–82** | Aseptic lines; long CIP cycles dominate |
| **Dairy UHT** — typical | 68–78 | 75–85 | 97.5–99 | **50–62** | PLT-003 seed: 48% → target 72% |
| **Dairy yogurt** — world-class | 84–89 | 86–90 | 98–99 | **72–79** | Fermentation dwell adds schedule risk |
| **Dairy yogurt** — typical | 66–76 | 72–82 | 96–98 | **46–58** | |
| **Pet food dry (extrusion)** — world-class | 88–92 | 87–92 | 99–99.5 | **76–84** | Dryer is OEE bottleneck |
| **Pet food dry (extrusion)** — typical | 76–86 | 75–85 | 97–99 | **56–68** | PLT-004 seed: 60% → target 78% |
| **Pet food wet (retort)** — world-class | 85–90 | 83–88 | 98.5–99.5 | **70–79** | Retort cycle time limits Performance |
| **Pet food wet (retort)** — typical | 72–82 | 70–80 | 97–99 | **50–63** | |
| **Prepared foods frozen** — world-class | 85–90 | 86–90 | 97.5–99 | **71–80** | Tunnel freezer failures are long MTTR |
| **Prepared foods frozen** — typical | 70–80 | 72–82 | 95.5–98 | **48–60** | PLT-005 seed: 52% → target 72% |
| **Prepared foods chilled** — world-class | 83–88 | 84–89 | 97–98.5 | **68–75** | |
| **Prepared foods chilled** — typical | 66–76 | 70–80 | 94–97 | **44–56** | |

> **Simulation anchor**: all `starting_oee` values in `nexusfab/seed/plants.py` sit at
> or below the typical floor for each category — intentional to show improvement
> headroom. World-class targets are achievable with PdM + SMED.

### 1.2 OEE Loss Distribution (typical plant)

| Loss Bucket | Component | Typical loss |
|---|---|---|
| Unplanned breakdowns | Availability | 6–10% |
| Changeovers / CIP | Availability | 4–8% |
| Minor stoppages / jams | Performance | 5–10% |
| Speed loss (running under rated) | Performance | 4–8% |
| Startup / transition scrap | Quality | 0.5–1.5% |
| In-process defects | Quality | 0.3–1.0% |

### 1.3 Planned Downtime Patterns

Planned downtime is **excluded from the OEE denominator** but must be modelled in
shift scheduling to avoid over-committing capacity.

#### CIP Schedules by Line Type

| Line Type | CIP Frequency | CIP Duration | Trigger |
|---|---|---|---|
| PET_BOTTLING / CANNING | Every 24 h (end-of-day) | 45–60 min | Daily micro reset |
| GLASS_BOTTLING | Every 24 h | 60–90 min | Rinse harder for glass residue |
| UHT_FILLING | Every 8–12 h | 90–120 min per cycle | Aseptic lines cannot exceed 12 h without CIP |
| ASEPTIC | Every 8 h | 90–150 min | FDA/FSMA aseptic process requirement |
| POWDER_PACKING | Every 48 h | 60–90 min | Dry product; less frequent wet clean |
| MOULDING / ENROBING | Every 24 h | 60–90 min | Chocolate fat bloom risk |
| WRAPPING | Every 48 h | 30–45 min | Film dust accumulation |
| EXTRUSION / DRYER | Every 24 h | 90–120 min | Kibble fines, fat, meat residue |
| RETORT_CANNING | Weekly (Saturdays) | 4–6 h | Retort chamber + filler deep clean |
| KIBBLE_COATING | Every 24 h | 60–90 min | Fat coating clogs if left overnight |
| MIXING_COOKING | Every 8 h (each shift) | 45–60 min | Allergen cross-contamination risk |
| FILLING (sauces) | Every 12 h | 30–45 min | High-acid products; micro risk |
| NOODLE_LINE | Every 24 h | 60–75 min | Fryer/dryer oil residue |

#### Planned Maintenance Windows

| Plant | Weekly PM window | Monthly deep PM | Annual shutdown |
|---|---|---|---|
| PLT-001 (Water) | Sun 02:00–06:00 (4 h) | 1st Mon/month 00:00–08:00 | 2 weeks Q1 |
| PLT-002 (Confec) | Sun 00:00–08:00 (8 h) | 1st Sat/month 06:00–14:00 | 1 week Q3 |
| PLT-003 (Dairy) | Sat 22:00–Sun 06:00 (8 h) | Last Fri/month 18:00–06:00 | 2 weeks Q2 |
| PLT-004 (Pet Food) | Sat 06:00–14:00 (8 h) | 3rd Sat/month 00:00–16:00 | 10 days Q4 |
| PLT-005 (Prepared) | Sun 04:00–12:00 (8 h) | 2nd Sun/month 00:00–12:00 | 1 week Q1 |

#### Shift Changeover Gaps (all plants: 3 × 8-hour shifts)

| Gap type | Duration | Activity |
|---|---|---|
| Standard handover | 15 min | Operator briefing, log review |
| Shift with scheduled CIP | 60–150 min | CIP runs across shift boundary |
| Shift with format changeover | 30–180 min | Product/pack-size change (see §5.1 matrix) |
| Shift after PM window | 30 min | Re-commissioning, speed ramp-up |

**Total planned downtime budget per plant per week:**

| Plant | CIP | PM | Shift gaps | Total | % of 168 h |
|---|---|---|---|---|---|
| PLT-001 | ~12 h | 4 h | 3 h | **~19 h** | 11% |
| PLT-002 | ~18 h | 8 h | 3 h | **~29 h** | 17% |
| PLT-003 | ~28 h | 8 h | 3 h | **~39 h** | 23% — aseptic every 8 h |
| PLT-004 | ~20 h | 8 h | 3 h | **~31 h** | 18% |
| PLT-005 | ~16 h | 8 h | 3 h | **~27 h** | 16% |

---

## 2. Line Speed Data & Plant Configuration

Speeds are **rated throughput** — 100% Performance. Actual = rated × OEE.
Source: `nexusfab/seed/plants.py` `speed_units_per_min` + industry handbook cross-check.

### 2.1 PLT-001 — NexWater-East (Water Bottling)

| Plant attribute | Value |
|---|---|
| Category | WATER |
| Location | Eastern Region (40.71°N, 74.01°W) |
| Plant capacity | 1,400 t/day |
| Lines | 4 |
| Starting OEE | 62% → target 80% |

| Line | Type | Unit | Rated/min | Rated/hr | Actual/hr @ 62% | Bottleneck equip (MTBF) |
|---|---|---|---|---|---|---|
| PLT-001-L1 | PET_BOTTLING | 500 mL bottles | 600 | 36,000 | ~22,320 | FILLER (160 h) |
| PLT-001-L2 | PET_BOTTLING | 1.5 L bottles | 500 | 30,000 | ~18,600 | FILLER (180 h) |
| PLT-001-L3 | GLASS_BOTTLING | 750 mL glass | 400 | 24,000 | ~14,880 | FILLER (140 h) |
| PLT-001-L4 | CANNING | 330 mL cans | 700 | 42,000 | ~26,040 | FILLER (200 h) |

Industry context: high-speed PET water lines (Sidel, Krones) run 600–1,200 bpm.
PLT-001-L1 at 600 bpm is a mid-tier line; world-class is 1,200 bpm.

**Product compatibility**: L1/L2 → PET water (all sizes); L3 → glass still/sparkling;
L4 → canned still/sparkling. No cross-product capability.

---

### 2.2 PLT-002 — NexConfec-Central (Confectionery)

| Plant attribute | Value |
|---|---|
| Category | CONFECTIONERY |
| Location | Central Region (41.88°N, 87.63°W) |
| Plant capacity | 140 t/day |
| Lines | 3 |
| Starting OEE | 55% → target 78% |

| Line | Type | Unit | Rated/min | Rated/hr | Actual/hr @ 55% | Bottleneck equip (MTBF) |
|---|---|---|---|---|---|---|
| PLT-002-L1 | MOULDING | bars/pieces | 400 | 24,000 | ~13,200 | FILLER (130 h) |
| PLT-002-L2 | ENROBING | coated bars | 300 | 18,000 | ~9,900 | FILLER (150 h) |
| PLT-002-L3 | WRAPPING | wrapped bars | 500 | 30,000 | ~16,500 | FILLER (170 h) |

Industry context: chocolate bar wrapping lines (Theegarten, Sollich) run 400–800
bars/min. Enrobing is slower due to tempering + cooling tunnel dwell.
L2 feeds L3 (enrobe → wrap) for finished confectionery.

**Product compatibility**: L1 → moulded chocolate bars; L2 → enrobed bars/biscuits;
L3 → wrapped sweets/candy.

---

### 2.3 PLT-003 — NexDairy-North (Dairy)

| Plant attribute | Value |
|---|---|
| Category | DAIRY |
| Location | Northern Region (44.98°N, 93.27°W) |
| Plant capacity | 550 t/day |
| Lines | 3 |
| Starting OEE | 48% → target 72% |

| Line | Type | Unit | Rated/min | Rated/hr | Actual/hr @ 48% | Bottleneck equip (MTBF) |
|---|---|---|---|---|---|---|
| PLT-003-L1 | UHT_FILLING | 1 L Tetra Pak | 300 | 18,000 | ~8,640 | PASTEURIZER (350 h) |
| PLT-003-L2 | POWDER_PACKING | powder tins | 350 | 21,000 | ~10,080 | PASTEURIZER (380 h) |
| PLT-003-L3 | ASEPTIC | aseptic pouches | 250 | 15,000 | ~7,200 | FILLER (120 h — lowest MTBF in fleet) |

Industry context: Tetra Pak TBA/22 runs ≈6,000–7,000 packs/hr (100–117/min);
PLT-003-L1 at 300/min implies a multi-head large-format line. Aseptic lines are
slowest due to sterilisation dwell.

PLT-003 has the lowest OEE in the fleet (48%) — aseptic line CIP every 8 h is the
primary driver. FILLER MTBF of 120 h on L3 also depresses Availability.

**Product compatibility**: L1 → UHT milk/cream (Tetra Pak); L2 → milk powder
tins/bags; L3 → aseptic UHT specialty (lactose-free, fortified).

---

### 2.4 PLT-004 — NexPet-South (Pet Food)

| Plant attribute | Value |
|---|---|
| Category | PET_FOOD |
| Location | Southern Region (33.75°N, 84.39°W) |
| Plant capacity | 420 t/day |
| Lines | 4 |
| Starting OEE | 60% → target 78% |

| Line | Type | Unit | Rated/min | Rated/hr | Actual/hr @ 60% | Bottleneck equip (MTBF / MTTR) |
|---|---|---|---|---|---|---|
| PLT-004-L1 | EXTRUSION | kg dry kibble | 500 | 30,000 kg | ~18,000 kg | DRYER (380 h / **5 h MTTR** — longest) |
| PLT-004-L2 | EXTRUSION | kg dry kibble | 450 | 27,000 kg | ~16,200 kg | DRYER (400 h / 4 h MTTR) |
| PLT-004-L3 | RETORT_CANNING | 400 g cans | 300 | 18,000 | ~10,800 | FILLER (140 h) |
| PLT-004-L4 | KIBBLE_COATING | coated kg | 400 | 24,000 kg | ~14,400 kg | MIXER (500 h — most reliable in fleet) |

Industry context: twin-screw extruders (Bühler, Clextral) output 500–5,000 kg/hr.
Dryer MTTR of 5 h means a single breakdown cancels most of a shift.
L4 takes dry base from L1 or L2 as input — scheduling dependency.

**Product compatibility**: L1/L2 → dry kibble (all sizes); L3 → wet canned pet food;
L4 → fat/palatant-coated kibble (depends on L1/L2 output).

---

### 2.5 PLT-005 — NexPrepared-West (Prepared Foods)

| Plant attribute | Value |
|---|---|
| Category | PREPARED_FOODS |
| Location | Western Region (34.05°N, 118.24°W) |
| Plant capacity | 220 t/day |
| Lines | 3 |
| Starting OEE | 52% → target 72% |

| Line | Type | Unit | Rated/min | Rated/hr | Actual/hr @ 52% | Bottleneck equip (MTBF) |
|---|---|---|---|---|---|---|
| PLT-005-L1 | MIXING_COOKING | meal trays | 250 | 15,000 | ~7,800 | MIXER (350 h) |
| PLT-005-L2 | FILLING | seasoning sachets | 300 | 18,000 | ~9,360 | FILLER (160 h) |
| PLT-005-L3 | NOODLE_LINE | noodle blocks | 280 | 16,800 | ~8,736 | FILLER (130 h — lowest in plant) |

Industry context: Maggi/Nissin-format instant noodle lines run 150–400 blocks/min
depending on block size and fryer/dryer length. L2 output frequently co-packs
with L3 (seasoning sachet inside noodle pack) — schedule these together.

**Product compatibility**: L1 → cooked meal bases/sauces; L2 → seasoning sachets;
L3 → instant noodle blocks.

---

### 2.6 Cross-Plant Product Compatibility Matrix

| Product Type | PLT-001 | PLT-002 | PLT-003 | PLT-004 | PLT-005 |
|---|---|---|---|---|---|
| Still/sparkling water | ✓ L1–L4 | — | — | — | — |
| Chocolate / candy bars | — | ✓ L1–L3 | — | — | — |
| UHT milk / dairy | — | — | ✓ L1,L3 | — | — |
| Dairy powder | — | — | ✓ L2 | — | — |
| Dry pet food kibble | — | — | — | ✓ L1,L2,L4 | — |
| Wet pet food (canned) | — | — | — | ✓ L3 | — |
| Prepared meal bases | — | — | — | — | ✓ L1 |
| Instant noodles | — | — | — | — | ✓ L3 |
| Seasoning sachets | — | — | — | — | ✓ L2 |

No cross-plant product flexibility currently modelled — each plant is single-category.
Only intra-plant dependency worth explicit scheduling: PLT-004 L4 (KIBBLE_COATING)
requires dry-base input from L1 or L2.

---

## 3. Line Rerouting Decision Algorithm

When a production line goes down — planned or unplanned — the system evaluates alternatives in strict priority order before accepting downtime. The algorithm lives at ISA-95 Level 3 (MES) with cost sign-off escalating to Level 4 (ERP/planning) above a configurable threshold.

---

### 3.1 Decision Tree

```
LINE DOWN EVENT
│
├─ [STEP 1] Same-plant alternative lines
│   ├─ Query: lines in same plant with compatible constraints (§3.2)
│   ├─ If ≥1 feasible → score (§3.4) → REROUTE (local)
│   └─ None feasible → proceed to Step 2
│
├─ [STEP 2] Cross-plant alternatives
│   ├─ Query: lines at peer plants with compatible constraints
│   ├─ Add transport cost & time to score (§3.3, §3.4)
│   ├─ If ≥1 feasible → score → REROUTE (cross-plant)
│   │   └─ If cross-plant cost > threshold → escalate to ERP for approval
│   └─ None feasible → proceed to Step 3
│
├─ [STEP 3] Partial rerouting
│   ├─ Split order across multiple lines (none individually fully compatible)
│   ├─ Evaluate: sum-of-partial-scores < full-downtime cost?
│   ├─ If yes → PARTIAL REROUTE (may require planner manual override in MES)
│   └─ No viable split → proceed to Step 4
│
└─ [STEP 4] Accept downtime
    ├─ Log event with root cause classification
    ├─ Trigger expedite order or customer notification
    └─ Update demand plan (feed back to Level 4 ERP)
```

**Feasibility gate** — a line must pass ALL to enter scoring:

| Gate | Fail condition |
|------|---------------|
| Allergen | Target line ran allergen not in this SKU's tolerance set AND changeover exceeds slack |
| Format | Package/bottle size or fill type mismatch; retooling exceeds available window |
| CIP | Required CIP class duration pushes start beyond order due time |
| Capacity | `current_utilization + rerouted_load > rated_capacity × 0.95` |
| Transport | `transit_time + buffers > remaining order slack` (cross-plant only) |

---

### 3.2 Constraint Matrix

#### 3.2.1 Allergen Compatibility

Each line carries an allergen history vector. A reroute is permitted if the target line's declared allergens are a subset of the SKU's allergen tolerance set, OR a verified changeover can complete within available slack.

| Allergen Group | CIP Class Required | Minimum Changeover Window |
|----------------|--------------------|--------------------------|
| Tree nuts | Class A (full strip) | 4 h |
| Peanut | Class A (full strip) | 6 h |
| Gluten (wheat/rye/barley) | Class B (hot flush) | 2 h |
| Dairy (milk/whey) | Class B (hot flush) | 2 h |
| Egg | Class B (hot flush) | 2 h |
| Soy | Class C (standard) | 45 min |
| Sulphites | Class C (standard) | 30 min |
| Free-from (no allergens declared) | — | 0 |

Compatibility check: `allergen_ok = (line_allergens ⊆ sku_tolerance) OR (changeover_duration ≤ slack)`.

#### 3.2.2 Package / Format Match

Format compatibility is a static lookup per line — tagged with primary packaging type, filler type, cap/seal type, and label applicator width range.

| Constraint | Check |
|------------|-------|
| Primary pack type (bag, pouch, bottle, can, tray) | Exact match required |
| Container volume range [min, max] | SKU volume ∈ line range |
| Label width | SKU label width ∈ line applicator range |
| Case packer format | SKU case config supported by target line |

A line fails this gate if any sub-check fails and retooling takes longer than available slack.

#### 3.2.3 CIP Requirement Between Products

CIP class is determined by the product transition matrix `cip_class(prev_sku, incoming_sku)`, maintained in the MES product library. This is the same matrix as section 5.1 but viewed from the rerouting context.

| CIP Class | Description | Typical Duration |
|-----------|-------------|-----------------|
| None | Same product; no changeover needed | 0 min |
| Rinse | Water rinse only | 15 min |
| Standard | Caustic + rinse | 45 min |
| Hot Flush | Caustic + hot water + rinse | 2 h |
| Full Strip | Full disassembly, caustic, sanitize, lab swab | 4–8 h |

The allergen changeover table (§3.2.1) overrides this if it requires a more stringent class.

#### 3.2.4 Rated Capacity Headroom

```
headroom_ok = (current_utilization + rerouted_load) ≤ rated_capacity × 0.95

current_utilization — scheduled volume on target line in the reroute window (cases/h)
rerouted_load       — failed line's order volume ÷ available window (cases/h)
rated_capacity      — line nameplate rate × line OEE factor
0.95 margin         — 5% buffer for minor stoppages; configurable per line
```

#### 3.2.5 Transport Time Between Plants (Cross-Plant Only)

```
transport_ok = transit_time(plant_A, plant_B)
             + loading_buffer
             + unloading_buffer
             ≤ order_slack
```

| Plant Pair | Road km | Standard Transit | Reefer Required |
|------------|---------|-----------------|-----------------|
| Plant 1 → Plant 2 | 120 km | 2.5 h | Yes (dairy/chilled) |
| Plant 1 → Plant 3 | 340 km | 6.0 h | Conditional |
| Plant 2 → Plant 3 | 280 km | 5.0 h | Conditional |
| Plant 1 → Plant 4 | 85 km | 1.8 h | No |

Values are seeded from the plant graph in `simulation/network.py`; update that file to propagate changes here.

---

### 3.3 Cost Function

Total rerouting cost is compared against the full-downtime cost (the baseline if no reroute is taken).

#### 3.3.1 Downtime Cost (Baseline — What Rerouting Avoids)

```
C_downtime = downtime_hours × cost_per_hour(sku)
```

| SKU Category | Downtime Cost / Hour | Basis |
|--------------|---------------------|-------|
| High-margin ambient (snacks, confectionery) | £4,500–£8,000 | Margin × throughput + overhead absorption |
| Standard ambient | £2,000–£3,500 | |
| Chilled / short shelf-life | £6,000–£12,000 | Includes write-off risk at expiry |
| Frozen | £3,000–£6,000 | |
| Promotional / launch SKU | 1.5× base rate | Reputational risk multiplier |
| Customer contract (take-or-pay clause) | Base + contractual penalty rate | Contract-specific |

#### 3.3.2 Transport Cost (Cross-Plant Only)

```
C_transport = units_rerouted × cost_per_unit(plant_A, plant_B)
            + fixed_load_cost(plant_A, plant_B)
```

| Plant Pair | Variable (£/case) | Fixed (£/shipment) | Reefer Surcharge |
|------------|------------------|--------------------|-----------------|
| P1 → P2 | 0.18 | 280 | +40% |
| P1 → P3 | 0.45 | 520 | +40% |
| P2 → P3 | 0.38 | 460 | +40% |
| P1 → P4 | 0.12 | 210 | — |

#### 3.3.3 Quality Risk Premium

```
C_quality = units_rerouted × unit_value × quality_risk_rate(scenario)
```

| Quality Risk Scenario | Risk Rate | Trigger |
|-----------------------|-----------|---------|
| Full allergen CIP, lab swab verified | 0.0% | Post-swab clearance obtained |
| Standard CIP, no swab | 0.5% | Process deviation risk |
| Allergen cross-contact possible | 3.0%–8.0% | Allergen mismatch, CIP skipped or downgraded |
| Line unfamiliar with SKU (first run) | 1.0% | New line–SKU combination |
| Aged equipment (last PM > 2× interval) | 0.8% | Maintenance flag in CMMS |

#### 3.3.4 Changeover Cost

```
C_changeover = labour_hours × blended_crew_rate
             + consumables_cost(cip_class)
             + opportunity_cost_of_displaced_jobs
```

| CIP Class | Crew Hours | Consumables (£) |
|-----------|-----------|-----------------|
| Rinse | 0.5 | 15 |
| Standard | 1.5 | 80 |
| Hot Flush | 3.0 | 180 |
| Full Strip | 6.0–10.0 | 420 |

#### 3.3.5 Total Rerouting Cost & Decision Rule

```
C_reroute = C_changeover + C_transport + C_quality

Reroute is preferred when:
  C_reroute < C_downtime                (same-plant)
  C_reroute < C_downtime − savings      (cross-plant, net of any deferred transport costs)
```

---

### 3.4 Scoring Model

All feasible candidates (lines that pass §3.2 gates) are ranked by a weighted composite score. **Lower score = better option** (cost-minimisation framing).

#### 3.4.1 Score Components

| Component | Symbol | Default Weight | Description |
|-----------|--------|---------------|-------------|
| Total rerouting cost | S_cost | 0.40 | C_reroute normalised across candidates |
| Time to switch | S_time | 0.25 | (CIP duration + setup) ÷ order slack |
| Quality risk | S_quality | 0.20 | quality_risk_rate from §3.3.3 |
| Target line utilisation | S_util | 0.15 | current_utilization ÷ rated_capacity |

Weights are configurable per plant in `simulation/network.py` or MES config. Default weights reflect a chilled-food context; ambient lines may reduce S_quality weight.

#### 3.4.2 Normalisation

Each component is normalised to [0, 1] across the candidate set before weighting:

```
S_cost_norm(i)    = C_reroute(i) / max(C_reroute)   across all candidates
S_time_norm(i)    = time_to_switch(i) / order_slack
S_quality_norm(i) = quality_risk_rate(i) / 0.10     (cap at 10%)
S_util_norm(i)    = current_utilization(i) / rated_capacity(i)
```

#### 3.4.3 Composite Score

```python
Score(i) = (w_cost    × S_cost_norm(i)
          + w_time    × S_time_norm(i)
          + w_quality × S_quality_norm(i)
          + w_util    × S_util_norm(i))

best = argmin Score(i)
```

#### 3.4.4 Tie-breaking Rules

1. Prefer same-plant over cross-plant (avoids transport risk and transit delay).
2. Among candidates within ±0.02 of top score, prefer the line with the longest time since last unplanned stoppage (more stable).
3. Escalate to planner if top two options are within 0.05 of each other AND one is cross-plant.

#### 3.4.5 Worked Example

Scenario: Line 3 (chilled snack, £4,500/h downtime) goes down. Expected downtime: 2 h → C_downtime = £9,000.

| Candidate | C_reroute (£) | Time to switch (h) | Quality risk | Utilisation | Composite Score |
|-----------|--------------|-------------------|-------------|------------|----------------|
| Line 3A (same plant) | 1,200 | 2.0 | 0.5% | 72% | **0.31** ← select |
| Line 3B (same plant) | 1,800 | 0.5 | 0.5% | 88% | 0.38 |
| Plant 2 Line 7 (cross-plant) | 3,400 | 6.5 | 1.0% | 60% | 0.62 |

All three beat downtime (all C_reroute < £9,000). Line 3A wins on composite score.

---

## 4. ISA-95 Level Mapping

### 4.1 Algorithm Placement

The rerouting algorithm spans ISA-95 Levels 3 and 4. It is a **Level 3 (MES) function** — it holds real-time line state, order book, and CIP status. Cost approval for cross-plant reroutes escalates to **Level 4 (ERP/planning)**.

```
┌────────────────────────────────────────────────────────────────┐
│  Level 4 — ERP / Planning (SAP, Oracle, etc.)                  │
│  • Receives: reroute cost summary, revised delivery dates      │
│  • Sends:    approved cost threshold, order priority flags     │
│  • Triggers: cross-plant approval, customer notification       │
└─────────────────────────┬──────────────────────────────────────┘
                          │  REST / OData  (B2MML / ISA-95 Part 5)
┌─────────────────────────▼──────────────────────────────────────┐
│  Level 3 — MES / Production Management                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  Rerouting Decision Engine   ← THIS ALGORITHM         │     │
│  │  Reads:  line status, CIP state, allergen history     │     │
│  │  Reads:  order book, due dates, SKU specs             │     │
│  │  Reads:  real-time utilisation (from L2 historian)    │     │
│  │  Writes: rerouted work orders, revised schedule       │     │
│  │  Writes: CIP work order to CMMS                      │     │
│  └───────────────────────────────────────────────────────┘     │
│  Plant historian (OSIsoft PI / Ignition) provides real-time    │
│  tag data for utilisation and line state                       │
└─────────────────────────┬──────────────────────────────────────┘
                          │  OPC-UA / MQTT  (real-time)
┌─────────────────────────▼──────────────────────────────────────┐
│  Level 2 — SCADA / DCS / HMI                                   │
│  • Sends:    line running/stopped state, active fault codes    │
│  • Sends:    current speed (ppm/cpm), reject counts           │
│  • Receives: reroute confirmation (line change notice to HMI)  │
└─────────────────────────┬──────────────────────────────────────┘
                          │  PLC I/O
┌─────────────────────────▼──────────────────────────────────────┐
│  Level 1 — PLC / Drive Control                                  │
│  • Physical interlocks, motor control, sensor I/O              │
│  • No rerouting logic; receives operator setpoints only        │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flows

#### Upward (L2 → L3 → L4)

| Data | Source | Destination | Protocol | Frequency |
|------|--------|-------------|----------|-----------|
| Line state (running / stopped / fault) | L2 SCADA | L3 MES | OPC-UA | Event-driven |
| Active fault code | L2 SCADA | L3 MES | OPC-UA | On change |
| Current throughput (cases/min) | L2 historian | L3 rerouting engine | REST / tag query | 1-min poll |
| CIP in-progress flag | L2 SCADA | L3 MES | OPC-UA | On change |
| Reroute cost summary | L3 MES | L4 ERP | REST / B2MML | Per reroute event |
| Revised delivery schedule | L3 MES | L4 ERP | REST / B2MML | Per reroute event |

#### Downward (L4 → L3 → L2)

| Data | Source | Destination | Protocol | Frequency |
|------|--------|-------------|----------|-----------|
| Order priority and due date | L4 ERP | L3 MES | REST / OData | Scheduled sync (hourly) |
| Approved cost threshold | L4 ERP | L3 rerouting engine | REST / OData | On change |
| Customer hold flag | L4 ERP | L3 MES | REST / OData | Event-driven |
| Rerouted work order | L3 MES | L2 HMI (operator display) | OPC-UA | Per reroute event |

### 4.3 Decision Authority Matrix

| Decision | Authority Level | Escalation Trigger |
|----------|----------------|--------------------|
| Same-plant reroute, C_reroute < £5 k | L3 MES (automatic) | None — executes silently, logs event |
| Same-plant reroute, C_reroute £5 k–£20 k | L3 MES + planner acknowledgement | Alert to planner; auto-executes after 10 min if no response |
| Cross-plant reroute, any cost | L3 MES proposes → L4 ERP approves | Auto-escalate; holds until approved |
| Partial reroute with quality risk > 2% | L3 MES proposes → QA manager approves | Alert to QA with risk detail |
| Downtime accepted > 4 h | L4 ERP + commercial team | Escalate with customer impact summary |

### 4.4 Integration Points in NexusFab

| NexusFab Module | Role in Rerouting Algorithm |
|-----------------|-----------------------------|
| `simulation/network.py` | Plant graph, transport costs, inter-plant distances, capacity data |
| `simulation/demand.py` | Order book, SKU due dates, lead times |
| `simulation/energy.py` | Energy cost delta for rerouted line (CIP, additional run time) |
| `optimization/` | CP-SAT scheduler re-solves affected time window post-reroute decision |
| React dashboard | Displays reroute recommendation; planner one-click accept / override |

The rerouting engine queries `network.py` for the plant graph and `demand.py` for the order book. Once a reroute is confirmed, the CP-SAT scheduler in `optimization/` is re-invoked on the affected window to regenerate the schedule with the updated line assignment.

---

## 5. Changeover Optimization & SMED Analysis

---

### 5.1 Changeover Time Matrix

Changeover durations depend on three factors: **equipment type** (wet process vs dry),
**product transition** (allergen / flavor / color delta), and **cleaning category**
(Full CIP → Rinse-only → Dry changeover).

#### Cleaning Category Definitions

| Category | Trigger | Scope | Typical Duration |
|----------|---------|-------|-----------------|
| **Full CIP** | Allergen cross-over, major flavor change, end-of-day micro reset | Full wash + sanitize + rinse + air-dry | 90–180 min |
| **Rinse-only CIP** | Same allergen class, minor flavor step, color adjacent | Hot-water flush + sanitize rinse | 30–60 min |
| **Dry changeover** | Same recipe family, pack-size/format only | Mechanical swap, no wet clean | 10–30 min |

#### Product-Pair Changeover Matrix — Beverage / Dairy Line (minutes)

Rows = **From product**, Columns = **To product**. Asymmetric: going from allergen-heavy
to allergen-free costs more than the reverse.

| From → To | Water (plain) | Fruit juice | Dairy base | Nut milk | Chocolate dairy |
|-----------|--------------|------------|-----------|----------|----------------|
| **Water** | — | 15 (dry) | 45 (rinse) | 90 (full CIP) | 90 (full CIP) |
| **Fruit juice** | 30 (rinse) | — | 60 (full CIP) | 90 (full CIP) | 90 (full CIP) |
| **Dairy base** | 90 (full CIP) | 90 (full CIP) | — | 90 (full CIP) | 45 (rinse) |
| **Nut milk** | 120 (full CIP) | 120 (full CIP) | 120 (full CIP) | — | 120 (full CIP) |
| **Chocolate dairy** | 90 (full CIP) | 90 (full CIP) | 45 (rinse) | 90 (full CIP) | — |

#### Product-Pair Changeover Matrix — Snack / Confectionery Line (minutes)

| From → To | Plain salted | Cheese flavor | Chili/spice | Nut-coated | Chocolate-coated |
|-----------|-------------|--------------|------------|-----------|-----------------|
| **Plain salted** | — | 20 (dry) | 30 (dry) | 60 (full CIP) | 60 (full CIP) |
| **Cheese flavor** | 45 (rinse) | — | 30 (dry) | 90 (full CIP) | 90 (full CIP) |
| **Chili/spice** | 60 (rinse) | 45 (rinse) | — | 90 (full CIP) | 90 (full CIP) |
| **Nut-coated** | 120 (full CIP) | 120 (full CIP) | 120 (full CIP) | — | 90 (full CIP) |
| **Chocolate-coated** | 90 (full CIP) | 90 (full CIP) | 90 (full CIP) | 60 (rinse) | — |

#### Product-Pair Changeover Matrix — Dry Powder / Blending Line (minutes)

| From → To | Base powder | Flavored blend | Vitamin premix | Allergen-free | Contains nuts |
|-----------|------------|---------------|---------------|--------------|--------------|
| **Base powder** | — | 15 (dry) | 20 (dry) | 30 (dry) | 45 (rinse) |
| **Flavored blend** | 25 (dry) | — | 20 (dry) | 45 (rinse) | 60 (full CIP) |
| **Vitamin premix** | 20 (dry) | 20 (dry) | — | 30 (dry) | 45 (rinse) |
| **Allergen-free** | 30 (dry) | 45 (rinse) | 30 (dry) | — | 90 (full CIP) |
| **Contains nuts** | 90 (full CIP) | 90 (full CIP) | 90 (full CIP) | 120 (full CIP) | — |

> **Implementation note**: store this as a 2D dict `changeover_matrix[from_sku][to_sku]` with
> a tuple `(minutes, category)`. Category drives CIP checklist selection in the MES.

---

### 5.2 SMED Analysis

SMED (Single-Minute Exchange of Die) separates changeover work into:

- **Internal** — machine must be stopped; cannot be parallelized with production.
- **External** — can be done while the previous run is finishing.

The core SMED insight: convert as many internal steps to external as possible, then
compress what remains.

#### Changeover Step Classification — Beverage Filling Line

| Step | Type | Duration (current) | External-convertible? | Converted Duration |
|------|------|-------------------|-----------------------|-------------------|
| Stop filler, drain product | Internal | 8 min | No | 8 min |
| Remove & label previous product hoses | Internal | 12 min | Partially (pre-label while running) | 5 min |
| Pre-stage CIP skid connection | Internal | 10 min | **Yes** — connect during last 10 min of run | 0 min (eliminated) |
| CIP cycle (full) | Internal | 60 min | No (equipment must be offline) | 60 min |
| Pre-heat next product to fill temp | Internal | 15 min | **Yes** — pre-heat in buffer tank while CIP runs | 0 min (parallel) |
| Install next product hoses/fittings | Internal | 10 min | Partially (pre-assemble) | 4 min |
| Flush & verify (micro sample) | Internal | 20 min | No | 20 min |
| Line speed / flow calibration | Internal | 8 min | No | 8 min |
| Paperwork / sign-off | Internal | 10 min | **Yes** — fill paperwork during CIP | 0 min |

**Before SMED**: 153 min total (all internal)
**After conversion**: 105 min internal + 48 min parallelized externally

**Net changeover reduction: ~31%** without changing any equipment.

#### Typical SMED Reduction Targets by Plant Type

| Plant Type | Baseline Changeover | Realistic SMED Target | Stretch Target |
|------------|--------------------|-----------------------|---------------|
| Beverage filling | 90–180 min | 55–110 min (35–40% reduction) | <60 min |
| Snack extrusion | 45–90 min | 25–55 min (35–40% reduction) | <30 min |
| Powder blending | 30–60 min | 20–40 min (30–35% reduction) | <20 min |
| Packaging line | 20–45 min | 10–25 min (40–45% reduction) | <10 min |

#### SMED Implementation Ladder

1. **Film & time** — video the current changeover, timestamp each step.
2. **Classify** — internal vs external (often 30–40% of steps are immediately movable).
3. **Convert** — pre-stage carts, shadow boards, pre-assembled sub-kits.
4. **Standardize** — one-touch fasteners, quick-connects, color-coded tooling.
5. **Measure** — OEE changeover loss before/after; report as % of available time.

---

### 5.3 Optimal Sequencing Rules

Sequencing rules encode domain knowledge as hard constraints or penalty weights
in the optimization model. Three axes matter:

#### 5.3.1 Allergen Sequencing (Light → Dark)

Run allergen-free or low-allergen products first, escalate toward high-allergen:

```
Allergen tier 0: no declared allergens (plain, unseasoned)
Allergen tier 1: gluten only
Allergen tier 2: dairy or soy
Allergen tier 3: eggs, fish, shellfish
Allergen tier 4: tree nuts, peanuts (most restrictive)
```

**Rule**: always sequence `tier[i] → tier[j]` where `i ≤ j` within a production block.
Reversing the order (tier 4 → tier 0) requires full CIP + micro verification.

**Why**: cross-contact risk is asymmetric — going light-to-dark allows rinse-only CIP;
dark-to-light mandates full CIP + allergen swab before release.

#### 5.3.2 Flavor Sequencing (Mild → Strong)

```
Neutral/unflavored → mild (vanilla, plain) → moderate (cheese, herb)
  → strong (chili, garlic) → very strong (smoked, fermented)
```

**Rule**: `flavor_intensity[i] ≤ flavor_intensity[j]` for consecutive run i→j.
Carry-over in piping and headspace is cumulative — a spice residue in neutral
product is a customer complaint; neutral residue in spice product is undetectable.

#### 5.3.3 Color Sequencing (Light → Dark)

```
White / cream → pale yellow → yellow → orange → red/pink → brown → dark brown → black
```

**Rule**: sequence by ascending darkness (Lab L* value, descending). Dark pigments
adsorb to equipment surfaces; light products run after dark ones show visual
contamination without CIP.

**Interaction with CIP**: correct color sequencing can eliminate 1–2 intermediate CIP
cycles per shift. At 60 min/CIP, sequencing alone saves 2–4 hours/week on a
high-SKU line.

#### 5.3.4 Combined Constraint Priority

When allergen, flavor, and color constraints conflict, priority order:

1. **Allergen** (regulatory / safety — non-negotiable)
2. **Flavor** (quality / sensory — negotiable with rinse CIP)
3. **Color** (cosmetic — negotiable with rinse CIP)

---

### 5.4 Changeover as TSP Variant

#### Problem Formulation

Given n products to schedule in a production block, find the permutation π that
minimizes total changeover cost:

```
minimize  Σ  C[π(i)][π(i+1)]   for i = 1..n-1
           i

subject to:
  π is a permutation of {1..n}
  allergen_tier[π(i)] ≤ allergen_tier[π(i+1)]   ∀ i   (allergen constraint)
  flavor_intensity[π(i)] ≤ flavor_intensity[π(i+1)]  ∀ i  (flavor — soft, penalized)
```

Where `C[i][j]` is the changeover matrix from section 5.1.

This is **Asymmetric TSP (ATSP)** — `C[i][j] ≠ C[j][i]` — with precedence
constraints from allergen tiers (making it a constrained ATSP, NP-hard but tractable
for n ≤ 50 common in shift schedules).

#### Solver Fit by Problem Size

| SKUs in block | Recommended approach | Library | Expected solve time | Notes |
|--------------|---------------------|---------|--------------------|-|
| ≤ 12 | Exact (Held-Karp DP) | OR-Tools / scipy | < 1 s | Optimal; feasible |
| 13–40 | OR-Tools TSP solver | `ortools.constraint_solver` | 1–30 s | Near-optimal with time limit |
| 41–100 | Nearest-neighbor + 2-opt | Custom / OR-Tools LK | < 5 s | ~10–20% above optimal |
| > 100 | Genetic algorithm | `deap` or custom | 30–120 s | Good for multi-shift planning |

#### OR-Tools TSP Skeleton

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve_changeover_sequence(skus, changeover_matrix, time_limit_sec=30):
    n = len(skus)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)
        return changeover_matrix[skus[i]][skus[j]]

    transit_cb = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    # Allergen precedence: add disjunctions or penalty arcs for tier violations
    for i, sku_i in enumerate(skus):
        for j, sku_j in enumerate(skus):
            if allergen_tier(sku_j) < allergen_tier(sku_i):
                # penytail: hard prohibition via large penalty, not a true precedence constraint
                routing.NextVar(manager.NodeToIndex(i)).RemoveValue(manager.NodeToIndex(j))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.time_limit.seconds = time_limit_sec

    solution = routing.SolveWithParameters(params)
    if not solution:
        return None

    index, order = routing.Start(0), []
    while not routing.IsEnd(index):
        order.append(skus[manager.IndexToNode(index)])
        index = solution.Value(routing.NextVar(index))
    return order
```

#### Nearest-Neighbor Heuristic (fallback)

```python
def nearest_neighbor_sequence(skus, matrix, start=None):
    remaining = set(skus)
    current = start or min(skus, key=lambda s: allergen_tier(s))
    order = [current]
    remaining.remove(current)

    while remaining:
        # only consider valid next SKUs (allergen tier >= current)
        eligible = [s for s in remaining if allergen_tier(s) >= allergen_tier(current)]
        if not eligible:
            eligible = list(remaining)  # fallback: accept violation, flag for CIP upgrade
        current = min(eligible, key=lambda s: matrix[current][s])
        order.append(current)
        remaining.remove(current)

    return order
```

#### When to Use Each

- **Shift planning (nightly batch)**: OR-Tools with 30 s limit — optimal or near-optimal.
- **Real-time re-sequence** (unplanned order insertion): nearest-neighbor in < 50 ms.
- **Weekly/campaign planning** with > 80 SKUs: genetic algorithm with allergen tier as
  a hard repair operator (fix violations post-crossover).

#### Expected Benefit

Optimized sequencing on a 15-SKU beverage line with 3 full CIP cycles/shift:

- Random sequence: avg 2.8 full CIP + 4.2 rinse = 2.8×90 + 4.2×45 = 441 min/shift changeover
- Optimized sequence: avg 1.0 full CIP + 6.0 rinse = 1.0×90 + 6.0×45 = 360 min/shift
- **Saving: ~81 min/shift (~18%)**, equivalent to 1–2 additional production runs.

---

### 5.5 Implementation Checklist

- [ ] Build `changeover_matrix` from historical MES records (actual times, not estimates)
- [ ] Tag each SKU with `allergen_tier`, `flavor_intensity`, `color_L_star` attributes
- [ ] Classify each changeover step as internal/external; target ≥30% external conversion
- [ ] Wire OR-Tools TSP solver into shift planning module; fall back to nearest-neighbor
      for intra-shift re-sequencing
- [ ] Track KPI: changeover minutes per 8-hour shift (target: reduce by 20% in 90 days)
- [ ] Validate: run optimized vs historical sequence on past 30 shifts, compare CIP count
