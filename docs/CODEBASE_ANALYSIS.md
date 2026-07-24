# NexusFab — Codebase Analysis Summary

> Generated for use by downstream agents (README rewrite, wiki pages, badges, hero banner).

---

## 1. Project Purpose

**NexusFab** is a real-time digital-twin platform for multi-plant manufacturing operations optimization. It simulates a Nestlé-scale factory network (5 plants, 22 production lines, 85+ equipment assets, 25 products) and provides:

- **OEE Monitoring** — SimPy discrete-event simulation with Weibull failure models
- **Predictive Maintenance** — IsolationForest anomaly detection + Weibull remaining-useful-life
- **Production Sequencing** — OR-Tools CP-SAT constraint solver with allergen/CIP/changeover constraints
- **Network Optimization** — PuLP CBC MILP for multi-plant allocation and transport flow
- **Demand Planning** — Time-series decomposition with SKU-level forecasts
- **Workforce Scheduling** — Constraint solver for shift coverage and regulatory compliance
- **Energy & Sustainability** — Tariff-aware load shifting, CO₂ tracking
- **Food Safety (HACCP)** — CCP monitoring, allergen segregation, CIP scheduling
- **Spare Parts** — ABC-XYZ classification + EOQ reorder optimization
- **Sensor Streaming** — SSE with synthetic data, live gauges, anomaly detection
- **What-If Scenarios** — Parameterized simulation (equipment failure, demand spike, energy price)

Core problem: when a production line goes down, NexusFab answers cascading decisions about rerouting, logistics, maintenance impact, and demand fulfillment in real-time.

---

## 2. Tech Stack (with versions)

### Backend (Python)
| Technology | Version | Role |
|---|---|---|
| Python | 3.12+ | Runtime |
| FastAPI | ≥0.115 | REST API framework |
| Uvicorn | ≥0.32 (standard extras) | ASGI server |
| SQLAlchemy | ≥2.0 (asyncio) | ORM / database layer |
| asyncpg | ≥0.30 | PostgreSQL async driver |
| Alembic | ≥1.14 | Database migrations |
| SimPy | ≥4.1 | Discrete-event simulation engine |
| OR-Tools | ≥9.11 | CP-SAT constraint programming solver |
| PuLP | ≥2.9 | CBC MILP linear programming |
| scikit-learn | ≥1.5 | IsolationForest predictive maintenance |
| NumPy | ≥1.26 | Numerical computation |
| Pydantic Settings | ≥2.7 | Configuration management |
| httpx | ≥0.28 | HTTP client |
| python-dotenv | ≥1.0 | Environment variable loading |

### Frontend (TypeScript/React)
| Technology | Version | Role |
|---|---|---|
| React | 19.2.7 | UI framework |
| React Router DOM | 7.18.1 | Client-side routing |
| Recharts | 3.10.0 | Data visualization / charting |
| Vite | 8.1.1 | Build tool / dev server |
| Tailwind CSS | 4.3.3 (via @tailwindcss/vite) | Utility-first CSS |
| TypeScript | ~6.0.2 | Type-safe JavaScript |
| OxLint | 1.71.0 | Linter |
| Playwright | 1.61.1 | E2E testing (listed as dep) |

### Infrastructure
| Technology | Version | Role |
|---|---|---|
| PostgreSQL | 16 (Alpine) | Relational database (optional — app runs simulation-only without it) |
| Docker Compose | v2 | Container orchestration |
| Adminer | latest | Database admin UI (port 8080) |
| uv | latest | Python package manager (preferred) |
| Hatchling | latest | Python build backend |

### Dev Tools
| Tool | Version | Role |
|---|---|---|
| pytest | ≥8.0 | Test runner |
| pytest-asyncio | ≥0.24 | Async test support |
| pytest-cov | ≥6.0 | Coverage reporting |
| Ruff | ≥0.8 | Linter + formatter (target: py312, line-length: 99) |

---

## 3. Project Structure

