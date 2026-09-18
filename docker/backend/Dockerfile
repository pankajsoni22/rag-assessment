# Build context is the repo root (see docker/docker-compose.yml's
# `context: ..`) because this is a uv workspace: resolving the rag-backend
# package requires the root pyproject.toml/uv.lock plus the workspace member
# it depends on (rag-storage), not just project/backend in isolation.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /usr/local/bin/

WORKDIR /app

# The whole project/ tree (not just backend+storage) because uv validates
# that every workspace member declared in the root pyproject.toml actually
# exists on disk - copying only the packages this image runs would make
# `uv sync` fail on the missing frontend/tests-e2e members.
COPY pyproject.toml uv.lock ./
COPY project ./project
COPY tests ./tests

RUN uv sync --package rag-backend --no-dev --frozen

EXPOSE 8000

CMD ["uv", "run", "--package", "rag-backend", "uvicorn", "backend.main:app", \
     "--app-dir", "project/backend/src", "--host", "0.0.0.0", "--port", "8000"]
