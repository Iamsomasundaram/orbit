# Archived JS Baseline

This directory preserves the original JavaScript thin-slice reference runtime that was used to establish behavioral parity before the Python worker became the only active backend direction.

Archive status:

- lifecycle stage: `archived-baseline`
- archival milestone: `Milestone 7.1`
- active backend direction: Python only
- active parity reference: committed baseline artifacts under `tests/fixtures/baselines/`

Archived source mapping:

- former worker JS entry points now live under `archive/js-baseline/apps/worker/src/`
- former JS baseline packages now live under `archive/js-baseline/packages/`

Important boundaries:

- this source is not part of the active Docker Compose workflow
- the `worker-js-baseline` Compose service has been removed
- top-level review execution now routes through the Python worker CLI
- parity still compares Python output to the committed artifact set produced from this archived baseline

Retained committed baseline artifacts:

- `tests/fixtures/baselines/procurepilot-js/`
- `tests/fixtures/baselines/traceforge-js/`
- `tests/fixtures/baselines/moodmesh-js/`

Archive intent:

- preserve the original behavioral reference for auditability
- remove ambiguity about the active backend direction
- keep parity validation stable without maintaining an executable second runtime
