# Mini ERP System — Architecture

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy + Alembic + PostgreSQL
- **Frontend**: React + TypeScript + Vite + Zustand + TanStack Query
- **Excel**: openpyxl (import/export)
- **Auth**: JWT (planned — not yet implemented)

## Module Overview

| Module | Description |
|--------|-------------|
| Item Master | Products, raw materials, BOMs |
| Production Plan | Planned work orders by period |
| Actual Output | Recorded production results |
| Inventory Movement | Stock in/out/adjustment ledger |
| Excel Import/Export | Bulk data via .xlsx |
| Dashboard | KPIs, variance, charts |

## Database Schema

### item_categories
- id, name, description, created_at

### items
- id, code (unique), name, category_id, unit, description
- item_type: PRODUCT | MATERIAL | WIP
- standard_cost, reorder_point, lead_time_days
- is_active, created_at, updated_at

### bom_headers (Bill of Materials)
- id, parent_item_id (FK items), version, effective_date, is_active

### bom_lines
- id, bom_header_id, component_item_id, qty_per, unit, scrap_pct

### production_plans
- id, plan_no (unique), item_id, planned_qty, unit
- period_start, period_end, status: DRAFT|RELEASED|CLOSED
- notes, created_by, created_at, updated_at

### actual_outputs
- id, output_no (unique), production_plan_id (nullable FK), item_id
- output_date, actual_qty, unit, good_qty, scrap_qty
- line_id, shift, operator, notes
- created_by, created_at

### inventory_movements
- id, movement_no (unique), item_id, movement_type
  - Types: RECEIPT | ISSUE | RETURN | ADJUSTMENT | TRANSFER | PRODUCTION_IN | PRODUCTION_OUT
- reference_type, reference_id (polymorphic to plan/output/PO)
- movement_date, qty (signed: + in, - out), unit
- from_location, to_location, notes
- created_by, created_at

### inventory_balances (materialized/computed)
- id, item_id, location, qty_on_hand, qty_reserved, last_updated

### import_jobs
- id, job_type, filename, status: PENDING|PROCESSING|DONE|ERROR
- total_rows, processed_rows, error_rows, error_detail (JSON)
- created_by, created_at, completed_at

## API Endpoints

### /api/items
- GET    /               list with filters (category, type, search)
- POST   /               create
- GET    /{id}           detail
- PUT    /{id}           update
- DELETE /{id}           soft-delete
- GET    /{id}/bom       get active BOM
- GET    /export         download xlsx
- POST   /import         upload xlsx

### /api/production-plans
- GET    /               list (status, period, item)
- POST   /               create
- GET    /{id}           detail with actuals
- PUT    /{id}           update
- PATCH  /{id}/release   change status DRAFT→RELEASED
- PATCH  /{id}/close     change status RELEASED→CLOSED
- GET    /export         download xlsx
- POST   /import         upload xlsx

### /api/actual-outputs
- GET    /               list (date range, item, plan)
- POST   /               create (auto-creates inventory movement)
- GET    /{id}           detail
- PUT    /{id}           update
- DELETE /{id}           void
- GET    /export         download xlsx
- POST   /import         upload xlsx

### /api/inventory
- GET    /movements      list movements
- POST   /movements      manual movement (adjustment/receipt/issue)
- GET    /movements/{id} detail
- GET    /balances       current stock by item/location
- GET    /balances/{item_id} item stock detail
- GET    /movements/export  download xlsx

### /api/dashboard
- GET    /kpis           production efficiency, plan vs actual, inventory value
- GET    /plan-vs-actual date range summary
- GET    /inventory-turnover
- GET    /recent-movements

### /api/import-jobs
- GET    /               list recent jobs
- GET    /{id}           job status + errors
