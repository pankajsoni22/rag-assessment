# Build context is the repo root (see docker/docker-compose.yml's
# `context: ..`) - same uv workspace reasoning as docker/backend/Dockerfile.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY project ./project
COPY tests ./tests

RUN uv sync --package rag-frontend --no-dev --frozen

EXPOSE 8501

CMD ["uv", "run", "--package", "rag-frontend", "streamlit", "run", \
     "project/frontend/src/frontend/app.py", \
     "--server.address", "0.0.0.0", "--server.port", "8501", \
     "--server.headless", "true"]
