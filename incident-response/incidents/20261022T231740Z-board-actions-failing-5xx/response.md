I found and fixed the bug behind the 500s on `PATCH /cards/{card_id}/move`, and the full test suite passes (17 tests). Nothing has been redeployed or committed.

**What was wrong:** When a card moves, `store.py` writes a log line that looks up the column's display name in `COLUMN_LABELS`. That map spelled the To Do column as `"to_do"`, but the API and the database call it `"todo"`. So moving a card into To Do raised a `KeyError` before the change was saved, and the user got a 500. Moves into other columns worked, which fits the evidence: that route shows both 200s (65.73) and 500s (22.16), and every other route is healthy.

**Fix:** In `backend/src/boardly_backend/store.py:17` I changed the key `"to_do"` to `"todo"`.

**Regression test:** I added `test_move_card_to_every_column` to `backend/tests/unit/test_cards.py`. It moves one card through all four columns. Before the fix it failed with the same `KeyError`; after the fix it passes.

INCIDENT: 20261022T231740Z-board-actions-failing-5xx
ROOT_CAUSE: COLUMN_LABELS in store.py used the key "to_do" while the column id is "todo", so every move into To Do raised a KeyError while writing the "card moved" log line and returned a 500.
FIX: backend/src/boardly_backend/store.py changed the COLUMN_LABELS key "to_do" to "todo"; backend/tests/unit/test_cards.py added test_move_card_to_every_column as a regression test.
TESTS: uv run --directory backend --frozen pytest -q -> 17 passed (the new test failed with KeyError before the fix)
ACTION: fixed
SUMMARY: Card moves into the To Do column returned 500 because of a mismatched column key in the move log label map; fixed the key and added a regression test.
