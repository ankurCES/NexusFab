import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase
from nexusfab.models.enums import DowntimeType


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
