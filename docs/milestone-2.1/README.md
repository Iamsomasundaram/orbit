# ORBIT Milestone 2.1

Milestone 2.1 is a stabilization milestone that hardens the platform foundation and parity posture around the Milestone 2 data model and executable schema work.

Included in this milestone:

- parity expansion across the strong, promising, and weak golden fixtures
- frozen JS baseline lifecycle controls with explicit archival target milestone
- worker host-port exposure for local debugging on `5004`
- Docker Compose updates that keep containerized workflow primary for platform bring-up and regression checks
- combined Milestone 2 and 2.1 review-gate documentation

Primary runtime entry points:

- `tests/fixtures/parity-cases.json`
- `tests/fixtures/source-documents/traceforge-thin-slice.md`
- `tests/fixtures/source-documents/moodmesh-thin-slice.md`
- `apps/worker/src/cli/refresh-baselines.js`
- `apps/worker/tests/test_thin_slice_parity.py`
- `docker-compose.yml`

Validation commands:

- `docker compose build api worker web worker-parity`
- `docker compose up -d postgres redis api worker web`
- `docker compose ps`
- `http://localhost:5004/health/ready`
- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`

Stop rule:

- Milestone 2 and Milestone 2.1 must be reviewed together as a combined gate.
- Milestone 3 work must not start until that combined gate is accepted.
