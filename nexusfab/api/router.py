from fastapi import APIRouter

from nexusfab.api.health import router as health_router
from nexusfab.api.routers.demand import router as demand_router
from nexusfab.api.routers.compliance import router as compliance_router
from nexusfab.api.routers.energy_scenarios import router as energy_scenarios_router
from nexusfab.api.routers.production import router as production_router
from nexusfab.api.routers.sensors import router as sensors_router
from nexusfab.api.routers.maintenance import router as maintenance_router
from nexusfab.api.routers.metrics import router as metrics_router
from nexusfab.api.routers.network import router as network_router
from nexusfab.api.routers.optimization import router as optimization_router
from nexusfab.api.routers.simulation import router as simulation_router
from nexusfab.api.routers.spares import router as spares_router
from nexusfab.api.routers.workforce import router as workforce_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(demand_router)
api_router.include_router(simulation_router)
api_router.include_router(metrics_router)
api_router.include_router(optimization_router)
api_router.include_router(maintenance_router)
api_router.include_router(network_router)
api_router.include_router(workforce_router)
api_router.include_router(spares_router)
api_router.include_router(energy_scenarios_router)
api_router.include_router(compliance_router)
api_router.include_router(production_router)
api_router.include_router(sensors_router)
