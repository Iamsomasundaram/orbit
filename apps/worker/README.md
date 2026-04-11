# Worker App

The worker now contains four active runtime layers:

- the Python thin-slice parity path from Milestone 0.5a onward
- the Milestone 1 Python worker service used by the local platform foundation
- the Milestone 2+ persistence contracts and database-facing schema boundary
- the Milestone 10 llm-backed committee engine with deterministic fallback mode
- the Milestone 11 deliberation-materialization layer derived from persisted committee artifacts

Current capability:

- ingest markdown portfolio documents through the Python runtime path
- canonicalize them into the ORBIT section model
- run all 15 specialist reviewers with structured outputs in either:
  - deterministic mode
  - llm mode
- execute 15 llm committee agents in parallel with bounded concurrency controls
- detect structured conflicts
- build a committee scorecard
- generate a committee report in JSON and Markdown
- generate ordered deliberation timeline entries from persisted review, debate, and re-synthesis artifacts
- materialize durable persistence bundles for portfolio, review, and audit artifacts
- expose worker liveness and readiness health endpoints for Compose and host debugging on port `5004`
- validate Python parity against the archived JS baseline artifact set through Docker Compose across all three golden fixtures
- validate the llm workflow with a mocked provider integration test

Archived JS baseline source:

- `archive/js-baseline/apps/worker/src/review-runner.js`
- `archive/js-baseline/apps/worker/src/cli/review-portfolio.js`
- `archive/js-baseline/apps/worker/src/cli/refresh-baselines.js`

Primary Python runtime entry points:

- `apps/worker/orbit_worker/runner.py`
- `apps/worker/orbit_worker/committee_engine.py`
- `apps/worker/orbit_worker/llm_provider.py`
- `apps/worker/orbit_worker/llm_specs.py`
- `apps/worker/orbit_worker/cli.py`
- `apps/worker/orbit_worker/service.py`
- `apps/worker/orbit_worker/persistence.py`
- `apps/worker/orbit_worker/deliberation.py`
- `apps/worker/tests/test_thin_slice_parity.py`
- `apps/worker/tests/test_persistence_models.py`
- `apps/worker/tests/test_llm_review_workflow.py`
- `apps/worker/tests/test_deliberation_service.py`

Compose validation commands:

- `docker compose build api worker web worker-parity`
- `docker compose up -d postgres redis api worker web`
- `docker compose --profile baseline run --rm worker-parity`
- `docker compose run --rm worker /app/.venv/bin/python -m orbit_worker.cli tests/fixtures/source-documents/procurepilot-thin-slice.md --output-dir .orbit-artifacts/thin-slice`
- `docker compose exec worker /app/.venv/bin/pytest apps/worker/tests -q`
- local llm execution:
  - keep the OpenAI API key in local `key.txt`
  - run with `LLM_RUNTIME_MODE=llm`
