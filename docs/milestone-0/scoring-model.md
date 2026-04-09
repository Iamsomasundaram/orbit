# ORBIT Scoring Model

## 1. Scoring Dimensions

Every portfolio receives scores across these eight dimensions:

- Problem Validity
- Market Fit
- Product Quality
- Technical Feasibility
- AI Reliability
- Economic Viability
- Operational Resilience
- Security & Compliance

## 2. Score Entry Contract

```json
{
  "dimension": "Technical Feasibility",
  "score": 3.6,
  "confidence": 0.74,
  "evidence_completeness": 0.81,
  "severity_flags": ["major_architecture_gap"],
  "rationale": "Core design is sound but resilience is underspecified",
  "evidence_refs": ["portfolio.architecture_system_design", "agent_review.system_architect.finding-001"]
}
```

## 3. Scale Definition

Use a 0 to 5 scale.

- 0.0 -> no credible basis for judgment or clearly invalid
- 1.0 -> critically deficient
- 2.0 -> materially weak
- 3.0 -> conditionally viable with notable gaps
- 4.0 -> strong with manageable concerns
- 5.0 -> exceptional and unusually well-supported

Intermediate decimals are allowed.

## 4. Dimension Weights

| Dimension | Weight |
| --- | --- |
| Problem Validity | 10 |
| Market Fit | 15 |
| Product Quality | 10 |
| Technical Feasibility | 15 |
| AI Reliability | 15 |
| Economic Viability | 10 |
| Operational Resilience | 10 |
| Security & Compliance | 15 |

Total weight = 100.

## 5. Aggregation Logic

1. Aggregate specialist dimension scores into committee-level dimension scores.
2. Weight dimensions according to the table above.
3. Apply confidence and evidence completeness as governance signals, not hidden modifiers.
4. Allow rule-based recommendation overrides for critical legal, compliance, security, or AI safety failures.
5. Treat override conditions as higher precedence than the aggregate weighted score. A portfolio with a strong weighted average can still receive `High Risk` or `Do Not Proceed` if a critical blocker remains unresolved.

Recommended reporting outputs:

- weighted composite score
- per-dimension score table
- average confidence
- average evidence completeness
- active severity flags

## 6. Recommendation Tiers

### Strong Proceed

- composite score >= 4.2
- no unresolved critical findings
- average confidence >= 0.70
- average evidence completeness >= 0.80

### Proceed with Conditions

- composite score between 3.5 and 4.19
- no unmitigated critical blockers
- clear remediation conditions can be stated

### Pilot Only

- composite score between 2.8 and 3.49, or
- evidence completeness is too limited for broad rollout, but a constrained pilot is reasonable

### High Risk

- composite score between 2.0 and 2.79, or
- multiple major risks remain unresolved across domains

### Do Not Proceed

- composite score < 2.0, or
- any critical legal, security, compliance, or AI safety blocker without credible mitigation

## 7. Severity Flags

Severity flags communicate why a score may need special handling. Planned levels:

- critical
- major
- moderate
- minor
- informational

Critical legal, compliance, security, or AI safety flags can override an otherwise acceptable weighted score and force a lower recommendation tier.

## 8. Confidence and Evidence Completeness

Confidence measures how strongly the committee believes its judgment is correct. Evidence completeness measures how much relevant material was actually provided.

High confidence with low evidence completeness is not acceptable for governance-sensitive decisions. The final report must display both values explicitly.

## 9. Scoring Governance Rules

- scores must be explainable through linked findings and evidence
- no dimension score should exist without rationale text and evidence references
- recommendation tiers must be reproducible from the same structured inputs
- any human override later must be recorded with an audit reason
