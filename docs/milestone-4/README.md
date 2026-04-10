# ORBIT Milestone 4

Milestone 4 adds bounded review-run orchestration on top of the persisted canonical portfolio state from Milestone 3.

Included in this milestone:

- initiate a review run from a persisted canonical portfolio
- reuse the approved Python thin-slice review path without changing committee behavior
- persist:
  - `review_runs`
  - `agent_reviews`
  - `conflicts`
  - `scorecards`
  - `committee_reports`
  - review audit events
- expose API routes to start, list, and fetch persisted review runs

Primary entry points:

- `apps/api/orbit_api/main.py`
- `apps/api/orbit_api/review_runs.py`
- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_review_run_service.py`

Primary API routes:

- `POST /api/v1/portfolios/{portfolio_id}/review-runs`
- `GET /api/v1/portfolios/{portfolio_id}/review-runs`
- `GET /api/v1/review-runs/{run_id}`

Validation commands:

- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`
- `Invoke-RestMethod http://localhost:5001/api/v1/system/info`
- `Invoke-RestMethod -Method Post http://localhost:5001/api/v1/portfolios/strong-ai-saas-001/review-runs`
- `Invoke-RestMethod http://localhost:5001/api/v1/review-runs/{run_id}`

Stop rule:

- Milestone 4 stops after persisted review-run initiation, storage, and retrieval are validated.
- Debate-engine redesign, async workflow expansion, and broader execution topology changes do not start in this milestone.
