# ORBIT Milestone 15

Milestone 15 introduces decision quality validation by capturing human expert reviews and comparing them against ORBIT committee outcomes.

## Scope Delivered

- human review capture with structured verdict, score, risks, confidence, and notes
- decision validation engine with recommendation match, score difference, and risk overlap metrics
- agreement score and confidence alignment calculations
- decision validation persistence and APIs
- Committee Mode human review overlay
- workspace decision validation summary panel
- deterministic compatibility preserved

## What Did Not Change

- committee orchestration, debate, or re-synthesis logic
- agent prompt structure and evidence-based reasoning schema
- persistence boundaries for existing review artifacts

## Key Files

- `apps/worker/orbit_worker/decision_validation.py`
- `apps/worker/orbit_worker/schemas.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/api/orbit_api/validation.py`
- `apps/api/orbit_api/main.py`
- `apps/web/lib/orbit-api.ts`
- `apps/web/app/page.tsx`
- `apps/web/app/review-runs/[runId]/committee/committee-mode.tsx`

## Validation

Run the standard Docker workflow:

```
docker compose run --rm migrate
docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q
docker compose --profile baseline run --rm worker-parity
docker compose run --rm browser-tests
```

Manual check:

1. Submit a portfolio and run a review.
2. POST a human review to `/api/v1/portfolios/{portfolio_id}/human-reviews`.
3. Open Committee Mode and verify the human overlay renders with agreement score.
4. Check the workspace home page for decision validation summary metrics.
