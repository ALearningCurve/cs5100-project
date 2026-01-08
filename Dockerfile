# Stage 1: Build dependencies using UV
FROM python:3.12-slim AS builder

WORKDIR /build

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
RUN UV_TORCH_BACKEND=auto uv sync --frozen --no-dev --extra cpu

# Stage 2: Runtime image (minimal)
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application files
COPY src ./src
COPY resources ./resources
COPY main.py .

# Set environment to use venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Expose port for uvicorn
EXPOSE 8080

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
