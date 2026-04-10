# ORBIT Milestone 6.1

Milestone 6.1 hardens the persistence layer and schema-evolution discipline introduced through Milestones 2 to 6 without changing the approved committee behavior.

Delivered:

- Alembic configuration and an initial persistence baseline revision at `20260410_01`
- a migration bootstrap path that:
  - upgrades a fresh local database to the baseline
  - stamps a legacy local dev database when the existing schema already matches the baseline
- API startup gated on migrated schema readiness instead of implicit `create_all`
- stronger DB-backed duplicate enforcement for:
  - portfolio submission
  - one debate per review run
  - one re-synthesis per debate
- persistence regression coverage for:
  - Alembic baseline creation
  - migration bootstrap classification
  - DB-backed duplicate enforcement
  - original versus re-synthesized artifact selection

Boundaries kept intact:

- original review artifacts, debate artifacts, and re-synthesized artifacts keep their approved table semantics
- approved committee scoring and outcomes remain unchanged
- Docker Compose remains the primary development workflow
- the JS baseline remains `frozen-baseline` reference-only with archival target `Milestone 7`
- no provider-backed reasoning, async job systems, or major frontend work was introduced

Primary files:

- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/versions/20260410_01_m61_initial_persistence_baseline.py`
- `apps/api/orbit_api/migrations.py`
- `apps/api/orbit_api/main.py`
- `apps/api/orbit_api/portfolios.py`
- `apps/api/orbit_api/debates.py`
- `apps/api/orbit_api/resyntheses.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/tests/test_persistence_hardening.py`

Validation snapshot from April 10, 2026:

- migrated stack startup succeeded with `stamp_then_upgrade` against the existing local dev database
- worker pytest suite: `23 passed`
- the suite includes `test_thin_slice_parity.py`, so frozen-baseline parity remained green while the persistence hardening tests were added
- live duplicate portfolio submission returned `409 Conflict`
- live review, debate, and re-synthesis still produced:
  - `15` agents
  - `5` conflicts
  - `Proceed with Conditions`
  - `3.61`
  - `active_artifact_source=original`

This milestone stops after migration discipline, persistence hardening, regression coverage, and the Ralph review pack are complete.
