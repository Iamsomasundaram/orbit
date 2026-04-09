# ORBIT Milestone 0.5a Review Pack

## Scope Delivered

Completed in this milestone:

- Python thin-slice runtime for the approved Milestone 0.5 review path
- Python ingestion and canonicalization of the source markdown portfolio
- Python structured schemas using Pydantic for executable contract validation
- Python execution path for all 15 specialist reviewers with structured outputs preserved
- Python conflict detection v1 on structured review data
- Python committee scorecard and committee report generation
- Python CLI for running the thin slice inside Docker Compose
- pytest parity test comparing Python output to the committed JS baseline artifacts
- Docker Compose services for JS baseline generation, Python execution, and Python parity validation
- migration notes documenting JS baseline retention and Python parity behavior

## Architecture Decisions

- the Milestone 0.5 JS implementation remains intact as the behavioral baseline and reference path
- Milestone 0.5a ports runtime execution only; it does not redesign ORBIT architecture or broaden into Milestone 1 platform work
- Python runtime contracts are enforced with Pydantic models using the existing Milestone 0.5 artifact shapes
- Docker Compose is used to execute the JS baseline and Python runtime without depending on host Python installation
- the Python containers run against the image-built virtual environment at `/app/.venv` so the bind-mounted workspace does not create runtime dependency drift
- parity is defined at full artifact equality for the reference portfolio, not only at headline metric equality

## Quality Status

Validation executed successfully:

- `docker compose build worker worker-test` -> pass
- `docker compose run --rm worker-js-baseline` -> pass
- `docker compose run --rm worker` -> pass
- `docker compose run --rm worker-test` -> pass

Observed thin-slice output for `ProcurePilot`:

- agents executed: 15
- conflicts detected: 5
- final recommendation: `Proceed with Conditions`
- weighted composite score: `3.61`

Parity result:

- Python output exactly matches the committed JS baseline artifact set for the reference portfolio
- no intentional structured output differences remain after parity alignment

Known issues:

- the deterministic heuristic reviewer approach remains a milestone proof path rather than a provider-backed production review engine
- parity is proven for the reference portfolio only; broader fixture coverage remains future work
- API, persistence, web UI, and debate execution remain outside this milestone boundary by design

## Risks

Technical risk:

- parity currently depends on one committed reference portfolio and should be extended in later milestones to the other golden fixtures
- JS and Python implementations now coexist, so future changes must preserve an explicit baseline or remove the dual path deliberately
- runtime parity included one formatting-sensitive scorecard alignment; future edits should keep artifact-level regression checks in place

Product risk:

- deterministic thin-slice behavior proves workflow shape, not final review quality for live investment or governance decisions
- only one portfolio has executable parity coverage today, even though the broader evaluation fixtures are defined

Delivery risk:

- Milestone 1 can still sprawl if service scaffolding starts before the typed Python contracts are treated as the source of truth for the worker runtime
- keeping JS as baseline and Python as target runtime is useful now, but should not remain ambiguous across multiple milestones

## Validation

How to validate locally:

1. Run `docker compose build worker worker-test`.
2. Run `docker compose run --rm worker-js-baseline`.
3. Run `docker compose run --rm worker`.
4. Run `docker compose run --rm worker-test`.
5. Inspect JS baseline artifacts in `tests/fixtures/baselines/procurepilot-js/`.
6. Inspect Python output artifacts in `.orbit-artifacts/python-thin-slice/`.
7. Review the migration notes in `docs/milestone-0.5a/migration-notes.md`.

## Review Checklist

- Does the Python runtime preserve all 15 specialist agents and their structured output contracts?
- Does conflict detection still operate on structured review artifacts rather than raw prose?
- Does the Python scorecard and report path reproduce the approved Milestone 0.5 committee output?
- Is Docker Compose now sufficient to run the baseline path, Python path, and pytest parity check locally?
- Is the milestone still constrained to runtime realignment without drifting into Milestone 1 platform foundation work?

## Recommendation

Proceed with fixes.

Fixes to carry into later milestone planning, not Milestone 0.5a expansion:

- extend parity validation to the promising and weak starter portfolios
- decide when the JS baseline path should become archival rather than active runtime reference
- add CI automation around the Docker Compose parity path so runtime drift is caught earlier

Milestone 0.5a is complete and should stop here pending review.
