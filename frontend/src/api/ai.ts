import { apiRequest } from "./client";
import type { AIAnalysisRead } from "../types/domain";

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

export function analyzeIncident(incidentId: string): Promise<AIAnalysisRead> {
  return apiRequest<AIAnalysisRead>(`/api/v1/ai/incidents/${incidentId}/analyze`, {
    method: "POST",
    body: JSON.stringify({ include_pod_logs: true }),
  });
}
