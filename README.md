# ORBIT

ORBIT stands for Organizational Review for Business, Intelligence, and Technology.

ORBIT is an AI-powered multi-agent product and investment review committee for startup ideas, AI products, and enterprise innovation proposals. It ingests portfolio documents, normalizes them into a canonical structure, runs bounded specialist reviews, detects conflicts, and synthesizes an evidence-backed committee report.

Current status:

- Milestone 0 artifacts are complete in `docs/milestone-0/`.
- Milestone 0.5 behavioral proof remains available as the JS reference baseline.
- Milestone 0.5a established the Python thin-slice runtime as the primary backend execution path.
- Milestone 1 added the local platform foundation for `web`, `api`, `worker`, `postgres`, and `redis` through Docker Compose.
- Milestone 2 adds durable persistence models, executable Postgres schema generation, and persistence boundary documentation while keeping the approved review behavior unchanged.
- Milestone 3 and later scope remain gated pending Milestone 2 review.

Primary references:

- `docs/milestone-0/README.md`
- `docs/milestone-0.5/review-pack.md`
- `docs/milestone-0.5a/review-pack.md`
- `docs/milestone-1/README.md`
- `docs/milestone-2/README.md`

Platform commands:

- `docker compose up -d --build postgres redis api worker web`
- `docker compose ps`
- `docker compose down --remove-orphans`
- `docker compose --profile baseline run --rm worker-js-baseline`
- `docker compose --profile baseline run --rm worker-parity`

Repository layout:

- `apps/api` -> FastAPI control plane and platform health surface
- `apps/web` -> Next.js platform shell and local workspace landing page
- `apps/worker` -> primary Python backend execution runtime and persistence contracts
- `packages/orbit-*` -> reference JS baseline modules retained until archival
- `docs/` -> milestone packs and review gates
- `tests/fixtures/` -> golden portfolios and committed baseline artifacts

Approved defaults:

- `pnpm` workspaces for the monorepo manager
- `poetry` for Python packaging
- provider abstraction from day 1
- OpenAI adapter first, with Anthropic and local placeholders
- Docker Compose as the local runtime target
