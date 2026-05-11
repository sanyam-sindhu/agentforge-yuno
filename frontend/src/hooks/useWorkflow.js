import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workflowsApi, executionsApi } from "../lib/api";

export function useWorkflows() {
  return useQuery({ queryKey: ["workflows"], queryFn: workflowsApi.list });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => workflowsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useUpdateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => workflowsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useDeleteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => workflowsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useExecutions(workflowId) {
  return useQuery({
    queryKey: ["executions", workflowId],
    queryFn: () => executionsApi.list(workflowId),
    refetchInterval: 3000,
  });
}

export function useRunWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, inputText }) => executionsApi.create(workflowId, inputText),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["executions"] }),
  });
}
