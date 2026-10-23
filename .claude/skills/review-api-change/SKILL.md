---
name: review-api-change
description: Change the Boardly API contract safely. Use whenever a task needs a new or changed endpoint, request/response field, or column value - anything that touches openapi.yaml.
---

# Review an API change

`openapi.yaml` is the contract between `frontend/src/api.js` and the FastAPI
backend. The PreToolUse guard (`agent-hooks/guard.py`) blocks edits to it until
this workflow has recorded a review.

1. **Spec first.** Check the change against `_docs/specs.md`. If it adds scope,
   stop and ask the human to update the spec (or confirm) before going on.
2. **Draft the contract change** as a diff in your reply (do not write it yet).
3. **Get a review.** Delegate to the `api-contract-reviewer` subagent with the
   draft diff and the issue's acceptance criteria. If the verdict is
   `changes-requested`, revise and ask again.
4. **Record the review** so the guard lets the edit through:
   `echo "<issue number> reviewed by api-contract-reviewer" > agent-hooks/.contract-reviewed`
5. **Apply in contract order:** `openapi.yaml` -> failing backend test ->
   `schemas.py`/`main.py`/`store.py` -> `frontend/src/api.js` -> frontend test.
6. **Verify:** `uv run --directory backend pytest -q` and `cd frontend && npm test`.
7. **Clean up:** delete `agent-hooks/.contract-reviewed`, so the next contract change
   needs its own review.
8. Summarise the change for the PR / issue comment: what changed in the
   contract, the review verdict, and the tests that cover it.
