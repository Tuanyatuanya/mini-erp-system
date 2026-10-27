import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productionApi, itemsApi, type ActualOutput } from "../services/api";
import Table from "../components/Table";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import { Plus, Download, XCircle } from "lucide-react";
import { useForm } from "react-hook-form";

type FormData = {
  item_id: number; output_date: string; actual_qty: number; unit: string;
  good_qty?: number; scrap_qty?: number; production_plan_id?: number;
  line_id?: string; shift?: string; operator?: string; notes?: string;
};

export default function ActualOutputs() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["outputs", page],
    queryFn: () => productionApi.listOutputs({ page, page_size: 20 }),
  });
  const { data: items } = useQuery({ queryKey: ["items-all"], queryFn: () => itemsApi.list({ page_size: 200 }) });
  const { data: plans } = useQuery({
    queryKey: ["plans-released"],
    queryFn: () => productionApi.listPlans({ status: "RELEASED", page_size: 200 }),
  });

  const { register, handleSubmit, reset, watch } = useForm<FormData>();

  const createMut = useMutation({
    mutationFn: productionApi.createOutput,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["outputs"] }); setModalOpen(false); reset(); },
  });
  const voidMut = useMutation({
    mutationFn: productionApi.voidOutput,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["outputs"] }),
  });

  const columns = [
    { key: "output_no", header: "Output No", render: (r: ActualOutput) => <span className="font-mono text-xs">{r.output_no}</span> },
    { key: "item", header: "Item", render: (r: ActualOutput) => `${r.item.code} — ${r.item.name}` },
    { key: "output_date", header: "Date" },
    { key: "actual_qty", header: "Actual Qty", render: (r: ActualOutput) => `${Number(r.actual_qty).toLocaleString()} ${r.unit}` },
    { key: "good_qty", header: "Good", render: (r: ActualOutput) => <span className="text-green-600">{Number(r.good_qty).toLocaleString()}</span> },
    { key: "scrap_qty", header: "Scrap", render: (r: ActualOutput) => <span className="text-red-500">{Number(r.scrap_qty).toLocaleString()}</span> },
    { key: "shift", header: "Shift", render: (r: ActualOutput) => r.shift ?? "—" },
    { key: "operator", header: "Operator", render: (r: ActualOutput) => r.operator ?? "—" },
    {
      key: "actions", header: "", render: (r: ActualOutput) => (
        !r.is_voided ? (
          <button onClick={e => { e.stopPropagation(); if (confirm("Void this output?")) voidMut.mutate(r.id); }}
            className="p-1 text-red-400 hover:text-red-600" title="Void">
            <XCircle size={14} />
          </button>
        ) : <span className="text-gray-300 text-xs">voided</span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Actual Outputs</h2>
        <div className="flex gap-2">
          <a href={productionApi.exportOutputsUrl()} download className="btn-secondary">
            <Download size={15} /> Export
          </a>
          <button onClick={() => { reset(); setModalOpen(true); }} className="btn-primary">
            <Plus size={15} /> Record Output
          </button>
        </div>
      </div>

      <Table columns={columns as never} data={(data?.items ?? []) as never} loading={isLoading} />
      <Pagination page={page} pageSize={20} total={data?.total ?? 0} onChange={setPage} />

      <Modal title="Record Actual Output" open={modalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleSubmit(d => createMut.mutate(d))} className="space-y-3">
          <div>
            <label className="label">Item *</label>
            <select className="input" {...register("item_id", { required: true, valueAsNumber: true })}>
              <option value="">— Select —</option>
              {items?.items.map(i => <option key={i.id} value={i.id}>{i.code} — {i.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Link to Plan (optional)</label>
            <select className="input" {...register("production_plan_id", { valueAsNumber: true })}>
              <option value="">— None —</option>
              {plans?.items.map(p => <option key={p.id} value={p.id}>{p.plan_no} — {p.item.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Output Date *</label>
              <input className="input" type="date" {...register("output_date", { required: true })} />
            </div>
            <div>
              <label className="label">Unit</label>
              <input className="input" defaultValue="EA" {...register("unit")} />
            </div>
            <div>
              <label className="label">Actual Qty *</label>
              <input className="input" type="number" step="0.01" {...register("actual_qty", { required: true, valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Good Qty</label>
              <input className="input" type="number" step="0.01" {...register("good_qty", { valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Scrap Qty</label>
              <input className="input" type="number" step="0.01" {...register("scrap_qty", { valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Shift</label>
              <select className="input" {...register("shift")}>
                <option value="">—</option>
                <option>Morning</option>
                <option>Afternoon</option>
                <option>Night</option>
              </select>
            </div>
            <div>
              <label className="label">Line</label>
              <input className="input" placeholder="LINE-1" {...register("line_id")} />
            </div>
            <div>
              <label className="label">Operator</label>
              <input className="input" {...register("operator")} />
            </div>
          </div>
          <div>
            <label className="label">Notes</label>
            <textarea className="input" rows={2} {...register("notes")} />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMut.isPending}>Record</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
