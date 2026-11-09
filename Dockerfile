# XULAN Advisor Studio: FastAPI app plus static UI in one image.
# Runs locally with Docker Compose and on platforms that set $PORT (e.g. Cloud Run).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first, for layer caching. Runtime dependencies only (no dev group).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code and the data it reads at runtime.
COPY src ./src
COPY static ./static
COPY data ./data
COPY fixtures ./fixtures

# Non-root user; runs/ holds per-call audit files and the spend ledger.
RUN useradd --create-home --uid 10001 xulan \
    && mkdir -p /app/runs \
    && chown -R xulan:xulan /app/runs
USER xulan

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/api/health', timeout=4)"

CMD ["sh", "-c", "exec uvicorn xulan.app:app --host 0.0.0.0 --port ${PORT}"]
