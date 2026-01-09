# ---------- Builder ----------
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

ENV UV_CACHE_DIR=/root/.cache/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --extra cpu

# ---------- Runtime ----------
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src ./src
COPY resources ./resources
COPY main.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "src.cmd.start_app"]