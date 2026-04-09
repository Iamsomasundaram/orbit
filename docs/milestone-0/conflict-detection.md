# ORBIT Conflict Detection Strategy

## 1. Objective

Conflict detection identifies meaningful disagreement between specialist reviewers before committee synthesis. It operates primarily on structured outputs, not raw prose, so the platform can detect, prioritize, and route disagreements consistently.

## 2. Structured Inputs

The conflict engine consumes:

- dimension scores by agent
- final recommendation tier by agent
- finding categories and severity levels
- assumption registers
- evidence gap declarations
- score impact entries attached to findings

## 3. Conflict Types

### 3.1 Score Divergence

Triggered when:

- two agents differ by 1.5 points or more on the same 0 to 5 dimension, or
- an agent score is a statistical outlier against the reviewer set for that dimension

### 3.2 Recommendation Conflict

Triggered when:

- two agents are two or more tiers apart in recommendation polarity, or
- recommended actions are mutually incompatible for the same issue

### 3.3 Assumption Mismatch

Triggered when:

- two agents make contradictory assumptions about the same topic
- one agent treats an assumption as satisfied while another flags it as missing or invalid

### 3.4 Evidence Completeness Mismatch

Triggered when:

- evidence completeness differs by 0.35 or more for the same dimension or topic
- one agent cites sufficient evidence while another declares a material evidence gap on the same topic

### 3.5 Risk Severity Mismatch

Triggered when:

- severity differs by two or more levels on the same risk topic
- one agent marks a topic as critical while another marks it low or informational

## 4. Conflict Object Contract

Every detected conflict should be represented as:

```json
{
  "conflict_id": "conflict-001",
  "conflict_type": "score_divergence",
  "topic": "Technical Feasibility",
  "participants": ["system_architect", "developer"],
  "severity": "high",
  "trigger_reason": "Score delta 1.8 exceeds threshold 1.5",
  "supporting_artifacts": ["agent_review.system_architect", "agent_review.developer"],
  "debate_required": true,
  "routing_reason": "Recommendation boundary may change",
  "status": "open"
}
```

## 5. Prioritization Rules

Conflicts are prioritized by impact and governance sensitivity.

High priority:

- conflicts touching Security & Compliance
- conflicts that can change the final recommendation tier
- conflicts with critical severity findings

Medium priority:

- conflicts that materially change one or more dimension scores
- conflicts that reveal evidence incompleteness on major topics

Low priority:

- stylistic or wording differences without score or recommendation impact
- low-severity findings with aligned mitigation direction

## 6. Debate Routing Policy

Route to debate when at least one of the following is true:

- conflict severity is high
- recommendation tier may change after resolution
- a critical or major risk is disputed
- evidence sufficiency is materially disputed

Do not route to debate when:

- the conflict can be resolved mechanically from the rubric
- the disagreement is informational only
- the conflict does not affect scoring, recommendation, or major mitigation actions

## 7. Bounded Debate Constraints

Milestone 0 architecture sets the following defaults:

- maximum 2 debate rounds per conflict cluster in Milestone 0.5
- moderator may request one clarification artifact from each side per round
- unresolved conflicts must still be surfaced in the final report

## 8. Output of Conflict Resolution

Each resolved conflict records:

- accepted position
- rejected or deferred position
- residual uncertainty
- impact on scores and recommendation
- moderator rationale and evidence basis

## 9. Design Notes

The conflict engine should compare normalized fields and enumerations wherever possible. Free-form text similarity may assist clustering later, but it must not be the primary basis of governance decisions.

