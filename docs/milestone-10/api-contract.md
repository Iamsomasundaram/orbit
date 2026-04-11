# ORBIT Milestone 10 API Contract

Milestone 10 does not introduce new portfolio, review, debate, history, or artifact endpoints. Instead, it changes how review runs are executed behind the existing API surface when `LLM_RUNTIME_MODE=llm`.

## Existing endpoints with new runtime behavior

### `POST /api/v1/portfolios/{portfolio_id}/review-runs`

Behavior by runtime mode:

- `deterministic`
  - runs the existing heuristic committee engine
  - remains the artifact-protected fallback runtime
- `llm`
  - runs 15 real llm committee agents in parallel
  - persists structured `agent_reviews`
  - then continues through the existing deterministic:
    - conflict detection
    - bounded debate
    - optional re-synthesis

The response shape is unchanged:

```json
{
  "run_id": "review-strong-ai-saas-001-20260411T171141493734Z",
  "portfolio_id": "strong-ai-saas-001",
  "review_status": "completed",
  "final_recommendation": "Pilot Only",
  "weighted_composite_score": 3.48,
  "agent_review_count": 15,
  "conflict_count": 6,
  "created_at": "2026-04-11T17:11:41.493734Z",
  "completed_at": "2026-04-11T17:11:41.493734Z"
}
```

## Existing artifact and history endpoints remain authoritative

- `GET /api/v1/review-runs/{run_id}`
- `GET /api/v1/review-runs/{run_id}/artifacts`
- `GET /api/v1/portfolios/{portfolio_id}/history`
- `GET /api/v1/debates/{debate_id}`
- `GET /api/v1/debates/{debate_id}/artifacts`
- `GET /api/v1/debates/{debate_id}/re-synthesis`
- `GET /api/v1/re-syntheses/{resynthesis_id}`
- `GET /api/v1/re-syntheses/{resynthesis_id}/artifacts`

These endpoints continue to expose the approved lineage and artifact-selection model. Milestone 10 only changes the upstream generation of `agent_reviews` in llm mode.

## Health and runtime reporting

### `GET /api/v1/system/info`

Milestone 10 extends the info payload with runtime-mode reporting:

```json
{
  "service": "orbit-api",
  "status": "ok",
  "milestone": "10",
  "runtime_direction": "llm-backed-parallel-committee-engine",
  "runtime_mode": "llm",
  "active_backend": "python",
  "reference_runtime": "js-baseline-only",
  "reference_runtime_stage": "archived-baseline",
  "reference_runtime_archival_target_milestone": "Milestone 7.1",
  "llm_max_concurrency": 15,
  "persistence_schema_version": "m6-v1",
  "persistence_tables": 14,
  "environment": "local",
  "llm_provider": "openai",
  "openai_model": "gpt-4o-mini"
}
```

### `GET /`

The worker root info payload now also exposes:

- `runtime_mode`
- `llm_provider`
- `llm_model`
- `llm_max_concurrency`
- `llm_request_timeout_seconds`

## Environment contract

Milestone 10 execution is controlled through environment variables:

- `LLM_RUNTIME_MODE`
  - `deterministic`
  - `llm`
- `LLM_PROVIDER`
  - `openai`
  - `anthropic` placeholder only
  - `local` placeholder only
- `LLM_MAX_CONCURRENCY`
- `LLM_REQUEST_TIMEOUT_SECONDS`
- `LLM_MAX_OUTPUT_TOKENS`
- `OPENAI_API_KEY`
- `OPENAI_API_KEY_FILE`
- `OPENAI_MODEL`

Local Docker-first testing path:

- keep the API key in local `key.txt`
- do not commit `key.txt`
- `OPENAI_API_KEY_FILE` defaults to `/workspace/key.txt` inside the containers

## Persistence compatibility

Milestone 10 keeps the persistence schema unchanged.

The llm runtime continues to populate the same durable artifact tables:

- `review_runs`
- `agent_reviews`
- `conflicts`
- `scorecards`
- `committee_reports`
- debate and re-synthesis tables when triggered

LLM-specific traceability is carried through existing structured fields:

- `agent_reviews.review_payload.review_summary`
- `agent_reviews.review_payload.findings`
- `agent_reviews.review_payload.dimension_scores`
- `agent_reviews.review_payload.review_metadata`
  - `prompt_contract_version`
  - `model_provider`
  - `model_name`
  - `duration_ms`
