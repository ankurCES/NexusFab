import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase
from nexusfab.models.enums import DowntimeType


class Product(UUIDBase):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    plant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), index=True)
    units_per_batch: Mapped[int] = mapped_column(Integer)
    changeover_minutes: Mapped[float] = mapped_column(Float)
    allergens: Mapped[list | None] = mapped_column(JSONB, nullable=True)


class ProductionRun(UUIDBase):
    __tablename__ = "production_runs"
    __table_args__ = (
        Index("ix_production_runs_line_start", "line_id", "start_time"),
    )

    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_lines.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_qty: Mapped[int] = mapped_column(Integer)
    actual_qty: Mapped[int] = mapped_column(Integer, default=0)
    good_qty: Mapped[int] = mapped_column(Integer, default=0)


class DowntimeEvent(UUIDBase):
    __tablename__ = "downtime_events"

    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_lines.id"), index=True)
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("equipment.id"), nullable=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    downtime_type: Mapped[DowntimeType] = mapped_column(Enum(DowntimeType))
    root_cause: Mapped[str | None] = mapped_column(String(200), nullable=True)


class OEERecord(UUIDBase):
    __tablename__ = "oee_records"
    __table_args__ = (
        Index("ix_oee_records_line_timestamp", "line_id", "timestamp"),
    )

    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_lines.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    availability: Mapped[float] = mapped_column(Float)
    performance: Mapped[float] = mapped_column(Float)
    quality: Mapped[float] = mapped_column(Float)
    oee: Mapped[float] = mapped_column(Float)
    shift: Mapped[int] = mapped_column(Integer)
