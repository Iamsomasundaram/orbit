# ORBIT Milestone 8

Milestone 8 enables the first practical ORBIT workflow: submit a new product idea, persist and canonicalize it, run the approved committee pipeline, and inspect the resulting lineage through the existing history and artifact APIs.

Delivered:

- JSON idea submission on `POST /api/v1/portfolios`
  - accepts `portfolio_name`, `portfolio_type`, `owner`, `description`, optional `tags`, and optional `metadata`
  - persists the portfolio row, source document metadata, canonical portfolio payload, and ingestion audit events
- user-facing review execution on `POST /api/v1/portfolios/{portfolio_id}/review-runs`
  - reuses the approved Python review path against persisted canonical portfolio data
  - automatically starts bounded debate when conflicts exist
  - automatically starts re-synthesis only when persisted debate resolutions require score recheck
- minimal Milestone 8 web shell pages:
  - `/` for idea submission and recent portfolio access
  - `/portfolios/{portfolio_id}` for portfolio detail and latest committee result
  - `/portfolios/{portfolio_id}/history` for lineage-oriented history inspection
- web-side POST handlers that forward form submissions to the FastAPI API while keeping the UI Docker-first
- confirmation that history-heavy indexes required for Milestone 8 are already present in the approved persistence model
- preserved archived-baseline parity protection through the committed manifest-backed artifact checks

Boundaries kept intact:

- specialist reviewer logic is unchanged
- conflict detection v1 is unchanged
- bounded debate logic is unchanged
- bounded re-synthesis logic is unchanged
- committee scoring behavior is unchanged
- no provider-backed reasoning, async job system, distributed worker model, or full dashboard expansion was introduced
- the JS archive boundary remains `archive/js-baseline/`
- the Compose profile name remains `baseline` in this milestone and is documented as parity-only

Primary files:

- `apps/api/orbit_api/portfolios.py`
- `apps/api/orbit_api/review_workflow.py`
- `apps/api/orbit_api/main.py`
- `apps/api/orbit_api/history.py`
- `apps/web/app/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/page.tsx`
- `apps/web/app/portfolios/[portfolioId]/history/page.tsx`
- `apps/web/app/api/portfolios/route.ts`
- `apps/web/app/api/portfolios/[portfolioId]/review-runs/route.ts`
- `apps/web/lib/orbit-api.ts`

Validation snapshot from April 10, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `32 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `32 passed`
- live Milestone 8 workflow validation:
  - created portfolio `procurepilot-m8-interactive`
  - created review run `review-procurepilot-m8-interactive-20260410T125850832934Z`
  - auto-created debate `debate-review-procurepilot-m8-interactive-20260410T125850832934Z`
  - no re-synthesis was created because `score_change_required_count=0`
  - latest active result returned:
    - `final_recommendation=Pilot Only`
    - `weighted_composite_score=3.48`
    - `agent_review_count=15`
    - `conflict_count=4`
    - `active_artifact_source=original`
- live web shell validation:
  - `/` rendered the submission form and recent portfolio cards
  - `/portfolios/procurepilot-m8-interactive` rendered the detail page and latest result card
  - `/portfolios/procurepilot-m8-interactive/history?runId=review-procurepilot-m8-interactive-20260410T125850832934Z` rendered the highlighted lineage view

Notes:

- the approved baseline example remains protected through parity validation against committed artifacts under `tests/fixtures/baselines/`
- the live Milestone 8 sample portfolio is a new input, so its committee output differs from the baseline fixture while remaining deterministic and compatible with the approved logic
- the portfolio detail page source is updated to render `submitted_at` from the portfolio record, but the local Next.js development server may require a clean rebuild to reflect that final date-only rendering consistently in the browser

This milestone stops after interactive submission, synchronous execution wiring, validation, and the Ralph review pack are complete.
