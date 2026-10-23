# Deployment

## Run everything locally (one command)

```bash
docker compose up -d --build --wait
```

Starts Postgres, the backend, the frontend (nginx), and the observability stack
(OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana). Ports are bound to
`127.0.0.1` only.

| URL | What |
|---|---|
| http://localhost:8080 | Boardly |
| http://localhost:3000/d/boardly/boardly | Grafana dashboard (anonymous viewer) |

Stop with `docker compose down` (add `-v` to also delete the data).

## Images

| Image | Dockerfile | Notes |
|---|---|---|
| `boardly-backend` | `backend/Dockerfile` | Python 3.14 + uv, non-root user, `/healthz` (liveness) and `/readyz` (checks the database) |
| `boardly-frontend` | `frontend/Dockerfile` | multi-stage: Node builds the React app, unprivileged nginx serves it and proxies `/api/` to `$BACKEND_URL` |

## Kubernetes

Manifests in `k8s/` (Postgres with a PVC, backend x2, frontend x2, Services,
readiness/liveness probes, resource limits). Each environment is a namespace:
`boardly-dev`, `boardly-prod`. The database password is generated per
environment by `scripts/deploy.sh` and stored only in a Kubernetes Secret.

```bash
make deploy-local            # build images, create/load a kind cluster, deploy to boardly-dev
kubectl -n boardly-dev port-forward service/frontend 8081:8080   # then open http://localhost:8081
```

`scripts/deploy.sh <dev|prod> <tag>`:

1. applies Postgres and waits for it;
2. applies the backend and frontend manifests with the new image tag
   (one rollout revision per deploy);
3. waits for both rollouts;
4. runs `scripts/smoke-test.sh` through the frontend service, exactly like a browser
   (page -> `/api/board` -> create -> move -> delete);
5. **if the rollout or the smoke test fails, it runs `kubectl rollout undo` on both
   deployments and exits non-zero**, so the previous version keeps serving.

Evidence from a real run on a local kind cluster:

- [`evidence/deploy-dev-v1.log`](evidence/deploy-dev-v1.log) - a good deploy, smoke test passed.
- [`evidence/deploy-dev-broken-rollback.log`](evidence/deploy-dev-broken-rollback.log) - a backend image that
  crashes on start: the rollout never becomes healthy, the script rolls back, and
  `v1` is still serving afterwards.

## CI/CD (`.github/workflows/ci.yml`)

| Trigger | Jobs |
|---|---|
| pull request | `backend` (lint, unit, integration **against Postgres**), `frontend` (lint, tests, build), `agents` (responder, MCP server, hooks) |
| push to `main` | the above -> `build` (images tagged with the commit SHA) -> `deploy-dev` (automatic) -> `deploy-prod` (**manual approval**) |

- **dev** deploys automatically after the tests pass.
- **prod** uses the GitHub environment `production`, which has a required reviewer:
  the job waits until the human approves it in the Actions UI, then deploys the
  *same* images that passed dev.
- Both deploy jobs create a kind cluster on the runner, load the images and run
  `scripts/deploy.sh`, so every deploy is smoke-tested and rolls back on failure.
  The run logs are public under the repository's **Actions** tab.

### About the target cluster

The CI clusters are ephemeral kind clusters (no cloud account or credentials are
needed to reproduce the project). `scripts/deploy.sh` only uses the current
`kubectl` context, so pointing the same workflow at a long-lived cluster means
replacing the `helm/kind-action` step with a step that writes that cluster's
kubeconfig from a repository secret - nothing else changes.
