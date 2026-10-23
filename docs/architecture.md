# Architecture

```
 Browser
   |  http://localhost:8080 (Compose)  /  Service "frontend" (Kubernetes)
   v
 frontend  (nginx: built React app + reverse proxy)
   |  /api/*  -> prefix stripped ->
   v
 backend   (FastAPI, uvicorn, 2 replicas in Kubernetes)
   |  SQLAlchemy
   v
 postgres  (SQLite in unit/integration tests)

 backend --OTLP--> otel-collector --> prometheus (metrics)
                                  --> loki       (logs)
                                  --> tempo      (traces)
                    grafana (dashboard + alert rule) --webhook--> incident responder (host)
                                                                    --> claude -p (sandboxed)
```

## Code layout

| Path | What |
|---|---|
| `frontend/src/api.js` | the only module that calls the network; same-origin `/api` |
| `frontend/src/App.jsx`, `components/` | board, columns, cards (drag and drop via `@dnd-kit`), modal, summary bar |
| `frontend/nginx.conf.template` | serves the build, proxies `/api/` to `$BACKEND_URL` |
| `openapi.yaml` | the contract between the two |
| `backend/src/boardly_backend/main.py` | routes, health/readiness, request metrics + logs middleware |
| `backend/src/boardly_backend/store.py` | `CardStore`: all database access |
| `backend/src/boardly_backend/telemetry.py` | OpenTelemetry traces, metrics, logs |
| `compose.yaml` | the whole system on one machine, one command |
| `k8s/` | Postgres, backend and frontend manifests (namespace per environment) |
| `scripts/deploy.sh` | deploy + smoke test + automatic rollback |
| `observability/` | Collector, Prometheus, Loki, Tempo, Grafana (dashboard + alert) |
| `incident-response/` | alert webhook -> evidence -> on-call agent -> redeploy -> verify |
| `mcp-server/` | MCP server exposing the board and incident log to coding agents |
| `agent-hooks/`, `.claude/` | guardrail hooks, subagents, skills, permissions |

## Key user journey

"Move a card to another column": `PATCH /api/cards/{id}/move` from the browser
-> nginx -> FastAPI route -> `CardStore.update` -> Postgres. This is the path the
alert watches, the drill breaks, and the on-call agent fixes.
