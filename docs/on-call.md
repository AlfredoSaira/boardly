# On-call agent

An agent wakes up on the Grafana alert, finds the bug from production evidence,
fixes it with a regression test, and the system - not the model - redeploys and
verifies the recovery. Code: [`incident-response/`](../incident-response/).

```
Grafana alert "Board actions failing (5xx)"
   │ webhook POST /alerts  (host.docker.internal:8001, loopback/Docker networks only)
   v
responder.py ── evidence.py: Prometheus (requests by route/status), Loki (5xx log lines
   │                         with card ids + trace ids), Tempo (error traces)
   │── prompt = responder-task.md + alert + evidence (marked as data, not instructions)
   v
agent_runner.py: claude -p --restricted --permission-mode dontAsk
   │   Edit only backend/src/** and backend/tests/**
   │   Bash only: pytest, verify-recovery.sh, git status/diff/log
   │   no docker, no git writes, no web; --max-budget-usd 2; 15 min timeout
   v
answer: ROOT_CAUSE / FIX / TESTS / ACTION (none | fixed | escalate) / SUMMARY
   │ if ACTION=fixed:
   ├── runbooks/redeploy.sh        (responder rebuilds the backend container)
   └── runbooks/verify-recovery.sh (responder replays the full card journey 3x)
          pass -> "recovered" (diff waits for human review)   fail -> "escalated"
```

Every step is written to `incident-response/incidents/<id>/`: the alert, the
evidence (JSON + Markdown), the exact prompt, the agent's full transcript, its
answer, the redeploy output and the verification output.

## Run it

```bash
docker compose up -d --build --wait                       # app + observability
cd incident-response && uv run --frozen python responder.py   # needs a logged-in `claude` CLI
# in another terminal:
scripts/incident-drill.sh start      # ship a buggy change and send traffic
curl -s localhost:8001/incidents     # watch the incident appear and resolve
scripts/incident-drill.sh reset      # back to the pre-drill code
```

## The drill

`scripts/incident-drill.sh start` applies
[`scenarios/move-activity-log.patch`](../incident-response/scenarios/move-activity-log.patch):
a realistic change that logs a human-readable column name on every move, with a
typo in its lookup table (`"to_do"` instead of `"todo"`). Before the incident no
test moved a card into To Do, so the change passed the existing test suite. In
production every drag into **To Do** returned 500 and the user's move was lost.

## A real run (2026-10-22)

Incident [`20261022T231740Z-board-actions-failing-5xx`](../incident-response/incidents/20261022T231740Z-board-actions-failing-5xx/):

| Time (UTC) | Status | Note |
|---|---|---|
| 23:17:40 | received | firing alert Board actions failing (5xx) |
| 23:17:40 | evidence_collected | 35 error logs, 5 error traces, failing routes: `PATCH /cards/{card_id}/move` |
| 23:17:40 | agent_running | claude --restricted, sandboxed to backend/src/ and backend/tests/ |
| 23:18:16 | agent_done | action=fixed exit=0 |
| 23:18:16 | redeploying | rebuilding the backend container with the agent's fix |
| 23:18:26 | recovered | verify-recovery.sh passed; fix awaits human review before commit |

The agent's answer ([`answer.json`](../incident-response/incidents/20261022T231740Z-board-actions-failing-5xx/answer.json)):

> **ROOT_CAUSE:** COLUMN_LABELS in store.py used the key "to_do" while the column id is "todo", so every move into To Do raised a KeyError while writing the "card moved" log line and returned a 500.
>
> **FIX:** backend/src/boardly_backend/store.py changed the COLUMN_LABELS key "to_do" to "todo"; backend/tests/unit/test_cards.py added test_move_card_to_every_column as a regression test.
>
> **TESTS:** uv run --directory backend --frozen pytest -q -> 17 passed (the new test failed with KeyError before the fix)

46 seconds from alert to verified recovery; 11 agent turns; US$0.14; zero permission
denials. **Human review:** the regression test was kept in the repository
(`test_move_card_to_every_column`); the faulty change itself was reverted rather
than fixed, so the drill can be replayed - and with that test in place, the same
change can no longer pass CI.

## Safety

Policy in [`autonomy-policy.yaml`](../incident-response/autonomy-policy.yaml); enforced
by the CLI flags in `agent_runner.py` and by `responder.py`:

- the agent starts with no tools (`--restricted`) and only the listed ones are re-added;
- anything else is denied automatically (`dontAsk`) - there is no human to ask;
- deploying and verifying are done by code after the agent answers; the agent's
  "fixed" is never trusted on its own;
- alert and evidence text is framed as data, never instructions (prompt injection);
- the webhook only listens on loopback and Docker's bridge, with a payload size limit
  and a 5-minute dedup per alert;
- the fix is never committed or pushed by the agent.
