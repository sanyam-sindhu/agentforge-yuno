import { GitFork, Search, MessageSquare, ArrowRight } from "lucide-react";
import { useWorkflows } from "../hooks/useWorkflow";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { useNavigate } from "react-router-dom";

const TEMPLATES = [
  {
    id: "research_report",
    name: "Research + Report",
    description: "Research any topic on the web and produce a structured markdown report.",
    icon: Search,
    agents: ["Research Agent", "Writer Agent"],
    tools: ["web_search", "scrape_url"],
  },
  {
    id: "customer_support_triage",
    name: "Triage + Respond",
    description: "Classify incoming messages by intent and route to a specialist for a response.",
    icon: MessageSquare,
    agents: ["Triage Agent", "Specialist Agent"],
    tools: ["web_search"],
  },
];

export function TemplatesPage() {
  const { data: workflows = [] } = useWorkflows();
  const navigate = useNavigate();

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Templates</h1>
        <p className="text-sm text-gray-500 mt-0.5">Pre-built workflow templates ready to use</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-3xl">
        {TEMPLATES.map(({ id, name, description, icon: Icon, agents, tools }) => {
          const existing = workflows.find((w) => w.template_id === id);
          return (
            <div key={id} className="card p-5 flex flex-col gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-indigo-50 p-2.5 shrink-0">
                  <Icon size={18} className="text-indigo-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{name}</h3>
                    {existing && <Badge label="installed" color="green" />}
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{description}</p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 flex-wrap">
                {agents.map((a, i) => (
                  <div key={a} className="flex items-center gap-1.5">
                    <Badge label={a} color="blue" />
                    {i < agents.length - 1 && <ArrowRight size={12} className="text-gray-400" />}
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-1.5">
                {tools.map((t) => <Badge key={t} label={t} color="gray" />)}
              </div>

              <div className="mt-auto">
                {existing ? (
                  <Button variant="secondary" size="sm" onClick={() => navigate("/workflows")}>
                    <GitFork size={13} /> Open Workflow
                  </Button>
                ) : (
                  <p className="text-xs text-gray-400 italic">Auto-installed on startup</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
