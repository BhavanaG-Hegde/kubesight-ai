import { apiRequest } from "./client";
import type { AIAnalysisListResponse, AIAnalysisRead } from "../types/domain";

export interface AskAIPayload {
  question: string;
  incident_id?: string;
  namespace?: string;
  pod_name?: string;
  include_logs?: boolean;
}

export function askAI(payload: AskAIPayload): Promise<AIAnalysisRead> {
  return apiRequest<AIAnalysisRead>("/api/v1/ai/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAIAnalyses(incidentId?: string): Promise<AIAnalysisListResponse> {
  const params = new URLSearchParams({ limit: "20" });
  if (incidentId) {
    params.set("incident_id", incidentId);
  }
  return apiRequest<AIAnalysisListResponse>(`/api/v1/ai/analyses?${params.toString()}`);
}

export function analyzeIncident(incidentId: string): Promise<AIAnalysisRead> {
  return apiRequest<AIAnalysisRead>(`/api/v1/ai/incidents/${incidentId}/analyze`, {
    method: "POST",
    body: JSON.stringify({ include_pod_logs: true }),
  });
}
