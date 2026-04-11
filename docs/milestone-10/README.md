# ORBIT Milestone 10

Milestone 10 introduces the first llm-backed ORBIT committee while preserving the deterministic committee engine as a fallback runtime mode. The approved review, conflict, debate, re-synthesis, history, artifact, and multi-portfolio workspace behavior remain intact; the change is in how the 15 specialist agent reviews are produced before the deterministic governance stages run.

Delivered:

- llm-backed committee execution with 15 real committee agents
  - Product Strategy Agent
  - Market Opportunity Agent
  - Customer Value Agent
  - Business Model Agent
  - Finance Agent
  - Competitive Landscape Agent
  - Growth / GTM Agent
  - Architecture Agent
  - AI Systems Agent
  - Security & Compliance Agent
  - Operations / Reliability Agent
  - Data Strategy Agent
  - Risk & Governance Agent
  - Implementation Feasibility Agent
  - Investment Committee Agent
- runtime-mode support through environment configuration
  - `LLM_RUNTIME_MODE=deterministic`
  - `LLM_RUNTIME_MODE=llm`
- provider abstraction for real inference calls
  - `OpenAIResponsesProvider` implemented first
  - Anthropic and local providers left as explicit placeholders
- parallel agent fan-out through `asyncio`
  - bounded concurrency control
  - timeout safeguards
  - deterministic result aggregation order
- compact prompt composition for token discipline
  - shared portfolio context serialized once
  - role-specific evaluation instructions per agent
  - strict structured output schema
  - short reasoning summaries
  - max output token guardrails
- deterministic post-llm normalization
  - score calibration caps tie dimension scores back to evidence completeness, recommendation tier, and risk severity
  - conflict detection, committee scoring, debate, and re-synthesis remain the existing deterministic governance layers
- mocked provider integration coverage for the full workflow
  - validates 15-agent parallel fan-out
  - validates persisted review, debate, and re-synthesis artifacts in llm mode
- live OpenAI-backed Docker validation path using `key.txt`
  - `key.txt` remains local-only and is ignored by git

Primary files:

- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/llm_provider.py`
- `apps/worker/orbit_worker/llm_specs.py`
- `apps/worker/orbit_worker/runner.py`
- `apps/api/orbit_api/review_runs.py`
- `apps/api/orbit_api/health.py`
- `apps/worker/orbit_worker/service.py`
- `apps/worker/tests/test_llm_review_workflow.py`

Token economics strategy:

- shared portfolio context is serialized once as compact JSON containing section summaries and key points only
- prompts forbid chain-of-thought and require concise structured JSON
- each agent is limited to its owned score dimensions
- evidence references are constrained to `portfolio.<section_key>` values
- output size is bounded with `LLM_MAX_OUTPUT_TOKENS`
- the default local model for Milestone 10 is `gpt-4o-mini` to control latency and cost

Parallel execution strategy:

- `AgentInferenceService` fans out 15 agent calls concurrently with `asyncio.gather`
- an `asyncio.Semaphore` enforces bounded concurrency via `LLM_MAX_CONCURRENCY`
- result order remains deterministic by registry order even though execution is concurrent
- the conflict detector, scorecard builder, report generator, debate service, and re-synthesis service still run on the structured outputs after fan-out completes

Validation snapshot from April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `38 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `38 passed`
- mocked llm workflow validation
  - result: passed inside `apps/worker/tests/test_llm_review_workflow.py`
  - confirms:
    - 15 llm agents execute
    - parallel fan-out occurs (`max_active_requests > 1`)
    - persisted debate runs
    - persisted re-synthesis runs when a mocked critical score divergence requires recheck
- live OpenAI-backed validation in Docker Compose
  - runtime mode: `llm`
  - provider: `openai`
  - model: `gpt-4o-mini`
  - best observed local wall-clock runtime on `strong-ai-saas-001`: `14.60s` at `LLM_MAX_CONCURRENCY=15`
  - observed output:
    - `15` agent reviews
    - `6` conflicts
    - debate created with `debate_status=completed`
    - `score_change_required_count=0`
    - final recommendation `Pilot Only`
    - weighted composite score `3.48`

Notes:

- the live llm committee path is working and persists through the approved artifact boundary
- the best observed runtime is still above the under-10-second target, so performance remains a follow-up item rather than a blocked implementation item
- deterministic fallback remained artifact-identical to the archived baseline set

This milestone stops after llm-backed committee execution, validation, and the Ralph review pack are complete.
