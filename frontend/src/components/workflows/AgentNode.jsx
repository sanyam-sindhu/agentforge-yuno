import { Handle, Position } from "reactflow";
import { Bot } from "lucide-react";

export function AgentNode({ data }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2.5 w-44 shadow-sm">
      <Handle type="target" position={Position.Left} style={{ background: "#6366f1", width: 8, height: 8, border: "2px solid white" }} />
      <div className="flex items-center gap-2 mb-0.5">
        <Bot size={13} className="text-indigo-500 shrink-0" />
        <span className="text-sm font-semibold text-gray-900 truncate">{data.label}</span>
      </div>
      <p className="text-xs text-gray-400">{data.role}</p>
      {data.tools?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {data.tools.map((t) => (
            <span key={t} className="bg-gray-100 text-gray-500 rounded px-1.5 py-0.5 text-[10px]">{t}</span>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Right} style={{ background: "#6366f1", width: 8, height: 8, border: "2px solid white" }} />
    </div>
  );
}
