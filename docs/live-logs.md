# Live Logs

KubeSight AI supports authenticated live pod log streaming through a
Server-Sent Events endpoint.

## API

```text
GET /api/v1/kubernetes/namespaces/{namespace}/pods/{pod_name}/logs/stream
```

Query parameters:

- `container`: optional container name.
- `tail_lines`: initial tail before following new logs, default `100`.
- `previous`: read previous container logs, default `false`.
- `timestamps`: include Kubernetes timestamps, default `true`.

The response uses `text/event-stream` and emits JSON payloads:

```text
event: log
data: {"line":"2026-07-08T12:00:00Z ERROR timeout while calling payment-service"}
```

If Kubernetes interrupts the stream, the API emits an `error` event with a
`detail` field.

## Frontend

The pod detail page includes:

- Start and stop streaming controls.
- Live buffer capped to the latest 1,000 lines.
- Search filtering.
- Severity filtering.
- Timestamp range filtering.
- Clear live buffer action.

The frontend uses `fetch` instead of browser `EventSource` so the JWT bearer
token can be sent in the `Authorization` header.
