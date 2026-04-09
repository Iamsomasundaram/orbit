# ORBIT Milestone 0.5a

Milestone 0.5a realigns the executable thin-slice runtime from Node.js to Python without changing the Milestone 0.5 committee behavior, contracts, or outputs.

Included in this milestone:

- Python thin-slice runner and CLI
- Python ingestion and canonical portfolio construction
- Python Pydantic schemas for executable contract validation
- Python execution path for all 15 specialist reviewers
- Python conflict detection v1 on structured reviewer outputs
- Python committee scorecard and report generation
- committed JS baseline artifacts for the reference portfolio
- Docker Compose services for baseline generation, Python execution, and pytest parity validation
- migration notes documenting runtime parity and any intentional differences

Primary Python runtime modules:

- `apps/worker/orbit_worker/domain.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/orbit_worker/ingestion.py`
- `apps/worker/orbit_worker/reviewer.py`
- `apps/worker/orbit_worker/conflicts.py`
- `apps/worker/orbit_worker/scorecard.py`
- `apps/worker/orbit_worker/reporting.py`
- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/cli.py`

Compose services:

- `worker-js-baseline`
- `worker`
- `worker-test`

Validation commands:

- `docker compose build worker worker-test`
- `docker compose run --rm worker-js-baseline`
- `docker compose run --rm worker`
- `docker compose run --rm worker-test`

Stop rule:

- Milestone 1 work must not start until the Milestone 0.5a review pack is accepted.
