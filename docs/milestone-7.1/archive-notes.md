# ORBIT Milestone 7.1 Archive Notes

## What Was Archived

The following former active JS baseline paths are now preserved under `archive/js-baseline/`:

- `apps/worker/src/`
- `packages/orbit-agents/`
- `packages/orbit-core/`
- `packages/orbit-debate/`
- `packages/orbit-ingestion/`
- `packages/orbit-reporting/`
- `packages/orbit-scoring/`

## What Remains Active

- Python worker execution under `apps/worker/orbit_worker/`
- committed baseline artifacts under `tests/fixtures/baselines/`
- parity validation through `apps/worker/tests/test_thin_slice_parity.py`
- Docker Compose `worker-parity` service

## What Was Removed From Active Workflow

- `worker-js-baseline` Compose service
- `baseline:refresh` top-level script
- Node-based thin-slice execution as the default review command

## Archive Discipline

- archived JS source is retained for historical traceability only
- archived JS source is no longer a supported runtime or refresh path
- if baseline artifacts ever need regeneration in a future approved milestone, that milestone must explicitly define the archival-exception process rather than silently reactivating the JS runtime
