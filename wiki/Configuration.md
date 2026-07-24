# Configuration

[← Home](Home)

---

## Environment Variables

All configuration is managed through a `.env` file (auto-copied from `.env.example` by `run.sh`).

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://nexusfab:nexusfab@localhost:5432/nexusfab` | Async SQLAlchemy connection string (asyncpg driver) |
| `SYNC_DATABASE_URL` | *(derived from DATABASE_URL)* | Synchronous URL for Alembic migrations |
| `API_PORT` | `8000` | Port for the uvicorn API server |
| `POSTGRES_USER` | `nexusfab` | PostgreSQL user (must match `docker-compose.yml`) |
| `POSTGRES_PASSWORD` | `nexusfab` | PostgreSQL password |
| `POSTGRES_DB` | `nexusfab` | PostgreSQL database name |
| `SENSOR_SEED` | `42` | RNG seed for reproducible sensor simulation |

### Settings Class

Configuration is loaded via `pydantic-settings` in `nexusfab/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nexusfab:nexusfab@localhost:5432/nexusfab"
    api_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}
```

Any additional env vars in `.env` are silently ignored (`extra = "ignore"`).

---

## Docker Compose Services

Defined in `docker-compose.yml`:

| Service | Image | Exposed Port | Notes |
|---------|-------|--------------|-------|
| `api` | Built from `Dockerfile` | `${API_PORT:-8000}` | Depends on `db` health check |
| `db` | `postgres:16-alpine` | `5432` | Persistent volume `pgdata` |
| `adminer` | `adminer` | `8080` | Lightweight DB admin UI |

---

## Simulation Tuning

These constants live in source code (not env vars) but are key tuning knobs:

### Per-Category OEE Tuning (`nexusfab/simulation/runner.py`)

| Category | Micro-Stop Probability | Quality Rate |
|----------|----------------------|--------------|
| WATER | 0.04 | 0.97 |
| CONFECTIONERY | 0.06 | 0.96 |
| DAIRY | 0.07 | 0.95 |
| PET_FOOD | 0.04 | 0.97 |
| PREPARED_FOODS | 0.06 | 0.96 |

### Weibull Parameters (`nexusfab/seed/plants.py`)

| Equipment Type | β (shape) | η (scale, hours) |
|---------------|-----------|-------------------|
| FILLER | 2.2 | 1100 |
| MIXER | 2.0 | 3400 |
| CAPPER | 1.8 | 900 |
| LABELER | 1.5 | 590 |
| CONVEYOR | 1.0 | 1500 |
| PACKAGING | 1.8 | 870 |
| PASTEURIZER | 2.5 | 2200 |
| HOMOGENIZER | 2.0 | 1250 |
| DRYER | 3.0 | 615 |

### CIP Schedules (`nexusfab/seed/plants.py`)

Cleaning-in-Place schedules vary by line type. Frequency and duration ranges are defined in the `CIP_SCHEDULES` dictionary.

---

## Build & Dev Configuration

### Python (`pyproject.toml`)

| Setting | Value |
|---------|-------|
| Python target | ≥ 3.12 |
| Build backend | Hatchling |
| Linter | Ruff (line length 99, rules: E, F, I, N, UP, B, SIM) |
| Test runner | pytest with `asyncio_mode = "auto"` |

### Frontend (`frontend/package.json`)

Managed with npm. Key scripts: `dev` (Vite), `build`, `preview`.

---

## Makefile Targets

```makefile
make dev          # uvicorn --reload on port 8000
make test         # pytest -v
make docker-up    # docker compose up -d --build
make docker-down  # docker compose down
make seed         # python -m nexusfab.seed
```

---

See also: [Getting Started](Getting-Started) · [Architecture](Architecture)