```
NexusFab/
├── nexusfab/                      # Python backend (74 .py files, ~10,363 LOC)
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point, lifespan, CORS, error handling
│   ├── config.py                  # Pydantic Settings (DATABASE_URL, API_PORT)
│   ├── database.py                # SQLAlchemy async engine + session factory
│   ├── api/
│   │   ├── main.py                # Re-export for Dockerfile back-compat
│   │   ├── router.py              # Central router — mounts 13 sub-routers
│   │   ├── health.py              # Health probes: /health/live, /ready, /detailed, /errors, /metrics
│   │   ├── deps.py                # Dependency injection
│   │   ├── plants.py              # Plant listing endpoints
│   │   ├── routers/               # 12 domain routers
│   │   │   ├── compliance.py      # HACCP/CCP/allergen/CIP endpoints
│   │   │   ├── demand.py          # Demand planning & forecasting
│   │   │   ├── energy_scenarios.py# Energy optimization & sustainability
│   │   │   ├── maintenance.py     # Predictive maintenance endpoints
│   │   │   ├── metrics.py         # OEE & dashboard metrics
│   │   │   ├── network.py         # Network optimization & allocation
│   │   │   ├── optimization.py    # General optimization endpoints
│   │   │   ├── production.py      # Production scheduling & KPIs
│   │   │   ├── sensors.py         # SSE sensor streaming
│   │   │   ├── simulation.py      # Simulation control
│   │   │   ├── spares.py          # Spare parts inventory
│   │   │   └── workforce.py       # Workforce scheduling
│   │   └── schemas/               # 14 Pydantic response schemas
│   │       ├── compliance.py, demand.py, energy.py, health.py,
│   │       │   maintenance.py, metrics.py, network.py, optimization.py,
│   │       │   plants.py, production.py, sensors.py, simulation.py,
│   │       │   spares.py, workforce.py
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── base.py                # Declarative base
│   │   ├── plant.py, product.py, production.py, workforce.py
│   │   ├── oee.py, downtime.py, maintenance.py
│   │   └── enums.py               # Shared enumerations
│   ├── optimization/              # Solver modules (11 files)
│   │   ├── sequencing.py          # OR-Tools CP-SAT production sequencing
│   │   ├── scheduling.py          # Scheduling optimizer
│   │   ├── network.py             # PuLP MILP network optimization
│   │   ├── rerouting.py           # Production rerouting logic
│   │   ├── predictive_maintenance.py  # IsolationForest + Weibull RUL
│   │   ├── maintenance.py         # Maintenance planning
│   │   ├── demand.py              # Demand planning / forecasting
│   │   ├── workforce.py           # Workforce constraint solver
│   │   ├── spare_parts.py         # ABC-XYZ + EOQ optimization
│   │   ├── energy.py              # Energy / sustainability optimizer
│   │   └── regulatory.py          # Regulatory compliance checks
│   ├── simulation/                # SimPy simulation engine (7 files)
│   │   ├── runner.py              # Simulation orchestrator
│   │   ├── line_model.py          # Production line DES model
│   │   ├── failure_generator.py   # Weibull failure generation
│   │   ├── failure_signatures.py  # Failure pattern definitions
│   │   ├── sensor_stream.py       # SSE synthetic sensor data
│   │   ├── scenarios.py           # What-if scenario engine
│   │   └── workforce_sim.py       # Workforce simulation
│   ├── seed/                      # In-memory seed data (no DB required)
│   │   ├── plants.py              # 5 plants, 22 lines, 85+ equipment
│   │   ├── products.py            # 25 products with allergen matrices
│   │   └── history.py             # Historical data generation
│   └── services/
│       └── oee.py                 # OEE calculation service
│
├── frontend/                      # React SPA (24 source files)
│   ├── src/
│   │   ├── App.tsx                # Router — 11 routes
│   │   ├── main.tsx               # React DOM entry
│   │   ├── index.css              # Global styles (Tailwind)
│   │   ├── api/
│   │   │   └── client.ts          # API client / fetch wrapper
│   │   ├── components/            # Reusable UI components
│   │   │   ├── Layout.tsx         # App shell / navigation
│   │   │   ├── OEEGauge.tsx       # OEE radial gauge
│   │   │   ├── PlantMap.tsx       # Plant network visualization
│   │   │   ├── GanttChart.tsx     # Production schedule Gantt
│   │   │   └── LineStatusCard.tsx # Line status indicator
│   │   ├── pages/                 # 11 page components
│   │   │   ├── Dashboard.tsx, PlantDetail.tsx, Maintenance.tsx,
│   │   │   │   Network.tsx, Workforce.tsx, Energy.tsx, Scenarios.tsx,
│   │   │   │   Analytics.tsx, Compliance.tsx, Sequencing.tsx, Sensors.tsx
│   │   ├── types/
│   │   │   └── api.ts             # TypeScript API type definitions
│   │   └── assets/
│   │       └── hero.png           # Hero image asset
│   ├── package.json
│   ├── vite.config.ts             # Vite config with /api proxy to :8000
│   ├── tsconfig.json, tsconfig.app.json, tsconfig.node.json
│   └── dist/                      # Production build output
│
├── tests/                         # 20 pytest test files
│   ├── test_allergens.py, test_allocation.py, test_ccps.py,
│   │   test_changeover.py, test_cip_schedules.py, test_demand.py,
│   │   test_energy_full.py, test_energy_scenarios.py, test_failure_gen.py,
│   │   test_lead_times.py, test_line_speeds.py, test_network.py,
│   │   test_pdm.py, test_sensor_stream.py, test_sequencing.py,
│   │   test_spare_parts.py, test_transport.py, test_weibull.py,
│   │   test_workforce.py, test_workforce_regulatory.py
│
├── alembic/                       # Database migration framework
│   ├── env.py, script.py.mako
│   └── versions/                  # Migration scripts
│
├── docs/
│   ├── REQUIREMENTS.md            # Detailed requirements document (v1.0)
│   └── research/                  # Domain research files (5 markdown docs)
│       ├── energy-workforce-simulation.md
│       ├── maintenance-spare-parts.md
│       ├── nestle-compliance.md
│       ├── production-operations.md
│       └── supply-chain-demand.md
│
├── Dockerfile                     # Python 3.12-slim + uv
├── docker-compose.yml             # api + postgres:16 + adminer
├── Makefile                       # dev, test, docker-up/down, seed targets
├── run.sh                         # One-command launcher (flags: --api-only, --no-seed, --prod, --reset)
├── pyproject.toml                 # Project metadata + deps (hatchling build)
├── uv.lock                        # Lockfile (uv package manager)
├── alembic.ini                    # Alembic configuration
├── .env.example                   # Environment template
├── .gitignore                     # Standard Python + Node ignores
└── README.md                      # Current documentation (comprehensive but needs polish)
```

