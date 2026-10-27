import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productionApi, itemsApi, type ProductionPlan, type PlanStatus } from "../services/api";
import Table from "../components/Table";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import StatusBadge from "../components/StatusBadge";
import { Plus, Download, Play, CheckCircle } from "lucide-react";
import { useForm } from "react-hook-form";

type FormData = {
  item_id: number; planned_qty: number; unit: string;
  period_start: string; period_end: string; notes?: string; plan_no?: string;
};

export default function ProductionPlans() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<PlanStatus | "">("");

  const { data, isLoading } = useQuery({
    queryKey: ["plans", page, statusFilter],
    queryFn: () => productionApi.listPlans({ page, page_size: 20, status: statusFilter || undefined }),
  });
  const { data: items } = useQuery({ queryKey: ["items-all"], queryFn: () => itemsApi.list({ page_size: 200 }) });

  const { register, handleSubmit, reset } = useForm<FormData>();

  const createMut = useMutation({
    mutationFn: productionApi.createPlan,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["plans"] }); setModalOpen(false); reset(); },
  });
  const releaseMut = useMutation({
    mutationFn: productionApi.releasePlan,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
  });
  const closeMut = useMutation({
    mutationFn: productionApi.closePlan,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
  });

  const achievementColor = (pct: number) =>
    pct >= 100 ? "text-green-600" : pct >= 80 ? "text-amber-600" : "text-red-600";

  const columns = [
    { key: "plan_no", header: "Plan No", render: (r: ProductionPlan) => <span className="font-mono text-xs">{r.plan_no}</span> },
    { key: "item", header: "Item", render: (r: ProductionPlan) => `${r.item.code} — ${r.item.name}` },
    { key: "planned_qty", header: "Planned", render: (r: ProductionPlan) => `${Number(r.planned_qty).toLocaleString()} ${r.unit}` },
    {
      key: "actual_qty_sum", header: "Actual",
      render: (r: ProductionPlan) => {
        const pct = r.planned_qty > 0 ? (Number(r.actual_qty_sum) / Number(r.planned_qty) * 100) : 0;
        return <span className={achievementColor(pct)}>{Number(r.actual_qty_sum).toLocaleString()} ({pct.toFixed(1)}%)</span>;
      }
    },
    { key: "period_start", header: "Period", render: (r: ProductionPlan) => `${r.period_start} ~ ${r.period_end}` },
    { key: "status", header: "Status", render: (r: ProductionPlan) => <StatusBadge value={r.status} /> },
    {
      key: "actions", header: "", render: (r: ProductionPlan) => (
        <div className="flex gap-1">
          {r.status === "DRAFT" && (
            <button onClick={e => { e.stopPropagation(); releaseMut.mutate(r.id); }}
              className="p-1 text-blue-400 hover:text-blue-600" title="Release">
              <Play size={14} />
            </button>
          )}
          {r.status === "RELEASED" && (
            <button onClick={e => { e.stopPropagation(); closeMut.mutate(r.id); }}
              className="p-1 text-green-400 hover:text-green-600" title="Close">
              <CheckCircle size={14} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Production Plans</h2>
        <div className="flex gap-2">
          <a href={productionApi.exportPlansUrl()} download className="btn-secondary">
            <Download size={15} /> Export
          </a>
          <button onClick={() => { reset(); setModalOpen(true); }} className="btn-primary">
            <Plus size={15} /> New Plan
          </button>
        </div>
      </div>

      <div className="flex gap-2">
        <select className="input max-w-[160px]" value={statusFilter} onChange={e => { setStatusFilter(e.target.value as PlanStatus | ""); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="DRAFT">DRAFT</option>
          <option value="RELEASED">RELEASED</option>
          <option value="CLOSED">CLOSED</option>
        </select>
      </div>

      <Table columns={columns as never} data={(data?.items ?? []) as never} loading={isLoading} />
      <Pagination page={page} pageSize={20} total={data?.total ?? 0} onChange={setPage} />

      <Modal title="New Production Plan" open={modalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleSubmit(d => createMut.mutate(d))} className="space-y-3">
          <div>
            <label className="label">Plan No (auto if blank)</label>
            <input className="input" placeholder="PP-202501-XXXXX" {...register("plan_no")} />
          </div>
          <div>
            <label className="label">Item *</label>
            <select className="input" {...register("item_id", { required: true, valueAsNumber: true })}>
              <option value="">— Select —</option>
              {items?.items.map(i => <option key={i.id} value={i.id}>{i.code} — {i.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Planned Qty *</label>
              <input className="input" type="number" step="0.01" {...register("planned_qty", { required: true, valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Unit</label>
              <input className="input" defaultValue="EA" {...register("unit")} />
            </div>
            <div>
              <label className="label">Period Start *</label>
              <input className="input" type="date" {...register("period_start", { required: true })} />
            </div>
            <div>
              <label className="label">Period End *</label>
              <input className="input" type="date" {...register("period_end", { required: true })} />
            </div>
          </div>
          <div>
            <label className="label">Notes</label>
            <textarea className="input" rows={2} {...register("notes")} />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMut.isPending}>Create</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
