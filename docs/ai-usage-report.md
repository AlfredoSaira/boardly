# AI Usage Report — Boardly

How AI (Claude Code, running end-to-end in an interactive session) was used
to build this project, per the module 2 deliverable list.

## Spec (Question 2)

The assistant proposed an MVP spec draft with reasonable defaults (single
board, no auth, three columns, title+description only) rather than
open-ended questions, to keep momentum. The user reviewed it and corrected
two things: add a fourth column ("New", for unrefined backlog items) and
its semantics. The assistant updated `_docs/specs.md` and recorded the
decisions as confirmed. The project name ("Boardly") was proposed by the
assistant and accepted without changes.

**Human judgment used for:** choosing the project type (mini kanban board)
out of the four options, and the one substantive scope correction (the
fourth column).

## Frontend (Question 4)

The assistant scaffolded the project (`npm create vite`), wrote all
components (`Board`, `Column`, `Card`, `CardModal`, `SummaryBar`), the
centralized mock API module (`api.js`), and the drag-and-drop wiring
(`@dnd-kit`). It ran `npm run build` and `npm run lint` after every change
to catch syntax/bundling errors.

The user asked for two follow-up changes after seeing the plan: a sprint
number + per-column task-count summary bar at the top (with a specific
rule — two-week sprints starting from Jan 1 of the current year), and
wider columns. Both were implemented directly from the user's description.

**Limitation disclosed to the user:** the assistant has no way to open a
real browser from this environment. Everything was verified by build/lint
passing and by reasoning about the code, not by visually confirming the
drag-and-drop interaction — the user was explicitly asked to try it
themselves before treating the frontend as done.

## Backend (Question 5)

The assistant wrote `openapi.yaml` first, then followed the project's own
rule ("write tests before implementing") — `tests/test_cards.py` was
written against the planned FastAPI routes before `main.py` existed, then
the implementation was written to make those tests pass. `ruff check` /
`ruff format` were run and fixed after every change.

## Connecting frontend and backend (Question 6)

The assistant replaced the mocked functions in `api.js` with real `fetch`
calls matching the OpenAPI contract, added CORS middleware to the backend,
and verified the connection with `curl` (including a CORS preflight
request) rather than a browser — same disclosed limitation as above.

## Database (Question 7)

The assistant swapped the in-memory mock store for SQLAlchemy + SQLite
behind the same internal interface (`CardStore`), keeping the engine
swappable via `DATABASE_URL`. To prove real persistence (not just an
in-memory Python object surviving within one process), the assistant
created a card via the API, killed the running server process entirely,
restarted it, and confirmed the card was still there via `curl`.

## Overall pattern

At each step: assistant proposes/implements → runs the available
non-visual checks (tests, lint, build, curl) → reports results and any
verification gap honestly → user reviews, corrects, or asks for a
follow-up change → assistant applies it. Commits were only made when the
user explicitly asked ("commitea"); pushes only when explicitly asked
("pushea").
