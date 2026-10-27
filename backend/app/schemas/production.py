from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, model_validator
from app.models.production import PlanStatus
from app.schemas.item import ItemSummary


class ProductionPlanBase(BaseModel):
    item_id: int
    planned_qty: Decimal
    unit: str = "EA"
    period_start: date
    period_end: date
    notes: str | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be >= period_start")
        return self


class ProductionPlanCreate(ProductionPlanBase):
    plan_no: str | None = None


class ProductionPlanUpdate(BaseModel):
    planned_qty: Decimal | None = None
    unit: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = None


class ProductionPlanOut(ProductionPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plan_no: str
    status: PlanStatus
    item: ItemSummary
    actual_qty_sum: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime


class ProductionPlanListOut(BaseModel):
    items: list[ProductionPlanOut]
    total: int
    page: int
    page_size: int


class ActualOutputBase(BaseModel):
    item_id: int
    output_date: date
    actual_qty: Decimal
    unit: str = "EA"
    good_qty: Decimal = Decimal("0")
    scrap_qty: Decimal = Decimal("0")
    production_plan_id: int | None = None
    line_id: str | None = None
    shift: str | None = None
    operator: str | None = None
    notes: str | None = None


class ActualOutputCreate(ActualOutputBase):
    output_no: str | None = None


class ActualOutputUpdate(BaseModel):
    actual_qty: Decimal | None = None
    good_qty: Decimal | None = None
    scrap_qty: Decimal | None = None
    line_id: str | None = None
    shift: str | None = None
    operator: str | None = None
    notes: str | None = None


class ActualOutputOut(ActualOutputBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    output_no: str
    is_voided: bool
    item: ItemSummary
    created_at: datetime


class ActualOutputListOut(BaseModel):
    items: list[ActualOutputOut]
    total: int
    page: int
    page_size: int
