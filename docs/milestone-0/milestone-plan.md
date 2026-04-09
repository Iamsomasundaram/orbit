# ORBIT Milestone Plan

## 1. Delivery Philosophy

ORBIT keeps the full 15-agent target architecture from day 1, but implementation follows a thin-slice progression. Each milestone has a review gate and should emphasize parallel work where dependencies allow it.

## 2. Milestone Map

| Milestone | Primary Outcome | Parallel Workstreams | Exit Criteria |
| --- | --- | --- | --- |
| 0 | planning and architecture | A, B, D, F | document pack, evaluation definition, repo blueprint, review pack |
| 0.5 | thin-slice proof | B, C, D, E, F | single portfolio runs end-to-end through all 15 agents |
| 1 | platform foundation | B, C, E | monorepo scaffold, Compose, env, health endpoints |
| 2 | data model and schemas | C, D, F | Pydantic models, DB schema, scoring and debate schemas |
| 3 | ingestion and canonicalization | C, D | file ingestion and canonical portfolio generation |
| 4 | specialist review engine | C, D | 15-agent framework, prompt contracts, structured findings |
| 5 | conflict detection | C, D, F | structured divergence rules and mismatch detection |
| 6 | debate and synthesis | C, D | bounded debate and committee synthesis report |
| 7 | frontend experience | E | upload, scorecards, findings dashboard, report viewer |
| 8 | evaluation harness | F, C, D | replayable reviews, regression tests, stability checks |
| 9 | ORBIT reviews ORBIT | A, C, D, F | ORBIT portfolio docs created and reviewed by ORBIT |

## 3. Milestone 0 Deliverables

- BRD
- PRD
- system architecture
- agent architecture
- conflict detection design
- scoring model
- evaluation rubric
- golden portfolio format
- repo structure
- milestone plan
- Ralph Framework review pack

## 4. Milestone 0.5 Deliverables

- one portfolio input path
- canonicalization flow
- all 15 agents with simplified but valid structured behavior
- conflict detection v1
- scorecard generation
- committee report synthesis

## 5. Parallel Workstream Detail

### Workstream A: Product Documentation

Owns product framing, scoring policy, evaluation rubric, and dogfooding artifacts.

### Workstream B: Platform Foundation

Owns workspace tooling, Compose, env, service bootstraps, and local run setup.

### Workstream C: Backend Core

Owns API, worker, persistence, orchestration state, and supporting services.

### Workstream D: Agent System

Owns agent contracts, prompt design, registry metadata, conflict rules, and debate protocol.

### Workstream E: Frontend

Owns upload flows, dashboards, report viewer, and scorecard UI.

### Workstream F: Evaluation

Owns golden datasets, replay scenarios, expected outputs, and regression definitions.

## 6. Gate Policy

After each milestone, produce a Milestone Review Pack containing:

- scope delivered
- architecture decisions
- quality status
- risks
- validation steps
- review checklist
- recommendation

No milestone should auto-advance without explicit review.

## 7. Current Recommendation

Complete Milestone 0 review first. If accepted, proceed to Milestone 0.5 with implementation limited to the thin slice only.
