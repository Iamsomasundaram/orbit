# ORBIT Milestone 9 Review Pack

## Scope Delivered

- added multi-portfolio workspace APIs for:
  - summary
  - comparison
  - deterministic ranking
- expanded the web shell into a thin multi-portfolio workspace:
  - sortable home page with ranking snapshot
  - comparison selection on the home page
  - side-by-side comparison page
- preserved existing detail, history, and artifact inspection as the lineage drill-down path
- improved JSON idea identity handling with a bounded fingerprint-based `portfolio_id`
- reduced double parsing on the JSON idea-submission path without changing canonical output semantics
- added Compose-based GitHub Actions regression coverage for:
  - migrations
  - worker tests
  - archived-baseline parity
- kept the archived JS baseline artifact boundary intact and runtime-inactive

## Architecture Decisions

- multi-portfolio comparison is implemented as a read-only workspace service over persisted state
  - `PortfolioWorkspaceService` composes existing repository and history services
  - ranking and comparison derive only from persisted active artifacts
- comparison does not duplicate artifact-selection logic
  - active recommendation, score, and lineage continue to come from the approved history and artifact surfaces
- idea identity was hardened without introducing a new persistence concept
  - JSON idea submissions derive `portfolio_id` from normalized content fingerprinting
  - this keeps the persistence boundary unchanged while avoiding portfolio-name-only collisions
- double parsing was reduced only where it was low risk
  - JSON idea submission now parses once before persistence
  - the original markdown document-submission path remains unchanged
- no new schema migration was introduced
  - the current query shape is already covered by the approved indexes on `review_runs`, `debate_sessions`, `resynthesis_sessions`, and `audit_events`
- the Compose `baseline` profile remains in place
  - it is now explicitly parity-only and still points to archived artifact validation, not runtime behavior

## Quality Status

Automated validation completed on April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `37 passed`
  - includes:
    - portfolio ingestion coverage
    - review workflow coverage
    - debate and re-synthesis coverage
    - history and artifact inspection coverage
    - workspace ranking and comparison coverage
    - archived-baseline artifact parity coverage
- `docker compose --profile baseline run --rm worker-parity`
  - result: `37 passed`

Live API validation completed on April 11, 2026:

- `GET /api/v1/system/info`
  - returned:
    - `milestone=9`
    - `runtime_direction=multi-portfolio-comparison-and-prioritization`
- `POST /api/v1/portfolios`
  - created `helixflow-m9-b72db1f1`
  - created `helixflow-m9-b6dcf8bf`
  - confirmed bounded identity for two ideas sharing the same display name
- `POST /api/v1/portfolios/helixflow-m9-b72db1f1/review-runs`
  - created `review-helixflow-m9-b72db1f1-20260411T155923052158Z`
  - returned:
    - `final_recommendation=Pilot Only`
    - `weighted_composite_score=3.35`
    - `agent_review_count=15`
    - `conflict_count=4`
- `POST /api/v1/portfolios/helixflow-m9-b6dcf8bf/review-runs`
  - created `review-helixflow-m9-b6dcf8bf-20260411T155923209343Z`
  - returned:
    - `final_recommendation=Pilot Only`
    - `weighted_composite_score=3.39`
    - `agent_review_count=15`
    - `conflict_count=4`
- `GET /api/v1/portfolios/summary?sort_by=weighted_composite_score&direction=desc`
  - returned deterministic ranking with:
    - `strong-ai-saas-001` first at `3.61`
    - `procurepilot-m8-interactive` second at `3.48`
    - `helixflow-m9-b6dcf8bf` third at `3.39`
    - `helixflow-m9-b72db1f1` fourth at `3.35`
- `GET /api/v1/portfolios/compare?portfolio_id=helixflow-m9-b72db1f1&portfolio_id=helixflow-m9-b6dcf8bf&portfolio_id=strong-ai-saas-001`
  - preserved requested order
  - returned latest lineage for all three items
  - exposed both `Pilot Only` and `Proceed with Conditions` active outcomes side by side
