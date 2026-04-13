# ORBIT Milestone 14 Review Pack

## Scope Delivered

- enforced structured claim-evidence-risk-implication reasoning for all agents
- added explicit confidence labels (Low/Medium/High) to agent reasoning
- exposed evidence-aware reasoning in Committee Mode and static deliberation timeline
- enriched conflict metadata with conflicting claims and evidence
- added evidence-aware moderator synthesis text in the deliberation timeline
- preserved deterministic compatibility and the existing review/debate workflow

## Architecture Decisions

- reasoning schema is embedded inside `agent_reviews.review_payload` to avoid schema churn
- deliberation APIs now return an `agent_reasoning` view derived from persisted reviews
- conflict detection enriches payloads without changing conflict detection rules
- no new tables or migrations were introduced

## Reasoning Schema

Each agent review now includes:

- `claim`
- `evidence`
- `risk`
- `implication`
- `score`
- `confidence` (Low | Medium | High)

## Quality Status

Automated validation completed on April 13, 2026:

- `docker compose run --rm migrate`
  - result: success
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
  - result: `46 passed`
- `docker compose --profile baseline run --rm worker-parity`
  - result: `46 passed`
- `docker compose run --rm browser-tests`
  - result: `2 passed`

Manual validation:

- confirm evidence fields are visible in Committee Mode and static timeline
- confirm conflicts show conflicting claims and evidence
- confirm deterministic runs still complete with zero token telemetry

## Risks

- evidence formatting quality depends on agent prompt discipline and response normalization
- some passive observers may show low-confidence evidence summaries by design
- legacy artifacts do not backfill reasoning; UI will show evidence only for new runs

## Validation Notes

Baseline parity remains deterministic and ignores new reasoning fields for archived fixtures.

## Recommendation

Proceed with fixes.

Reasoning structure is now explicit and auditable, but prompt tuning and evidence normalization will need iterative refinement as more real portfolios are reviewed.
