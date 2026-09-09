import { apiFetch } from "./client";
import type { ResearchAcceptedResponse, ResearchRequest, ResearchResponse } from "./types";

export function listResearch(): Promise<ResearchResponse[]> {
  return apiFetch<ResearchResponse[]>("/research");
}

export function createResearch(body: ResearchRequest): Promise<ResearchAcceptedResponse> {
  return apiFetch<ResearchAcceptedResponse>("/research", { method: "POST", body });
}

export function deleteResearch(researchId: string): Promise<void> {
  return apiFetch<void>(`/research/${researchId}`, { method: "DELETE" });
}
