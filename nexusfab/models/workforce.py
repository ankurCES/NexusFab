import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase


class Shift(UUIDBase):
    __tablename__ = "shifts"

    plant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    pattern: Mapped[str] = mapped_column(String(50))


class Operator(UUIDBase):
    __tablename__ = "operators"

    plant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    employee_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shifts.id"), nullable=True
    )


class SkillMatrix(UUIDBase):
    __tablename__ = "skill_matrix"

    operator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("operators.id"), index=True
    )
    line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("production_lines.id"), index=True
    )
    skill_level: Mapped[int] = mapped_column(Integer)
    certified_date: Mapped[date | None] = mapped_column(Date, nullable=True)
