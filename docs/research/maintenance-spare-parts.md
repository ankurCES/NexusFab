# Equipment MTBF/MTTR & Failure Distributions

## 1. MTBF/MTTR Reference Table — Food & CPG Manufacturing

> **Sources:** ISO 14224 (reliability data for process industry), OREDA Handbook, GEA/Tetra Pak maintenance bulletins, PMMI benchmarks, Reliasoft Weibull++ industry datasets. All figures assume continuous 3-shift production with planned maintenance excluded from MTBF.

### 1.1 MTBF/MTTR by Equipment Type

| Equipment Type | Variant | MTBF (hrs) | MTTR (hrs) | Failure Distribution | Weibull β | Weibull η (hrs) | Exp λ (failures/hr) |
|---|---|---|---|---|---|---|---|
| **Rotary Filler** | Liquid/semi-liquid, volumetric | 800–1,200 | 2.5–4.0 | Weibull (wear-out) | 2.2 | 1,100 | — |
| **Linear Filler** | Piston/peristaltic | 600–1,000 | 1.5–3.0 | Weibull (wear-out) | 1.8 | 900 | — |
| **Gravity Filler** | Dry/free-flow product | 2,500–4,000 | 1.0–2.0 | Exponential (random) | ~1.0 | — | 2.9×10⁻⁴ |
| **UHT Sterilizer** | Tubular heat exchanger | 1,500–2,500 | 3.0–6.0 | Weibull (thermal fatigue) | 2.5 | 2,200 | — |
| **UHT Sterilizer** | Plate heat exchanger | 800–1,500 | 4.0–8.0 | Weibull (gasket wear) | 2.0 | 1,250 | — |
| **Mixer / Blender** | Paddle/ribbon, industrial | 2,000–4,000 | 2.0–4.0 | Weibull (wear-out) | 2.0 | 3,400 | — |
| **Mixer / Blender** | High-shear / homogenizer | 800–1,500 | 3.0–5.0 | Weibull (rotor-stator) | 2.5 | 1,330 | — |
| **Extruder** | Twin-screw, pet food | 400–700 | 5.0–8.0 | Weibull (abrasive wear) | 3.0 | 615 | — |
| **Extruder** | Single-screw, confectionery | 800–1,500 | 3.0–5.0 | Weibull (moderate wear) | 2.2 | 1,300 | — |
| **Flow-wrap (HFFS/VFFS)** | Standard film packaging | 350–700 | 0.5–1.5 | Weibull (mixed) | 1.5 | 590 | — |
| **Cartoner** | Horizontal/vertical | 500–1,000 | 1.5–3.0 | Weibull (wear-out) | 1.8 | 870 | — |
| **Case Packer** | Wrap-around / RSC | 700–1,200 | 2.0–4.0 | Weibull (wear-out) | 2.0 | 1,080 | — |
| **Palletizer** | Conventional layer type | 1,500–3,000 | 2.0–4.0 | Weibull (wear-out) | 2.0 | 2,540 | — |
| **Palletizer** | Robotic (6-axis arm) | 3,000–8,000 | 3.0–6.0 | Weibull (mixed) | 1.5 | 5,960 | — |
| **Belt Conveyor** | Flat/inclined | 3,000–6,000 | 0.5–2.0 | Exponential (random) | ~1.0 | — | 2.2×10⁻⁴ |
| **Roller/Slat Conveyor** | Accumulation / transfer | 5,000–10,000 | 0.5–1.5 | Exponential (random) | ~1.0 | — | 1.3×10⁻⁴ |
| **CIP Skid** | Centralized, multi-circuit | 1,200–2,500 | 1.0–3.0 | Weibull (seal + sensor) | 1.6 | 2,100 | — |

### 1.2 Weibull Parameter Notes

| β range | Failure rate behaviour | Typical cause | Example equipment |
|---|---|---|---|
| β < 1 | Decreasing (infant mortality) | Manufacturing defects, install errors | New seals, incorrect assembly |
| β = 1 | Constant (random) | Random shocks, operator error | Conveyors, gravity fillers |
| β 1.5–2 | Slowly increasing (early wear-out) | Mixed random + wear | Flow-wrap, CIP skids, robotic palletizers |
| β 2–3 | Moderate wear-out | Cyclic mechanical fatigue | Rotary fillers, mixers, UHT plates |
| β > 3 | Rapid wear-out | Abrasion, thermal cycling | Pet food extruders (screw/barrel) |

**η (characteristic life)** = age at which 63.2% of units have failed. Use η ≈ MTBF / Γ(1 + 1/β):
- β=1.5 → MTBF ≈ 0.903 η
- β=2.0 → MTBF ≈ 0.886 η
- β=2.5 → MTBF ≈ 0.900 η
- β=3.0 → MTBF ≈ 0.893 η

### 1.3 Availability Benchmarks (OEE reference)

| Equipment Class | Target Availability | Typical Achieved | Key driver of gap |
|---|---|---|---|
| Fillers (rotary/linear) | 90–95% | 82–88% | Seal changes, product changeover |
| UHT sterilizers | 92–96% | 85–91% | CIP + gasket management |
| Extruders (pet food) | 80–88% | 72–80% | Screw/die wear frequency |
| Flow-wrap | 88–93% | 78–85% | Film breaks, sealing jaw fouling |
| Palletizers (robotic) | 95–99% | 91–95% | End-of-arm tooling, safety resets |
| Conveyors | 97–99% | 94–97% | Unplanned jams, belt splices |
| CIP Skids | 90–95% | 85–92% | Conductivity probe drift, valve faults |

---

## 2. Common Failure Modes by Equipment Type

