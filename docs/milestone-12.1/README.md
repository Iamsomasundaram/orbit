# ORBIT Milestone 12.1

Milestone 12.1 improves the usability, clarity, and observability of Committee Mode without changing the approved review, debate, re-synthesis, or persistence flow. The experience still replays persisted deliberation records only. No new LLM calls are introduced.

Delivered:

- stronger agent identity treatment in Committee Mode
  - persistent role cards
  - avatar / initials
  - stance badges
  - reasoning snapshot
- enhanced conflict spotlight
  - conflict topic
  - participating agents
  - stance-aware position cards
  - moderator interpretation
- playback speed control
  - `1x`
  - `2x`
  - `5x`
  - `instant`
- runtime telemetry display in the Committee Mode header
  - runtime mode
  - provider
  - model
  - agent count
  - total tokens
  - per-agent token telemetry
  - estimated cost
- deterministic compatibility preserved
  - deterministic runs render zero-token telemetry
- archived baseline protection preserved
  - committed baseline artifacts were not regenerated
  - parity now normalizes additive zero-token telemetry fields while still failing on frozen artifact drift

Primary files:

- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/committee/page.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/layout.tsx`
- `apps/web/app/api/health/live/route.ts`
- `apps/web/lib/orbit-api.ts`
- `apps/web/lib/config.ts`
- `apps/api/orbit_api/deliberations.py`
- `apps/api/orbit_api/config.py`
- `apps/api/orbit_api/health.py`
- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/llm_provider.py`
- `apps/worker/orbit_worker/reviewer.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/tests/test_deliberation_service.py`
- `apps/worker/tests/test_llm_review_workflow.py`
- `apps/worker/tests/test_thin_slice_parity.py`

Validation snapshot from April 12, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `43 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `43 passed`
- live deterministic validation run
  - portfolio id: `strong-ai-saas-001`
  - run id: `review-strong-ai-saas-001-20260412T062417384254Z`
  - recommendation: `Proceed with Conditions`
  - weighted composite score: `3.61`
  - active artifact source: `original`
  - persisted deliberation entries: `53`
  - phases returned: `5`
  - runtime metadata:
    - mode `deterministic`
    - agent count `15`
    - total tokens `0`
    - estimated cost `0.0`
- Committee Mode route
  - `GET /review-runs/{run_id}/committee`
  - result: `200`
  - verified sections:
    - `Committee Runtime Metadata`
    - `Agent Identity Lineup`
    - `Playback speed`
    - `Conflict Spotlight`

Validation note:

- the repo still does not include browser automation for click-level playback assertions, so playback interaction was validated through the rebuilt web route, server-rendered page content checks, and client-code inspection of the Committee Mode controller

This milestone stops after the Committee Mode improvements, Docker validation, documentation, and Ralph review pack are complete.
