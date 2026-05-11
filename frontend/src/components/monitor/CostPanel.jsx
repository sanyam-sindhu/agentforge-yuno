import { ExternalLink } from "lucide-react";
import { Badge } from "../ui/Badge";

const statusColor = { completed: "green", pending: "yellow", running: "blue", failed: "red" };

export function CostPanel({ execution }) {
  if (!execution) return null;
  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-800">Execution #{execution.id}</span>
        <Badge label={execution.status} color={statusColor[execution.status] ?? "gray"} />
      </div>
      <p className="text-xs text-gray-500">Started {new Date(execution.started_at).toLocaleTimeString()}</p>
      {execution.langfuse_trace_id && (
        <a href={`https://jp.cloud.langfuse.com/trace/${execution.langfuse_trace_id}`}
          target="_blank" rel="noreferrer"
          className="flex items-center gap-1 text-xs text-indigo-600 hover:underline">
          <ExternalLink size={12} /> View trace in Langfuse
        </a>
      )}
      {execution.output_text && (
        <div className="bg-gray-50 rounded p-3">
          <p className="text-xs text-gray-500 mb-1">Output</p>
          <p className="text-xs text-gray-700 whitespace-pre-wrap line-clamp-6">{execution.output_text}</p>
        </div>
      )}
    </div>
  );
}
