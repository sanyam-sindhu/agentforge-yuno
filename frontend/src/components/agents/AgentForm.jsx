import { useState } from "react";
import { Button } from "../ui/Button";

const AVAILABLE_TOOLS = ["web_search", "scrape_url", "http_request"];
const MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"];

export function AgentForm({ initial = {}, onSubmit, loading }) {
  const [form, setForm] = useState({
    name: "", role: "", system_prompt: "", model: "gpt-4o-mini",
    tools: [], memory_enabled: false, channel: null, ...initial,
  });

  const toggleTool = (tool) => {
    const tools = form.tools ?? [];
    setForm((f) => ({
      ...f,
      tools: tools.includes(tool) ? tools.filter((t) => t !== tool) : [...tools, tool],
    }));
  };

  const label = (text, children) => (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{text}</label>
      {children}
    </div>
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(form); }} className="space-y-4">
      {label("Name",
        <input className="input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
      )}
      {label("Role",
        <input className="input" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} required />
      )}
      {label("Model",
        <select className="input" value={form.model} onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}>
          {MODELS.map((m) => <option key={m}>{m}</option>)}
        </select>
      )}
      {label("System Prompt",
        <textarea rows={4} className="input resize-none font-mono text-xs"
          value={form.system_prompt}
          onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))} required />
      )}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">Tools</label>
        <div className="flex flex-wrap gap-2">
          {AVAILABLE_TOOLS.map((tool) => (
            <button key={tool} type="button" onClick={() => toggleTool(tool)}
              className={`px-3 py-1 text-xs rounded-md border transition-colors ${
                (form.tools ?? []).includes(tool)
                  ? "bg-indigo-600 border-indigo-600 text-white"
                  : "bg-white border-gray-300 text-gray-600 hover:border-indigo-400"
              }`}>
              {tool}
            </button>
          ))}
        </div>
      </div>
      <label className="flex items-center gap-2.5 cursor-pointer">
        <input type="checkbox" checked={form.memory_enabled}
          onChange={(e) => setForm((f) => ({ ...f, memory_enabled: e.target.checked }))}
          className="w-4 h-4 accent-indigo-600" />
        <span className="text-sm text-gray-700">Enable memory</span>
      </label>
      <Button type="submit" disabled={loading} className="w-full justify-center">
        {loading ? "Saving..." : "Save Agent"}
      </Button>
    </form>
  );
}
