# ORBIT Milestone 7.1 Review Pack

## Scope Delivered

- completed archival of the executable JS baseline source
- removed the executable JS baseline service from Docker Compose
- preserved the committed JS baseline artifacts as the parity reference
- updated platform metadata and UI to report `archived-baseline`
- repointed the top-level thin-slice command to the Python worker CLI
- preserved approved review, debate, re-synthesis, history, and artifact inspection behavior

## Architecture Decisions

- the archived JS baseline is now a historical reference, not an executable runtime
  - archived source moved under `archive/js-baseline/`
  - active backend direction remains Python only
- parity remains artifact-based
  - Python output is still compared to the committed JS baseline artifacts
  - no live JS execution is required for parity validation
- Docker Compose remains the system of record for local execution
  - the active stack is `postgres`, `redis`, `api`, `worker`, and `web`
  - optional parity validation remains available through `worker-parity`

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose up -d api worker web`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `28 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `28 passed`

Live validation completed on April 10, 2026:

- `GET /api/v1/system/info`
  - returned `milestone=7.1`
  - returned `runtime_direction=review-history-and-baseline-archival`
  - returned `reference_runtime_stage=archived-baseline`
- `GET http://localhost:5000/api/health/live`
  - returned milestone `7.1`
- fresh archival-era review path created:
  - `review-strong-ai-saas-001-20260410T115612290555Z`
  - `debate-review-strong-ai-saas-001-20260410T115612290555Z`
  - `resynthesis-debate-review-strong-ai-saas-001-20260410T115612290555Z`
- that archival-era review path returned:
  - `15` agents
  - `5` conflicts
  - `Proceed with Conditions`
  - `3.61`
  - `active_artifact_source=original`

## Risks

Technical risk:

- parity still depends on the committed artifact set staying curated and protected in CI
- archived source is preserved for traceability, but no regeneration workflow remains in the active runtime path
- history-query indexing and audit query refinement remain deferred from Milestone 7

Product risk:

- this milestone improves platform discipline, not end-user feature breadth
- provider-backed reasoning remains outside scope, so committee depth is still bounded and deterministic

Delivery risk:

- CI automation for parity and history regression is still pending
- if a future team tries to regenerate baseline artifacts without an approved archival exception, the archive boundary could erode

## Validation

Primary local workflow:

- `docker compose up -d api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference checks:

- `GET http://localhost:5001/api/v1/system/info`
- `GET http://localhost:5000/api/health/live`
- `GET http://localhost:5004/health/ready`

## Review Checklist

- JS baseline source is archived outside the active runtime path
- the executable `worker-js-baseline` service is removed
- committed baseline artifacts remain available for parity
- Python remains the only active backend runtime
- approved committee outcomes remain unchanged after archival
- Docker Compose remains the primary workflow

## Carry-Forward

- add CI automation for archived-baseline parity and history regression
- add indexing strategy for history-heavy query paths
- refine audit-event query boundaries later if a safe improvement is approved
- keep source-document artifact strategy explicitly local-first and temporary until a later milestone changes it

## Recommendation

Proceed with fixes.

Milestone 7.1 completes the JS baseline archival requirement without discovering a blocker. The remaining work is operational hardening, not a runtime-direction decision.
