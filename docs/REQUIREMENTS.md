# NexusFab — Manufacturing Operations Optimizer
## Requirements Document v1.0

**Project:** NexusFab — AI-Driven Manufacturing Operations Optimization Platform  
**Case Study:** Nestlé S.A. Manufacturing Network (simulated with public data)  
**Date:** 2026-07-23  

---

## 1. Executive Summary

NexusFab is an operational optimization platform for multi-plant food & beverage manufacturing networks. It simulates and optimizes production scheduling, line allocation, maintenance planning, spare parts management, workforce scheduling, and supply chain coordination across a network of plants.

The platform uses Nestlé's publicly available manufacturing footprint as the simulation case study — 270+ factories across 70+ countries producing beverages, confectionery, dairy, pet food, infant nutrition, water, and coffee products.

### Core Problem Statement

When a production line goes down (planned or unplanned), manufacturers face cascading decisions:
- Can the workload shift to another line in the same plant?
- Can a sister plant absorb the production without impacting its own schedule?
- What are the logistics costs of inter-plant transfers?
- How does the rerouting affect maintenance schedules, spare parts, workforce, and demand fulfillment?

NexusFab answers these questions in real-time with optimization algorithms backed by realistic simulation.

---

## 2. Nestlé Manufacturing Footprint (Simulation Baseline)

### 2.1 Global Network

| Metric | Value | Source |
|--------|-------|--------|
| Total factories | 270+ (as of 2024) | Nestlé Annual Report |
| Countries | 76 | Nestlé Corporate |
| Employees (manufacturing) | ~150,000 of 270,000 total | Nestlé Annual Report |
| Revenue | CHF 93 billion (2023) | Nestlé Annual Report |
| Product brands | 2,000+ | Nestlé Corporate |

### 2.2 Product Categories & Production Types

| Category | Example Brands | Line Types | Typical Plant Scale |
|----------|---------------|------------|-------------------|
| **Water & Beverages** | Perrier, S.Pellegrino, Nestea, Nesquik | PET bottling, glass bottling, canning, Tetra Pak | 5-15 lines, 200-800 bpm |
| **Coffee & Beverages** | Nescafé, Nespresso, Starbucks@Home | Freeze-drying, spray-drying, capsule filling, jar filling | 3-10 lines, specialized |
| **Confectionery** | KitKat, Smarties, Aero, Quality Street | Moulding, enrobing, wrapping, packaging | 5-20 lines, 200-800 pcs/min |
| **Dairy & Ice Cream** | Häagen-Dazs, Dreyer's, Carnation | UHT filling, aseptic packaging, frozen filling | 3-12 lines, CIP-intensive |
| **Infant Nutrition** | NAN, Cerelac, Gerber | Spray-drying, blending, aseptic filling, powder packaging | 2-8 lines, pharma-grade controls |
| **Pet Food** | Purina, Friskies, Felix, Fancy Feast | Extrusion, retort canning, kibble coating, packaging | 5-15 lines, long campaigns |
| **Prepared Foods** | Maggi, Stouffer's, Lean Cuisine, Hot Pockets | Mixing, cooking, filling, freezing, packaging | 5-15 lines, multi-component |

### 2.3 Simulated Plant Network (for NexusFab MVP)

We simulate a **regional cluster of 5 plants** representing Nestlé's operational diversity:

| Plant ID | Name | Location | Category | Lines | Shifts | Annual Volume |
|----------|------|----------|----------|-------|--------|---------------|
| PLT-001 | NexWater-East | Eastern Region | Water/Beverages | 8 | 24/7 | 500M bottles |
| PLT-002 | NexConfec-Central | Central Region | Confectionery | 12 | 3-shift, 5 days | 50K tons |
| PLT-003 | NexDairy-North | Northern Region | Dairy/Ice Cream | 6 | 24/7 | 200M liters |
| PLT-004 | NexPet-South | Southern Region | Pet Food | 10 | 3-shift, 5 days | 150K tons |
| PLT-005 | NexPrepared-West | Western Region | Prepared Foods | 8 | 2-shift, 6 days | 80K tons |

### 2.4 Nestlé Continuous Excellence (NCE) Program

Nestlé's internal operational excellence methodology, based on TPM/WCM principles:
- **Foundation:** Total Productive Maintenance (TPM) pillars
- **Key metrics:** OEE, MTBF, MTTR, Cost Deployment, Quality Loss
- **Maturity levels:** Foundation → Pillar Establishment → Consistency → Excellence
- **Digital overlay:** Connected factories initiative, IoT sensors, predictive analytics