---

## 4. Architecture Summary

```
Frontend (React 19 + Vite + Tailwind)  →  /api proxy  →  FastAPI (Uvicorn :8000)
                                                              │
                                          ┌───────────────────┼───────────────────┐
                                          │                   │                   │
                                    Simulation          Optimization           ML/PdM
                                    (SimPy DES)         (OR-Tools CP-SAT)     (IsolationForest)
                                    Weibull failures    (PuLP CBC MILP)       Weibull RUL
                                    Sensor SSE          Demand planning       Z-score
                                    CIP scheduling      Workforce solver      Feature eng
                                          │                   │                   │
                                          └───────────────────┼───────────────────┘
                                                              │
                                                    Seed Data (in-memory)
                                                    5 plants · 22 lines · 85+ equipment
                                                              │
                                                    PostgreSQL 16 (optional)
                                                    Alembic migrations
```

- **33 API endpoints** across 13 routers
- **Health probes**: `/health/live`, `/health/ready`, `/health/detailed`, `/health/errors`, `/metrics`
- **Graceful DB fallback**: runs entirely from in-memory seed data when PostgreSQL is unavailable
- **SSE streaming**: real-time sensor data push to frontend

---

## 5. Key Metrics

| Metric | Value |
|---|---|
| Backend Python files | 74 |
| Backend LOC (approx) | ~10,363 |
| Frontend source files | 24 |
| Frontend pages | 11 |
| Frontend components | 5 reusable |
| API routers | 13 |
| API endpoints | 33+ |
| Pydantic schemas | 14 |
| Optimization modules | 11 |
| Simulation modules | 7 |
| ORM models | 9 |
| Test files | 20 |
| Seed data | 5 plants, 22 lines, 85+ equipment, 25 products |
| Research docs | 5 |

---

## 6. Build & Run

| Method | Command |
|---|---|
| **One-command (Docker)** | `./run.sh` |
| **API only** | `./run.sh --api-only` |
| **Production mode** | `./run.sh --prod` (4 uvicorn workers) |
| **Reset** | `./run.sh --reset` (wipes Docker volumes) |
| **Manual API** | `PYTHONPATH=. uvicorn nexusfab.main:app --host 0.0.0.0 --port 8000 --reload` |
| **Manual frontend** | `cd frontend && npm install && npm run dev` |
| **Tests** | `pytest -v` or `make test` |
| **Docker Compose** | `docker compose up -d --build` or `make docker-up` |
| **Seed DB** | `python -m nexusfab.seed` or `make seed` |
| **Lint** | Ruff (backend), OxLint (frontend) |

---

## 7. License

**MIT** (stated in README, no separate LICENSE file found in repo root).

---

## 8. CI/CD

No CI/CD pipeline files found (no `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`). The project is set up for local Docker Compose deployment.

---

## 9. Badge-Relevant Facts

| Badge Area | Value |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| Frontend | React 19 |
| Build | Vite 8 |
| CSS | Tailwind CSS 4 |
| Database | PostgreSQL 16 |
| Package Manager | uv (Python), npm (JS) |
| Linter | Ruff (Python), OxLint (JS) |
| Tests | pytest |
| Container | Docker |
| License | MIT |
| Simulation | SimPy 4 |
| Optimization | OR-Tools, PuLP |
| ML | scikit-learn |

---

## 10. Existing Assets

- `frontend/src/assets/hero.png` — existing hero image
- `docs/REQUIREMENTS.md` — 10-section requirements document (~5,000 words)
- `docs/research/` — 5 domain research markdown files
- `README.md` — comprehensive but could benefit from badges, hero banner, and wiki structure
