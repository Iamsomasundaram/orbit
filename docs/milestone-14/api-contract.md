# ORBIT Milestone 14 API Contract Updates

## Agent Review Reasoning

`AgentReview` now includes `reasoning`:

- `claim` (string)
- `evidence` (array[string])
- `risk` (array[string])
- `implication` (string)
- `score` (number)
- `confidence` (Low | Medium | High)

This is persisted inside `agent_reviews.review_payload` and remains backward compatible because the field is optional for legacy artifacts.

## Deliberation API

`GET /api/v1/review-runs/{run_id}/deliberation` now returns:

- `agent_reasoning`: list of per-agent reasoning summaries derived from persisted `agent_reviews`.

Each entry includes:

- `agent_id`
- `agent_role`
- `claim`
- `evidence`
- `risk`
- `implication`
- `score`
- `confidence`

## Conflict Metadata

`ConflictRecord` now includes:

- `conflicting_claims` (array[string])
- `conflicting_evidence` (array[string])

These fields are populated by conflict detection and used in Committee Mode conflict spotlights.

## Backward Compatibility

Older artifacts without the new reasoning or conflict metadata remain readable. New runs will populate the full schema.