NexusFab models NCE-aligned KPIs and improvement tracking.

---

## 3. Optimization Modules

### 3.1 Module 1: Production Line Failure & Rerouting

**Scenario:** A bottling line goes down. Find the best alternative.

**Decision Variables:**
- Alternative lines in same plant (compatible format, available capacity)
- Alternative lines in sister plants (same product capability)
- Current workload on candidate lines (must not displace existing orders)
- Changeover time to switch product on candidate line
- Transport cost & time for inter-plant rerouting
- Customer SLA impact (OTIF risk)

**Constraints:**
- Candidate line must be format-compatible (same bottle type/size OR changeover feasible)
- Candidate line current utilization + rerouted volume ≤ 95% capacity
- Inter-plant transfer time + production time ≤ order due date
- Food safety: product must be approved for production at candidate plant (regulatory registration)
- Allergen compatibility (no allergen cross-contamination risk)

**Optimization Objective:** Minimize total cost = (downtime loss) + (changeover cost) + (transport cost) + (overtime cost) + (SLA penalty)

**Simulation Parameters:**
| Parameter | Range | Unit |
|-----------|-------|------|
| Downtime cost | $5,000 — $50,000 | per hour |
| Changeover time (same plant, same format) | 15 — 60 | minutes |
| Changeover time (same plant, different format) | 2 — 8 | hours |
| Inter-plant transport time | 4 — 48 | hours |
| Inter-plant transport cost | $500 — $5,000 | per load |
| SLA penalty (late delivery) | $1,000 — $50,000 | per order |
| Line speed (bottling) | 200 — 800 | bottles/min |

### 3.2 Module 2: Spare Parts Inventory & Availability

**Scenario:** Predict spare parts needs, maintain optimal inventory, prevent stockouts.

**Decision Variables:**
- Reorder point per part (based on MTBF and lead time)
- Safety stock level (based on demand variability and criticality)
- Vendor selection (lead time vs cost tradeoff)
- Cross-plant pooling of critical spares

**Constraints:**
- Budget ceiling per plant per quarter
- Warehouse capacity limits
- Minimum service level (95-99% parts availability)
- Vendor lead times (1 day — 16 weeks depending on part)

**Data Model:**

| Part Category | Examples | MTBF Trigger | Lead Time | Unit Cost | Criticality |
|---------------|---------|-------------|-----------|-----------|-------------|
| Wear parts | Seals, O-rings, gaskets, belts | 500-2000 hrs | 1-5 days | $5-$200 | Medium |
| Mechanical | Bearings, gearboxes, shafts | 2000-8000 hrs | 1-4 weeks | $100-$5,000 | High |
| Electrical | Motors, VFDs, PLCs, sensors | 5000-20000 hrs | 1-8 weeks | $200-$20,000 | Critical |
| Specialty | Custom molds, format parts | On-demand | 4-16 weeks | $1,000-$50,000 | Critical |

### 3.3 Module 3: Demand Planning & Production Scheduling

**Scenario:** Optimize production schedule to meet demand with minimal changeovers and waste.

**Decision Variables:**
- Production sequence per line per week
- Batch sizes per SKU
- Campaign lengths
- Make-to-stock vs make-to-order allocation
- Safety stock targets by SKU

**Constraints:**
- Demand forecast (with confidence intervals)
- Shelf life limits (fresh products: 7-30 days; ambient: 6-24 months)
- Minimum batch sizes (line-specific)
- Maximum inventory capacity (warehouse space)
- Allergen sequencing rules (non-allergen before allergen, or full CIP between)

**Simulation Parameters:**

| Parameter | Range | Notes |
|-----------|-------|-------|
| Forecast accuracy (SKU/month) | 60-80% | MAPE basis |
| Forecast accuracy (category/month) | 80-95% | |
| Promotional uplift | 1.5x — 4x | 1-4 week duration |
| Seasonal peak:trough ratio | 1.1:1 — 5.0:1 | By product category |
| SKUs per plant | 50-500 | Pareto: top 20% = 80% volume |
| Planning horizon | 1-4 weeks rolling | Frozen window: 24-72 hrs |
| Batch size (beverages) | 5,000 — 100,000 L | |
| Batch size (confectionery) | 200 — 10,000 kg | |
| Batch size (dairy) | 2,000 — 50,000 L | |

