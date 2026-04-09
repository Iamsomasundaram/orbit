# ORBIT Milestone 1 Carry-Forward Notes

## Parity Expansion Plan

The Milestone 0.5a parity gate currently proves exact Python parity for the `ProcurePilot` strong portfolio.

Next parity additions should cover the other two defined starter fixtures without changing the approved runtime logic:

1. `tests/fixtures/portfolios/promising-devtool-gaps.yaml`
   Goal: confirm structured conflicts and recommendation bands stay stable for the mixed-quality case.
2. `tests/fixtures/portfolios/weak-startup-idea.yaml`
   Goal: confirm downside scoring, conflict clustering, and recommendation floors behave consistently in the weak case.

Recommended execution sequence:

- add canonical source markdown documents for the two remaining fixtures
- generate committed JS baseline artifacts under a `baseline` fixture directory for each case
- extend the Python parity pytest suite to compare full artifact equality across all three portfolios

## JS Baseline Archival Plan

The JS thin-slice path remains reference-only after Milestone 1.

Recommended archival path:

1. keep the JS baseline active as a reference profile through Milestone 2 while Python remains the production-direction runtime
2. freeze JS baseline behavior once Python parity covers all three starter portfolios
3. move JS baseline modules behind an explicit `reference/legacy` documentation boundary once CI parity checks are stable
4. stop using JS services in active Compose paths after parity and CI are fully trusted

## CI And Regression Strategy Preparation

Recommended CI jobs for the next platform gate:

- Compose build job for `api`, `worker`, and `web`
- health smoke job that boots `postgres`, `redis`, `api`, `worker`, and `web` and checks the health surfaces
- baseline profile regression job for `worker-js-baseline` and `worker-parity`
- parity matrix job across all three starter portfolios after the additional fixtures are added

Recommended acceptance signal:

- no merge to the active backend path unless the Python parity suite and the Compose health smoke suite both pass
