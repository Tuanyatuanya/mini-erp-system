# Mini ERP System

A full-stack manufacturing data-management app covering **item master and BOMs, production plans, actual outputs, an inventory ledger, Excel import/export, and a plan-vs-actual dashboard**. It models the core data flows a plant planner works with every day.

**Stack:** FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL / SQLite · React · TypeScript · Vite · TanStack Query · Tailwind · Docker Compose

---

## Features
| Module | What it does |
|---|---|
| **Item master** | Products, materials and WIP with cost, reorder point and lead time. Includes categories and a versioned **bill of materials**. |
| **Production plans** | Work orders by period with a `DRAFT → RELEASED → CLOSED` lifecycle |
| **Actual outputs** | Good / scrap quantities by line, shift and operator, linked to plans |
| **Inventory ledger** | Every stock change is a typed movement (receipt, issue, return, adjustment, transfer, production in/out). Balances are maintained per item and location. |
| **Excel I/O** | Bulk item import, plus export of items, plans, outputs and movements to `.xlsx` |
| **Dashboard** | KPIs (active items, plan achievement rate, inventory value, low-stock items), plan vs. actual by item, and recent movements |

## Architecture
```
React + TS (Vite) ──REST/JSON──► FastAPI routers ──► services ──► SQLAlchemy async ORM ──► PostgreSQL / SQLite
   pages, TanStack Query          items, production,   inventory,     Alembic migrations
                                  inventory, dashboard excel, sequence
```
- 33 REST endpoints with auto-generated OpenAPI docs at `/docs`
- Stock is **never edited directly**. All changes go through `apply_movement()`, which writes a signed ledger entry and updates the balance in the same transaction.
- Document numbers (plans, outputs, movements) come from a sequence service.

Schema and module details: [ARCHITECTURE.md](ARCHITECTURE.md)

## Run
**Docker Compose (PostgreSQL)**
```bash
docker compose up --build
docker compose exec backend alembic upgrade head
# frontend http://localhost:5173 · API docs http://localhost:8000/docs
```

**Local dev (SQLite, no database server needed)**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./erp.db"
alembic upgrade head
uvicorn app.main:app --reload

cd ../frontend
npm install && npm run dev
```

## Excel import format (items)
| Code | Name | Type | Unit | Standard Cost | Reorder Point | Lead Time (days) | Description |
|---|---|---|---|---|---|---|---|
| FG-001 | Finished Widget | PRODUCT | EA | 25.50 | 100 | 3 | … |

## Roadmap
- JWT authentication and role-based access
- BOM explosion for material requirements
- Unit and integration test suite (pytest is already in the requirements)
