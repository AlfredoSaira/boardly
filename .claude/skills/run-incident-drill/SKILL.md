---
name: run-incident-drill
description: Run the Boardly on-call drill end to end (bad change -> alert -> on-call agent fix -> redeploy -> verification) and report the result. Use when asked to demo, test, or debug the alerting and the on-call agent.
---

# Run the incident drill

Preconditions (check, do not assume):
- `docker compose ps` shows backend, frontend, postgres, grafana, prometheus,
  loki, tempo and otel-collector up. If not, ask the human to run `docker compose up -d --build --wait`.
- The responder answers: `curl -s localhost:8001/healthz`. If not, ask the human
  to start it in another terminal: `cd incident-response && uv run --frozen python responder.py`.
- `git status` is clean under `backend/src/` so the drill patch applies.

Steps:
1. `scripts/incident-drill.sh start` - applies `incident-response/scenarios/move-activity-log.patch`,
   rebuilds the backend, and sends traffic (expect `failed(5xx)` > 0).
2. Wait for the alert (about 1-2 minutes). Poll with the `list_incidents` MCP tool
   (or `curl -s localhost:8001/incidents`), sending `scripts/incident-drill.sh traffic`
   every minute until an incident appears.
3. Poll `get_incident` until the status is `recovered`, `closed` or `escalated`.
4. Read `incident-response/incidents/<id>/answer.json` and `verification.json`.
5. Show the human `git diff backend/` - the agent's fix is **never** committed
   without a human reading it.
6. Report: timeline, root cause, fix, tests, verification output, agent cost.
7. If the human wants the board back to the pre-drill state: `scripts/incident-drill.sh reset`.
