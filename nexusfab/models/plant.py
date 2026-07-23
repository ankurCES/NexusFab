import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nexusfab.models.base import UUIDBase
from nexusfab.models.enums import EquipmentType, LineStatus, PlantCategory


class Plant(UUIDBase):
    __tablename__ = "plants"

    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(100))
    category: Mapped[PlantCategory] = mapped_column(Enum(PlantCategory))
    capacity_tons_per_day: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="active")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    lines: Mapped[list["ProductionLine"]] = relationship(back_populates="plant")


class ProductionLine(UUIDBase):
    __tablename__ = "production_lines"

    plant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    line_type: Mapped[str] = mapped_column(String(50))
    speed_units_per_min: Mapped[float] = mapped_column(Float)
    status: Mapped[LineStatus] = mapped_column(Enum(LineStatus), default=LineStatus.IDLE)

    plant: Mapped["Plant"] = relationship(back_populates="lines")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="line")


class Equipment(UUIDBase):
    __tablename__ = "equipment"

    line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("production_lines.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    equipment_type: Mapped[EquipmentType] = mapped_column(Enum(EquipmentType))
    mtbf_hours: Mapped[float] = mapped_column(Float)
    mttr_hours: Mapped[float] = mapped_column(Float)
    position_in_line: Mapped[int] = mapped_column(Integer)

    line: Mapped["ProductionLine"] = relationship(back_populates="equipment")
