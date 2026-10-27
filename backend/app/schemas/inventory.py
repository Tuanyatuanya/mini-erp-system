from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.inventory import MovementType
from app.schemas.item import ItemSummary


class InventoryMovementBase(BaseModel):
    item_id: int
    movement_type: MovementType
    movement_date: date
    qty: Decimal
    unit: str
    reference_type: str | None = None
    reference_id: int | None = None
    from_location: str | None = None
    to_location: str | None = None
    notes: str | None = None


class InventoryMovementCreate(InventoryMovementBase):
    movement_no: str | None = None


class InventoryMovementOut(InventoryMovementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movement_no: str
    item: ItemSummary
    created_at: datetime


class InventoryMovementListOut(BaseModel):
    items: list[InventoryMovementOut]
    total: int
    page: int
    page_size: int


class InventoryBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    item: ItemSummary
    location: str
    qty_on_hand: Decimal
    qty_reserved: Decimal
    qty_available: Decimal = Decimal("0")
    last_updated: datetime

    @classmethod
    def from_orm_with_available(cls, obj):
        data = cls.model_validate(obj)
        data.qty_available = data.qty_on_hand - data.qty_reserved
        return data
