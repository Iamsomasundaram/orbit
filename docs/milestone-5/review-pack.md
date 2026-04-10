# ORBIT Milestone 5 Review Pack

## Scope Delivered

- added bounded debate initiation from persisted review-run state
- added deterministic moderator-controlled conflict resolution using structured persisted artifacts only
- persisted debate artifacts through the existing worker persistence boundary:
  - `debate_sessions`
  - `conflict_resolutions`
  - debate audit events
- exposed debate retrieval APIs without changing the approved scorecard or committee report generation behavior
- kept the JS baseline reference-only and moved its archival target to `Milestone 6`

## Architecture Decisions

- Debate remains synchronous and bounded.
  - This milestone explicitly avoids async job queues and long-running orchestration redesign.
- One debate session is allowed per review run.
  - The service prevents duplicate debate creation and the persistence model enforces `run_id` uniqueness in `debate_sessions`.
- Debate is derived from persisted structured state, not reparsed text.
  - Inputs are the stored `agent_reviews` and `conflicts` for a completed review run.
- Debate does not mutate the committee scorecard.
  - Resolutions can mark `score_change_required`, but score recalculation is deferred to a later milestone if needed.
- Debate audit events stay in the shared `audit_events` table for now.
  - Retrieval filters debate-scoped actions rather than splitting audit storage prematurely.

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `14 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `14 passed`
- `docker compose ps`
  - result: `api`, `web`, `worker`, `postgres`, and `redis` healthy

Live API validation completed on April 10, 2026:

- `POST /api/v1/portfolios/strong-ai-saas-001/review-runs`
  - created run `review-strong-ai-saas-001-20260410T055330553109Z`
- `POST /api/v1/review-runs/review-strong-ai-saas-001-20260410T055330553109Z/debates`
  - created debate `debate-review-strong-ai-saas-001-20260410T055330553109Z`
- `GET /api/v1/review-runs/review-strong-ai-saas-001-20260410T055330553109Z/debates`
  - returned `1` persisted debate session
- `GET /api/v1/debates/debate-review-strong-ai-saas-001-20260410T055330553109Z`
  - returned `5` conflicts, `5` conflict resolutions, `6` debate audit events
- repeated debate creation attempt
  - returned `409 Conflict`

Observed committee outcome for the validated run:

- agents executed: `15`
- conflicts detected: `5`
- final recommendation: `Proceed with Conditions`
- weighted composite score: `3.61`
- score-change-required count after debate: `0`

## Risks

Technical risk:

- migration tooling is still not in place; schema evolution still relies on SQLAlchemy `create_all` instead of Alembic-managed migrations
- preexisting locally stored canonical portfolio rows may still show older `schema_version` values until they are re-ingested
- audit-event separation between review and debate scopes still depends on action filtering within a shared table

Product risk:

- debate is deterministic and rule-based in this milestone, so it proves control flow and persistence but not provider-backed reasoning quality
- resolution outcomes currently add conditions and recheck flags only; they do not yet feed a downstream committee re-synthesis step

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
- `GET http://localhost:5001/api/v1/debates/{debate_id}`

Reference health checks:

- `http://localhost:5001/health/ready`
- `http://localhost:5004/health/ready`
- `http://localhost:5000/api/health/ready`

## Review Checklist

- all 15 agents still participate in the persisted review path
- debate operates on structured persisted conflicts and agent reviews only
- conflict resolutions persist separately from the original conflict records
- committee scorecard and report remain unchanged unless a future milestone explicitly implements score recheck handling
- Docker Compose remains the primary development workflow
- JS baseline remains frozen reference-only, not the active backend direction

## Carry-Forward

- improve duplicate submission handling with DB-backed conflict enforcement
- keep migration tooling planning active
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event separation between ingestion and review or debate scopes later if needed

## Recommendation

Proceed with fixes.

The bounded debate engine is implemented, persisted, and validated. The next gate should address schema migration discipline and any follow-on score recheck or committee re-synthesis behavior without changing the approved Milestone 5 behavior retroactively.
