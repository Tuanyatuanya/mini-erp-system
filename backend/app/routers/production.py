from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.production import ProductionPlan, ActualOutput, PlanStatus
from app.models.inventory import MovementType
from app.schemas.production import (
    ProductionPlanCreate, ProductionPlanUpdate, ProductionPlanOut, ProductionPlanListOut,
    ActualOutputCreate, ActualOutputUpdate, ActualOutputOut, ActualOutputListOut,
)
from app.services.sequence import make_plan_no, make_output_no
from app.services.inventory_service import apply_movement
from app.services.excel_service import export_production_plans, export_actual_outputs

router = APIRouter(prefix="/api/production", tags=["production"])


# ─── Production Plans ─────────────────────────────────────────────────────────

@router.get("/plans/export")
async def export_plans_xlsx(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionPlan).options(selectinload(ProductionPlan.item))
    )
    plans = result.scalars().all()
    enriched = []
    for p in plans:
        d = ProductionPlanOut.model_validate(p).model_dump()
        actual = await db.scalar(
            select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
            .where(ActualOutput.production_plan_id == p.id, ActualOutput.is_voided == False)
        )
        d["actual_qty_sum"] = float(actual or 0)
        enriched.append(d)
    content = export_production_plans(enriched)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=production_plans.xlsx"},
    )


