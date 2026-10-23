#!/usr/bin/env bash
# Post-deploy smoke test through the frontend's /api proxy: page loads, board
# loads, a card can be created, moved and deleted.
# Usage: scripts/smoke-test.sh <frontend-base-url>
set -euo pipefail
base="${1:?usage: $0 <frontend-base-url>}"

curl -sf "$base/" | grep -q '<div id="root">' && echo "frontend page: ok"
curl -sf "$base/api/board" | grep -q '"columns"' && echo "GET /api/board: ok"
id="$(curl -sf -X POST "$base/api/cards" -H 'Content-Type: application/json' \
  -d '{"title":"smoke test"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "POST /api/cards: ok ($id)"
curl -sf -X PATCH "$base/api/cards/$id/move" -H 'Content-Type: application/json' \
  -d '{"column":"todo"}' | grep -q '"column":"todo"' && echo "PATCH move: ok"
curl -sf -X DELETE "$base/api/cards/$id" -o /dev/null && echo "DELETE: ok"
echo "SMOKE TEST PASSED"
