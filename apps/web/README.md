# Web App

Milestone 14 keeps the existing workspace shell and extends it for evidence-based committee reasoning with explicit claim chains, confidence display, and conflict evidence visibility while preserving adaptive routing telemetry and playback controls.

Current capability:

- landing page for JSON product-idea submission, ranking, and comparison selection
- client-side submission flow with inline loading and error handling
- side-by-side comparison page for multiple persisted portfolios
- portfolio detail page with latest review result visibility
- portfolio history page with lineage-aware review, debate, and artifact links
- review-run detail page with active artifact state, adaptive routing telemetry, fallback banner, conflict metadata, and review-scope audit events
- review-run Committee Mode page with staged playback, phase rail, conflict spotlight, final verdict reveal, `0.5x` to `instant` playback controls, passive-observer visibility, and telemetry-aware agent identity cards
- review-run static deliberation page with ordered committee statements and phase summaries
- runtime copy and health metadata aligned to the Milestone 14 evidence-based reasoning milestone
- web-side POST handlers that forward submission and review triggers to the FastAPI backend with JSON-aware responses for reliable client interaction
- liveness and readiness endpoints for Compose health checks
- typed runtime config for internal and public API base URLs
- Playwright browser automation for creation, review, comparison, and Committee Mode playback flows
- local Docker build and run support through pnpm workspaces

Entry points:

- `apps/web/app/page.tsx`
- `apps/web/app/home-submission-card.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolio-review-action.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/review-runs/[runId]/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`
- `apps/web/app/api/health/live/route.ts`
- `apps/web/app/api/health/ready/route.ts`
- `apps/web/playwright.config.ts`
- `apps/web/tests-e2e/milestone-12-2.spec.ts`
- `apps/web/lib/orbit-api.ts`
- `apps/web/Dockerfile`
- `apps/web/Dockerfile.e2e`
