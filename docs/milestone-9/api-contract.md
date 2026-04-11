# ORBIT Milestone 9 API Contract

Milestone 9 adds comparison and prioritization APIs on top of the approved submission, review, debate, re-synthesis, history, and artifact surfaces.

## `GET /api/v1/portfolios/summary`

Returns the current workspace summary for all persisted portfolios.

Query parameters:

- `sort_by`
  - allowed values:
    - `latest_updated_at`
    - `portfolio_name`
    - `weighted_composite_score`
    - `recommendation_rank`
    - `conflict_count`
    - `score_change_required_count`
- `direction`
  - allowed values:
    - `asc`
    - `desc`

Response shape:

```json
{
  "sort_by": "weighted_composite_score",
  "direction": "desc",
  "items": [
    {
      "portfolio": {
        "portfolio_id": "strong-ai-saas-001",
        "portfolio_name": "ProcurePilot",
        "portfolio_type": "product",
        "owner": "Venture Studio Alpha",
        "submitted_at": "2026-04-09",
        "portfolio_status": "reviewed",
        "latest_review_run_id": "review-strong-ai-saas-001-20260410T115612290555Z",
        "created_at": "2026-04-10T11:56:12.304347Z",
        "updated_at": "2026-04-10T11:56:12.304347Z"
      },
      "latest_review_status": "completed",
      "latest_final_recommendation": "Proceed with Conditions",
      "latest_weighted_composite_score": 3.61,
      "active_artifact_source": "original",
      "agent_review_count": 15,
      "conflict_count": 5,
      "score_change_required_count": 0,
      "review_run_count": 6,
      "debate_count": 5,
      "resynthesis_count": 4,
      "latest_updated_at": "2026-04-10T11:56:13.432259Z",
      "latest_lineage": {
        "portfolio_id": "strong-ai-saas-001",
        "review_run_id": "review-strong-ai-saas-001-20260410T115612290555Z",
        "debate_id": "debate-review-strong-ai-saas-001-20260410T115612290555Z",
        "resynthesis_id": "resynthesis-debate-review-strong-ai-saas-001-20260410T115612290555Z"
      },
      "recommendation_rank": 4
    }
  ]
}
```

## `GET /api/v1/portfolios/compare`

Returns side-by-side comparison state for one or more requested portfolios.

Query parameters:

- repeated `portfolio_id`

Rules:

- preserves requested portfolio order
- deduplicates repeated `portfolio_id` values
- returns `400` when no `portfolio_id` is provided
- returns `404` when one or more requested portfolio IDs do not exist

Response shape:

```json
{
  "requested_portfolio_ids": [
    "helixflow-m9-b72db1f1",
    "helixflow-m9-b6dcf8bf",
    "strong-ai-saas-001"
  ],
  "items": [
    {
      "portfolio": {
        "portfolio_id": "helixflow-m9-b72db1f1",
        "portfolio_name": "HelixFlow M9",
        "portfolio_type": "product_idea",
        "owner": "Team One",
        "submitted_at": "2026-04-11",
        "portfolio_status": "reviewed",
        "latest_review_run_id": "review-helixflow-m9-b72db1f1-20260411T155923052158Z",
        "created_at": "2026-04-11T15:59:23.065707Z",
        "updated_at": "2026-04-11T15:59:23.065707Z"
      },
      "latest_review_status": "completed",
      "latest_final_recommendation": "Pilot Only",
      "latest_weighted_composite_score": 3.35,
      "active_artifact_source": "original",
      "agent_review_count": 15,
      "conflict_count": 4,
      "score_change_required_count": 0,
      "review_run_count": 1,
      "debate_count": 1,
      "resynthesis_count": 0,
      "latest_updated_at": "2026-04-11T15:59:23.441569Z",
      "latest_lineage": {
        "portfolio_id": "helixflow-m9-b72db1f1",
        "review_run_id": "review-helixflow-m9-b72db1f1-20260411T155923052158Z",
        "debate_id": "debate-review-helixflow-m9-b72db1f1-20260411T155923052158Z",
        "resynthesis_id": null
      },
      "recommendation_rank": 3
    }
  ]
}
```

## `GET /api/v1/portfolios/ranking`

Returns deterministic ranking derived from the latest active persisted artifacts.

Query parameters:

- `sort_by`
  - allowed values:
    - `weighted_composite_score`
    - `recommendation_rank`
    - `conflict_count`
    - `score_change_required_count`
- `direction`
  - allowed values:
    - `asc`
    - `desc`

Response shape:

```json
{
  "sort_by": "weighted_composite_score",
  "direction": "desc",
  "items": [
    {
      "rank": 1,
      "portfolio": {
        "portfolio_id": "strong-ai-saas-001",
        "portfolio_name": "ProcurePilot",
        "portfolio_type": "product",
        "owner": "Venture Studio Alpha",
        "submitted_at": "2026-04-09",
        "portfolio_status": "reviewed",
        "latest_review_run_id": "review-strong-ai-saas-001-20260410T115612290555Z",
        "created_at": "2026-04-10T11:56:12.304347Z",
        "updated_at": "2026-04-10T11:56:12.304347Z"
      },
      "latest_review_status": "completed",
      "latest_final_recommendation": "Proceed with Conditions",
      "latest_weighted_composite_score": 3.61,
      "active_artifact_source": "original",
      "agent_review_count": 15,
      "conflict_count": 5,
      "score_change_required_count": 0,
      "review_run_count": 6,
      "debate_count": 5,
      "resynthesis_count": 4,
      "latest_updated_at": "2026-04-10T11:56:13.432259Z",
      "latest_lineage": {
        "portfolio_id": "strong-ai-saas-001",
        "review_run_id": "review-strong-ai-saas-001-20260410T115612290555Z",
        "debate_id": "debate-review-strong-ai-saas-001-20260410T115612290555Z",
        "resynthesis_id": "resynthesis-debate-review-strong-ai-saas-001-20260410T115612290555Z"
      },
      "recommendation_rank": 4
    }
  ]
}
```

## Existing endpoints reused by Milestone 9

- `POST /api/v1/portfolios`
  - existing JSON idea submission path remains the entry point for new ideas
  - JSON idea submissions now use bounded fingerprint-based `portfolio_id` generation
- `POST /api/v1/portfolios/{portfolio_id}/review-runs`
  - existing synchronous review workflow remains the execution trigger
- `GET /api/v1/portfolios/{portfolio_id}/history`
  - remains the canonical lineage history surface
- `GET /api/v1/review-runs/{run_id}/artifacts`
  - remains the canonical active-artifact inspection surface

## Milestone 9 UI routes

- `/`
  - workspace home with submission form, ranking cards, sorting, and comparison selection
- `/compare?portfolioId=...`
  - side-by-side comparison view using the comparison API
- `/portfolios/{portfolio_id}`
  - existing detail page
- `/portfolios/{portfolio_id}/history`
  - existing history page
