# ORBIT Milestone 12.1 Review Pack

## Scope Delivered

- improved Committee Mode agent identity rendering with persistent role cards, initials-based avatars, stance badges, and opening-statement snapshots
- extended the conflict spotlight to show disagreement topic, involved agents, stance-aware positions, and moderator interpretation
- added playback speed controls:
  - `1x`
  - `2x`
  - `5x`
  - `instant`
- exposed committee runtime telemetry in Committee Mode:
  - runtime mode
  - provider
  - model
  - agent count
  - total tokens
  - per-agent tokens
  - estimated cost
- preserved deterministic compatibility with explicit zero-token rendering
- preserved the archived JS baseline artifact set and strengthened parity checks so additive deterministic telemetry does not masquerade as baseline drift

## Architecture Decisions

- Milestone 12.1 remains a presentation and observability milestone, not a new reasoning stage
  - no extra LLM inference calls
  - no backend recomputation during playback
  - no committee logic redesign
- Committee Mode continues to fetch the persisted deliberation dataset once and drive playback locally in the browser
- runtime telemetry is derived from existing persisted agent-review metadata rather than from a new persistence table
- archived baseline artifacts remain frozen on disk; parity now compares the historical deterministic baseline shape while separately asserting zero-token telemetry for deterministic runs
- moderator and system entries no longer receive misleading support/neutral/oppose badges when no recommendation signal exists

## Persistence Schema

- no schema change in Milestone 12.1
- no new Alembic revision
- existing authoritative tables remain unchanged:
  - review artifacts
  - debate artifacts
  - re-synthesized artifacts
  - deliberation entries

## API Endpoints

No new backend endpoints in Milestone 12.1.

Committee Mode continues to consume:

- `GET /api/v1/review-runs/{run_id}/deliberation`
- `GET /api/v1/review-runs/{run_id}/deliberation/summary`

The deliberation detail payload now includes runtime telemetry metadata derived from persisted review records:

- committee-level runtime metadata
- per-agent token and cost telemetry

## UI Design Decisions

- agent identity is shown as a stable lineup rather than only within the currently speaking card, which makes role continuity easier to track across the replay
- stance is displayed separately from recommendation so conflict positions are easier to scan
- playback speed stays explicit and local to the browser rather than introducing a streaming transport or server push
- runtime telemetry stays grouped in a dedicated header panel so execution context is visible without displacing the deliberation flow
- the static timeline route remains the audit-first inspection surface while Committee Mode remains the playback-first surface

## Quality Status

Automated validation completed on April 12, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `43 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `43 passed`

Live platform validation completed on April 12, 2026:

- `docker compose ps`
  - `api`, `worker`, `web`, `postgres`, and `redis` healthy after rebuild
- `GET http://localhost:5001/api/v1/system/info`
  - returned:
    - `milestone=12.1`
    - `runtime_mode=deterministic`
    - `runtime_direction=llm-backed-parallel-committee-engine-with-observable-boardroom-playback`
- live deterministic review run:
  - portfolio id: `strong-ai-saas-001`
  - run id: `review-strong-ai-saas-001-20260412T062417384254Z`
  - result:
    - recommendation `Proceed with Conditions`
    - weighted composite score `3.61`
    - active artifact source `original`
    - `53` persisted deliberation entries
    - `5` persisted phases
    - `15` agents executed
    - total tokens `0`
    - estimated cost `0.0`
- Committee Mode page
  - `GET http://localhost:5000/review-runs/{run_id}/committee`
  - returned `200`
  - verified page sections:
    - `Committee Runtime Metadata`
    - `Agent Identity Lineup`
    - `Playback speed`
    - `Conflict Spotlight`
- deliberation detail API
  - `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation`
  - returned runtime telemetry with zero-token deterministic values

## Risks

Technical risk:

- the repo still has no browser-automation harness for click-level playback verification, so interaction behavior is validated by rebuilt route checks and client-code inspection rather than headless browser regression
- token telemetry is visible in Committee Mode, but richer per-agent duration and token drill-down outside the playback page is still deferred
- deterministic fallback when LLM execution fails remains deferred

Product risk:

- Committee Mode remains a replay interface; it does not yet provide filtering, transcript collapsing, or richer side-by-side persona analysis
- conflict interpretation quality still depends on the quality of persisted reasoning summaries from earlier milestones

Delivery risk:

- the markdown submission path still carries the bounded identity and double-parsing follow-up items
- source-document artifact strategy remains local-first and temporary
- composite index tuning can become necessary if history or workspace query volume grows

## Validation

Primary Docker workflow:

- `docker compose up -d --build postgres redis api worker web`
- `docker compose run --rm migrate`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference live validation:

- `GET http://localhost:5001/api/v1/system/info`
- `POST http://localhost:5001/api/v1/portfolios/{portfolio_id}/review-runs`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation/summary`
- `GET http://localhost:5000/review-runs/{run_id}/committee`

## Review Checklist

- Committee Mode page loads successfully
- agent identity cards render from persisted committee roles
- conflict spotlight shows stance-aware disagreement context
- playback speed options render correctly
- runtime telemetry appears in the Committee Mode header
- deterministic runtime mode still produces zero-token telemetry
- archived-baseline parity remains green
- static timeline page remains available

## Carry-Forward

- extend the safer bounded identity strategy to the markdown document-submission path
- reduce double parsing in the markdown document-submission path if it can be done without changing canonical behavior
- maintain Alembic migration authoring discipline for future schema changes
- evaluate composite index tuning if workspace and history query volume grows
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event query boundaries later if beneficial
- add richer per-agent runtime duration and token telemetry surfaces beyond Committee Mode
- add committee-level cost trending and historical telemetry comparisons
- introduce automatic deterministic fallback when LLM execution fails
- persist richer conflict metadata with explicit `conflict_reason` and `conflicting_agents` fields if that change is approved later

## Recommendation

Proceed with fixes.

Milestone 12.1 materially improves Committee Mode clarity and observability without changing the approved committee engine or persistence model. The remaining gap is interaction-level browser automation, not a defect in the review, debate, re-synthesis, or deliberation architecture.
