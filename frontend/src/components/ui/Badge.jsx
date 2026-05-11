import { clsx } from "clsx";

export function Badge({ label, color = "gray" }) {
  return (
    <span className={clsx(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
      color === "green" && "bg-green-100 text-green-700",
      color === "blue" && "bg-blue-100 text-blue-700",
      color === "yellow" && "bg-yellow-100 text-yellow-700",
      color === "red" && "bg-red-100 text-red-700",
      color === "orange" && "bg-orange-100 text-orange-700",
      color === "gray" && "bg-gray-100 text-gray-600",
    )}>
      {label}
    </span>
  );
}
