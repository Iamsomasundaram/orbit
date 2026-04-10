# ORBIT Milestone 5 API Contract

Milestone 5 extends the Milestone 4 review-run API surface with bounded debate initiation and retrieval.

## POST `/api/v1/review-runs/{run_id}/debates`

Purpose:

- start one synchronous moderator-controlled debate session for the persisted conflicts on a completed review run

Behavior:

- loads the persisted review run, agent reviews, conflicts, scorecard, and committee report
- runs the deterministic Python debate engine against structured persisted data only
- persists `debate_sessions`, `conflict_resolutions`, and debate audit events
- returns the created debate summary

Response body:

```json
{
  "debate_id": "debate-review-strong-ai-saas-001-20260410T055330553109Z",
  "run_id": "review-strong-ai-saas-001-20260410T055330553109Z",
  "portfolio_id": "strong-ai-saas-001",
  "debate_status": "completed",
  "conflicts_considered": 5,
  "score_change_required_count": 0,
  "created_at": "2026-04-10T05:54:11.606831Z"
}
```

Errors:

- `404` if the review run does not exist
- `409` if the review run already has a persisted debate session

## GET `/api/v1/review-runs/{run_id}/debates`

Purpose:

- list the persisted debate sessions associated with one review run

Behavior:

- validates that the review run exists
- returns debate summaries ordered newest first

## GET `/api/v1/debates/{debate_id}`

Purpose:

- retrieve the full persisted debate artifact and its linked review context

Response body includes:

- `portfolio`
- `review_run`
- `conflicts`
- `scorecard`
- `committee_report`
- `debate_session`
- `conflict_resolutions`
- `audit_events`

## Debate execution rules

- one debate session per review run
- maximum of 2 moderator rounds per debated conflict
- persisted structured artifacts only; no raw-text reparsing
- committee scores are not mutated during debate
- a resolution may set `score_change_required=true` to flag later committee recheck

## Persistence additions

- `debate_sessions`
- `conflict_resolutions`

Existing review artifacts remain unchanged:

- `review_runs`
- `agent_reviews`
- `conflicts`
- `scorecards`
- `committee_reports`
- `audit_events`
