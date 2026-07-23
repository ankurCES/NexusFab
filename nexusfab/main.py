import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nexusfab.api.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ponytail: DB init skipped — all endpoints use seed/simulation data, not SQL
    try:
        from nexusfab.database import engine
        from nexusfab.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")
    except Exception:
        logger.info("Database unavailable — running in simulation-only mode")
    yield


app = FastAPI(
    title="NexusFab Manufacturing Operations API",
    version="1.0.0",
    description=(
        "Real-time manufacturing intelligence platform for multi-plant operations. "
        "Covers OEE monitoring, predictive maintenance, production scheduling, "
        "food-safety compliance (HACCP/CCP/allergen), network optimization, "
        "demand planning, energy/sustainability tracking, and workforce scheduling."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.middleware("http")
async def _count_requests(request: Request, call_next):
    from nexusfab.api.health import counters

    counters["requests_total"] += 1
    response = await call_next(request)
    if response.status_code >= 400:
        from nexusfab.api.health import record_error

        record_error(
            path=request.url.path,
            method=request.method,
            status=response.status_code,
            detail="",
        )
    return response


@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception):
    import traceback

    from nexusfab.api.health import record_error

    detail = traceback.format_exception_only(type(exc), exc)[-1].strip()
    logger.error("Unhandled exception %s %s: %s", request.method, request.url.path, detail)
    record_error(
        path=request.url.path,
        method=request.method,
        status=500,
        detail=detail,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
