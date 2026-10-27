from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, Numeric, Boolean, Text, DateTime,
    ForeignKey, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ItemType(str, PyEnum):
    PRODUCT = "PRODUCT"
    MATERIAL = "MATERIAL"
    WIP = "WIP"


class ItemCategory(Base):
    __tablename__ = "item_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("item_categories.id"))
    item_type: Mapped[str] = mapped_column(
        Enum(ItemType, name="item_type_enum"), nullable=False, default=ItemType.MATERIAL
    )
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    description: Mapped[str | None] = mapped_column(Text)
    standard_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[ItemCategory | None] = relationship(back_populates="items")
    bom_headers: Mapped[list["BOMHeader"]] = relationship(
        back_populates="parent_item", foreign_keys="BOMHeader.parent_item_id"
    )
    production_plans: Mapped[list["ProductionPlan"]] = relationship(back_populates="item")
    actual_outputs: Mapped[list["ActualOutput"]] = relationship(back_populates="item")
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="item")
    inventory_balances: Mapped[list["InventoryBalance"]] = relationship(back_populates="item")


class BOMHeader(Base):
    __tablename__ = "bom_headers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    parent_item: Mapped[Item] = relationship(
        back_populates="bom_headers", foreign_keys=[parent_item_id]
    )
    lines: Mapped[list["BOMLine"]] = relationship(
        back_populates="bom_header", cascade="all, delete-orphan"
    )


class BOMLine(Base):
    __tablename__ = "bom_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_header_id: Mapped[int] = mapped_column(Integer, ForeignKey("bom_headers.id"), nullable=False)
    component_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    qty_per: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    scrap_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    bom_header: Mapped[BOMHeader] = relationship(back_populates="lines")
    component_item: Mapped[Item] = relationship(foreign_keys=[component_item_id])


# Avoid circular import
from app.models.production import ProductionPlan, ActualOutput  # noqa: E402
from app.models.inventory import InventoryMovement, InventoryBalance  # noqa: E402
