FROM python:3.12-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# API stage
FROM base as api

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uv", "run", "python", "-m", "apps.api.main"]

# Saver stage
FROM base as saver

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://api:8000/health')" || exit 1

# Run the application
CMD ["uv", "run", "python", "-m", "apps.saver.main"]
