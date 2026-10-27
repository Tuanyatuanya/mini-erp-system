const colors: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  RELEASED: "bg-blue-100 text-blue-700",
  CLOSED: "bg-green-100 text-green-700",
  RECEIPT: "bg-green-100 text-green-700",
  ISSUE: "bg-red-100 text-red-700",
  RETURN: "bg-yellow-100 text-yellow-700",
  ADJUSTMENT: "bg-purple-100 text-purple-700",
  TRANSFER: "bg-indigo-100 text-indigo-700",
  PRODUCTION_IN: "bg-teal-100 text-teal-700",
  PRODUCTION_OUT: "bg-orange-100 text-orange-700",
  PRODUCT: "bg-blue-100 text-blue-700",
  MATERIAL: "bg-gray-100 text-gray-700",
  WIP: "bg-amber-100 text-amber-700",
};

export default function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`badge ${colors[value] ?? "bg-gray-100 text-gray-600"}`}>
      {value.replace(/_/g, " ")}
    </span>
  );
}
