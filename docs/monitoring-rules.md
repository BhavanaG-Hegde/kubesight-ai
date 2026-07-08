# Health Scoring And Incident Detection

KubeSight AI now includes a rule-based monitoring layer that analyzes live pod
state, Kubernetes events, and recent logs.

## Health Score

Each pod starts at a score of `100`. Signals reduce the score based on operational
risk.

| Signal | Severity | Score Impact |
| --- | --- | --- |
| Failed pod phase | Critical | 45 |
| Pending pod phase | Warning | 15 |
| Unknown pod phase | Warning | 25 |
| Not all containers ready | Warning | 15 |
| Restart count >= 10 | Critical | Up to 35 |
| Restart count >= 3 | Warning | Up to 20 |
| CrashLoopBackOff | Critical | 35 |
| OOMKilled | Critical | 35 |
| ImagePullBackOff or ErrImagePull | Critical | 30 |
| Repeated error logs | Warning | Up to 20 |
| Timeout logs | Warning | Up to 20 |
| Database connectivity logs | Critical | Up to 30 |

## Health Labels

| Score | Label |
| --- | --- |
| 80-100 | Healthy |
| 50-79 | Warning |
| 0-49 | Critical |

## Incident Candidates

The detection engine returns incident candidates from live Kubernetes state.
Incident sync endpoints can persist these candidates into PostgreSQL for history,
search, and resolution tracking.

Detected incident types:

- CrashLoopBackOff
- OOMKilled
- ImagePullBackOff
- High restart count
- Timeout errors
- Database connection failures
- Error log spikes
- Pod not ready

## API Endpoints

All monitoring endpoints require JWT authentication.

```text
GET /api/v1/monitoring/namespaces/{namespace}/health
GET /api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/health
GET /api/v1/monitoring/namespaces/{namespace}/incidents/detect
GET /api/v1/monitoring/namespaces/{namespace}/pods/{pod_name}/incidents/detect
```

Persist detected incidents:

```text
POST /api/v1/incidents/sync/namespaces/{namespace}
POST /api/v1/incidents/sync/namespaces/{namespace}/pods/{pod_name}
```

Query parameters:

- `include_logs`: include recent pod logs in scoring. Defaults to `false` for
  namespace health and `true` for pod health and incident detection.
- `tail_lines`: number of recent log lines to inspect. Defaults to `200`.
