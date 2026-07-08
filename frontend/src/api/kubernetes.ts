import { ApiError, apiRequest, apiUrl, getStoredToken } from "./client";
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

interface StreamPodLogsOptions {
  tailLines?: number;
  timestamps?: boolean;
  previous?: boolean;
  container?: string | null;
}

interface StreamPodLogsCallbacks {
  onLine: (line: string) => void;
  onError?: (message: string) => void;
}

export async function streamPodLogs(
  namespace: string,
  podName: string,
  options: StreamPodLogsOptions,
  signal: AbortSignal,
  callbacks: StreamPodLogsCallbacks,
): Promise<void> {
  const params = new URLSearchParams({
    tail_lines: String(options.tailLines ?? 100),
    timestamps: String(options.timestamps ?? true),
    previous: String(options.previous ?? false),
  });
  if (options.container) {
    params.set("container", options.container);
  }

  const headers = new Headers();
  const token = getStoredToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    apiUrl(
      `/api/v1/kubernetes/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(
        podName,
      )}/logs/stream?${params.toString()}`,
    ),
    { headers, signal },
  );

  if (!response.ok) {
    throw new ApiError(response.statusText || "Unable to stream logs", response.status);
  }
  if (!response.body) {
    throw new Error("Log stream is unavailable in this browser.");
  }

  await readServerSentEvents(response.body, callbacks, signal);
}

async function readServerSentEvents(
  body: ReadableStream<Uint8Array>,
  callbacks: StreamPodLogsCallbacks,
  signal: AbortSignal,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const event of events) {
        handleServerSentEvent(event, callbacks);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function handleServerSentEvent(event: string, callbacks: StreamPodLogsCallbacks): void {
  const lines = event.split("\n");
  const eventType = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  if (!data) {
    return;
  }

  const payload = JSON.parse(data) as { line?: string; detail?: string };
  if (eventType === "error") {
    callbacks.onError?.(payload.detail ?? "Log stream failed.");
    return;
  }
  if (payload.line !== undefined) {
    callbacks.onLine(payload.line);
  }
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
