# ORBIT Milestone 8 Review Pack

## Scope Delivered

- added JSON product-idea submission on `POST /api/v1/portfolios`
- persisted idea submissions through the approved ingestion and canonicalization boundary
- added a user-facing review workflow that automatically executes:
  - review run
  - bounded debate when conflicts exist
  - bounded re-synthesis only when score change is required
- added minimal web pages for:
  - idea submission
  - portfolio detail
  - portfolio history and lineage inspection
- kept history and artifact inspection on the existing API surface
- confirmed history-query indexes already exist in the approved persistence model
- preserved archived-baseline parity protection and archive boundary discipline

## Architecture Decisions

- the automatic follow-on path lives in a dedicated workflow service
  - `ReviewRunService` stays the low-level review primitive
  - `DebateService` stays the low-level debate primitive
  - `ResynthesisService` stays the low-level re-synthesis primitive
  - `ReviewWorkflowService` coordinates them for the user-facing Milestone 8 trigger
- JSON idea submission is implemented as a thin adapter over the approved markdown ingestion path
  - a deterministic markdown source document is rendered from the idea fields
  - canonicalization then reuses the existing Milestone 3 ingestion boundary
- the web shell remains thin and server-rendered
  - form POST handlers forward to the API
  - detail and history pages read directly from the existing typed APIs
- the Compose `baseline` profile was not renamed
  - existing parity and validation commands already depend on it
  - in Milestone 8 it is documented explicitly as parity-only

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `32 passed`
  - includes:
    - idea submission coverage
    - workflow-service coverage
    - history and artifact inspection coverage
    - archived-baseline manifest and parity coverage
- `docker compose --profile baseline run --rm worker-parity`
  - result: `32 passed`

Live API validation completed on April 10, 2026:

- `POST /api/v1/portfolios`
  - created `procurepilot-m8-interactive`
  - persisted `section_count=11`
- `POST /api/v1/portfolios/procurepilot-m8-interactive/review-runs`
  - created `review-procurepilot-m8-interactive-20260410T125850832934Z`
  - returned:
    - `final_recommendation=Pilot Only`
    - `weighted_composite_score=3.48`
    - `agent_review_count=15`
    - `conflict_count=4`
- `GET /api/v1/portfolios/procurepilot-m8-interactive/history`
  - returned:
    - `review_run_count=1`
    - `debate_count=1`
    - `resynthesis_count=0`
    - lineage linking the portfolio to the created review run and debate
- `GET /api/v1/review-runs/review-procurepilot-m8-interactive-20260410T125850832934Z/artifacts`
  - returned:
    - `active_artifact_source=original`
    - `agent_review_count=15`
    - `conflict_count=4`
    - `score_change_required_count=0`

Live web validation completed on April 10, 2026:

- `GET http://localhost:5000`
  - rendered Milestone 8 submission form and recent portfolio cards
- `GET http://localhost:5000/portfolios/procurepilot-m8-interactive`
  - rendered detail page with latest result card and review action
- `GET http://localhost:5000/portfolios/procurepilot-m8-interactive/history?runId=review-procurepilot-m8-interactive-20260410T125850832934Z`
  - rendered highlighted lineage view
  - showed:
    - `Pilot Only`
    - `3.48`
    - `15 agents`
    - `4 conflicts`
    - `original` artifact source
- local caveat:
  - the detail page source has been updated to render `portfolio.submitted_at` as the submission date
  - the running Next.js development container may still require a clean rebuild to reflect that final date-only rendering consistently in the browser

Compatibility validation completed on April 10, 2026:

- the archived baseline parity suite remained green at `32 passed`
- no committed baseline artifacts were regenerated
- the approved baseline fixture behavior remains protected through the existing artifact set under `tests/fixtures/baselines/`

## Risks

Technical risk:

- new idea submissions derive `portfolio_id` from the portfolio name, so duplicate-name handling still depends on deterministic ID conflict behavior rather than a broader identity strategy
- the ingestion path still parses markdown twice when persisting a new submission
- CI automation for parity and workflow regression is still pending
- local web validation can still be affected by stale Next.js development cache state until the web service is cleanly rebuilt

Product risk:

- the Milestone 8 UI is intentionally thin and functional, not a full operator dashboard
- new submitted ideas can naturally produce different committee outcomes from the archived baseline examples because they are different inputs

Delivery risk:

- migration tooling exists, but no new Milestone 8 migration was needed because the required history indexes were already present
- source-document artifact storage remains local-first and temporary
- audit-event separation remains shared-table and may still need refinement later

## Validation

Primary local workflow:

- `docker compose run --rm migrate`
- `docker compose up -d api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference Milestone 8 API checks:

- `POST http://localhost:5001/api/v1/portfolios`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `GET http://localhost:5001/api/v1/portfolios/{portfolio_id}/history`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/artifacts`

Reference Milestone 8 UI checks:

- `http://localhost:5000`
- `http://localhost:5000/portfolios/{portfolio_id}`
- `http://localhost:5000/portfolios/{portfolio_id}/history`

## Review Checklist

- JSON idea submission persists portfolio, source document, canonical portfolio, and ingestion audit events
- review trigger reuses the approved Python review path
- debate runs automatically when conflicts exist
- re-synthesis runs only when debate resolution requires score change
- portfolio detail page shows latest committee result values from artifact inspection
- history page exposes review lineage across review run, debate, and re-synthesis
- archived-baseline parity remains green without regenerating baseline artifacts
- Docker Compose remains the primary development workflow
- JS archive boundary remains `archive/js-baseline/`

## Carry-Forward

- improve duplicate submission handling with broader DB-backed conflict enforcement
- reduce double parsing in portfolio ingestion if the optimization stays safe
- keep Alembic migration authoring discipline active for later schema changes
- add CI automation for parity and workflow regression
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event separation later if a safe boundary improvement becomes necessary

## Recommendation

Proceed with fixes.

Milestone 8 delivers the first practical end-to-end ORBIT workflow without redesigning the approved committee engine. The remaining work is operational hardening and broader UX depth, not a change in runtime direction or committee semantics.
