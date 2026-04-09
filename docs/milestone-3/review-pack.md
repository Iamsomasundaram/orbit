# ORBIT Milestone 3 Review Pack

## Scope Delivered

Completed in this milestone:

- implemented bounded portfolio submission APIs for markdown documents
- canonicalized submitted documents into the approved ORBIT portfolio structure using the existing Python ingestion logic
- persisted portfolio envelopes, source document metadata, canonical portfolios, and ingestion audit events in Postgres
- added a Postgres-backed repository implementation under the Milestone 2 persistence boundary
- kept the approved thin-slice review behavior intact and validated parity regression after the ingestion changes

## Architecture Decisions

- the Python worker contracts remain the source of truth for canonical portfolio shape and persistence record models
- Milestone 3 extends the existing persistence boundary into a live ingestion write path instead of introducing a separate ingestion-only schema
- submitted markdown is stored under `PORTFOLIO_STORAGE_DIR` so `source_documents.path` remains durable and locally debuggable in Docker-first development
- the API accepts one markdown document per submission in this milestone; multi-document intake and richer parsing remain out of scope
- review execution is not triggered from the submission APIs, which keeps Milestone 3 bounded away from orchestration and debate scope

## Quality Status

Validation executed successfully:

- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q` -> pass (`9 passed`)
- `docker compose --profile baseline run --rm worker-parity` -> pass (`9 passed`)
- `docker compose ps` -> `api`, `web`, `worker`, `postgres`, and `redis` healthy
- `http://localhost:5001/api/v1/system/info` -> pass
- `POST /api/v1/portfolios` with `procurepilot-thin-slice.md` -> pass
- `GET /api/v1/portfolios` -> pass
- `GET /api/v1/portfolios/strong-ai-saas-001` -> pass
- duplicate `POST /api/v1/portfolios` for the same canonical `portfolio_id` -> `409 Conflict` as designed

Observed ingestion results:

- submitted portfolio id: `strong-ai-saas-001`
- stored canonical section count: `11`
- stored source document count: `1`
- stored ingestion audit event count: `2`
- source document persisted at `/workspace/.orbit-data/portfolio-submissions/strong-ai-saas-001/procurepilot-thin-slice.md`

Thin-slice stability remains unchanged:

- all 15 agents still execute in the approved review path
- structured conflicts still materialize from structured state
- the strong fixture still lands at `Proceed with Conditions`
- weighted composite remains `3.61`

Known issues:

- schema bootstrap still uses SQLAlchemy `create_all`; Alembic planning remains a carry-forward item
- submission APIs currently accept markdown documents only
- ingestion stores source files in local workspace-backed storage, which is correct for Docker-first development but not a production artifact strategy

## Risks

Technical risk:

- indexing is still only at the Milestone 2 foundation level; portfolio retrieval patterns may need more targeted indexes once submission volume grows
- source file storage is intentionally local-first for Milestone 3 and will need a more formal artifact strategy later
- structured logging for worker review runs is still deferred, so ingestion is durable but later review execution observability remains incomplete

Product risk:

- Milestone 3 proves submission and canonical storage, not asynchronous review initiation or portfolio history UX beyond the current API surface
- single-document markdown submission is sufficient for this gate but not full enterprise intake breadth

Delivery risk:

- if migration tooling is delayed too long, schema evolution pressure will increase around later workflow milestones
- if parity regression is not automated in CI soon, later ingestion or persistence work could accidentally disturb the approved review baseline

## Validation

How to validate locally:

1. Review `.env.example` and optionally create `.env`.
2. Run `docker compose build api`.
3. Run `docker compose up -d postgres redis api worker web`.
4. Run `docker compose ps`.
5. Check `http://localhost:5001/api/v1/system/info`.
6. Submit a portfolio document to `POST http://localhost:5001/api/v1/portfolios`.
7. Check `GET http://localhost:5001/api/v1/portfolios`.
8. Check `GET http://localhost:5001/api/v1/portfolios/{portfolio_id}`.
9. Run `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`.
10. Run `docker compose --profile baseline run --rm worker-parity`.
11. Run `docker compose down --remove-orphans` when finished.

## Review Checklist

- Does the API accept a bounded markdown portfolio document and canonicalize it successfully?
- Are canonical portfolios persisted through the approved Milestone 2 persistence boundary?
- Are source document metadata and ingestion audit events stored durably?
- Does duplicate submission return a controlled conflict response?
- Is Docker Compose still the primary validated local workflow?
- Does the approved thin-slice review behavior remain unchanged after Milestone 3?
- Are later-scope items explicitly deferred rather than partially implemented?

## Recommendation

Proceed with fixes.

Carry-forward items, not Milestone 3 expansion:

- add structured logging for worker review runs
- plan and introduce Alembic when live schema evolution becomes necessary
- refine indexing strategy for persistence tables based on actual query patterns
- automate parity and Compose health regression in CI

Milestone 3 is complete and stops at the portfolio ingestion API gate.
