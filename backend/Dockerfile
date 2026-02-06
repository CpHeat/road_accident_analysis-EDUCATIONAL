FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

ENV UV_CACHE_DIR=/app/.cache

RUN apt-get update && apt-get install -y --no-install-recommends curl \
&& rm -rf /var/lib/apt/lists/*

COPY pyproject.toml pyproject.toml

RUN chown -R 1001:1001 /app

USER 1001:1001

RUN uv sync

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0"]