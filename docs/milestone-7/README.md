# ORBIT Milestone 7

Milestone 7 adds auditable review history and artifact-lineage visibility across persisted portfolios, review runs, debates, and re-syntheses without changing the approved committee behavior.

Delivered:

- portfolio history retrieval at `GET /api/v1/portfolios/{portfolio_id}/history`
- artifact inspection retrieval at:
  - `GET /api/v1/review-runs/{run_id}/artifacts`
  - `GET /api/v1/debates/{debate_id}/artifacts`
  - `GET /api/v1/re-syntheses/{resynthesis_id}/artifacts`
- lineage-oriented response models that expose:
  - portfolio -> review run -> debate -> re-synthesis relationships
  - original versus active artifact ownership
  - active artifact source selection
  - scoped review, debate, and re-synthesis audit events
- regression coverage for:
  - portfolio history ordering and lineage retrieval
  - original artifact inspection before follow-up sessions
  - debate lineage inspection
  - re-synthesis artifact selection for unchanged and score-recheck paths
- Docker-first validation against the live platform stack

Boundaries kept intact:

- approved review, debate, and re-synthesis behavior stays unchanged
- committee scoring logic and recommendation outcomes stay unchanged
- orchestration remains synchronous and bounded
- provider-backed reasoning, async job systems, and major frontend expansion remain out of scope
- the JS baseline remains `frozen-baseline` reference-only and its archival execution is carried forward to `Milestone 7.1`

Primary files:

- `apps/api/orbit_api/history.py`
- `apps/api/orbit_api/main.py`
- `apps/worker/tests/test_history_service.py`
- `apps/web/app/page.tsx`
- `README.md`

Validation snapshot from April 10, 2026:

- `docker compose up -d api worker web`
  - result: success
- `docker compose ps`
  - result: `api`, `worker`, `web`, `postgres`, and `redis` healthy
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `28 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `28 passed`
- live API validation created:
  - review run `review-strong-ai-saas-001-20260410T112228673688Z`
  - debate `debate-review-strong-ai-saas-001-20260410T112228673688Z`
  - re-synthesis `resynthesis-debate-review-strong-ai-saas-001-20260410T112228673688Z`
- live history and artifact inspection returned:
  - latest lineage pointing to the new review run, debate, and re-synthesis
  - `active_artifact_source=original`
  - `final_recommendation=Proceed with Conditions`
  - `weighted_composite_score=3.61`
  - review audit actions scoped to `review_run.completed` and `committee_report.materialized`

This milestone stops after history visibility, artifact inspection, validation, and the Ralph review pack are complete.
