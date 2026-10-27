from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.item import ItemType


class ItemCategoryBase(BaseModel):
    name: str
    description: str | None = None


class ItemCategoryCreate(ItemCategoryBase):
    pass


class ItemCategoryOut(ItemCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class BOMLineBase(BaseModel):
    component_item_id: int
    qty_per: Decimal
    unit: str
    scrap_pct: Decimal = Decimal("0")


class BOMLineCreate(BOMLineBase):
    pass


class BOMLineOut(BOMLineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component_item: "ItemSummary"


class BOMHeaderBase(BaseModel):
    parent_item_id: int
    version: str = "1.0"
    effective_date: datetime
    is_active: bool = True


class BOMHeaderCreate(BOMHeaderBase):
    lines: list[BOMLineCreate] = []


class BOMHeaderOut(BOMHeaderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lines: list[BOMLineOut]
    created_at: datetime


class ItemBase(BaseModel):
    code: str
    name: str
    category_id: int | None = None
    item_type: ItemType = ItemType.MATERIAL
    unit: str = "EA"
    description: str | None = None
    standard_cost: Decimal = Decimal("0")
    reorder_point: Decimal = Decimal("0")
    lead_time_days: int = 0
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    item_type: ItemType | None = None
    unit: str | None = None
    description: str | None = None
    standard_cost: Decimal | None = None
    reorder_point: Decimal | None = None
    lead_time_days: int | None = None
    is_active: bool | None = None


class ItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    unit: str


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: ItemCategoryOut | None = None
    created_at: datetime
    updated_at: datetime


class ItemListOut(BaseModel):
    items: list[ItemOut]
    total: int
    page: int
    page_size: int


BOMLineOut.model_rebuild()
