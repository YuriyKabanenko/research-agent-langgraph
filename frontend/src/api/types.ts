// Mirrors the Pydantic models in server/models/*.py 1:1. Keep in sync by hand -
// there's no shared schema generation between the two sides.

export type ResearchMode = "quick" | "thorough";

export type ModelFamily = "anthropic" | "openai" | "google";

export type ResearchStatus = "pending" | "running" | "completed" | "failed";

// --- auth_models.py ---

export interface RegisterRequest {
  name: string;
  password: string;
}

export interface RegisterResponse {
  user_id: string;
  name: string;
  token: string;
}

export interface LoginRequest {
  name: string;
  password: string;
}

export interface LoginResponse {
  token: string;
}

// --- agent_models.py ---

export interface AgentCreateRequest {
  name: string;
}

export interface AgentUpdateRequest {
  name: string;
}

export interface AgentResponse {
  id: string;
  name: string;
  user_id: string;
  has_config: boolean;
}

export interface AgentConfigCreateRequest {
  research_mode: ResearchMode;
  retry_max_count: number;
  critique_threshold: number;
  api_token: string;
  model_family: ModelFamily;
  model_name: string;
}

export interface AgentConfigUpdateRequest {
  research_mode: ResearchMode;
  retry_max_count: number;
  critique_threshold: number;
  // Omit or leave blank to keep the existing token.
  api_token?: string;
}

export interface AgentConfigResponse {
  agent_id: string;
  research_mode: ResearchMode;
  retry_max_count: number;
  critique_threshold: number;
  model_family: ModelFamily;
  model_name: string;
}

// --- research_models.py ---

export interface ResearchRequest {
  topic: string;
  agent_id: string;
}

export interface ResearchAcceptedResponse {
  id: string;
  status: ResearchStatus;
}

export interface ResearchResponse {
  id: string;
  topic: string;
  status: ResearchStatus;
  research: string | null;
  tools_used: string[] | null;
  research_rate: number | null;
  error_message: string | null;
  created_at: string;
  agent_name: string;
}
