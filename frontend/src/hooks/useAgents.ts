import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as agentsApi from "../api/agents";
import type { AgentConfigCreateRequest, AgentCreateRequest } from "../api/types";

export function useAgents() {
  return useQuery({ queryKey: ["agents"], queryFn: agentsApi.listAgents });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AgentCreateRequest) => agentsApi.createAgent(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useCreateAgentConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, body }: { agentId: string; body: AgentConfigCreateRequest }) =>
      agentsApi.createAgentConfig(agentId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => agentsApi.deleteAgent(agentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });
}
