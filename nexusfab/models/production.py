import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase


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
