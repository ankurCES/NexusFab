"""OEE & metrics API endpoints."""

from fastapi import APIRouter, HTTPException

from nexusfab.api.schemas.metrics import DashboardResponse, DowntimeParetoResponse, LineListItem, OEEResult, PlantListItem, PlantOEE
from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.services.oee import oee_from_simulation
from nexusfab.simulation.runner import _line_config_from_seed, run_plant, run_single_line

router = APIRouter(prefix="/api", tags=["Production"])


@router.get("/oee/plant/{plant_id}", response_model=PlantOEE, summary="OEE summary for all lines in a plant")
async def get_plant_oee(plant_id: str, duration_hours: float = 168.0, seed: int = 42):
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")

    result = run_plant(plant_id, duration_hours, seed)
    return {
        "plant_id": plant_id,
        "plant_name": plant.name,
        "plant_oee": round(result.plant_oee, 4),
        "lines": result.to_dict()["lines"],
        "total_units": result.total_units,
        "total_failures": result.total_failures,
    }


@router.get("/metrics/dashboard", response_model=DashboardResponse, summary="Full dashboard — all plants summary with OEE, best/worst lines")
async def dashboard(duration_hours: float = 168.0, seed: int = 42):
    """Full dashboard payload — all plants summary."""
    plants_data = []
    for plant in PLANTS:
        result = run_plant(plant.id, duration_hours, seed)
        worst_line = min(result.line_results, key=lambda l: l.oee) if result.line_results else None
        best_line = max(result.line_results, key=lambda l: l.oee) if result.line_results else None

        plants_data.append({
            "plant_id": plant.id,
            "plant_name": plant.name,
            "category": plant.category,
            "location": plant.location,
            "oee": round(result.plant_oee, 4),
            "starting_oee": plant.starting_oee,
            "target_oee": plant.target_oee,
            "total_lines": len(plant.lines),
            "total_units": result.total_units,
            "total_failures": result.total_failures,
            "worst_line": worst_line.line_name if worst_line else None,
            "worst_oee": round(worst_line.oee, 4) if worst_line else None,
            "best_line": best_line.line_name if best_line else None,
            "best_oee": round(best_line.oee, 4) if best_line else None,
        })

    network_oee = sum(p["oee"] for p in plants_data) / len(plants_data) if plants_data else 0
    return {
        "network_oee": round(network_oee, 4),
        "plant_count": len(plants_data),
        "plants": plants_data,
    }


@router.get("/metrics/downtime-pareto/{plant_id}", response_model=DowntimeParetoResponse, summary="Downtime Pareto chart — top causes by minutes for a plant")
async def downtime_pareto(plant_id: str, duration_hours: float = 168.0, seed: int = 42):
    result = run_plant(plant_id, duration_hours, seed)
    pareto = []
    for lr in result.line_results:
        m = lr.metrics
        if m.downtime_mechanical > 0:
            pareto.append({"line": lr.line_name, "cause": "mechanical", "minutes": round(m.downtime_mechanical, 1)})
        if m.downtime_changeover > 0:
            pareto.append({"line": lr.line_name, "cause": "changeover", "minutes": round(m.downtime_changeover, 1)})
        if m.downtime_cip > 0:
            pareto.append({"line": lr.line_name, "cause": "cip", "minutes": round(m.downtime_cip, 1)})

    pareto.sort(key=lambda x: x["minutes"], reverse=True)
    return {"plant_id": plant_id, "pareto": pareto}


@router.get("/oee/{plant_id}/{line_name}", response_model=OEEResult, summary="OEE breakdown for a single production line")
async def get_line_oee(plant_id: str, line_name: str, duration_hours: float = 168.0, seed: int = 42):
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")

    line_seed = next((l for l in plant.lines if l.name == line_name), None)
    if not line_seed:
        raise HTTPException(404, f"Line {line_name} not found")

    cfg = _line_config_from_seed(line_seed, plant.category)
    lr = run_single_line(cfg, duration_hours, seed)
    oee_result = oee_from_simulation(lr.metrics, cfg)
    return oee_result.to_dict()


@router.get("/plants", response_model=list[PlantListItem], tags=["Plants"], summary="List all plants with geo-coordinates")
async def list_plants():
    return [
        {
            "id": p.id,
            "name": p.name,
            "location": p.location,
            "category": p.category,
            "capacity_tons_per_day": p.capacity_tons_per_day,
            "line_count": len(p.lines),
            "lat": p.lat,
            "lon": p.lon,
        }
        for p in PLANTS
    ]


@router.get("/plants/{plant_id}/lines", response_model=list[LineListItem], tags=["Plants"], summary="List production lines for a plant")
async def list_lines(plant_id: str):
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")
    return [
        {
            "name": l.name,
            "line_type": l.line_type,
            "speed_units_per_min": l.rated_speed_per_min,
            "equipment_count": len(l.equipment),
        }
        for l in plant.lines
    ]
