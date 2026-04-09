# ORBIT Product Requirements Document

## 1. Product Goal

Build a serious multi-agent decision intelligence platform that evaluates product and investment proposals through a committee-style workflow and produces evidence-backed findings, scores, conflicts, and recommendations.

## 2. Personas

- Portfolio Submitter: provides product documentation and expects a coherent committee review
- Committee Operator: initiates runs, tracks status, and manages review settings
- Functional Leader: reads domain-specific findings for business, product, engineering, operations, security, or legal lenses
- Executive Decision Maker: reads the final recommendation and conditions
- Audit and Compliance Reviewer: inspects evidence coverage, assumptions, and run traceability

## 3. Primary User Journeys

### 3.1 Submit Portfolio

1. User uploads one or more portfolio documents.
2. ORBIT creates an intake record and stores source artifacts.
3. The system parses documents and builds a canonical ORBIT portfolio.

### 3.2 Run Review Committee

1. Committee Operator starts a review run on a canonical portfolio.
2. The intake manager validates required sections and evidence completeness.
3. Specialist agents run under a manager-led orchestration plan.
4. Conflicts are detected on structured outputs.
5. Debate is triggered only where thresholds are crossed.
6. Committee synthesis produces the final scorecard and recommendation.

### 3.3 Inspect Decision Quality

1. User opens the report dashboard.
2. User reviews section-level findings, conflicts, and open questions.
3. User checks linked evidence and missing evidence gaps.
4. User exports or shares the committee report.

### 3.4 Evaluate System Quality

1. Operator runs ORBIT against golden portfolios.
2. The evaluation harness compares scores, findings, and recommendation tiers.
3. Stability thresholds and regression alerts are generated.

## 4. Functional Requirements

### 4.1 Ingestion

- accept portfolio inputs as markdown, text, PDF-derived text, or structured JSON later
- store source document metadata and provenance
- support one-to-many source documents for a single portfolio review

### 4.2 Canonicalization

- normalize all inputs into the eleven required ORBIT portfolio sections
- mark missing, inferred, and source-backed fields separately
- generate evidence references at section and field level

### 4.3 Agent Review

- register all 15 specialist reviewer agents
- enforce structured output contracts for every agent
- preserve agent-specific assumptions, open questions, and evidence gaps
- allow simplified prompt behaviors in Milestone 0.5 without changing contracts

### 4.4 Conflict Detection and Debate

- compare reviewer outputs on structured representations rather than raw text
- detect score divergence, recommendation conflict, assumption mismatch, evidence completeness mismatch, and risk severity mismatch
- escalate only bounded conflicts into debate rounds
- stop debate after configured round limits and produce moderator resolution notes

### 4.5 Scoring and Governance

- score every portfolio on the eight mandatory dimensions
- record numeric score, confidence, evidence completeness, and severity flags
- compute a final recommendation tier with rule-based guardrails
- expose confidence and evidence completeness alongside recommendation outputs

### 4.6 Reporting

- generate a committee summary, domain findings, conflict summary, scorecard, recommendation tier, and conditions
- preserve evidence references for every material finding
- support ORBIT reviewing ORBIT in a future milestone using the same pipeline

### 4.7 Audit and Persistence

- store review runs, agent outputs, conflicts, debate artifacts, final reports, and configuration metadata
- preserve replayability for later evaluation and audit review

### 4.8 Evaluation

- define golden portfolio fixtures from Milestone 0 onward
- compare recommendation tiers, dimension scores, and key findings against expectations
- fail evaluations when stability thresholds are violated

## 5. Non-Functional Requirements

- typed schemas everywhere for core objects
- modular architecture with clear service and package boundaries
- reproducible local development under Docker Compose
- provider abstraction with first-class support for switching LLM backends later
- auditability for every portfolio run
- explicit milestone gates using the Ralph Framework

## 6. Milestone 0.5 Thin Slice Requirements

The thin slice must prove:

- a single portfolio can be ingested and normalized
- all 15 agents can execute and return valid structured findings
- conflict detection v1 operates on structured outputs
- scoring and final recommendation can be generated
- a committee report can be rendered from the run state

Temporary simplifications allowed in Milestone 0.5:

- simplified prompt depth and deterministic heuristics where useful
- single-document review input path
- reduced UI polish
- minimal persistence footprint if replayability is retained

Forbidden simplifications:

- reducing the permanent agent set below 15
- bypassing canonical portfolio generation
- collapsing conflict detection into free-form text summarization only
- removing evidence references from findings

## 7. External Dependencies

- OpenAI API for initial live LLM adapter
- PostgreSQL and pgvector for persistence and future retrieval support
- Redis for task and workflow coordination
- Docker Compose for local environment orchestration

## 8. Acceptance Criteria for Milestone 0

- all milestone documents are present and reviewable
- the repo scaffold matches the approved package and app boundaries
- golden portfolio fixtures exist for strong, middling, and weak proposals
- the Milestone 0 review pack includes validation steps and a recommendation
