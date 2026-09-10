import { apiFetch } from "./client";
import type {
  AgentConfigCreateRequest,
  AgentConfigResponse,
  AgentConfigUpdateRequest,
  AgentCreateRequest,
  AgentResponse,
  AgentUpdateRequest,
} from "./types";

export function listAgents(): Promise<AgentResponse[]> {
  return apiFetch<AgentResponse[]>("/agents");
}

export function createAgent(body: AgentCreateRequest): Promise<AgentResponse> {
  return apiFetch<AgentResponse>("/agents", { method: "POST", body });
}

export function updateAgent(agentId: string, body: AgentUpdateRequest): Promise<AgentResponse> {
  return apiFetch<AgentResponse>(`/agents/${agentId}`, { method: "PATCH", body });
}

export function createAgentConfig(
  agentId: string,
  body: AgentConfigCreateRequest,
): Promise<AgentConfigResponse> {
  return apiFetch<AgentConfigResponse>(`/agents/${agentId}/config`, { method: "POST", body });
}

export function getAgentConfig(agentId: string): Promise<AgentConfigResponse> {
  return apiFetch<AgentConfigResponse>(`/agents/${agentId}/config`);
}

export function updateAgentConfig(
  agentId: string,
  body: AgentConfigUpdateRequest,
): Promise<AgentConfigResponse> {
  return apiFetch<AgentConfigResponse>(`/agents/${agentId}/config`, { method: "PATCH", body });
}

export function deleteAgent(agentId: string): Promise<void> {
  return apiFetch<void>(`/agents/${agentId}`, { method: "DELETE" });
}
