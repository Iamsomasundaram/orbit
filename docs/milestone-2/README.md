# ORBIT Milestone 2

Milestone 2 adds durable persistence models and executable schema boundaries around the approved Python backend path without changing the Milestone 0.5, 0.5a, or Milestone 1 review behavior.

Included in this milestone:

- durable persistence records for portfolios, source documents, canonical portfolios, review runs, agent reviews, conflicts, scorecards, committee reports, and audit events
- SQLAlchemy-backed Postgres table metadata generated from the Python worker contracts
- in-memory persistence repository boundary for executable schema validation without introducing new workflow scope
- API schema introspection endpoints for persistence catalog and generated DDL
- Milestone 2 documentation covering the data model, persistence boundary, and carry-forward planning

Primary runtime entry points:

- `apps/worker/orbit_worker/persistence.py`
- `apps/api/orbit_api/persistence.py`
- `apps/api/orbit_api/main.py`
- `apps/worker/tests/test_persistence_models.py`
- `docker-compose.yml`
- `docs/milestone-2/postgres-ddl.sql`

Validation commands:

- `docker compose build api worker web`
- `docker compose up -d postgres redis api worker web`
- `docker compose ps`
- `http://localhost:5001/api/v1/system/persistence/schema`
- `http://localhost:5001/api/v1/system/persistence/ddl`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`

Stop rule:

- Milestone 2 and Milestone 2.1 are reviewed together as a combined gate.
- Milestone 3 work must not start until that combined gate is accepted.