### 2.1 Failure Mode Matrix

| Equipment | Mechanical Wear | Electrical / Drive | Sensor Drift | Contamination / Hygiene |
|---|---|---|---|---|
| **Rotary Filler** | Rotary valve seat wear, piston seal extrusion, cam follower wear | Servo drive faults (overcurrent), encoder failure | Fill volume sensor (level, flow), NO₂ flush pressure | Product ingress in valve body; CIP port blockage; biofilm on contact surfaces |
| **Linear Filler** | Piston O-ring extrusion, check valve leakage, peristaltic tube fatigue | Stepper/servo overcurrent on thick products | Volumetric flow meter drift, pressure transducer offset | Sticky product residue in cylinder bore |
| **Gravity Filler** | Gate valve seat erosion (dry product), slide gate jamming | Motor contactor wear, VFD overtemperature | Level sensor fouled by dust, capacitive sensor drift | Product caking in hopper; dust ingress into motor cooling |
| **UHT Sterilizer (tubular)** | Tube scaling (calcium carbonate, protein denaturation), pump impeller erosion | Pump motor insulation degradation (heat) | Thermocouple calibration drift (HACCP CCP ±0.5°C), flow meter fouling | Biofilm in low-velocity zones; seam corrosion if CIP chemistry wrong |
| **UHT Sterilizer (plate)** | Gasket extrusion/swelling, plate deformation (water hammer), inter-plate crack | Homogenizer high-pressure pump valve wear | Pressure differential transmitter drift | Plate channelling failure (cross-contamination risk); gasket microcracking |
| **Mixer / Blender (paddle)** | Agitator blade erosion, shaft seal wear, gearbox tooth pitting | Main drive motor winding degradation, VFD fault (harmonics) | Load cell drift (product accumulation under feet), speed encoder fault | Seal failure allowing product contamination of bearings; product caking in dead-zones |
| **Mixer / Blender (high-shear)** | Rotor-stator gap closure (tip wear), mechanical seal failure | Motor overload (viscous product), bearing overtemperature | Temperature probe drift in stator gap | Product carbonisation on rotor at high shear; mechanical seal water leak → product dilution |
| **Extruder (pet food)** | Screw flight erosion (abrasive meat meal, ash), barrel liner wear, die insert wear, thrust bearing fatigue | Drive gearbox oil seal failure, DC/AC drive thermal shutdown | Barrel temperature PID sensor drift (±2-5°C shifts), melt pressure transducer zero drift | Rancid product residue in flights; die blockage (bone fragments); Moisture intrusion into motor compartment |
| **Extruder (confectionery)** | Screw wear (moderate, sugar abrasion), die clogging (sugar crystallisation) | Barrel heater element burnout, thermocouple open circuit | Temperature zone sensor drift | Fat bloom residue in flights; sugar crystallisation in die orifices overnight shutdown |
| **Flow-wrap (HFFS)** | Sealing jaw wear/scoring, cutter blade dulling, film drive roller grooving | Servo amplifier fault (jaw servo), photocell power supply | Film registration sensor (mark sensor) drift, product detection sensor false trips | Sealing jaw contamination (fat/sauce deposit) causes seal integrity failure; film dust |
| **Cartoner** | Blank feeder cam wear, glue wheel coating, chain stretch in indexing drive | Servo fault (axis jam), 24V DC PSU dropout | Blank-present sensor (reflective) fouled by glue dust, flap-closed sensor | Glue contamination on sensors and product; cardboard dust in servo motor cooling slots |
| **Case Packer** | Gripper pad wear, pneumatic cylinder cushion failure, cam follower wear | Pneumatic solenoid valve coil burnout, servo fault | Presence sensors (capacitive/photoelectric) drift from case dust | Product spillage contaminates case sensor faces; conveyor belt contamination |
| **Palletizer (layer)** | Pusher plate wear, layer sheet feed rollers, pallet conveyor chain | Layer-forming servo fault, stretch wrap motor | Layer complete sensor (photoeye), pallet height sensor | Sheet paper dust in control cabinet; stretch wrap film jams |
| **Palletizer (robotic)** | End-of-arm tooling (EOAT) suction cup wear, wrist joint overload | Servo amplifier (axis 4–6 most stressed), teach pendant cable fray | Force/torque sensor drift, vision system calibration shift | Product residue on suction cups causes pick failures; grease migration from joints |
| **Belt Conveyor** | Belt splice failure, drive pulley lagging wear, return roller bearing failure, belt edge fraying | VFD overtemperature, motor bearing failure | Speed encoder (belt slip detection), belt tracking sensor | Product spillage accelerates belt degradation; caustic CIP splash on bearings |
| **Roller/Slat Conveyor** | Roller bearing seizure (water ingress), slat hinge pin wear, chain elongation | Drive motor bearing failure (wet environment) | Jam detection (current sensor) | Product accumulation in roller gaps; standing water in frame from CIP → corrosion |
| **CIP Skid** | Centrifugal pump mechanical seal failure, impeller erosion (caustic), valve actuator diaphragm fatigue | Pump motor winding fault (moisture ingress), conductivity transmitter power supply | Conductivity probe coating/fouling (milk stone), flow meter zero drift, temperature probe offset | Chemical cross-contamination if valve sequencing fails; biofilm if CIP temperature not maintained |

### 2.2 Failure Mode Frequency Distribution (typical across food plant)

