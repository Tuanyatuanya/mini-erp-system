from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.inventory import InventoryMovement, InventoryBalance, MovementType
from app.schemas.inventory import (
    InventoryMovementCreate, InventoryMovementOut, InventoryMovementListOut,
    InventoryBalanceOut,
)
from app.services.inventory_service import apply_movement
from app.services.excel_service import export_inventory_movements

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/movements/export")
async def export_movements_xlsx(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InventoryMovement).options(selectinload(InventoryMovement.item))
        .order_by(InventoryMovement.movement_date.desc())
    )
    movements = result.scalars().all()
    data = [InventoryMovementOut.model_validate(m).model_dump() for m in movements]
    content = export_inventory_movements(data)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_movements.xlsx"},
    )


@router.get("/movements", response_model=InventoryMovementListOut)
async def list_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    item_id: int | None = None,
    movement_type: MovementType | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(InventoryMovement).options(selectinload(InventoryMovement.item))
    if item_id:
        q = q.where(InventoryMovement.item_id == item_id)
    if movement_type:
        q = q.where(InventoryMovement.movement_type == movement_type)
    if date_from:
        q = q.where(InventoryMovement.movement_date >= date_from)
    if date_to:
        q = q.where(InventoryMovement.movement_date <= date_to)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(
        q.order_by(InventoryMovement.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return InventoryMovementListOut(
        items=result.scalars().all(), total=total, page=page, page_size=page_size
    )


@router.post("/movements", response_model=InventoryMovementOut, status_code=201)
async def create_movement(data: InventoryMovementCreate, db: AsyncSession = Depends(get_db)):
    from decimal import Decimal
    movement = await apply_movement(
        db=db,
        item_id=data.item_id,
        movement_type=data.movement_type,
        qty=abs(data.qty),
        unit=data.unit,
        movement_date=data.movement_date,
        location=data.to_location or data.from_location or "DEFAULT",
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        notes=data.notes,
    )
    await db.refresh(movement, ["item"])
    return movement


@router.get("/movements/{movement_id}", response_model=InventoryMovementOut)
async def get_movement(movement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InventoryMovement).options(selectinload(InventoryMovement.item))
        .where(InventoryMovement.id == movement_id)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Movement not found")
    return m


@router.get("/balances", response_model=list[InventoryBalanceOut])
async def list_balances(
    item_id: int | None = None,
    location: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(InventoryBalance).options(selectinload(InventoryBalance.item))
    if item_id:
        q = q.where(InventoryBalance.item_id == item_id)
    if location:
        q = q.where(InventoryBalance.location == location)
    result = await db.execute(q.order_by(InventoryBalance.item_id))
    balances = result.scalars().all()
    return [InventoryBalanceOut.from_orm_with_available(b) for b in balances]


@router.get("/balances/{item_id}", response_model=list[InventoryBalanceOut])
async def get_item_balances(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InventoryBalance).options(selectinload(InventoryBalance.item))
        .where(InventoryBalance.item_id == item_id)
    )
    balances = result.scalars().all()
    return [InventoryBalanceOut.from_orm_with_available(b) for b in balances]
