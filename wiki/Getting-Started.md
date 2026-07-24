# Getting Started

[← Home](Home)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend, simulation, optimization |
| Node.js | 20+ | React frontend |
| Docker & Docker Compose | Latest | PostgreSQL, containerized deployment |
| uv *(optional)* | Latest | Fast Python dependency management |

---

## Installation

### 1. Clone & Environment

```bash
git clone https://github.com/ankurCES/NexusFab.git
cd NexusFab
cp .env.example .env        # edit DB credentials if needed
```

### 2. One-Command Launch (Recommended)

```bash
chmod +x run.sh && ./run.sh
```

`run.sh` performs pre-flight checks (Python version, Node version, port availability), starts PostgreSQL via Docker Compose, runs Alembic migrations, seeds demo data, launches the API server, sensor simulator, and Vite dev server.

**Flags:**

| Flag | Effect |
|------|--------|
| `--no-seed` | Skip demo data seeding |
| `--prod` | Run uvicorn with 4 workers instead of `--reload` |
| `--reset` | `docker compose down -v` before starting (wipes DB) |
| `--api-only` | Skip frontend; API + DB only |

### 3. Manual Setup (Alternative)

```bash
# Backend
uv sync                     # or: pip install -e .[dev]
docker compose up -d db     # start PostgreSQL
alembic upgrade head        # run migrations
make seed                   # seed 5 plants + 30-day history
make dev                    # uvicorn --reload on port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### 4. Docker-Only

```bash
docker compose up -d --build
```

Starts API (port 8000), PostgreSQL (5432), and Adminer (8080).

---

## Verify Installation

```bash
# API liveness
curl http://localhost:8000/api/health/live
# → {"status": "ok"}

# Full readiness (DB + migrations + seed + sensor sim)
curl http://localhost:8000/api/health/ready

# Run tests
make test
```

---

## Service Endpoints

| Service | URL |
|---------|-----|
| API (Swagger) | http://localhost:8000/docs |
| Dashboard | http://localhost:5173 |
| Adminer (DB UI) | http://localhost:8080 |
| Health probe | http://localhost:8000/api/health/live |
| Prometheus metrics | http://localhost:8000/api/metrics |

---

## First API Call

```bash
# Run a 1-week simulation for the water-bottling plant
curl -X POST http://localhost:8000/api/simulate/run \
  -H "Content-Type: application/json" \
  -d '{"plant_id": "PLT-001", "duration_hours": 168, "seed": 42}'
```

---

## Next Steps

- [Architecture](Architecture) — understand the module layout
- [API Reference](API-Reference) — explore all endpoints
- [Configuration](Configuration) — tune environment variables
