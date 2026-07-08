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
- Resource trends from persisted cluster snapshots.
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
Historical resource charts use `cluster_snapshots` written by metric collection.

## Metric Collection

Trigger a collection pass with:

```text
POST /api/v1/metrics/collect
```

The collector stores:

- One `cluster_snapshots` row per collection run.
- One `pod_metrics` row per pod when Metrics Server data is available.
- Current CPU, memory, restart, health score, and phase values on stored pod
  catalog records.

If Metrics Server is unavailable, the collector still stores pod state and a
cluster snapshot with zero CPU/memory totals, and returns a warning explaining
that Metrics Server is required for resource samples.