| Failure category | Share of recorded failures | Notes |
|---|---|---|
| Mechanical wear (seals, bearings, wear parts) | 38–45% | Most predictable; driven by run-hours and load cycles |
| Electrical / drive (motors, VFDs, contactors) | 20–28% | VFD and motor bearing faults dominant |
| Sensor drift / calibration | 12–18% | Often masked until CCP audit or quality escape |
| Contamination / hygiene stops | 8–15% | Highest consequence (regulatory stop risk) |
| Lubrication failures | 5–10% | Leading root cause of premature bearing and gearbox failure |
| Operator-induced / procedural | 5–8% | Incorrect CIP, wrong product loaded, over-torqued fitting |

### 2.3 Failure Cascade Patterns

Equipment failures rarely stay contained. Common upstream/downstream propagation:

| Initiating Failure | Direct Cascade | Secondary Cascade | Recovery Constraint |
|---|---|---|---|
| Filler stops | Upstream buffer fills → upstream processing slows/stops | Downstream packaging starved → idle labor | Filler MTTR (2–4 hrs) gates entire line |
| UHT sterilizer unplanned stop | Upstream raw milk tank overflow risk (if continuous) | Downstream UHT packer starved; opened containers expire | CIP mandatory before restart (1.5–3 hrs added to MTTR) |
| Extruder die blockage (pet food) | Upstream cooker/conditioner must be stopped or vented to waste | Downstream dryer/coater starved | Die cleaning adds 1–3 hrs; product in conditioner may be lost |
| Case packer jam | Palletizer starved; cases back-accumulate on conveyor | Upstream packaging slows to accumulation limit | 20–30 min cascade if conveyor fills before fix |
| Palletizer stops | Full cases accumulate → case packer back-pressured → upstream packaging slows | Significant floor congestion; manual diversion needed | Labor-intensive manual palletising fallback |
| Belt conveyor drive failure | Complete line segment stop | Both upstream and downstream equipment halted | Failure MTTR 0.5–2 hrs but cascade resume takes 30–60 min |
| CIP skid failure | Cannot clean any circuit on skid | All equipment on that circuit is production-locked until CIP complete | Regulatory hold: no production restart without validated CIP |
| Robot palletizer E-stop (safety curtain) | Stops case flow from packer | Back-pressure to packer, then to packaging | Often clears in <5 min (false trip) — but 3 resets per shift = significant loss |

**Cascade severity rule of thumb:** Any stop upstream of a CIP-mandatory point (UHT, filler, CIP skid) adds 1.5–3 hrs to effective MTTR because the equipment cannot restart without a CIP cycle before re-introduction of food.

---

# Spare Parts Inventory & Criticality Model

## 1. ABC-XYZ Classification — Food Manufacturing

### Classification Matrix

| | X (Predictable demand, CV < 0.5) | Y (Variable demand, CV 0.5–1.0) | Z (Sporadic/rare, CV > 1.0) |
|---|---|---|---|
| **A** (High value/critical, top 20% spend) | **AX** Bearings for main conveyor drive, VFD units, PLC I/O modules | **AY** Centrifugal pump seals, heat exchanger gaskets | **AZ** Compressor crankshaft, extruder barrel sections |
| **B** (Moderate, mid 30% spend) | **BX** V-belts, shaft couplings, standard motors ≤ 15kW | **BY** Solenoid valves, pneumatic cylinders, proximity sensors | **BZ** Gearbox assemblies, custom mixing paddles |
| **C** (Low value, bottom 50% spend) | **CX** O-rings, fasteners, filters, lubricants | **CY** Light curtains, indicator lamps, cable glands | **CZ** Obsolete legacy PLC cards, one-off fabricated brackets |

### Stock Policy by Cell

| Cell | Policy | Min Stock | Reorder Trigger |
|------|---------|-----------|-----------------|
| AX | Always-in-stock | 2× MTTR consumption | ROP-based, auto |
| AY | Buffer stock | 1× MTTR | ROP-based |
| AZ | Insurance / critical spare | 1 unit (NBD delivery risk) | Annual review |
| BX | Cycle stock | 0–1 unit | ROP-based |
| BY | On-demand with buffer | 0–1 unit | Semi-annual review |
| BZ | Make-to-order or consignment | 0 | Triggered by failure |
| CX | Bulk stock | 30-day supply | Min-max |
| CY/CZ | Minimum or no stock | 0 | Order on failure |

---

## 2. Reorder Point Formulas

### Reorder Point (ROP)

```
ROP = (Average Daily Usage × Lead Time in Days) + Safety Stock
```

### Safety Stock

```
SS = Z × σ_LTD

where:
  Z        = service level z-score (see table)
  σ_LTD   = std dev of demand during lead time
           = sqrt(Lead_Time × σ_d²  +  d_avg² × σ_LT²)
  σ_d      = std dev of daily demand
  σ_LT     = std dev of lead time (days)
  d_avg    = average daily demand
```

#### Service Level → Z-Score

| Service Level | Z-Score |
|---------------|---------|
| 90% | 1.28 |
| 95% | 1.645 |
| 98% | 2.05 |
| 99% | 2.33 |
| 99.5% | 2.575 |

### Worked Example — Conveyor Drive Bearing

- `d_avg` = 0.05 units/day (1 bearing every 20 days)
- `σ_d` = 0.03 units/day
- Lead time = 14 days (domestic distributor)
- `σ_LT` = 2 days
- Target service level = 99% → Z = 2.33

```
σ_LTD = sqrt(14 × 0.03² + 0.05² × 2²)
       = sqrt(0.0126 + 0.01)
       = sqrt(0.0226) ≈ 0.15 units

SS    = 2.33 × 0.15 ≈ 0.35 → round up to 1 unit

ROP   = (0.05 × 14) + 1 = 1.7 → order when stock ≤ 2 units
```

