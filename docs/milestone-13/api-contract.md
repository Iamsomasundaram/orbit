# ORBIT Milestone 13 API Contract

Milestone 13 does not add a new top-level reasoning endpoint. It changes the runtime behavior behind the existing review surfaces so that llm execution is the default, adaptive routing metadata is persisted, and deterministic fallback remains visible without changing the approved artifact model.

## Runtime defaults

System runtime defaults now resolve to:

- `LLM_RUNTIME_MODE=llm`
- `LLM_PROVIDER=openai`
- `LLM_REQUEST_TIMEOUT_SECONDS=45`

Deterministic execution still exists in two ways:

- explicit runtime configuration with `LLM_RUNTIME_MODE=deterministic`
- automatic fallback when llm execution fails

## Existing backend endpoints with adaptive behavior

### `GET /api/v1/system/info`

Milestone 13 impact:

- `runtime_mode` now defaults to `llm`
- `runtime_direction` now describes the adaptive tiered committee
- no contract break for existing health or info consumers

### `POST /api/v1/portfolios/{portfolio_id}/review-runs`

No new route.

Milestone 13 changes the execution behavior behind this endpoint:

- Tier-1 core agents execute first
- the adaptive router evaluates the core evidence
- Tier-2 specialists run only when the router activates them
- inactive specialists persist as passive observers
- if llm execution fails, deterministic fallback still completes the review

Persisted artifact families remain the same:

- `agent_reviews`
- `conflicts`
- `scorecards`
- `committee_reports`
- `debate_sessions`
- `resynthesis_sessions`
- `deliberation_entries`

### `GET /api/v1/review-runs/{run_id}`

No route change.

The detail payload remains the main review artifact inspection surface and still exposes:

- review-run metadata
- persisted agent reviews
- conflicts
- scorecard
- committee report
- audit events

Because `agent_reviews` already persist the full review payload, adaptive routing data now appears through each agent review's `review_metadata` object without a schema break.

Additive `review_metadata` fields now used by Milestone 13:

- `activation_tier`
- `activation_status`
- `activation_reason`
- `routing_strategy_version`

### `GET /api/v1/review-runs/{run_id}/deliberation`

This remains the main runtime-telemetry and Committee Mode data source.

Milestone 13 additive runtime metadata:

- `routing_strategy_version`
- `core_executed_count`
- `activated_specialist_count`
- `passive_observer_count`
- `routing_signals`
- `agents[]`
  - `activation_tier`
  - `activation_status`
  - `activation_reason`
  - `duration_ms`
  - `input_tokens`
  - `output_tokens`
  - `total_tokens`
  - `estimated_cost_usd`

Fallback visibility remains explicit:

- `requested_runtime_mode`
- `effective_runtime_mode`
- `fallback_applied`
- `fallback_reason`
- `fallback_category`

### `GET /api/v1/review-runs/{run_id}/deliberation/summary`

No payload redesign.

Committee Mode still uses this endpoint for:

- phase labels
- phase counts
- phase representative statements
- final recommendation
- weighted composite score
- active artifact source

### History and artifact endpoints

Milestone 13 does not redesign:

- `/api/v1/portfolios/{portfolio_id}/history`
- `/api/v1/review-runs/{run_id}/artifacts`
- `/api/v1/debates/{debate_id}/artifacts`
- `/api/v1/re-syntheses/{resynthesis_id}/artifacts`

All approved lineage and artifact-selection semantics remain intact.

## Web contract impact

Committee Mode and review-run detail now consume the additive adaptive telemetry fields above.

UI routes strengthened by Milestone 13:

- `/`
  - workspace copy aligned to adaptive llm-first execution
- `/review-runs/{run_id}`
  - adaptive routing counts and routing signals
- `/review-runs/{run_id}/committee`
  - agent activation status
  - passive-observer visibility
  - routing metadata
  - `0.5x` playback speed
- `/review-runs/{run_id}/deliberation`
  - static view copy aligned to adaptive committee semantics

## Persistence and migration impact

Milestone 13 does not introduce a new persistence table and does not require a new Alembic revision.

Reasons:

- adaptive routing data is persisted inside existing JSON payload boundaries
- runtime routing summary is persisted through existing audit-event payloads
- existing tables remain authoritative

Database schema impact:

- no destructive schema change
- no new table
- no new index in this milestone

The current persistence schema version therefore remains:

- `m12.2-v1`

## Archived baseline parity

Archived deterministic parity remains green.

Milestone 13 keeps archived-baseline validation stable by stripping additive adaptive fields from parity normalization:

- `activation_tier`
- `activation_status`
- `activation_reason`
- `routing_strategy_version`

This prevents false baseline drift while still failing on actual committee-output changes.

## Non-goals preserved

Milestone 13 does not:

- redesign conflicts, debate, or re-synthesis
- introduce new provider-backed debate stages
- add async job queues or distributed orchestration
- redesign historical artifacts or Committee Mode playback semantics
- replace deterministic execution support
