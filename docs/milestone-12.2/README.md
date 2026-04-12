# ORBIT Milestone 12.2

Milestone 12.2 hardens the existing ORBIT platform without changing review semantics, committee scoring, debate behavior, or re-synthesis rules. The work is operational and UX-focused: reliable web interactions, browser automation coverage, richer telemetry, deterministic fallback safety, safer markdown ingestion, conflict explainability, query/index improvements, clearer source-artifact boundaries, and cleaner audit scopes.

Delivered:

- Playwright browser automation harness
  - portfolio creation flow
  - review trigger flow
  - review-run detail and telemetry inspection
  - Committee Mode playback controls
  - static deliberation timeline inspection
  - multi-portfolio comparison flow
- browser automation in CI
  - Compose-based GitHub workflow now runs worker tests, archived-baseline parity, and browser automation
- UI interaction hardening
  - client-side portfolio creation with loading and inline error handling
  - client-side review trigger with loading and inline error handling
  - stable selectors for workspace, detail, and Committee Mode controls
- deeper runtime telemetry surfaces
  - review-run detail page
  - Committee Mode header and fallback panel
  - requested versus effective runtime mode
  - provider, model, duration, token, and cost visibility
- deterministic fallback safety
  - llm runtime errors now fall back to deterministic execution
  - fallback state is logged and persisted through review audit events
  - fallback is visible in deliberation telemetry and the review-run UI
- markdown submission hardening
  - bounded portfolio-id normalization
  - single-pass markdown parsing in the persisted document-submission path
  - stable source-document rebinding to persisted local artifact paths
- conflict metadata enrichment
  - `conflicting_agents`
  - `conflict_category`
  - `conflict_reason`
- query and indexing hardening
  - composite indexes for review history, debate history, re-synthesis history, and audit timelines
  - Alembic migration `20260412_01`
- audit event boundary cleanup
  - explicit creation events for review, debate, and re-synthesis
  - review-scope fallback event for llm-to-deterministic runtime changes
- source artifact handling clarified
  - source documents remain local-first under `PORTFOLIO_STORAGE_DIR`
  - no cloud or remote artifact storage introduced

Primary files:

- `apps/api/alembic/versions/20260412_01_m122_query_hardening.py`
- `apps/api/orbit_api/deliberations.py`
- `apps/api/orbit_api/history.py`
- `apps/api/orbit_api/portfolios.py`
- `apps/api/orbit_api/review_runs.py`
- `apps/web/app/page.tsx`
- `apps/web/app/home-submission-card.tsx`
- `apps/web/app/portfolio-review-action.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/review-runs/[runId]/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`
- `apps/web/playwright.config.ts`
- `apps/web/tests-e2e/milestone-12-2.spec.ts`
- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/conflicts.py`
- `apps/worker/orbit_worker/ingestion.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/tests/test_llm_review_workflow.py`
- `apps/worker/tests/test_persistence_models.py`
- `apps/worker/tests/test_portfolio_ingestion_service.py`
- `apps/worker/tests/test_thin_slice_parity.py`
- `.github/workflows/compose-regression.yml`
- `docker-compose.yml`

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
    - `milestone=12.2`
    - `runtime_mode=deterministic`
    - `persistence_schema_version=m12.2-v1`
    - `llm_provider=openai`
    - `openai_model=gpt-4o-mini`
- `GET http://localhost:5000`
  - result: `200`

Browser validation scenarios covered in Milestone 12.2:

- create portfolio through the UI and confirm redirect to history
- trigger a review from the UI and confirm result rendering
- open review-run detail and inspect telemetry plus persisted conflicts
- open Committee Mode, change playback speed, run playback, skip phase, and jump to final verdict
- open the static deliberation timeline page
- create a second portfolio and compare multiple portfolios side by side

This milestone stops after hardening, Docker validation, browser automation validation, documentation, and the Ralph review pack are complete.
