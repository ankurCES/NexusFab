<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/-NexusFab-0d1117?style=for-the-badge&labelColor=0d1117">
    <source media="(prefers-color-scheme: light)" srcset="https://img.shields.io/badge/-NexusFab-ffffff?style=for-the-badge&labelColor=ffffff">
    <img alt="" src="" width="1" height="1">
  </picture>
</p>

<div align="center">

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗███████╗ █████╗ ██████╗  │
  │    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔════╝██╔══██╗██╔══██╗ │
  │    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗█████╗  ███████║██████╔╝ │
  │    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██╔══╝  ██╔══██║██╔══██╗ │
  │    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║██║     ██║  ██║██████╔╝ │
  │    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═╝╚═════╝  │
  │                                                                     │
  │             Manufacturing Operations Optimizer                      │
  │                                                                     │
  │    Real-time digital twin · Discrete-event simulation               │
  │    OR-Tools optimization · Predictive maintenance · React UI        │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
```

**A full-stack digital twin for multi-plant manufacturing operations.**<br>
**SimPy simulation × OR-Tools optimization × ML predictive maintenance × React dashboard**

</div>

---

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 19"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS 4"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL 16"></a>
  <br>
  <a href="https://github.com/google/or-tools"><img src="https://img.shields.io/badge/OR--Tools-9.11-4285F4?style=flat-square&logo=google&logoColor=white" alt="OR-Tools"></a>
  <a href="https://simpy.readthedocs.io/"><img src="https://img.shields.io/badge/SimPy-4.1-green?style=flat-square" alt="SimPy"></a>
  <a href="https://scikit-learn.org/"><img src="https://img.shields.io/badge/scikit--learn-1.5-F7931E?style=flat-square&logo=scikitlearn&logoColor=white" alt="scikit-learn"></a>
  <a href="https://github.com/ankurCES/NexusFab"><img src="https://img.shields.io/github/last-commit/ankurCES/NexusFab?style=flat-square&color=blue" alt="Last Commit"></a>
  <a href="https://github.com/ankurCES/NexusFab"><img src="https://img.shields.io/github/repo-size/ankurCES/NexusFab?style=flat-square&color=purple" alt="Repo Size"></a>
  <a href="https://github.com/ankurCES/NexusFab"><img src="https://img.shields.io/badge/version-0.1.0-orange?style=flat-square" alt="Version 0.1.0"></a>
</p>

---

## ✨ Features

| Domain | Capability | Engine |
|--------|-----------|--------|
| 🏭 **Production Scheduling** | Changeover-aware line sequencing, allergen constraints, CIP scheduling | OR-Tools CP-SAT |
| 🔧 **Predictive Maintenance** | Weibull failure modeling, sensor anomaly detection, spare parts optimization | scikit-learn + SimPy |
| ⚡ **Energy Optimization** | Scenario modeling for energy costs, sustainability tracking | PuLP / OR-Tools |
| 👷 **Workforce Planning** | Shift optimization, regulatory compliance, skill-based allocation | OR-Tools |
| 🌐 **Network Optimization** | Multi-plant demand allocation, transport routing, lead-time modeling | OR-Tools |
| 📊 **Digital Twin** | Discrete-event simulation of production lines with real-time sensor streams | SimPy |
| 📈 **Analytics Dashboard** | OEE gauges, Gantt charts, plant maps, scenario comparison | React + Recharts |
| 🛡️ **Compliance** | Regulatory constraint tracking, allergen cross-contact prevention | Domain rules engine |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/ankurCES/NexusFab.git
cd NexusFab

# One-command launch (Docker)
docker compose up -d --build

# Or use the launcher script (auto-copies .env, starts DB + API + frontend)
chmod +x run.sh && ./run.sh
```

The API is at **http://localhost:8000** · Dashboard at **http://localhost:5173** · Adminer (DB UI) at **http://localhost:8080**

---

## 📦 Installation

### Prerequisites
- **Python 3.12+** · **Node.js 20+** · **PostgreSQL 16** (or Docker)

### Backend
```bash
# Install dependencies (using uv — or pip install -e .[dev])
uv sync

# Copy environment config
cp .env.example .env          # edit DB credentials if needed

# Run database migrations
alembic upgrade head

# Seed demo data (5 plants, production lines, 30-day history)
make seed

# Start API server
make dev                      # → http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # → http://localhost:5173
```

