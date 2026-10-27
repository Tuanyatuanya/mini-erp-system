from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.item import Item, ItemCategory, BOMHeader, BOMLine, ItemType
from app.models.import_job import ImportJob, JobStatus
from app.schemas.item import (
    ItemCreate, ItemUpdate, ItemOut, ItemListOut, ItemCategoryCreate, ItemCategoryOut,
    BOMHeaderCreate, BOMHeaderOut,
)
from app.services.excel_service import export_items, parse_items_xlsx
from datetime import datetime

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/categories", response_model=list[ItemCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemCategory).order_by(ItemCategory.name))
    return result.scalars().all()


@router.post("/categories", response_model=ItemCategoryOut, status_code=201)
async def create_category(data: ItemCategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = ItemCategory(**data.model_dump())
    db.add(cat)
    await db.flush()
    return cat


@router.get("/export")
async def export_items_xlsx(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Item).options(selectinload(Item.category)).order_by(Item.code)
    )
    items = result.scalars().all()
    data = [ItemOut.model_validate(i).model_dump() for i in items]
    content = export_items(data)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=items.xlsx"},
    )


@router.post("/import")
async def import_items_xlsx(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    valid_rows, error_rows = parse_items_xlsx(content)

    job = ImportJob(
        job_type="items",
        filename=file.filename or "upload.xlsx",
        status=JobStatus.PROCESSING,
        total_rows=len(valid_rows) + len(error_rows),
    )
    db.add(job)
    await db.flush()

    processed = 0
    for row in valid_rows:
        existing = await db.execute(select(Item).where(Item.code == row["code"]))
        item = existing.scalar_one_or_none()
        if item:
            for k, v in row.items():
                setattr(item, k, v)
        else:
            db.add(Item(**row))
        processed += 1

    job.processed_rows = processed
    job.error_rows = len(error_rows)
    job.error_detail = {"errors": error_rows}
    job.status = JobStatus.DONE
    job.completed_at = datetime.utcnow()
    await db.flush()
    return {"job_id": job.id, "processed": processed, "errors": len(error_rows)}


@router.get("", response_model=ItemListOut)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category_id: int | None = None,
    item_type: ItemType | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Item).options(selectinload(Item.category))
    if search:
        q = q.where(or_(Item.code.ilike(f"%{search}%"), Item.name.ilike(f"%{search}%")))
    if category_id:
        q = q.where(Item.category_id == category_id)
    if item_type:
        q = q.where(Item.item_type == item_type)
    if is_active is not None:
        q = q.where(Item.is_active == is_active)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.order_by(Item.code).offset((page - 1) * page_size).limit(page_size))
    return ItemListOut(items=result.scalars().all(), total=total, page=page, page_size=page_size)


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(data: ItemCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(Item).where(Item.code == data.code))
    if existing:
        raise HTTPException(400, f"Item code '{data.code}' already exists")
    item = Item(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item, ["category"])
    return item


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Item).options(selectinload(Item.category)).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(item_id: int, data: ItemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Item).options(selectinload(Item.category)).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    await db.flush()
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    item.is_active = False
    await db.flush()


@router.get("/{item_id}/bom", response_model=BOMHeaderOut | None)
async def get_item_bom(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BOMHeader)
        .options(
            selectinload(BOMHeader.lines).selectinload(BOMLine.component_item)
        )
        .where(BOMHeader.parent_item_id == item_id, BOMHeader.is_active == True)
        .order_by(BOMHeader.effective_date.desc())
    )
    return result.scalars().first()


@router.post("/{item_id}/bom", response_model=BOMHeaderOut, status_code=201)
async def create_bom(item_id: int, data: BOMHeaderCreate, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    await db.execute(
        select(BOMHeader).where(BOMHeader.parent_item_id == item_id)
    )
    bom = BOMHeader(
        parent_item_id=item_id,
        version=data.version,
        effective_date=data.effective_date,
        is_active=True,
    )
    db.add(bom)
    await db.flush()
    for line_data in data.lines:
        db.add(BOMLine(bom_header_id=bom.id, **line_data.model_dump()))
    await db.flush()
    await db.refresh(bom, ["lines"])
    return bom
