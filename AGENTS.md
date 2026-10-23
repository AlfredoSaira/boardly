# Boardly - agent instructions

Boardly is a single-user mini kanban board (New / To Do / In Progress / Done):
React + Vite frontend, FastAPI backend, Postgres, OpenTelemetry + Grafana stack,
Kubernetes deploys via GitHub Actions, and a headless on-call agent that fixes
incidents from alerts.

## Read before working

| Topic | Doc |
|---|---|
| What we build (source of truth for scope) | [`_docs/specs.md`](_docs/specs.md) |
| How work flows from issue to production | [`docs/process.md`](docs/process.md) |
| Who does what (humans, agents, subagents) | [`docs/agent-team.md`](docs/agent-team.md) |
| Code layout and request path | [`docs/architecture.md`](docs/architecture.md) |
| Where each kind of test lives | [`docs/testing.md`](docs/testing.md) |
| Docker, Kubernetes, CI/CD, rollback | [`docs/deployment.md`](docs/deployment.md) |
| Metrics, traces, logs, dashboard, alert | [`docs/observability.md`](docs/observability.md) |
| Alert -> on-call agent -> verified recovery | [`docs/on-call.md`](docs/on-call.md) |
| What each agent may and may not do | [`docs/permissions.md`](docs/permissions.md) |
| Skills, subagents, hooks, MCP server | [`docs/agent-extension-pack.md`](docs/agent-extension-pack.md) |

## Commands

- `docker compose up -d --build --wait` - whole system: http://localhost:8080 (app), http://localhost:3000 (Grafana)
- `cd backend && uv run pytest -q` - backend unit + integration tests
- `cd backend && uv run ruff check . && uv run ruff format --check .` - backend lint
- `cd frontend && npm test` / `npm run lint` / `npm run build` - frontend tests, lint, build
- `cd frontend && npm run dev` - frontend dev server on :5173 (proxies `/api` to :8000)
- `cd backend && uv run fastapi dev src/boardly_backend/main.py` - backend dev server on :8000
- `make test` - every test suite (backend, frontend, responder, MCP server, hooks)
- `make deploy-local` - build images and deploy to a local kind cluster

## Rules

- `_docs/specs.md` is the source of truth for scope. Anything not in it is out of
  scope until the human asks for it explicitly.
- Every task is a GitHub issue with acceptance criteria. Reference it in commits
  (`Closes #N`) and comment on the issue with what was done and how it was tested.
- Tests before implementation for backend endpoints. Do not commit until all
  test suites pass.
- `openapi.yaml` changes go through the `review-api-change` skill (a hook enforces it).
- All frontend network calls go through `frontend/src/api.js`. The browser only
  ever calls the same-origin `/api` prefix.
- Keep the backend database-agnostic (SQLAlchemy; SQLite in tests, Postgres in
  Compose/Kubernetes).
- Telemetry never carries card titles or descriptions (user content).
- Never commit, push, deploy to production, or delete data without the human's OK.
