# Supply Chain & Demand Research

**Date:** 2026-07-23  
**Scope:** 5-plant food & beverage manufacturing network (Nestlé case study basis)  
**Status:** Active research document

## 1. Demand Forecasting Methods & Benchmarks

### 1.1 Method Comparison

Accuracy ranges are representative MAPE% for weekly SKU-level forecasts on mature FMCG products with 2+ years of history.

| Method | Accuracy (MAPE%) | Data Requirement | Seasonality Handling | Computational Cost | Best Fit Product Type |
|--------|------------------|------------------|---------------------|-------------------|----------------------|
| **Simple Exponential Smoothing** | 30–45% | 6+ months weekly | None (level only) | Negligible | Stable non-seasonal: dairy UHT, pet food kibble |
| **Holt-Winters (triple exp. smoothing)** | 20–35% | 2+ years (full seasonal cycle) | Additive or multiplicative seasonal component | Low | Regular seasonal cycles: water, ice cream |
| **ARIMA** | 20–35% | 2+ years, stationary after differencing | Manual via differencing only | Low–Medium | Low-variance staples with trend: dairy, pet food |
| **SARIMA** | 18–30% | 2+ years; (p,d,q)×(P,D,Q,52) for weekly | Native seasonal AR/MA components | Medium | Single dominant seasonal pattern: water summer, prepared foods winter |
| **Prophet** | 18–30% | 1+ year; tolerates gaps/outliers | Multiple seasonality + holiday regressors | Medium | Holiday-driven: confectionery; products with known structural breaks |
| **Gradient-Boosted Trees (XGBoost/LightGBM)** | 15–28% | 2+ years + external features | Encoded as cyclical features + holiday flags | Medium–High | High-SKU portfolios; promo-heavy categories |

**Current NexusFab implementation**: `demand.py` uses a seasonal-index multiplicative model (`_SEASONALITY` dict, line 24) with uniform noise to simulate forecast error at configurable `target_mape` (default 0.35). This is closest to a **simplified Holt-Winters** without fitted parameters — the trend is a fixed 0.2%/week linear ramp (line 187). Upgrade path: SARIMA or Prophet for individual SKU forecasting; gradient-boosted trees for cross-portfolio demand sensing.

### 1.2 Forecast Accuracy Benchmarks

Industry-representative MAPE% ranges by product stability class and horizon (sourced from IBF benchmarks, Gartner supply chain research, M-competition results applied to CPG).

| Product Stability Class | NexusFab Examples | Weekly MAPE% | Monthly MAPE% | Quarterly MAPE% |
|------------------------|-------------------|-------------|--------------|-----------------|
| **Stable / base demand** | Dairy UHT milk, pet food kibble, bottled water (off-peak) | 20–30% | 12–20% | 8–15% |
| **Seasonal** | Bottled water (peak), ice cream, prepared soups (winter) | 25–40% | 15–25% | 10–18% |
| **Promotional / spike-driven** | Confectionery (holiday), any SKU under BOGO/TPR | 35–55% | 20–35% | 15–25% |
| **New product / short lifecycle** | Line extensions, limited editions, seasonal flavours | 40–60%+ | 25–40% | 18–30% |
| **Intermittent / long-tail** | Low-volume specialty SKUs, MTO items | 50–80%+ | 35–55% | 25–40% |

**Key relationships**:
- Monthly MAPE is typically 40–50% lower than weekly MAPE for the same SKU (noise cancels).
- Plant-level forecast accuracy is 5–10 pp better than SKU-level (hierarchy aggregation).
- NexusFab's default `target_mape=0.35` aligns with the "seasonal" class — appropriate for the mixed portfolio but could be sharpened per-category.

**Recommended per-category MAPE targets for NexusFab**:

| Category | Suggested `target_mape` | Rationale |
|----------|------------------------|-----------|
| WATER | 0.30 | Seasonal but predictable; weather-correlated |
| CONFECTIONERY | 0.40 | Holiday spikes create high variance; 4:1 peak:trough |
| DAIRY | 0.25 | Steady base demand; short shelf life forces accuracy |
| PET_FOOD | 0.25 | Stable consumption; low seasonality (1.2:1) |
| PREPARED_FOODS | 0.30 | Moderate seasonality (1.5:1); winter peak predictable |

### 1.3 Demand Sensing vs Demand Planning

| Dimension | Demand Sensing | Demand Planning |
|-----------|---------------|-----------------|
| **Horizon** | 1–2 weeks | 3–12 months |
| **Primary data** | POS sell-through, warehouse withdrawals, real-time inventory | Historical shipments, seasonal patterns, trade plans |
| **Update frequency** | Daily or intra-week | Weekly or monthly S&OP cycle |
| **Methods** | ML on recent signals (GBT, neural nets); POS-weighted blending | Statistical (SARIMA, Holt-Winters, Prophet); judgemental adjustment |
| **Accuracy gain** | 20–40% MAPE reduction vs statistical baseline at 1-week horizon | Sets the baseline; captures structural changes |
| **Use case** | Replenishment, short-cycle production scheduling, promo response | Capacity planning, procurement, S&OP |
| **NexusFab relevance** | Short-cycle plants: dairy (72h milk shelf life), water (continuous) | All plants; especially confectionery (8–12 wk cocoa lead) and prepared foods (6–8 wk imports) |

**How they work together**: Demand planning sets the baseline and drives long-lead procurement. Demand sensing overwrites the near-term window (1–2 weeks) with POS-adjusted actuals. In NexusFab, `generate_demand_plan()` serves the planning role; a sensing layer would adjust `forecast_units` for weeks 1–2 while leaving weeks 3+ untouched.

---

## 2. FMCG Demand Patterns & Promotion Effects

### 2.1 Seasonality Profiles by Category

