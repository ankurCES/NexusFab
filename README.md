# NexusFab — Manufacturing Operations Optimizer

Real-time digital twin for multi-plant manufacturing operations. Combines **SimPy** discrete-event simulation, **OR-Tools / PuLP** optimization, **scikit-learn** predictive maintenance, and a **React** dashboard — all launchable with a single script.

Built as a Nestlé-scale reference architecture: 5 plants, 22 production lines, 85+ equipment assets, full product catalog with allergen matrices and changeover costs.

## What It Does

| Module | Engine | What you get |
|--------|--------|-------------|
| **OEE Monitoring** | SimPy DES with Weibull failures | Plant/line OEE, availability, performance, quality metrics |
| **Predictive Maintenance** | IsolationForest + Weibull RUL | Equipment health matrix, RUL timeline, alert levels (GREEN→RED) |
| **Production Sequencing** | OR-Tools CP-SAT | Changeover-minimized schedules with allergen/CIP constraints |
| **Network Optimization** | PuLP CBC MILP | Multi-plant allocation, transport flow optimization, rerouting |
| **Demand Planning** | Time-series decomposition | SKU-level forecasts, capacity gap analysis |
| **Workforce Scheduling** | Constraint solver | Shift coverage, skill-gap analysis, regulatory compliance |
| **Energy & Sustainability** | Tariff-aware optimizer | Load shifting, CO₂ tracking, savings opportunities |
| **Food Safety (HACCP)** | Rule engine | CCP monitoring, allergen segregation, CIP scheduling |
| **Spare Parts** | ABC-XYZ + EOQ | Inventory classification, reorder points, stockout risk |
| **Sensor Streaming** | SSE + synthetic data | Live sensor gauges, sparklines, anomaly detection |
| **What-If Scenarios** | Parameterized simulation | Equipment failure, demand spike, energy price scenarios |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React + Vite + Tailwind CSS (port 5173)                │
│  11 pages: Dashboard, Maintenance, Network, Compliance, │
│  Sequencing, Sensors, Workforce, Energy, Scenarios,     │
│  Analytics, Plant Detail                                │
└──────────────────────┬──────────────────────────────────┘
                       │ /api proxy
┌──────────────────────▼──────────────────────────────────┐
│  FastAPI + Uvicorn (port 8000)                          │
│  33 endpoints across 13 routers                         │
│  Health probes: /health/live, /health/ready, /metrics   │
├─────────────────────────────────────────────────────────┤
│  Simulation        │ Optimization      │ ML / PdM       │
│  SimPy DES engine  │ OR-Tools CP-SAT   │ IsolationForest│
│  Weibull failures  │ PuLP CBC MILP     │ Weibull RUL    │
│  CIP scheduling    │ Demand planning   │ Z-score norm   │
│  Sensor streams    │ Workforce solver  │ Feature eng    │
├─────────────────────────────────────────────────────────┤
│  Seed Data (in-memory)                                  │
│  5 plants · 22 lines · 85+ equipment · 25 products      │
│  Runs without a database (simulation-only mode)         │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL 16 (optional, via Docker)                   │
│  Alembic migrations · Adminer UI on :8080               │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Docker** (for PostgreSQL — optional, app runs in simulation-only mode without it)
- **uv** (recommended) or pip

### One-command launch (with Docker)

```bash
git clone https://github.com/ankurCES/NexusFab.git
cd NexusFab
./run.sh
```

`run.sh` handles everything: Docker DB, migrations, seed data, API server, sensor simulator, and frontend dev server. Open **http://localhost:5173** when it's ready.

**Flags:**
```
--api-only    Skip frontend (API on :8000 only)
--no-seed     Skip database seeding
--prod        Run uvicorn with 4 workers (no hot reload)
--reset       Wipe Docker volumes and start fresh
```

### Manual setup (no Docker, simulation-only)

