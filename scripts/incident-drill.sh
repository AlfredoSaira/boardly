#!/usr/bin/env bash
# Incident drill: ship a realistic bug, let real traffic hit it, and watch
# the alert -> on-call agent -> redeploy -> verification loop handle it.
#
#   scripts/incident-drill.sh start   # apply the faulty change, redeploy, send traffic
#   scripts/incident-drill.sh traffic # send more traffic (keeps the alert firing)
#   scripts/incident-drill.sh reset   # undo the faulty change (if the agent didn't) and redeploy
#
# The responder must be running (see incident-response/README.md) for the
# alert to reach the agent.
set -euo pipefail
cd "$(dirname "$0")/.."

patch=incident-response/scenarios/move-activity-log.patch

case "${1:-start}" in
  start)
    git apply "$patch"
    echo "Applied $patch (a move activity log with a typo in its column map)."
    incident-response/runbooks/redeploy.sh
    scripts/traffic.sh 20
    echo "Grafana evaluates the alert every minute and fires after 1m pending."
    echo "Watch: http://localhost:3000/d/boardly/boardly  and  curl -s localhost:8001/incidents"
    ;;
  traffic)
    scripts/traffic.sh "${2:-20}"
    ;;
  reset)
    if git apply -R --check "$patch" 2>/dev/null; then
      git apply -R "$patch"
      echo "Reverted $patch."
    else
      echo "Faulty change is not applied as-is (already fixed or reverted); leaving the code alone."
    fi
    incident-response/runbooks/redeploy.sh
    ;;
  *)
    echo "usage: $0 [start|traffic|reset]" >&2
    exit 2
    ;;
esac
