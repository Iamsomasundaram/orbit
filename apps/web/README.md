# Web App

Milestone 9 turns the Next.js shell into a thin ORBIT workspace for multi-portfolio submission, comparison, ranking, and lineage inspection.

Current capability:

- landing page for JSON product-idea submission, ranking, and comparison selection
- side-by-side comparison page for multiple persisted portfolios
- portfolio detail page with latest review result visibility
- portfolio history page with lineage-aware review, debate, and artifact links
- web-side POST handlers that forward submission and review triggers to the FastAPI backend
- liveness and readiness endpoints for Compose health checks
- typed runtime config for internal and public API base URLs
- local Docker build and run support through pnpm workspaces

Entry points:

- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`
- `apps/web/app/api/health/live/route.ts`
- `apps/web/app/api/health/ready/route.ts`
- `apps/web/lib/orbit-api.ts`
- `apps/web/Dockerfile`
