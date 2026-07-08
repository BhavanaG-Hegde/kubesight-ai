import { apiRequest } from "./client";
import type { MetricsCollectionResponse } from "../types/domain";

export function collectMetrics(): Promise<MetricsCollectionResponse> {
  return apiRequest<MetricsCollectionResponse>("/api/v1/metrics/collect", {
    method: "POST",
  });
}
