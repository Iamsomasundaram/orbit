# ORBIT Milestone 4 Review Pack

## Scope Delivered

Completed in this milestone:

- added an API path to initiate a review run from a persisted canonical portfolio
- reused the approved Python thin-slice review path directly against persisted canonical data
- persisted review run artifacts through the existing worker persistence boundary:
  - `review_runs`
  - `agent_reviews`
  - `conflicts`
  - `scorecards`
  - `committee_reports`
  - review audit events
- added API routes to list review runs for a portfolio and fetch a stored review-run detail bundle
- kept the approved committee behavior unchanged and revalidated parity after orchestration changes

## Architecture Decisions

- Milestone 4 orchestrates from persisted canonical portfolio state instead of reparsing source markdown at review-start time
- the API layer remains a thin coordinator; the review logic still lives in the worker runtime and is reused through `run_review_pipeline_for_portfolio`
- persistence writes continue through the existing worker persistence boundary instead of introducing a second review-run storage model
- orchestration remains synchronous and bounded for this milestone; async job management and debate-engine expansion remain out of scope
- review run IDs are timestamp-based to allow multiple persisted runs per portfolio without changing committee logic

## Quality Status

Validation executed successfully:

- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q` -> pass (`11 passed`)
- `docker compose --profile baseline run --rm worker-parity` -> pass (`11 passed`)
- `docker compose ps` -> `api`, `web`, `worker`, `postgres`, and `redis` healthy
- `http://localhost:5001/api/v1/system/info` -> pass
- `POST /api/v1/portfolios/strong-ai-saas-001/review-runs` -> pass
- `GET /api/v1/portfolios/strong-ai-saas-001/review-runs` -> pass
- `GET /api/v1/review-runs/{run_id}` -> pass
- `http://localhost:5000/api/health/ready` -> pass

Observed orchestration results for `strong-ai-saas-001`:

- review run id: `review-strong-ai-saas-001-20260410T050820418232Z`
- review status: `completed`
- final recommendation: `Proceed with Conditions`
- weighted composite score: `3.61`
- persisted agent review count: `15`
- persisted conflict count: `5`
- portfolio lifecycle updated to `reviewed`
- latest persisted review run id updated on the portfolio record

Thin-slice behavior remains unchanged:

- all 15 specialist agents still execute
- structured conflicts still materialize from structured outputs
- committee scorecard and committee report still derive from structured state
- the strong fixture still resolves to `Proceed with Conditions` at `3.61`

Known issues:

- review orchestration is synchronous and API-request-bound for now
- duplicate submission handling is still application-level rather than enforced through DB conflict handling
- review audit events currently include portfolio and canonical materialization events in the run bundle because the existing persistence boundary is reused as-is

## Risks

Technical risk:

- without async execution controls, long-running future review paths could outgrow the current request lifecycle
- migration tooling is still pending, so schema evolution remains manually disciplined
- source-document artifact storage remains intentionally local-first and temporary

Product risk:

- Milestone 4 proves stored review execution, not richer operational controls such as cancellation, retry policy, or queue visibility
- review-run retrieval is available through the API, but there is no dedicated frontend review history experience yet

Delivery risk:

- if DB-backed conflict enforcement for duplicate submissions is delayed, ingestion behavior may remain more fragile than the review path
- if parity regression is not automated in CI, later orchestration changes could still disturb the approved committee baseline

## Validation

How to validate locally:

1. Review `.env.example` and optionally create `.env`.
2. Run `docker compose up -d --build postgres redis api worker web`.
3. Run `docker compose ps`.
4. Check `http://localhost:5001/api/v1/system/info`.
5. Submit a portfolio document if needed through `POST http://localhost:5001/api/v1/portfolios`.
6. Start a review run through `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`.
7. Check `GET http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`.
8. Check `GET http://localhost:5001/api/v1/review-runs/{run_id}`.
9. Run `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`.
10. Run `docker compose --profile baseline run --rm worker-parity`.
11. Run `docker compose down --remove-orphans` when finished.

## Review Checklist

- Can a review run be initiated from a persisted canonical portfolio?
- Are all review artifacts persisted through the existing worker persistence boundary?
- Does the stored review outcome match the approved thin-slice committee behavior?
- Can review runs be listed and fetched back through the API?
- Is the orchestration path still bounded and synchronous without spilling into later async scope?
- Are the carry-forward items explicitly tracked instead of partially implemented?

## Recommendation

Proceed with fixes.

Carry-forward items, not Milestone 4 expansion:

- improve duplicate submission handling with DB-backed conflict enforcement
- reduce double parsing in portfolio ingestion if practical
- keep migration tooling planning active
- keep source-document artifact strategy explicitly local-first and temporary

Milestone 4 is complete and stops at the review-run orchestration gate.
