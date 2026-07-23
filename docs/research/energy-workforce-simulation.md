# Energy Optimization & Utility Cost Modeling
## NexusFab Research Reference — Sections 1–2

**Date:** 2026-07-23  
**Scope:** Food & beverage manufacturing (Nestlé case study basis)  
**Status:** Research complete — grounds `nexusfab/optimization/energy.py`

---

## Section 1 — Energy Consumption Profiles

### 1.1 Equipment kWh/hour by Type

Typical industrial nameplate power for food & beverage manufacturing equipment.
Values represent **full-load operating draw** (not standby/idle). Actual draw
varies with line speed, product viscosity, and age; apply 0.85–1.15 variance
in simulation.

| Equipment Type | kWh/hour (full load) | Notes |
|---|---|---|
| **Compressor (air)** | 75–150 | Central compressed-air station; 20–40 bar; largest single consumer in many plants |
| **Refrigeration / chiller** | 80–200 | Varies by tonnage; ammonia systems ~15% more efficient than HFC |
| **UHT pasteurizer** | 45–65 | Current model uses 45 (`PASTEURIZER`); UHT-specific is 55–65 |
| **Spray dryer / drum dryer** | 120–350 | Infant nutrition, coffee; thermal + electrical combined; `DRYER` = 55 is electrical only |
| **Freeze dryer (lyophilizer)** | 60–100 | Nescafé premium; low throughput, very high $/kg energy cost |
| **Extruder (pet food / cereal)** | 55–90 | Twin-screw = higher end; current model has gap here |
| **Homogenizer** | 30–40 | Current model: 35 — within range |
| **CIP / SIP heating (steam)** | 40–80 | Electric equivalent; steam boiler at 85% efficiency adds 15–20% effective draw |
| **HVAC (climate-controlled rooms)** | 25–60 | Dairy/infant nutrition cleanrooms: higher; confectionery: lower |
| **Lighting (full plant floor)** | 5–15 | Legacy HPS ≈ 15; LED retrofit ≈ 5–7 |
| **Mixer / blender** | 20–30 | Current model: 25 — on target |
| **Filler (liquid / powder)** | 12–20 | Current model: 15 — mid-range |
| **Conveyor system (total)** | 8–18 | Current model: 12; increases with plant length |
| **Packaging line (complete)** | 8–14 | Current model: 10 |
| **Capper / labeler** | 5–10 | Current model: CAPPER=8, LABELER=5 |

**Gaps in current `_ENERGY_RATES`:** Compressor, refrigeration, CIP heating, HVAC,
extruder, and freeze dryer are not modelled as distinct types. These collectively
account for 45–60% of plant energy in dairy and pet food. Recommend adding:

```python
"COMPRESSOR":   110.0,   # central air station, mid-range
"REFRIGERATION": 140.0,  # chiller bank, typical dairy
"CIP_HEATER":    55.0,   # electric equivalent for steam CIP
"HVAC":          35.0,   # climate-controlled production area
"EXTRUDER":      70.0,   # twin-screw pet food / cereal
```

### 1.2 Plant-Level Consumption Benchmarks

Annual kWh per tonne of production (kWh/t) by sub-sector:

| Sub-sector | kWh/t (typical) | kWh/t (best-in-class) | Key driver |
|---|---|---|---|
| Water / PET bottling | 30–60 | 20 | Compressed air dominates |
| Confectionery (chocolate) | 250–400 | 180 | Tempering, moulding, refrigeration |
| Dairy (liquid milk) | 60–120 | 45 | Pasteurization, CIP, refrigeration |
| Ice cream | 350–550 | 260 | Freezing tunnels, cold chain |
| Infant nutrition (powder) | 800–1,400 | 600 | Spray drying, sterile HVAC |
| Instant coffee (spray-dried) | 600–1,200 | 450 | Extraction, evaporation, drying |
| Pet food (extruded dry) | 280–480 | 200 | Extrusion, kibble drying |
| Prepared foods (frozen) | 150–280 | 110 | Cooking, freezing |

**Current model's `kwh_per_ton` output** is a post-hoc ratio, not
equipment-type-aware. The benchmarks above can validate simulation plausibility —
if `kwh_per_ton` falls outside ±30% of these ranges for a plant type, the
equipment roster or utilization assumptions likely need adjustment.

### 1.3 Time-of-Day Consumption Patterns

Food plants have characteristic daily load shapes:

- **Continuous process (dairy, water, 24/7):** Flat base load with CIP valleys
  (1–2 hours per line per day, typically 6 AM and 2 AM). Peak demand occurs at
  production changeovers when multiple lines restart simultaneously.
- **Batch/shift plants (confectionery, prepared foods):** Sharp ramp at shift
  start (06:00 or 22:00), sustained plateau, ramp-down at shift end. Demand
  spikes at ramp-up are the primary driver of demand charges.
- **Spray dryer plants (coffee, infant nutrition):** Nearly constant — dryers
  cannot be easily stopped and restarted (thermal mass). CIP is the only
  significant interruptible load.

---

## Section 2 — Utility Rate Structures

### 2.1 Industrial Tariff Anatomy

A typical large-industrial electricity bill has four components:

