from fastapi import APIRouter

from nexusfab.api.health import router as health_router
from nexusfab.api.plants import router as plants_router
from nexusfab.api.routers.metrics import router as metrics_router
from nexusfab.api.routers.optimization import router as optimization_router
from nexusfab.api.routers.simulation import router as simulation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(plants_router)
api_router.include_router(simulation_router)
api_router.include_router(metrics_router)
api_router.include_router(optimization_router)
