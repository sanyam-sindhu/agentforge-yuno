import axios from "axios";

const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

const http = axios.create({ baseURL: BASE });

export const agentsApi = {
  list: () => http.get("/agents").then((r) => r.data),
  create: (data) => http.post("/agents", data).then((r) => r.data),
  update: (id, data) => http.put(`/agents/${id}`, data).then((r) => r.data),
  delete: (id) => http.delete(`/agents/${id}`),
};

export const workflowsApi = {
  list: () => http.get("/workflows").then((r) => r.data),
  create: (data) => http.post("/workflows", data).then((r) => r.data),
  update: (id, data) => http.put(`/workflows/${id}`, data).then((r) => r.data),
  delete: (id) => http.delete(`/workflows/${id}`),
};

export const executionsApi = {
  list: (workflowId) =>
    http.get("/executions", { params: workflowId ? { workflow_id: workflowId } : {} }).then((r) => r.data),
  create: (workflowId, inputText) =>
    http.post("/executions", { workflow_id: workflowId, input_text: inputText }).then((r) => r.data),
};

export const messagesApi = {
  list: (executionId) =>
    http.get("/messages", { params: executionId ? { execution_id: executionId } : {} }).then((r) => r.data),
};