| Component | Typical range | Mechanism |
|---|---|---|
| **Energy charge** | $0.05–$0.16/kWh | Per kWh consumed, varies by time-of-use period |
| **Demand charge** | $8–$22/kW | Peak 15-min average kW in the billing month |
| **Customer/fixed charge** | $200–$2,000/month | Fixed regardless of usage |
| **Power factor penalty** | 0–5% surcharge | Applied when PF < 0.90–0.95 threshold |

**Demand charges often represent 30–50% of the total bill** for energy-intensive
manufacturers. The current model charges only per-kWh — this systematically
underestimates total utility cost and misses the biggest optimization lever
(peak demand reduction).

### 2.2 Time-of-Use (TOU) Period Structure

Standard North American large-industrial TOU structure:

| Period | Hours (weekday) | Rate multiplier vs flat | Typical $/kWh |
|---|---|---|---|
| **Off-peak** | 23:00–07:00 | 0.45–0.55× | $0.04–$0.07 |
| **Shoulder** | 07:00–09:00, 17:00–23:00 | 0.75–0.85× | $0.07–$0.10 |
| **On-peak** | 09:00–17:00 | 1.00× (reference) | $0.10–$0.16 |
| **Critical peak** | Utility-declared (~10 days/yr) | 3–5× | $0.30–$0.60 |

Weekends are typically all-off-peak or all-shoulder. The current `_TARIFF_PERIODS`
in `energy.py` (lines 211–218) models off-peak at 0.5×, shoulder at 0.8×, peak
at 1.0× — this is accurate for the energy-charge component. It omits critical-peak
events and weekend differentiation.

Regional variation:

| Region | Flat rate $/kWh | Demand charge $/kW | Notes |
|---|---|---|---|
| US Midwest (MISO) | $0.07–$0.10 | $8–$14 | Cheapest North American industrial |
| US Northeast (ISO-NE) | $0.10–$0.16 | $14–$22 | High demand charges |
| Western Europe (Germany) | €0.12–$0.18 | €8–€15 + grid fees | Renewable surcharge adds €0.04–0.06 |
| UK | £0.10–$0.16 | £4–£10 + TNUoS | Triad demand (3 winter half-hours) |
| Australia (NEM) | A$0.09–$0.16 | A$12–$20 | High solar penetration → volatile spot |
| India | ₹7–₹11/kWh (~$0.08–$0.13) | ₹200–₹400/kVA | kVA-based demand, PF penalty common |

Current per-plant flat rates (`_ENERGY_COSTS`, lines 28–33) are in the
$0.10–$0.14/kWh range — reasonable for US industrial. Add demand charges to get
realistic total cost modelling.

### 2.3 Demand Charges — Mechanics and Impact

**How demand charges work:**

1. Utility measures average kW in every consecutive 15-minute interval all month.
2. The single highest interval becomes the "billing demand."
3. Bill = billing_demand_kW × $/kW rate.

**Consequence for optimization:** A one-time 15-minute startup spike — e.g., three
pasteurizers restarting simultaneously after a CIP — can set the demand charge for
the entire month. Staggering startups by 20–30 minutes eliminates the spike at
zero energy cost.

**Demand charge estimation formula for the model:**

```
estimated_demand_kW = (peak_concurrent_equipment_draw) × 1.15  # 15% demand factor
monthly_demand_cost = estimated_demand_kW × demand_rate_per_kW
```

Typical demand charge savings from load management: 10–25% of total bill.

### 2.4 Power Factor Penalties

**Power factor (PF)** = real power (kW) / apparent power (kVA). Industrial motors
and drives without correction run at PF 0.75–0.85. Utilities penalize PF < 0.90
(sometimes 0.95) because low PF wastes transmission capacity.

Penalty structures:

- **Excess kVAR charge:** $0.50–$2.50 per kVAR over threshold, monthly
- **Demand adjustment:** bill demand inflated by (PF_threshold / actual_PF)
- **Flat surcharge:** 1–5% of energy charges when PF < threshold

**Correction:** Capacitor banks at motor loads cost $15–30/kVAR installed and
typically pay back in 12–24 months. Variable-frequency drives (VFDs) improve
PF intrinsically.

For NexusFab simulation: apply a 3% surcharge to plants where `_ENERGY_RATES`
equipment weighted average implies PF < 0.90 (i.e., plants with heavy motor
loads and no VFD assumption).

### 2.5 Demand Response Programs

**Demand response (DR)** lets utilities call on industrial customers to curtail
load during grid stress events, paid via:

| Program type | Curtailment notice | Payment |
|---|---|---|
| **Interruptible tariff** | 10–30 min | $5–$20/kW/month capacity payment |
| **Emergency DR (PJM/MISO)** | 30 min | $50–$150/MWh event payment |
| **Economic DR (day-ahead)** | Day-ahead | Market price × 0.8–1.0 |
| **Ancillary services (regulation)** | Real-time | $20–$50/MW/hour |

Food plant candidacy for DR: CIP cycles (interruptible 60–90 min), refrigeration
compressors (reduce setpoint 1–2°C for 30 min), HVAC (shed non-cleanroom zones).
Spray dryers and UHT lines are generally **not** DR-eligible due to food safety
constraints — batch in progress cannot be interrupted.

