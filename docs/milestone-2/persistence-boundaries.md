# ORBIT Milestone 2 Persistence Boundaries

## Boundary Design

Milestone 2 introduces a persistence boundary without expanding into Milestone 3 ingestion workflow or database write orchestration.

Boundary layers:

1. Runtime contracts
   `apps/worker/orbit_worker/schemas.py`

2. Persistence record models
   `apps/worker/orbit_worker/persistence.py`

3. Repository abstraction
   `PersistenceRepository` protocol with `InMemoryPersistenceRepository`

4. Database-facing schema
   SQLAlchemy table metadata plus generated Postgres DDL

5. Introspection surface
   `apps/api/orbit_api/persistence.py` and `/api/v1/system/persistence/*`

## Materialization Flow

The approved thin-slice runtime still executes this sequence:

- ingestion
- canonicalization
- 15 specialist agent reviews
- conflict detection v1
- scorecard generation
- committee report generation

Milestone 2 adds a persistence materialization layer after those artifacts exist in structured form.

The persistence bundle builder:

- versions the materialization under `m2-v1`
- records hashes for canonical portfolio, agent review payloads, conflicts, scorecard, report payload, and markdown
- preserves the Python worker contracts as source-of-truth payloads
- creates row-shaped values that can be inserted into Postgres later without changing the runtime contracts

## Deliberate Non-Scope

Milestone 2 does not add:

- live database write paths
- migrations framework setup
- portfolio submission APIs
- job queue workflow redesign
- LangGraph orchestration changes
- Milestone 3 ingestion expansion

## Carry-Forward Planning

Tracked for future approved milestones:

- parity expansion to `promising-devtool-gaps` and `weak-startup-idea`
- JS baseline moves from active reference to archival after parity covers all three starter portfolios and parity CI is stable
- CI should add Compose health smoke checks plus baseline parity regression before broader backend workflow work
