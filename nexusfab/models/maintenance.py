import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase
from nexusfab.models.enums import ABCClass, EquipmentType, MaintenanceType


class MaintenanceTask(UUIDBase):
    __tablename__ = "maintenance_tasks"
    __table_args__ = (
        Index("ix_maintenance_tasks_equip_date", "equipment_id", "scheduled_date"),
    )

    equipment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("equipment.id"))
    task_type: Mapped[MaintenanceType] = mapped_column(Enum(MaintenanceType))
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SparePart(UUIDBase):
    __tablename__ = "spare_parts"

    name: Mapped[str] = mapped_column(String(100))
    equipment_type: Mapped[EquipmentType] = mapped_column(Enum(EquipmentType))
    qty_on_hand: Mapped[int] = mapped_column(Integer)
    reorder_point: Mapped[int] = mapped_column(Integer)
    lead_time_days: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[float] = mapped_column(Float)
    abc_class: Mapped[ABCClass] = mapped_column(Enum(ABCClass))
