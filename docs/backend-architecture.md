# Backend Architecture

The backend follows a layered architecture so Kubernetes integration, incident
detection, AI analysis, and persistence can evolve independently.

## Layers

```text
API routes
  -> schemas
  -> services
  -> repositories
  -> SQLAlchemy models
  -> PostgreSQL
```

## Responsibilities

- `api`: HTTP routes, dependencies, request validation, response models.
- `schemas`: Pydantic objects used at API boundaries.
- `services`: business logic such as auth, Kubernetes collection, health scoring,
  incident detection, analytics, and AI analysis.
- `repositories`: database reads and writes. Services should not contain raw query
  details once repository classes are introduced.
- `models`: SQLAlchemy ORM entities.
- `core`: settings, logging, security, exceptions, and shared infrastructure.
- `workers`: scheduled or background jobs for metric collection and incident scans.

## Planned Services

- `AuthService`: registration, login, password hashing, JWT issuing.
- `KubernetesService`: namespaces, deployments, pods, services, events, logs.
- `MetricsService`: cluster and pod resource collection.
- `HealthScoringService`: pod and cluster health scores.
- `IncidentDetectionService`: rule-based incident detection.
- `MonitoringService`: orchestration for live health assessment and detection.
- `AIAssistantService`: Ollama-backed explanations and troubleshooting steps.
- `AnalyticsService`: dashboard aggregates and chart-ready series.

## API Principles

- All public routes are versioned under `/api/v1`.
- Route handlers stay thin and delegate business decisions to services.
- Pydantic schemas validate all request and response bodies.
- Domain errors are represented with custom exceptions and mapped to HTTP errors.
- Configuration comes from environment variables, never hardcoded production values.
