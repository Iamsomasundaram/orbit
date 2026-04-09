# ORBIT Milestone 0.5a Migration Notes

## Objective

Milestone 0.5a ports the executable thin-slice worker path from Node.js to Python while preserving the Milestone 0.5 committee behavior, structured contracts, and output artifacts.

## JS Baseline Kept Intact

The Milestone 0.5 JS implementation remains the reference baseline in place:

- `apps/worker/src/review-runner.js`
- `apps/worker/src/cli/review-portfolio.js`
- `packages/orbit-ingestion/src/markdown-intake.js`
- `packages/orbit-agents/src/reviewer.js`
- `packages/orbit-debate/src/conflicts.js`
- `packages/orbit-scoring/src/scorecard.js`
- `packages/orbit-reporting/src/report.js`

The reference artifact set for the approved portfolio is committed under:

- `tests/fixtures/baselines/procurepilot-js/`

## Python Runtime Added

The Python thin-slice runtime now exists alongside the JS baseline:

- `apps/worker/orbit_worker/domain.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/orbit_worker/ingestion.py`
- `apps/worker/orbit_worker/reviewer.py`
- `apps/worker/orbit_worker/conflicts.py`
- `apps/worker/orbit_worker/scorecard.py`
- `apps/worker/orbit_worker/reporting.py`
- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/cli.py`
- `apps/worker/tests/test_thin_slice_parity.py`

## Parity Result For ProcurePilot

Validated against the same source portfolio:

- agents executed: `15`
- structured conflicts: `5`
- final recommendation: `Proceed with Conditions`
- weighted composite score: `3.61`

Python output matched the committed JS baseline artifacts for:

- `canonical-portfolio.json`
- `agent-reviews.json`
- `conflicts.json`
- `scorecard.json`
- `committee-report.json`
- `committee-report.md`

## Intentional Differences

No intentional structured output differences were introduced for the reference portfolio.

Runtime-level changes only:

- the executable worker path is now available in Python
- Pydantic models enforce the runtime contracts
- Docker Compose runs the Python path without requiring host Python installation
- the Python containers execute with the image-built virtual environment at `/app/.venv` to avoid workspace mount drift at runtime

## Notes On Rounding And Parity

One parity fix was required during implementation:

- committee-level aggregate confidence and completeness fields were aligned to JS-style two-decimal formatting behavior so the Python scorecard exactly matched the JS baseline artifact set

## Validation Commands

- `docker compose build worker worker-test`
- `docker compose run --rm worker-js-baseline`
- `docker compose run --rm worker`
- `docker compose run --rm worker-test`
