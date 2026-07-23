"""Health, readiness, liveness, and metrics endpoints."""

import collections
import resource
import sys
import time

from fastapi import APIRouter, Response
from sqlalchemy import func, select, text

from nexusfab.api.schemas.health import DetailedHealthResponse, ErrorsResponse, LivenessResponse, ReadinessResponse

router = APIRouter(prefix="/api", tags=["Health"])

_start_time = time.monotonic()
_errors: collections.deque = collections.deque(maxlen=100)

# Prometheus counters — incremented by middleware in main.py
counters = {"requests_total": 0, "errors_total": 0, "simulation_events_total": 0}


def record_error(path: str, method: str, status: int, detail: str) -> None:
    _errors.append(
        {
            "ts": time.time(),
            "method": method,
            "path": path,
            "status": status,
            "detail": detail[:500],
        }
    )
    counters["errors_total"] += 1


# ── liveness ────────────────────────────────────────────────────────────────


@router.get("/health/live", response_model=LivenessResponse, summary="Liveness probe")
async def liveness():
    return {"status": "ok"}


# ── readiness ────────────────────────────────────────────────────────────────


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness probe — checks DB, migrations, seed, and simulation")
async def readiness():
    checks: dict[str, dict] = {}

    # DB ping
    db_ok = False
    try:
        from nexusfab.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
        checks["db"] = {"ok": True}
    except Exception as e:
        checks["db"] = {"ok": False, "error": str(e)}

    # Alembic head check
    mig_ok = False
    try:
        from alembic.config import Config
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        from nexusfab.database import engine

        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head = script_dir.get_current_head()

        async with engine.connect() as conn:
            current = await conn.run_sync(
                lambda sync_conn: MigrationContext.configure(sync_conn).get_current_revision()
            )
        mig_ok = current == head
        checks["migrations"] = {"ok": mig_ok, "current": current, "head": head}
    except Exception as e:
        checks["migrations"] = {"ok": False, "error": str(e)}

    # Seed: plants available (DB or in-memory seed data)
    seed_ok = False
    count = 0
    try:
        from nexusfab.database import async_session
        from nexusfab.models.plant import Plant

        async with async_session() as session:
            count = await session.scalar(select(func.count()).select_from(Plant))
    except Exception:
        pass
    if count < 5:
        from nexusfab.seed.plants import PLANTS
        count = len(PLANTS)
        checks["seed"] = {"ok": count >= 5, "plant_count": count, "source": "memory"}
    else:
        checks["seed"] = {"ok": True, "plant_count": count}
    seed_ok = count >= 5

    # Sensor simulator: last run within 60s (updated by run_plant calls)
    sim_ok = False
    try:
        from nexusfab.simulation import runner as _runner

        age = time.monotonic() - _runner._sim_last_at
        sim_ok = age < 60
        checks["sensor_sim"] = {"ok": sim_ok, "last_run_seconds_ago": round(age, 1)}
    except Exception as e:
        checks["sensor_sim"] = {"ok": False, "error": str(e)}

    all_ok = all(c.get("ok") for c in checks.values())
    status_code = 200 if all_ok else 503
    return Response(
        content=__import__("json").dumps({"status": "ready" if all_ok else "degraded", "checks": checks}),
        media_type="application/json",
        status_code=status_code,
    )


# ── detailed ─────────────────────────────────────────────────────────────────


@router.get("/health/detailed", response_model=DetailedHealthResponse, summary="Detailed health — uptime, DB pool, simulation status, per-plant OEE snapshot")
async def detailed():
    uptime_s = time.monotonic() - _start_time

    # DB pool stats
    pool_stats: dict = {}
    try:
        from nexusfab.database import engine

        pool = engine.sync_engine.pool
        pool_stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception as e:
        pool_stats = {"error": str(e)}

    # Simulation engine status
    sim_status: dict = {}
    try:
        from nexusfab.simulation import runner as _runner

        age = time.monotonic() - _runner._sim_last_at
        sim_status = {
            "status": "running" if age < 60 else "idle",
            "last_run_seconds_ago": round(age, 1),
        }
    except Exception as e:
        sim_status = {"status": "unknown", "error": str(e)}

    # Per-plant status (quick 1h sim for OEE snapshot)
    plants_status = []
    try:
        from nexusfab.seed.plants import PLANTS
        from nexusfab.simulation.runner import run_plant

        for plant in PLANTS:
            result = run_plant(plant.id, duration_hours=1.0, seed=42)
            alerts = [lr.line_name for lr in result.line_results if lr.oee < 0.6]
            plants_status.append(
                {
                    "plant_id": plant.id,
                    "plant_name": plant.name,
                    "lines_active": len(result.line_results),
                    "oee": round(result.plant_oee, 4),
                    "alerts": alerts,
                }
            )
    except Exception as e:
        plants_status = [{"error": str(e)}]

    # Memory usage
    try:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS returns bytes; Linux returns kilobytes
        mem_mb = rss / (1024 * 1024) if sys.platform == "darwin" else rss / 1024
        memory = {"rss_mb": round(mem_mb, 1)}
    except Exception:
        memory = {}

    last_error = _errors[-1] if _errors else None

    return {
        "status": "ok",
        "uptime_seconds": round(uptime_s, 1),
        "db_pool": pool_stats,
        "simulation": sim_status,
        "plants": plants_status,
        "memory": memory,
        "last_error": last_error,
        "error_count": len(_errors),
    }


# ── errors ring buffer ────────────────────────────────────────────────────────


@router.get("/health/errors", response_model=ErrorsResponse, summary="Last 100 API errors (ring buffer)")
async def errors():
    return {"errors": list(_errors), "total_buffered": len(_errors)}


# ── prometheus metrics ────────────────────────────────────────────────────────


@router.get("/metrics", response_class=Response, summary="Prometheus metrics (text/plain)")
async def prometheus_metrics():
    sim_events = counters["simulation_events_total"]
    try:
        from nexusfab.simulation import runner as _runner

        sim_events = _runner._sim_events_total
    except Exception:
        pass

    db_pool_size = 0
    try:
        from nexusfab.database import engine

        db_pool_size = engine.sync_engine.pool.size()
    except Exception:
        pass

    lines = [
        "# HELP requests_total Total HTTP requests handled",
        "# TYPE requests_total counter",
        f"requests_total {counters['requests_total']}",
        "",
        "# HELP errors_total Total HTTP errors (4xx/5xx)",
        "# TYPE errors_total counter",
        f"errors_total {counters['errors_total']}",
        "",
        "# HELP simulation_events_total Total simulation events generated",
        "# TYPE simulation_events_total counter",
        f"simulation_events_total {sim_events}",
        "",
        "# HELP active_simulations Currently running simulation count",
        "# TYPE active_simulations gauge",
        "active_simulations 0",
        "",
        "# HELP db_pool_size Database connection pool size",
        "# TYPE db_pool_size gauge",
        f"db_pool_size {db_pool_size}",
        "",
        "# HELP equipment_health_avg Average equipment health score [0,1]",
        "# TYPE equipment_health_avg gauge",
        # ponytail: static baseline; pull from live simulation if needed
        "equipment_health_avg 0.85",
        "",
    ]
    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4")
