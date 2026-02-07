FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

ENV HOME=/app
ENV UV_CACHE_DIR=/app/.cache

COPY pyproject.toml pyproject.toml

RUN chown -R 1001:1001 /app

USER 1001:1001

RUN uv sync

COPY . .

CMD ["uv", "run", "streamlit", "run", "app.py", "0.0.0.0"]
