# ORBIT Milestone 12.1 API Contract

Milestone 12.1 does not add new reasoning endpoints. It strengthens the Committee Mode presentation by exposing runtime telemetry already carried in persisted review metadata and by consuming the existing deliberation APIs more richly.

## Existing API surface used by Committee Mode

### `GET /api/v1/review-runs/{run_id}/deliberation`

Milestone 12.1 continues to fetch the full ordered deliberation timeline once and drive playback locally in the browser.

The response now includes `runtime_metadata` for Committee Mode observability:

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
- `agents[]`

Each `agents[]` entry exposes per-agent telemetry:

- `agent_id`
- `agent_role`
- `recommendation`
- `model_provider`
- `model_name`
- `duration_ms`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost_usd`

Usage in Milestone 12.1:

- render the Committee Runtime Metadata panel
- render the Agent Identity Lineup
- show per-agent token usage and estimated cost
- keep deterministic runs visible with zero-token telemetry
- preserve the same persisted `sequence_number` order for playback
- preserve `conflict_reference` values for conflict spotlight rendering

### `GET /api/v1/review-runs/{run_id}/deliberation/summary`

This endpoint remains unchanged and continues to drive:

- phase labels and counts
- representative phase summaries
- final recommendation
- weighted composite score
- active artifact source

## UI route

Milestone 12.1 keeps the existing web route:

- `/review-runs/{run_id}/committee`

Behavior:

- fetches the two persisted deliberation endpoints server-side
- passes the persisted data into the client-side Committee Mode controller
- adjusts playback speed locally in the browser only
- performs no new server-side reasoning
- performs no new LLM calls

## Playback behavior

Committee Mode playback remains derived only from stored deliberation records:

- reveals entries in persisted order
- supports pause / resume without refetching
- supports skipping to the next phase
- supports jumping to the final verdict
- supports `1x`, `2x`, `5x`, and `instant` pacing locally in the browser
- highlights conflicts using persisted conflict references and persisted reasoning statements

## Persistence impact

Milestone 12.1 does not add a new table and does not add a new Alembic revision.

Persistence remains non-breaking:

- review artifacts unchanged
- debate artifacts unchanged
- re-synthesized artifacts unchanged
- deliberation timeline structure unchanged

Runtime telemetry is derived from the already persisted `review_metadata` content in `agent_reviews`. Deterministic runs keep these values at zero.
