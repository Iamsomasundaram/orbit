# ORBIT Milestone 8 API Contract

## Portfolio Submission

Endpoint:

- `POST /api/v1/portfolios`

Milestone 8 keeps the existing document-ingestion path and adds a JSON idea-submission path.

### Idea Submission Request

```json
{
  "portfolio_name": "ProcurePilot M8 Interactive",
  "portfolio_type": "product_idea",
  "owner": "Somasundaram P",
  "description": "AI workflow platform for procurement leadership that reduces manual cycle-time, improves auditability, and gives buyers a human approval path.",
  "tags": ["ai-saas", "procurement", "workflow"],
  "metadata": {
    "region": "us"
  }
}
```

Behavior:

- renders the submission into a markdown source document
- canonicalizes the document into the approved 11-section ORBIT portfolio structure
- persists:
  - `portfolios`
  - `source_documents`
  - `canonical_portfolios`
  - portfolio ingestion `audit_events`
- returns `201 Created` with the created portfolio detail payload

Error handling:

- `400` for missing required fields
- `409` when the derived `portfolio_id` already exists

### Response Shape

Returns the existing `PortfolioDetail` contract:

- `portfolio`
- `source_documents`
- `canonical_portfolio`
- `audit_events`

## Review Run Trigger

Endpoint:

- `POST /api/v1/portfolios/{portfolio_id}/review-runs`

Milestone 8 keeps the response contract as `ReviewRunSummary`, but changes the user-facing execution path:

1. create the review run from the persisted canonical portfolio
2. if conflicts exist, automatically create one bounded debate session
3. if one or more resolutions set `score_change_required=true`, automatically create one bounded re-synthesis session
4. return the `ReviewRunSummary`

Response example:

```json
{
  "run_id": "review-procurepilot-m8-interactive-20260410T125850832934Z",
  "portfolio_id": "procurepilot-m8-interactive",
  "review_status": "completed",
  "final_recommendation": "Pilot Only",
  "weighted_composite_score": 3.48,
  "agent_review_count": 15,
  "conflict_count": 4,
  "created_at": "2026-04-10T12:58:50.840965Z",
  "completed_at": "2026-04-10T12:58:50.840965Z"
}
```

## Inspection Endpoints Used by Milestone 8 UI

Portfolio detail and history pages use existing endpoints:

- `GET /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `GET /api/v1/portfolios/{portfolio_id}/history`
- `GET /api/v1/review-runs/{run_id}/artifacts`

Milestone 8 history display relies on:

- `PortfolioHistoryDetail.items[*].lineage`
- `PortfolioHistoryDetail.items[*].review_run`
- `PortfolioHistoryDetail.items[*].debate`
- `PortfolioHistoryDetail.items[*].resynthesis`
- `PortfolioHistoryDetail.items[*].artifact_selection`
- `ArtifactInspectionDetail.agent_review_count`
- `ArtifactInspectionDetail.conflict_count`
- `ArtifactInspectionDetail.active_scorecard.final_recommendation`
- `ArtifactInspectionDetail.active_scorecard.weighted_composite_score`
- `ArtifactInspectionDetail.artifact_selection.active_artifact_source`

## Web Shell POST Forwarders

Milestone 8 adds web-side POST handlers:

- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`

These handlers:

- keep browser requests same-origin to the Next.js shell
- forward typed JSON payloads to the FastAPI API using the internal Compose network
- redirect to:
  - `/portfolios/{portfolio_id}/history?created=1` after submission
  - `/portfolios/{portfolio_id}/history?runId={run_id}` after review execution

## Baseline and Parity Posture

- the archived JS source stays under `archive/js-baseline/`
- committed parity artifacts stay under `tests/fixtures/baselines/`
- the Compose `baseline` profile remains parity-only in Milestone 8
- no baseline artifacts are regenerated in this milestone
