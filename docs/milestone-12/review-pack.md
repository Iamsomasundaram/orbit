# ORBIT Milestone 12 Review Pack

## Scope Delivered

- added Committee Mode as a dedicated boardroom playback route for completed review runs
- staged reveal of persisted deliberation entries across the five fixed committee phases
- added client-side playback controls:
  - start
  - pause / resume
  - skip to next phase
  - jump to final verdict
  - reset
  - skip delays
- added conflict spotlight visualization driven by persisted `conflict_reference` values
- preserved the existing static deliberation page for audit-style inspection
- added Committee Mode navigation from workspace, comparison, portfolio detail, history, and static timeline pages
- preserved deterministic and llm runtime compatibility without changing review, debate, or re-synthesis behavior

## Architecture Decisions

- Committee Mode is a presentation-layer feature, not a new reasoning engine
  - no extra llm inference calls
  - no backend recomputation during playback
  - no schema redesign
- the page fetches the full persisted deliberation dataset once and performs playback locally in the browser
- the five committee phases remain aligned to the persisted Milestone 11 deliberation model
- conflict spotlights are derived from existing persisted conflict references and moderator statements
- the static deliberation page remains available as the audit-first inspection surface

## Persistence Schema

- no schema change in Milestone 12
- no new Alembic revision
- existing authoritative tables remain unchanged:
  - review artifacts
  - debate artifacts
  - re-synthesized artifacts
  - deliberation entries

## API Endpoints

No new backend endpoints in Milestone 12.

Committee Mode consumes the existing persisted timeline surfaces:

- `GET /api/v1/review-runs/{run_id}/deliberation`
- `GET /api/v1/review-runs/{run_id}/deliberation/summary`

New UI route:

- `/review-runs/{run_id}/committee`

## UI Design Decisions

- the boardroom page uses a dark hero and lighter inspection panels to distinguish playback from the static timeline view
- each committee role is visually identified using bounded avatar initials and role-family color coding
- playback controls are kept explicit and deterministic rather than using auto-streaming or hidden timers
- final verdict remains visually withheld until the playback reaches the last phase or the user explicitly jumps to it
- conflict spotlight stays separate from the transcript so disagreements remain interpretable while the timeline grows

## Quality Status

Automated validation completed on April 11, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `42 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `42 passed`

Live platform validation completed on April 11, 2026:

- `docker compose ps`
  - `api`, `worker`, `web`, `postgres`, and `redis` healthy
- `GET http://localhost:5001/api/v1/system/info`
  - returned:
    - `milestone=12`
    - `runtime_mode=deterministic`
    - `runtime_direction=llm-backed-parallel-committee-engine-with-boardroom-playback`
- live deterministic review run:
  - run id: `review-strong-ai-saas-001-20260411T183358404802Z`
  - result:
    - recommendation `Proceed with Conditions`
    - weighted composite score `3.61`
    - active artifact source `original`
    - `53` persisted deliberation entries
    - `5` persisted phases
    - first phase `opening_statements`
    - last phase `final_verdict`
- Committee Mode page
  - `GET http://localhost:5000/review-runs/{run_id}/committee`
  - returned `200`
  - rendered:
    - `Start Playback`
    - `Skip to Next Phase`
    - `Jump to Final Verdict`
    - `Conflict Spotlight`
    - `Phase Rail`
    - `Final Verdict Reveal`
- static timeline page
  - `GET http://localhost:5000/review-runs/{run_id}/deliberation`
  - returned `200`
  - rendered `Static Timeline`
  - linked back to `Committee Mode`
- deterministic runtime timeline generation
  - confirmed through the live run above and the persisted deliberation APIs:
    - `GET /api/v1/review-runs/{run_id}/deliberation`
    - `GET /api/v1/review-runs/{run_id}/deliberation/summary`

## Risks

Technical risk:

- Committee Mode currently relies on page-load fetch and client-side playback only; there is no streaming transport or progressive server push
- the repo still has no browser-automation harness for click-level playback verification, so interactive control behavior is validated by live render checks and client-code inspection rather than headless browser regression
- per-agent runtime duration, token usage, and committee-level cost telemetry are still deferred
- automatic deterministic failover when llm execution fails is still deferred

Product risk:

- the boardroom playback is intentionally thin and replay-focused; it does not yet include filters, thread collapsing, or richer persona comparison tools
- conflict spotlight quality is bounded by the persisted reasoning summaries produced in earlier milestones

Delivery risk:

- the markdown submission path still carries the bounded identity and double-parsing follow-up items
- source-document artifact strategy remains local-first and temporary
- audit-event query boundaries remain shared-table and can be refined later if query volume grows

## Validation

Primary Docker workflow:

- `docker compose run --rm migrate`
- `docker compose up -d api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`

Reference live validation:

- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation`
- `GET http://localhost:5001/api/v1/review-runs/{run_id}/deliberation/summary`
- `GET http://localhost:5000/review-runs/{run_id}/committee`
- `GET http://localhost:5000/review-runs/{run_id}/deliberation`

## Review Checklist

- Committee Mode page loads successfully
- deliberation entries reveal in persisted order
- playback controls work correctly
- conflict spotlight shows disagreement context from persisted records
- final verdict reveal remains tied to the persisted last phase
- deterministic runtime mode still produces timelines
- archived-baseline parity remains green
- static timeline page remains available

## Carry-Forward

- extend the safer bounded identity strategy to the markdown document-submission path
- reduce double parsing in the markdown document-submission path if it can be done without changing canonical behavior
- maintain Alembic migration authoring discipline for future schema changes
- evaluate composite index tuning if workspace and history query volume grows
- keep source-document artifact strategy explicitly local-first and temporary
- refine audit-event query boundaries later if beneficial
- add per-agent telemetry including runtime duration and token usage
- add committee-level token usage and estimated cost
- introduce automatic deterministic fallback when llm execution fails
- persist richer conflict metadata with explicit `conflict_reason` and `conflicting_agents` fields if that change is approved later

## Recommendation

Proceed with fixes.

Milestone 12 delivers the boardroom playback experience without changing the approved review, debate, re-synthesis, persistence, or lineage model. The remaining gap is interaction-level browser automation, not a defect in the underlying committee or timeline architecture.
