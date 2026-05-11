import { NavLink } from "react-router-dom";
import { Bot, GitFork, Activity, LayoutTemplate } from "lucide-react";
import { clsx } from "clsx";

const links = [
  { to: "/agents", label: "Agents", icon: Bot },
  { to: "/workflows", label: "Workflows", icon: GitFork },
  { to: "/templates", label: "Templates", icon: LayoutTemplate },
  { to: "/monitor", label: "Monitor", icon: Activity },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-52 flex-col border-r border-gray-200 bg-white shrink-0">
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-100">
        <span className="text-sm font-semibold text-gray-900">AgentForge</span>
      </div>
      <nav className="flex-1 px-3 py-3 space-y-0.5">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2.5 px-3 py-2 text-sm rounded-md transition-colors",
                isActive
                  ? "bg-indigo-50 text-indigo-700 font-medium"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">v1.0.0</p>
      </div>
    </aside>
  );
}
