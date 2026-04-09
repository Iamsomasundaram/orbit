# ORBIT Milestone 3 API Contract

## Submission Route

`POST /api/v1/portfolios`

Request body:

```json
{
  "document_title": "procurepilot-thin-slice.md",
  "document_kind": "markdown",
  "content": "# ProcurePilot Portfolio\n..."
}
```

Behavior:

- accepts one markdown portfolio document
- uses the approved Python canonicalization logic from `orbit_worker.ingestion`
- writes the submitted markdown to `PORTFOLIO_STORAGE_DIR`
- persists:
  - `portfolios`
  - `source_documents`
  - `canonical_portfolios`
  - `audit_events`
- rejects duplicate `portfolio_id` submissions with `409 Conflict`

Response body:

- `portfolio`
- `source_documents`
- `canonical_portfolio`
- `audit_events`

## List Route

`GET /api/v1/portfolios`

Returns a summary list of canonicalized portfolio submissions with:

- `portfolio_id`
- `portfolio_name`
- `portfolio_type`
- `owner`
- `submitted_at`
- `portfolio_status`
- `source_document_count`
- `canonical_schema_version`
- `created_at`
- `updated_at`

## Detail Route

`GET /api/v1/portfolios/{portfolio_id}`

Returns the stored canonical submission detail for one portfolio:

- `portfolio`
- `source_documents`
- `canonical_portfolio`
- `audit_events`

## Bounded Scope

- only markdown submission is supported in Milestone 3
- one source document per submission path
- no review orchestration, conflict execution, scorecard generation, or committee synthesis is triggered by these APIs
- the approved thin-slice review path remains separate and unchanged