### Economic Order Quantity (EOQ)

```
EOQ = sqrt((2 × D × S) / H)

where:
  D = annual demand (units)
  S = ordering cost ($/order)  — typically $50–$150 for industrial parts
  H = annual holding cost ($/unit/year) = unit cost × holding rate (20–30%)
```

---

## 3. Critical Spare Parts by Equipment Type

### Filling & Packaging Line

| Equipment | Critical Part | Failure Mode | Lead Time (domestic) | Lead Time (import) | Est. Downtime if OOS |
|-----------|--------------|--------------|---------------------|--------------------|----------------------|
| Form-Fill-Seal machine | Film drive servo motor | Catastrophic jam, no fill | 3–5 days | 4–8 weeks | 8–16 hrs |
| Form-Fill-Seal machine | Sealing jaw heater element | No seal integrity | 1–2 days | 2–4 weeks | 2–4 hrs |
| Rotary filler | Rotary valve seal set | Product leakage, hygiene stop | 2–3 days | 3–6 weeks | 4–8 hrs |
| Labeler | Label sensor (photoeye) | Misapplication, line stop | 1–3 days | 2–4 weeks | 1–2 hrs |
| Case packer | Pneumatic cylinder (main fold) | Package damage | 2–4 days | 3–6 weeks | 2–4 hrs |
| Checkweigher | Load cell | False rejects or no check | 5–10 days | 6–12 weeks | Full line stop |
| Metal detector | Coil assembly | Regulatory stop (HACCP CCP) | 7–14 days | 8–16 weeks | Full line stop |

### Cooking & Processing Equipment

| Equipment | Critical Part | Failure Mode | Lead Time (domestic) | Lead Time (import) |
|-----------|--------------|--------------|---------------------|--------------------|
| Industrial mixer | Main drive gearbox | Total loss of agitation | 5–10 days | 8–16 weeks |
| Industrial mixer | Agitator shaft seal | Product contamination, hygiene | 3–5 days | 4–8 weeks |
| Retort / autoclave | Safety relief valve | Pressure vessel stop (regulatory) | 5–14 days | 10–20 weeks |
| Retort / autoclave | Temperature sensor (RTD) | HACCP CCP failure | 2–5 days | 2–6 weeks |
| Pasteurizer (HTST) | Divert valve | Food safety stop | 3–7 days | 6–12 weeks |
| Spray dryer | Atomizer disc/wheel | Total production stop | 10–21 days | 12–24 weeks |
| Evaporator | Mechanical seal set | Product loss, hygiene stop | 3–7 days | 6–10 weeks |

### Utilities & Auxiliary

| Equipment | Critical Part | Failure Mode | Lead Time (domestic) | Lead Time (import) |
|-----------|--------------|--------------|---------------------|--------------------|
| Air compressor | Unloader valve | No compressed air → plant-wide stop | 2–5 days | 4–8 weeks |
| Air compressor | Air-end (screw element) | Catastrophic loss | 10–21 days | 16–30 weeks |
| Refrigeration compressor | Shaft seal | Refrigerant loss, product temp excursion | 3–7 days | 8–16 weeks |
| Boiler | Water level sensor | Safety shutdown | 2–5 days | 4–10 weeks |
| Boiler | Burner control module | No steam, processing stop | 5–10 days | 8–16 weeks |
| Conveyor system | Drive shaft bearing (main) | Line stop | 1–3 days | 3–8 weeks |
| Conveyor system | Drive motor + VFD | Line stop | 2–5 days | 6–12 weeks |
| CIP system | Centrifugal pump mechanical seal | Hygiene protocol fail | 2–4 days | 4–8 weeks |
| CIP system | Conductivity probe | Cannot verify clean | 1–3 days | 3–6 weeks |

### Control & Instrumentation

| Part | Lead Time (domestic) | Lead Time (import) | Notes |
|------|---------------------|--------------------|----|
| PLC CPU module (common brands) | 3–10 days | 8–20 weeks | Keep 1 in stock always |
| I/O cards (DI/DO/AI/AO) | 2–7 days | 6–16 weeks | Stock by card type in use |
| HMI panel | 5–14 days | 10–20 weeks | Image backup is critical |
| VFD (common ratings: 5.5, 11, 22, 37 kW) | 3–10 days | 8–16 weeks | Stock 1 per rating used |
| Safety relay module | 2–5 days | 4–10 weeks | Regulatory stop if failed |
| Flow transmitter (Coriolis/mag) | 5–14 days | 10–20 weeks | Process stop if CCP-linked |

---

## 4. Spare Parts Cost Model

### Total Cost of Ownership

```
Total Annual Spare Parts Cost =
    Holding Cost
  + Ordering Cost
  + Stockout Cost (expected)
  + Obsolescence Cost
```

### 4.1 Holding Cost

```
H = C_unit × i × Q_avg

where:
  C_unit  = unit purchase price
  i       = holding rate (typically 20–30%/yr for industrial parts)
            Components:
              Capital cost of money:   8–12%
              Warehousing/space:        3–5%
              Insurance:                1–2%
              Deterioration/damage:     2–4%
              Inventory management:     2–3%
  Q_avg   = average on-hand quantity = (max stock + SS) / 2
```

**Typical holding rate for food manufacturing: 25% per year.**

Example: $5,000 gearbox, keep 1 unit → holding cost = $5,000 × 0.25 = $1,250/yr

### 4.2 Stockout Cost

