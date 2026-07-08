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

## Local Checklist

1. Start Minikube or Kind.
2. Confirm the cluster is reachable:

```bash
kubectl get namespaces
```

3. Set `KUBECONFIG_PATH` or rely on the default kubeconfig.
4. Register and log in through the auth API.
5. Call `GET /api/v1/kubernetes/namespaces` with the bearer token.
