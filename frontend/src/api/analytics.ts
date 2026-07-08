import { apiRequest } from "./client";
import type { AnalyticsOverviewResponse } from "../types/domain";

export function getAnalyticsOverview(days = 30): Promise<AnalyticsOverviewResponse> {
  return apiRequest<AnalyticsOverviewResponse>(`/api/v1/analytics/overview?days=${days}`);
}