---

## Cross-Reference: Current Model vs Research Findings

| Parameter | `energy.py` current value | Research-grounded value | Action |
|---|---|---|---|
| Compressor kWh/hr | Not modelled | 110 kWh | Add `COMPRESSOR` type |
| Refrigeration kWh/hr | Not modelled | 140 kWh | Add `REFRIGERATION` type |
| Demand charges | Not modelled | $8–$22/kW/month | Add demand cost layer |
| Power factor penalty | Not modelled | ~3% surcharge | Optional multiplier |
| Critical peak events | Not modelled | 3–5× rate, ~10 days/yr | Add to tariff periods |
| CO2 factor | 0.42 kg/kWh | 0.38–0.42 (US 2024 mix) | Current value is correct |
| kWh/t range (dairy) | Derived from model | 60–120 | Validate PLT-003 output |

---

---

## Section 3 — Workforce Scheduling Models

### 3.1 Shift Patterns

Food manufacturing operates 24/7 to maximise asset utilisation. Four patterns dominate:

#### 3.1.1 Continental (4-Crew Rotating)

- **Structure:** 4 crews rotate across Days / Lates / Nights / Rest using a repeating 4-week cycle (e.g., 2 days on → 2 nights on → 4 off, or the classic DDD NNN RRR variant).
- **Worked hours/week:** ~42 h averaged over the cycle (some weeks 48, some 36).
- **Labor utilisation:** ~85–88% of scheduled hours are productive (accounts for handover overlap, ~30 min/shift).
- **Pros:** True 24/7 coverage with no gap weekends; predictable rotation staff can plan lives around; lower Monday-spike absenteeism.
- **Cons:** Night premium costs add 15–20% to wage bill; requires 25–33% headcount buffer vs. a day-only operation; fatigue risk on long night blocks.
- **Best fit:** High-volume continuous lines (ready-meals, dairy, beverages).

#### 3.1.2 12-Hour Shifts — 2-2-3 (Pitman) Pattern

- **Structure:** Two crews cover Days (06:00–18:00), two cover Nights (18:00–06:00). Averages 42 h/week over a 2-week cycle.
- **Labor utilisation:** ~90–92% — only 2 handovers/day vs. 3, shorter total handover time.
- **Pros:** Fewer handovers → better batch/CCP continuity; staff prefer longer off-blocks; reduced daily transport costs.
- **Cons:** Fatigue in final hours of 12-h block (error rate +30–50% in hours 9–12 per HSE RR446); harder to schedule mid-shift training; overtime often triggers at 84 h/2-week period under CBAs.
- **Best fit:** Packaging lines, cold-store operations, single-SKU high-throughput.

#### 3.1.3 8-Hour 3-Shift (Classic Continental)

- **Structure:** Morning 06:00–14:00 / Afternoon 14:00–22:00 / Night 22:00–06:00 rotating across 3 crews. Typically 5-day coverage with weekend premium for a true 24/7 fourth crew.
- **Worked hours/week:** 40 h standard.
- **Labor utilisation:** ~82–85% — three 30-min handovers/day; higher overlap cost.
- **Pros:** Shortest continuous work block → lowest fatigue; easier to flex part-time headcount at shift boundaries; simpler overtime calculation.
- **Cons:** Three handovers daily = more contamination/quality-gap risk; requires a fourth crew (or heavy overtime) for true 24/7; 20–30% premium for unsocial shift slots.
- **Best fit:** Mixed-SKU lines needing frequent changeover; operations with significant QA hold-and-test cycles.

#### 3.1.4 5-Day 2-Shift (Days + Lates)

- **Structure:** Mon–Fri only, Day 06:00–14:00 + Late 14:00–22:00. Two crews, no night shift.
- **Worked hours/week:** 40 h.
- **Labor utilisation:** ~92–94% — minimal premium pay, no night fatigue.
- **Pros:** Lowest wage cost (no night differential); easiest recruitment; compliance simpler (no WTD night-worker health assessment).
- **Cons:** Zero weekend production; any demand spike requires overtime or weekend call-in at 1.5–2× rate; line OEE capped at ~71% of 168 h/week maximum.
- **Best fit:** Seasonal / campaign products, artisan lines, maintenance-heavy lines needing weekend downtime.

#### Summary Table

| Pattern | Avg h/week | Handovers/day | Labor util% | Night premium | Weekend coverage |
|---|---|---|---|---|---|
| Continental 4-crew | ~42 | 2–3 | 85–88% | +15–20% | Full |
| 12-h Pitman (2-2-3) | ~42 | 2 | 90–92% | +15–20% | Full |
| 8-h 3-shift | 40 | 3 | 82–85% | +20–25% | Full (4th crew or OT) |
| 5-day 2-shift | 40 | 2 | 92–94% | none | None |

---

### 3.2 Skill Matrix

#### 3.2.1 Operator Certification Levels

| Level | Label | Typical certification | Pay band premium |
|---|---|---|---|
| L0 | **Trainee** | On-the-job < 3 months; line-specific induction only | Base |
| L1 | **Qualified Operator** | Certified on ≥1 line type; basic HACCP awareness; hygiene passport | +5–8% |
| L2 | **Multi-Skilled Operator** | Certified on ≥3 line types; minor changeover; CCP monitoring | +12–18% |
| L3 | **Team Leader / Chargehand** | All lines; shift sign-off authority; first-line HACCP decision | +20–30% |

