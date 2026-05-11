import ReactFlow, { Background, Controls, MiniMap, addEdge, useNodesState, useEdgesState } from "reactflow";
import "reactflow/dist/style.css";
import { useCallback, useEffect } from "react";
import { AgentNode } from "./AgentNode";

const nodeTypes = { agentNode: AgentNode };

export function WorkflowCanvas({ agents, nodes: initNodes, edges: initEdges, onChange }) {
  const agentMap = Object.fromEntries(agents.map((a) => [a.id, a]));

  const rfNodes = initNodes.map((n) => ({
    id: n.id, type: "agentNode", position: n.position,
    data: {
      label: agentMap[n.agent_id]?.name ?? `Agent ${n.agent_id}`,
      role: agentMap[n.agent_id]?.role ?? "",
      tools: agentMap[n.agent_id]?.tools ?? [],
      agent_id: n.agent_id,
    },
  }));

  const rfEdges = initEdges.map((e) => ({
    id: e.id, source: e.source, target: e.target,
    animated: true, style: { stroke: "#6366f1", strokeWidth: 2 },
  }));

  const [rfNodeState, setRfNodes, onNodesChange] = useNodesState(rfNodes);
  const [rfEdgeState, setRfEdges, onEdgesChange] = useEdgesState(rfEdges);

  const onConnect = useCallback(
    (conn) => setRfEdges((eds) => addEdge({ ...conn, animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } }, eds)),
    [setRfEdges]
  );

  useEffect(() => {
    onChange(
      rfNodeState.map((n) => ({ id: n.id, agent_id: n.data.agent_id, position: n.position })),
      rfEdgeState.map((e) => ({ id: e.id, source: e.source, target: e.target }))
    );
  }, [rfNodeState, rfEdgeState]);

  const addAgent = (agent) => {
    const id = `node-${Date.now()}`;
    setRfNodes((ns) => [...ns, {
      id, type: "agentNode",
      position: { x: 80 + ns.length * 220, y: 180 },
      data: { label: agent.name, role: agent.role, tools: agent.tools, agent_id: agent.id },
    }]);
  };

  return (
    <div className="flex h-full gap-4">
      <div className="flex flex-col gap-2 w-40 shrink-0">
        <p className="text-xs text-gray-500 font-medium mb-1">Add agents</p>
        {agents.map((a) => (
          <button key={a.id} onClick={() => addAgent(a)}
            className="border border-gray-200 bg-white rounded-lg px-3 py-2 text-left hover:border-indigo-400 hover:shadow-sm transition-all">
            <span className="text-xs font-medium text-gray-800 block">{a.name}</span>
            <span className="text-xs text-gray-400">{a.role}</span>
          </button>
        ))}
      </div>
      <div className="flex-1 rounded-lg border border-gray-200 overflow-hidden bg-gray-50">
        <ReactFlow nodes={rfNodeState} edges={rfEdgeState}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect} nodeTypes={nodeTypes} fitView>
          <Background color="#e5e7eb" gap={20} />
          <Controls />
          <MiniMap nodeColor="#6366f1" />
        </ReactFlow>
      </div>
    </div>
  );
}
