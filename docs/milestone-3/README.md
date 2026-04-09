# ORBIT Milestone 3

Milestone 3 adds the bounded portfolio ingestion API surface.

Included in this milestone:

- submit one markdown portfolio document through the API
- canonicalize the submitted document into the approved ORBIT portfolio shape
- persist the portfolio envelope, source document metadata, canonical payload, and ingestion audit events in Postgres
- keep Docker Compose as the primary local execution path
- preserve the approved thin-slice review behavior and frozen JS baseline parity posture

Primary entry points:

- `apps/api/orbit_api/main.py`
- `apps/api/orbit_api/portfolios.py`
- `apps/worker/orbit_worker/ingestion.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_portfolio_ingestion_service.py`
- `apps/worker/tests/test_persistence_models.py`

Primary API routes:

- `POST /api/v1/portfolios`
- `GET /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`

Validation commands:

- `docker compose build api`
- `docker compose up -d postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`
- `Invoke-RestMethod http://localhost:5001/api/v1/system/info`
- `Invoke-RestMethod http://localhost:5001/api/v1/portfolios`

Stop rule:

- Milestone 3 stops after the ingestion API, canonicalization, and persistence path is validated.
- Review orchestration, debate, and later workflow expansion do not start in this milestone.