```bash
# 1. Clone
git clone https://github.com/ankurCES/NexusFab.git
cd NexusFab

# 2. Python environment
uv venv && source .venv/bin/activate
uv sync

# 3. Environment file
cp .env.example .env

# 4. Start API server
PYTHONPATH=. uvicorn nexusfab.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. All data comes from in-memory seed — no database required.

### With pip (instead of uv)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## API Endpoints

All endpoints are prefixed with `/api`. Interactive docs at **http://localhost:8000/docs**.

| Group | Endpoints |
|-------|-----------|
| Health | `GET /health/live` · `/health/ready` · `/health/detailed` · `/health/errors` · `/metrics` |
| OEE | `GET /oee/plant/{id}` · `/oee/{plant}/{line}` · `/metrics/dashboard` · `/metrics/downtime-pareto/{id}` |
| Plants | `GET /plants` · `/plants/{id}/lines` |
| Maintenance | `GET /maintenance/schedule/{id}` · `/maintenance/predictions/{id}` · `/maintenance/history/{id}` |
| Spares | `GET /spares/status/{id}` · `/spares/alerts` · `/spares/pooling` · `/spares/{id}` |
| Production | `GET /production/schedule/{id}` · `/production/kpis/{id}` · `POST /production/optimize-sequence` |
| Compliance | `GET /compliance/{id}/ccps` · `/compliance/{id}/allergens` · `/compliance/{id}/cip-schedule` · `/compliance/{id}/score` |
| Network | `GET /network/status` · `/network/flows` · `/network/allocation` · `POST /network/balance` · `/network/optimize` |
| Sensors | `GET /sensors/{plant}/{line}/equipment` · `/sensors/{plant}/{line}/{equip}` · `/sensors/{equip}/history` · SSE `/sensors/stream/{plant}/{line}` |
| Demand | `GET /network/demand/{id}` |
| Workforce | `GET /workforce` · `/workforce/{id}` |
| Energy | `GET /energy` · `/energy/{id}` · `POST /energy/optimize` |
| Scenarios | `GET /scenarios` · `POST /scenarios/run` · `/scenarios/custom` |
| Simulation | `POST /simulate` |

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

20 test modules covering simulation, optimization, predictive maintenance, spare parts, energy, compliance, and network allocation.

## Project Structure

```
NexusFab/
├── nexusfab/
│   ├── api/                  # FastAPI routers + Pydantic schemas
│   │   ├── routers/          # 13 endpoint modules
│   │   └── schemas/          # Request/response models
│   ├── models/               # SQLAlchemy ORM models
│   ├── optimization/         # OR-Tools, PuLP, scikit-learn solvers
│   │   ├── scheduling.py     # CP-SAT production sequencing
│   │   ├── network.py        # MILP network allocation
│   │   ├── predictive_maintenance.py  # IsolationForest + Weibull
│   │   ├── spare_parts.py    # ABC-XYZ inventory optimization
│   │   └── ...
│   ├── seed/                 # In-memory plant/product/history data
│   ├── services/             # OEE calculation service
│   └── simulation/           # SimPy DES engine
│       ├── line_model.py     # Production line simulator
│       ├── runner.py         # Plant/line orchestrator
│       ├── sensor_stream.py  # SSE sensor data generator
│       └── scenarios.py      # What-if scenario engine
├── frontend/                 # React + Vite + Tailwind
│   └── src/pages/            # 11 dashboard pages
├── tests/                    # 20 test modules
├── alembic/                  # Database migrations
├── docker-compose.yml        # PostgreSQL + Adminer
├── run.sh                    # Single-script launcher
└── pyproject.toml            # Python project config
```

## Seed Data

The simulation runs on realistic manufacturing data modeled after global FMCG operations:

| Plant | Location | Category | Lines |
|-------|----------|----------|-------|
| PLT-001 | Vevey, Switzerland | Dairy | 5 lines |
| PLT-002 | Arlington, USA | Pet Food | 4 lines |
| PLT-003 | York, UK | Confectionery | 5 lines |
| PLT-004 | Dongguan, China | Beverages | 4 lines |
| PLT-005 | Araras, Brazil | Dairy | 4 lines |

Each plant has full equipment trees with Weibull failure parameters, sensor configurations, product catalogs with allergen profiles, and changeover cost matrices.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic |
| Simulation | SimPy 4.1 (DES), Weibull failure models |
| Optimization | OR-Tools (CP-SAT), PuLP (CBC MILP) |
| ML | scikit-learn (IsolationForest), NumPy |
| Frontend | React 19, Vite, Tailwind CSS 4, Recharts 3 |
| Database | PostgreSQL 16 (optional), Alembic migrations |
| Infrastructure | Docker Compose, uv package manager |

## License

MIT
