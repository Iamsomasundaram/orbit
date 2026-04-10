# Milestone 6.1 Migration Workflow

## Baseline

- Alembic revision: `20260410_01`
- scope: full persistence baseline through Milestone 6 artifact tables
- owner: `apps/api/alembic/`

## Local Workflow

1. Build the runtime images:
   - `docker compose build migrate api worker web`
2. Start the platform:
   - `docker compose up -d postgres redis api worker web`
3. Check the migration result:
   - `docker compose logs --no-color --tail 80 migrate`
4. Run the regression suite:
   - `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`

## Migration Bootstrap Behavior

- Fresh database:
  - runs `alembic upgrade head`
- Legacy local dev database with the full pre-Alembic ORBIT schema already present:
  - runs `alembic stamp head`
  - then runs `alembic upgrade head`
- Partial pre-Alembic database:
  - fails fast instead of stamping an incomplete schema

This bootstrap logic is implemented in `apps/api/orbit_api/migrations.py`.

## Manual Rerun

- `docker compose run --rm migrate`

## Runtime Expectations

- `api` and `worker` now depend on the `migrate` service completing successfully
- `api` startup calls `assert_schema_ready()` and fails if the Alembic-managed schema is missing
- DB-backed uniqueness now owns bounded create paths for:
  - portfolio ingestion
  - debate creation
  - re-synthesis creation

## JS Baseline Lifecycle

- current stage: `frozen-baseline`
- archival target milestone: `Milestone 7`
- active backend direction: Python only
