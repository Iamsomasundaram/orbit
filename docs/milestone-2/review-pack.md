# ORBIT Milestone 2 Review Pack

## Scope Delivered

Completed in this milestone:

- durable persistence models for portfolios, source documents, canonical portfolios, review runs, agent reviews, conflicts, scorecards, committee reports, and audit events
- SQLAlchemy metadata defining the executable Postgres table and index model for the approved runtime artifacts
- persistence repository boundary through an executable `PersistenceRepository` protocol and `InMemoryPersistenceRepository`
- API introspection endpoints for persistence schema catalog and generated Postgres DDL
- committed `docs/milestone-2/postgres-ddl.sql` artifact generated from the executable schema endpoint
- web surface updates showing Milestone 2 schema state and backend direction
- Milestone 2 documentation for data model, persistence boundaries, and carry-forward planning

## Architecture Decisions

- the Python worker contracts remain the sole source of truth for executable backend state
- Milestone 2 wraps the approved runtime outputs in persistence record models rather than redefining the thin-slice behavior
- Postgres-facing schema is generated from SQLAlchemy metadata, with raw structured payloads stored in `JSONB` alongside explicit query columns
- persistence writing is intentionally bounded behind a repository protocol; live DB write orchestration remains out of scope until a later approved milestone
- the JS baseline remains reference-only and is still isolated to the Compose `baseline` profile
- API schema introspection is read-only and exists to validate the persistence contract without broadening into review submission APIs

## Quality Status

Validation executed successfully:

- `docker compose build api worker web` -> pass
- `docker compose up -d postgres redis api worker web` -> pass
- `docker compose ps` -> core services healthy
- `http://localhost:5001/health/ready` -> pass
- `http://localhost:5001/api/v1/system/info` -> pass
- `http://localhost:5001/api/v1/system/persistence/schema` -> pass
- `http://localhost:5001/api/v1/system/persistence/ddl` -> pass
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q` -> pass
- `docker compose --profile baseline run --rm worker-js-baseline` -> pass
- `docker compose --profile baseline run --rm worker-parity` -> pass

Observed results:

- persistence schema version: `m2-v1`
- durable table count: `9`
- active backend: `python`
- reference runtime: `js-baseline-only`
- thin-slice strong fixture result remains `Proceed with Conditions` with weighted composite `3.61`

Known issues:

- durable models and DDL are executable, but no live database write path is added yet by design
- parity coverage still only executes against the strong starter portfolio; the promising and weak cases remain planned carry-forward work
- the JS baseline is still retained as a reference profile until the broader parity and CI gates are complete

## Risks

Technical risk:

- schema evolution rules are not yet backed by a migrations framework, so future schema changes still need strict milestone discipline
- payload hashes provide drift detection, but replay and regression coverage across all three starter portfolios is still incomplete
- API-to-worker contract sharing currently relies on Compose `PYTHONPATH` wiring; that is acceptable for the local platform but should be formalized further before larger backend expansion

Product risk:

- Milestone 2 proves persistence contracts and boundaries, not end-user data submission or historical review browsing workflows
- committee data is modeled durably, but no user-facing review history UI exists yet

Delivery risk:

- if parity expansion slips, the JS baseline could remain active longer than intended as a validation crutch
- if CI health and parity gates are delayed, schema changes could outpace executable regression coverage

## Validation

How to validate locally:

1. Review `.env.example` and optionally create `.env`.
2. Run `docker compose build api worker web`.
3. Run `docker compose up -d postgres redis api worker web`.
4. Run `docker compose ps`.
5. Check `http://localhost:5001/health/ready`.
6. Check `http://localhost:5001/api/v1/system/info`.
7. Check `http://localhost:5001/api/v1/system/persistence/schema`.
8. Check `http://localhost:5001/api/v1/system/persistence/ddl`.
9. Run `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`.
10. Run `docker compose --profile baseline run --rm worker-js-baseline`.
11. Run `docker compose --profile baseline run --rm worker-parity`.
12. Run `docker compose down --remove-orphans` when finished.

## Review Checklist

- Are all Milestone 2 durable entities modeled explicitly and typed?
- Does the Python worker remain the source of truth for backend runtime contracts?
- Is the persistence boundary introduced without broadening into Milestone 3 workflow scope?
- Do the API introspection endpoints expose the schema catalog and generated DDL successfully?
- Does the approved thin-slice behavior remain unchanged for the strong starter portfolio?
- Are parity expansion, JS archival timing, and CI regression planning explicitly tracked as carry-forward items?

## Recommendation

Proceed with fixes.

Fixes to carry into the next approved planning gate, not Milestone 2 expansion:

- expand parity coverage to the promising and weak starter portfolios
- define the exact milestone gate that moves the JS baseline from active reference to documented archive
- formalize CI for Compose health checks and parity regression before broader backend workflow work
- introduce a migrations strategy only when the next approved milestone requires live database writes

Milestone 2 is complete and should stop here pending review.


