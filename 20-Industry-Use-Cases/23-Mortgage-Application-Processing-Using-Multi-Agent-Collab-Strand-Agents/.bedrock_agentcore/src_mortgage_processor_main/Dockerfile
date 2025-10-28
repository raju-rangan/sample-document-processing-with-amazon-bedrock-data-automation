# syntax=docker/dockerfile:1.9

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1 \
    DOCKER_CONTAINER=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-dev --no-editable

CMD ["opentelemetry-instrument", "python", "-m", "mortgage_processor.main"]