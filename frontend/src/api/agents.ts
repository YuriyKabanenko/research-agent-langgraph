import { apiFetch } from "./client";
import type {
  AgentConfigCreateRequest,
  AgentConfigResponse,
  AgentCreateRequest,
  AgentResponse,
} from "./types";

export function listAgents(): Promise<AgentResponse[]> {
  return apiFetch<AgentResponse[]>("/agents");
}

export function createAgent(body: AgentCreateRequest): Promise<AgentResponse> {
  return apiFetch<AgentResponse>("/agents", { method: "POST", body });
}

export function createAgentConfig(
  agentId: string,
  body: AgentConfigCreateRequest,
): Promise<AgentConfigResponse> {
  return apiFetch<AgentConfigResponse>(`/agents/${agentId}/config`, { method: "POST", body });
}

export function deleteAgent(agentId: string): Promise<void> {
  return apiFetch<void>(`/agents/${agentId}`, { method: "DELETE" });
}
