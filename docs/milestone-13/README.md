# ORBIT Milestone 13

Milestone 13 upgrades ORBIT from a fixed full-committee llm pass into an adaptive committee architecture. The platform now defaults to `llm` runtime mode, runs a Tier-1 core screening wave first, activates Tier-2 specialists only when the core evidence indicates deeper review is needed, and preserves deterministic fallback plus the existing persisted governance flow.

Delivered:

- llm is now the default runtime mode
  - `LLM_RUNTIME_MODE=llm` is the platform default in `docker-compose.yml`, `.env.example`, API settings, and worker settings
  - deterministic execution remains a supported explicit mode and the automatic fallback path
- adaptive committee execution
  - Tier-1 core agents always execute:
    - Product Strategy
    - Market Opportunity
    - Finance
    - Architecture
    - Risk Governance
  - Tier-2 specialists activate conditionally from core-review signals
  - inactive specialists persist as passive observers when the routing decision does not require deep execution
- deterministic fallback safety
  - provider errors, timeouts, and invalid llm execution outcomes still complete the review through deterministic execution
  - requested versus effective runtime state remains visible in persisted telemetry and the UI
- richer adaptive telemetry
  - per-agent activation tier
  - per-agent activation status
  - per-agent activation reason
  - routing strategy version
  - routing signals
  - core executed count
  - activated specialist count
  - passive observer count
  - committee token and cost totals
- Committee Mode playback enhancement
  - new `0.5x` playback option
  - adaptive-routing telemetry appears in Committee Mode and review-run detail views
- preserved governance flow
  - review artifacts, conflicts, scorecards, committee reports, debates, re-syntheses, history, and deliberation timelines remain backward-compatible
  - no new deliberation or artifact semantics were introduced

Primary files:

- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/llm_specs.py`
- `apps/worker/orbit_worker/llm_provider.py`
- `apps/worker/orbit_worker/reviewer.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/api/orbit_api/config.py`
- `apps/api/orbit_api/health.py`
- `apps/api/orbit_api/deliberations.py`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/page.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/tests-e2e/milestone-12-2.spec.ts`
- `apps/worker/tests/test_llm_review_workflow.py`
- `apps/worker/tests/test_thin_slice_parity.py`
- `docker-compose.yml`
- `.github/workflows/compose-regression.yml`

Validation snapshot from April 12, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `46 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `46 passed`
- `docker compose run --rm browser-tests`
  - result: `2 passed`
- `GET http://localhost:5001/api/v1/system/info`
  - result:
    - `milestone=13`
    - `runtime_mode=llm`
    - `llm_provider=openai`
    - `openai_model=gpt-4o-mini`
    - `llm_max_concurrency=6`
    - `persistence_schema_version=m12.2-v1`
- live API review validation
  - portfolio: `adaptive-m13-live-20260412215602-ac296c0a`
  - run: `review-adaptive-m13-live-20260412215602-ac296c0a-20260412T162602964419Z`
  - result:
    - `effective_runtime_mode=llm`
    - `fallback_applied=false`
    - `agent_review_count=15`
    - `conflict_count=9`
    - `core_executed_count=5`
    - `activated_specialist_count=10`
    - `passive_observer_count=0`
    - `routing_strategy_version=m13-adaptive-v1`
    - `total_tokens=37181`
    - `estimated_cost_usd=0.0090867`
- direct adaptive-provider validation against `procurepilot-thin-slice.md`
  - result:
    - `effective_runtime_mode=llm`
    - `fallback_applied=false`
    - `core_agent_ids=5`
    - `activated_specialist_ids=9`
    - `passive_specialist_ids=1`
    - passive observer: `business_model_agent`

Operational note:

- the original `25` second request safeguard caused live OpenAI runs in this environment to fall back to deterministic mode too aggressively
- Milestone 13 raises the default safeguard to `45` seconds
- fallback safety remains intact and still completed earlier timed-out runs without crashing the platform

This milestone stops after adaptive committee delivery, Docker validation, browser validation, and the Ralph review pack.
