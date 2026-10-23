# Testing

One command runs everything: `make test` (or `scripts/test-all.sh` where `make`
is not installed). CI runs the same suites on every pull request and push.

| Suite | Kind | Where | Runs against | Command |
|---|---|---|---|---|
| Backend unit | unit | `backend/tests/unit/` | FastAPI `TestClient`, in-memory SQLite per test | `cd backend && uv run pytest -q tests/unit` |
| Backend integration | integration | `backend/tests/integration/` | a real `uvicorn` process over HTTP, SQLite file locally / **Postgres in CI** (`INTEGRATION_DATABASE_URL`) - full card lifecycle, persistence across a server restart, CORS | `cd backend && uv run pytest -q tests/integration` |
| Frontend | unit + component | `frontend/src/*.test.js(x)` | Vitest + Testing Library + jsdom, API mocked: rendering the board, error states, creating a card through the modal, optimistic delete rollback, sprint math, `api.js` request shapes | `cd frontend && npm test` |
| Post-deploy smoke | end to end | `scripts/smoke-test.sh` | the deployed system through nginx: page, board, create, move, delete | run by `scripts/deploy.sh` |
| On-call responder | unit | `incident-response/tests/` | fake evidence + fake agent: test alerts, full fix flow, unverified fix escalated, failed redeploy escalated, dedup | `cd incident-response && uv run pytest -q` |
| MCP server | unit | `mcp-server/test_server.py` | mocked Boardly API and responder | `cd mcp-server && uv run pytest -q test_server.py` |
| Guardrail hooks | unit | `agent-hooks/tests/` | `guard.py` as a subprocess with real hook payloads | `make test-hooks` |

Conventions:

- Backend endpoints are written test-first.
- Tests never touch the dev database (`boardly.db`) or a running Compose stack.
- A bug fix comes with a regression test that fails without the fix (the on-call
  agent follows the same rule - see `test_move_card_to_every_column`, added by the
  agent during the incident in [`on-call.md`](on-call.md)).
