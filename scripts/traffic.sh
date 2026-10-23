#!/usr/bin/env bash
# Simulate a user working the board through the frontend's /api proxy:
# create a card, edit it, drag it across columns, delete it. Runs N rounds.
#
# Usage: scripts/traffic.sh [rounds] [base_url]
set -uo pipefail

rounds="${1:-30}"
base="${2:-http://127.0.0.1:${BOARDLY_PORT:-8080}/api}"
ok=0
failed=0

req() {
  local code
  code="$(curl -s -o /tmp/boardly-traffic.$$ -w '%{http_code}' --max-time 5 -X "$1" \
    -H 'Content-Type: application/json' ${3:+-d "$3"} "$base$2")"
  if [[ "$code" == 5* || "$code" == 000 ]]; then failed=$((failed + 1)); else ok=$((ok + 1)); fi
  cat /tmp/boardly-traffic.$$ 2>/dev/null
}

for i in $(seq 1 "$rounds"); do
  req GET /board >/dev/null
  id="$(req POST /cards "{\"title\":\"Task $i\",\"description\":\"generated\"}" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' 2>/dev/null)"
  [ -z "$id" ] && continue
  req PATCH "/cards/$id" "{\"title\":\"Task $i (refined)\"}" >/dev/null
  for column in todo in_progress done; do
    req PATCH "/cards/$id/move" "{\"column\":\"$column\"}" >/dev/null
  done
  req DELETE "/cards/$id" >/dev/null
done
rm -f /tmp/boardly-traffic.$$
echo "requests ok=$ok failed(5xx)=$failed"
