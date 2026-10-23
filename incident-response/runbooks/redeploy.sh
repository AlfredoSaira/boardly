#!/usr/bin/env bash
# Rebuild and restart only the backend container from the current working
# tree. Postgres and the telemetry stack keep running, so the recovery shows
# up on the same dashboard that detected the incident.
set -euo pipefail

cd "$(dirname "$0")/../.."
docker compose up --build -d --wait --no-deps backend
docker compose ps backend
