# ORBIT System Architecture

## 1. Architecture Principles

- enterprise architecture with explicit module boundaries
- typed schemas as the system contract, not a documentation afterthought
- evidence-backed findings with traceable provenance
- bounded orchestration controlled by managers and moderators
- replayability and auditability as first-class requirements
- thin-slice first, but with the full target architecture preserved

## 2. Runtime Topology

Planned local runtime under Docker Compose:

- `web` on port 5000 for Next.js user interfaces
- `api` on port 5001 for FastAPI control plane and read APIs
- `worker` as an internal background execution service
- `postgres` on port 5002 for structured persistence
- `redis` on port 5003 for queues, locks, and workflow coordination

## 3. Core Services and Packages

| Layer | Component | Responsibility |
| --- | --- | --- |
| App | `apps/web` | portfolio submission, run monitoring, scorecards, reports |
| App | `apps/api` | intake endpoints, run orchestration commands, report access |
| App | `apps/worker` | document processing, agent execution, debate, scoring, reporting |
| Package | `orbit-core` | shared models, provider abstraction, settings, audit primitives |
| Package | `orbit-ingestion` | parsing, normalization, canonical portfolio construction |
| Package | `orbit-agents` | agent registry, prompt contracts, structured review schemas |
| Package | `orbit-scoring` | score normalization, weighting, recommendation logic |
| Package | `orbit-debate` | conflict detection, debate routing, moderator decisions |
| Package | `orbit-reporting` | committee synthesis and report assembly |
| Package | `orbit-evals` | golden datasets, replay scripts, stability checks |

## 4. Platform Modules

Mandatory modules and their expected location:

- ingestion -> `packages/orbit-ingestion`
- document parsing -> `packages/orbit-ingestion`
- portfolio canonicalization -> `packages/orbit-ingestion`
- agent registry -> `packages/orbit-agents`
- review orchestration -> `apps/worker` plus `packages/orbit-agents`
- conflict detection -> `packages/orbit-debate`
- debate engine -> `packages/orbit-debate`
- scoring engine -> `packages/orbit-scoring`
- reporting engine -> `packages/orbit-reporting`
- evaluation harness -> `packages/orbit-evals`
- persistence layer -> `apps/api`, `apps/worker`, and future shared data package
- audit trail -> `orbit-core` contracts plus persistence adapters

## 5. End-to-End Review Flow

1. Source documents are ingested and stored with metadata.
2. Parsing extracts structured content and evidence fragments.
3. Canonicalization maps material into the eleven ORBIT portfolio sections.
4. Intake Manager validates completeness and opens a review run.
5. Structuring Agent prepares a review brief for specialists.
6. All 15 specialist reviewer agents execute against the canonical portfolio.
7. Conflict Detector compares structured outputs and groups conflicts.
8. Debate Moderator runs bounded rounds only where conflict severity requires it.
9. Committee Synthesizer merges accepted findings, residual disagreements, and scores.
10. Report Generator emits the final committee report and audit bundle.

## 6. Manager-Led Orchestration Model

Manager-led orchestration is the only allowed execution pattern.

Control roles:

- Intake Manager: validates submission and run readiness
- Structuring Agent: prepares canonical review context
- Conflict Detector: detects structured disagreements
- Debate Moderator: resolves or documents bounded disagreements
- Committee Synthesizer: merges reviewer outputs into a board view
- Report Generator: produces the final artifact package

Specialists never self-organize into open-ended peer chatter. All specialist communication is mediated through structured artifacts owned by the orchestration layer.

## 7. Data Planes

- Control Plane: run commands, workflow state, health, configuration
- Review Plane: canonical portfolios, specialist outputs, conflicts, debates, reports
- Knowledge Plane: prompt contracts, rubrics, scoring rules, evaluation fixtures
- Audit Plane: run metadata, evidence references, versioned configs, replay artifacts

## 8. Provider Abstraction

Provider abstraction is a day-one requirement.

Planned adapter contract:

- request model name and provider name explicitly
- provide deterministic, structured output mode where available
- capture prompt, response metadata, token usage, and latency
- support provider-specific adapters behind a shared interface

Planned adapters:

- OpenAI adapter first and testable in local Docker once implementation begins
- Anthropic adapter placeholder from day 1
- local model adapter placeholder from day 1

## 9. Persistence Boundaries

Planned persistent entities:

- portfolio
- source document
- canonical portfolio
- review run
- agent review
- finding
- score entry
- conflict record
- debate round
- committee report
- audit event

Redis is used for orchestration coordination, short-lived workflow state, and task distribution. PostgreSQL is the source of truth for durable review state.

## 10. Security & Compliance Posture

Milestone 0 architecture assumes:

- explicit audit logs for review actions and model invocations
- evidence traceability for high-severity findings
- separable handling of confidential inputs and generated outputs
- future policy hooks for data retention, redaction, and legal review controls

## 11. Milestone 0.5 Implementation Boundary

Milestone 0.5 may simplify internals, but it must preserve:

- the full staged pipeline
- all 15 specialist contracts
- structured conflicts and score outputs
- report generation from structured state rather than only free-form summaries

