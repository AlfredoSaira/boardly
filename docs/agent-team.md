# Agent team

Five roles, three of them agents. Each agent has one job, a narrow set of tools,
and hands off through files, issues or diffs - never through shared hidden state.

| Role | Who | Responsibilities | Tools / limits | Defined in |
|---|---|---|---|---|
| Product owner | Human (Alfredo) | Decides scope, approves the spec, prioritises issues, approves production deploys, reviews every agent diff before it is committed | Everything | - |
| Planner / implementer | Claude Code, main interactive session | Turns the spec into issues with acceptance criteria; implements issues test-first; orchestrates the subagents; comments on issues; commits only when the human says so | Repo tools, guarded by hooks and `.claude/settings.json` (`ask` for commit/push/deploy, `deny` for secrets and destructive commands) | [`AGENTS.md`](../AGENTS.md), [`.claude/settings.json`](../.claude/settings.json) |
| API contract reviewer | Subagent | Reviews any change to `openapi.yaml`, schemas, routes or `api.js`; returns blocking / non-blocking findings | **Read-only**: Read, Grep, Glob, `git diff/log/show` | [`.claude/agents/api-contract-reviewer.md`](../.claude/agents/api-contract-reviewer.md) |
| QA tester | Subagent | Turns acceptance criteria into unit / integration / frontend tests and runs them; reports bugs instead of fixing app code | Edit **test files only**, run test commands | [`.claude/agents/qa-tester.md`](../.claude/agents/qa-tester.md) |
| On-call responder | Headless custom agent (`claude -p --restricted`) | Woken by a Grafana alert; reads evidence from Prometheus/Loki/Tempo; finds the root cause; fixes it with a regression test or escalates | Edits only `backend/src/**` and `backend/tests/**`; can run pytest and the verification script; no git writes, no docker, no network tools; budget and time capped | [`incident-response/`](../incident-response/), [`autonomy-policy.yaml`](../incident-response/autonomy-policy.yaml) |

## How they work together

```
human ──spec/priorities──> planner ──issues──> GitHub tracker
                              │
                              ├─ implements issue (test-first)
                              ├─> api-contract-reviewer (if the contract changes) ──findings──┐
                              ├─> qa-tester (acceptance criteria -> tests) ──results──────────┤
                              │<──────────────────────────────────────────────────────────────┘
                              └─ comments on issue, asks human to commit ──> CI/CD ──> dev ──(human approves)──> prod

Grafana alert ──> responder ──evidence──> on-call agent ──fix + test──> responder redeploys + verifies
                                                                      └──> human reviews diff, commits
```

Rules that keep the team safe:

- **Separation of duties:** the agent that writes code is never the only check on
  it - a read-only reviewer, the test suite, CI, and a human sit after it.
- **Code enforces permission, the model supplies judgement:** limits are in
  tool allowlists, hooks and CLI flags, not only in prompts.
- **Evidence over claims:** the responder re-verifies every "fixed" itself.
