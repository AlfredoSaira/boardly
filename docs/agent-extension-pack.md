# Agent extension pack (module 5)

How coding agents are extended and constrained in this repo. Files target
Claude Code; `AGENTS.md` and the MCP server work with any agent.

| Capability | Question it answers | Here |
|---|---|---|
| Project instructions | What is this repo, what are the rules? | [`AGENTS.md`](../AGENTS.md) (portable) + [`CLAUDE.md`](../CLAUDE.md) (imports it) + modular [`docs/`](.) |
| Reusable workflow (skills) | How do we always do X? | [`review-api-change`](../.claude/skills/review-api-change/SKILL.md), [`run-incident-drill`](../.claude/skills/run-incident-drill/SKILL.md) |
| Specialised subagents | Who does this side task, with which tools? | [`api-contract-reviewer`](../.claude/agents/api-contract-reviewer.md) (read-only), [`qa-tester`](../.claude/agents/qa-tester.md) (tests only) |
| MCP server | Which live data and actions may the agent use? | [`mcp-server/`](../mcp-server/): `get_board`, `create_card`, `move_card`, `list_incidents`, `get_incident`, prompt `plan-sprint`; registered in [`.mcp.json`](../.mcp.json) |
| Hooks / guardrails | What must always (or never) happen? | [`agent-hooks/guard.py`](../agent-hooks/guard.py) (PreToolUse: secrets, destructive commands, contract review, evidence), [`format_on_save.py`](../agent-hooks/format_on_save.py) (PostToolUse: ruff); wired in [`.claude/settings.json`](../.claude/settings.json) |
| Custom agent | What runs unattended? | the on-call responder: [`incident-response/`](../incident-response/) |
| Permissions note | Who may do what? | [`permissions.md`](permissions.md) |

Rule of thumb: knowledge in instructions, procedures in skills, focused judgement
with limited tools in subagents, live data and actions behind MCP, things that
must not depend on the model remembering in hooks, unattended jobs in a custom agent.

## Use it

```bash
docker compose up -d --build --wait
claude          # in the repo root; approve the "boardly" MCP server once
```

Inside Claude Code: `/agents` lists the subagents, `/mcp` shows the server, and
skills load when relevant (or ask: "use the review-api-change skill").

## Demo script

1. The agent reads `AGENTS.md` (ask: "what are the rules for changing the API?").
2. Invoke the workflow: "add an optional `color` field to cards using the
   review-api-change skill".
3. The skill delegates to `api-contract-reviewer`, which flags that colors are a
   non-goal in the spec -> blocking finding.
4. The agent calls the MCP tool `get_board` to show the current cards.
5. The guard hook blocks the agent from editing `openapi.yaml` before the review is
   recorded, and blocks `rm -rf` / reading `.env`.
6. The human reviews the final diff (`git diff`) before anything is committed.