```
C_stockout = P_stockout × (Production_Loss_Rate × MTTR + Emergency_Procurement_Premium)

where:
  P_stockout          = probability of stockout event (from service level model)
  Production_Loss_Rate = $ per hour of downtime
  MTTR                 = Mean Time To Repair (hours)
  Emergency_Premium    = expedited freight + premium supplier cost
```

#### Typical Production Loss Rates — Food Manufacturing

| Line Type | Downtime Cost ($/hr) | Basis |
|-----------|----------------------|-------|
| High-speed packaging (>200 units/min) | $8,000–$20,000 | Lost throughput + labor + scrap |
| Filling line (continuous) | $5,000–$12,000 | — |
| Batch cooking / processing | $3,000–$8,000 | Batch loss + restart waste |
| CIP / utilities only | $2,000–$5,000 | Indirect (delays downstream) |

#### Worked Example — Checkweigher Load Cell

- MTTR: 6 hours (diagnosis + swap + calibration)
- Downtime cost: $10,000/hr
- P_stockout at 95% SL: 5% per demand event, ~2 demand events/yr
- Emergency premium: $2,000 (overnight freight + expedite fee)

```
Expected annual stockout cost = 0.05 × 2 × (6 × $10,000 + $2,000)
                              = 0.10 × $62,000
                              = $6,200/yr

Holding cost of 1 spare ($3,500 load cell × 25%) = $875/yr

→ Stocking is justified: $875 << $6,200
```

### 4.3 Obsolescence Cost

| Part Category | Annual Obsolescence Risk | Notes |
|---------------|-------------------------|-------|
| PLC/HMI hardware | 5–10% of part value/yr | Vendor end-of-life cycles |
| Mechanical (bearings, seals) | 1–3% | Low risk if stored properly |
| Pneumatic / hydraulic | 2–5% | Seal degradation over time |
| Electronic sensors | 4–8% | Technology changes |
| Safety relays/modules | 3–6% | Standard revision changes |

**Maximum recommended shelf life (insurance spares):** 5–7 years for electronics, 10 years for mechanical with proper storage.

### 4.4 Criticality Score (for prioritization)

```
Criticality = (Downtime Cost × MTTR × P_failure) / (Unit Cost × Holding Rate)

Score > 10  → Always-in-stock (AZ or AX insurance spare)
Score 3–10  → ROP-based stocking
Score < 3   → Order-on-fail or consignment
```

---

## 5. Vendor Lead Time Reference Table

### Domestic Suppliers (US / Canada)

| Part Category | Standard Lead Time | Expedited (premium) | Typical Premium |
|---------------|-------------------|--------------------|----|
| Bearings (common sizes, SKF/NSK/FAG) | 1–3 days | Same day / next day | 2–3× |
| Standard motors (≤ 22 kW, NEMA) | 3–7 days | 1–3 days | 1.5–2× |
| VFDs (common brands: AB, Siemens, Danfoss) | 3–10 days | 1–5 days | 1.5–2× |
| PLC modules (AB, Siemens, Omron — common) | 3–10 days | 1–3 days | 2–3× |
| Pneumatic components (Festo, SMC, Parker) | 2–5 days | 1–2 days | 1.5–2× |
| Seals / O-rings (Parker, Trelleborg) | 1–3 days | Same day | 1.5× |
| Gearboxes (standard ratios) | 5–14 days | 3–7 days | 1.5–2.5× |
| Custom gearboxes / specialty | 6–16 weeks | 4–10 weeks | Minimal gain |
| Sensors (Sick, Keyence, Balluff) | 3–7 days | 1–3 days | 1.5–2× |
| Safety components (Pilz, Sick, Schmersal) | 5–14 days | 3–7 days | 1.5–2× |
| Mechanical seals (Flowserve, John Crane) | 5–14 days | 3–5 days | 2–3× |
| Heat exchanger plates/gaskets | 7–21 days | 5–10 days | 2× |

### Import / OEM Parts

| Part Category | Standard Import Lead Time | Notes |
|---------------|--------------------------|-------|
| European OEM parts (Italy, Germany) | 4–10 weeks | Air freight cuts to 2–4 weeks |
| Asian OEM parts (Japan, Taiwan, Korea) | 4–8 weeks | Air freight cuts to 2–3 weeks |
| Chinese commodity parts | 3–6 weeks | Quality variance; source from authorized dist |
| OEM-specific (proprietary to machine maker) | 8–24 weeks | Single source; highest risk |
| Spray dryer atomizer (GEA, APV, Niro) | 12–24 weeks | Custom-machined; maintain 1 in stock |
| Extruder screws/barrels | 12–20 weeks | Custom alloy; 1-for-1 insurance policy |
| Retort pressure vessels (custom) | 20–40 weeks | Regulatory re-cert required |

### Decision Rule: Stock vs Order

```
If (expedited_lead_time × downtime_cost_per_day) > (unit_cost × holding_rate + ordering_cost):
    → Stock locally
Else:
    → Order on demand (or use supplier consignment)
```

**Rule of thumb:** Any part whose expedited lead time exceeds 3 days AND whose failure causes > $5,000/hr downtime should be stocked on-site.

### Supplier Relationship Tiers (recommended)

| Tier | Description | Commitment |
|------|-------------|------------|
| Tier 1 (Emergency) | Local stocking distributor with same-day pull | Blanket PO, VMI agreement |
| Tier 2 (Primary) | Regional distributor, 1–5 day lead | Annual pricing agreement |
| Tier 3 (OEM/Specialty) | Direct to manufacturer or authorized OEM agent | Forecast sharing, safety stock at supplier |
| Tier 4 (Global spot) | Spot market for obsolete/rare parts | No commitment; due-diligence on counterfeits |

---

