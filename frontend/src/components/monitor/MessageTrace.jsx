import { useQuery } from "@tanstack/react-query";
import { messagesApi } from "../../lib/api";

export function MessageTrace({ executionId }) {
  const { data: messages = [] } = useQuery({
    queryKey: ["messages", executionId],
    queryFn: () => messagesApi.list(executionId),
    enabled: !!executionId,
    refetchInterval: 2000,
  });

  if (!executionId) return <p className="text-xs text-gray-400 text-center py-8">Select an execution to view messages</p>;

  return (
    <div className="space-y-2">
      {messages.map((msg) => (
        <div key={msg.id} className="border border-gray-100 rounded-lg bg-white p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-medium text-indigo-600">{msg.from_agent}</span>
            <span className="text-xs text-gray-400">→</span>
            <span className="text-xs font-medium text-gray-700">{msg.to_agent}</span>
            {msg.tokens_used > 0 && <span className="ml-auto text-xs text-gray-400">{msg.tokens_used} tokens</span>}
          </div>
          <p className="text-xs text-gray-500 line-clamp-3 whitespace-pre-wrap">{msg.content}</p>
        </div>
      ))}
      {messages.length === 0 && <p className="text-xs text-gray-400 text-center py-4">No messages yet</p>}
    </div>
  );
}
