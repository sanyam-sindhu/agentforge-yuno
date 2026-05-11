import { useState } from "react";
import { Trash2 } from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";
import { useExecutions } from "../hooks/useWorkflow";
import { LiveFeed } from "../components/monitor/LiveFeed";
import { MessageTrace } from "../components/monitor/MessageTrace";
import { CostPanel } from "../components/monitor/CostPanel";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

const statusColor = { completed: "green", pending: "yellow", running: "blue", failed: "red" };

export function MonitorPage() {
  const { events, connected, clear } = useWebSocket();
  const { data: executions = [] } = useExecutions();
  const [selectedExecution, setSelectedExecution] = useState(null);

  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-gray-200 p-4 flex flex-col gap-2 overflow-y-auto bg-white">
        <h3 className="text-sm font-semibold text-gray-800 mb-1">Executions</h3>
        {executions.map((ex) => (
          <div key={ex.id} onClick={() => setSelectedExecution(ex)}
            className={`rounded-lg border p-3 cursor-pointer transition-colors ${
              selectedExecution?.id === ex.id ? "border-indigo-300 bg-indigo-50" : "border-gray-200 hover:border-gray-300"
            }`}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-700">#{ex.id}</span>
              <Badge label={ex.status} color={statusColor[ex.status] ?? "gray"} />
            </div>
            <p className="text-xs text-gray-400 line-clamp-1">{ex.input_text}</p>
          </div>
        ))}
        {executions.length === 0 && <p className="text-xs text-gray-400">No executions yet</p>}
      </div>

      <div className="flex-1 flex flex-col gap-4 p-6 overflow-y-auto">
        {selectedExecution && <CostPanel execution={selectedExecution} />}
        <div className="flex-1 card p-4 overflow-y-auto">
          <h4 className="text-sm font-semibold text-gray-800 mb-3">Message Trace</h4>
          <MessageTrace executionId={selectedExecution?.id} />
        </div>
      </div>

      <div className="w-72 border-l border-gray-200 p-4 flex flex-col bg-white">
        <div className="flex justify-end mb-2">
          <Button variant="ghost" size="sm" onClick={clear}><Trash2 size={13} /> Clear</Button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <LiveFeed events={events} connected={connected} />
        </div>
      </div>
    </div>
  );
}
