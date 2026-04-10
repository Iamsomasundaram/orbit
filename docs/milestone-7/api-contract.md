# ORBIT Milestone 7 API Contract

Milestone 7 extends the persisted review surface with lineage-aware history retrieval and artifact inspection.

## GET `/api/v1/portfolios/{portfolio_id}/history`

Purpose:

- retrieve the persisted review history for one portfolio across review runs, debates, and optional re-syntheses

Response body includes:

- `portfolio`
- `canonical_portfolio`
- `source_documents`
- `latest_review_run_id`
- `review_run_count`
- `debate_count`
- `resynthesis_count`
- `items`
- `audit_events`

Each `items[]` entry contains:

- `lineage`
- `review_run`
- `debate`
- `resynthesis`
- `artifact_selection`
- `active_final_recommendation`
- `active_weighted_composite_score`

Behavior:

- review history is ordered newest first
- lineage is resolved from persisted run, debate, and re-synthesis records
- active artifact state reflects the currently active scorecard and committee report
- portfolio audit events are returned across the full persisted lifecycle, not just ingestion

## GET `/api/v1/review-runs/{run_id}/artifacts`

Purpose:

- inspect the original and active artifact state anchored to a persisted review run

Response body includes:

- `anchor_type=review_run`
- `lineage`
- `artifact_selection`
- `portfolio`
- `review_run`
- `debate_session`
- `resynthesis_session`
- `original_scorecard`
- `original_committee_report`
- `active_scorecard`
- `active_committee_report`
- `resynthesized_scorecard`
- `resynthesized_committee_report`
- `review_audit_events`
- `debate_audit_events`
- `resynthesis_audit_events`
- `conflict_resolutions`

Behavior:

- review audit events are scoped to review-only actions
- if a later debate or re-synthesis exists, the lineage references are included without mutating the original artifacts

## GET `/api/v1/debates/{debate_id}/artifacts`

Purpose:

- inspect artifacts and lineage anchored to one persisted debate session

Behavior:

- includes the linked review run context
- includes conflict resolutions and debate audit events
- includes active artifact state, whether it still points to original review artifacts or to re-synthesized artifacts

## GET `/api/v1/re-syntheses/{resynthesis_id}/artifacts`

Purpose:

- inspect artifact lineage anchored to one persisted re-synthesis session

Behavior:

- includes both original and active committee artifacts
- when `score_change_required_count=0`, active artifact source remains `original`
- when persisted resolutions require a recheck, active artifact source becomes `resynthesized`

## Lineage and Artifact Selection Rules

- original review artifacts remain durable and always retrievable
- active artifact source is one of:
  - `original`
  - `resynthesized`
- artifact ownership is explicit for both scorecard and committee report
- lineage retrieval does not change approved committee behavior or recompute outputs

## Errors

- `404` if the referenced portfolio, review run, debate, or re-synthesis does not exist
