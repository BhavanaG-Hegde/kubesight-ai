# KubeSight AI Backend

FastAPI backend for Kubernetes monitoring, incident detection, analytics, and AI
log analysis.

## Local Development

Start PostgreSQL from the repository root:

```bash
cp .env.example .env
docker compose up -d postgres
```

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Prefix

Versioned APIs live under:

```text
/api/v1
```

Current endpoint:

```text
GET /api/v1/health
```

Authentication endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/token
GET  /api/v1/auth/me
```

Kubernetes endpoints:

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

Monitoring endpoints:

```text
GET /api/v1/monitoring/namespaces/{namespace}/health
GET /api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/health
GET /api/v1/monitoring/namespaces/{namespace}/incidents/detect
GET /api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/incidents/detect
```