- `GET /api/v1/portfolios/helixflow-m9-b72db1f1/history`
  - returned:
    - `review_run_count=1`
    - `debate_count=1`
    - `resynthesis_count=0`
- `GET /api/v1/review-runs/review-helixflow-m9-b72db1f1-20260411T155923052158Z/artifacts`
  - returned:
    - `active_artifact_source=original`
    - `score_change_required_count=0`
    - debate lineage present

Live web validation completed on April 11, 2026:

- `GET http://localhost:5000/api/health/live`
  - returned `milestone=9`
- `GET http://localhost:5000`
  - rendered the Milestone 9 workspace
  - showed:
    - priority snapshot
    - portfolio workspace sorting controls
    - comparison selection
- `GET http://localhost:5000/compare?portfolioId=helixflow-m9-b72db1f1&portfolioId=helixflow-m9-b6dcf8bf&portfolioId=strong-ai-saas-001`
  - rendered the side-by-side comparison page
  - showed:
    - both `HelixFlow M9` portfolios
    - `strong-ai-saas-001`
    - `Pilot Only`
    - `Proceed with Conditions`

Compatibility validation completed on April 11, 2026:

- archived-baseline parity remained green at `37 passed`
- no committed baseline artifacts were regenerated
- the JS archive boundary remained `archive/js-baseline/`

## Risks

Technical risk:

- broader portfolio identity is improved for JSON idea submissions, but the older markdown document-submission path still follows the original ingestion identity behavior
- double parsing was reduced only for JSON idea submissions; the markdown document-submission path still parses twice
- workspace summary and comparison are correct for the current persisted query volume, but larger datasets may still need composite index tuning later
- CI now covers Compose regression and parity, but it does not yet include browser-level UI checks

Product risk:

- the Milestone 9 UI is intentionally thin and operational, not a full investment-decision dashboard
- ranking is deterministic and useful, but it remains a projection of the approved committee outputs rather than a new decision model

Delivery risk:

- no new Alembic migration was required in Milestone 9, so future schema-heavy workspace features still need explicit migration authorship when they arrive
- source-document storage remains local-first and temporary
- audit-event query boundaries remain shared-table and may still need later refinement

## Validation

Primary local workflow:

- `docker compose run --rm migrate`
- `docker compose up -d --build postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference Milestone 9 API checks:

- `GET http://localhost:5001/api/v1/portfolios/summary`
- `GET http://localhost:5001/api/v1/portfolios/compare?portfolio_id=...`
- `GET http://localhost:5001/api/v1/portfolios/ranking`
- `POST http://localhost:5001/api/v1/portfolios`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `GET http://localhost:5001/api/v1/portfolios/{portfolio_id}/history`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/artifacts`

Reference Milestone 9 UI checks:

- `http://localhost:5000`
- `http://localhost:5000/compare?portfolioId=...`
- `http://localhost:5000/portfolios/{portfolio_id}`
- `http://localhost:5000/portfolios/{portfolio_id}/history`

## Review Checklist

- portfolio submission still persists canonical portfolio state without changing approved review semantics
- multi-portfolio summary returns the latest active committee state for persisted portfolios
- comparison preserves requested portfolio order and links back to lineage
- ranking remains deterministic and derived only from persisted active state
- home page supports sorting and comparison selection
- comparison page renders side-by-side outcomes without duplicating artifact logic
- archived-baseline parity remains green without regenerating artifacts
- Compose remains the primary development and validation workflow
- the JS archive boundary remains `archive/js-baseline/`

## Carry-Forward

- extend the safer bounded identity strategy to the markdown document-submission path if that path remains user-facing
- reduce double parsing in the original markdown document-submission path if it can be done without risking canonical drift
- keep Alembic migration authoring discipline active for future schema changes
- consider composite index tuning if workspace/history query volume grows materially
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event query boundaries later if a small safe improvement becomes worthwhile

## Recommendation

Proceed with fixes.

Milestone 9 delivers the first practical multi-portfolio ORBIT workspace without changing the approved committee engine. The remaining work is hardening, scale tuning, and UI depth rather than a change in committee semantics or runtime direction.
