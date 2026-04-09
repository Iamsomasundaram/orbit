# Worker App

The worker now contains three runtime layers:

- the approved JS thin-slice baseline path for reference only
- the Python thin-slice parity path from Milestone 0.5a
- the Milestone 1 Python worker service used by the local platform foundation

Current capability:

- ingest one markdown portfolio document through the Python runtime path
- canonicalize it into the ORBIT section model
- run all 15 specialist reviewers with structured outputs
- detect structured conflicts
- build a committee scorecard
- generate a committee report in JSON and Markdown
- expose worker liveness and readiness health endpoints for Compose
- validate Python parity against the JS baseline through Docker Compose

Reference baseline entry points:

- `apps/worker/src/review-runner.js`
- `apps/worker/src/cli/review-portfolio.js`

Primary Python runtime entry points:

- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/cli.py`
- `apps/worker/orbit_worker/service.py`
- `apps/worker/tests/test_thin_slice_parity.py`

Compose validation commands:

- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`
