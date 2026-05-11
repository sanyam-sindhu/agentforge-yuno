import { ArrowRight, Zap, CheckCircle } from "lucide-react";

const EVENT_CONFIG = {
  agent_start: { icon: Zap, color: "text-yellow-500", bg: "bg-yellow-50" },
  agent_message: { icon: ArrowRight, color: "text-indigo-500", bg: "bg-indigo-50" },
  execution_done: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-50" },
};

export function LiveFeed({ events, connected }) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">Live Events</h3>
        <span className={`text-xs flex items-center gap-1.5 ${connected ? "text-green-600" : "text-red-500"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-green-500" : "bg-red-400"}`} />
          {connected ? "connected" : "disconnected"}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2">
        {events.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">Waiting for events...</p>
        )}
        {events.map((ev, i) => {
          const cfg = EVENT_CONFIG[ev.event] ?? { icon: Zap, color: "text-gray-400", bg: "bg-gray-50" };
          const Icon = cfg.icon;
          return (
            <div key={i} className={`flex items-start gap-2 rounded-lg ${cfg.bg} px-3 py-2`}>
              <Icon size={13} className={`${cfg.color} mt-0.5 shrink-0`} />
              <div className="min-w-0 text-xs text-gray-600">
                {ev.event === "agent_start" && <span>Agent <b>{ev.data.agent}</b> started</span>}
                {ev.event === "agent_message" && (
                  <span><b>{ev.data.from}</b> → <b>{ev.data.to}</b>
                    {ev.data.tokens > 0 && <span className="ml-1 text-gray-400">{ev.data.tokens} tokens</span>}
                  </span>
                )}
                {ev.event === "execution_done" && <span>Execution #{ev.data.execution_id} complete</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
