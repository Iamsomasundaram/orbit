# ORBIT Milestone 10 Review Pack

## Scope Delivered

- added a real llm-backed committee engine behind the existing review-run API
- preserved the deterministic engine as a fallback runtime mode
- implemented 15 llm committee agents with structured outputs compatible with the existing `agent_reviews` persistence model
- added provider abstraction with OpenAI implemented first and Anthropic/local placeholders kept explicit
- added parallel agent fan-out with bounded concurrency and timeout safeguards
- preserved deterministic conflict detection, debate, re-synthesis, scoring, history, and artifact behavior
- added mocked-provider integration coverage for the full llm workflow
- added local Docker-first OpenAI validation using `key.txt` without committing the key file

## Architecture Decisions

- the llm runtime is an insertion layer, not a committee redesign
  - agent generation changed
  - downstream governance remained the same
- `CommitteeRuntimeOptions` controls runtime mode and llm limits
  - `deterministic` keeps the approved fallback path
  - `llm` enables real provider-backed agent generation
- `AgentInferenceService` handles parallel fan-out
  - shared context is serialized once
  - role-specific prompts stay compact
  - `asyncio.Semaphore` enforces bounded concurrency
  - `asyncio.gather` preserves deterministic result ordering
- `OpenAIResponsesProvider` encapsulates OpenAI-specific inference calls
  - no direct provider calls live in agent business logic
  - the design leaves a clean future boundary for Anthropic and local inference
- llm outputs are normalized before persistence
  - evidence references are constrained to known `portfolio.<section_key>` values
  - dimension scores are capped deterministically against recommendation tier, evidence completeness, and risk severity
  - this keeps llm optimism from bypassing the approved scoring discipline
- no persistence schema change was introduced
  - llm reasoning rides inside the existing structured review payloads

## Token Economics Strategy

- shared portfolio context is serialized once as compact JSON using section summaries and key points only
- prompts forbid chain-of-thought and require concise reasoning summaries
- each agent is constrained to its owned score dimensions
- evidence references are restricted to a fixed allowed set
- response size is bounded with `LLM_MAX_OUTPUT_TOKENS`
- the default local model is `gpt-4o-mini` to favor speed and cost discipline

## Parallel Execution Model

- 15 agent calls are fanned out concurrently
- concurrency is bounded by `LLM_MAX_CONCURRENCY`
- per-agent inference is timeout-protected
- result collection stays deterministic by registry order
- deterministic aggregation starts only after fan-out completes:
  - conflict detection
  - committee scorecard
  - committee report
  - debate
  - optional re-synthesis

## Quality Status

Automated validation completed on April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `38 passed`
  - includes:
    - deterministic fallback coverage
    - workspace/history/artifact coverage
    - mocked llm workflow coverage
    - parallel fan-out assertion
    - debate and re-synthesis integration under llm mode
- `docker compose --profile baseline run --rm worker-parity`
  - result: `38 passed`

Live llm validation completed on April 11, 2026:

- runtime info:
  - `runtime_mode=llm`
  - `llm_provider=openai`
  - `openai_model=gpt-4o-mini`
- first live OpenAI run at `LLM_MAX_CONCURRENCY=10`
  - wall-clock runtime: `23.28s`
  - output:
    - `15` agent reviews
    - `6` conflicts
    - `Pilot Only`
    - `3.52`
    - `debate_status=completed`
- best observed live OpenAI run at `LLM_MAX_CONCURRENCY=15`
  - run id: `review-strong-ai-saas-001-20260411T171141493734Z`
  - wall-clock runtime: `14.60s`
  - output:
    - `15` agent reviews
    - `6` conflicts
    - `Pilot Only`
    - `3.48`
    - `active_artifact_source=original`
    - `score_change_required_count=0`
    - `debate_status=completed`

Live web/API surface validation completed on April 11, 2026:

- `GET http://localhost:5000/api/health/live`
  - returned `milestone=10`
- `GET http://localhost:5001/api/v1/system/info`
  - returned Milestone 10 runtime metadata including:
    - `runtime_direction=llm-backed-parallel-committee-engine`
    - `runtime_mode=llm`
    - `llm_max_concurrency=15`
- `GET http://localhost:5000`
  - rendered Milestone 10 workspace copy with `Parallel LLM Committee`

## Risks

Technical risk:

- the live llm path is working, but the best observed local runtime is still `14.60s`, which is above the under-10-second target
- provider-backed scoring is still sensitive to prompt calibration; deterministic score caps reduce optimism, but more empirical tuning is still warranted
- Anthropic and local providers remain placeholders
- the markdown document-submission path still uses the older identity and double-parsing behavior

Product risk:

- llm-backed committee outcomes are now more realistic than the first uncalibrated run, but further calibration data is still needed before committee outputs should be treated as production-grade investment recommendations
- the current UI does not yet visualize individual agent reasoning or disagreement details, even though the persisted data now supports that future direction

Delivery risk:

- no schema change was required in Milestone 10, so future llm-specific observability requirements still need to fit within the current persistence contract or be introduced through a later migration
- source-document storage remains local-first and temporary
- audit-event query boundaries remain shared-table

## Validation

Primary deterministic fallback workflow:

- `docker compose run --rm migrate`
- `docker compose up -d --build postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference live llm workflow:

- keep the API key in local `key.txt`
- restart services with:
  - `LLM_RUNTIME_MODE=llm`
  - `OPENAI_MODEL=gpt-4o-mini`
  - `LLM_MAX_CONCURRENCY=15`
- run:
  - `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
  - `GET http://localhost:5001/api/v1/review-runs/{run_id}/artifacts`

## Review Checklist

- deterministic fallback remains green against archived baseline artifacts
- llm runtime is selectable by environment configuration
- OpenAI inference is isolated behind a provider boundary
- 15 llm agents execute in parallel with bounded concurrency
- structured outputs still persist through the existing artifact boundary
- debate remains triggered from persisted conflicts
- re-synthesis remains triggered only when debate marks score change required
- the API and web surfaces expose Milestone 10 runtime information without requiring new endpoints
- `key.txt` remains local-only and ignored by git

## Carry-Forward

- extend the safer bounded identity strategy to the markdown document-submission path if that path remains user-facing
- reduce double parsing in the original markdown document-submission path if it can be done without risking canonical drift
- keep Alembic migration authoring discipline active for future schema changes
- consider composite index tuning if workspace/history query volume grows materially
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event query boundaries later if a small safe improvement becomes worthwhile
- continue performance tuning toward the under-10-second local llm target
- add future provider implementations behind the existing abstraction boundary

## Recommendation

Proceed with fixes.

Milestone 10 delivers a working provider-backed committee engine without breaking the validated deterministic governance stack. The remaining work is performance tuning, calibration, and future visualization depth rather than a change in committee architecture or persistence direction.
