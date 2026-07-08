# Folder Structure

This project is intentionally split into independent frontend, backend,
infrastructure, Kubernetes, and documentation areas.

```text
kubernetes_log_analyzer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/
│       ├── assets/
│       ├── components/
│       ├── features/
│       ├── hooks/
│       ├── layouts/
│       ├── pages/
│       ├── routes/
│       ├── theme/
│       ├── types/
│       └── utils/
├── docker/
├── kubernetes/
│   ├── base/
│   ├── rbac/
│   └── sample-apps/
├── docs/
└── .github/
    └── workflows/
```

## Backend

- `api/v1`: FastAPI routers and route dependencies.
- `core`: configuration, logging, security, and shared exceptions.
- `db`: SQLAlchemy database session, migrations, and base metadata.
- `models`: SQLAlchemy ORM models.
- `schemas`: Pydantic request and response schemas.
- `repositories`: database access layer.
- `services`: business logic such as auth, Kubernetes collection, health scoring,
  incident detection, analytics, and AI analysis.
- `workers`: background collection or scheduled incident detection jobs.
- `tests`: backend test suite.

## Frontend

- `api`: HTTP clients and React Query functions.
- `components`: reusable UI components.
- `features`: domain modules such as auth, dashboard, explorer, logs, incidents,
  analytics, and AI assistant.
- `hooks`: shared React hooks.
- `layouts`: application shells and protected layouts.
- `pages`: route-level pages.
- `routes`: React Router definitions and route guards.
- `theme`: Material UI theme configuration.
- `types`: shared TypeScript types.
- `utils`: formatting, constants, and helpers.

## Infrastructure

- `docker`: Docker support files.
- `kubernetes/base`: application deployment manifests.
- `kubernetes/rbac`: Kubernetes read-only access permissions for the backend.
- `kubernetes/sample-apps`: sample workloads used to generate realistic pod states
  and logs during development.
- `.github/workflows`: CI/CD workflows.
