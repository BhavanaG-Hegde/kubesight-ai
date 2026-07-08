# Kubernetes Integration

KubeSight AI reads Kubernetes data through the official Kubernetes Python client.
The backend supports two modes:

- Local development: load a kubeconfig from `KUBECONFIG_PATH` or the default
  kubeconfig location.
- In-cluster deployment: use the service account mounted into the backend pod.

## Environment

```env
KUBECONFIG_PATH=/path/to/kubeconfig
KUBERNETES_CONTEXT=minikube
```

Both variables are optional. If neither is set, the backend first tries in-cluster
configuration and then falls back to the default local kubeconfig.

## API Endpoints

All Kubernetes endpoints require JWT authentication.

```text
GET /api/v1/kubernetes/summary
GET /api/v1/kubernetes/namespaces
GET /api/v1/kubernetes/namespaces/{namespace}/deployments
GET /api/v1/kubernetes/namespaces/{namespace}/services
GET /api/v1/kubernetes/namespaces/{namespace}/pods
GET /api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}
GET /api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}/events
GET /api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}/logs
GET /api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}/logs/stream
```

## RBAC

The read-only service account manifest lives at:

```text
kubernetes/rbac/kubesight-readonly.yaml
```

It grants access to:

- Namespaces
- Pods and pod logs
- Pod status
- Services and endpoints
- Events
- Deployments and related workload resources
- Metrics API pods and nodes for upcoming CPU and memory endpoints

Apply it after creating the `kubesight` namespace:

```bash
kubectl create namespace kubesight
kubectl apply -f kubernetes/rbac/kubesight-readonly.yaml
```

## Deployment Manifests

The deployable Kubernetes platform lives in:

```text
kubernetes/base
```

It includes:

- `kubesight` namespace
- Backend deployment and service
- Frontend deployment and service
- Postgres StatefulSet and service
- Ollama StatefulSet and service
- Read-only backend RBAC

Secrets are not committed. Create `kubesight-secrets` before applying the base
manifests:

```bash
kubectl apply -f kubernetes/base/namespace.yaml
kubectl -n kubesight create secret generic kubesight-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="replace-this-password" \
  --from-literal=DATABASE_URL="postgresql+psycopg://kubesight:replace-this-password@kubesight-postgres:5432/kubesight"
kubectl apply -k kubernetes/base
```

The full deployment runbook is in [kubernetes/README.md](../kubernetes/README.md).

## Demo Workloads

The `kubernetes/sample-apps` package creates intentionally unhealthy workloads
for local demos:

- CrashLoopBackOff
- OOMKilled
- ImagePullBackOff
- Timeout and database error logs
- High CPU usage

Apply them with:

```bash
kubectl apply -k kubernetes/sample-apps
```

## Local Checklist

1. Start Minikube or Kind.
2. Confirm the cluster is reachable:

```bash
kubectl get namespaces
```

3. Set `KUBECONFIG_PATH` or rely on the default kubeconfig.
4. Register and log in through the auth API.
5. Call `GET /api/v1/kubernetes/namespaces` with the bearer token.
6. Apply `kubernetes/sample-apps` to generate realistic incident signals.
