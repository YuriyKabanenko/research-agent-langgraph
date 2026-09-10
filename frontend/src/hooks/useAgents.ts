import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as agentsApi from "../api/agents";
import type {
  AgentConfigCreateRequest,
  AgentConfigUpdateRequest,
  AgentCreateRequest,
  AgentUpdateRequest,
} from "../api/types";

export function useAgents() {
  return useQuery({ queryKey: ["agents"], queryFn: agentsApi.listAgents });
}

export function useAgentConfig(agentId?: string) {
  return useQuery({
    queryKey: ["agents", agentId, "config"],
    queryFn: () => agentsApi.getAgentConfig(agentId as string),
    enabled: !!agentId,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AgentCreateRequest) => agentsApi.createAgent(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, body }: { agentId: string; body: AgentUpdateRequest }) =>
      agentsApi.updateAgent(agentId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useUpdateAgentConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, body }: { agentId: string; body: AgentConfigUpdateRequest }) =>
      agentsApi.updateAgentConfig(agentId, body),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: ["agents", variables.agentId, "config"] }),
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
