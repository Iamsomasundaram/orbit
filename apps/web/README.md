# Web App

Milestone 12 keeps the existing workspace shell and adds Committee Mode, a live-feel boardroom playback page backed by persisted timeline records.

Current capability:

- landing page for JSON product-idea submission, ranking, and comparison selection
- side-by-side comparison page for multiple persisted portfolios
- portfolio detail page with latest review result visibility
- portfolio history page with lineage-aware review, debate, and artifact links
- review-run Committee Mode page with staged playback, phase rail, conflict spotlight, and final verdict reveal
- review-run static deliberation page with ordered committee statements and phase summaries
- runtime copy and health metadata aligned to the Milestone 12 boardroom playback experience
- web-side POST handlers that forward submission and review triggers to the FastAPI backend
- liveness and readiness endpoints for Compose health checks
- typed runtime config for internal and public API base URLs
- local Docker build and run support through pnpm workspaces

Entry points:

- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`
- `apps/web/app/api/health/live/route.ts`
- `apps/web/app/api/health/ready/route.ts`
- `apps/web/lib/orbit-api.ts`
- `apps/web/Dockerfile`
