import { clsx } from "clsx";

export function Button({ children, variant = "primary", size = "md", className, ...props }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center gap-1.5 font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        size === "sm" && "px-3 py-1.5 text-xs",
        size === "md" && "px-4 py-2 text-sm",
        variant === "primary" && "bg-indigo-600 text-white hover:bg-indigo-700",
        variant === "secondary" && "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
        variant === "ghost" && "text-gray-500 hover:text-gray-700 hover:bg-gray-100",
        variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