## 6. Sensor-Based Monitoring & Predictive Maintenance Signals

---

### 6.1 Sensor Taxonomy

| Equipment Type | Sensor Type | Measurand | Sampling Rate | Raw Data Volume |
|---|---|---|---|---|
| **Rotating machinery** (motors, pumps, fans, compressors) | Vibration (accelerometer) | RMS, peak, crest factor (X/Y/Z) | 10–25.6 kHz (raw), 1–10 Hz (RMS aggregated) | ~50 MB/day raw per axis; ~1 KB/day aggregated |
| | Temperature (RTD/thermocouple) | Bearing housing, motor winding | 1–4 Hz | ~350 KB/day |
| | Current (CT clamp) | Phase current, imbalance | 1–10 kHz (power quality), 1 Hz (trend) | ~5 MB/day raw; ~86 KB/day trend |
| | Acoustic emission | Ultrasonic 40–400 kHz | 500 kHz–1 MHz burst | ~200 MB/hr during burst capture |
| **Conveyors / drives** | Vibration | Belt tension resonance, roller bearing | 1–4 kHz | ~10 MB/day |
| | Temperature | Drive electronics, friction points | 1 Hz | ~86 KB/day |
| | Speed / encoder | RPM, slip | 100 Hz | ~8 MB/day |
| **Heat exchangers / boilers** | Temperature (multipoint) | Inlet/outlet ΔT, shell/tube | 1–4 Hz | ~350 KB/day per point |
| | Pressure (transmitter) | Differential pressure, fouling index | 1–4 Hz | ~350 KB/day |
| | Flow (Coriolis / mag) | Mass flow, volumetric | 4–10 Hz | ~700 KB/day |
| **Valves / actuators** | Position (LVDT / limit switch) | % open, travel time | 10 Hz | ~860 KB/day |
| | Torque / current | Actuator load | 100 Hz | ~8 MB/day |
| | Pressure (upstream/downstream) | Seat leakage proxy | 4 Hz | ~350 KB/day |
| **CNC / machine tools** | Spindle vibration | Chatter, imbalance | 10–50 kHz | ~100 MB/day raw |
| | Spindle current | Tool wear proxy | 1 kHz | ~86 MB/day |
| | Temperature | Spindle bearing, coolant | 1 Hz | ~86 KB/day |
| **Electrical switchgear / MCC** | Partial discharge (UHF) | Insulation degradation | 1 MS/s burst | Burst only, ~10 MB/event |
| | Temperature (IR / thermocouple) | Connection resistance rise | 0.1–1 Hz | ~8 KB/day |
| | Current / voltage | Harmonic distortion, THD | 10 kHz (power quality) | ~50 MB/day |

**Rule of thumb:** Raw vibration = 1–100 MB/sensor/day. Always aggregate to RMS + kurtosis + FFT bands at the edge; send ~1–10 KB/sensor/day to cloud.

---

### 6.2 Failure Signature Patterns

#### Rotating Machinery — Bearing Failure
| Time-to-Failure | Observable Signal | Threshold / Pattern |
|---|---|---|
| 2–4 weeks | Ultrasonic acoustic emission ↑ | dB level +6–10 dB above baseline |
| 1–2 weeks | Vibration kurtosis ↑ | Kurtosis > 4 (impulsive shock onset) |
| 72–168 hours | Vibration RMS ↑ (broadband) | RMS > 2× baseline; BPFO/BPFI sidebands in FFT |
| 24–48 hours | Bearing housing temp ↑ | +15–25°C above ambient, rising trend |
| 0–24 hours | Vibration RMS ↑↑, temp spike | RMS > 5× baseline; temp > 80°C |

**Action threshold:** Vibration RMS > 2× 30-day rolling median AND kurtosis > 5 → schedule replacement within 72 hours.

#### Pump — Cavitation / Impeller Wear
| Signal | Pattern |
|---|---|
| Vibration (broadband noise floor ↑) | Subnoise broadband energy rise at 1–10 kHz |
| Differential pressure ↓ | Flow performance curve shifts left (head loss) |
| Motor current ↑ | Absorbed power rises as efficiency drops |
| Acoustic emission | Intermittent bursts at bubble collapse frequency |

**Signature:** ΔP drops >10% below design curve at nominal flow AND current rises >5% → cavitation; check NPSH, inspect impeller within 2 weeks.

#### Motor — Winding Insulation / Overload
| Signal | Pattern |
|---|---|
| Winding temperature ↑ | >Class F limit (155°C); 10°C rise → 50% insulation life reduction (Arrhenius) |
| Current imbalance | Phase imbalance >2% → negative sequence heating |
| THD (harmonics) | THD >5% → additional copper losses |

#### Gearbox — Tooth Wear
| Signal | Pattern |
|---|---|
| Gear mesh frequency (GMF) sidebands in FFT | Sideband amplitude at GMF ± 1× shaft freq |
| Vibration RMS at GMF | Rises 3–6 dB over 2–4 weeks before spalling |
| Oil debris (particle counter) | Ferrous particle count >500 ppm → inspect |

#### Valve — Seat Leakage / Actuator Degradation
| Signal | Pattern |
|---|---|
| Seat leakage (pressure bleedthrough) | Downstream pressure rises when valve closed |
| Travel time increase | Actuator cycle time drifts >20% from baseline |
| Torque signature | Friction spike at mid-travel → packing wear |

---

### 6.3 PLC/SCADA Data Points — OPC-UA Tag Structure

