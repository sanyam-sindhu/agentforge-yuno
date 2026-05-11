import { Pencil, Trash2 } from "lucide-react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export function AgentCard({ agent, onEdit, onDelete }) {
  return (
    <div className="card p-5 flex flex-col gap-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-gray-500 mb-0.5">{agent.role}</p>
          <h3 className="font-semibold text-gray-900">{agent.name}</h3>
        </div>
        <div className="flex gap-1 shrink-0">
          <Button variant="ghost" size="sm" onClick={() => onEdit(agent)}>
            <Pencil size={13} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete(agent.id)}>
            <Trash2 size={13} className="text-red-500" />
          </Button>
        </div>
      </div>

      <p className="text-xs text-gray-500 line-clamp-2 bg-gray-50 rounded px-2 py-1.5 font-mono">
        {agent.system_prompt}
      </p>

      <div className="flex flex-wrap gap-1.5 pt-1 border-t border-gray-100">
        <Badge label={agent.model} color="blue" />
        {(agent.tools ?? []).map((t) => <Badge key={t} label={t} color="gray" />)}
        {agent.memory_enabled && <Badge label="memory" color="green" />}
      </div>
    </div>
  );
}
