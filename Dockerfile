# Multi-stage build for better optimization
FROM python:3.12-slim as dependencies

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies only (not the current project)
RUN poetry install --only=main --no-root

# Final stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local /usr/local

# Copy source code
COPY baseten_backend_take_home/ ./baseten_backend_take_home/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Arguments for customization with better defaults
ARG APP_MODULE="baseten_backend_take_home.main:app"
ARG PORT=8000

# Set environment variables to make them available at runtime
ENV APP_MODULE=${APP_MODULE}
ENV PORT=${PORT}

# Expose port
EXPOSE ${PORT}

# Health check with dynamic port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healtz || exit 1

# Run the application with proper signal handling
CMD ["sh", "-c", "uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT}"]