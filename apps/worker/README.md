# Worker App

The worker now contains both the Milestone 0.5 JS thin-slice baseline and the Milestone 0.5a Python runtime realignment path.

Current capability:

- ingest one markdown portfolio document
- canonicalize it into the ORBIT section model
- run all 15 specialist reviewers with structured outputs
- detect structured conflicts
- build a committee scorecard
- generate a committee report in JSON and Markdown
- validate Python parity against the JS baseline through Docker Compose

JS baseline entry points:

- `apps/worker/src/review-runner.js`
- `apps/worker/src/cli/review-portfolio.js`

Python runtime entry points:

- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/cli.py`
- `apps/worker/tests/test_thin_slice_parity.py`

Compose validation commands:

- `docker compose run --rm worker-js-baseline`
- `docker compose run --rm worker`
- `docker compose run --rm worker-test`
