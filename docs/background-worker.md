# Background Worker

KubeSight AI includes an optional backend worker that runs inside the FastAPI
process. It is managed by the application lifespan, starts when the API starts,
and shuts down cleanly with the API.

## Jobs

The worker runs two periodic jobs:

- Metrics collection: stores a `cluster_snapshots` row and pod metric samples.
- Incident scanning: scans Kubernetes namespaces, detects rule-based incidents,
  and persists new or updated incident history records.

## Configuration

The worker is disabled by default for local development. Enable it with:

```env
BACKGROUND_WORKER_ENABLED=true
```

Supported settings:

```env
METRICS_COLLECTION_INTERVAL_SECONDS=60
INCIDENT_SCAN_INTERVAL_SECONDS=120
INCIDENT_SCAN_NAMESPACES=
INCIDENT_SCAN_EXCLUDED_NAMESPACES=kube-system,kube-public,kube-node-lease,kubesight
INCIDENT_SCAN_INCLUDE_LOGS=true
INCIDENT_SCAN_TAIL_LINES=200
```

If `INCIDENT_SCAN_NAMESPACES` is empty, the worker discovers all namespaces and
skips the excluded namespace list. Set it to a comma-separated list such as
`default,kubesight-samples` for a tighter demo scan.

## Kubernetes Deployment

The base Kubernetes manifests enable the worker by default because the backend
pod has in-cluster Kubernetes credentials through the `kubesight-backend`
service account.

For local Docker Compose usage, keep the worker disabled unless the backend
container has access to a valid kubeconfig.

## Operational Notes

- Metrics Server is required for CPU and memory samples.
- Incident scanning can include logs, which is useful for timeout/database
  detection but more expensive than state-only scans.
- In multi-replica API deployments, run only one worker-enabled backend replica
  or move the worker into a separate deployment to avoid duplicate collection
  runs.