### 3.4 Module 4: Changeover Optimization

**Scenario:** Minimize changeover time and frequency through intelligent sequencing.

**Decision Variables:**
- Production sequence (which SKU follows which)
- Grouping of similar products (same flavor family, same format)
- Timing of CIP cycles (between product groups, not between each SKU)

**Key Data:**

| Changeover Type | Before SMED | After SMED | CIP Required? |
|-----------------|------------|------------|---------------|
| Same product, different size | 15-45 min | 5-15 min | No |
| Same flavor family, same format | 10-30 min | 5-10 min | Rinse only (5-15 min) |
| Different product, same format | 30-90 min | 10-30 min | Short CIP (20-45 min) |
| Different product + format | 2-8 hrs | 1-3 hrs | Full CIP (45-90 min) |
| Allergen transition | 2-4 hrs | 1-2 hrs | Allergen CIP (90-180 min) |
| End-of-day full sanitation | 2-4 hrs | N/A | Mandatory |

**Optimization:** Traveling Salesman Problem variant — find the sequence that minimizes total changeover time across all lines for a given planning period.

### 3.5 Module 5: Preventive & Predictive Maintenance

**Scenario:** Schedule maintenance to minimize unplanned downtime while maximizing line availability.

**Decision Variables:**
- Maintenance window scheduling (which shifts, which days)
- PM task grouping (batch multiple PMs when line is down)
- Condition-based trigger thresholds (vibration, temperature, pressure)
- Resource allocation (technicians, contractors)

**Parameters:**

| Equipment Type | MTBF (hrs) | MTTR (hrs) | PM Interval | PM Duration |
|----------------|-----------|-----------|-------------|-------------|
| Rotary filler | 400-1,200 | 0.5-4 | 500 hrs | 2-4 hrs |
| Screw capper | 500-1,500 | 0.5-2 | 750 hrs | 1-2 hrs |
| Labeler | 300-1,000 | 0.5-2 | 400 hrs | 1-3 hrs |
| Conveyor | 2,000-6,000 | 0.5-2 | 2,000 hrs | 1-2 hrs |
| Pasteurizer | 1,000-3,000 | 1-6 | 1,500 hrs | 4-8 hrs |
| Case packer | 500-1,500 | 0.5-3 | 750 hrs | 2-3 hrs |
| Palletizer | 1,000-4,000 | 0.5-3 | 1,500 hrs | 2-4 hrs |

**Cost Ratio:** Unplanned downtime costs 3x-10x more than planned maintenance.

### 3.6 Module 6: Energy Optimization

**Scenario:** Schedule energy-intensive operations during off-peak tariff periods.

**Parameters:**
| Parameter | Range |
|-----------|-------|
| Energy as % of manufacturing cost | 3-8% |
| Peak vs off-peak rate differential | 1.5x — 3.0x |
| Energy per ton (beverages) | 100-300 kWh/ton |
| Energy per ton (dairy) | 200-600 kWh/ton |
| Energy per ton (bakery) | 300-800 kWh/ton |
| Compressed air cost | 15-30% of electrical cost |
| Refrigeration cost | 20-40% of electrical cost |

**Energy-intensive operations to schedule:** Pasteurization, sterilization (retort), freezing tunnels, spray drying, oven/baking, compressed air generation.

### 3.7 Module 7: Quality Control & Waste Reduction

**Scenario:** Track quality metrics, predict defect patterns, minimize waste.

**Parameters:**
| Metric | Range |
|--------|-------|
| First Pass Yield | 90-99.5% |
| Fill weight compliance | 99.0-99.9% |
| Label accuracy | 99.5-99.99% |
| Packaging defect rate | 0.1-2% |
| Product waste (process) | 1-5% |
| Packaging waste | 1-3% |
| Rework rate | 0.5-3% |

### 3.8 Module 8: Multi-Plant Supply Chain Coordination

**Scenario:** Coordinate production across plant network to balance load and minimize logistics cost.

**Decision Variables:**
- Plant-to-DC allocation
- Inter-plant production transfers
- Capacity sharing during peak seasons
- Inventory pre-positioning

