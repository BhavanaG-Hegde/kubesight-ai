export type UserRole = "admin" | "viewer";
export type HealthStatus = "healthy" | "warning" | "critical" | "unknown";
export type IncidentSeverity = "info" | "warning" | "critical";
export type IncidentStatus = "open" | "acknowledged" | "resolved";
export type IncidentType =
  | "crash_loop_back_off"
  | "oom_killed"
  | "image_pull_back_off"
  | "high_restart_count"
  | "high_cpu"
  | "high_memory"
  | "timeout_errors"
  | "database_connection_failure"
  | "error_log_spike"
  | "pod_not_ready";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface ClusterSummary {
  total_pods: number;
  running_pods: number;
  pending_pods: number;
  failed_pods: number;
  restart_count: number;
}

export interface NamespaceRead {
  name: string;
  status: string;
  labels: Record<string, string>;
}

export interface ContainerStatusRead {
  name: string;
  ready: boolean;
  restart_count: number;
  state: string;
  reason?: string | null;
}

export interface PodRead {
  name: string;
  namespace: string;
  phase: string;
  node_name?: string | null;
  pod_ip?: string | null;
  host_ip?: string | null;
  restart_count: number;
  ready_containers: number;
  total_containers: number;
  containers: ContainerStatusRead[];
  labels: Record<string, string>;
  annotations: Record<string, string>;
  created_at?: string | null;
}

export interface DeploymentRead {
  name: string;
  namespace: string;
  desired_replicas: number;
  ready_replicas: number;
  available_replicas: number;
  updated_replicas: number;
  labels: Record<string, string>;
  selector: Record<string, unknown>;
}

export interface ServiceRead {
  name: string;
  namespace: string;
  service_type?: string | null;
  cluster_ip?: string | null;
  ports: Array<{
    name?: string | null;
    protocol: string;
    port: number;
    target_port?: string | null;
    node_port?: number | null;
  }>;
  labels: Record<string, string>;
}

export interface PodEventRead {
  event_type: string;
  reason: string;
  message: string;
  source_component?: string | null;
  count: number;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface PodLogRead {
  namespace: string;
  pod_name: string;
  container?: string | null;
  tail_lines: number;
  lines: string[];
}

export interface HealthSignalRead {
  code: string;
  severity: IncidentSeverity;
  message: string;
  evidence?: string | null;
  score_impact: number;
}

export interface PodHealthAssessmentRead {
  namespace: string;
  pod_name: string;
  phase: string;
  health_status: HealthStatus;
  health_score: number;
  restart_count: number;
  ready_containers: number;
  total_containers: number;
  signals: HealthSignalRead[];
}

export interface IncidentRead {
  id: string;
  cluster_name: string;
  namespace?: string | null;
  pod_name?: string | null;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  title: string;
  summary: string;
  root_cause?: string | null;
  recommendation?: string | null;
  resolution?: string | null;
  detection_source: string;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentListResponse {
  total: number;
  limit: number;
  offset: number;
  items: IncidentRead[];
}

export interface AIAnalysisRead {
  id: string;
  incident_id?: string | null;
  pod_id?: string | null;
  model_name: string;
  question?: string | null;
  response: string;
  created_at: string;
}
