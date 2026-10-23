# One-command entry points. See README.md for what each one does.
TAG ?= local
KIND_CLUSTER ?= boardly

.PHONY: up down test test-backend test-frontend test-responder test-mcp test-hooks deploy-local responder drill drill-reset

up: ## Build and start the whole system (app + Postgres + observability)
	docker compose up -d --build --wait
	@echo "Boardly:  http://localhost:8080"
	@echo "Grafana:  http://localhost:3000/d/boardly/boardly"

down:
	docker compose down

test: test-backend test-frontend test-responder test-mcp test-hooks ## Unit + integration tests for everything

test-backend:
	cd backend && uv sync --frozen -q && uv run pytest -q

test-frontend:
	cd frontend && npm ci --silent && npm test

test-responder:
	cd incident-response && uv sync --frozen -q && uv run --frozen pytest -q

test-mcp:
	cd mcp-server && uv sync --frozen -q && uv run --frozen pytest -q test_server.py

test-hooks:
	cd backend && uv run python -m pytest -q -p no:cacheprovider ../agent-hooks/tests

deploy-local: ## Build images and deploy to a local kind cluster (namespace boardly-dev)
	docker build -t boardly-backend:$(TAG) backend
	docker build -t boardly-frontend:$(TAG) frontend
	kind get clusters | grep -qx $(KIND_CLUSTER) || kind create cluster --name $(KIND_CLUSTER)
	kind load docker-image boardly-backend:$(TAG) boardly-frontend:$(TAG) --name $(KIND_CLUSTER)
	kubectl config use-context kind-$(KIND_CLUSTER)
	scripts/deploy.sh dev $(TAG)

responder: ## Run the on-call agent service (needs a logged-in `claude` CLI)
	cd incident-response && uv run --frozen python responder.py

drill: ## Ship a realistic bug and send traffic so the alert fires
	scripts/incident-drill.sh start

drill-reset:
	scripts/incident-drill.sh reset
