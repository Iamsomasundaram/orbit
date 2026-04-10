# ORBIT

ORBIT stands for Organizational Review for Business, Intelligence, and Technology.

ORBIT is an AI-powered multi-agent product and investment review committee for startup ideas, AI products, and enterprise innovation proposals. It ingests portfolio documents, normalizes them into a canonical structure, runs bounded specialist reviews, detects conflicts, and synthesizes an evidence-backed committee report.

Current status:

- Milestone 0 artifacts are complete in `docs/milestone-0/`.
- Milestone 0.5 behavioral proof remains available as the JS reference baseline.
- Milestone 0.5a established the Python thin-slice runtime as the primary backend execution path.
- Milestone 1 added the local platform foundation for `web`, `api`, `worker`, `postgres`, and `redis` through Docker Compose.
- Milestone 2 added durable persistence models, executable Postgres schema generation, and persistence boundary documentation while keeping the approved review behavior unchanged.
- Milestone 2.1 hardens the platform with full-fixture parity coverage, frozen JS baseline lifecycle controls, and worker host debugging on port `5004`.
- Milestone 3 adds bounded portfolio submission APIs, canonical portfolio materialization, and durable ingestion storage without broadening into review orchestration.
- Milestone 4 adds bounded review-run orchestration APIs that execute the approved Python thin-slice review path from persisted canonical portfolios and store review artifacts durably.
- Milestone 5 adds bounded moderator-controlled debate APIs that resolve persisted conflicts, store debate artifacts and resolution outcomes, and preserve approved committee scoring unless a resolution explicitly flags recheck.
- Milestone 6 adds bounded score recheck and committee re-synthesis APIs that consume persisted debate resolutions, preserve original committee artifacts, and materialize re-synthesized outputs only when a resolution explicitly requires it.
- Milestone 6.1 hardens persistence with Alembic-managed schema discipline, DB-backed duplicate enforcement on bounded creation paths, migration bootstrap for legacy local dev databases, and regression coverage for original versus re-synthesized artifact selection.

Primary references:

- `docs/milestone-0/README.md`
- `docs/milestone-0.5/review-pack.md`
- `docs/milestone-0.5a/review-pack.md`
- `docs/milestone-1/README.md`
- `docs/milestone-2/README.md`
- `docs/milestone-2.1/README.md`
- `docs/milestone-3/README.md`
- `docs/milestone-4/README.md`
- `docs/milestone-5/README.md`
- `docs/milestone-6/README.md`
- `docs/milestone-6.1/README.md`

Platform commands:

- `docker compose up -d --build postgres redis api worker web`
- `docker compose run --rm migrate`
- `docker compose ps`
- `docker compose down --remove-orphans`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `POST http://localhost:5001/api/v1/portfolios`
- `GET http://localhost:5001/api/v1/portfolios`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}`
- `POST http://localhost:5001/api/v1/review-runs/{run_id}/debates`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/debates`
- `GET http://localhost:5001/api/v1/debates/{debate_id}`
- `POST http://localhost:5001/api/v1/debates/{debate_id}/re-synthesis`
- `GET http://localhost:5001/api/v1/debates/{debate_id}/re-synthesis`
- `GET http://localhost:5001/api/v1/re-syntheses/{resynthesis_id}`
- `docker compose --profile baseline run --rm worker-js-baseline`

Repository layout:

- `apps/api` -> FastAPI control plane, health surface, and portfolio submission APIs
- `apps/web` -> Next.js platform shell and local workspace landing page
- `apps/worker` -> primary Python backend execution runtime, parity tests, and persistence contracts
- `packages/orbit-*` -> frozen JS baseline modules retained until archival
- `docs/` -> milestone packs and review gates
- `tests/fixtures/` -> golden portfolios, source documents, parity matrix, and committed baseline artifacts

Approved defaults:

- `pnpm` workspaces for the monorepo manager
- `poetry` for Python packaging
- provider abstraction from day 1
- OpenAI adapter first, with Anthropic and local placeholders
- Docker Compose as the local runtime target