Steady-state target mix: 60% L1, 25% L2, 10% L3, 5% L0.

#### 3.2.2 Skills Required per Line Type

| Line type | Min level | Specialist skills | Typical crew size |
|---|---|---|---|
| Continuous cooking / retort | L2 | HACCP CCP sign-off, temperature validation | 4–6 |
| Packaging / wrapping | L1 | Date-coding verification, allergen changeover | 3–5 |
| Mixing / blending | L2 | Recipe management, allergen control | 3–4 |
| Slicing / portion control | L1 | Blade safety, weight-check SPC | 2–4 |
| Cold-store / dispatch | L1 | Cold-chain documentation, FEFO rotation | 2–3 |
| Maintenance-support role | L3 | Permit-to-work, isolation/LOTO | 1–2 per area |

Minimum staffing rule: every active line must have ≥1 L2+ operator during any CCP-producing run. No L2 available → line must halt (see wiki: HACCP CCPs must cover all line types or compliance % drops to zero).

#### 3.2.3 Cross-Training Impact on Flexibility

- Each additional certified line per L1→L2 upgrade reduces scheduling gaps by ~8–12% in simulation runs (empirical benchmark from BRC-audited sites).
- **Flexibility index** = (total certified line-slots across crew) / (lines × target crew size). Target ≥ 1.4 for robust scheduling (absorbs 1.5× average absenteeism comfortably).
- Cross-training cost: ~£800–£1,200 / operator / line (training time + assessor, UK mid-market 2024). Payback period typically 6–14 weeks at overtime savings rate.
- Expose `skill_flexibility_index` in the scheduling model; values < 1.2 should trigger a warning and contingency hire recommendation.

---

### 3.3 Labor Constraints

#### 3.3.1 Maximum Hours per Week

| Jurisdiction | Statutory max | Opt-out available | Night worker limit |
|---|---|---|---|
| EU (Working Time Directive 2003/88/EC) | **48 h/week** averaged over 17 weeks | Yes (individual written opt-out) | 8 h/24 h averaged; no opt-out for hazardous work |
| UK (Working Time Regulations 1998) | **48 h/week** (same reference period) | Yes (individual opt-out) | Same 8 h night limit |
| USA (FLSA) | No federal cap; **overtime ≥ 1.5× at 40 h/week** | N/A; state laws vary (CA: daily OT > 8 h) | No federal night limit |
| Canada | Province-dependent: typically **44–48 h/week** before OT | Varies by province/CBA | No federal limit |

EU/UK sites have a hard 48 h ceiling; US sites use a cost-based OT threshold instead — parameterise `jurisdiction` in the model.

#### 3.3.2 Mandatory Rest Periods

- **EU/UK:** ≥11 consecutive hours rest per 24 h; ≥24 h uninterrupted rest per 7 days (or 48 h per 14 days); ≥20-min break if shift > 6 h.
- **USA:** No federal mandate; OSHA recommends ≥8 h between shifts; many CBAs stipulate 10–12 h.
- Encode as `rest_gap_hours` constraint (default 11 for EU, 8 for US); check before assigning any back-to-back shift pair.

#### 3.3.3 Fatigue Management

Evidence-based fatigue multipliers on operator error rate (HSE RR446 / FRMS benchmarks):

| Shift position | Fatigue multiplier on error rate |
|---|---|
| Day shift, hours 1–6 | 1.0× baseline |
| Day shift, hours 7–8 | 1.1× |
| 12-h shift, hours 9–12 | 1.3–1.5× |
| Night shift, hours 1–4 | 1.4× |
| Night shift, hours 5–8 | 1.6× |
| 3rd consecutive night | 1.8× |
| Post-rest-day return | 0.9× (first 2 h adjustment) |

Scheduling optimizer should penalise assignments accumulating fatigue multiplier > 1.5× on CCP-critical stations.

#### 3.3.4 Minimum Staffing per Line

- Food safety: ≥2 persons on any running production line (lone worker prohibition in most food safety management systems).
- HACCP compliance: ≥1 L2+ on any CCP-producing line (see §3.2.2).
- Fire/emergency: minimum 2 trained evacuators per floor/zone per shift.
- Model constraint: `min_crew[line_type]` lookup; headcount below threshold → line status `starved`, not `running`.

---

### 3.4 Absenteeism Modeling

#### 3.4.1 Baseline Rates

- Food manufacturing sector median: **6.5% absenteeism** (range 5–8%, BRC/CIPD 2023 benchmarks).
- Compared to UK all-sector average ~4.6% — food manufacturing runs higher due to physical demands, temperature extremes, and shift fatigue.
- Long-term sickness (> 4 weeks): ~1.5% of workforce at any time; model separately from short-term absence.

#### 3.4.2 Seasonal Patterns

