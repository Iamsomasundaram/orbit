# ORBIT Milestone 6 Review Pack

## Scope Delivered

- added bounded re-synthesis initiation from persisted debate state
- added deterministic score recheck logic driven only by persisted conflict resolutions that mark `score_change_required`
- preserved the original committee scorecard and report when no score recheck is required
- persisted re-synthesis artifacts through the existing worker persistence boundary:
  - `resynthesis_sessions`
  - `resynthesized_scorecards`
  - `resynthesized_committee_reports`
  - re-synthesis audit events
- exposed retrieval APIs that show original committee artifacts and the currently active artifact set side by side

## Architecture Decisions

- Re-synthesis is debate-scoped and synchronous.
  - This milestone explicitly avoids async jobs or long-running orchestration redesign.
- One re-synthesis session is allowed per debate session.
  - The API rejects duplicates and the persistence schema enforces uniqueness on `debate_id`.
- Original committee artifacts are preserved.
  - Re-synthesized scorecards and reports are stored in dedicated tables instead of overwriting `scorecards` or `committee_reports`.
- Score recheck remains deterministic and bounded.
  - Re-synthesis uses the approved committee scoring rules, plus explicit downgrade logic triggered by persisted resolution state.
- No-change cases stay no-op.
  - When debate produces zero `score_change_required` resolutions, the system persists only the re-synthesis session and keeps the original committee artifacts active.

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `18 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `18 passed`
- `docker compose ps`
  - result: `api`, `web`, `worker`, `postgres`, and `redis` healthy

Live API validation completed on April 10, 2026:

- `POST /api/v1/portfolios/strong-ai-saas-001/review-runs`
  - created run `review-strong-ai-saas-001-20260410T063048874962Z`
- `POST /api/v1/review-runs/review-strong-ai-saas-001-20260410T063048874962Z/debates`
  - created debate `debate-review-strong-ai-saas-001-20260410T063048874962Z`
- `POST /api/v1/debates/debate-review-strong-ai-saas-001-20260410T063048874962Z/re-synthesis`
  - created re-synthesis `resynthesis-debate-review-strong-ai-saas-001-20260410T063048874962Z`
- `GET /api/v1/debates/debate-review-strong-ai-saas-001-20260410T063048874962Z/re-synthesis`
  - returned `1` persisted re-synthesis session
- `GET /api/v1/re-syntheses/resynthesis-debate-review-strong-ai-saas-001-20260410T063048874962Z`
  - returned original scorecard and report as the active artifacts, with `resynthesized_scorecard=null` and `resynthesized_committee_report=null`
- repeated re-synthesis creation attempt
  - returned `409 Conflict`

Observed live no-change outcome:

- agents executed in underlying review run: `15`
- conflicts detected in underlying review run: `5`
- debate score-change-required count: `0`
- re-synthesis status: `completed_without_changes`
- active artifact source: `original`
- final recommendation remained `Proceed with Conditions`
- weighted composite remained `3.61`

Forced recheck path validated in worker tests:

- one persisted resolution was marked `score_change_required=true`
- re-synthesis materialized both replacement artifacts
- active recommendation downgraded from `Proceed with Conditions` to `Pilot Only`
- weighted composite score decreased from the original scorecard

## Risks

Technical risk:

- migration tooling is still not in place; schema evolution still relies on SQLAlchemy `create_all` instead of Alembic-managed migrations
- preexisting locally stored canonical portfolio rows may still show older schema versions until they are re-ingested
- audit-event separation still relies on action filtering within a shared table

Product risk:

- recheck logic is deterministic and rule-based in this milestone; it proves the bounded control flow but not provider-backed reasoning quality
- only scorecard and report are re-synthesized; no broader committee rerun or new debate loop is introduced

Delivery risk:

- duplicate submission handling is still enforced at the application layer rather than by stronger database-backed conflict handling
- source-document storage remains local-first and temporary, which is acceptable for current local development but not durable production artifact management

## Validation

Primary local workflow:

- `docker compose up -d --build postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `POST http://localhost:5001/api/v1/review-runs/{run_id}/debates`
- `POST http://localhost:5001/api/v1/debates/{debate_id}/re-synthesis`
- `GET http://localhost:5001/api/v1/re-syntheses/{resynthesis_id}`

Reference health checks:

- `http://localhost:5001/health/ready`
- `http://localhost:5004/health/ready`
- `http://localhost:5000/api/health/ready`

## Review Checklist

- re-synthesis consumes persisted debate resolutions only
- no-change debates preserve the original scorecard and report as the active artifacts
- recheck-required debates materialize replacement scorecard and report artifacts without overwriting the originals
- original review-run and debate artifacts remain durable and retrievable
- Docker Compose remains the primary development workflow
- JS baseline remains frozen reference-only, not the active backend direction

## Carry-Forward

- improve duplicate submission handling with DB-backed conflict enforcement
- keep migration tooling planning active
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event separation later if needed

## Recommendation

Proceed with fixes.

The bounded re-synthesis path is implemented, persisted, and validated. The next gate should focus on migration discipline and stronger persistence safeguards without broadening beyond the approved Milestone 6 behavior.