**Parameters:**
| Parameter | Range |
|-----------|-------|
| Inter-plant transfer lead time | 4-48 hours |
| Transfer cost per pallet | $50-$500 |
| DC-to-customer lead time | 1-7 days |
| Minimum transfer quantity | 1 full truck (26-33 pallets) |
| Cross-docking feasibility | Plant-specific |

### 3.9 Module 9: Workforce Scheduling

**Scenario:** Optimize shift assignments, skill matching, and overtime.

**Parameters:**
| Parameter | Range |
|-----------|-------|
| Shift patterns | 8hr/12hr, 2-shift/3-shift, 5-day/7-day |
| Operators per line | 2-6 (depends on automation level) |
| Skill levels | 1 (basic) — 5 (specialist) |
| Cross-training coverage target | Each line operable by ≥3 operators |
| Overtime premium | 1.5x — 2.0x |
| Max overtime per week | 10-20 hours |
| Absenteeism rate | 3-8% |
| Training time for new skill | 2-8 weeks |

### 3.10 Module 10: Raw Material Management

**Scenario:** Track raw material availability, shelf life, and substitution options.

**Parameters:**
| Material Type | Lead Time | Shelf Life | # Approved Suppliers |
|---------------|-----------|------------|---------------------|
| Sugar/sweeteners | 1-4 weeks | 12-24 months | 2-5 |
| Cocoa | 4-12 weeks | 6-12 months | 2-4 |
| Milk/dairy | 1-3 days | 2-7 days (fresh) | 1-3 (local) |
| Packaging film | 2-6 weeks | 12-24 months | 2-4 |
| PET preforms | 2-4 weeks | Indefinite | 2-5 |
| Flavoring/additives | 2-8 weeks | 6-24 months | 1-3 |
| Meat/protein | 1-5 days | 3-7 days (fresh) | 2-5 |

### 3.11 Module 11: Regulatory Compliance

**Scenario:** Ensure production scheduling respects food safety requirements.

**Requirements:**
- **HACCP:** Critical Control Points monitored at defined frequencies; deviation triggers hold/rework
- **GMP:** Equipment cleaning validation, batch traceability, personnel hygiene protocols
- **FSSC 22000:** Certified management system with audit trail
- **Allergen management:** Sequencing rules (non-allergen → allergen), validated CIP between allergen groups, dedicated lines where volume justifies
- **Traceability:** 1-up/1-down minimum; Nestlé requires full chain traceability
- **Environmental:** Water discharge limits, air emissions, waste disposal compliance

**Scheduling Constraints from Regulatory:**
| Constraint | Impact on Schedule |
|------------|-------------------|
| Allergen sequencing | Forces production order (non-allergen first) |
| CIP validation | Minimum 45-180 min between certain product groups |
| Batch record completion | 15-30 min per batch for QA sign-off |
| Metal detection verification | Every 30-60 min during production |
| Environmental testing (Listeria, Salmonella) | Hold product 24-48 hrs for results (dairy/meat) |

### 3.12 Module 12: Capacity Planning & Bottleneck Analysis

**Scenario:** Identify bottlenecks, plan capacity expansion, model what-if scenarios.

**Approach:** Theory of Constraints (TOC) applied to production lines.

**Parameters:**
| Metric | Range |
|--------|-------|
| Line utilization target | 80-90% (above 90% = fragile) |
| Bottleneck identification | Lowest throughput station on line |
| Buffer sizing | 5-30 min of throughput between stations |
| Capacity expansion lead time | 6-18 months (new line installation) |
| Capacity expansion cost | $2M — $50M per line |

---

## 4. OEE Benchmarks (Simulation Targets)

### By Plant Type in Simulated Network

| Plant | Category | Starting OEE | Target OEE | Key Loss Driver |
|-------|----------|-------------|------------|-----------------|
| PLT-001 | Water/Beverages | 62% | 80% | Micro-stops, speed loss |
| PLT-002 | Confectionery | 55% | 78% | Changeovers, wrapping jams |
| PLT-003 | Dairy | 48% | 72% | CIP downtime, short runs |
| PLT-004 | Pet Food | 60% | 78% | Extrusion wear, coating variability |
| PLT-005 | Prepared Foods | 52% | 72% | Multi-component assembly, freezer bottleneck |

### OEE Component Breakdown

| Component | Poor | Average | Good | World-Class |
|-----------|------|---------|------|-------------|
| Availability | 65-75% | 75-83% | 83-88% | 88-92% |
| Performance | 60-75% | 75-85% | 85-92% | 92-97% |
| Quality | 90-95% | 95-97% | 97-99% | 99-99.9% |