| Period | Relative absence multiplier | Driver |
|---|---|---|
| Jan–Feb | 1.3× | Post-holiday fatigue, winter illness (flu/respiratory) |
| Mar–Apr | 1.0× | Baseline |
| May–Jun | 0.9× | Improving weather, lower illness |
| Jul–Aug | 1.1× | School holidays (carer absence), summer GI illness |
| Sep–Oct | 1.0× | Baseline |
| Nov | 1.2× | Early winter illness |
| Dec | 1.4× | Peak-season fatigue, holiday requests, Christmas illness |

Peak-season production (Nov–Dec) collides with peak absenteeism — the critical scheduling stress point.

#### 3.4.3 Contingency Staffing Formulas

```python
# Basic relief factor
relief_factor = 1 / (1 - absenteeism_rate)
# At 6.5%:  1 / 0.935 = 1.069  → hire 6.9% above minimum headcount

# With seasonal adjustment
headcount_required = base_headcount * relief_factor * seasonal_multiplier[month]
# December: 100 * 1.069 * 1.4 = 150 FTE needed

# Agency / flex buffer rule of thumb
core_permanent = base_headcount * 1.05   # covers average absence
agency_pool    = base_headcount * 0.12   # covers seasonal peaks + surge
# Require: core + agency >= headcount_required(peak_month)
```

Model parameters: `absenteeism_rate` (default 0.065), `seasonal_multipliers` (12-element float array per §3.4.2), `agency_pool_fraction` (default 0.12).

---

### 3.5 Labor Cost Model

#### 3.5.1 Cost Components

| Component | Typical value (UK food manufacturing, 2024) | Notes |
|---|---|---|
| Base wage | £12.50–£16.00/h (L1–L3) | NLW £11.44/h floor |
| Employer NI | +13.8% on earnings > £9,100/y | UK statutory |
| Pension | +3–5% employer contribution | Workplace Pension Regs |
| Holiday accrual | +12.07% (statutory 5.6 weeks) | Embedded in effective hourly rate |
| Overtime premium | **1.5×** base for > 40 h/week; **2.0×** for > 60 h or public holidays | CBA-dependent |
| Night shift differential | **+15–25%** on base | Site/union agreement |
| Weekend differential | **+25–50%** (Sat); **+50–100%** (Sun) | Wide variation |
| Skill premium | +5–8% (L1), +12–18% (L2), +20–30% (L3) vs. L0 | See §3.2.1 |
| Agency margin | +20–35% on equivalent permanent rate | Labour supply agency fee |

On-costs total: ~30% uplift (NI + pension + holiday accrual) on gross wage.

#### 3.5.2 Effective Cost per Production Hour by Shift Type

Assumptions: L1 operator, base £13.50/h, on-costs +30% → effective £17.55/h.

| Shift type | Shift differential | Effective £/h (incl. on-costs) |
|---|---|---|
| Day (Mon–Fri) | 0% | £17.55 |
| Late/Afternoon | +10% | £19.31 |
| Night (Mon–Thu) | +20% | £21.06 |
| Night (Fri–Sat) | +35% | £23.69 |
| Sunday | +50% | £26.33 |
| Overtime 1.5× (any shift) | base shift rate × 1.5 | £26.33–£39.49 |
| Overtime 2.0× (BH / > 60 h) | base × 2.0 | £35.10–£52.66 |
| Agency L1 equivalent | +25% agency margin on night | ~£28–£32/h |

#### 3.5.3 Cost Formula for Scheduling Model

```python
def labor_cost_per_hour(base_wage, level, shift_type, is_overtime=False, is_agency=False):
    LEVEL_PREMIUM  = {0: 0.00, 1: 0.06, 2: 0.15, 3: 0.25}
    SHIFT_PREMIUM  = {"day": 0.00, "late": 0.10, "night": 0.20,
                      "night_weekend": 0.35, "sunday": 0.50}
    ON_COST_FACTOR = 1.30   # NI + pension + holiday accrual
    OT_MULTIPLIER  = 1.5    # ponytail: 2.0x only for >60h/BH, not the common case
    AGENCY_MARGIN  = 1.28   # mid-point of 20–35% range

    rate = base_wage * (1 + LEVEL_PREMIUM[level]) * (1 + SHIFT_PREMIUM[shift_type])
    rate *= ON_COST_FACTOR
    if is_overtime:
        rate *= OT_MULTIPLIER
    if is_agency:
        rate *= AGENCY_MARGIN
    return round(rate, 2)
```

#### 3.5.4 Cost Comparison: Shift Patterns (100-person line, 1 week)

| Pattern | Productive hours | Total wage cost (L1 mix) | Cost/productive hour |
|---|---|---|---|
| Continental 4-crew (24/7) | 3,360 | ~£72,000 | ~£21.43 |
| 12-h Pitman 2-2-3 (24/7) | 3,360 | ~£70,500 | ~£20.98 |
| 8-h 3-shift (24/7 + 4th crew) | 3,360 | ~£74,500 | ~£22.17 |
| 5-day 2-shift | 1,600 | ~£30,500 | ~£19.06 |

The 12-h Pitman pattern is marginally cheapest for 24/7 coverage — fewer handover-hours paid and fewer shift-premium transitions per week.

---

### 3.6 Model Integration — Parameter Reference

