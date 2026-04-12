# ORBIT Milestone 12.2 Review Pack

## Scope Delivered

- added a Playwright browser automation harness for:
  - portfolio creation
  - portfolio listing and comparison
  - review trigger flow
  - Committee Mode playback
  - static deliberation timeline inspection
- added Compose-driven browser automation to CI
- fixed interactive web actions that previously depended on redirect-only form handling
  - client-side portfolio creation with loading and error states
  - client-side review trigger with loading and error states
- added a review-run detail page to expose:
  - runtime telemetry
  - requested versus effective runtime mode
  - fallback state
  - enriched conflict metadata
  - review-scope audit events
- expanded Committee Mode observability with persisted fallback metadata and enriched conflict spotlight inputs
- introduced deterministic fallback safety for llm runtime failures without changing committee semantics
- hardened markdown ingestion with bounded identity normalization and single-pass parsing
- enriched persisted conflict payloads with explainability metadata
- added composite indexes for history and workspace query paths through Alembic
- tightened audit-event boundaries with explicit creation events for review, debate, and re-synthesis
- documented the local-first source-document artifact strategy clearly

## Architecture Decisions

- Milestone 12.2 remains a hardening milestone, not a reasoning milestone
  - no new reasoning stages
  - no new LLM calls
  - no scoring redesign
- browser automation is Docker-first and Compose-driven
  - Playwright runs in a dedicated `browser-tests` container
  - CI uses the same Compose workflow as local validation
- deterministic fallback is implemented inside the existing committee runtime boundary
  - llm failures degrade to deterministic reviewer execution
  - the review still completes and persists the approved artifact types
  - fallback state is surfaced through persisted audit and deliberation metadata
- conflict metadata enrichment is additive
  - no new conflict table
  - enriched fields live inside the existing persisted conflict payload
- markdown submission stability is improved without changing canonical semantics
  - bounded portfolio id normalization
  - single parse followed by source-document rebinding
- audit-event cleanup separates ingestion from review, debate, and re-synthesis scopes more cleanly while keeping the shared table model

## Persistence and Migration

Alembic discipline remains active.

Milestone 12.2 migration:

- `apps/api/alembic/versions/20260412_01_m122_query_hardening.py`

Schema impact:

- no destructive schema change
- no new artifact tables
- additive composite indexes only

Indexes added:

- `ix_review_runs_portfolio_id_created_at`
- `ix_debate_sessions_run_id_created_at`
- `ix_resynthesis_sessions_debate_id_created_at`
- `ix_audit_events_portfolio_id_created_at_event_id`
- `ix_audit_events_run_id_created_at_event_id`

Conflict explainability impact:

- `conflicting_agents`
- `conflict_category`
- `conflict_reason`

These remain backward-compatible because they are stored in the existing JSON payload boundary.

## Quality Status

Automated validation completed on April 12, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `46 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `46 passed`
- `docker compose run --rm browser-tests`
  - result: `2 passed`

Live runtime checks completed on April 12, 2026:

- `docker compose ps`
  - `api`, `worker`, `web`, `postgres`, and `redis` healthy
- `GET http://localhost:5001/api/v1/system/info`
  - returned:
    - `milestone=12.2`
    - `runtime_mode=deterministic`
    - `persistence_schema_version=m12.2-v1`
    - `llm_provider=openai`
    - `openai_model=gpt-4o-mini`
- `GET http://localhost:5000`
  - returned `200`

Hardening-specific regression coverage now includes:

- deterministic fallback on provider failure via mocked llm provider
- markdown bounded-id normalization
- markdown single-pass parsing
- persistence DDL coverage for the new composite indexes
- archived-baseline parity that ignores additive conflict metadata while still failing on frozen artifact drift

## Risks

Technical risk:

- deterministic fallback is validated through a mocked provider failure path, not through live OpenAI fault injection
- the browser suite covers the main bounded workflows, but it is still a thin harness rather than a full UX regression matrix
- conflict explainability metadata is stored in JSON payloads, so future analytics over those fields may justify dedicated indexed columns later

Product risk:

- source documents remain local-first and temporary; they are not yet managed by a durable remote artifact strategy
- markdown and JSON submissions now align more closely, but the markdown path still deserves future identity unification with the safer JSON idea fingerprinting model

Delivery risk:

- additional composite index tuning may still be required if workspace and history query volume grows materially
- audit-event query boundaries are improved but still share a single table, so future scale may justify more explicit query helper surfaces

## Validation

Primary Docker workflow:

- `docker compose build migrate api worker web browser-tests worker-parity`
- `docker compose run --rm migrate`
- `docker compose up -d postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`
- `docker compose run --rm browser-tests`

Browser validation scenarios:

- create portfolio from the home page and verify redirect to history
- trigger review from the history page and verify result rendering
- open review-run detail and inspect telemetry, fallback surface, and enriched conflicts
- run Committee Mode playback, change speed, skip phase, and jump to final verdict
- open the static deliberation timeline
- compare multiple portfolios side by side

## Review Checklist

- browser automation runs in Docker Compose locally and in CI
- portfolio creation works end to end through the web UI
- review trigger works end to end through the web UI
- Committee Mode playback controls respond reliably
- playback speed selection works
- review-run telemetry renders on the dedicated detail page
- deterministic fallback is persisted and observable when llm execution fails
- markdown submission remains canonical and bounded
- conflict spotlight data is richer and remains backward-compatible
- archived-baseline parity remains green

## Carry-Forward

- keep source-document artifact strategy explicitly local-first and temporary until a later storage milestone
- unify the safer bounded identity strategy across all submission modes, including future markdown-first workflows beyond the current bounded normalization
- evaluate whether JSON-payload conflict metadata should eventually gain dedicated indexed columns for analytics-heavy workloads
- continue Alembic authoring discipline for any future persistence change
- revisit composite index tuning only if real history/workspace query volume justifies it

## Recommendation

Proceed.

Milestone 12.2 closes the main hardening gaps from the prior review packs without changing committee behavior. The platform is materially more reliable to operate, easier to observe, and now has automated UI regression coverage in the primary Docker workflow.
