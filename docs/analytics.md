# Analytics

KubeSight AI exposes chart-ready analytics from stored incident history and the
latest pod catalog data.

## API

```text
GET /api/v1/analytics/overview?days=30
```

The endpoint requires JWT authentication and accepts a `days` window from `1` to
`90`.

## Included Views

- Incident trends by day.
- Severity distribution.
- Incident status distribution.
- Incident type and error distribution.
- Top failing pods by incident count.
- Top CPU pods from the latest pod catalog state.
- Top memory pods from the latest pod catalog state.
- Top restarting pods from the latest pod catalog state.

## Data Sources

Incident charts are based on persisted rule-based incidents. CPU, memory, and
restart charts use the latest pod records already stored by the catalog layer.
Full historical resource charts will become richer once scheduled metric
collection writes recurring `cluster_snapshots` and `pod_metrics` records.