| Research parameter | Suggested model field | Default |
|---|---|---|
| Shift pattern | `shift_pattern` enum | `"continental_4crew"` |
| Absenteeism rate | `absenteeism_rate` float | `0.065` |
| Seasonal multipliers | `seasonal_multipliers` float[12] | See §3.4.2 |
| Skill flexibility index | `skill_flexibility_index` float | `1.4` |
| Min rest gap | `rest_gap_hours` int | `11` (EU) / `8` (US) |
| Base wage | `base_wage_per_hour` float | `13.50` |
| Overtime threshold | `ot_threshold_hours` int | `40` |
| OT multiplier | `ot_multiplier` float | `1.5` |
| Agency pool fraction | `agency_pool_fraction` float | `0.12` |
| Max hours/week | `max_hours_per_week` int | `48` (EU) / cost-only (US) |
| Min crew per line | `min_crew` dict | See §3.3.4 |

---

*Section 3 authored by business-analyst agent, sprint task `535459fc-f96f-41b4-966d-f10b4220b594`, 2026-07-23.*

---

## Section 4 — Simulation Engine (SimPy DES + Seeded Replications + OR-Tools CP-SAT)

### 4.1 SimPy DES Patterns for Manufacturing

#### Core Primitives

| Primitive | Manufacturing mapping |
|-----------|----------------------|
| `Resource` | Machine, operator, crane — exclusive-use equipment |
| `Container` | Bulk buffer / silo — continuous level (kg, litres) |
| `Store` | WIP queue — discrete units (pallets, batches) |
| `Process` | Production run, CIP cycle, changeover |
| `Environment` | Simulation clock; drives all `yield env.timeout()` |

#### Machine Breakdown (random process)

```python
import simpy, random

def machine_with_breakdowns(env, resource, mttf=480, mttr=60, seed=42):
    rng = random.Random(seed)
    while True:
        yield env.timeout(rng.expovariate(1 / mttf))   # time-to-failure (minutes)
        resource._capacity = 0                          # force unavailable
        yield env.timeout(rng.expovariate(1 / mttr))   # repair time
        resource._capacity = 1
```

Use `simpy.PreemptiveResource` if breakdown must interrupt an active job. For NexusFab, breakdowns trigger the rerouting optimizer — the SimPy event fires a callback that calls OR-Tools CP-SAT.

#### CIP (Scheduled Interrupt)

CIP is calendar-driven, not random. Model as a separate process that `interrupt()`s the production process:

```python
def cip_scheduler(env, prod_process, cip_interval=480, cip_duration=45):
    while True:
        yield env.timeout(cip_interval)
        prod_process.interrupt("CIP")

def production(env, machine):
    while True:
        try:
            with machine.request() as req:
                yield req
                yield env.timeout(run_time)
        except simpy.Interrupt:
            yield env.timeout(cip_duration)
```

#### Changeover (Setup Time)

Between products A→B, insert a deterministic (or PERT-distributed) setup timeout before the next job. Track `current_product` on the resource; if `next_product != current_product`, add setup time drawn from a changeover matrix.

#### Batch vs Continuous Lines

- **Batch**: model each batch as `Store.get()` + process + `Store.put()`. Buffer level is item count.
- **Continuous**: model flow rate as `Container` fill/drain with `env.timeout(delta_t)` ticks; check level against thresholds each tick. Use small `delta_t` (e.g., 1 min) for accuracy; larger for speed.

### 4.2 Seeded Simulation Design — Reproducibility & Confidence Intervals

#### Independent RNG Streams

Never use `random.seed()` globally — it makes parallel replications share state. Give each stochastic process its own `random.Random(seed)` instance:

```python
breakdown_rng  = random.Random(base_seed + 1)
demand_rng     = random.Random(base_seed + 2)
repair_rng     = random.Random(base_seed + 3)
```

For NumPy: `rng = np.random.default_rng(seed)` (new Generator API; avoid `np.random.seed()` globally).

#### Running Replications

```python
def run_replications(n=30, base_seed=0):
    results = []
    for i in range(n):
        env = simpy.Environment()
        sim = NexusFabSim(env, seed=base_seed + i)
        env.run(until=SIM_HORIZON)
        results.append(sim.collect_kpis())
    return results
```

Rule of thumb: **n = 30** replications gives ~95% CI with ±5–10% half-width for most manufacturing KPIs. Use **n = 10** for fast dev iteration, **n = 100** for final validation.

#### Confidence Intervals

```python
import numpy as np, scipy.stats as st

def ci_95(data):
    n = len(data)
    mean, se = np.mean(data), st.sem(data)
    return mean, st.t.interval(0.95, df=n-1, loc=mean, scale=se)

throughput_vals = [r["throughput_tph"] for r in results]
mean, (lo, hi) = ci_95(throughput_vals)
# Report: 142.3 tph [139.1, 145.5]
```

The 95% CI becomes the confidence band shown on the React dashboard. The simulation runner at `nexusfab/simulation/runner.py` should accept `n_replications` and `base_seed` parameters and return `{mean, ci_lo, ci_hi}` per KPI.

### 4.3 OR-Tools CP-SAT — Job-Shop Scheduling

#### Problem Formulation

Job-shop scheduling: J jobs × M machines. Each job is a sequence of tasks; each task runs on a specific machine; no machine runs two tasks simultaneously.

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
horizon = sum(duration for job in jobs for _, duration in job)

