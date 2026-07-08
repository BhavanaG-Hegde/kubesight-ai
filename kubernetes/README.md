# Kubernetes Deployment

This directory contains Kubernetes manifests for running KubeSight AI on a local
Minikube or Kind cluster.

## Layout

- `base/`: KubeSight AI platform manifests for frontend, backend, Postgres, and
  Ollama.
- `rbac/`: read-only Kubernetes permissions used by the backend service account.
- `sample-apps/`: intentionally unhealthy workloads for incident detection demos.

## Prerequisites

- A running Kubernetes cluster from Minikube or Kind.
- `kubectl` configured for that cluster.
- Docker available for building the local frontend and backend images.
- Optional: Metrics Server installed if you want CPU and memory metrics.

## Build Images

For Minikube:

```bash
eval "$(minikube docker-env)"
docker build -f docker/backend.Dockerfile -t kubesight-ai-backend:local .
docker build \
  -f docker/frontend.Dockerfile \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  -t kubesight-ai-frontend:local \
  .
```

For Kind:

```bash
docker build -f docker/backend.Dockerfile -t kubesight-ai-backend:local .
docker build \
  -f docker/frontend.Dockerfile \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  -t kubesight-ai-frontend:local \
  .
kind load docker-image kubesight-ai-backend:local kubesight-ai-frontend:local
```

## Create Secrets

The manifests intentionally do not store real secrets. Create them in the
cluster before applying the base platform:

```bash
kubectl apply -f kubernetes/base/namespace.yaml
kubectl -n kubesight create secret generic kubesight-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="replace-this-password" \
  --from-literal=DATABASE_URL="postgresql+psycopg://kubesight:replace-this-password@kubesight-postgres:5432/kubesight"
```

Use the same Postgres password in both `POSTGRES_PASSWORD` and `DATABASE_URL`.

## Deploy Platform

```bash
kubectl apply -k kubernetes/base
kubectl -n kubesight get pods -w
```

Load the Ollama model after the Ollama pod is running:

```bash
kubectl -n kubesight get pods -l app.kubernetes.io/component=ollama
kubectl -n kubesight exec -it <ollama-pod-name> -- ollama pull llama3.2
```

## Open Locally

Use port forwarding for local demos:

```bash
kubectl -n kubesight port-forward svc/kubesight-backend 8000:8000
kubectl -n kubesight port-forward svc/kubesight-frontend 5173:80
```

Then open:

```text
http://localhost:5173
```

## Add Demo Incidents

```bash
kubectl apply -k kubernetes/sample-apps
kubectl get pods -n kubesight-samples -w
```

The dashboard should show failed pods, restart signals, log-based errors, and
incident candidates in the `kubesight-samples` namespace.

## Cleanup

```bash
kubectl delete -k kubernetes/sample-apps
kubectl delete -k kubernetes/base
```
