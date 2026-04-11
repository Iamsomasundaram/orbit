# ORBIT Milestone 12

Milestone 12 introduces Committee Mode, a live-feel boardroom playback experience built on the persisted deliberation timeline from Milestone 11. The underlying review, conflict detection, bounded debate, optional re-synthesis, and artifact persistence flow stays unchanged. This milestone only changes how the persisted timeline is consumed and presented in the UI.

Delivered:

- new Committee Mode route
  - `/review-runs/{run_id}/committee`
- staged client-side playback of persisted deliberation entries
  - start
  - pause / resume
  - skip to next phase
  - jump to final verdict
  - reset
  - optional delay skipping
- five-phase boardroom visualization
  - opening statements
  - conflict identification
  - conflict discussion
  - moderator synthesis
  - final verdict
- conflict spotlight panel
  - disagreement topic
  - agent arguments
  - moderator resolution summary
- agent identity presentation
  - role display
  - avatar / initials
  - stance badges
- static timeline preserved
  - existing `/review-runs/{run_id}/deliberation` route remains available
- no new llm calls
  - Committee Mode reuses the persisted timeline only
  - no new reasoning stage
  - no new token cost

Primary files:

- `apps/web/app/review-runs/[runId]/committee/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`
- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/globals.css`
- `apps/web/lib/config.ts`
- `apps/api/orbit_api/health.py`

Validation snapshot from April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `42 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `42 passed`
- live deterministic validation run
  - run id: `review-strong-ai-saas-001-20260411T183358404802Z`
  - recommendation: `Proceed with Conditions`
  - weighted composite score: `3.61`
  - conflicts: `5`
  - persisted deliberation entries: `53`
  - phases returned: `5`
- Committee Mode page load
  - route: `/review-runs/{run_id}/committee`
  - result: `200`
  - rendered controls:
    - `Start Playback`
    - `Skip to Next Phase`
    - `Jump to Final Verdict`
    - `Conflict Spotlight`
    - `Final Verdict Reveal`
- static timeline page load
  - route: `/review-runs/{run_id}/deliberation`
  - result: `200`
  - rendered `Static Timeline` and linked back to `Committee Mode`

Validation note:

- the repo does not yet include browser automation for click-path replay checks, so Committee Mode interaction was validated through live render checks plus code-path inspection of the client playback controller

This milestone stops after the boardroom playback UI, validation, documentation, and Ralph review pack are complete.
