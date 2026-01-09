# ---------- Builder ----------
FROM python:3.12-slim AS builder
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build
COPY pyproject.toml uv.lock ./

# Create a virtual environment and install dependencies into it
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --extra cpu

# ---------- Runtime ----------
FROM python:3.12-slim
WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /build/.venv /app/.venv
# Ensure the app uses the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

COPY src ./src
COPY resources ./resources
COPY main.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "src.cmd.start_app"]