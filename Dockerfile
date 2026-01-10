# TaoCore Docker Image
# Multi-stage build for optimal image size

FROM python:3.9.25-slim AS builder

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.9.25-slim

WORKDIR /app

# Copy uv from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY examples/ ./examples/
COPY pyproject.toml uv.lock Makefile README.md ./

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Default command: run demo
CMD ["python", "examples/demo.py"]

# Metadata
LABEL org.opencontainers.image.title="TaoCore"
LABEL org.opencontainers.image.description="Systems layer for stability, coherence, and dynamics analysis"
LABEL org.opencontainers.image.version="0.1.0"
