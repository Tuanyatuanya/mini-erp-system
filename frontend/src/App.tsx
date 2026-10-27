import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Items from "./pages/Items";
import ProductionPlans from "./pages/ProductionPlans";
import ActualOutputs from "./pages/ActualOutputs";
import Inventory from "./pages/Inventory";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="items" element={<Items />} />
        <Route path="production-plans" element={<ProductionPlans />} />
        <Route path="actual-outputs" element={<ActualOutputs />} />
        <Route path="inventory" element={<Inventory />} />
      </Route>
    </Routes>
  );
}
