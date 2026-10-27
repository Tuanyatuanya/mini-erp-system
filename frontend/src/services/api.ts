import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ─── Types ────────────────────────────────────────────────────────────────────

export type ItemType = "PRODUCT" | "MATERIAL" | "WIP";
export type PlanStatus = "DRAFT" | "RELEASED" | "CLOSED";
export type MovementType =
  | "RECEIPT" | "ISSUE" | "RETURN" | "ADJUSTMENT"
  | "TRANSFER" | "PRODUCTION_IN" | "PRODUCTION_OUT";

export interface ItemCategory { id: number; name: string; description?: string }
export interface ItemSummary { id: number; code: string; name: string; unit: string }
export interface Item extends ItemSummary {
  category_id?: number; category?: ItemCategory;
  item_type: ItemType; description?: string;
  standard_cost: number; reorder_point: number; lead_time_days: number;
  is_active: boolean; created_at: string; updated_at: string;
}
export interface BOMLine {
  id: number; component_item_id: number; component_item: ItemSummary;
  qty_per: number; unit: string; scrap_pct: number;
}
export interface BOMHeader {
  id: number; parent_item_id: number; version: string;
  effective_date: string; is_active: boolean; lines: BOMLine[];
}

export interface ProductionPlan {
  id: number; plan_no: string; item: ItemSummary; item_id: number;
  planned_qty: number; actual_qty_sum: number; unit: string;
  period_start: string; period_end: string; status: PlanStatus;
  notes?: string; created_at: string; updated_at: string;
}
export interface ActualOutput {
  id: number; output_no: string; item: ItemSummary; item_id: number;
  output_date: string; actual_qty: number; good_qty: number; scrap_qty: number;
  unit: string; production_plan_id?: number; line_id?: string;
  shift?: string; operator?: string; notes?: string; is_voided: boolean; created_at: string;
}

export interface InventoryMovement {
  id: number; movement_no: string; item: ItemSummary; item_id: number;
  movement_type: MovementType; movement_date: string; qty: number; unit: string;
  from_location?: string; to_location?: string;
  reference_type?: string; reference_id?: number; notes?: string; created_at: string;
}
export interface InventoryBalance {
  id: number; item_id: number; item: ItemSummary; location: string;
  qty_on_hand: number; qty_reserved: number; qty_available: number; last_updated: string;
}

export interface KPIs {
  total_active_items: number; total_plans_this_month: number;
  total_outputs_this_month: number; plan_achievement_rate: number;
  total_inventory_value: number; low_stock_items: number;
}
export interface PlanVsActualRow {
  plan_no: string; item_code: string; item_name: string;
  planned_qty: number; actual_qty: number; variance: number;
  achievement_pct: number; period_start: string; period_end: string; status: string;
}
export interface PlanVsActual {
  rows: PlanVsActualRow[]; total_planned: number;
  total_actual: number; overall_achievement_pct: number;
}
export interface RecentMovement {
  movement_no: string; item_code: string; item_name: string;
  movement_type: string; qty: number; unit: string; movement_date: string;
}

export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number }

// ─── API calls ────────────────────────────────────────────────────────────────

export const itemsApi = {
  list: (params?: object) => api.get<Paginated<Item>>("/items", { params }).then(r => r.data),
  get: (id: number) => api.get<Item>(`/items/${id}`).then(r => r.data),
  create: (data: object) => api.post<Item>("/items", data).then(r => r.data),
  update: (id: number, data: object) => api.put<Item>(`/items/${id}`, data).then(r => r.data),
  delete: (id: number) => api.delete(`/items/${id}`),
  categories: () => api.get<ItemCategory[]>("/items/categories").then(r => r.data),
  createCategory: (data: object) => api.post<ItemCategory>("/items/categories", data).then(r => r.data),
  bom: (id: number) => api.get<BOMHeader | null>(`/items/${id}/bom`).then(r => r.data),
  exportUrl: () => "/api/items/export",
  import: (file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return api.post("/items/import", fd, { headers: { "Content-Type": "multipart/form-data" } }).then(r => r.data);
  },
};

export const productionApi = {
  listPlans: (params?: object) => api.get<Paginated<ProductionPlan>>("/production/plans", { params }).then(r => r.data),
  getPlan: (id: number) => api.get<ProductionPlan>(`/production/plans/${id}`).then(r => r.data),
  createPlan: (data: object) => api.post<ProductionPlan>("/production/plans", data).then(r => r.data),
  updatePlan: (id: number, data: object) => api.put<ProductionPlan>(`/production/plans/${id}`, data).then(r => r.data),
  releasePlan: (id: number) => api.patch<ProductionPlan>(`/production/plans/${id}/release`).then(r => r.data),
  closePlan: (id: number) => api.patch<ProductionPlan>(`/production/plans/${id}/close`).then(r => r.data),
  exportPlansUrl: () => "/api/production/plans/export",

  listOutputs: (params?: object) => api.get<Paginated<ActualOutput>>("/production/outputs", { params }).then(r => r.data),
  getOutput: (id: number) => api.get<ActualOutput>(`/production/outputs/${id}`).then(r => r.data),
  createOutput: (data: object) => api.post<ActualOutput>("/production/outputs", data).then(r => r.data),
  updateOutput: (id: number, data: object) => api.put<ActualOutput>(`/production/outputs/${id}`, data).then(r => r.data),
  voidOutput: (id: number) => api.delete(`/production/outputs/${id}`),
  exportOutputsUrl: () => "/api/production/outputs/export",
};

export const inventoryApi = {
  listMovements: (params?: object) => api.get<Paginated<InventoryMovement>>("/inventory/movements", { params }).then(r => r.data),
  createMovement: (data: object) => api.post<InventoryMovement>("/inventory/movements", data).then(r => r.data),
  listBalances: (params?: object) => api.get<InventoryBalance[]>("/inventory/balances", { params }).then(r => r.data),
  exportMovementsUrl: () => "/api/inventory/movements/export",
};

export const dashboardApi = {
  kpis: () => api.get<KPIs>("/dashboard/kpis").then(r => r.data),
  planVsActual: (params?: object) => api.get<PlanVsActual>("/dashboard/plan-vs-actual", { params }).then(r => r.data),
  recentMovements: () => api.get<RecentMovement[]>("/dashboard/recent-movements").then(r => r.data),
};
