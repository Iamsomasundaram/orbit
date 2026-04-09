# ORBIT Milestone 2 Data Model

## Source Of Truth

The executable source of truth remains the Python worker contracts in `apps/worker/orbit_worker/schemas.py`.

Milestone 2 adds persistence-facing record models in `apps/worker/orbit_worker/persistence.py` that wrap, hash, and version those runtime contracts without changing their approved behavior.

## Durable Entities

### 1. Portfolios

Represents the submission envelope and lifecycle status for a portfolio.

Primary key:
- `portfolio_id`

### 2. Source Documents

Stores the original input documents attached to a portfolio, with a durable document hash and the typed `SourceDocument` payload.

Primary key:
- `source_document_row_id`

### 3. Canonical Portfolios

Persists the canonical ORBIT portfolio payload and the persistence schema version used to materialize it.

Primary key:
- `canonical_portfolio_row_id`

### 4. Review Runs

Represents one committee review execution envelope, including active backend, reference runtime, prompt contract version, and artifact bundle hash.

Primary key:
- `run_id`

### 5. Agent Reviews

Stores the structured output for each of the 15 specialist agents within a run.

Primary key:
- `agent_review_row_id`

### 6. Conflicts

Stores structured conflict records generated from agent outputs. Conflict detection remains based on structured review data, not raw text.

Primary key:
- `conflict_row_id`

### 7. Scorecards

Stores the committee scorecard for a run, including weighted composite score, recommendation, and structured score payload.

Primary key:
- `run_id`

### 8. Committee Reports

Stores the typed committee report payload plus a durable markdown artifact hash for the rendered report.

Primary key:
- `run_id`

### 9. Audit Events

Stores append-only audit trail events for portfolio registration, canonicalization, review completion, and report materialization.

Primary key:
- `event_id`

## Persistence Characteristics

- schema version: `m2-v1`
- active backend: `python`
- reference runtime: `js-baseline-only`
- JSON payload columns use Postgres `JSONB`
- queryable columns remain explicit alongside the raw payload columns
- table and index definitions are generated directly from executable SQLAlchemy metadata

## Output Stability

Milestone 2 does not change the approved review semantics for the strong thin-slice fixture:

- 15 agents execute
- structured conflicts are produced
- scorecard and committee report still materialize from structured state
- the approved recommendation remains `Proceed with Conditions`
- weighted composite remains `3.61`
