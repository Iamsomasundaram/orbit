# Worker App

The worker now contains four runtime layers:

- the approved JS thin-slice baseline path for reference only
- the Python thin-slice parity path from Milestone 0.5a
- the Milestone 1 Python worker service used by the local platform foundation
- the Milestone 2 persistence contracts and database-facing schema boundary

Current capability:

- ingest markdown portfolio documents through the Python runtime path
- canonicalize them into the ORBIT section model
- run all 15 specialist reviewers with structured outputs
- detect structured conflicts
- build a committee scorecard
- generate a committee report in JSON and Markdown
- materialize durable persistence bundles for portfolio, review, and audit artifacts
- expose worker liveness and readiness health endpoints for Compose and host debugging on port `5004`
- validate Python parity against the frozen JS baseline through Docker Compose across all three golden fixtures

Reference baseline entry points:

- `apps/worker/src/review-runner.js`
- `apps/worker/src/cli/review-portfolio.js`
- `apps/worker/src/cli/refresh-baselines.js`

Primary Python runtime entry points:

- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/cli.py`
- `apps/worker/orbit_worker/service.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_thin_slice_parity.py`
- `apps/worker/tests/test_persistence_models.py`

Compose validation commands:

- `docker compose build api worker web worker-parity`
- `docker compose up -d postgres redis api worker web`
- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`
