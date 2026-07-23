import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase


class OEERecord(UUIDBase):
    __tablename__ = "oee_records"
    __table_args__ = (
        Index("ix_oee_records_line_shift", "line_id", "shift_date", "shift_number"),
    )

    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("production_lines.id"))
    shift_date: Mapped[date] = mapped_column(Date)
    shift_number: Mapped[int] = mapped_column(Integer)
    availability: Mapped[float] = mapped_column(Float)
    performance: Mapped[float] = mapped_column(Float)
    quality: Mapped[float] = mapped_column(Float)
    oee: Mapped[float] = mapped_column(Float)
    six_big_losses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
