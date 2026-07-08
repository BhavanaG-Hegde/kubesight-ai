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
- CI/CD: GitHub Actions

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

Current phase: backend foundation and database schema.

## Backend Quickstart

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Health check:

```text
GET http://localhost:8000/api/v1/health
```

## Architecture Docs

- [Folder structure](docs/folder-structure.md)
- [Backend architecture](docs/backend-architecture.md)
- [Database schema](docs/database-schema.md)
