import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nexusfab.database import get_session
from nexusfab.models.plant import Plant
from nexusfab.api.schemas.plants import PlantDetail, PlantSummary

router = APIRouter(prefix="/plants", tags=["Plants"])


@router.get("/", response_model=list[PlantSummary], summary="List all manufacturing plants")
async def list_plants(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Plant).options(selectinload(Plant.lines)).order_by(Plant.name)
    )
    plants = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "location": p.location,
            "category": p.category.value,
            "capacity_tons_per_day": p.capacity_tons_per_day,
            "status": p.status,
            "line_count": len(p.lines),
        }
        for p in plants
    ]


@router.get("/{plant_id}", response_model=PlantDetail, summary="Get plant detail with production lines")
async def get_plant(plant_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Plant).options(selectinload(Plant.lines)).where(Plant.id == plant_id)
    )
    plant = result.scalar_one_or_none()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return {
        "id": str(plant.id),
        "name": plant.name,
        "location": plant.location,
        "category": plant.category.value,
        "capacity_tons_per_day": plant.capacity_tons_per_day,
        "status": plant.status,
        "lines": [
            {
                "id": str(line.id),
                "name": line.name,
                "line_type": line.line_type,
                "speed_units_per_min": line.speed_units_per_min,
                "status": line.status.value,
            }
            for line in plant.lines
        ],
    }
