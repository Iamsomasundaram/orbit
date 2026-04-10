# ORBIT Milestone 4 API Contract

## Start Review Run

`POST /api/v1/portfolios/{portfolio_id}/review-runs`

Behavior:

- loads the persisted canonical portfolio for `portfolio_id`
- reuses the approved Python thin-slice review path against the stored canonical payload
- persists the resulting review bundle through the existing worker persistence boundary
- returns a summary of the completed run

Response fields:

- `run_id`
- `portfolio_id`
- `review_status`
- `final_recommendation`
- `weighted_composite_score`
- `agent_review_count`
- `conflict_count`
- `created_at`
- `completed_at`

Failure behavior:

- returns `404 Not Found` if the canonical portfolio does not exist in the ingestion store

## List Review Runs For A Portfolio

`GET /api/v1/portfolios/{portfolio_id}/review-runs`

Returns a summary list of persisted review runs for one portfolio.

## Get Review Run Detail

`GET /api/v1/review-runs/{run_id}`

Returns the stored review bundle detail:

- `portfolio`
- `canonical_portfolio`
- `review_run`
- `agent_reviews`
- `conflicts`
- `scorecard`
- `committee_report`
- `audit_events`

## Bounded Scope

- Milestone 4 orchestration is synchronous and intentionally simple
- no debate-engine redesign is introduced
- no advanced queueing or distributed worker topology is introduced
- the thin-slice committee logic is reused as-is rather than reinterpreted in the API layer
