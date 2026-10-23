# Boardly — Product Spec

> Started as the module 2 homework spec (proposed by the coding assistant,
> corrected and approved by the user on 2026-09-14). Extended on 2026-10-22 for
> the final project with the operational requirements below. Each item is
> tracked as a GitHub issue with its acceptance criteria.

## Summary

Boardly is a single-user mini kanban board: one board, a fixed set of
columns, and cards you can create, edit, move, and delete. Data persists
across sessions.

## Columns

1. **New** — unrefined items; may need grooming before they're ready to be
   picked up. Lives here until it's clear enough to move to To Do (possibly
   for a future sprint).
2. **To Do** — refined and ready to be worked on.
3. **In Progress** — currently being worked on.
4. **Done** — finished.

## User stories

1. As a user, I can create a card with a title and an optional description
   so I can track a piece of work.
2. As a user, I can see all cards grouped into columns (New / To Do /
   In Progress / Done) so I know the state of my work at a glance.
3. As a user, I can move a card from one column to another (drag-and-drop)
   so I can reflect progress.
4. As a user, I can edit a card's title/description so I can correct or
   refine it.
5. As a user, I can delete a card I no longer need.
6. As a user, I can refresh the page or come back later and still see all
   my cards in the column I last left them in.

## Acceptance criteria

- The board shows exactly four columns, in this fixed order: **New**,
  **To Do**, **In Progress**, **Done**.
- New cards are created in the **New** column by default.
- Creating a card requires a title (non-empty); description is optional.
- A card can be dragged from any column to any other column, in any order
  of columns (no enforced workflow direction).
- Editing and deleting a card is possible from the card itself (e.g. a
  small menu or icon on the card).
- All card data (title, description, column, position) is persisted in a
  database and survives a page refresh or server restart.
- The UI updates immediately when a card is created, moved, edited, or
  deleted (no manual refresh needed).

## Non-goals (out of scope)

- User accounts / authentication / login.
- Multiple boards — only one board exists.
- Custom columns (renaming, adding, or removing columns).
- Real-time collaboration between multiple browser tabs/users (each client
  reloads its own state; no WebSocket sync required).
- Card assignees, due dates, labels/tags, comments, or attachments.
- Card change history / audit log.

## Operational requirements (final project)

7. As a user, I can open Boardly from one URL and it works without knowing
   where the backend runs.
   - The browser only calls the same origin (`/api/*`); nginx proxies to the backend.
8. As the maintainer, I can start the whole system with one command.
   - `docker compose up` starts the frontend, backend, Postgres and the
     observability stack; the backend reports ready only when the database is reachable.
9. As the maintainer, every change is tested before it can ship.
   - Unit and integration tests (real HTTP server, real database) run with one
     command and on every pull request.
10. As the maintainer, a merge to `main` reaches users safely.
    - Deploys to dev automatically, to prod only after a manual approval.
    - Each deploy is smoke-tested and rolled back automatically if it fails.
11. As the maintainer, I can see whether users' board actions succeed.
    - Every API request emits a trace, metrics and a structured log sharing one
      trace id; card titles and descriptions never appear in telemetry.
    - A dashboard shows traffic, errors and latency per action.
12. As the maintainer, I am alerted when users cannot save their changes, and a
    first responder handles it.
    - An alert fires on 5xx responses from the board API (not on CPU/memory).
    - The alert wakes an on-call agent that collects evidence, fixes the bug with
      a regression test or escalates; the system redeploys and verifies recovery
      itself, and a human reviews the diff before it is committed.

## Tech shape

- `frontend/` — React + Vite, calls the backend through one centralized API
  module (mocked first, then real).
- `openapi.yaml` — contract between frontend and backend.
- `backend/` — FastAPI, managed with `uv`. Mock in-memory store first, then
  swapped for SQLAlchemy (SQLite in tests, Postgres in Compose/Kubernetes).
- Tests written before implementation for backend endpoints; frontend and
  backend tests both required before the database swap is considered done.

## Decisions confirmed by the user (2026-09-14)

- Name: **Boardly**.
- Single board, no auth, four fixed columns (New / To Do / In Progress /
  Done) — no custom columns, no multiple boards.
- Card fields: title + description only, no color tag.