---

## 5. Technical Architecture

### 5.1 ISA-95 Alignment

| ISA-95 Level | NexusFab Component | Function |
|-------------|-------------------|----------|
| Level 4 | Planning Engine | Demand planning, S&OP, MPS |
| Level 3 | Optimization Engine | Production scheduling, line allocation, maintenance planning |
| Level 3 | Simulation Engine | Discrete event simulation, what-if scenarios |
| Level 2 | Data Ingestion Layer | Real-time OEE data, sensor feeds (simulated) |
| Level 1-0 | Simulated Plant Floor | Virtual PLCs, sensors, actuators |

### 5.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend API | Python (FastAPI) | Rapid development, rich optimization libraries |
| Optimization | OR-Tools / PuLP / SciPy | Production-grade solvers |
| Simulation | SimPy | Discrete event simulation, Python-native |
| Database | PostgreSQL | Relational data (plants, lines, SKUs, orders) |
| Time-series | TimescaleDB (PostgreSQL extension) | OEE metrics, sensor data |
| Frontend | React + TypeScript | Dashboard, real-time visualization |
| Charts | Recharts / D3.js | OEE gauges, Gantt charts, network maps |
| API Docs | OpenAPI (auto-generated) | FastAPI built-in |

### 5.3 Data Model (Core Entities)

```
Plant
  ├── ProductionLine[]
  │     ├── Equipment[]
  │     │     ├── SparePart[]
  │     │     ├── MaintenanceSchedule[]
  │     │     └── SensorReading[] (simulated)
  │     ├── Capability[] (product types this line can produce)
  │     └── OEERecord[]
  ├── Warehouse
  │     ├── RawMaterialInventory[]
  │     ├── FinishedGoodsInventory[]
  │     └── SparePartsInventory[]
  ├── Workforce[]
  │     ├── Skill[]
  │     └── ShiftAssignment[]
  └── RegulatoryLicense[]

Product
  ├── BillOfMaterials[]
  ├── Recipe / ProcessSpec
  ├── AllergenProfile
  ├── ShelfLife
  └── QualitySpec[]

Order
  ├── Customer
  ├── SKU + Quantity
  ├── DueDate
  ├── Priority
  └── SLATerms

ProductionSchedule
  ├── PlannedRun[]
  │     ├── Line assignment
  │     ├── SKU
  │     ├── BatchSize
  │     ├── StartTime / EndTime
  │     └── ChangeoverBefore
  └── Status (draft / confirmed / in-progress / completed)
```

---

## 6. Simulation Engine

### 6.1 Discrete Event Simulation (SimPy-based)

The simulation models each production line as a resource with:
- **Capacity:** Rated speed (units/min)
- **Availability:** Random failures (Weibull distribution, parameterized by MTBF)
- **Repair:** MTTR (lognormal distribution)
- **Changeovers:** Sequence-dependent setup times
- **CIP:** Scheduled cleaning based on product transitions
- **Quality:** Random defect generation (binomial distribution)
- **Demand:** Stochastic order arrival (Poisson process with seasonal modulation)

### 6.2 Seeded Scenarios

| Scenario ID | Description | Trigger | Expected Outcome |
|------------|-------------|---------|-----------------|
| SIM-001 | Bottling line PLT-001-L3 filler failure | MTBF event at t=100hrs | Reroute to PLT-001-L5 (same format) |
| SIM-002 | KitKat moulding line down during holiday peak | Equipment failure + high demand | Cross-plant rerouting to PLT-002-L8 |
| SIM-003 | Dairy CIP overrun blocking next batch | CIP takes 2x expected time | Schedule reoptimization, downstream delay |
| SIM-004 | Spare part stockout (filler seal) | Inventory hits zero, lead time 5 days | Emergency procurement + temporary line shutdown |
| SIM-005 | Demand spike: 3x normal (promotional event) | External demand signal | Multi-plant load balancing |
| SIM-006 | Raw material shortage (cocoa) | Supplier delay 4 weeks | Recipe substitution or production postponement |
| SIM-007 | Allergen cross-contamination risk | Wrong sequencing detected | Emergency CIP, schedule correction |
| SIM-008 | Energy price spike (2x peak rate) | External tariff signal | Shift energy-intensive ops to off-peak |
| SIM-009 | Workforce shortage (flu season, 15% absent) | Absenteeism event | Cross-training deployment, overtime activation |
| SIM-010 | Quality excursion: fill weight drift | Sensor detection | Line slowdown, recalibration, rework assessment |

