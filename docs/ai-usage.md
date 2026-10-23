# How AI was used

Boardly was built almost entirely by a coding agent (Claude Code), with a human
deciding scope and approving anything irreversible. This page explains how the
agents got context, what was delegated to whom, how generated code was
reviewed, and how results were verified, including the mistakes the agent made
and how they were caught.

## 1. Giving the agents context

| Context | Where | Why |
|---|---|---|
| Product scope | [`_docs/specs.md`](../_docs/specs.md) | Single source of truth: user stories, acceptance criteria, non-goals. Anything not in it is out of scope. |
| Project rules and commands | [`AGENTS.md`](../AGENTS.md) (`CLAUDE.md` imports it) | Loaded at the start of every session: how to run and test, and the rules (test-first, contract-first, no user content in telemetry, nothing irreversible without the human). |
| Modular docs | [`docs/`](.) | `AGENTS.md` stays short and points to one doc per topic, so an agent reads only what the task needs. |
| The task itself | [GitHub issues #1-#11](https://github.com/AlfredoSaira/boardly/issues?q=is%3Aissue) | Each issue has acceptance criteria as a checklist; the agent works one issue at a time. |
| The contract | [`openapi.yaml`](../openapi.yaml) | Frontend and backend are built against it, so neither side guesses the other. |
| Previous work | Module 3 (Kubernetes deploy) and module 4 (OpenTelemetry + on-call responder) repos | Reused deliberately instead of rewritten, then adapted to Boardly. |
| Production evidence (on-call) | [`incident-response/evidence.py`](../incident-response/evidence.py) | The on-call agent gets metrics, error logs and trace ids, marked as data, never as instructions. |

## 2. Delegating work

| Work | Delegated to | Human role |
|---|---|---|
| Choosing the project idea, column names, final-project base app | - | Decided by the human |
| Spec, issues and acceptance criteria | Main agent (draft) | Reviewed and approved |
| Implementation, tests, Docker, Kubernetes, CI/CD, telemetry, docs | Main agent, one issue at a time | Approved publishing (repo, commits, push) |
| API contract review | `api-contract-reviewer` subagent (read-only) | - |
| Turning acceptance criteria into tests | `qa-tester` subagent (tests only) | - |
| Fixing a production incident | Headless on-call agent, sandboxed | Reviews the diff before anything is committed |
| Production deploy | CI/CD pipeline | **Manual approval** in the `production` environment |

Roles, tools and hand-offs are detailed in [`agent-team.md`](agent-team.md).

## 3. Reviewing generated code

- **Guardrails in code, not in prompts:** hooks block secrets, destructive
  commands, unreviewed contract edits and edits to incident evidence
  ([`agent-hooks/guard.py`](../agent-hooks/guard.py)); `.claude/settings.json`
  makes commit, push, deploy and `kubectl` ask first.
- **Separate reviewer:** contract changes go through a read-only subagent, so
  the agent that writes the code is never the only check on it.
- **Human review of the on-call fix:** the agent's fix for the real incident was
  read before anything was kept. Decision: keep its regression test
  (`test_move_card_to_every_column`), revert the faulty change instead of keeping
  the patched version, so the drill stays repeatable and CI now catches that bug.
- **CI as the final reviewer:** every push runs lint and all test suites before
  anything is deployed.

## 4. Verifying the result

Nothing was considered done because the agent said so; each claim was checked
by running it:

| Claim | How it was verified |
|---|---|
| Backend works with a real database | Integration tests start a real uvicorn server over HTTP, run against SQLite and against Postgres 17 |
| One command starts everything | `docker compose down -v && docker compose up -d --build --wait` from scratch, then [`scripts/smoke-test.sh`](../scripts/smoke-test.sh) |
| Deploys are safe | A good deploy and a deliberately crashing image on a local kind cluster: the bad one was rolled back automatically ([evidence](evidence/)) |
| CI/CD works | [First GitHub Actions run](https://github.com/AlfredoSaira/boardly/actions/runs/39887620494): all jobs green, smoke tests passed in dev and in prod after manual approval |
| Logs, metrics and traces are connected | Queried Loki for a 500, took its `trace_id`, found the same trace in Tempo ([evidence](evidence/observability-queries.md)) |
| No user content in telemetry | Unit test with a secret card title, asserted absent from every log line |
| The on-call agent fixes real bugs | A real drill: alert -> agent fix + regression test -> redeploy -> independent verification in 46 s ([`on-call.md`](on-call.md)) |

## 5. Mistakes the agent made, and how they were caught

| Mistake | Caught by | Fix |
|---|---|---|
| Concatenated two Kubernetes YAML files without a `---` separator, so the backend Service was silently never created and the frontend crash-looped | The deploy's rollout check on kind, then reading the pod logs (`host not found in upstream "backend"`) | Apply each manifest separately |
| `kubectl apply` reset the image to `:local` before `set image`, adding an extra rollout revision, so a rollback went to the wrong version | Testing the rollback with a crashing image | Apply manifests with the new tag already substituted (one revision per deploy) |
| The first drill bug was caught by an existing test, so it could never have reached production: an unrealistic drill | Running the test suite with the patch applied | Moved the bug to a path no test covered (moving a card into To Do), which is exactly the gap the on-call agent then closed |
| A JSON log test failed because the log handler captured `sys.stdout` at import time | The test itself | Handler resolves `sys.stdout` when writing |
| Screenshots of Grafana could not be taken (Grafana does not boot in the headless browsers available) | Looking at the screenshots, which showed an error page | Replaced with the real output of the Prometheus, Loki and Tempo queries |

The module 2 version of this report (how the original app was built) is in
[`ai-usage-report.md`](ai-usage-report.md).