Profiles match `_SEASONALITY` in `demand.py` (lines 24–31). Drivers and sub-patterns documented per category.

#### Water (WATER) — Summer Peak

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| **Index** | 0.70 | 0.75 | 0.85 | 0.95 | 1.10 | 1.30 | 1.40 | 1.35 | 1.10 | 0.90 | 0.75 | 0.70 |

- **Pattern**: Unimodal bell peaking Jul (1.40), trough Dec–Jan (0.70). Peak:trough = 2:1.
- **Drivers**: Temperature and hydration. Each +1°C above 20°C adds ~2–3% to bottled water volume.
- **Sub-patterns**: Sparkling less seasonal (1.5:1); large-format 5L more seasonal (2.5:1, BBQ/outdoor). Single-serve 0.5L flatter (impulse/convenience).
- **Forecast levers**: Weekly max temperature regressor can reduce MAPE by 5–8 pp during May–Sep.

#### Confectionery (CONFECTIONERY) — Holiday Spikes

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| **Index** | 0.55 | 1.60 | 0.60 | 1.70 | 0.60 | 0.55 | 0.55 | 0.55 | 0.65 | 1.70 | 1.10 | 2.20 |

- **Pattern**: Multi-modal — 4 spikes: Feb (Valentine's 1.60), Apr (Easter 1.70), Oct (Halloween 1.70), Dec (Christmas 2.20). Deep summer troughs (0.55). Peak:trough = 4:1.
- **Drivers**: Gifting occasions. Production must ramp 6–8 weeks before each spike (cocoa lead times).
- **Sub-patterns**: Everyday bars ~2:1; seasonal moulds (Easter eggs, advent calendars) are make-or-miss with zero demand post-holiday.
- **Forecast levers**: Holiday dates known years ahead — Prophet holiday regressor particularly effective. Key risk: over/under-producing seasonal moulds (near-zero residual value).

#### Dairy (DAIRY) — Steady Base + Ice Cream Summer

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| **Index** | 0.50 | 0.55 | 0.70 | 0.90 | 1.20 | 1.50 | 1.50 | 1.40 | 1.10 | 0.80 | 0.55 | 0.50 |

- **Pattern**: Summer peak from ice cream/flavoured milk. UHT and powder near-flat; swing is chilled/frozen sub-portfolio. Peak:trough = 3:1.
- **Drivers**: Temperature (ice cream), school holidays (flavoured milk). Raw milk supply is counter-seasonal (spring flush, winter trough) — supply-demand mismatch.
- **Sub-patterns**: UHT 1.2:1. Yoghurt 1.5:1. Ice cream 4:1+ (near-zero Dec–Jan in cold climates).
- **Forecast levers**: 72-hour raw milk shelf life makes dairy the strongest demand sensing candidate — small errors create waste/stockouts within days.

#### Pet Food (PET_FOOD) — Steady + Promo Spikes

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| **Index** | 0.90 | 0.90 | 0.95 | 1.00 | 1.05 | 1.10 | 1.10 | 1.05 | 1.00 | 0.95 | 0.90 | 0.95 |

- **Pattern**: Near-flat (1.2:1). Mild summer uptick from outdoor activity. Real volatility comes from promotions, not seasons.
- **Drivers**: Habitual year-round consumption. Dec slight bump from premium treat gifting.
- **Sub-patterns**: Kibble flattest. Wet food slightly seasonal (1.3:1). Treats most volatile — promotion-driven.
- **Forecast levers**: Best-in-portfolio MAPE potential (20–25%). Primary error source is promotion timing/depth — 40% price cut on mainstream kibble generates 2–3× volume spike for 2–4 weeks, then demand trough from pantry destock.

#### Prepared Foods (PREPARED_FOODS) — Winter Peak + Holiday

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| **Index** | 1.00 | 0.95 | 0.90 | 0.85 | 0.90 | 0.95 | 0.90 | 0.85 | 1.00 | 1.10 | 1.20 | 1.30 |

- **Pattern**: Inverted-U peaking winter (Nov–Jan). Trough Apr–Aug. Peak:trough = 1.5:1.
- **Drivers**: Comfort food (soups, noodles, ready meals) in cold weather. Holiday entertaining (Dec). Back-to-school convenience (Sep–Oct).
- **Sub-patterns**: Soups/broths most seasonal (2:1). Noodles 1.3:1. Frozen ready meals flatter (1.2:1).
- **Forecast levers**: Gradual ramp (Sep→Dec) gives 8–12 weeks to build inventory. Cold snaps create short-term spikes above baseline.

### 2.2 Promotion Effect Modeling

Trade promotions account for 30–60% of total volume in FMCG categories like confectionery and pet food. Modeling them is essential for production scheduling and inventory management.

#### Promotion Types & Typical Lift

| Promotion Type | Mechanism | Volume Lift | Duration | Post-Promo Dip | Cannibalisation |
|----------------|-----------|------------|----------|----------------|-----------------|
| **Temporary Price Reduction (TPR)** | 10–30% off shelf | +30–80% | 1–2 wks | –15–25% for 2–3 wks | 5–15% adjacent SKUs |
| **BOGO / Buy-2-Get-1** | 33–50% effective discount | +100–200% | 1–2 wks | –25–40% for 3–4 wks (pantry loading) | 10–20% smaller packs |
| **Feature & Display (F&D)** | End-cap, flyer | +20–50% | 1 wk | Minimal | Low |
| **Seasonal Campaign** | Holiday packs, limited editions | +50–150% | 4–8 wks | Near-zero residual post-season | Shifts everyday → seasonal pack |
| **Bundling / Multipack** | e.g. 8-pack for price of 6 | +40–60% | 2–4 wks | –10–20% on single units | Cannibalises single-serve |

#### Modeling Approaches

**1. Uplift multiplier (current-architecture compatible)**

Simplest — multiply baseline by uplift factor during promo weeks:
```
promo_forecast = baseline × seasonal_factor × promo_uplift_factor
```
Add post-promo dip factor (e.g. 0.80 for 2 weeks after BOGO) to capture forward-buying.

**2. Regression-based (intermediate)**

Include promotion features in the model: `is_promo`, `promo_discount_pct`, `promo_type` (one-hot), `weeks_since_last_promo` (dip decay), `competitor_promo`. Prophet handles via `add_regressor()`; for GBT these become feature columns.

**3. Causal / econometric (advanced)**

Estimate price elasticity from scan data:
- Own-price elasticity: –1.5 to –3.0 for FMCG (10% price cut → 15–30% volume increase)
- Cross-price elasticity: +0.3 to +0.8 for close substitutes
- Promotion frequency fatigue: 4th TPR in a quarter is 30–50% weaker than the 1st

#### Post-Promotion Effects

| Effect | Magnitude | Duration | Most Affected |
|--------|-----------|----------|---------------|
| **Pantry loading** | –15–40% vs baseline | 2–4 wks | Pet food kibble, water multipack, dairy UHT |
| **Category expansion** | +3–8% sustained lift | 4–8 wks | Confectionery (impulse), prepared foods (trial) |
| **Brand switching** | Net zero if symmetric | 2–6 wks | All with close substitutes |
| **Pull-forward** | +30–60% ship week –1 | 1 wk before promo | All (acute in DSD channels) |

### 2.3 Modelling Implications for NexusFab

1. **Per-category MAPE targets** — Replace flat `target_mape=0.35` (line 153) with category-specific values per §1.2 benchmarks. Dairy/pet food → 0.25; confectionery → 0.40.
2. **Weather regressors** — For water and dairy (ice cream), weekly temperature forecasts reduce MAPE by 5–8 pp during May–Sep peak.
3. **Promotion overlay** — No promotion mechanism exists in the current model. A promo calendar with uplift multipliers (§2.2) is the minimum viable extension, compatible with the existing seasonal-index architecture.
4. **Demand sensing for perishables** — Dairy's 72-hour shelf life and water's continuous production make these plants prime candidates for POS-driven sensing (§1.3), overriding weeks 1–2 of the statistical forecast.
5. **Seasonal mould management** — Confectionery holiday SKUs (Easter eggs, advent calendars) need separate forecast processes with retailer forward-order data, not statistical extrapolation.

---

## 3. Multi-Plant Allocation Optimization

### 3.1 Problem Formulation

**Objective:** Minimize total landed cost across the network:

```
min Σ_p Σ_l Σ_s Σ_t [
    C_prod(p,l,s) · x(p,l,s,t)           # production cost
  + C_change(l,s,s') · y(l,s,s',t)       # changeover cost
  + Σ_q C_trans(p,q) · z(p,q,s,t)        # transport cost
  + C_stock(s) · u(s,t)                   # stockout penalty
]
```

Where:
- `p` ∈ Plants {PLT-001..PLT-005}, `l` ∈ Lines per plant, `s` ∈ SKUs, `t` ∈ Periods (weeks)
- `x(p,l,s,t)` = units of SKU `s` produced on line `l` at plant `p` in period `t` (continuous, ≥ 0)
- `y(l,s,s',t)` = 1 if line `l` changes from SKU `s` to `s'` in period `t` (binary)
- `z(p,q,s,t)` = units of SKU `s` transferred from plant `p` to plant `q` in period `t` (continuous, ≥ 0)
- `u(s,t)` = stockout units for SKU `s` in period `t` (continuous slack variable, ≥ 0)

**Decision variables for NexusFab scale:**
- 5 plants × 17 lines × ~50 SKUs × 12 periods = ~102,000 continuous vars
- 17 lines × ~50 SKUs × 12 periods = ~10,200 binary changeover vars
- 5×4 routes × ~50 SKUs × 12 periods = ~12,000 transport vars
- Total: ~124,000 variables (~10K binary). This is a medium-scale MILP.

### 3.2 Constraints

**Capacity constraints — per line per period:**
```
Σ_s x(p,l,s,t) / rate(l,s) ≤ NetAvailableHours(p,l,t)
```
Each line type (`PET_BOTTLING`, `MOULDING`, `UHT_FILLING`, etc.) has a rated speed from seed data (`speed_units_per_min` in `LineSeed`). Not all SKUs can run on all lines.

**Allergen / category segregation:**
```
x(p,l,s,t) = 0  if category(s) ∉ allowed_categories(l)
```
NexusFab maps each plant to one category (WATER, CONFECTIONERY, DAIRY, PET_FOOD, PREPARED_FOODS). Cross-category production requires cleaning validation. Model as: inter-category transfers allowed, inter-category production on same line disallowed unless explicit allergen changeover cost is paid.

**Minimum batch size:**
```
x(p,l,s,t) ≥ MinBatch(s) · w(p,l,s,t)   [w binary: 1 if any production]
x(p,l,s,t) ≤ BigM · w(p,l,s,t)
```
From `products.py`, `units_per_batch` ranges 2,000–10,000. Production either meets minimum batch or is zero — no partial batches.

**Demand satisfaction:**
```
Σ_p x(p,l,s,t) + I(s,t-1) - I(s,t) + Σ_q z(q,p_demand,s,t) - u(s,t) ≥ D(s,t)
```
Where `D(s,t)` is the demand forecast from `generate_demand_plan()` and `I(s,t)` is ending inventory.

**Storage / inventory limits:**
```
I(s,t) ≤ MaxStorage(p) for all s at plant p
Σ_s I(s,t) ≤ PlantStorageCapacity(p)
```

**Transport minimum load (full truck):**
```
z(p,q,s,t) ≥ PALLETS_PER_TRUCK × TONS_PER_PALLET × v(p,q,s,t)  [v binary: ship or not]
```
From `network.py`: `PALLETS_PER_TRUCK = 20`, `TONS_PER_PALLET = 1.0`, so minimum 20 tons per shipment.

### 3.3 Transport Cost/Time Matrix

Derived from actual plant coordinates in `plants.py`. Euclidean approximation scaled to US road distances (multiply by ~69 miles/degree, then 1.3× road factor):

| From → To | PLT-001 (NYC) | PLT-002 (Chicago) | PLT-003 (Minneapolis) | PLT-004 (Atlanta) | PLT-005 (LA) |
|---|---|---|---|---|---|
| **PLT-001** | — | $180/plt, 14h | $250/plt, 20h | $140/plt, 13h | $460/plt, 42h |
| **PLT-002** | $180/plt, 14h | — | $110/plt, 7h | $130/plt, 11h | $310/plt, 30h |
| **PLT-003** | $250/plt, 20h | $110/plt, 7h | — | $210/plt, 18h | $270/plt, 26h |
| **PLT-004** | $140/plt, 13h | $130/plt, 11h | $210/plt, 18h | — | $370/plt, 34h |
| **PLT-005** | $460/plt, 42h | $310/plt, 30h | $270/plt, 26h | $370/plt, 34h | — |

**Cold chain surcharge:** Dairy (PLT-003) shipments require refrigerated trucks — add 35–50% to base pallet cost. Current `transport_cost_pallet()` does not differentiate; implementation should add a `cold_chain_factor` multiplier keyed on category = DAIRY.

**Truck parameters:**
- Standard dry van: 20 pallets, 44,000 lbs max payload (~20 tons)
- Refrigerated: 18 pallets effective (insulation takes space), same weight limit
- Transit times assume single-driver FTL; team drivers cut long-haul times by ~35%

### 3.4 Changeover Cost Model

Changeover costs differ dramatically by line type:

| Line Type | Typical Changeover Time | Cost (lost production + labor + materials) |
|---|---|---|
| PET_BOTTLING | 0.5–2 hrs | $500–$2,000 (format change) |
| GLASS_BOTTLING | 2–4 hrs | $2,000–$5,000 (mould change) |
| MOULDING | 3–6 hrs | $3,000–$8,000 (chocolate tempering reset) |
| ENROBING | 2–4 hrs | $2,500–$6,000 |
| UHT_FILLING | 4–8 hrs | $4,000–$10,000 (full CIP required) |
| POWDER_PACKING | 1–3 hrs | $1,500–$4,000 |
| EXTRUSION | 2–5 hrs | $3,000–$7,000 (recipe/die change) |
| RETORT_CANNING | 1–3 hrs | $1,000–$3,000 |
| KIBBLE_COATING | 1–2 hrs | $800–$2,000 |
| WRAPPING | 0.5–1.5 hrs | $400–$1,500 |
| MIXING_COOKING | 2–4 hrs | $2,000–$5,000 |
| FILLING | 1–2 hrs | $800–$2,500 |
| NOODLE_LINE | 2–4 hrs | $2,000–$4,000 (die/cut change) |
| CANNING | 0.5–1.5 hrs | $500–$1,500 |
| ASEPTIC | 4–6 hrs | $3,500–$8,000 (full sterilization cycle) |

The optimizer should use a simplified 3-tier changeover model:
1. **Same family:** 15 min, $200 (format change only)
2. **Same category, different family:** full changeover per table above
3. **Cross-category:** not permitted on same line (allergen constraint)

---

## 4. Capacity Planning & Network Inventory

### 4.1 Net Available Capacity Model

**Net available capacity per line per week:**

```
NetHours(p,l,t) = CalendarHours × (1 - PlannedDowntime%) × OEE%
```

For a 24/7 operation: `CalendarHours = 168 hrs/week`

Applying NexusFab seed data:

| Plant | Lines | Starting OEE | Planned DT* | Net hrs/line/wk | Capacity tons/day |
|---|---|---|---|---|---|
| PLT-001 (Water) | 4 | 62% | 8% | 95.8 | 1,400 |
| PLT-002 (Confec) | 3 | 55% | 12% | 81.3 | 140 |
| PLT-003 (Dairy) | 3 | 48% | 10% | 72.6 | 550 |
| PLT-004 (Pet Food) | 4 | 60% | 8% | 92.7 | 420 |
| PLT-005 (Prepared) | 3 | 52% | 10% | 78.6 | 220 |

*Planned downtime estimates: CIP/SIP cleaning (dairy/confec higher), planned maintenance windows, shift changeovers.

**Calculating production capacity in units:**
```python
net_hours = 168 * (1 - planned_downtime_pct) * oee
units_per_week = net_hours * 60 * speed_units_per_min  # speed from LineSeed
tons_per_week = units_per_week / units_per_ton          # product-specific conversion
```

**OEE decomposition** (for identifying improvement levers):
```
OEE = Availability × Performance × Quality
```
- Availability = (Planned production time - Unplanned stops) / Planned production time
- Performance = (Ideal cycle time × Total units) / Operating time
- Quality = Good units / Total units

Current `PlantSeed.starting_oee` is aggregate. For the optimizer, decompose into these three factors so maintenance improvements (availability), line speed tuning (performance), and quality initiatives can be modeled independently.

### 4.2 Single-Location Safety Stock (Current Model)

Current implementation in `demand.py` (`_safety_stock`):
```python
SS = z × σ_d × √(LT)
```
Where:
- `z` = service level z-score (1.65 for 95%)
- `σ_d` = demand std dev ≈ avg_demand × MAPE
- `LT` = lead time in weeks (default 2.0)

This is the standard formula. Correct for single-echelon.

### 4.3 Multi-Plant Network Safety Stock

**The square-root law for inventory pooling:**

When consolidating inventory from `n` independent-demand locations into `k` locations:
```
SS_pooled = SS_single × √(k/n)
```

For NexusFab's 5-plant network, centralizing safety stock from 5 locations to 1:
```
SS_central = SS_per_plant × √(1/5) = SS_per_plant × 0.447
```
**~55% safety stock reduction** if demand is uncorrelated across regions.

**Reality check:** Demand across NexusFab plants is NOT fully independent — national promotions and weather patterns create positive correlation (ρ > 0). Adjusted formula:

```
SS_pooled = SS_single × √[ (1/n) + ρ × (1 - 1/n) ]
```

With ρ = 0.3 (moderate regional correlation for food/bev):
```
SS_pooled = SS_single × √[ 0.2 + 0.3 × 0.8 ] = SS_single × √0.44 = SS_single × 0.66
```
**~34% reduction** — more realistic.

### 4.4 Centralized vs Decentralized: Decision Framework

| Factor | Centralized (1–2 hubs) | Decentralized (per-plant) | NexusFab Recommendation |
|---|---|---|---|
| Safety stock cost | Lower (pooling benefit) | Higher (each plant buffers independently) | Centralize slow-movers |
| Transport cost | Higher (more outbound miles) | Lower (closer to demand) | Decentralize fast-movers |
| Response time | Slower (42h max from LA→NYC) | Faster (local) | Decentralize perishables |
| Risk | Single point of failure | Resilient | Hybrid |
| Cold chain | Expensive to ship long-distance | Natural fit for dairy | Dairy stays at PLT-003 |

**Recommended hybrid strategy for NexusFab:**

1. **WATER (PLT-001):** Decentralized — high-volume, low-value, transport cost dominates. Hold safety stock at PLT-001.
2. **CONFECTIONERY (PLT-002):** Semi-centralized — high seasonality (4:1 holiday spikes) makes safety stock expensive. Pre-build and distribute 6–8 weeks before peaks. PLT-002 holds base stock; overflow to PLT-001 dry storage.
3. **DAIRY (PLT-003):** Decentralized — cold chain constraint, perishability. Safety stock at PLT-003 only, short shelf life limits pooling benefit.
4. **PET_FOOD (PLT-004):** Centralized candidate — mild seasonality (1.2:1), long shelf life, high-value. Pool at PLT-004, ship to regional DCs.
5. **PREPARED_FOODS (PLT-005):** Decentralized — moderate volume, some perishability. Hold at PLT-005.

### 4.5 Multi-Echelon Inventory Optimization (MEIO)

For a full network model, optimize inventory at two echelons:
- **Echelon 1:** Plant finished goods buffer (cycle stock + safety stock)
- **Echelon 2:** Regional distribution centers (safety stock only, replenished from plants)

**Guaranteed service time model:** Each node promises a service time to its downstream customer. Safety stock at each node covers the gap between its replenishment time and its committed service time:
```
SS(node) = z × σ_d × √( replenishment_time - committed_service_time )
```

This decomposes the network inventory problem into independent per-node calculations once service times are fixed — solvable without the full MILP.

### 4.6 Solver Selection & Performance

**Problem characteristics:**

| Metric | Value |
|---|---|
| Continuous variables | ~114,000 (production + transport) |
| Binary variables | ~22,200 (changeover + batch + ship-or-not) |
| Total variables | ~136,000 |
| Constraints | ~150,000 |
| Problem class | Mixed-Integer Linear Program (MILP) |

**Solver comparison:**

| Solver | License | Expected Solve Time | Recommendation |
|---|---|---|---|
| **OR-Tools CP-SAT** | Apache 2.0 | 30–120s to optimal | **Use this.** Already a dependency (`rerouting.py`). Handles mixed scheduling + allocation. Parallelizes across cores. |
| **PuLP + CBC** | EPL 1.0 | 5–15s (LP relaxation), 60–300s (MILP) | Good for Phase 2 prototyping (LP relaxation, drop binaries). |
| **Gurobi** | Commercial | 10–30s to optimal | 3–10× faster than CBC. Overkill unless solve time is critical. |
| **HiGHS** | MIT | 10–60s (MILP) | Open-source CBC alternative. Drop-in PuLP backend. |

**Do NOT add Gurobi** — the problem at ~136K vars / ~22K binaries is well within CP-SAT's capability. Gurobi adds license management complexity for marginal speed gain.

**Scaling notes:**
- 12-week horizon, weekly periods: 136K vars — CP-SAT 30–120s
- 52-week horizon: ~590K vars — 5–15 min; use rolling horizon (solve 12 weeks, advance 4, re-solve)
- Daily periods (84 days): ~1.1M vars — rolling horizon mandatory; solve 2-week windows

**CP-SAT configuration (same pattern as `rerouting.py`):**
```python
solver.parameters.max_time_in_seconds = 120
solver.parameters.num_workers = 8
```
CP-SAT requires integer variables — multiply continuous quantities by 100 (centitones) for 2-decimal precision. Use `NewOptionalIntervalVar` for changeovers, same pattern as `rerouting.py`.

### 4.7 Implementation Phasing

1. **Phase 1 (current):** Heuristic rebalancing in `network.py` — transfer from overloaded (>80% util) to underloaded (<60%) plants based on utilization thresholds.
2. **Phase 2:** LP relaxation — drop binary changeover/batch variables, solve continuous allocation + transport with PuLP/CBC. Gives optimal flow but ignores sequencing.
3. **Phase 3:** Full MILP — add changeover binaries and minimum batch constraints via OR-Tools CP-SAT. Target: weekly planning cycle with 12-week rolling horizon.

---

## 5. Raw Material Management & Supplier Lead Times

### 5.1 Raw Material Categories by Plant Type

Each NexusFab plant type (mapped to `category` in `nexusfab/seed/plants.py`) consumes a distinct bill of materials. Materials split into **process inputs** (transformed into product) and **packaging inputs** (containment, labelling).

#### PLT-001 — Water Bottling (WATER, 1 400 t/day)

| Category | Materials | Sourcing |
|----------|-----------|----------|
| Process — water | Source water (municipal/spring), CO₂ (food-grade, bulk liquid) | Local utility / regional spring; industrial gas supplier |
| Packaging — primary | PET preforms (0.5 L, 1.0 L, 1.5 L), glass bottles (L3), aluminium cans (L4) | Domestic blow-mould / glass plant; regional can supplier |
| Packaging — secondary | HDPE caps, shrink-sleeve labels, carton trays, shrink film | Domestic |
| Process aids | Ozone, UV lamps, CIP chemicals (caustic, peracetic acid) | Industrial chemical distributor |

#### PLT-002 — Confectionery (CONFECTIONERY, 140 t/day)

| Category | Materials | Sourcing |
|----------|-----------|----------|
| Process — bulk | Cocoa mass, cocoa butter, cocoa powder | Imported (West Africa / SE Asia) |
| Process — sweeteners | Sugar (granulated), glucose syrup, milk powder (whole/skim) | Domestic/regional |
| Process — inclusions | Hazelnuts, wafer sheets, vanilla extract, lecithin | Imported (Turkey/Italy — nuts) / domestic |
| Packaging — primary | Flow-wrap film (BOPP/metalized), moulded trays, foil | Domestic converter |
| Packaging — secondary | Display cartons, case shippers, palletisation film | Domestic |

#### PLT-003 — Dairy (DAIRY, 550 t/day)

| Category | Materials | Sourcing |
|----------|-----------|----------|
| Process — base | Raw milk (Grade A), cream, skim milk concentrate | Local dairy co-ops (daily collection) |
| Process — cultures & additives | Starter cultures, stabilisers (pectin, carrageenan), fruit preparations | Cultures imported (Denmark/France); fruit prep regional |
| Process — powder line | Whole milk for spray-drying, maltodextrin | Local dairy pool |
| Packaging — primary | Tetra Pak cartons (aseptic), HDPE bottles, powder tins/pouches | Tetra Pak regional; domestic |
| Packaging — secondary | Corrugated trays, shrink bundles | Domestic |

#### PLT-004 — Pet Food (PET_FOOD, 420 t/day)

| Category | Materials | Sourcing |
|----------|-----------|----------|
| Process — proteins | Meat & bone meal (chicken, beef, fish), fresh meat slurry | Domestic renderers / regional abattoirs |
| Process — carbohydrates | Corn, wheat, rice, soy meal | Domestic grain elevators |
| Process — micro-ingredients | Vitamin/mineral premix, taurine, palatability coatings, colours | Specialty suppliers (imported premix blends) |
| Packaging — primary | Multi-wall kraft bags (kibble), retort pouches, steel cans | Domestic |
| Packaging — secondary | Corrugated cases, pallet stretch film | Domestic |

#### PLT-005 — Prepared Foods (PREPARED_FOODS, 220 t/day)

| Category | Materials | Sourcing |
|----------|-----------|----------|
| Process — vegetables | Dehydrated vegetables, tomato paste, onion powder, spice blends | Regional (tomato paste sometimes imported — Italy/China) |
| Process — proteins | Chicken/beef IQF portions, textured soy protein, egg powder | Domestic poultry/beef; soy imported |
| Process — sauces/seasonings | Soy sauce, MSG, chilli paste, seasoning oils, wheat flour | Mix of domestic and imported (SE Asia) |
| Process — noodles (L3) | Wheat flour, palm oil, starch | Domestic flour mill; palm oil imported (SE Asia) |
| Packaging — primary | PP/EVOH trays (MAP), laminated sachets, cups with lidding film | Domestic converter |
| Packaging — secondary | Printed cartons, corrugated shippers | Domestic |

---

### 5.2 Supplier Lead Time Table

Lead times drive the `lead_time_weeks` parameter in `nexusfab/optimization/demand.py:_safety_stock()` (current default: 2.0 weeks). The table below provides category-specific values for more accurate safety stock sizing.

| Material Category | Local Lead Time | Imported Lead Time | MOQ (typical) | Shelf Life Constraint |
|---|---|---|---|---|
| **WATER — source water** | 0 (continuous) | n/a | n/a | Use within 24 h of treatment |
| **WATER — CO₂** | 1–2 days | n/a | 1 tanker (20 t) | Indefinite (compressed gas) |
| **WATER — PET preforms** | 1–2 weeks | 4–6 weeks | 1 truckload (~500k units) | 12 months (UV degradation) |
| **WATER — caps / labels** | 1–2 weeks | 3–4 weeks | 100k units | 18 months |
| **WATER — glass bottles** | 2–3 weeks | 6–8 weeks | 1 pallet (2 000 units) | Indefinite |
| **CONFEC — cocoa (mass/butter/powder)** | n/a | 8–12 weeks (origin) | 1 container (20 t) | 12 months (cool/dry) |
| **CONFEC — sugar** | 1–2 weeks | 4–6 weeks | 25 t bulk | 24 months |
| **CONFEC — milk powder** | 2–3 weeks | 6–8 weeks | 1 t bags | 18 months |
| **CONFEC — hazelnuts** | n/a | 6–10 weeks (harvest-dependent) | 5 t | 9 months (cold stored) |
| **CONFEC — packaging film** | 2–3 weeks | 5–6 weeks | 1 roll lot (10k m) | 12 months |
| **DAIRY — raw milk** | 0 (daily collection) | n/a | 1 tanker (25 000 L) | 72 h (chilled at 4 °C) |
| **DAIRY — cultures** | 2–4 weeks | 4–6 weeks (import) | 1 unit dose (50 L batch) | 6 months (frozen) |
| **DAIRY — fruit preparations** | 2–3 weeks | 4–6 weeks | 1 t IBC | 9 months (chilled) |
| **DAIRY — Tetra Pak cartons** | 3–4 weeks | 6–8 weeks | 100k units | 18 months |
| **PET FOOD — meat meal** | 1–2 weeks | 4–6 weeks | 25 t bulk | 6 months (ambient) |
| **PET FOOD — grains (corn/wheat/rice)** | 1–2 weeks | 3–5 weeks | 25 t truck | 12 months (dry) |
| **PET FOOD — vitamin premix** | 3–4 weeks | 8–12 weeks | 500 kg | 12 months (cool/dry) |
| **PET FOOD — retort pouches** | 2–3 weeks | 5–7 weeks | 50k units | 24 months |
| **PET FOOD — steel cans** | 2–3 weeks | 5–6 weeks | 1 pallet (5k units) | Indefinite |
| **PREPARED — dehydrated veg** | 1–2 weeks | 4–6 weeks | 1 t | 18 months (ambient) |
| **PREPARED — IQF proteins** | 1–2 weeks | 4–6 weeks | 5 t | 18 months (frozen at –18 °C) |
| **PREPARED — tomato paste** | 2–3 weeks | 6–8 weeks (Italy/China) | 1 t drum | 24 months |
| **PREPARED — wheat flour** | 1 week | 3–4 weeks | 25 t bulk | 12 months |
| **PREPARED — palm oil** | n/a | 6–8 weeks (SE Asia) | 20 t flexitank | 12 months |
| **PREPARED — MAP trays** | 2–3 weeks | 5–6 weeks | 50k units | 12 months |

**Recommendation for model**: Override the flat `lead_time_weeks=2.0` default in `demand.py` with per-category values. Critical imported materials (cocoa, nuts, palm oil, vitamin premix) need 8–12 week lead times; local perishables (milk, water) need near-zero.

---

### 5.3 Material Substitution Rules

Substitution is constrained by food safety regulation, customer specification, and organoleptic impact. Approved alternates below are pre-qualified — they can be switched without a new product development cycle.

| Primary Material | Approved Alternate(s) | Quality Impact | Switching Time |
|---|---|---|---|
| Cocoa butter | Cocoa butter equivalents (CBE — shea/sal/illipe) | Minor flavour/snap change; labelling update required ("contains vegetable fat") | 1–2 weeks (reformulation validation) |
| Granulated sugar (beet) | Granulated sugar (cane); isoglucose | None (cane); slight process change (isoglucose viscosity) | Same day (cane); 1 week (isoglucose) |
| Whole milk powder | Skim milk powder + anhydrous milk fat | Equivalent if ratio maintained | 2–3 days (blend ratio change) |
| Hazelnuts (Turkey) | Hazelnuts (Italy/Oregon) | Slight size/flavour variance | 1–2 weeks (supply switch) |
| PET preforms (Supplier A) | PET preforms (Supplier B) | None if same resin spec (FDA-approved PET) | 1 week (qualification run) |
| Raw milk (Co-op A) | Raw milk (Co-op B) | Fat/protein profile variance ±0.3 %; standardise in-plant | Same day |
| Chicken meal | Turkey meal | Slight palatability shift (pet food); label update | 1 week (feeding trial sign-off) |
| Corn (grain) | Wheat or rice | Nutritional profile shift — reformulate premix | 2–4 weeks (nutritional validation) |
| Tomato paste (Italian) | Tomato paste (Chinese/Californian) | Brix/colour variance; taste panel needed | 1–2 weeks |
| Wheat flour (local mill) | Wheat flour (alternate mill) | Gluten % variance — test dough rheology | 3–5 days |
| Palm oil (SE Asia) | Sunflower oil / rapeseed oil | Different frying behaviour; reformulation needed for noodle lines | 2–3 weeks |
| Tetra Pak (standard) | SIG Combibloc (aseptic carton) | Equivalent barrier; line changeover parts needed | 4–6 weeks (equipment adaptation) |

**Rules engine notes**:
- Substitutions within the same allergen class (e.g., tree-nut-for-tree-nut) only require QA sign-off.
- Cross-allergen substitutions (e.g., soy protein for milk protein) require full HACCP review — see `nexusfab/optimization/regulatory.py`.
- Packaging substitutions that change dimensions require line tooling changes — factor MTTR from `nexusfab/seed/plants.py` equipment data.

---

### 5.4 Supply Disruption Scenarios

NexusFab already models one supply disruption: **SIM-006** ("Raw Material Shortage — Cocoa", 4-week duration, PLT-002) in `nexusfab/simulation/scenarios.py`. The table below catalogues the broader disruption landscape for all plant types.

| Disruption Type | Affected Materials | Typical Cause | Frequency | Duration | Severity | Mitigation Strategy |
|---|---|---|---|---|---|---|
| **Commodity price spike** | Cocoa, sugar, palm oil, grains | Crop failure, speculation, export bans | 1–2×/year | 2–6 months (price) | Medium — margin squeeze, no stockout | Forward contracts (6–12 mo); dual-source |
| **Origin supply failure** | Cocoa, hazelnuts, palm oil | Drought, political instability (W. Africa, Turkey) | 1×/2–3 years | 4–12 weeks | High — potential stockout | Strategic buffer (8 weeks); substitute materials (§5.3) |
| **Transport disruption** | All imported materials | Port congestion, vessel delays, Suez/Panama canal events | 2–3×/year | 1–4 weeks | Medium | Safety stock; regional alternate suppliers; air freight for critical micro-ingredients |
| **Local supplier failure** | Raw milk, fresh meat, regional flour | Equipment failure at supplier, quality rejection, bankruptcy | 1–2×/year per supplier | 1–3 days (quality); 2–6 weeks (bankruptcy) | Medium–High | Multi-source contracts (min. 2 suppliers per critical category); daily quality screening |
| **Quality/contamination hold** | Any ingredient | Failed micro test, foreign body, allergen cross-contact | 3–5×/year across network | 1–5 days (retest); 2–4 weeks (recall) | High — regulatory risk | Supplier audit programme; incoming inspection; lot traceability |
| **Packaging supplier disruption** | PET preforms, cartons, cans, film | Resin shortage, converting plant fire, print plate delay | 1–2×/year | 2–6 weeks | Medium — line downtime | Dual-source packaging; 4-week buffer stock for primary packaging |
| **Energy/utility disruption** | CO₂, water, steam, electricity | Grid outage, gas curtailment, water quality event | 1–3×/year | Hours to 2 days | Low–Medium | On-site backup (generators, CO₂ tanks); see `nexusfab/optimization/energy.py` |
| **Regulatory/sanctions** | Imported ingredients from affected countries | Trade sanctions, import ban, new tariff | Rare (<1×/year) | Months | High — supply redesign | Geographic diversification; approved alternate origins |
| **Seasonal harvest gap** | Hazelnuts (Aug–Oct harvest), fruit prep (seasonal fruit) | Off-season = no new supply | Annual, predictable | 3–6 months off-season | Low if planned | Pre-season procurement; cold-stored buffer |

**Recommendation for model**: Extend `ScenarioConfig` with a `supply_disruption` parameter (material, delay_weeks, affected_plants) to generalise SIM-006 to other disruption types. Current `demand_multiplier` doesn't capture supply-side shocks.

---

### 5.5 Inventory Holding Costs

Storage requirements and costs vary by temperature regime. Costs below are per standard pallet position per week (industry averages for multi-plant FMCG networks).

| Storage Regime | Temperature | Applicable Materials | Cost / Pallet / Week | Notes |
|---|---|---|---|---|
| **Ambient (dry warehouse)** | 15–25 °C, <65% RH | Sugar, flour, grains, PET preforms, cans, dry packaging, dehydrated veg, cocoa (tempered) | $3.50–5.00 | Lowest cost; bulk of inventory by volume |
| **Cool / tempered** | 12–18 °C | Cocoa butter, chocolate mass, confectionery WIP, vitamin premix | $5.50–7.50 | Required to prevent bloom (cocoa) and potency loss (vitamins) |
| **Chilled** | 2–6 °C | Raw milk, cream, cultures, fruit preparations, fresh meat | $8.00–12.00 | High energy cost; short shelf life drives FIFO discipline |
| **Frozen** | –18 °C to –25 °C | IQF proteins (chicken, beef, fish), frozen fruit prep, ice cream WIP | $12.00–18.00 | Highest energy; blast freezing capex; longest shelf life |
| **Hazardous / controlled** | Varies | CIP chemicals (caustic, acid), ozone, food-grade lubricants | $6.00–10.00 | Bunded storage; regulatory permits; low volume |

#### Holding Cost Breakdown (typical)

| Cost Component | % of Total Holding Cost |
|---|---|
| Warehouse space (rent/depreciation) | 30–35% |
| Energy (refrigeration, climate control) | 15–35% (higher for chilled/frozen) |
| Insurance & shrinkage | 5–8% |
| Handling (in/out, stock rotation) | 15–20% |
| Capital cost of inventory (WACC on tied-up cash) | 10–15% |
| Quality monitoring & waste/expiry write-off | 5–12% |

#### Per-Plant Estimated Weekly Holding Costs

| Plant | Primary Storage Type | Estimated Pallets on Hand | Est. Weekly Cost |
|---|---|---|---|
| PLT-001 (Water) | Ambient (preforms, cans) + cool (CO₂) | 800–1 200 | $3 500–5 500 |
| PLT-002 (Confec) | Tempered (cocoa) + ambient (sugar, packaging) | 600–900 | $4 000–6 000 |
| PLT-003 (Dairy) | Chilled (milk, cream) + frozen (cultures) + ambient (powder, cartons) | 1 000–1 500 | $9 000–15 000 |
| PLT-004 (Pet Food) | Ambient (meal, grains) + cool (premix) + chilled (fresh meat) | 700–1 100 | $5 000–8 000 |
| PLT-005 (Prepared) | Frozen (IQF) + ambient (dry goods) + chilled (sauces) | 500–800 | $5 500–9 000 |

**Recommendation for model**: Incorporate holding cost per storage regime into demand planning — currently `demand.py` calculates safety stock purely on service level and lead time. High-cost frozen/chilled materials should have tighter reorder points to avoid excessive carrying cost, while cheap ambient materials can hold larger buffers.

---

### 5.6 Key Modelling Implications

1. **Per-category lead times** — Replace the flat `lead_time_weeks=2.0` in `demand.py:generate_demand_plan()` with a material-category lookup. The range is 0 (raw milk) to 12 weeks (imported cocoa/vitamin premix).
2. **Supply-side scenarios** — Generalise `SIM-006` in `scenarios.py` by adding `supply_disruption` fields to `ScenarioConfig`. This enables simulation of the full disruption matrix in §5.4.
3. **Substitution engine** — A future module could consume the rules in §5.3 to auto-switch materials when lead time exceeds buffer, feeding into the demand replanning loop.
4. **Holding cost weighting** — Weight safety stock calculations by holding cost per pallet-week to avoid over-stocking expensive chilled/frozen materials. A simple cost multiplier in `_safety_stock()` would suffice.
5. **Perishable inventory** — Materials with shelf life < 2 weeks (raw milk, cream, fresh meat) need daily replenishment logic, not weekly reorder-point models. This is a distinct inventory policy from the bulk dry goods.