### 6.3 Simulation Clock

- **Time step:** 1 minute (production events) / 1 hour (planning events)
- **Simulation horizon:** 1-52 weeks
- **Warm-up period:** 2 weeks (reach steady state before measuring)
- **Replications:** 30+ runs per scenario (statistical significance)

---

## 7. Phased Implementation

### Phase 1: Foundation (Weeks 1-3)
- Project scaffolding (Python project, DB schema, API skeleton)
- Core data model (Plants, Lines, Equipment, Products, SKUs)
- Seed data generator (Nestlé-modeled 5-plant network)
- Basic SimPy simulation engine (single line, failures, repairs)
- OEE calculator

### Phase 2: Production Optimization (Weeks 4-6)
- Production scheduling engine (demand → schedule)
- Changeover optimizer (sequence optimization)
- Line failure rerouting algorithm
- Multi-line, single-plant simulation
- Dashboard: Gantt chart, OEE gauges

### Phase 3: Maintenance & Spare Parts (Weeks 7-8)
- Preventive maintenance scheduler
- Spare parts inventory model
- MTBF-based reorder point calculation
- Maintenance cost tracking

### Phase 4: Multi-Plant & Supply Chain (Weeks 9-10)
- Multi-plant network model
- Inter-plant rerouting optimizer
- Transport cost calculator
- Demand planning with seasonality
- Multi-plant dashboard

### Phase 5: Workforce & Compliance (Weeks 11-12)
- Workforce scheduling engine
- Skill matrix and cross-training model
- Regulatory constraint enforcement (allergen sequencing, CIP rules)
- Quality tracking module

### Phase 6: Energy & Advanced Analytics (Weeks 13-14)
- Energy optimization module
- Raw material management
- What-if scenario builder (UI)
- Reporting and analytics dashboard
- Simulation scenario library (all 10 seeded scenarios)

---

## 8. Key Performance Indicators (Tracked by NexusFab)

| KPI | Formula | Target |
|-----|---------|--------|
| OEE | Availability × Performance × Quality | ≥ 75% |
| Schedule Adherence | Actual vs Planned production | ≥ 92% |
| OTIF | Orders delivered on-time and in-full | ≥ 95% |
| Unplanned Downtime | Unplanned stops / Total scheduled time | ≤ 5% |
| Changeover Efficiency | Actual vs Target changeover time | ≤ 110% of target |
| Spare Parts Availability | Parts available when needed / Total needs | ≥ 97% |
| First Pass Yield | Good units / Total units (first attempt) | ≥ 96% |
| Energy per Unit | kWh / ton of product | Trend: decreasing |
| Maintenance Cost Ratio | Maintenance spend / RAV | ≤ 4% |
| Waste % | Waste weight / Total input weight | ≤ 3% |

---

## 9. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| Simulation speed | 1 week simulated in < 30 seconds |
| API response time | < 500ms for dashboard queries |
| Concurrent users | 10+ (multi-plant coordinators) |
| Data retention | 2 years of simulation history |
| Export formats | CSV, JSON, PDF reports |
| Authentication | JWT-based (future: SSO) |
| Deployment | Docker Compose (local), extensible to K8s |

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **OEE** | Overall Equipment Effectiveness = Availability × Performance × Quality |
| **MTBF** | Mean Time Between Failures |
| **MTTR** | Mean Time To Repair |
| **CIP** | Clean-in-Place (automated cleaning cycle) |
| **SMED** | Single-Minute Exchange of Die (changeover reduction methodology) |
| **HACCP** | Hazard Analysis and Critical Control Points |
| **GMP** | Good Manufacturing Practice |
| **FSSC 22000** | Food Safety System Certification |
| **NCE** | Nestlé Continuous Excellence |
| **TOC** | Theory of Constraints |
| **ISA-95** | International standard for manufacturing system integration |
| **SKU** | Stock Keeping Unit |
| **OTIF** | On-Time In-Full (delivery metric) |
| **S&OP** | Sales & Operations Planning |
| **MPS** | Master Production Schedule |
| **RAV** | Replacement Asset Value |
| **TPM** | Total Productive Maintenance |
