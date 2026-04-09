# ORBIT Repo Structure

## 1. Repository Layout

```text
apps/
  api/
  web/
  worker/
packages/
  orbit-core/
  orbit-agents/
  orbit-ingestion/
  orbit-scoring/
  orbit-debate/
  orbit-reporting/
  orbit-evals/
docs/
  milestone-0/
tests/
  fixtures/
    portfolios/
    reviews/
```

## 2. Ownership Model by Workstream

| Workstream | Primary Scope | Planned Directories |
| --- | --- | --- |
| A. Product Documentation | BRD, PRD, framework docs, scoring, rubric | `docs/milestone-0` |
| B. Platform Foundation | workspace config, Compose, env, service bootstraps | root config, `apps/*` |
| C. Backend Core | API skeleton, worker skeleton, persistence design | `apps/api`, `apps/worker`, shared Python packages later |
| D. Agent System | agent registry, prompts, review schemas | `packages/orbit-agents`, `packages/orbit-core` |
| E. Frontend | upload UI, dashboard shell, report UI | `apps/web` |
| F. Evaluation | golden datasets, regression harness, replay tooling | `packages/orbit-evals`, `tests/fixtures` |

## 3. Monorepo Conventions

- `pnpm` workspaces govern JavaScript and TypeScript packages from day 1
- `poetry` is the Python packaging standard for backend services and Python libraries
- service-level code stays under `apps/`
- reusable domain logic stays under `packages/`
- docs that define approval gates stay under `docs/`
- fixtures and regression assets stay under `tests/fixtures/`

## 4. Planned Package Boundaries

- `orbit-core` contains shared contracts that must not depend on downstream business modules
- `orbit-ingestion` owns canonicalization and evidence mapping only
- `orbit-agents` owns registry metadata, prompt contracts, and structured agent outputs
- `orbit-scoring` converts accepted findings into scorecards and recommendation tiers
- `orbit-debate` evaluates reviewer disagreements and manages bounded debate flows
- `orbit-reporting` transforms final run state into human-readable and machine-readable reports
- `orbit-evals` owns benchmark data, replay assertions, and stability criteria

## 5. Milestone 0 Scaffold Policy

The current repository scaffold is intentionally light.

Allowed in Milestone 0:

- directory creation
- root workspace configuration
- documentation and fixtures
- placeholder README files that establish ownership boundaries

Deferred until Milestone 1 or later:

- bootable web, api, and worker applications
- database migrations
- Compose services
- executable review orchestration code
