# Observability

Everything is OpenTelemetry, shipped through one Collector, stored in
Prometheus (metrics), Loki (logs) and Tempo (traces), and viewed in Grafana.
Setup: [`backend/src/boardly_backend/telemetry.py`](../backend/src/boardly_backend/telemetry.py),
[`observability/`](../observability/).

## The instrumented journey

Every board API request (load board, create, edit, move, delete card) produces:

| Signal | What | Where |
|---|---|---|
| Trace | FastAPI server span + one child span per SQL statement (SQLAlchemy instrumentation) | Tempo, service `boardly-backend` |
| Metric | `boardly_http_requests_total{http_route, http_method, http_status_code}` | Prometheus |
| Metric | `boardly_http_request_duration_milliseconds` histogram by route/method | Prometheus |
| Log | one structured record per request: route, method, status, duration, `card_id`, **`trace_id`, `span_id`** | Loki (and JSON on stdout) |

The log record carries the trace id of the request, so in Grafana a log line
links straight to its trace (Loki derived field -> Tempo) and a trace links back
to its logs (Tempo `tracesToLogs` -> Loki). Health checks (`/healthz`, `/readyz`)
are excluded so they do not drown the user traffic.

Real output of these queries from a local run, showing one failed request's log line
and the trace with the same id: [`evidence/observability-queries.md`](evidence/observability-queries.md).

## Privacy

Card **titles and descriptions never leave the app as telemetry**: only route
templates (`/cards/{card_id}/move`, never the raw path with user input), methods,
status codes, durations and opaque card ids. A unit test
(`test_request_logs_are_json_and_never_contain_card_content`) creates a card
with a secret title and asserts it appears in no log line. No credentials are
sent either: the database URL is never logged.

## Dashboard

http://localhost:3000/d/boardly/boardly (provisioned from
`observability/grafana/dashboards/boardly.json`):

- requests per second by route and status code;
- failed board actions (5xx) in the last 5 minutes;
- error ratio;
- p95 latency per route;
- recent error traces (Tempo);
- backend logs (click a `trace_id` to open the trace).

## Alert on user impact

`observability/grafana/provisioning/alerting/rules.yaml` - **Board actions failing (5xx)**:

```promql
sum(increase(boardly_http_requests_total{http_status_code=~"5.."}[5m])) or vector(0)  > 0   for 1m
```

A 5xx on the board API means a user tried to load the board or create, edit,
move or delete a card and **their change was not saved**. That is the impact the
alert pages on - not CPU or memory. 4xx (a user typo, a card that was already
deleted) does not page. The contact point is a webhook to the on-call responder
(see [`on-call.md`](on-call.md)).