task_vars = {}
for job_id, job in enumerate(jobs):
    for task_id, (machine_id, duration) in enumerate(job):
        suffix = f"_{job_id}_{task_id}"
        start    = model.NewIntVar(0, horizon, "start"  + suffix)
        end      = model.NewIntVar(0, horizon, "end"    + suffix)
        interval = model.NewIntervalVar(start, duration, end, "interval" + suffix)
        task_vars[(job_id, task_id)] = (start, end, interval, machine_id)
```

#### No-Overlap Constraints

```python
machine_intervals = {m: [] for m in range(num_machines)}
for (job_id, task_id), (_, _, interval, machine_id) in task_vars.items():
    machine_intervals[machine_id].append(interval)

for intervals in machine_intervals.values():
    model.AddNoOverlap(intervals)
```

#### Optional Intervals for Rerouting

When a job can go to machine A *or* machine B (alternate routing):

```python
presence_a = model.NewBoolVar(f"presence_a_{job_id}_{task_id}")
presence_b = model.NewBoolVar(f"presence_b_{job_id}_{task_id}")
model.Add(presence_a + presence_b == 1)   # exactly one route

interval_a = model.NewOptionalIntervalVar(start, dur_a, end, presence_a, "iv_a")
interval_b = model.NewOptionalIntervalVar(start, dur_b, end, presence_b, "iv_b")
machine_a_intervals.append(interval_a)
machine_b_intervals.append(interval_b)
```

This is the key mechanism for NexusFab line-rerouting after a breakdown: force the broken machine's `presence` literal to 0 and re-solve in seconds.

#### Objective Functions

```python
# Minimize makespan
makespan = model.NewIntVar(0, horizon, "makespan")
model.AddMaxEquality(makespan, [end for (_, end, _, _) in task_vars.values()])
model.Minimize(makespan)

# Minimize weighted tardiness (preferred for NexusFab)
tardiness_terms = []
for job_id, (due_date, weight) in enumerate(job_deadlines):
    last_end = task_vars[(job_id, len(jobs[job_id])-1)][1]
    tard = model.NewIntVar(0, horizon, f"tard_{job_id}")
    model.AddMaxEquality(tard, [0, last_end - due_date])
    tardiness_terms.append(weight * tard)
model.Minimize(sum(tardiness_terms))
```

#### Solver Configuration

```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0   # hard limit for real-time use
solver.parameters.num_search_workers  = 8
status = solver.Solve(model)
# status: OPTIMAL, FEASIBLE (time limit hit), INFEASIBLE, UNKNOWN
```

---

## Section 5 — Optimization Solvers: PuLP/CBC and Theory of Constraints

### 5.1 PuLP/CBC for LP/MIP

#### When to Use LP vs MIP

| Scenario | Model type | Why |
|----------|-----------|-----|
| Ingredient blending (meet specs) | LP | Continuous proportions |
| Capacity allocation across plants | LP | Resource shares are fractional |
| Scheduling with binary on/off decisions | MIP | Binary variable per job-machine assignment |
| Lot sizing (produce or not per period) | MIP | Binary setup + continuous quantity |
| Network flow, splittable arcs | LP | No integrality needed |
| Network flow, truck-capacity arcs | MIP | Arc indivisibility requires binary |

#### LP Example — Blending

```python
import pulp

prob = pulp.LpProblem("blend", pulp.LpMinimize)
x = {i: pulp.LpVariable(f"x_{i}", lowBound=0) for i in ingredients}

prob += pulp.lpSum(cost[i] * x[i] for i in ingredients)
for nutrient, (lo, hi) in specs.items():
    prob += pulp.lpSum(content[i][nutrient] * x[i] for i in ingredients) >= lo
    prob += pulp.lpSum(content[i][nutrient] * x[i] for i in ingredients) <= hi
prob += pulp.lpSum(x[i] for i in ingredients) == batch_size

prob.solve(pulp.PULP_CBC_CMD(msg=False))
```

#### MIP Example — Lot Sizing with Setup Cost

```python
y = {t: pulp.LpVariable(f"y_{t}", cat="Binary") for t in periods}
q = {t: pulp.LpVariable(f"q_{t}", lowBound=0) for t in periods}

prob += pulp.lpSum(setup_cost * y[t] + unit_cost * q[t] for t in periods)
for t in periods:
    prob += q[t] <= max_capacity * y[t]   # big-M linking constraint
