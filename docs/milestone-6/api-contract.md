# ORBIT Milestone 6 API Contract

Milestone 6 extends the Milestone 5 debate surface with bounded score recheck and committee re-synthesis.

## POST `/api/v1/debates/{debate_id}/re-synthesis`

Purpose:

- start one synchronous re-synthesis session for the persisted resolutions attached to a completed debate

Behavior:

- loads the persisted debate session, conflict resolutions, review run, original scorecard, and original committee report
- checks whether any persisted conflict resolutions mark `score_change_required=true`
- when no recheck is required:
  - persists a `resynthesis_session`
  - keeps the original scorecard and report active
  - does not materialize replacement scorecard or report artifacts
- when recheck is required:
  - recomputes a bounded scorecard from the original review state plus persisted resolution triggers
  - re-synthesizes the committee report from the rechecked scorecard
  - persists `resynthesized_scorecards` and `resynthesized_committee_reports`

Response body:

```json
{
  "resynthesis_id": "resynthesis-debate-review-strong-ai-saas-001-20260410T063048874962Z",
  "debate_id": "debate-review-strong-ai-saas-001-20260410T063048874962Z",
  "run_id": "review-strong-ai-saas-001-20260410T063048874962Z",
  "portfolio_id": "strong-ai-saas-001",
  "resynthesis_status": "completed_without_changes",
  "score_change_required_count": 0,
  "active_artifact_source": "original",
  "created_at": "2026-04-10T06:31:29.417433Z"
}
```

Errors:

- `404` if the debate session does not exist
- `409` if the debate session already has a persisted re-synthesis session

## GET `/api/v1/debates/{debate_id}/re-synthesis`

Purpose:

- list persisted re-synthesis sessions for one debate

Behavior:

- validates that the debate session exists
- returns re-synthesis summaries ordered newest first

## GET `/api/v1/re-syntheses/{resynthesis_id}`

Purpose:

- retrieve the full persisted re-synthesis artifact set and its linked review and debate context

Response body includes:

- `portfolio`
- `review_run`
- `debate_session`
- `conflict_resolutions`
- `original_scorecard`
- `original_committee_report`
- `active_scorecard`
- `active_committee_report`
- `resynthesis_session`
- `resynthesized_scorecard`
- `resynthesized_committee_report`
- `audit_events`

## Re-synthesis rules

- one re-synthesis session per debate session
- re-synthesis remains synchronous and bounded
- no score recheck occurs unless persisted resolutions explicitly set `score_change_required=true`
- original committee artifacts remain durable and retrievable even when re-synthesized artifacts exist

## Persistence additions

- `resynthesis_sessions`
- `resynthesized_scorecards`
- `resynthesized_committee_reports`

Existing persistence artifacts remain unchanged:

- `review_runs`
- `agent_reviews`
- `conflicts`
- `scorecards`
- `committee_reports`
- `debate_sessions`
- `conflict_resolutions`
- `audit_events`
