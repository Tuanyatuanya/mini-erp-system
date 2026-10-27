import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard, Package, ClipboardList, Factory,
  ArrowLeftRight, Menu, X
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/items", label: "Item Master", icon: Package },
  { to: "/production-plans", label: "Production Plans", icon: ClipboardList },
  { to: "/actual-outputs", label: "Actual Outputs", icon: Factory },
  { to: "/inventory", label: "Inventory", icon: ArrowLeftRight },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? "w-56" : "w-14"} flex-shrink-0 bg-primary flex flex-col transition-all duration-200`}
      >
        <div className="flex items-center gap-2 px-3 py-4 border-b border-primary-dark">
          <button
            onClick={() => setSidebarOpen(v => !v)}
            className="text-white/70 hover:text-white p-1 rounded"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          {sidebarOpen && (
            <span className="text-white font-bold text-base tracking-wide truncate">Mini ERP</span>
          )}
        </div>
        <nav className="flex-1 py-3 space-y-0.5">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-white/20 text-white font-semibold"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <Icon size={18} className="flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center">
          <h1 className="text-gray-500 text-sm">Manufacturing Data Management</h1>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
