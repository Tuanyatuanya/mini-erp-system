from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.item import Item
from app.models.production import ProductionPlan, ActualOutput, PlanStatus
from app.models.inventory import InventoryMovement, InventoryBalance
from app.schemas.dashboard import KPIOut, PlanVsActualOut, PlanVsActualRow, RecentMovementRow

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=KPIOut)
async def get_kpis(db: AsyncSession = Depends(get_db)):
    today = date.today()
    month_start = today.replace(day=1)

    active_items = await db.scalar(select(func.count(Item.id)).where(Item.is_active == True))

    plans_this_month = await db.scalar(
        select(func.count(ProductionPlan.id))
        .where(ProductionPlan.period_start >= month_start)
    )

    outputs_this_month = await db.scalar(
        select(func.count(ActualOutput.id))
        .where(ActualOutput.output_date >= month_start, ActualOutput.is_voided == False)
    )

    # Achievement rate for released+closed plans this month
    planned_sum = await db.scalar(
        select(func.coalesce(func.sum(ProductionPlan.planned_qty), 0))
        .where(
            ProductionPlan.period_start >= month_start,
            ProductionPlan.status.in_([PlanStatus.RELEASED, PlanStatus.CLOSED]),
        )
    ) or Decimal("0")

    actual_sum = await db.scalar(
        select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
        .where(ActualOutput.output_date >= month_start, ActualOutput.is_voided == False)
    ) or Decimal("0")

    achievement = (actual_sum / planned_sum * 100).quantize(Decimal("0.01")) if planned_sum else Decimal("0")

    # Inventory value = qty_on_hand * standard_cost
    inv_value_result = await db.execute(
        select(func.coalesce(func.sum(InventoryBalance.qty_on_hand * Item.standard_cost), 0))
        .join(Item, InventoryBalance.item_id == Item.id)
    )
    inv_value = inv_value_result.scalar() or Decimal("0")

    # Low stock: qty_on_hand <= reorder_point
    low_stock = await db.scalar(
        select(func.count(InventoryBalance.id))
        .join(Item, InventoryBalance.item_id == Item.id)
        .where(InventoryBalance.qty_on_hand <= Item.reorder_point, Item.reorder_point > 0)
    )

    return KPIOut(
        total_active_items=active_items or 0,
        total_plans_this_month=plans_this_month or 0,
        total_outputs_this_month=outputs_this_month or 0,
        plan_achievement_rate=achievement,
        total_inventory_value=Decimal(str(inv_value)).quantize(Decimal("0.01")),
        low_stock_items=low_stock or 0,
    )


@router.get("/plan-vs-actual", response_model=PlanVsActualOut)
async def plan_vs_actual(
    period_start: str | None = None,
    period_end: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(ProductionPlan)
        .options(selectinload(ProductionPlan.item))
        .where(ProductionPlan.status.in_([PlanStatus.RELEASED, PlanStatus.CLOSED]))
    )
    if period_start:
        q = q.where(ProductionPlan.period_start >= period_start)
    if period_end:
        q = q.where(ProductionPlan.period_end <= period_end)

    result = await db.execute(q.order_by(ProductionPlan.period_start))
    plans = result.scalars().all()

    rows = []
    total_planned = Decimal("0")
    total_actual = Decimal("0")

    for plan in plans:
        actual = await db.scalar(
            select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
            .where(ActualOutput.production_plan_id == plan.id, ActualOutput.is_voided == False)
        ) or Decimal("0")
        planned = plan.planned_qty
        variance = actual - planned
        achievement = (actual / planned * 100).quantize(Decimal("0.01")) if planned else Decimal("0")
        total_planned += planned
        total_actual += actual
        rows.append(PlanVsActualRow(
            plan_no=plan.plan_no,
            item_code=plan.item.code,
            item_name=plan.item.name,
            planned_qty=planned,
            actual_qty=actual,
            variance=variance,
            achievement_pct=achievement,
            period_start=str(plan.period_start),
            period_end=str(plan.period_end),
            status=plan.status,
        ))

    overall = (total_actual / total_planned * 100).quantize(Decimal("0.01")) if total_planned else Decimal("0")
    return PlanVsActualOut(
        rows=rows, total_planned=total_planned,
        total_actual=total_actual, overall_achievement_pct=overall,
    )


@router.get("/recent-movements", response_model=list[RecentMovementRow])
async def recent_movements(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InventoryMovement)
        .options(selectinload(InventoryMovement.item))
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )
    return [
        RecentMovementRow(
            movement_no=m.movement_no,
            item_code=m.item.code,
            item_name=m.item.name,
            movement_type=m.movement_type,
            qty=m.qty,
            unit=m.unit,
            movement_date=str(m.movement_date),
        )
        for m in result.scalars().all()
    ]
