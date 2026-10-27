import { useQuery } from "@tanstack/react-query";
import { dashboardApi, type PlanVsActualRow } from "../services/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell
} from "recharts";
import { Package, ClipboardList, Factory, TrendingUp, DollarSign, AlertTriangle } from "lucide-react";
import StatusBadge from "../components/StatusBadge";

function KPICard({
  label, value, icon: Icon, color = "text-primary",
}: { label: string; value: string | number; icon: React.ElementType; color?: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-gray-100 ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gray-800 mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: kpis } = useQuery({ queryKey: ["kpis"], queryFn: dashboardApi.kpis });
  const { data: pva } = useQuery({ queryKey: ["pva"], queryFn: () => dashboardApi.planVsActual() });
  const { data: movements } = useQuery({
    queryKey: ["recent-movements"],
    queryFn: dashboardApi.recentMovements,
  });

  const chartData = (pva?.rows ?? []).slice(0, 10).map((r: PlanVsActualRow) => ({
    name: r.item_code,
    Planned: Number(r.planned_qty),
    Actual: Number(r.actual_qty),
  }));

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <KPICard label="Active Items" value={kpis?.total_active_items ?? "—"} icon={Package} />
        <KPICard label="Plans This Month" value={kpis?.total_plans_this_month ?? "—"} icon={ClipboardList} />
        <KPICard label="Outputs This Month" value={kpis?.total_outputs_this_month ?? "—"} icon={Factory} />
        <KPICard
          label="Achievement Rate"
          value={kpis ? `${kpis.plan_achievement_rate}%` : "—"}
          icon={TrendingUp}
          color={kpis && kpis.plan_achievement_rate >= 90 ? "text-green-600" : "text-amber-500"}
        />
        <KPICard
          label="Inventory Value"
          value={kpis ? `$${Number(kpis.total_inventory_value).toLocaleString()}` : "—"}
          icon={DollarSign}
        />
        <KPICard
          label="Low Stock Items"
          value={kpis?.low_stock_items ?? "—"}
          icon={AlertTriangle}
          color={kpis && kpis.low_stock_items > 0 ? "text-red-600" : "text-green-600"}
        />
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-4">Plan vs Actual (Top 10 Plans)</h3>
        {chartData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No plan data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Planned" fill="#2E75B6" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Actual" fill="#E67E22" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
        {pva && (
          <div className="mt-3 flex gap-6 text-sm text-gray-600">
            <span>Total Planned: <strong>{Number(pva.total_planned).toLocaleString()}</strong></span>
            <span>Total Actual: <strong>{Number(pva.total_actual).toLocaleString()}</strong></span>
            <span>Overall: <strong>{pva.overall_achievement_pct}%</strong></span>
          </div>
        )}
      </div>

      {/* Recent Movements */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-3">Recent Inventory Movements</h3>
        {!movements?.length ? (
          <p className="text-gray-400 text-sm">No movements yet</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 pr-4">No.</th>
                <th className="pb-2 pr-4">Item</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Qty</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {movements.map(m => (
                <tr key={m.movement_no} className="border-b border-gray-50 last:border-0">
                  <td className="py-1.5 pr-4 text-gray-500 font-mono text-xs">{m.movement_no}</td>
                  <td className="py-1.5 pr-4">{m.item_code} – {m.item_name}</td>
                  <td className="py-1.5 pr-4"><StatusBadge value={m.movement_type} /></td>
                  <td className={`py-1.5 pr-4 font-semibold ${Number(m.qty) >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {Number(m.qty) >= 0 ? "+" : ""}{Number(m.qty).toLocaleString()} {m.unit}
                  </td>
                  <td className="py-1.5 text-gray-500">{m.movement_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
