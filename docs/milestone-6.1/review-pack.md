# ORBIT Milestone 6.1 Review Pack

## Scope Delivered

- added Alembic configuration and the initial persistence baseline revision
- replaced API startup `create_all` behavior with migration-driven schema readiness
- added migration bootstrap logic for legacy local dev databases that already match the approved baseline
- strengthened DB-backed duplicate enforcement for:
  - portfolio submission
  - debate creation
  - re-synthesis creation
- added persistence regression tests covering migration setup and original-versus-resynthesized artifact selection
- preserved approved review, debate, and re-synthesis behavior and table semantics

## Architecture Decisions

- Alembic is now authoritative for persistence schema evolution.
  - `SqlAlchemyPersistenceRepository` no longer creates tables implicitly at startup.
- Migration bootstrap is explicit and bounded.
  - Fresh databases upgrade normally.
  - Legacy local dev databases are stamped only when the existing schema fully matches the baseline.
  - Partial legacy schemas fail fast instead of being silently accepted.
- Bounded create paths now rely on repository-level conflict handling.
  - `save_portfolio_bundle` is create-only.
  - `save_debate_bundle` and `save_resynthesis_bundle` are create-only.
  - review persistence keeps portfolio-row upserts where lifecycle state must advance, while run-scoped artifacts remain create-only.
- Artifact semantics remain stable.
  - original review artifacts, debate artifacts, and re-synthesized artifacts stay in their existing dedicated tables.
  - no scorecard or committee-report behavior was changed beyond approved Milestone 6 logic.

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose build migrate api worker web`
  - result: success
- `docker compose up -d postgres redis api worker web`
  - result: success
- `docker compose logs --no-color --tail 80 migrate`
  - result: `Applied migration action: stamp_then_upgrade`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `23 passed`
  - includes:
    - persistence hardening coverage
    - `test_thin_slice_parity.py` frozen-baseline parity assertions

Live API validation completed on April 10, 2026:

- `GET /api/v1/portfolios`
  - returned persisted portfolio `strong-ai-saas-001`
- duplicate `POST /api/v1/portfolios`
  - returned `409 Conflict`
- `POST /api/v1/portfolios/strong-ai-saas-001/review-runs`
  - created run `review-strong-ai-saas-001-20260410T082713877685Z`
- `POST /api/v1/review-runs/review-strong-ai-saas-001-20260410T082713877685Z/debates`
  - created debate `debate-review-strong-ai-saas-001-20260410T082713877685Z`
- `POST /api/v1/debates/debate-review-strong-ai-saas-001-20260410T082713877685Z/re-synthesis`
  - created re-synthesis `resynthesis-debate-review-strong-ai-saas-001-20260410T082713877685Z`
- `GET /api/v1/re-syntheses/resynthesis-debate-review-strong-ai-saas-001-20260410T082713877685Z`
  - returned `active_artifact_source=original`
  - returned `final_recommendation=Proceed with Conditions`
  - returned `weighted_composite_score=3.61`

Platform health completed on April 10, 2026:

- `http://localhost:5001/health/ready`
  - status: `ok`
- `http://localhost:5004/health/ready`
  - status: `ok`
- `http://localhost:5000/api/health/ready`
  - status: `ok`

## Risks

Technical risk:

- only the initial Alembic baseline exists; follow-on migration authoring discipline still needs to be exercised in later milestones
- source-document artifacts remain local-first and temporary, so persisted metadata and filesystem artifacts can still diverge under local I/O failure
- audit events remain in the shared `audit_events` table and still rely on action filtering by scope

Product risk:

- committee scoring and debate reasoning remain deterministic and bounded, which is correct for this milestone but not a substitute for future provider-backed evaluation depth
- parity expansion beyond the current frozen-baseline fixture set still depends on the existing JS reference artifacts staying curated

Delivery risk:

- indexing strategy is still foundational and not yet tuned for broader workload growth
- CI automation for Compose health, migrations, and parity regression is still pending
- the JS baseline archival step is documented but not yet executed

## Validation

Primary local workflow:

- `docker compose build migrate api worker web`
- `docker compose up -d postgres redis api worker web`
- `docker compose logs --no-color --tail 80 migrate`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`

Reference API checks:

- `POST http://localhost:5001/api/v1/portfolios`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `POST http://localhost:5001/api/v1/review-runs/{run_id}/debates`
- `POST http://localhost:5001/api/v1/debates/{debate_id}/re-synthesis`
- `GET http://localhost:5001/api/v1/re-syntheses/{resynthesis_id}`

Reference health checks:

- `http://localhost:5001/health/ready`
- `http://localhost:5004/health/ready`
- `http://localhost:5000/api/health/ready`

## Review Checklist

- Alembic owns the persistence baseline and startup no longer depends on implicit table creation
- legacy local dev databases are only stamped when they already match the approved baseline
- duplicate portfolio, debate, and re-synthesis creation paths return bounded conflict behavior from DB-backed enforcement
- original and re-synthesized artifact selection remains correct after persistence round-trip
- approved review, debate, and re-synthesis outputs remain unchanged
- Docker Compose remains the primary local workflow
- the JS baseline remains frozen reference-only and the Python worker stays the active backend direction

## Carry-Forward

- source-document artifact strategy remains explicitly local-first and temporary
- audit-event separation can remain shared-table for now unless a later safe refinement is needed
- prepare follow-on Alembic revisions and migration review discipline for later persistence changes
- continue CI automation planning for Compose health, migration checks, and parity regression
- keep the JS baseline archival target at `Milestone 7` until the archival gate is explicitly approved

## Recommendation

Proceed with fixes.

Milestone 6.1 closes the main persistence hardening gap: schema evolution is now migration-driven, bounded duplicate paths are DB-backed, and the approved committee behavior remains intact. The remaining work is mostly operational hardening, not architectural rework.
