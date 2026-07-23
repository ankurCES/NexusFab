import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from nexusfab.models.base import UUIDBase


class Product(UUIDBase):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    plant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), index=True)
    units_per_batch: Mapped[int] = mapped_column(Integer)
    changeover_minutes: Mapped[float] = mapped_column(Float)
    allergens: Mapped[list | None] = mapped_column(JSONB, nullable=True)
