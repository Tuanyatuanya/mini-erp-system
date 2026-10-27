import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi, itemsApi, type InventoryMovement, type MovementType } from "../services/api";
import Table from "../components/Table";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import StatusBadge from "../components/StatusBadge";
import { Plus, Download, List, BarChart3 } from "lucide-react";
import { useForm } from "react-hook-form";

type FormData = {
  item_id: number; movement_type: MovementType; movement_date: string;
  qty: number; unit: string; from_location?: string; to_location?: string; notes?: string;
};

type Tab = "movements" | "balances";

export default function Inventory() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("balances");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: movements, isLoading: movLoading } = useQuery({
    queryKey: ["movements", page],
    queryFn: () => inventoryApi.listMovements({ page, page_size: 20 }),
    enabled: tab === "movements",
  });
  const { data: balances, isLoading: balLoading } = useQuery({
    queryKey: ["balances"],
    queryFn: () => inventoryApi.listBalances(),
    enabled: tab === "balances",
  });
  const { data: items } = useQuery({ queryKey: ["items-all"], queryFn: () => itemsApi.list({ page_size: 200 }) });

  const { register, handleSubmit, reset } = useForm<FormData>();
  const createMut = useMutation({
    mutationFn: inventoryApi.createMovement,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["movements"] });
      qc.invalidateQueries({ queryKey: ["balances"] });
      setModalOpen(false); reset();
    },
  });

  const movColumns = [
    { key: "movement_no", header: "No.", render: (r: InventoryMovement) => <span className="font-mono text-xs">{r.movement_no}</span> },
    { key: "item", header: "Item", render: (r: InventoryMovement) => `${r.item.code} — ${r.item.name}` },
    { key: "movement_type", header: "Type", render: (r: InventoryMovement) => <StatusBadge value={r.movement_type} /> },
    { key: "movement_date", header: "Date" },
    {
      key: "qty", header: "Qty",
      render: (r: InventoryMovement) => (
        <span className={Number(r.qty) >= 0 ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
          {Number(r.qty) >= 0 ? "+" : ""}{Number(r.qty).toLocaleString()} {r.unit}
        </span>
      ),
    },
    { key: "from_location", header: "From", render: (r: InventoryMovement) => r.from_location ?? "—" },
    { key: "to_location", header: "To", render: (r: InventoryMovement) => r.to_location ?? "—" },
    { key: "notes", header: "Notes", render: (r: InventoryMovement) => r.notes ?? "—" },
  ];

  const balColumns = [
    { key: "item_code", header: "Code", render: (r: any) => <span className="font-mono text-xs">{r.item.code}</span> },
    { key: "item_name", header: "Item Name", render: (r: any) => r.item.name },
    { key: "location", header: "Location" },
    { key: "qty_on_hand", header: "On Hand", render: (r: any) => <span className="font-semibold">{Number(r.qty_on_hand).toLocaleString()}</span> },
    { key: "qty_reserved", header: "Reserved", render: (r: any) => Number(r.qty_reserved).toLocaleString() },
    {
      key: "qty_available", header: "Available",
      render: (r: any) => {
        const avail = Number(r.qty_on_hand) - Number(r.qty_reserved);
        return <span className={avail <= 0 ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>{avail.toLocaleString()}</span>;
      },
    },
    { key: "unit", header: "Unit", render: (r: any) => r.item.unit },
    { key: "last_updated", header: "Updated", render: (r: any) => new Date(r.last_updated).toLocaleDateString() },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Inventory</h2>
        <div className="flex gap-2">
          <a href={inventoryApi.exportMovementsUrl()} download className="btn-secondary">
            <Download size={15} /> Export Movements
          </a>
          <button onClick={() => { reset(); setModalOpen(true); }} className="btn-primary">
            <Plus size={15} /> New Movement
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {(["balances", "movements"] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setPage(1); }}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "balances" ? <BarChart3 size={15} /> : <List size={15} />}
            {t === "balances" ? "Stock Balances" : "Movements"}
          </button>
        ))}
      </div>

      {tab === "movements" && (
        <>
          <Table columns={movColumns as never} data={(movements?.items ?? []) as never} loading={movLoading} />
          <Pagination page={page} pageSize={20} total={movements?.total ?? 0} onChange={setPage} />
        </>
      )}
      {tab === "balances" && (
        <Table columns={balColumns as never} data={(balances ?? []) as never} loading={balLoading} />
      )}

      <Modal title="New Inventory Movement" open={modalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleSubmit(d => createMut.mutate(d))} className="space-y-3">
          <div>
            <label className="label">Item *</label>
            <select className="input" {...register("item_id", { required: true, valueAsNumber: true })}>
              <option value="">— Select —</option>
              {items?.items.map(i => <option key={i.id} value={i.id}>{i.code} — {i.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Type *</label>
              <select className="input" {...register("movement_type", { required: true })}>
                <option value="RECEIPT">RECEIPT</option>
                <option value="ISSUE">ISSUE</option>
                <option value="RETURN">RETURN</option>
                <option value="ADJUSTMENT">ADJUSTMENT</option>
                <option value="TRANSFER">TRANSFER</option>
              </select>
            </div>
            <div>
              <label className="label">Date *</label>
              <input className="input" type="date" {...register("movement_date", { required: true })} />
            </div>
            <div>
              <label className="label">Qty *</label>
              <input className="input" type="number" step="0.01" {...register("qty", { required: true, valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Unit</label>
              <input className="input" defaultValue="EA" {...register("unit")} />
            </div>
            <div>
              <label className="label">From Location</label>
              <input className="input" {...register("from_location")} />
            </div>
            <div>
              <label className="label">To Location</label>
              <input className="input" {...register("to_location")} />
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
