FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies and uv as root first
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Create user with uid 501 and set up directories
RUN groupadd -g 501 appuser && \
    useradd -r -d /app -u 501 -g appuser appuser && \
    mkdir -p /app /app/backend/static/images /tmp/uv-cache && \
    chown -R appuser:appuser /app /tmp/uv-cache

# Set work directory
WORKDIR /app

# Copy dependency files with proper ownership
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

# Switch to non-root user
USER appuser

# Install dependencies with uv
RUN uv sync --frozen --no-dev --no-install-project

# Copy project with proper ownership
COPY --chown=appuser:appuser src /app/src

# Expose port
EXPOSE 8000

# Run the application with uv
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
