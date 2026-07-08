# KubeSight AI Backend

FastAPI backend for Kubernetes monitoring, incident detection, analytics, and AI
log analysis.

## Local Development

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
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
