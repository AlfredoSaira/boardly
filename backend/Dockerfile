FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/uv
WORKDIR /app

# Dependencies first so this layer is reused when only app code changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    DATABASE_URL=sqlite:////data/boardly.db
RUN useradd --create-home boardly && mkdir -p /data && chown boardly /data
USER boardly
EXPOSE 8000

# 0.0.0.0, not 127.0.0.1: the container must accept connections from outside itself.
CMD ["uvicorn", "boardly_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
