# Incident History

KubeSight AI stores detected incidents in PostgreSQL so operators can search,
acknowledge, resolve, and review previous failures.

## Flow

1. Monitoring endpoints detect incident candidates from live Kubernetes state.
2. Sync endpoints persist those candidates to PostgreSQL.
3. Existing active incidents are updated instead of duplicated.
4. Resolved incidents stay closed, so a future repeat creates a new history item.

## API Endpoints

All incident history endpoints require JWT authentication.

```text
GET   /api/v1/incidents
GET   /api/v1/incidents/{incident_id}
PATCH /api/v1/incidents/{incident_id}
POST  /api/v1/incidents/sync/namespaces/{namespace}
POST  /api/v1/incidents/sync/namespaces/{namespace}/pods/{pod_name}
```

## Search Filters

`GET /api/v1/incidents` supports:

- `status`
- `severity`
- `incident_type`
- `namespace`
- `pod_name`
- `search`
- `limit`
- `offset`

## Updating Incidents

Use `PATCH /api/v1/incidents/{incident_id}` to update:

- `status`
- `root_cause`
- `recommendation`
- `resolution`

When `status` is set to `resolved`, the backend automatically sets
`resolved_at`.

## Frontend Workflow

The incident list links each incident title to a detail page at:

```text
/incidents/{incident_id}
```

The detail page supports:

- Reviewing severity, status, type, source, first seen, last seen, and resolved
  timestamps.
- Opening the affected pod when namespace and pod context are available.
- Editing root cause, recommendation, resolution, and status.
- Resolving the incident from the detail page.
- Running AI analysis against the incident.
- Asking follow-up AI questions with the incident as context.
- Reviewing previous AI analyses saved for the incident.
