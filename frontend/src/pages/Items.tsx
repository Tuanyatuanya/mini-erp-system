import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { itemsApi, type Item, type ItemType } from "../services/api";
import Table from "../components/Table";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import StatusBadge from "../components/StatusBadge";
import { Plus, Download, Upload, Search, Pencil, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";

type FormData = {
  code: string; name: string; item_type: ItemType; unit: string;
  category_id?: number; standard_cost?: number; reorder_point?: number;
  lead_time_days?: number; description?: string;
};

export default function Items() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Item | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["items", page, search],
    queryFn: () => itemsApi.list({ page, page_size: 20, search: search || undefined }),
  });
  const { data: categories } = useQuery({ queryKey: ["categories"], queryFn: itemsApi.categories });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>();

  const createMut = useMutation({
    mutationFn: itemsApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["items"] }); closeModal(); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: object }) => itemsApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["items"] }); closeModal(); },
  });
  const deleteMut = useMutation({
    mutationFn: itemsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["items"] }),
  });
  const importMut = useMutation({
    mutationFn: itemsApi.import,
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["items"] });
      alert(`Imported ${res.processed} rows. Errors: ${res.errors}`);
    },
  });

  function openCreate() { setEditing(null); reset({}); setModalOpen(true); }
  function openEdit(item: Item) {
    setEditing(item);
    reset({
      code: item.code, name: item.name, item_type: item.item_type,
      unit: item.unit, standard_cost: item.standard_cost,
      reorder_point: item.reorder_point, lead_time_days: item.lead_time_days,
      description: item.description, category_id: item.category_id,
    });
    setModalOpen(true);
  }
  function closeModal() { setModalOpen(false); setEditing(null); }

  function onSubmit(values: FormData) {
    if (editing) updateMut.mutate({ id: editing.id, data: values });
    else createMut.mutate(values);
  }

  const columns = [
    { key: "code", header: "Code", render: (r: Item) => <span className="font-mono text-xs text-gray-600">{r.code}</span> },
    { key: "name", header: "Name" },
    { key: "item_type", header: "Type", render: (r: Item) => <StatusBadge value={r.item_type} /> },
    { key: "category", header: "Category", render: (r: Item) => r.category?.name ?? "—" },
    { key: "unit", header: "Unit" },
    { key: "standard_cost", header: "Std Cost", render: (r: Item) => Number(r.standard_cost).toLocaleString() },
    { key: "is_active", header: "Active", render: (r: Item) => r.is_active ? "✓" : "—" },
    {
      key: "actions", header: "", render: (r: Item) => (
        <div className="flex gap-1">
          <button onClick={e => { e.stopPropagation(); openEdit(r); }} className="p-1 text-gray-400 hover:text-primary"><Pencil size={14} /></button>
          <button onClick={e => { e.stopPropagation(); if (confirm("Deactivate?")) deleteMut.mutate(r.id); }} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={14} /></button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Item Master</h2>
        <div className="flex gap-2">
          <a href={itemsApi.exportUrl()} download className="btn-secondary">
            <Download size={15} /> Export
          </a>
          <button onClick={() => fileRef.current?.click()} className="btn-secondary">
            <Upload size={15} /> Import
          </button>
          <input ref={fileRef} type="file" accept=".xlsx" className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) importMut.mutate(f); e.target.value = ""; }} />
          <button onClick={openCreate} className="btn-primary"><Plus size={15} /> New Item</button>
        </div>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-2.5 text-gray-400" />
          <input
            className="input pl-8"
            placeholder="Search code or name..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
      </div>

      <Table columns={columns as never} data={(data?.items ?? []) as never} loading={isLoading} />
      <Pagination page={page} pageSize={20} total={data?.total ?? 0} onChange={setPage} />

      <Modal title={editing ? "Edit Item" : "New Item"} open={modalOpen} onClose={closeModal}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Code *</label>
              <input className="input" {...register("code", { required: true })} disabled={!!editing} />
            </div>
            <div>
              <label className="label">Name *</label>
              <input className="input" {...register("name", { required: true })} />
            </div>
            <div>
              <label className="label">Type</label>
              <select className="input" {...register("item_type")}>
                <option value="MATERIAL">MATERIAL</option>
                <option value="PRODUCT">PRODUCT</option>
                <option value="WIP">WIP</option>
              </select>
            </div>
            <div>
              <label className="label">Unit</label>
              <input className="input" {...register("unit")} defaultValue="EA" />
            </div>
            <div>
              <label className="label">Category</label>
              <select className="input" {...register("category_id", { valueAsNumber: true })}>
                <option value="">— None —</option>
                {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Standard Cost</label>
              <input className="input" type="number" step="0.0001" {...register("standard_cost", { valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Reorder Point</label>
              <input className="input" type="number" step="0.01" {...register("reorder_point", { valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Lead Time (days)</label>
              <input className="input" type="number" {...register("lead_time_days", { valueAsNumber: true })} />
            </div>
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input" rows={2} {...register("description")} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMut.isPending || updateMut.isPending}>
              {editing ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
