#!/usr/bin/env bash
# Replay the full card journey against the running backend: load the board,
# create a card, edit it, move it through every column, delete it. Fails if
# any step answers 5xx or does not answer at all. Used both by the agent (to
# check its own fix) and by the responder (to check the agent's claim).
#
# Takes no arguments on purpose: it only ever talks to the local backend.
set -euo pipefail

base_url="http://127.0.0.1:${BACKEND_PORT:-8000}"
attempts="${VERIFY_ATTEMPTS:-3}"
failed=0

call() {
  local method="$1" path="$2" body="${3:-}"
  local out code
  out="$(mktemp)"
  if [ -n "$body" ]; then
    code="$(curl -s -o "$out" -w '%{http_code}' --max-time 5 -X "$method" \
      -H 'Content-Type: application/json' -d "$body" "$base_url$path" || true)"
  else
    code="$(curl -s -o "$out" -w '%{http_code}' --max-time 5 -X "$method" "$base_url$path" || true)"
  fi
  echo "$method $path -> $code" >&2
  if [[ "$code" == 000 || "$code" == 5* ]]; then
    failed=1
  fi
  cat "$out"
  rm -f "$out"
}

for attempt in $(seq 1 "$attempts"); do
  echo "attempt $attempt" >&2
  call GET /board >/dev/null
  card="$(call POST /cards '{"title":"verify-recovery probe","description":"synthetic"}')"
  card_id="$(printf '%s' "$card" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))' 2>/dev/null || true)"
  if [ -z "$card_id" ]; then
    failed=1
    continue
  fi
  call PATCH "/cards/$card_id" '{"title":"verify-recovery probe (edited)"}' >/dev/null
  for column in todo in_progress done new; do
    call PATCH "/cards/$card_id/move" "{\"column\":\"$column\"}" >/dev/null
  done
  call DELETE "/cards/$card_id" >/dev/null
done

if [ "$failed" -ne 0 ]; then
  echo "NOT RECOVERED"
  exit 1
fi
echo "RECOVERED"
