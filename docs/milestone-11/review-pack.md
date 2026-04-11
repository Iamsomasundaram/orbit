# ORBIT Milestone 11 Review Pack

## Scope Delivered

- added a persisted deliberation timeline for completed review runs
- represented committee reasoning in five ordered phases:
  - opening statements
  - conflict identification
  - conflict discussion
  - moderator synthesis
  - final verdict
- derived deliberation entries from existing persisted artifacts only
- added new deliberation retrieval endpoints and a server-rendered timeline page
- preserved deterministic and llm runtime compatibility without changing approved committee outcomes
- introduced the schema extension through Alembic rather than application-side schema drift

## Architecture Decisions

- the deliberation timeline is a derived persistence layer, not a new reasoning engine
  - no extra llm inference calls
  - no synthetic chat transcript generation
  - no committee redesign
- `deliberation_entries` stores one ordered statement per persisted timeline step
- the timeline is rematerialized when the persisted review state changes:
  - review save
  - debate save
  - re-synthesis save
- API summary views are derived from persisted deliberation entries, not from live recomputation
- the UI reads the new timeline APIs and links back to the existing history and artifact surfaces

## Persistence Schema

- added Alembic revision `20260411_01`
- added durable table `deliberation_entries`
- key columns:
  - `run_id`
  - `portfolio_id`
  - `sequence_number`
  - `phase`
  - `agent_role`
  - `statement_type`
  - `statement_text`
  - optional `conflict_reference`
  - `created_at`
- added query index:
  - `ix_deliberation_entries_run_id`

Schema semantics preserved:

- original review artifacts remain authoritative
- debate artifacts remain authoritative
- re-synthesized artifacts remain authoritative when selected
- deliberation augments the model and does not replace existing history or artifact tables

## API Endpoints

New:

- `GET /api/v1/review-runs/{run_id}/deliberation`
- `GET /api/v1/review-runs/{run_id}/deliberation/summary`

Behavior:

- both endpoints read from persisted deliberation records
- both endpoints preserve lineage and active artifact-selection state
- neither endpoint triggers new committee execution or llm usage

## Quality Status

Automated validation completed on April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `42 passed`
  - includes:
    - persistence bundle coverage
    - review/debate/re-synthesis workflow coverage
    - deliberation materialization coverage
    - llm mocked-provider workflow coverage
    - history and artifact regression coverage
- `docker compose --profile baseline run --rm worker-parity`
  - result: `42 passed`

Live platform validation completed on April 11, 2026:

- `docker compose ps`
  - `api`, `worker`, `web`, `postgres`, and `redis` healthy
- `GET http://localhost:5001/api/v1/system/info`
  - returned:
    - `milestone=11`
    - `runtime_mode=deterministic`
    - `runtime_direction=llm-backed-parallel-committee-engine-with-deliberation-timeline`
- live deterministic review run:
  - run id: `review-strong-ai-saas-001-20260411T180031109996Z`
  - result:
    - `15` opening statements
    - `5` conflicts
    - `53` persisted timeline entries
    - `5` persisted phases
    - recommendation `Proceed with Conditions`
    - weighted composite score `3.61`
    - active artifact source `original`
- ordering verification:
  - first entry: `sequence_number=1`, `phase=opening_statements`
  - last entry: `sequence_number=53`, `phase=final_verdict`
- `GET http://localhost:5000/review-runs/{run_id}/deliberation`
  - returned `200`
  - rendered `Committee Deliberation`

## Risks

Technical risk:

- the timeline currently reuses persisted reasoning summaries and bounded debate text; it is useful and auditable, but future richer discussion UX will need more granular telemetry if per-agent runtime and token-level inspection become mandatory
- committee-level token usage and estimated cost are still not persisted
- automatic deterministic failover when llm execution fails is still deferred

Product risk:

- the deliberation page is intentionally thin and replay-oriented; it does not yet provide live streaming, thread filtering, or richer cross-agent visualization
- moderator synthesis currently reflects the bounded deterministic debate model rather than a richer provider-backed moderator

Delivery risk:

- the markdown submission path still carries the older bounded identity and double-parsing follow-up items
- source-document artifact strategy remains local-first and temporary
- audit-event query boundaries remain shared-table and can be refined later if query volume grows

## Validation

Primary Docker workflow:

- `docker compose run --rm migrate`
- `docker compose up -d api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference live validation:

- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation/summary`
- `GET http://localhost:5000/review-runs/{run_id}/deliberation`

## Review Checklist

- Alembic migration is required and applied for the new table
- deliberation records are created during review lifecycle persistence
- timeline retrieval uses persisted records only
- five deliberation phases are represented in order
- deterministic runtime mode still works
- archived-baseline parity remains green
- UI renders the reasoning sequence from the new APIs
- original versus active artifact state remains explicit

## Carry-Forward

- extend the safer bounded identity strategy to the markdown document-submission path
- reduce double parsing in the markdown document-submission path if it can be done without changing canonical behavior
- keep Alembic migration authoring discipline active for future schema changes
- consider composite index tuning if workspace and history query volume grows
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event query boundaries later if beneficial
- add per-agent telemetry including runtime duration and token usage
- add committee-level token usage and estimated cost
- introduce automatic deterministic fallback when llm execution fails
- persist richer conflict metadata with explicit `conflict_reason` and `conflicting_agents` fields if that change is approved in a later schema milestone

## Recommendation

Proceed with fixes.

Milestone 11 delivers the first auditable committee reasoning timeline without changing the approved governance flow or increasing token usage. The remaining work is observability and richer interaction depth, not a redesign of review, debate, or artifact lineage behavior.
