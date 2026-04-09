FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/poetry.lock ./
RUN poetry install --no-root

WORKDIR /workspace
COPY apps/api /workspace/apps/api
