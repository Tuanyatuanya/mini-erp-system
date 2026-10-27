from decimal import Decimal
from pydantic import BaseModel


class KPIOut(BaseModel):
    total_active_items: int
    total_plans_this_month: int
    total_outputs_this_month: int
    plan_achievement_rate: Decimal
    total_inventory_value: Decimal
    low_stock_items: int


class PlanVsActualRow(BaseModel):
    plan_no: str
    item_code: str
    item_name: str
    planned_qty: Decimal
    actual_qty: Decimal
    variance: Decimal
    achievement_pct: Decimal
    period_start: str
    period_end: str
    status: str


class PlanVsActualOut(BaseModel):
    rows: list[PlanVsActualRow]
    total_planned: Decimal
    total_actual: Decimal
    overall_achievement_pct: Decimal


class RecentMovementRow(BaseModel):
    movement_no: str
    item_code: str
    item_name: str
    movement_type: str
    qty: Decimal
    unit: str
    movement_date: str
