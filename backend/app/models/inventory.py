from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, Numeric, Text, DateTime, Date,
    ForeignKey, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class MovementType(str, PyEnum):
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"
    PRODUCTION_IN = "PRODUCTION_IN"
    PRODUCTION_OUT = "PRODUCTION_OUT"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movement_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(
        Enum(MovementType, name="movement_type_enum"), nullable=False
    )
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    from_location: Mapped[str | None] = mapped_column(String(100))
    to_location: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    item: Mapped["Item"] = relationship(back_populates="inventory_movements")


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="DEFAULT")
    qty_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    qty_reserved: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    item: Mapped["Item"] = relationship(back_populates="inventory_balances")


from app.models.item import Item  # noqa: E402
