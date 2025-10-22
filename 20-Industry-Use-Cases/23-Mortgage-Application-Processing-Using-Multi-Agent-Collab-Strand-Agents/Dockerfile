# Use BuildKit features
# syntax = docker/dockerfile:1.4

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1 \
    DOCKER_CONTAINER=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd -m -u 1000 bedrock_agentcore

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY --chown=bedrock_agentcore:bedrock_agentcore src src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

EXPOSE 8080 8000

CMD ["opentelemetry-instrument", "python", "-m", "src.mortgage_processor.main"]