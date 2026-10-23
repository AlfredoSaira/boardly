# Observability evidence (local Compose stack, 2026-10-22)

## Prometheus: requests by route and status over the last 3 hours (includes the incident drill's 500s)
```
/board 200 43
/cards 201 42
/cards/{card_id} 200 38
/cards/{card_id} 204 36
/cards/{card_id}/move 200 98
/cards/{card_id}/move 404 0
/cards/{card_id}/move 500 21
```

## Loki: one structured log line for a 500 during the drill (labels include trace_id)
```
{
  "service_name": "boardly-backend",
  "deployment_environment": "local",
  "http_method": "PATCH",
  "http_route": "/cards/{card_id}/move",
  "http_status_code": "500",
  "duration_ms": "2.79",
  "card_id": "b326d43b-9e62-4ee2-9906-030d1329ecac",
  "trace_id": "01b0e577893aa8929f58a381c8d5dc08",
  "span_id": "aabe5800632068cd",
  "severity_text": "ERROR"
}
body: board api request
```

## Tempo: the trace with that same trace_id (01b0e577893aa8929f58a381c8d5dc08)
```
PATCH /cards/{card_id}/move http receive         0.01 ms  status=
PATCH /cards/{card_id}/move http send            0.02 ms  status=STATUS_CODE_ERROR
PATCH /cards/{card_id}/move http send            0.01 ms  status=
PATCH /cards/{card_id}/move                      4.94 ms  status=STATUS_CODE_ERROR
connect                                          0.08 ms  status=
SELECT boardly                                   0.41 ms  status=
```
