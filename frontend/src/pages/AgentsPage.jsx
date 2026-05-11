import { useState } from "react";
import { Plus } from "lucide-react";
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent } from "../hooks/useAgents";
import { AgentCard } from "../components/agents/AgentCard";
import { AgentForm } from "../components/agents/AgentForm";
import { Modal } from "../components/ui/Modal";
import { Button } from "../components/ui/Button";

export function AgentsPage() {
  const { data: agents = [], isLoading } = useAgents();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();
  const deleteAgent = useDeleteAgent();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const handleSubmit = async (data) => {
    editing ? await updateAgent.mutateAsync({ id: editing.id, data }) : await createAgent.mutateAsync(data);
    setModalOpen(false);
    setEditing(null);
  };

  const handleDelete = async () => {
    await deleteAgent.mutateAsync(confirmDelete.id);
    setConfirmDelete(null);
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Agents</h1>
          <p className="text-sm text-gray-500 mt-0.5">Create and configure AI agents</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true); }}>
          <Plus size={15} /> New Agent
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent}
              onEdit={(a) => { setEditing(a); setModalOpen(true); }}
              onDelete={(id) => setConfirmDelete(agents.find(a => a.id === id))} />
          ))}
          {agents.length === 0 && (
            <div className="col-span-3 text-center py-16 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-xl">
              No agents yet — create your first one
            </div>
          )}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }}
        title={editing ? "Edit Agent" : "New Agent"}>
        <AgentForm initial={editing || {}} onSubmit={handleSubmit}
          loading={createAgent.isPending || updateAgent.isPending} />
      </Modal>

      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Delete Agent">
        <p className="text-sm text-gray-600 mb-5">
          Are you sure you want to delete <span className="font-semibold text-gray-900">{confirmDelete?.name}</span>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button variant="danger" onClick={handleDelete} disabled={deleteAgent.isPending}>
            {deleteAgent.isPending ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
