# Development process

How a change goes from idea to production in this repo. The same flow is used
by humans and agents.

1. **Spec.** Scope lives in [`_docs/specs.md`](../_docs/specs.md). A change in
   scope is a spec change first, approved by the human.
2. **Issue.** Every task is a GitHub issue in the public tracker
   (https://github.com/AlfredoSaira/boardly/issues) with acceptance criteria as
   a checklist. The product role (human + main agent) writes and grooms them.
3. **Implement.** The implementer agent (Claude Code, main session) reads
   `AGENTS.md`, the issue, and the docs it points to. Backend endpoints are
   test-first. Contract changes go through the `review-api-change` skill.
4. **Review.** Subagents review in their own context: `api-contract-reviewer`
   for contract changes, `qa-tester` to cover the acceptance criteria with tests.
   Guardrail hooks run on every tool call (see [`permissions.md`](permissions.md)).
5. **Commit.** Only with all test suites green (`make test` or
   `scripts/test-all.sh`). Commit messages reference the issue (`Closes #N`) and the
   agent comments on the issue with what changed and how it was tested.
6. **CI.** Every pull request and push runs lint + unit + integration tests for the
   backend (against Postgres), frontend, responder, MCP server and hooks.
7. **CD.** A push to `main` builds the images, deploys to **dev** automatically
   with a smoke test and automatic rollback, then waits for a **manual approval**
   before deploying the same images to **prod**. See [`deployment.md`](deployment.md).
8. **Operate.** Grafana alerts on user impact (failed board actions). The on-call
   agent investigates, fixes, and the responder redeploys and verifies. A human
   reviews the agent's diff before it is committed. See [`on-call.md`](on-call.md).
