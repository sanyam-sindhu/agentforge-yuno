import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { agentsApi } from "../lib/api";

export function useAgents() {
  return useQuery({ queryKey: ["agents"], queryFn: agentsApi.list });
}

export function useCreateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => agentsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useUpdateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => agentsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useDeleteAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => agentsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}
