import { useState } from "react";
import { Plus, Play, Save } from "lucide-react";
import { useAgents } from "../hooks/useAgents";
import { useWorkflows, useCreateWorkflow, useUpdateWorkflow, useRunWorkflow } from "../hooks/useWorkflow";
import { WorkflowCanvas } from "../components/workflows/WorkflowCanvas";
import { Modal } from "../components/ui/Modal";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

export function WorkflowsPage() {
  const { data: workflows = [] } = useWorkflows();
  const { data: agents = [] } = useAgents();
  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const runWorkflow = useRunWorkflow();

  const [selected, setSelected] = useState(null);
  const [canvasNodes, setCanvasNodes] = useState([]);
  const [canvasEdges, setCanvasEdges] = useState([]);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [createModal, setCreateModal] = useState(false);
  const [runModal, setRunModal] = useState(false);
  const [runInput, setRunInput] = useState("");
  const [runTarget, setRunTarget] = useState(null);

  const openWorkflow = (wf) => { setSelected(wf); setCanvasNodes(wf.graph_json.nodes); setCanvasEdges(wf.graph_json.edges); };

  return (
    <div className="flex h-full">
      <div className="w-56 border-r border-gray-200 p-4 flex flex-col gap-2 overflow-y-auto bg-white">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-gray-800">Workflows</h2>
          <Button size="sm" variant="ghost" onClick={() => setCreateModal(true)}><Plus size={14} /></Button>
        </div>
        {workflows.map((wf) => (
          <div key={wf.id} onClick={() => openWorkflow(wf)}
            className={`rounded-lg border p-3 cursor-pointer transition-colors ${
              selected?.id === wf.id ? "border-indigo-300 bg-indigo-50" : "border-gray-200 hover:border-gray-300"
            }`}>
            <p className="text-sm font-medium text-gray-800">{wf.name}</p>
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{wf.description}</p>
            <div className="flex items-center gap-2 mt-2">
              {wf.template_id && <Badge label="template" color="yellow" />}
              <button onClick={(e) => { e.stopPropagation(); setRunTarget(wf); setRunModal(true); }}
                className="ml-auto text-gray-400 hover:text-green-600 transition-colors">
                <Play size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex-1 flex flex-col">
        {selected ? (
          <>
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-3 bg-white">
              <span className="text-sm font-semibold text-gray-800">{selected.name}</span>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary"
                  onClick={() => updateWorkflow.mutateAsync({ id: selected.id, data: { graph_json: { nodes: canvasNodes, edges: canvasEdges } } })}
                  disabled={updateWorkflow.isPending}>
                  <Save size={13} /> {updateWorkflow.isPending ? "Saving..." : "Save"}
                </Button>
                <Button size="sm" onClick={() => { setRunTarget(selected); setRunModal(true); }}>
                  <Play size={13} /> Run
                </Button>
              </div>
            </div>
            <div className="flex-1 p-4">
              <WorkflowCanvas key={selected.id} agents={agents} nodes={canvasNodes} edges={canvasEdges}
                onChange={(n, e) => { setCanvasNodes(n); setCanvasEdges(e); }} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
            Select or create a workflow
          </div>
        )}
      </div>

      <Modal open={createModal} onClose={() => setCreateModal(false)} title="New Workflow">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
            <input className="input" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <input className="input" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
          </div>
          <Button onClick={async () => {
            const wf = await createWorkflow.mutateAsync({ name: newName, description: newDesc, graph_json: { nodes: [], edges: [] } });
            setCreateModal(false); setNewName(""); setNewDesc(""); openWorkflow(wf);
          }} disabled={!newName || createWorkflow.isPending} className="w-full justify-center">
            Create
          </Button>
        </div>
      </Modal>

      <Modal open={runModal} onClose={() => setRunModal(false)} title={`Run — ${runTarget?.name}`}>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Input</label>
            <textarea rows={3} className="input resize-none" placeholder="Enter your prompt..."
              value={runInput} onChange={(e) => setRunInput(e.target.value)} />
          </div>
          <Button onClick={async () => {
            await runWorkflow.mutateAsync({ workflowId: runTarget.id, inputText: runInput });
            setRunModal(false); setRunInput("");
          }} disabled={!runInput || runWorkflow.isPending} className="w-full justify-center">
            {runWorkflow.isPending ? "Running..." : "Run Workflow"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
