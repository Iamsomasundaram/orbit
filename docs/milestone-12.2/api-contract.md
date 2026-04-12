# ORBIT Milestone 12.2 API Contract

Milestone 12.2 does not add new reasoning stages or provider calls. It hardens the existing API and UI interaction contract so the approved review, debate, re-synthesis, history, and Committee Mode flows are more reliable and more observable.

## Existing backend endpoints with strengthened behavior

### `POST /api/v1/portfolios`

Supported submissions remain:

- JSON idea submission
- markdown document submission

Milestone 12.2 hardening:

- markdown submissions now normalize portfolio ids through bounded validation
- markdown ingestion now parses once and then rebinds the persisted source-document path
- source documents remain local-first under `PORTFOLIO_STORAGE_DIR`
- duplicate conflicts still return bounded `409` behavior through the persistence boundary

JSON idea submission remains the primary interactive path for the web UI.

### `POST /api/v1/portfolios/{portfolio_id}/review-runs`

No review semantics changed.

Milestone 12.2 impact:

- llm runtime failures now fall back to deterministic execution instead of crashing the run
- the created review persists runtime request versus effective runtime information
- fallback state is logged through audit events and later exposed through deliberation telemetry and UI detail views

### `GET /api/v1/review-runs/{run_id}`

Milestone 12.2 uses the existing review-run detail endpoint as the main review inspection surface for the web UI.

The response is used to render:

- review-run metadata
- persisted agent reviews
- persisted conflicts
- scorecard
- committee report
- review-scope audit events

### `GET /api/v1/review-runs/{run_id}/artifacts`

No contract redesign in Milestone 12.2.

This endpoint remains the source for:

- latest active recommendation
- weighted composite score
- active artifact source
- lineage references

### `GET /api/v1/review-runs/{run_id}/deliberation`

Milestone 12.2 strengthens the payload used by both Review Run Detail and Committee Mode.

The persisted response now includes:

- `runtime_metadata`
  - `requested_runtime_mode`
  - `effective_runtime_mode`
  - `requested_provider`
  - `requested_model_name`
  - `runtime_mode`
  - `model_provider`
  - `model_name`
  - `prompt_contract_version`
  - `agent_count`
  - `total_duration_ms`
  - `total_input_tokens`
  - `total_output_tokens`
  - `total_tokens`
  - `estimated_cost_usd`
  - `fallback_applied`
  - `fallback_reason`
  - `fallback_category`
  - `agents[]` with per-agent duration, token, and cost telemetry
- `conflicts[]`
  - full persisted conflict payloads for review-run conflict inspection and Committee Mode spotlight enrichment

Milestone 12.2 conflict payload enrichment is additive and backward-compatible:

- `conflicting_agents`
- `conflict_category`
- `conflict_reason`

### `GET /api/v1/review-runs/{run_id}/deliberation/summary`

No breaking change.

Committee Mode still uses this endpoint for:

- phase labels
- phase counts
- phase summaries
- final recommendation
- weighted composite score
- active artifact source

### `GET /api/v1/portfolios/{portfolio_id}/history`

No new endpoint, but the underlying audit boundaries are cleaner.

Milestone 12.2 keeps the existing history route while aligning persisted review-stage actions to:

- `review_run.created`
- `review_run.runtime_fallback`
- `review_run.completed`
- `committee_report.materialized`

Debate and re-synthesis scopes now also include explicit creation events:

- `debate_session.created`
- `resynthesis.created`

## Internal web handlers hardened for client-side interaction

Milestone 12.2 keeps the Next.js proxy handlers but adds JSON-aware behavior for client components.

### `apps/web/app/api/portfolios/route.ts`

When the request accepts JSON:

- success returns a JSON payload with:
  - `redirect_to`
  - `portfolio`
- failure returns a JSON payload with:
  - `detail`

When the request does not accept JSON:

- redirect behavior remains intact for non-JS form flows

### `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`

When the request accepts JSON:

- success returns:
  - `redirect_to`
  - `review_run`
- failure returns:
  - `detail`

This contract supports loading states and visible error handling in the web UI.

## UI routes introduced or strengthened in Milestone 12.2

- `/`
  - client-side portfolio creation
  - workspace ranking and comparison selection
- `/portfolios/{portfolio_id}`
  - portfolio detail plus reliable review trigger
- `/portfolios/{portfolio_id}/history`
  - review history plus reliable review trigger
- `/review-runs/{run_id}`
  - review-run detail, runtime telemetry, fallback state, persisted conflict metadata, and review audit events
- `/review-runs/{run_id}/committee`
  - Committee Mode playback with telemetry and enriched conflict spotlight
- `/review-runs/{run_id}/deliberation`
  - static ordered timeline inspection
- `/compare?...`
  - side-by-side persisted comparison

## Persistence and migration impact

Milestone 12.2 does not introduce a new reasoning table and does not change approved artifact semantics.

Persistence changes:

- additive conflict metadata stored inside the existing conflict payload
- explicit audit events for creation boundaries
- deterministic fallback audit event for review runs

Alembic revision:

- `apps/api/alembic/versions/20260412_01_m122_query_hardening.py`

Indexes added:

- `ix_review_runs_portfolio_id_created_at`
- `ix_debate_sessions_run_id_created_at`
- `ix_resynthesis_sessions_debate_id_created_at`
- `ix_audit_events_portfolio_id_created_at_event_id`
- `ix_audit_events_run_id_created_at_event_id`

## Browser automation contract

Milestone 12.2 introduces Playwright coverage for the thin functional UI surface.

Primary files:

- `apps/web/playwright.config.ts`
- `apps/web/tests-e2e/milestone-12-2.spec.ts`
- `apps/web/Dockerfile.e2e`
- `.github/workflows/compose-regression.yml`

Validation path:

- `docker compose run --rm browser-tests`

CI now runs:

- migrations
- worker pytest suite
- archived-baseline parity
- browser automation suite

## Non-goals preserved

Milestone 12.2 does not:

- add new LLM calls
- redesign committee behavior
- change deterministic review outputs
- change debate or re-synthesis logic
- introduce async job systems or distributed orchestration
