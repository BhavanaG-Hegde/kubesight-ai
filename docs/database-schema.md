# Database Schema

KubeSight AI uses PostgreSQL as the source of truth for users, Kubernetes object
snapshots, metrics, logs, incidents, and AI-generated analysis.

## Tables

### `users`

Stores authenticated application users.

- `id`
- `email`
- `full_name`
- `hashed_password`
- `role`
- `is_active`
- `created_at`
- `updated_at`

### `clusters`

Represents a monitored Kubernetes cluster or local context.

- `id`
- `name`
- `context_name`
- `api_server`
- `status`
- `last_seen_at`
- `created_at`
- `updated_at`

### `kubernetes_namespaces`

Stores namespaces discovered from a cluster.

- `id`
- `cluster_id`
- `name`
- `labels`
- `created_at`
- `updated_at`

Unique key: `cluster_id`, `name`.

### `deployments`

Stores deployment-level inventory and replica state.

- `id`
- `namespace_id`
- `name`
- `desired_replicas`
- `available_replicas`
- `labels`
- `selector`
- `created_at`
- `updated_at`

### `kubernetes_services`

Stores Kubernetes service inventory.

- `id`
- `namespace_id`
- `name`
- `service_type`
- `cluster_ip`
- `ports`
- `labels`
- `created_at`
- `updated_at`

### `pods`

Stores the latest known pod state.

- `id`
- `namespace_id`
- `name`
- `node_name`
- `phase`
- `health_status`
- `health_score`
- `restart_count`
- `ready_containers`
- `total_containers`
- `cpu_millicores`
- `memory_mebibytes`
- `reason`
- `message`
- `owner_kind`
- `owner_name`
- `labels`
- `annotations`
- `last_seen_at`
- `created_at`
- `updated_at`

Unique key: `namespace_id`, `name`.

### `pod_metrics`

Stores time-series resource samples for pods.

- `id`
- `pod_id`
- `cpu_millicores`
- `memory_mebibytes`
- `cpu_limit_millicores`
- `memory_limit_mebibytes`
- `sampled_at`
- `created_at`
- `updated_at`

### `cluster_snapshots`

Stores dashboard-ready cluster aggregate samples.

- `id`
- `cluster_id`
- `total_pods`
- `running_pods`
- `pending_pods`
- `failed_pods`
- `restart_count`
- `cpu_millicores`
- `memory_mebibytes`
- `health_score`
- `sampled_at`

### `pod_events`

Stores Kubernetes events associated with pods.

- `id`
- `pod_id`
- `event_uid`
- `event_type`
- `reason`
- `message`
- `source_component`
- `count`
- `first_seen_at`
- `last_seen_at`
- `created_at`
- `updated_at`

Unique key: `pod_id`, `event_uid`.

### `log_entries`

Stores important log lines and searchable log excerpts. The live log viewer can
stream directly from Kubernetes, while this table keeps incident-relevant logs.

- `id`
- `pod_id`
- `container_name`
- `severity`
- `message`
- `fingerprint`
- `observed_at`
- `created_at`

### `incidents`

Stores detected operational incidents.

- `id`
- `cluster_id`
- `namespace_id`
- `pod_id`
- `incident_type`
- `severity`
- `status`
- `title`
- `summary`
- `root_cause`
- `recommendation`
- `detection_source`
- `first_seen_at`
- `last_seen_at`
- `resolved_at`
- `created_at`
- `updated_at`

### `ai_analyses`

Stores Ollama-generated explanations for incidents, logs, or user questions.

- `id`
- `incident_id`
- `pod_id`
- `model_name`
- `question`
- `prompt`
- `response`
- `created_at`
- `updated_at`

## Indexing Strategy

- Users are indexed by `email`.
- Clusters are indexed by `name`.
- Namespaces, deployments, services, and pods are indexed by Kubernetes names.
- Pod metrics and cluster snapshots are indexed by `sampled_at`.
- Logs are indexed by `observed_at`, `severity`, and `fingerprint`.
- Incidents are indexed by `status`, `severity`, `incident_type`, and foreign keys.

## Retention Plan

Initial development keeps all records. A later production phase should add data
retention jobs, for example:

- Raw log excerpts: 7 to 14 days.
- Pod metrics: 30 days.
- Cluster snapshots: 90 days.
- Incidents and AI analyses: permanent unless deleted by an admin.