@router.get("/plans", response_model=ProductionPlanListOut)
async def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: PlanStatus | None = None,
    item_id: int | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(ProductionPlan).options(selectinload(ProductionPlan.item))
    if status:
        q = q.where(ProductionPlan.status == status)
    if item_id:
        q = q.where(ProductionPlan.item_id == item_id)
    if period_start:
        q = q.where(ProductionPlan.period_start >= period_start)
    if period_end:
        q = q.where(ProductionPlan.period_end <= period_end)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(
        q.order_by(ProductionPlan.period_start.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    plans = result.scalars().all()

    out_items = []
    for p in plans:
        actual_sum = await db.scalar(
            select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
            .where(ActualOutput.production_plan_id == p.id, ActualOutput.is_voided == False)
        )
        obj = ProductionPlanOut.model_validate(p)
        obj.actual_qty_sum = actual_sum or 0
        out_items.append(obj)

    return ProductionPlanListOut(items=out_items, total=total, page=page, page_size=page_size)


@router.post("/plans", response_model=ProductionPlanOut, status_code=201)
async def create_plan(data: ProductionPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = ProductionPlan(
        plan_no=data.plan_no or make_plan_no(),
        **data.model_dump(exclude={"plan_no"}),
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan, ["item"])
    obj = ProductionPlanOut.model_validate(plan)
    obj.actual_qty_sum = 0
    return obj


@router.get("/plans/{plan_id}", response_model=ProductionPlanOut)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionPlan)
        .options(selectinload(ProductionPlan.item))
        .where(ProductionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    actual_sum = await db.scalar(
        select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
        .where(ActualOutput.production_plan_id == plan_id, ActualOutput.is_voided == False)
    )
    obj = ProductionPlanOut.model_validate(plan)
    obj.actual_qty_sum = actual_sum or 0
    return obj


@router.put("/plans/{plan_id}", response_model=ProductionPlanOut)
async def update_plan(plan_id: int, data: ProductionPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionPlan).options(selectinload(ProductionPlan.item))
        .where(ProductionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.status == PlanStatus.CLOSED:
        raise HTTPException(400, "Cannot update a CLOSED plan")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(plan, k, v)
    await db.flush()
    actual_sum = await db.scalar(
        select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
        .where(ActualOutput.production_plan_id == plan_id, ActualOutput.is_voided == False)
    )
    obj = ProductionPlanOut.model_validate(plan)
    obj.actual_qty_sum = actual_sum or 0
    return obj


@router.patch("/plans/{plan_id}/release", response_model=ProductionPlanOut)
async def release_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionPlan).options(selectinload(ProductionPlan.item))
        .where(ProductionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.status != PlanStatus.DRAFT:
        raise HTTPException(400, f"Plan is {plan.status}, cannot release")
    plan.status = PlanStatus.RELEASED
    await db.flush()
    obj = ProductionPlanOut.model_validate(plan)
    obj.actual_qty_sum = 0
    return obj


@router.patch("/plans/{plan_id}/close", response_model=ProductionPlanOut)
async def close_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionPlan).options(selectinload(ProductionPlan.item))
        .where(ProductionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.status != PlanStatus.RELEASED:
        raise HTTPException(400, f"Plan is {plan.status}, cannot close")
    plan.status = PlanStatus.CLOSED
    await db.flush()
    actual_sum = await db.scalar(
        select(func.coalesce(func.sum(ActualOutput.actual_qty), 0))
        .where(ActualOutput.production_plan_id == plan_id, ActualOutput.is_voided == False)
    )
    obj = ProductionPlanOut.model_validate(plan)
    obj.actual_qty_sum = actual_sum or 0
    return obj


# ─── Actual Outputs ───────────────────────────────────────────────────────────

@router.get("/outputs/export")
async def export_outputs_xlsx(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActualOutput).options(selectinload(ActualOutput.item))
        .where(ActualOutput.is_voided == False)
    )
    outputs = result.scalars().all()
    data = [ActualOutputOut.model_validate(o).model_dump() for o in outputs]
    content = export_actual_outputs(data)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=actual_outputs.xlsx"},
    )


@router.get("/outputs", response_model=ActualOutputListOut)
async def list_outputs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    item_id: int | None = None,
    plan_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(ActualOutput).options(selectinload(ActualOutput.item)).where(ActualOutput.is_voided == False)
    if item_id:
        q = q.where(ActualOutput.item_id == item_id)
    if plan_id:
        q = q.where(ActualOutput.production_plan_id == plan_id)
    if date_from:
        q = q.where(ActualOutput.output_date >= date_from)
    if date_to:
        q = q.where(ActualOutput.output_date <= date_to)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(
        q.order_by(ActualOutput.output_date.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return ActualOutputListOut(items=result.scalars().all(), total=total, page=page, page_size=page_size)


@router.post("/outputs", response_model=ActualOutputOut, status_code=201)
async def create_output(data: ActualOutputCreate, db: AsyncSession = Depends(get_db)):
    output = ActualOutput(
        output_no=data.output_no or make_output_no(),
        **data.model_dump(exclude={"output_no"}),
    )
    db.add(output)
    await db.flush()

    # Auto-create inventory PRODUCTION_IN movement for finished goods
    await apply_movement(
        db=db,
        item_id=output.item_id,
        movement_type=MovementType.PRODUCTION_IN,
        qty=output.good_qty if output.good_qty > 0 else output.actual_qty,
        unit=output.unit,
        movement_date=output.output_date,
        reference_type="actual_output",
        reference_id=output.id,
        notes=f"From output {output.output_no}",
    )

    await db.refresh(output, ["item"])
    return output


@router.get("/outputs/{output_id}", response_model=ActualOutputOut)
async def get_output(output_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActualOutput).options(selectinload(ActualOutput.item))
        .where(ActualOutput.id == output_id)
    )
    output = result.scalar_one_or_none()
    if not output:
        raise HTTPException(404, "Output not found")
    return output


@router.put("/outputs/{output_id}", response_model=ActualOutputOut)
async def update_output(output_id: int, data: ActualOutputUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActualOutput).options(selectinload(ActualOutput.item))
        .where(ActualOutput.id == output_id)
    )
    output = result.scalar_one_or_none()
    if not output:
        raise HTTPException(404, "Output not found")
    if output.is_voided:
        raise HTTPException(400, "Cannot update a voided output")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(output, k, v)
    await db.flush()
    return output


@router.delete("/outputs/{output_id}", status_code=204)
async def void_output(output_id: int, db: AsyncSession = Depends(get_db)):
    output = await db.get(ActualOutput, output_id)
    if not output:
        raise HTTPException(404, "Output not found")
    output.is_voided = True
    # Reverse the inventory movement
    await apply_movement(
        db=db,
        item_id=output.item_id,
        movement_type=MovementType.ADJUSTMENT,
        qty=-(output.good_qty if output.good_qty > 0 else output.actual_qty),
        unit=output.unit,
        movement_date=output.output_date,
        reference_type="void_output",
        reference_id=output.id,
        notes=f"Void output {output.output_no}",
    )
    await db.flush()
