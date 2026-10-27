from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inventory import InventoryBalance, InventoryMovement, MovementType
from app.services.sequence import make_movement_no


async def apply_movement(
    db: AsyncSession,
    item_id: int,
    movement_type: MovementType,
    qty: Decimal,
    unit: str,
    movement_date: date,
    location: str = "DEFAULT",
    reference_type: str | None = None,
    reference_id: int | None = None,
    notes: str | None = None,
    created_by: str | None = None,
) -> InventoryMovement:
    # Positive types increase stock; negative types decrease
    signed_qty = qty if movement_type in (
        MovementType.RECEIPT, MovementType.RETURN,
        MovementType.ADJUSTMENT, MovementType.PRODUCTION_IN
    ) else -qty

    movement = InventoryMovement(
        movement_no=make_movement_no(movement_type),
        item_id=item_id,
        movement_type=movement_type,
        movement_date=movement_date,
        qty=signed_qty,
        unit=unit,
        to_location=location if signed_qty > 0 else None,
        from_location=location if signed_qty < 0 else None,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)

    # Upsert balance
    result = await db.execute(
        select(InventoryBalance).where(
            InventoryBalance.item_id == item_id,
            InventoryBalance.location == location,
        )
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = InventoryBalance(item_id=item_id, location=location, qty_on_hand=Decimal("0"))
        db.add(balance)

    balance.qty_on_hand = (balance.qty_on_hand or Decimal("0")) + signed_qty
    await db.flush()
    return movement
