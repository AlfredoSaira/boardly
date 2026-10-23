# Permissions and security

Principle: least privilege per actor, enforced in code or configuration - a
prompt is guidance, not a control.

## Coding agents in this repo (Claude Code)

| Actor | May | May not | Enforced by |
|---|---|---|---|
| Main agent | read and edit code, run tests and linters, read the board and incidents via MCP, read GitHub issues | read `.env*` (except `.env.example`), kubeconfig or keys; edit incident evidence; edit `openapi.yaml` without a contract review; `rm -rf`, force push, `git reset --hard`, `kubectl delete`, dropping volumes or tables | `agent-hooks/guard.py` (PreToolUse), `.claude/settings.json` `deny` |
| Main agent | commit, push, create/comment/close issues, `docker compose`, `kubectl`, deploy, create or move cards via MCP | do any of these without asking the human first | `.claude/settings.json` `ask` |
| `api-contract-reviewer` | Read, Grep, Glob, `git diff/log/show` | edit anything, run anything else | `tools:` in its frontmatter |
| `qa-tester` | read; edit test files only; run test commands | change application code | `tools:` in its frontmatter (`Edit(backend/tests/**)`, `Edit(frontend/src/**/*.test.*)`) |
| Hooks | format and lint the edited file; append to `agent-hooks/logs/audit.jsonl` | network access, reading secrets | code review of `agent-hooks/`, tests in `agent-hooks/tests/` |

## MCP server (`mcp-server/server.py`)

- Talks only to the Boardly `/api` and the responder's incident endpoints.
- Read-only tools (`get_board`, `list_incidents`, `get_incident`) are allowed
  without prompting; the two write tools (`create_card`, `move_card`) need approval.
- **No delete tool.** An agent can add or move work, never destroy it.
- Ids are validated before they are put in a URL; user text is truncated to 300
  characters per field and documented as untrusted data.
- Only the `boardly` server from `.mcp.json` is enabled (`enableAllProjectMcpServers: false`).

## On-call agent (headless)

See [`on-call.md`](on-call.md) and
[`incident-response/autonomy-policy.yaml`](../incident-response/autonomy-policy.yaml):
starts with no tools, edits only `backend/src/**` and `backend/tests/**`, can only
run pytest, the verification script and read-only git; no docker, no git writes,
no web; budget and time capped; its result is verified by code and reviewed by a
human before commit.

## Application and infrastructure

- No secrets in git: the Compose Postgres password is a local default that can be
  overridden with `POSTGRES_PASSWORD`; in Kubernetes it is generated per
  environment by `scripts/deploy.sh` and kept in a Secret.
- All Compose ports bind to `127.0.0.1`. The incident webhook binds to loopback and
  the Docker bridge only.
- Containers run as non-root (backend user `boardly`, `nginx-unprivileged`).
- Telemetry carries no user content (see [`observability.md`](observability.md)).
- CI has no production credentials; prod deploys need a human approval in the
  `production` GitHub environment.