#### Typical OPC-UA Namespace Layout
```
ns=2; s=Plant.Site01.Area_A.Cell_03.Pump_P101
├── Process
│   ├── FlowRate_LPS         (Float, 4 Hz)
│   ├── Pressure_InBar       (Float, 4 Hz)
│   ├── Pressure_OutBar      (Float, 4 Hz)
│   └── DifferentialPressure (Float, 4 Hz)  ← computed on PLC
├── Motor
│   ├── Current_A_PhaseA     (Float, 10 Hz)
│   ├── Current_A_PhaseB     (Float, 10 Hz)
│   ├── Current_A_PhaseC     (Float, 10 Hz)
│   ├── Speed_RPM            (Float, 4 Hz)
│   └── MotorTemp_DegC       (Float, 1 Hz)
├── Bearing
│   ├── BearingTemp_Drive    (Float, 1 Hz)
│   ├── BearingTemp_NonDrive (Float, 1 Hz)
│   └── VibrationRMS_mmps    (Float, 1 Hz)   ← on-board sensor unit
├── Status
│   ├── RunningStatus        (Bool)
│   ├── FaultCode            (UInt16)
│   ├── AlarmActive          (Bool)
│   └── RunHours_Total       (UInt32)
└── Maintenance
    ├── LastMaintDate        (DateTime)
    ├── NextMaintDue_Hours   (UInt32)
    └── OilLevel_Pct         (Float, 0.1 Hz)
```

#### Tag Count Estimates by Equipment Type

| Equipment | PLC Tags (typical) | OPC-UA Published Tags | Notes |
|---|---|---|---|
| Centrifugal pump | 40–60 | 15–25 | VFD adds ~20 tags |
| Conveyor drive | 25–40 | 10–18 | |
| Heat exchanger | 30–50 | 12–20 | Multipoint temps × 4–8 |
| Compressor | 80–120 | 30–50 | PID loops + valve positions |
| CNC machine | 150–300 | 50–100 | Axis positions + tool offsets |
| MCC / switchgear | 20–35 | 8–15 | Power quality meter tags |
| **Plant total (20 assets)** | ~1,500–3,000 | ~400–800 | At 100 ms–1 s scan rates |

#### OPC-UA Subscription Best Practices
- Use **monitored items** with deadband (engineering units): 0.5% FS for analog, any-change for digital.
- Group by scan rate: 100 ms group (current, vibration RMS), 1 s group (temp, pressure), 10 s group (status), 60 s group (totalisers).
- Deadband cuts network load 60–80% vs raw polling for slowly-changing process values.
- Set `PublishingInterval` = `SamplingInterval` of fastest group to avoid queue buildup.

---

### 6.4 Edge vs. Cloud Processing Tradeoffs

#### Decision Framework

```
Latency required < 100 ms   → Edge only (safety interlock, real-time alarm)
Latency OK < 5 s            → Edge detection, cloud confirmation
Latency OK < 60 s           → Edge aggregation, cloud ML inference
Latency OK hours/days       → Cloud only (trend analysis, model training)
```

#### What Stays at the Edge

| Function | Rationale | Compute Requirement |
|---|---|---|
| High-frequency vibration FFT | 10–50 kHz raw → extract 10–20 band features | ARM Cortex-A55 or equiv. |
| RMS / kurtosis / crest factor | Real-time streaming aggregation | Minimal |
| Alarm threshold comparison | < 10 ms latency needed | Minimal |
| Protocol translation (OPC-UA → MQTT Sparkplug B) | Bandwidth reduction before WAN | Minimal |
| Local historian buffer (on disconnect) | Never lose data during WAN outage | 8–32 GB SSD |
| Waveform capture trigger | Capture full waveform on threshold breach | Edge storage |

**Edge hardware target:** Industrial PC with dual-NIC (OT side + IT side), 4–8 core ARM/x86, 8 GB RAM, 64 GB SSD. Examples: Beckhoff CX series, Siemens IPC, Advantech UNO.

#### What Goes to Cloud

| Function | Rationale |
|---|---|
| ML model training (LSTM, autoencoder) | GPU compute, full dataset needed |
| RUL estimation with fleet data | Cross-asset comparison across plant/sites |
| Anomaly baseline updates | Rolling 30/90-day statistics |
| Trend dashboards & reporting | Not time-critical |
| Maintenance work order integration (ERP/CMMS) | Business system integration |
| Model version deployment back to edge | Inference model push |

#### Data Volume After Edge Reduction

| Raw sensor data | Edge output (aggregated features) | Reduction |
|---|---|---|
| 1 pump, raw vibration: 50 MB/day | 10 FFT band features @ 1 Hz: ~0.9 MB/day | 98% |
| 20-asset plant, all sensors: ~2 GB/day | Edge aggregated: ~20 MB/day | 99% |

**OT/IT segmentation rule:** Edge box has one NIC on OT VLAN (no internet, no WAN), one NIC on DMZ/IT VLAN. Data flows one direction: OT → edge buffer → DMZ → cloud. No inbound connections from cloud to OT network.

---

### 6.5 Recommended ML Approaches for Predictive Maintenance

#### 6.5.1 Anomaly Detection (no labeled failure data required)

**Isolation Forest** (baseline, ship first)
```python
from sklearn.ensemble import IsolationForest

# Features: [vib_rms, kurtosis, bearing_temp, motor_current, dp]
model = IsolationForest(contamination=0.02, n_estimators=100, random_state=42)
model.fit(normal_operating_data)  # 30–90 days of healthy operation

scores = model.decision_function(new_window)  # negative = anomalous
# ponytail: no tuning needed until false-positive rate > 5%
```
- Train on 30-day rolling window of "normal" operation.
- Contamination = 0.01–0.05 depending on expected failure frequency.
- Latency: < 1 ms inference per window → runs on edge.

