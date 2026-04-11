# ORBIT Milestone 9

Milestone 9 expands ORBIT from a single-portfolio review flow into a multi-portfolio decision workspace. Users can now submit ideas, run the approved committee workflow, rank multiple portfolios from persisted outcomes, compare them side by side, and trace each result back to the approved history and artifact APIs.

Delivered:

- multi-portfolio summary API on `GET /api/v1/portfolios/summary`
  - lists persisted portfolios with latest active recommendation, weighted score, artifact source, lifecycle counts, and latest lineage
- side-by-side comparison API on `GET /api/v1/portfolios/compare`
  - preserves requested `portfolio_id` order
  - exposes the latest active recommendation, score, conflict footprint, score-recheck count, and lineage reference for each selected portfolio
- deterministic ranking API on `GET /api/v1/portfolios/ranking`
  - supports persisted-state ranking by weighted score, recommendation rank, conflict count, and score-change-required count
- Milestone 9 web shell updates:
  - `/` now serves as the portfolio workspace with submission, sorting, ranking, and comparison selection
  - `/compare` renders a thin side-by-side comparison view
  - existing detail and history pages remain the canonical lineage drill-down path
- safer bounded identity for JSON idea submission
  - identical idea names can now coexist when the submitted owner/content differs
  - `portfolio_id` is derived from a normalized fingerprint rather than portfolio name alone
- reduced double parsing for JSON idea submission
  - the idea-submission path now parses generated markdown once before persistence
  - the original markdown document-submission path remains unchanged
- Compose-first regression automation in `.github/workflows/compose-regression.yml`
  - runs migrations, worker tests, and archived-baseline parity validation
- confirmation that the existing persistence indexes already cover the current history and workspace query paths
  - no Milestone 9 schema migration was required

Boundaries kept intact:

- reviewer logic is unchanged
- conflict detection v1 is unchanged
- bounded debate logic is unchanged
- bounded re-synthesis logic is unchanged
- committee scoring semantics are unchanged
- no provider-backed reasoning, async job system, distributed execution model, or major dashboard redesign was introduced
- the JS archive boundary remains `archive/js-baseline/`
- the Compose `baseline` profile remains parity-only in this milestone and was not reintroduced as runtime behavior

Primary files:

- `apps/api/orbit_api/workspace.py`
- `apps/api/orbit_api/main.py`
- `apps/api/orbit_api/portfolios.py`
- `apps/web/app/page.tsx`
- `apps/web/app/compare/page.tsx`
- `apps/web/lib/orbit-api.ts`
- `apps/worker/tests/test_workspace_service.py`
- `apps/worker/tests/test_portfolio_ingestion_service.py`
- `.github/workflows/compose-regression.yml`

Validation snapshot from April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `37 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `37 passed`
- live Milestone 9 API validation:
  - `GET /api/v1/portfolios/summary?sort_by=weighted_composite_score&direction=desc`
    - returned deterministic workspace ordering with `strong-ai-saas-001` at `3.61`
  - `POST /api/v1/portfolios`
    - created `helixflow-m9-b72db1f1`
    - created `helixflow-m9-b6dcf8bf`
    - confirmed bounded identity for two ideas sharing the same display name
  - `POST /api/v1/portfolios/{portfolio_id}/review-runs`
    - created `review-helixflow-m9-b72db1f1-20260411T155923052158Z`
    - created `review-helixflow-m9-b6dcf8bf-20260411T155923209343Z`
    - returned deterministic results of `15` agents, `4` conflicts, `Pilot Only`, and scores `3.35` / `3.39`
  - `GET /api/v1/portfolios/compare`
    - returned the requested portfolio order and latest lineage for both new ideas and `strong-ai-saas-001`
  - `GET /api/v1/portfolios/ranking`
    - returned deterministic ranking with `strong-ai-saas-001` ranked first by weighted score
  - `GET /api/v1/review-runs/{run_id}/artifacts`
    - returned `active_artifact_source=original`, `score_change_required_count=0`, and the expected debate lineage for the new idea
- live web validation:
  - `/` rendered the Milestone 9 workspace with ranking cards, sort controls, and comparison selection
  - `/compare?portfolioId=helixflow-m9-b72db1f1&portfolioId=helixflow-m9-b6dcf8bf&portfolioId=strong-ai-saas-001`
    - rendered the side-by-side comparison view with both `Pilot Only` and `Proceed with Conditions` outcomes

Notes:

- no committed archived-baseline artifacts were regenerated
- parity remains artifact-based against the committed set under `tests/fixtures/baselines/`
- the new GitHub Actions workflow protects the parity path and worker regression path without turning the archived JS source back into runtime code

This milestone stops after multi-portfolio comparison, prioritization, validation, and the Ralph review pack are complete.
