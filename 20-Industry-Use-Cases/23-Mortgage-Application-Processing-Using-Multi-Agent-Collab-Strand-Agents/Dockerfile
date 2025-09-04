# Single-stage build - simpler but slightly larger image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Set uv environment variables for optimization
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency files first for better layer caching
COPY uv.lock pyproject.toml ./

# Install dependencies (excluding project) in cached layer
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source code
COPY src src

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Set AWS environment variables
ENV AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1 \
    DOCKER_CONTAINER=1 \
    PATH="/app/.venv/bin:$PATH"

# Create and switch to non-root user
RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app
USER bedrock_agentcore

# Expose ports
EXPOSE 8080 8000

# Run using uv run (automatically activates the project environment)
CMD ["uv", "run", "opentelemetry-instrument", "python", "-m", "src.mortgage_processor.agents.main_agent"]