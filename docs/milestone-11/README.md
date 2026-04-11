# ORBIT Milestone 11

Milestone 11 introduces a persisted committee deliberation timeline for each review run. The timeline is derived from the artifacts already produced by the approved ORBIT review path: agent reviews, conflicts, bounded debate, optional re-synthesis, and the active verdict. No additional LLM calls are introduced in this milestone.

Delivered:

- persisted deliberation timeline entries for each review run
  - opening statements
  - conflict identification
  - conflict discussion
  - moderator synthesis
  - final verdict
- deterministic derivation from existing persisted artifacts
  - no synthetic chat transcript layer
  - no new reasoning stage
  - no added token cost
- Alembic-managed schema extension
  - new revision `20260411_01`
  - new durable table `deliberation_entries`
- API support for timeline retrieval
  - `GET /api/v1/review-runs/{run_id}/deliberation`
  - `GET /api/v1/review-runs/{run_id}/deliberation/summary`
- automatic rematerialization of the timeline when persisted review state changes
  - after review persistence
  - after debate persistence
  - after re-synthesis persistence
- thin server-rendered web visualization
  - new page `/review-runs/{run_id}/deliberation`
  - links added from portfolio detail, history, and comparison pages
- deterministic compatibility preserved
  - deterministic runtime mode still creates deliberation records
  - archived-baseline parity remains green

Primary files:

- `apps/worker/orbit_worker/deliberation.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/api/orbit_api/deliberations.py`
- `apps/api/orbit_api/main.py`
- `apps/api/alembic/versions/20260411_01_m11_deliberation_entries.py`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/lib/orbit-api.ts`
- `apps/worker/tests/test_deliberation_service.py`
- `apps/worker/tests/test_persistence_models.py`

Deliberation model:

- entries are stored in `deliberation_entries`
- each entry includes:
  - `run_id`
  - `portfolio_id`
  - `sequence_number`
  - `phase`
  - `agent_role`
  - `statement_type`
  - `statement_text`
  - optional `conflict_reference`
  - `created_at`
- entry ordering is persisted by `sequence_number`
- the timeline is rewritten from persisted review state when downstream artifacts change, so the active view always matches the current lineage state

Validation snapshot from April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `42 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `42 passed`
- live deterministic validation run
  - run id: `review-strong-ai-saas-001-20260411T180031109996Z`
  - recommendation: `Proceed with Conditions`
  - weighted composite score: `3.61`
  - conflicts: `5`
  - persisted deliberation entries: `53`
  - phases returned: `5`
  - web page `/review-runs/{run_id}/deliberation`
    - result: `200`

This milestone stops after deliberation persistence, API exposure, UI rendering, validation, and the Ralph review pack are complete.