### Docker (all-in-one)
```bash
docker compose up -d --build  # API + PostgreSQL + Adminer
```

---

## 🔌 API Endpoints

| Route | Description |
|-------|-------------|
| `GET /health` | Health check |
| `GET /plants` | List all plants and lines |
| `GET /metrics/oee` | OEE calculations |
| `POST /optimization/schedule` | Production scheduling |
| `POST /optimization/sequence` | Line sequencing with changeovers |
| `GET /maintenance/predictions` | Predictive maintenance alerts |
| `GET /sensors/stream` | Real-time sensor data |
| `POST /simulation/run` | Run SimPy simulation scenarios |
| `POST /demand/plan` | Demand planning optimization |
| `GET /network/allocation` | Multi-plant network optimization |
| `GET /workforce/schedule` | Workforce shift optimization |
| `GET /energy/scenarios` | Energy scenario modeling |
| `GET /compliance/status` | Regulatory compliance dashboard |
| `GET /spares/inventory` | Spare parts optimization |

Full interactive docs at **http://localhost:8000/docs** (Swagger UI).

---

## 🗂️ Project Structure

```
NexusFab/
├── nexusfab/                  # Python backend (74 modules)
│   ├── api/                   # FastAPI application
│   │   ├── main.py            # App factory + CORS + lifespan
│   │   ├── routers/           # 12 route modules (production, maintenance, sensors…)
│   │   └── schemas/           # Pydantic request/response models
│   ├── models/                # SQLAlchemy ORM (plant, product, downtime, workforce…)
│   ├── optimization/          # OR-Tools / PuLP solvers
│   │   ├── scheduling.py      # CP-SAT production scheduler
│   │   ├── sequencing.py      # Changeover-aware line sequencing
│   │   ├── predictive_maintenance.py  # Weibull + ML failure prediction
│   │   ├── network.py         # Multi-plant demand allocation
│   │   ├── workforce.py       # Shift optimization
│   │   └── energy.py          # Energy cost scenarios
│   ├── simulation/            # SimPy discrete-event engine
│   │   ├── runner.py          # Simulation orchestrator
│   │   ├── sensor_stream.py   # Synthetic sensor data generator
│   │   └── workforce_sim.py   # Workforce simulation
│   ├── services/              # Business logic (OEE calculator)
│   ├── seed/                  # Demo data generators
│   ├── config.py              # Pydantic Settings
│   └── database.py            # Async SQLAlchemy engine
├── frontend/                  # React 19 + TypeScript + Tailwind 4
│   └── src/
│       ├── pages/             # 11 pages (Dashboard, Maintenance, Sensors…)
│       └── components/        # GanttChart, OEEGauge, PlantMap…
├── alembic/                   # Database migrations
├── tests/                     # 21 pytest modules
├── docker-compose.yml         # API + PostgreSQL 16 + Adminer
├── Makefile                   # dev, test, docker-up, seed
└── pyproject.toml             # Project metadata + dependencies
```

---

## ⚙️ Configuration

All config via environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://nexusfab:nexusfab@localhost:5432/nexusfab` | Async DB connection |
| `SYNC_DATABASE_URL` | *(derived)* | Alembic migrations |
| `API_PORT` | `8000` | API server port |
| `SENSOR_SEED` | `42` | Reproducible simulation runs |
| `POSTGRES_USER` | `nexusfab` | Docker Compose DB user |
| `POSTGRES_PASSWORD` | `nexusfab` | Docker Compose DB password |

---

## 🧪 Testing

```bash
# Run full suite (21 test modules)
make test

# With coverage
pytest --cov=nexusfab -v
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Ensure `make test` and `ruff check .` pass
5. Submit a pull request

**Code style:** Ruff with Python 3.12 target, 99-char line length.

---

## 📄 License

This project is currently unlicensed. Contact the maintainer for usage terms.

---

<p align="center">
  <b>Built with</b><br>
  <a href="https://fastapi.tiangolo.com/">FastAPI</a> ·
  <a href="https://simpy.readthedocs.io/">SimPy</a> ·
  <a href="https://github.com/google/or-tools">OR-Tools</a> ·
  <a href="https://react.dev/">React</a> ·
  <a href="https://www.postgresql.org/">PostgreSQL</a>
</p>