**Autoencoder** (better for temporal patterns)
```python
# Keras 3-layer symmetric: input → 32 → 8 → 32 → input
# Train on normal data; reconstruction error = anomaly score
# Threshold: mean + 3σ of reconstruction error on validation set
# Deploy frozen model to edge via ONNX → onnxruntime (no GPU needed)
```
- Use when Isolation Forest false-positive rate is too high.
- ONNX export keeps edge inference < 5 ms on CPU.

#### 6.5.2 Remaining Useful Life (RUL) Estimation

**Survival Analysis — Weibull** (interpretable, works with small dataset)
```python
from lifelines import WeibullAFTFitter

# Covariates: vib_rms, bearing_temp, run_hours, load_factor
# Outcome: failure event + time
aft = WeibullAFTFitter()
aft.fit(df, duration_col='run_hours', event_col='failure')
rul_days = aft.predict_median(new_asset_features)
```
- Requires only ~50–200 historical failure events to fit.
- Produces probability distribution over RUL, not just point estimate.
- Use `lifelines` library; no GPU needed.

**LSTM / Temporal Fusion Transformer** (high-data regime)
```python
# Input: sliding window of 168 time steps (7 days @ 1 Hz)
# Features per step: [vib_rms, kurtosis, temp, current, dp] = 5 features
# Output: RUL in hours (regression) or P(failure in next 24h) (classification)
# Architecture: 2-layer LSTM → Dense(64) → Dense(1)
# ponytail: start with Weibull; LSTM only if Weibull RMSE > 20% of mean RUL
```
- Requires labeled run-to-failure dataset (use NASA CMAPSS for prototyping).
- Train in cloud; export to ONNX for edge inference.
- Target: RMSE < 15% of mean RUL on held-out assets.

#### 6.5.3 Failure Mode Classification (root cause, requires labeled data)

**Random Forest** (default choice)
```python
from sklearn.ensemble import RandomForestClassifier

# Classes: {normal, bearing_wear, imbalance, cavitation, overload, misalignment}
# Features: statistical features from 60-second windows
#   vib_rms, vib_peak, kurtosis, crest_factor, fft_band_1..10,
#   temp_delta, current_imbalance_pct, thd_pct

clf = RandomForestClassifier(n_estimators=200, max_depth=15, class_weight='balanced')
# Feature importance exposes which sensors matter most per failure mode
```
- Works with 500–5000 labeled examples per class.
- Feature importance → sensor selection for sparse deployments.
- Inference < 1 ms → runs on edge.

Use XGBoost/LightGBM when Random Forest macro-F1 < 0.85.

#### 6.5.4 Feature Engineering (the real work)

| Feature | Formula | Failure modes it catches |
|---|---|---|
| RMS | √(mean(x²)) | General severity |
| Kurtosis | E[x⁴]/σ⁴ | Impulsive bearing faults |
| Crest factor | peak/RMS | Shock events |
| FFT band energy | sum(|X[f1:f2]|²) | Gear mesh, bearing BPFO/BPFI |
| Spectral entropy | -Σ p log p | Complexity / randomness |
| ΔTemp (rate) | dT/dt over 10 min | Thermal runaway |
| Current THD | harmonic sum / fundamental | Power quality, winding faults |

#### 6.5.5 Implementation Sequence

```
Week 1–2:  Edge aggregation (RMS, kurtosis, temp) → MQTT Sparkplug B → cloud historian
Week 3–4:  Isolation Forest anomaly detection on 30-day baseline → alert integration
Month 2:   Weibull RUL model on first 3 asset classes with historical failure data
Month 3+:  LSTM/autoencoder for assets with >1 year continuous data
Month 6+:  Random Forest failure mode classification as labeled dataset accumulates
```

#### 6.5.6 Evaluation Metrics

| Model type | Primary metric | Target |
|---|---|---|
| Anomaly detection | Precision @ 90% recall | > 0.70 |
| RUL estimation | RMSE / mean RUL | < 15% |
| Failure classification | Macro F1 | > 0.85 |
| False alarm rate | Alarms/asset/month | < 2 |

---

### 6.6 Reference Architecture

```
 OT Network (isolated VLAN)
 ┌──────────────────────────────────────────┐
 │  PLC / Drive / Sensor                    │
 │  OPC-UA Server @ 100ms–1s scan          │
 └──────────────┬───────────────────────────┘
                │ OPC-UA subscriptions (asyncua)
 ┌──────────────▼───────────────────────────┐
 │  Edge Box (industrial PC, dual-NIC)      │
 │  • Feature extraction: RMS, kurtosis,    │
 │    FFT bands (numpy/scipy)               │
 │  • Isolation Forest inference (<1ms)     │
 │  • Local historian buffer (8–32 GB SSD)  │
 │  • MQTT Sparkplug B publisher            │
 └──────────────┬───────────────────────────┘
                │ MQTT over TLS (one-way: OT → DMZ)
 ┌──────────────▼───────────────────────────┐
 │  Cloud / On-prem (IT Network)            │
 │  • Time-series DB (InfluxDB/TimescaleDB) │
 │  • ML training (Weibull, LSTM)           │
 │  • Dashboard + alert routing             │
 │  • CMMS / ERP work order integration     │
 └──────────────────────────────────────────┘
```

**Python libraries:** `asyncua` (OPC-UA), `pymodbus` (Modbus fallback), `paho-mqtt` (MQTT Sparkplug B), `scikit-learn` (IF, RF), `lifelines` (Weibull RUL), `onnxruntime` (edge inference), `influxdb-client` (time-series).