```

#### Problem Size Limits — CBC (Free) vs Commercial

| Scale | CBC (free, PuLP default) | Gurobi / CPLEX (commercial) |
|-------|--------------------------|------------------------------|
| Continuous variables | < 10,000 fast | Millions |
| Binary variables | < 500 for fast solve | 100,000+ |
| Constraints | < 50,000 | Millions |
| Hard MIP solve time | Degrades badly | 10–100× faster branch-and-bound |
| NexusFab practical limit | Single-plant blending & lot sizing | Multi-plant multi-week MIP |

**For NexusFab**: use PuLP/CBC for blending optimization and single-plant allocation LP problems. For multi-plant scheduling MIPs with >200 binary variables, prefer OR-Tools CP-SAT (free, purpose-built for combinatorial scheduling). CP-SAT typically outperforms CBC on pure scheduling MIPs at moderate size even though it uses a different algorithm.

#### Solver Selection in PuLP

```python
prob.solve(pulp.PULP_CBC_CMD(timeLimit=60, msg=False))   # default free
prob.solve(pulp.HiGHS_CMD(msg=False))                    # free, faster for LP
prob.solve(pulp.GUROBI_CMD(timeLimit=60))                # commercial, if licensed
```

**HiGHS** (`pip install highspy`) is free, faster than CBC for LP, and a recommended drop-in upgrade for NexusFab LP problems.

### 5.2 Theory of Constraints / Drum-Buffer-Rope

#### Identifying the Bottleneck

The bottleneck is the resource with the highest utilization — the machine that limits system throughput.

**Detection method** (simulation-friendly):
1. Run SimPy for a warm-up period (e.g., 2× average cycle time).
2. Track `busy_time / sim_time` for every resource.
3. Machine with utilization nearest 100% = bottleneck.
4. Cross-check: queue depth (`Store` size) in front of it should be persistently non-zero.

```python
class TrackedResource(simpy.Resource):
    def __init__(self, env, capacity=1):
        super().__init__(env, capacity)
        self._busy_start = {}
        self.busy_total  = 0.0

    def request(self):
        req = super().request()
        req.callbacks.append(lambda _: self._mark_busy(req))
        return req

    def _mark_busy(self, req):
        self._busy_start[req] = self._env.now

    def release(self, req):
        self.busy_total += self._env.now - self._busy_start.pop(req, self._env.now)
        return super().release(req)
```

#### Drum-Buffer-Rope Mechanics

| DBR Component | Definition | NexusFab implementation |
|--------------|------------|------------------------|
| **Drum** | Bottleneck machine pace — sets production rhythm | Identified by utilization scan; its cycle time = master schedule cadence |
| **Buffer** | Time buffer upstream of bottleneck — protects against starvation | `safety_factor × avg_upstream_variability`; typically 3× σ of upstream lead time |
| **Rope** | Release signal from bottleneck back to raw-material release — limits WIP | Release new job only when bottleneck completes one; prevents WIP explosion |

#### Buffer Sizing Rules

**Time buffer** (preferred for job-shop):
```
buffer_time = k × σ_upstream_lead_time
  k = 1.5  if CV < 0.5   (low variability)
  k = 2.0  if CV 0.5–1.0
  k = 3.0  if CV > 1.0   (high variability)
```

**Stock buffer** (continuous / bulk lines):
```
buffer_level = demand_rate_at_bottleneck × replenishment_lead_time × (1 + safety_factor)
```

Buffer penetration zones (TOC standard):

| Zone | Penetration | Response |
|------|-------------|----------|
| Green | 0–33% | Normal — no action |
| Yellow | 33–66% | Expedite upstream |
| Red | 66–100% | Emergency — override schedule, pull alternate source |

#### DBR Integration with Finite-Capacity Scheduling

DBR and CP-SAT are complementary, not competing:
1. **DBR identifies** the bottleneck and sets the master schedule pace (drum).
2. **CP-SAT optimizes** the detailed schedule for all non-bottleneck machines (subordination step).
3. **Buffers** provide the slack that makes the CP-SAT schedule robust to variability.

NexusFab workflow: after each SimPy replication, compute utilization per machine → identify bottleneck → pass bottleneck ID + buffer parameters to CP-SAT scheduler → CP-SAT generates detail schedule with bottleneck protected. Re-evaluate bottleneck identity on every rerouting event (bottleneck can shift after a breakdown).

#### TOC Five Focusing Steps (dashboard framing)

1. **Identify** — utilization heatmap, queue-length chart per machine
2. **Exploit** — eliminate waste at bottleneck (reduce setup/CIP time, prevent starving)
3. **Subordinate** — all non-bottleneck machines pace to bottleneck
4. **Elevate** — add capacity at bottleneck only if steps 1–3 are insufficient
5. **Repeat** — bottleneck moves after elevation; restart the cycle

---

## Cross-Reference: Simulation & Solver Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| DES engine | SimPy | Lightweight, process-based, pure-Python; sufficient for NexusFab scale |
| Scheduling solver | OR-Tools CP-SAT | Free, combinatorial-native, optional-interval rerouting; outperforms CBC on scheduling MIPs |
| LP / blending solver | PuLP + HiGHS | HiGHS is free and faster than CBC for LP; same PuLP API |
| Bottleneck detection | Utilization scan post-sim | Avoids analytical queue models; simulation already running anyway |
| Buffer sizing | Time-buffer DBR formula | Matches variability-driven food-plant reality better than fixed stock buffers |
| Replication count | 30 (production), 10 (dev) | Balances statistical validity with runtime cost |

---

## References

- SimPy documentation: https://simpy.readthedocs.io/
- OR-Tools CP-SAT scheduling guide: https://developers.google.com/optimization/scheduling/job_shop
- PuLP documentation: https://coin-or.github.io/pulp/
- HiGHS solver: https://highs.dev/
- Goldratt, E.M. — *The Goal* (DBR fundamentals)
- Hopp & Spearman — *Factory Physics* (buffer sizing analytics, variability theory)
