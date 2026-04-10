# ORBIT Milestone 7 Review Pack

## Scope Delivered

- added portfolio history retrieval for persisted review lineage
- added artifact inspection retrieval for review runs, debates, and re-syntheses
- exposed original versus active artifact state through explicit ownership fields
- exposed lineage across:
  - portfolio
  - review run
  - debate
  - re-synthesis
- added regression coverage for lineage retrieval and artifact selection
- preserved approved committee behavior, scoring, and bounded orchestration

## Architecture Decisions

- history and artifact inspection are read-only services layered on top of the existing persistence boundary
  - no review, debate, or re-synthesis execution logic was redesigned
- artifact selection remains derived from persisted state
  - original review artifacts stay authoritative for historical inspection
  - resynthesized artifacts only become active when the persisted re-synthesis session says so
- audit visibility is intentionally scoped by lifecycle
  - portfolio history returns the full portfolio lifecycle event stream
  - review artifact inspection returns review-only events
  - debate and re-synthesis inspection return their own scoped audit events
- Docker Compose remains the primary validation workflow
  - live API inspection is verified against the same local platform stack used for earlier milestones

## Quality Status

Automated validation completed on April 10, 2026:

- `docker compose up -d api worker web`
  - result: success
- `docker compose ps`
  - result: `api`, `worker`, `web`, `postgres`, and `redis` healthy
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `28 passed`
  - includes:
    - `test_history_service.py`
    - parity assertions still covered through the worker suite
- `docker compose --profile baseline run --rm worker-parity`
  - result: `28 passed`

Live API validation completed on April 10, 2026:

- `GET /api/v1/portfolios/strong-ai-saas-001/history`
  - returned `review_run_count=4` before fresh validation activity
  - returned lineage-aware history with persisted debates and re-syntheses
- `POST /api/v1/portfolios/strong-ai-saas-001/review-runs`
  - created run `review-strong-ai-saas-001-20260410T112228673688Z`
- `POST /api/v1/review-runs/review-strong-ai-saas-001-20260410T112228673688Z/debates`
  - created debate `debate-review-strong-ai-saas-001-20260410T112228673688Z`
- `POST /api/v1/debates/debate-review-strong-ai-saas-001-20260410T112228673688Z/re-synthesis`
  - created re-synthesis `resynthesis-debate-review-strong-ai-saas-001-20260410T112228673688Z`
- `GET /api/v1/review-runs/review-strong-ai-saas-001-20260410T112228673688Z/artifacts`
  - returned `active_artifact_source=original`
  - returned review audit actions limited to:
    - `review_run.completed`
    - `committee_report.materialized`
- `GET /api/v1/debates/debate-review-strong-ai-saas-001-20260410T112228673688Z/artifacts`
  - returned `conflict_resolution_count=5`
  - returned the linked re-synthesis id
- `GET /api/v1/re-syntheses/resynthesis-debate-review-strong-ai-saas-001-20260410T112228673688Z/artifacts`
  - returned `active_artifact_source=original`
  - returned `final_recommendation=Proceed with Conditions`
  - returned `weighted_composite_score=3.61`
- `GET /api/v1/portfolios/strong-ai-saas-001/history`
  - returned updated counts:
    - `review_run_count=5`
    - `debate_count=4`
    - `resynthesis_count=3`

Platform health completed on April 10, 2026:

- `http://localhost:5001/health/ready`
  - status: `ok`
- `http://localhost:5004/health/ready`
  - status: `ok`
- `http://localhost:5000/api/health/live`
  - status: `ok`
  - milestone: `7`

## Risks

Technical risk:

- history queries are functional but not yet tuned with milestone-specific indexing for broader audit workloads
- audit events still share one table and rely on scoped filtering; further refinement may still be useful in `M7.1`
- source-document artifacts remain local-first and temporary, so persisted metadata can still outlive local file availability

Product risk:

- the new inspection endpoints improve traceability, but there is still no major frontend history UX beyond the current platform shell
- committee reasoning remains deterministic and bounded, which is correct for the current architecture gate but not a substitute for future provider-backed depth

Delivery risk:

- CI automation for history and artifact regression is still pending
- JS baseline archival execution is not done in this milestone and is carried forward to `M7.1`
- migration tooling discipline exists, but follow-on revisions still need continued governance

## Validation

Primary local workflow:

- `docker compose up -d api worker web`
- `docker compose ps`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference history checks:

- `GET http://localhost:5001/api/v1/portfolios/{portfolio_id}/history`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/artifacts`
- `GET http://localhost:5001/api/v1/debates/{debate_id}/artifacts`
- `GET http://localhost:5001/api/v1/re-syntheses/{resynthesis_id}/artifacts`

Reference health checks:

- `http://localhost:5001/health/ready`
- `http://localhost:5004/health/ready`
- `http://localhost:5000/api/health/live`

## Review Checklist

- portfolio history returns persisted lineage across review runs, debates, and re-syntheses
- artifact inspection makes original versus active artifact ownership explicit
- active artifact source remains unchanged when no score recheck is required
- regression coverage includes forced recheck cases so resynthesized selection stays bounded and verifiable
- approved committee scoring and outcomes remain unchanged
- Docker Compose remains the primary local workflow
- the JS baseline remains frozen reference-only and archival execution is deferred to `M7.1`

## Carry-Forward

- add indexing strategy for history-heavy query paths in `M7.1`
- add CI automation for history and artifact regression in `M7.1`
- decide whether the frozen JS baseline should be archived in `M7.1`
- refine audit-event query boundaries further if a small safe improvement is warranted
- keep source-document artifact strategy explicitly local-first and temporary until a later approved milestone changes it

## Recommendation

Proceed with fixes.

Milestone 7 closes the main auditability gap for persisted review artifacts. The remaining work is operational hardening and archive discipline, not a redesign of the approved review system.
