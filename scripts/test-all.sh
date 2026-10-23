#!/usr/bin/env bash
# Same as `make test`, for machines without make: every test suite, one command.
set -euo pipefail
cd "$(dirname "$0")/.."
(cd backend && uv sync --frozen -q && uv run ruff check . && uv run pytest -q)
(cd frontend && npm ci --silent && npm run lint && npm test)
(cd incident-response && uv sync --frozen -q && uv run --frozen pytest -q)
(cd mcp-server && uv sync --frozen -q && uv run --frozen pytest -q test_server.py)
(cd backend && uv run python -m pytest -q -p no:cacheprovider ../agent-hooks/tests)
echo "ALL TEST SUITES PASSED"
