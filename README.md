# ORBIT

ORBIT stands for Organizational Review for Business, Intelligence, and Technology.

ORBIT is an AI-powered multi-agent product and investment review committee for startup ideas, AI products, and enterprise innovation proposals. It is designed to ingest portfolio documents, normalize them into a canonical structure, run bounded specialist reviews, detect conflicts, moderate debate, and synthesize an evidence-backed committee report.

Current status:

- Milestone 0 artifacts are complete in `docs/milestone-0/`.
- The repository includes only Milestone 0 scaffolding and starter fixtures.
- Milestone 0.5 and later implementation work is intentionally gated pending review.

Primary references:

- `docs/milestone-0/README.md`
- `docs/milestone-0/review-pack.md`
- `tests/fixtures/portfolios/`

Planned repository layout:

- `apps/api` -> FastAPI control plane and public API
- `apps/web` -> Next.js review workspace and report UI
- `apps/worker` -> orchestration and background execution
- `packages/orbit-core` -> shared domain models and provider abstraction
- `packages/orbit-agents` -> agent registry, contracts, prompt definitions
- `packages/orbit-ingestion` -> ingestion and canonicalization logic
- `packages/orbit-scoring` -> score normalization and recommendation logic
- `packages/orbit-debate` -> conflict detection and debate workflow
- `packages/orbit-reporting` -> committee synthesis and report generation
- `packages/orbit-evals` -> golden portfolio datasets and regression harness

Approved defaults captured in Milestone 0:

- `pnpm` workspaces for the monorepo manager
- `poetry` for Python packaging
- provider abstraction from day 1
- OpenAI adapter first, with Anthropic and local placeholders
- Docker Compose as the local runtime target
