import { apiRequest } from "./client";
import type {
  ClusterSummary,
  DeploymentRead,
  NamespaceRead,
  PodEventRead,
  PodHealthAssessmentRead,
  PodLogRead,
  PodRead,
  ServiceRead,
} from "../types/domain";

export function getClusterSummary(): Promise<ClusterSummary> {
  return apiRequest<ClusterSummary>("/api/v1/kubernetes/summary");
}

export function getNamespaces(): Promise<NamespaceRead[]> {
  return apiRequest<NamespaceRead[]>("/api/v1/kubernetes/namespaces");
}

export function getDeployments(namespace: string): Promise<DeploymentRead[]> {
  return apiRequest<DeploymentRead[]>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/deployments`,
  );
}

export function getServices(namespace: string): Promise<ServiceRead[]> {
  return apiRequest<ServiceRead[]>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/services`,
  );
}

export function getPods(namespace: string): Promise<PodRead[]> {
  return apiRequest<PodRead[]>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
}

export function getPod(namespace: string, podName: string): Promise<PodRead> {
  return apiRequest<PodRead>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(
      podName,
    )}`,
  );
}

export function getPodEvents(namespace: string, podName: string): Promise<PodEventRead[]> {
  return apiRequest<PodEventRead[]>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(
      podName,
    )}/events`,
  );
}

export function getPodLogs(namespace: string, podName: string): Promise<PodLogRead> {
  return apiRequest<PodLogRead>(
    `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(
      podName,
    )}/logs?tail_lines=300&timestamps=true`,
  );
}

export function getPodHealth(
  namespace: string,
  podName: string,
): Promise<PodHealthAssessmentRead> {
  return apiRequest<PodHealthAssessmentRead>(
    `/api/v1/monitoring/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(
      podName,
    )}/health?include_logs=true`,
  );
}
