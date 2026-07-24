# Architecture

[← Home](Home)

---

## High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                     React Dashboard (Vite)                  │
│              Recharts · Tailwind CSS 4 · React 19           │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Health   │  │   Routers    │  │     Schemas           │  │
│  │  Probes   │  │  (13 modules)│  │  (Pydantic models)    │  │
│  └──────────┘  └──────┬───────┘  └───────────────────────┘  │
│                        │                                     │
│  ┌─────────────────────▼─────────────────────────────────┐  │
│  │              Services (OEE calculation)                │  │
│  └───────────────────────────────────────────────────────┘  │
│                        │                                     │
│  ┌─────────────┬───────▼───────┬──────────────────────────┐ │
│  │ Simulation  │ Optimization  │        Seed Data          │ │
│  │  (SimPy)    │ (OR-Tools)    │  (5 plants, products)     │ │
│  └─────────────┴───────────────┴──────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ SQLAlchemy (asyncpg)
┌────────────────────────────▼────────────────────────────────┐
│              PostgreSQL 16 (Alembic migrations)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Map

### `nexusfab/` — Python Backend

| Module | Files | Purpose |
|--------|-------|---------|
| `main.py` | 1 | FastAPI app factory, CORS, error handling, lifespan |
| `config.py` | 1 | `pydantic-settings` — `DATABASE_URL`, `API_PORT` |
| `database.py` | 1 | AsyncEngine + session factory (SQLAlchemy) |
| `api/routers/` | 13 | REST endpoint modules (one per domain) |
| `api/schemas/` | 15 | Pydantic response models |
| `models/` | 8 | SQLAlchemy ORM models (Plant, Line, Equipment, OEE, etc.) |
| `simulation/` | 7 | SimPy discrete-event engine |
| `optimization/` | 11 | OR-Tools / PuLP solvers |
| `services/` | 1 | OEE calculation service |
| `seed/` | 3 | In-memory seed data (plants, products, history) |

### `frontend/` — React Dashboard

| Stack | Details |
|-------|---------|
| React 19 | SPA with component-based UI |
| Tailwind CSS 4 | Utility-first styling |
| Recharts | OEE gauges, trend charts, Pareto diagrams |
| Vite | Dev server + production build |

### `tests/` — 20 Test Modules

Covers allergens, allocation, CCPs, changeovers, CIP, demand, energy, failures, lead times, line speeds, network, predictive maintenance, sensors, sequencing, spare parts, transport, Weibull, workforce, and regulatory compliance.

---

## Simulation Engine (`nexusfab/simulation/`)

| File | Role |
|------|------|
| `line_model.py` | `ProductionLine` SimPy process — equipment failures, micro-stops, CIP, changeovers |
| `runner.py` | Orchestrates per-line / per-plant / network-wide simulation runs |
| `failure_generator.py` | Weibull-distributed failure event generation |
| `failure_signatures.py` | Failure mode signatures per equipment type |
| `sensor_stream.py` | Generates realistic sensor time-series (temperature, pressure, vibration, flow) |
| `scenarios.py` | 10 pre-built what-if scenarios (forced failures, demand spikes, CIP delays) |
| `workforce_sim.py` | Workforce availability overlay for simulation |

### Simulation Flow

1. `run_plant()` loads seed data for a plant.
2. For each production line, builds a `LineConfig` from seed + per-category tuning (micro-stop probability, quality rate, speed factor derived from equipment MTBF).
3. Creates a SimPy `Environment`, instantiates `ProductionLine`, runs for N minutes.
4. Collects `LineMetrics` — units produced, failures, downtime breakdown (mechanical / changeover / CIP).
5. Computes **OEE = Availability × Performance × Quality** per line; averages across lines for the plant OEE.

---

## Optimization Engine (`nexusfab/optimization/`)

| File | Solver | Problem |
|------|--------|---------|
| `scheduling.py` | OR-Tools CP-SAT | Production order scheduling with changeover awareness |
| `sequencing.py` | OR-Tools TSP/MILP | SKU sequencing to minimize changeover + allergen conflicts |
| `network.py` | OR-Tools MILP | Multi-plant demand allocation, load balancing, transport |
| `maintenance.py` | Heuristic | Maintenance grouping to minimize total downtime windows |
| `predictive_maintenance.py` | scikit-learn | ML failure prediction with remaining useful life (RUL) |
| `spare_parts.py` | ABC-XYZ + EOQ | Inventory classification, reorder points, cross-plant pooling |
| `demand.py` | Statistical | Demand forecasting with safety stock and service-level targeting |
| `energy.py` | PuLP | Energy schedule optimization — peak shaving, off-peak shifting |
| `workforce.py` | OR-Tools | Shift scheduling with skill-based allocation and regulatory rules |
| `regulatory.py` | Rule engine | Allergen sequencing, CIP class determination, compliance scoring |
| `rerouting.py` | Heuristic | Line-failure rerouting across the plant network |

---

## Data Model (`nexusfab/models/`)

| Model | Table | Key Fields |
|-------|-------|------------|
| `Plant` | `plants` | id, name, location, category, capacity |
| `ProductionLine` | `production_lines` | plant_id, name, line_type, rated_speed |
| `Equipment` | `equipment` | line_id, equipment_type, mtbf, mttr, Weibull β/η |
| `OEERecord` | `oee_records` | line_id, timestamp, availability, performance, quality |
| `DowntimeEvent` | `downtime_events` | equipment_id, start, end, cause |
| `MaintenanceTask` | `maintenance_tasks` | equipment_id, type, due_date, status |
| `Product` | `products` | sku, name, category, allergens, line_type |
| `WorkforceShift` | `workforce_shifts` | plant_id, shift, headcount, skills |

---

## Data Flow

```
Seed Data (in-memory)  ──→  Simulation Engine  ──→  API Routers  ──→  Frontend
         │                        │                       │
         └── PostgreSQL (ORM) ────┘                       │
                                                          ▼
                                              Swagger UI / React Dashboard
```

The system operates in **simulation-only mode** when PostgreSQL is unavailable — all seed data lives in memory, making the API fully functional without a database connection.

---

See also: [API Reference](API-Reference) · [Configuration](Configuration)
