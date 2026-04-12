# ORBIT Milestone 13 Review Pack

## Scope Delivered

- changed the default runtime mode to `llm`
- preserved deterministic execution as:
  - explicit runtime mode
  - automatic fallback when llm execution fails
- implemented adaptive committee routing
  - Tier-1 core screening wave
  - Tier-2 specialist activation from deterministic routing rules
  - passive observers for inactive specialists
- expanded persisted runtime telemetry with:
  - activation tier
  - activation status
  - activation reason
  - routing strategy version
  - routing signals
  - core / specialist / passive counts
  - per-agent duration and token usage
  - committee token and cost totals
- surfaced adaptive telemetry in:
  - review-run detail page
  - Committee Mode
  - deliberation API payloads
- added `0.5x` Committee Mode playback speed
- preserved review, conflict, debate, re-synthesis, deliberation, lineage, and artifact behavior

## Architecture Decisions

- Milestone 13 keeps the approved governance pipeline intact
  - portfolio submission
  - canonicalization
  - review
  - conflict detection
  - bounded debate
  - optional re-synthesis
  - deliberation timeline generation
- adaptive routing is implemented inside the existing committee engine rather than as a new orchestration service
- Tier-1 routing rules are deterministic
  - routing decisions are derived from:
    - portfolio context
    - Tier-1 review scores
    - Tier-1 findings
    - recommendation polarity
- inactive specialists remain visible as passive observers
  - the 15-agent committee identity is preserved
  - Committee Mode can still render the full committee without fabricating new reasoning
- fallback safety remains part of the committee execution boundary
  - llm failures do not crash the review lifecycle
  - requested versus effective runtime remains visible in telemetry
- no new persistence table was introduced
  - adaptive-routing metadata is stored inside existing JSON payloads and audit events

## Runtime Model

Default runtime:

- `llm`

Fallback runtime:

- `deterministic`

Tier-1 core agents:

- Product Strategy Agent
- Market Opportunity Agent
- Finance Agent
- Architecture Agent
- Risk Governance Agent

Tier-2 specialist routing is activated from structured signals such as:

- customer-value uncertainty
- business-model uncertainty
- competitive pressure
- go-to-market complexity
- ai-system risk
- security and compliance risk
- operations complexity
- data dependency complexity
- implementation feasibility risk
- investment-case uncertainty

## Persistence and Migration

Alembic discipline remains active.

Milestone 13 schema impact:

- no new Alembic revision
- no table change
- no destructive persistence modification

Current schema version remains:

- `m12.2-v1`

Reason:

- adaptive routing uses the existing `agent_reviews` JSON payload boundary
- committee runtime summary uses the existing `audit_events` payload boundary
- deliberation records are still generated from persisted artifacts, not recomputed reasoning

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

- `GET http://localhost:5001/api/v1/system/info`
  - returned:
    - `milestone=13`
    - `runtime_mode=llm`
    - `llm_provider=openai`
    - `openai_model=gpt-4o-mini`
    - `llm_max_concurrency=6`
- `GET http://localhost:5000`
  - returned `200`
- live API review run:
  - portfolio `adaptive-m13-live-20260412215602-ac296c0a`
  - run `review-adaptive-m13-live-20260412215602-ac296c0a-20260412T162602964419Z`
  - returned:
    - `effective_runtime_mode=llm`
    - `fallback_applied=false`
    - `final_recommendation=Pilot Only`
    - `weighted_composite_score=2.83`
    - `agent_review_count=15`
    - `conflict_count=9`
    - `core_executed_count=5`
    - `activated_specialist_count=10`
    - `passive_observer_count=0`
    - `total_tokens=37181`
    - `estimated_cost_usd=0.0090867`
    - `routing_strategy_version=m13-adaptive-v1`
- direct adaptive-provider validation on `procurepilot-thin-slice.md`
  - returned:
    - `effective_runtime_mode=llm`
    - `fallback_applied=false`
    - `core_agent_ids=5`
    - `activated_specialist_ids=9`
    - `passive_specialist_ids=1`
    - passive observer `business_model_agent`

Behavioral validation covered:

- llm mode is the default runtime
- deterministic fallback still completes the review when provider calls time out
- Tier-1 execution order and selective Tier-2 activation are verified in `apps/worker/tests/test_llm_review_workflow.py`
- Committee Mode still replays the persisted timeline and exposes `0.5x` playback
- archived baseline parity remains green

## Risks

Technical risk:

- the llm path is functioning, but local OpenAI execution still needs a larger timeout guard than the original `25` second default in this environment
- direct live llm runs remain materially slower than the target under-10-second aspiration
- adaptive routing is deterministic and transparent, but the trigger set is still heuristic and may need future tuning as more real portfolios accumulate

Product risk:

- some portfolios can still activate most or all specialists, which reduces the latency benefit of the adaptive design
- Committee Mode correctly preserves passive observers, but some live portfolios may not exhibit passive states if their routing signals are broad

Delivery risk:

- the current provider integration still depends on network stability to OpenAI
- future telemetry analytics may justify indexed extraction of some routing metadata if usage volume grows

## Validation

Primary Docker workflow:

- `docker compose build migrate api worker web browser-tests worker-parity`
- `docker compose run --rm migrate`
- `docker compose up -d postgres redis api worker web`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- `docker compose --profile baseline run --rm worker-parity`
- `docker compose run --rm browser-tests`

Adaptive committee validation highlights:

- default runtime surfaced by API health is `llm`
- provider-timeout fallback still completes and persists deterministic artifacts
- live llm execution persisted routing signals and token usage
- Committee Mode and review-run detail rendered the new adaptive telemetry
- browser automation still covered:
  - portfolio creation
  - review trigger
  - Committee Mode playback
  - `0.5x` playback speed selection
  - static deliberation view
  - comparison flow

## Carry-Forward

- keep source-document artifact strategy explicitly local-first and temporary
- continue Alembic authoring discipline for any future persistence changes
- tune adaptive routing triggers with real portfolio volume before broader production use
- evaluate whether future telemetry analytics justify dedicated indexed columns
- consider additional prompt and context compression so live llm runs converge toward the latency target without relying on a larger timeout safeguard

## Review Checklist

- default runtime mode is `llm`
- deterministic fallback still completes failed llm runs
- Tier-1 core agents execute first
- Tier-2 specialists activate selectively
- passive observers remain compatible with 15-agent Committee Mode rendering
- adaptive telemetry is visible in review-run detail and Committee Mode
- `0.5x` playback speed is available
- archived baseline parity is still green
- browser automation still passes in Docker Compose

## Recommendation

Proceed with fixes.

Milestone 13 delivers the adaptive committee architecture and preserves the approved governance model. The main remaining gap is performance tuning: live provider execution now works in the default llm mode, but it required increasing the timeout safeguard to `45` seconds in this environment and still runs slower than the target aspiration. The architecture is ready to move forward, but latency and prompt-efficiency tuning should remain active in the next milestone.
