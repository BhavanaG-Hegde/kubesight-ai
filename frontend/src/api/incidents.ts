import { apiRequest } from "./client";
import type { IncidentListResponse, IncidentRead, IncidentStatus } from "../types/domain";

export interface IncidentFilters {
  status?: string;
  severity?: string;
  incident_type?: string;
  namespace?: string;
  pod_name?: string;
  search?: string;
}

export function getIncidents(filters: IncidentFilters = {}): Promise<IncidentListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  params.set("limit", "100");
  return apiRequest<IncidentListResponse>(`/api/v1/incidents?${params.toString()}`);
}

export interface IncidentUpdatePayload {
  status?: IncidentStatus;
  root_cause?: string;
  recommendation?: string;
  resolution?: string;
}

export function getIncident(incidentId: string): Promise<IncidentRead> {
  return apiRequest<IncidentRead>(`/api/v1/incidents/${incidentId}`);
}

export function updateIncident(
  incidentId: string,
  payload: IncidentUpdatePayload,
): Promise<IncidentRead> {
  return apiRequest<IncidentRead>(`/api/v1/incidents/${incidentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateIncidentStatus(
  incidentId: string,
  status: IncidentStatus,
): Promise<IncidentRead> {
  return updateIncident(incidentId, { status });
}

export function syncNamespaceIncidents(namespace: string): Promise<unknown> {
  return apiRequest(`/api/v1/incidents/sync/namespaces/${encodeURIComponent(namespace)}`, {
    method: "POST",
  });
}
