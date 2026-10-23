#!/usr/bin/env bash
# Deploy Boardly to one environment (namespace) of the current Kubernetes
# cluster, smoke-test it, and roll back automatically if either step fails.
#
# Usage: scripts/deploy.sh <dev|prod> <image-tag>
# Both images (boardly-backend:<tag>, boardly-frontend:<tag>) must already be
# available to the cluster (CI and `make deploy` load them with `kind load`).
set -euo pipefail
cd "$(dirname "$0")/.."

env="${1:?usage: $0 <dev|prod> <image-tag>}"
tag="${2:?usage: $0 <dev|prod> <image-tag>}"
case "$env" in dev|prod) ;; *) echo "unknown environment: $env" >&2; exit 2 ;; esac
ns="boardly-$env"
timeout="${ROLLOUT_TIMEOUT:-180s}"

kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -

# Generate the DB password once per environment; never stored in git.
if ! kubectl -n "$ns" get secret boardly-db >/dev/null 2>&1; then
  password="$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9')"
  kubectl -n "$ns" create secret generic boardly-db \
    --from-literal=POSTGRES_USER=boardly \
    --from-literal=POSTGRES_DB=boardly \
    --from-literal=POSTGRES_PASSWORD="$password" \
    --from-literal=DATABASE_URL="postgresql+psycopg://boardly:$password@postgres:5432/boardly"
fi

kubectl -n "$ns" apply -f k8s/postgres.yaml
kubectl -n "$ns" rollout status deployment/postgres --timeout="$timeout"

rollback() {
  echo "::error::$1 -- rolling back $ns to the previous version"
  kubectl -n "$ns" rollout undo deployment/backend || true
  kubectl -n "$ns" rollout undo deployment/frontend || true
  kubectl -n "$ns" rollout status deployment/backend --timeout="$timeout" || true
  kubectl -n "$ns" rollout status deployment/frontend --timeout="$timeout" || true
  exit 1
}

# Apply the app manifests with the new tag already in place, so each deploy
# is exactly one rollout revision and "rollout undo" returns to the previous tag.
for manifest in k8s/backend.yaml k8s/frontend.yaml; do
  sed -e "s#image: boardly-backend:.*#image: boardly-backend:$tag#" \
      -e "s#image: boardly-frontend:.*#image: boardly-frontend:$tag#" \
      "$manifest" | kubectl -n "$ns" apply -f -
done
kubectl -n "$ns" rollout status deployment/backend --timeout="$timeout" || rollback "backend rollout did not become healthy"
kubectl -n "$ns" rollout status deployment/frontend --timeout="$timeout" || rollback "frontend rollout did not become healthy"

# Smoke test through the same path a browser uses: frontend (nginx) -> /api -> backend -> Postgres.
port=$((18000 + RANDOM % 1000))
kubectl -n "$ns" port-forward service/frontend "$port:8080" >/dev/null 2>&1 &
pf=$!
trap 'kill $pf 2>/dev/null || true' EXIT
for _ in $(seq 1 30); do curl -sf "http://127.0.0.1:$port/healthz" >/dev/null && break; sleep 1; done

if ! scripts/smoke-test.sh "http://127.0.0.1:$port"; then
  rollback "smoke test failed"
fi
echo "Deployed boardly:$tag to $ns"
kubectl -n "$ns" get deployments -o wide
