# ORBIT Milestone 2.1 Review Pack

## Scope Delivered

Completed in this milestone:

- expanded the parity matrix to all three golden fixtures: `strong-ai-saas`, `promising-devtool-gaps`, and `weak-startup-idea`
- added canonical markdown source documents for the two previously missing fixture inputs
- refreshed committed JS baseline artifacts for all parity cases through a Docker-first baseline runner
- exposed the Python worker service on host port `5004` for local debugging while keeping Compose as the primary development workflow
- formalized the JS baseline lifecycle as `frozen-baseline` with archival target `Milestone 4`
- updated milestone and runtime docs so Milestone 2 and 2.1 are reviewed together as a combined gate

## Architecture Decisions

- Milestone 2.1 does not change scoring logic, conflict logic, or portfolio semantics; it stabilizes the approved behavior through broader regression coverage
- parity remains full-artifact comparison between Python outputs and the frozen JS baseline outputs, not a looser score-only comparison
- the JS baseline remains isolated to the Compose `baseline` profile and is now treated as frozen reference behavior rather than an evolving parallel backend path
- local debugging needs are addressed by exposing the worker on host port `5004`, while Docker Compose remains the system of record for runtime execution and dependency management
- the archival target is documented now, but actual archival work remains out of scope until the target milestone is approved

## Quality Status

Validation executed successfully:

- `docker compose build api worker web worker-parity` -> pass
- `docker compose up -d postgres redis api worker web` -> pass
- `docker compose ps` -> platform services healthy
- `http://localhost:5001/health/ready` -> pass
- `http://localhost:5000/api/health/ready` -> pass
- `http://localhost:5004/health/ready` -> pass
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q` -> pass
- `docker compose --profile baseline run --rm worker-js-baseline` -> pass
- `docker compose --profile baseline run --rm worker-parity` -> pass

Observed parity results:

- `strong-ai-saas` -> 15 agents, 5 conflicts, `Proceed with Conditions`, `3.61`
- `promising-devtool-gaps` -> artifact-identical Python and JS outputs
- `weak-startup-idea` -> artifact-identical Python and JS outputs
- full parity suite now passes across all three fixtures in the Python runtime

Known issues:

- the JS baseline is now frozen but not yet archived; the code remains in-repo until the archival target milestone is approved
- Compose is the validated path, but host-side package manager drift remains a reason to avoid non-containerized setup as the primary workflow
- parity coverage is complete for the golden fixtures, but CI enforcement for this gate still needs to be formalized in a later approved milestone

## Risks

Technical risk:

- frozen baseline drift is now controlled through artifacts, but without CI enforcement future changes could still skip the parity gate unless process discipline holds
- worker port exposure is for local debugging only and should not be mistaken for a production networking posture
- the next milestone must avoid changing ingestion or review behavior without re-running the full three-case parity suite

Product risk:

- Milestone 2.1 improves confidence in backend correctness, not user-facing workflow breadth
- strong parity does not replace the need for future evaluation harness and replay coverage beyond the starter golden set

Delivery risk:

- if archival slips beyond the documented target, the frozen JS path could still impose maintenance drag
- if the combined Milestone 2 and 2.1 gate is not treated as mandatory, later milestone work could erode the stabilization value prematurely

## Validation

How to validate locally:

1. Review `.env.example` and optionally create `.env`.
2. Run `docker compose build api worker web worker-parity`.
3. Run `docker compose up -d postgres redis api worker web`.
4. Run `docker compose ps`.
5. Check `http://localhost:5001/health/ready`.
6. Check `http://localhost:5000/api/health/ready`.
7. Check `http://localhost:5004/health/ready`.
8. Run `docker compose --profile baseline run --rm worker-js-baseline`.
9. Run `docker compose --profile baseline run --rm worker-parity`.
10. Run `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`.
11. Run `docker compose down --remove-orphans` when finished.

## Review Checklist

- Does the parity suite now cover all three golden fixtures?
- Are Python artifacts still identical to the frozen JS baseline artifacts for every fixture?
- Is the worker exposed on host port `5004` for local debugging?
- Does Docker Compose remain the primary and validated development workflow?
- Is the JS baseline lifecycle clearly marked as `frozen-baseline` with an archival target milestone?
- Are Milestone 2 and Milestone 2.1 clearly treated as one combined review gate before any move forward?

## Recommendation

Proceed with fixes.

Fixes to carry beyond the combined gate, not Milestone 2.1 expansion:

- enforce the three-fixture parity matrix and Compose health checks in CI
- archive the frozen JS baseline at the approved target milestone rather than letting it linger as an implied second backend
- keep the worker debug port local-only and maintain Docker-first developer guidance

Milestone 2.1 is complete and is reviewed together with Milestone 2 before any move forward.
