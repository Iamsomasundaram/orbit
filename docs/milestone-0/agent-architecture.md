# ORBIT Agent Architecture

## 1. Execution Model

ORBIT uses a manager-led execution model:

Intake Manager -> Structuring Agent -> 15 Specialist Reviewers -> Conflict Detector -> Debate Moderator -> Committee Synthesizer -> Report Generator

The 15 specialist agents are fixed architecture elements. Their first implementation may be simplified, but their contracts remain stable.

## 2. Common Specialist Output Contract

Every specialist returns the same top-level structure:

```json
{
  "agent_id": "system_architect",
  "agent_name": "System Architect",
  "portfolio_id": "portfolio-001",
  "review_summary": "Short executive summary",
  "findings": [
    {
      "finding_id": "finding-001",
      "title": "Architecture has a single-region dependency",
      "category": "operational_resilience",
      "severity": "major",
      "claim": "The current architecture has no regional failover plan.",
      "evidence_refs": ["portfolio.architecture_system_design", "portfolio.operational_resilience"],
      "assumptions": ["initial deployment is cloud-hosted"],
      "recommended_action": "Add failover architecture and recovery objectives",
      "score_impacts": [
        {
          "dimension": "Operational Resilience",
          "delta": -1.0,
          "rationale": "No stated disaster recovery posture"
        }
      ]
    }
  ],
  "dimension_scores": [
    {
      "dimension": "Technical Feasibility",
      "score": 3.4,
      "confidence": 0.72,
      "evidence_completeness": 0.68,
      "severity_flags": ["major_architecture_gap"]
    }
  ],
  "recommendation": "Proceed with Conditions",
  "open_questions": ["What are the target uptime objectives?"],
  "evidence_gaps": ["No scaling assumptions document was provided"],
  "assumption_register": ["Core workload is multi-tenant SaaS"],
  "review_metadata": {
    "prompt_contract_version": "v1",
    "model_provider": "openai",
    "model_name": "placeholder",
    "duration_ms": 0
  }
}
```

## 3. Prompt Contract Template

Every specialist prompt contract must include:

- role identity and board mandate
- portfolio sections in scope
- scoring dimensions the agent may influence
- mandatory evidence citation rules
- structured output schema
- explicit instruction to record assumptions and evidence gaps
- recommendation guardrails consistent with the scoring model

## 4. Specialist Reviewer Catalog

| Agent | Domain Lens | Core Questions | Primary Score Influence |
| --- | --- | --- | --- |
| Business Owner | strategic sponsorship | Does the proposal solve a meaningful business problem with clear ownership and value? | Problem Validity, Economic Viability |
| Finance Lead | financial viability | Are cost structure, unit economics, and funding assumptions credible? | Economic Viability |
| Sales Strategist | revenue motion | Is there a viable buyer journey, segment focus, and sales motion? | Market Fit, Economic Viability |
| Marketing Strategist | demand creation | Is positioning clear, differentiated, and reachable through realistic channels? | Market Fit, Product Quality |
| Product Manager | product scope | Does the product solve the right problem with a coherent roadmap and measurable outcomes? | Product Quality, Problem Validity |
| UX/UI Reviewer | usability and workflow | Will target users understand and adopt the product experience? | Product Quality |
| Customer Success Lead | adoption and retention | Can onboarding, support, and expansion succeed with the proposed model? | Product Quality, Operational Resilience |
| System Architect | system design | Is the architecture coherent, scalable, secure, and operable? | Technical Feasibility, Operational Resilience |
| AI/Data Scientist | model quality and data | Are data strategy, evaluation, model behavior, and safety assumptions credible? | AI Reliability, Technical Feasibility |
| Developer | delivery feasibility | Can the proposed system be built and maintained with realistic engineering effort? | Technical Feasibility |
| DevOps Architect | delivery platform | Are CI/CD, environments, observability, and release controls adequate? | Operational Resilience, Technical Feasibility |
| System Maintenance Lead | sustainment | Can the system be supported, upgraded, and operated over time? | Operational Resilience |
| QA/SDET | quality engineering | Is the test strategy sufficient to manage delivery and regression risk? | Product Quality, Operational Resilience |
| InfoSec Architect | security posture | Are identity, data protection, infrastructure security, and threat assumptions sound? | Security & Compliance, Operational Resilience |
| Legal & Compliance Reviewer | regulatory posture | Are legal, regulatory, privacy, and contractual risks understood and mitigated? | Security & Compliance |

## 5. Orchestration Control Roles

These roles are part of the platform architecture even though they are not counted in the 15 board agents:

- Intake Manager: validates portfolio readiness and routes missing inputs
- Structuring Agent: prepares the canonical review brief from normalized sections
- Conflict Detector: compares structured outputs and creates conflict objects
- Debate Moderator: manages bounded debate and records accepted or unresolved positions
- Committee Synthesizer: aggregates accepted findings and final score rationale
- Report Generator: converts final run state into a report package

## 6. Evidence Policy

Every material claim must point to one or more evidence references. Evidence references can target:

- canonical portfolio sections
- source document fragments
- prior conflict or debate artifacts when reused
- explicit evidence-gap markers if evidence is missing

A finding without evidence is valid only as an open question or assumption, not as a high-confidence conclusion.

## 7. M0.5 Simplification Policy

For Milestone 0.5, agent prompts may use simplified rubric-guided reasoning, reduced context windows, and fixed templates. The following cannot be simplified away:

- all 15 agents must execute
- all agents must return the shared structured contract
- each agent must emit evidence gaps and assumptions when relevant
- recommendations must remain aligned to the scoring model tiers

