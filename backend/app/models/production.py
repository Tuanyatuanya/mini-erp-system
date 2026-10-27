from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, Numeric, Text, DateTime, Date,
    ForeignKey, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PlanStatus(str, PyEnum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    CLOSED = "CLOSED"


class ProductionPlan(Base):
    __tablename__ = "production_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PlanStatus, name="plan_status_enum"), nullable=False, default=PlanStatus.DRAFT
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    item: Mapped["Item"] = relationship(back_populates="production_plans")
    actual_outputs: Mapped[list["ActualOutput"]] = relationship(back_populates="production_plan")


class ActualOutput(Base):
    __tablename__ = "actual_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    output_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    production_plan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("production_plans.id")
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    output_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    good_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    scrap_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    line_id: Mapped[str | None] = mapped_column(String(50))
    shift: Mapped[str | None] = mapped_column(String(20))
    operator: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    is_voided: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    production_plan: Mapped[ProductionPlan | None] = relationship(back_populates="actual_outputs")
    item: Mapped["Item"] = relationship(back_populates="actual_outputs")


from app.models.item import Item  # noqa: E402
