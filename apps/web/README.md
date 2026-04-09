# Web App

Milestone 1 establishes the Next.js platform shell for ORBIT.

Current capability:

- platform landing page aligned to the Python runtime direction
- liveness and readiness endpoints for Compose health checks
- typed runtime config for internal and public API base URLs
- local Docker build and run support through pnpm workspaces

Entry points:

- `apps/web/app/page.tsx`
- `apps/web/app/api/health/live/route.ts`
- `apps/web/app/api/health/ready/route.ts`
- `apps/web/Dockerfile`
