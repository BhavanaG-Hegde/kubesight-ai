# KubeSight AI

KubeSight AI is a Kubernetes health monitoring and incident prediction platform.
It is designed as a production-quality portfolio project that combines
cloud-native observability, backend engineering, DevOps, and local AI assistance.

## Project Goal

Build a lightweight observability platform for Kubernetes clusters that can:

- Monitor pods, namespaces, deployments, services, logs, events, CPU, and memory.
- Calculate health scores for workloads.
- Detect incidents such as CrashLoopBackOff, OOMKilled, ImagePullBackOff, high CPU,
  high memory, restart spikes, timeout errors, and database connection failures.
- Store incident history and analytics.
- Use Ollama with Llama 3.2 to explain logs and suggest troubleshooting steps.

## Tech Stack

- Frontend: React, TypeScript, Material UI, React Query, React Router, Recharts
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL
- Kubernetes: Kubernetes Python Client, Minikube or Kind
- AI: Ollama, Llama 3.2
- Infrastructure: Docker, Docker Compose, Kubernetes manifests
- CI/CD: GitHub Actions, Dependabot

## Repository Structure

```text
frontend/              React TypeScript dashboard
backend/               FastAPI application
docker/                Docker-related configuration
kubernetes/            Kubernetes manifests and sample workloads
docs/                  Architecture and planning documents
.github/workflows/     CI/CD pipelines
```

See [docs/folder-structure.md](docs/folder-structure.md) for the complete planned
folder layout.

## Build Roadmap

1. Design folder structure.
2. Design database schema.
3. Design backend architecture.
4. Create the FastAPI backend.
5. Create the React frontend.
6. Add authentication.
7. Add Kubernetes integration.
8. Add monitoring, health scoring, and incident detection.
9. Add AI log analysis.
10. Add analytics, Docker, Kubernetes manifests, CI, and documentation.

## Status

Current phase: Kubernetes deployment manifests and demo incident workloads.

## Backend Quickstart

Start PostgreSQL:

```bash
cp .env.example .env
docker compose up -d postgres
```

Run the backend locally:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Run backend through Docker Compose:

```bash
docker compose --profile app up --build
```

Run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Run on Kubernetes:

```bash
kubectl apply -f kubernetes/base/namespace.yaml
kubectl -n kubesight create secret generic kubesight-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="replace-this-password" \
  --from-literal=DATABASE_URL="postgresql+psycopg://kubesight:replace-this-password@kubesight-postgres:5432/kubesight"
kubectl apply -k kubernetes/base
kubectl apply -k kubernetes/sample-apps
```

Health check:

```text
GET http://localhost:8000/api/v1/health
```

Authentication:

```text
POST http://localhost:8000/api/v1/auth/register
POST http://localhost:8000/api/v1/auth/login
POST http://localhost:8000/api/v1/auth/token
GET  http://localhost:8000/api/v1/auth/me
```

Kubernetes inspection:

```text
GET http://localhost:8000/api/v1/kubernetes/summary
GET http://localhost:8000/api/v1/kubernetes/namespaces
GET http://localhost:8000/api/v1/kubernetes/namespaces/{namespace}/pods
GET http://localhost:8000/api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}/logs
```

Monitoring and incident detection:

```text
GET http://localhost:8000/api/v1/monitoring/namespaces/{namespace}/health
GET http://localhost:8000/api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/health
GET http://localhost:8000/api/v1/monitoring/namespaces/{namespace}/incidents/detect
GET http://localhost:8000/api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/incidents/detect
```

Incident history:

```text
GET   http://localhost:8000/api/v1/incidents
GET   http://localhost:8000/api/v1/incidents/{incident_id}
PATCH http://localhost:8000/api/v1/incidents/{incident_id}
POST  http://localhost:8000/api/v1/incidents/sync/namespaces/{namespace}
POST  http://localhost:8000/api/v1/incidents/sync/namespaces/{namespace}/pods/{pod_name}
```

AI assistant:

```text
GET  http://localhost:8000/api/v1/ai/analyses
GET  http://localhost:8000/api/v1/ai/analyses/{analysis_id}
POST http://localhost:8000/api/v1/ai/pods/logs/analyze
POST http://localhost:8000/api/v1/ai/incidents/{incident_id}/analyze
POST http://localhost:8000/api/v1/ai/ask
```

## Architecture Docs

- [Folder structure](docs/folder-structure.md)
- [Backend architecture](docs/backend-architecture.md)
- [Database schema](docs/database-schema.md)
- [Kubernetes integration](docs/kubernetes-integration.md)
- [Health scoring and incident detection](docs/monitoring-rules.md)
- [Incident history](docs/incident-history.md)
- [AI assistant](docs/ai-assistant.md)
- [CI/CD](docs/ci-cd.md)
- [Kubernetes deployment](kubernetes/README.md)
