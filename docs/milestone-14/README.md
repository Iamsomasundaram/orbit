# ORBIT Milestone 14

Milestone 14 upgrades committee reasoning to a structured evidence-based format without changing the review workflow.

## Scope Delivered

- structured claim-evidence-risk-implication reasoning in every agent review
- explicit confidence labels for all agents
- evidence-aware moderator synthesis in the deliberation timeline
- evidence visibility in Committee Mode and static deliberation views
- conflict metadata enriched with conflicting claims and evidence
- deterministic compatibility preserved

## What Did Not Change

- review, debate, re-synthesis, and deliberation orchestration
- persistence tables and artifact boundaries
- scoring, conflict detection rules, and committee recommendations

## Key Files

- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/orbit_worker/llm_specs.py`
- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/reviewer.py`
- `apps/worker/orbit_worker/conflicts.py`
- `apps/worker/orbit_worker/deliberation.py`
- `apps/api/orbit_api/deliberations.py`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`
- `apps/web/app/review-runs/[runId]/deliberation/page.tsx`

## Validation

Run the standard Docker workflow:

```
docker compose run --rm migrate
docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q
docker compose --profile baseline run --rm worker-parity
docker compose run --rm browser-tests
```

Manual check:

1. Submit or select a portfolio.
2. Trigger a review run.
3. Open Committee Mode and verify claim/evidence/risk/implication/confidence are visible.
4. Open the static deliberation timeline and verify the same reasoning fields appear.
