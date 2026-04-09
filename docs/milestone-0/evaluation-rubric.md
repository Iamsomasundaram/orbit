# ORBIT Evaluation Rubric

## 1. Evaluation Goals

ORBIT evaluation must measure both decision quality and decision stability.

The rubric should answer:

- are findings evidence-backed and actionable
- are scores consistent across repeated runs
- does the final recommendation stay within an acceptable band
- do specialist agents identify the expected major risks and strengths
- can results be replayed and audited later

## 2. Golden Portfolio Dataset Requirements

Every golden portfolio fixture must include:

- canonical portfolio metadata
- all eleven ORBIT portfolio sections
- expected recommendation band
- expected score band
- expected high-signal strengths
- expected top 3 to 5 risks or gaps
- expected top 1 to 3 conflict clusters
- optional notes on where evidence is intentionally incomplete

Starter set required from Milestone 0:

- one strong AI SaaS portfolio
- one promising devtool with gaps
- one weak startup idea

## 3. Expected Finding Structure

Review outputs are considered valid only if findings contain:

- stable finding identifier
- short title
- category
- severity
- explicit claim
- evidence references
- recommended action
- score impact references when applicable

High-quality findings should also include:

- assumptions used to reach the claim
- evidence gaps that reduce confidence
- open questions for unresolved uncertainty

## 4. Quality Rubric

### Evidence Traceability

- 5: every material finding is grounded in precise evidence references
- 3: most findings cite evidence, but some rely on loose summaries
- 1: findings are largely unsupported or generic

### Issue Specificity

- 5: findings identify concrete failure modes or strengths
- 3: findings are directionally useful but somewhat generic
- 1: findings are vague, repetitive, or boilerplate

### Actionability

- 5: mitigations are clear, bounded, and relevant
- 3: mitigations exist but are broad or underspecified
- 1: mitigations are missing or not useful

### Governance Clarity

- 5: severity, confidence, and evidence completeness are explicit
- 3: some governance signals are present but incomplete
- 1: recommendation exists without adequate rationale signals

## 5. Stability Criteria

Once the evaluation harness exists, each golden portfolio should be replayed at least 5 times per major model or prompt change.

Target stability thresholds:

- recommendation tier remains identical in at least 4 of 5 runs
- mean absolute deviation per dimension <= 0.35 on the 0 to 5 scale
- average confidence deviation <= 0.15
- average evidence completeness deviation <= 0.15
- all expected critical or major risks are surfaced in at least 4 of 5 runs

## 6. Starter Portfolio Expectations

### Strong AI SaaS

Expected recommendation band:

- Proceed with Conditions to Strong Proceed

Expected score band:

- 3.5 to 4.2

Expected strengths:

- clear problem and buyer
- coherent architecture and operating model
- credible metrics and roadmap

Expected caution areas:

- integration complexity
- data governance depth
- enterprise readiness evidence is still thinner than the commercial case

Expected top conflicts:

- recommendation conflict between growth-oriented and risk-oriented reviewers around rollout timing`n- assumption mismatch on what single-region MVP readiness really means`n- risk severity mismatch on security and operational readiness

### Promising Devtool with Gaps

Expected recommendation band:

- Pilot Only to Proceed with Conditions

Expected score band:

- 2.8 to 3.7

Expected strengths:

- strong developer value proposition
- plausible technical feasibility

Expected caution areas:

- unclear monetization
- weak compliance posture
- incomplete evaluation and support model
- high-volume telemetry cost assumptions are incomplete

Expected top conflicts:

- score divergence on Market Fit between product and commercial reviewers
- evidence completeness mismatch on AI Reliability due missing evaluation benchmarks
- recommendation conflict on whether enterprise pilots are premature

### Weak Startup Idea

Expected recommendation band:

- High Risk to Do Not Proceed

Expected score band:

- 0.8 to 2.4

Expected weaknesses:

- poor problem validation
- weak differentiation
- unsupported business assumptions
- unclear or speculative delivery path
- no credible safety or moderation model

Expected top conflicts:

- risk severity mismatch between product novelty optimism and security or legal concerns
- recommendation conflict on whether a prototype is still worth piloting
- assumption mismatch on whether user demand exists at all

## 7. Regression Triggers

The future evaluation harness should fail or flag a regression when:

- recommendation band falls outside the expected range
- critical findings disappear from the weak portfolio without evidence changes
- dimension scores drift beyond stability thresholds
- evidence traceability falls below the acceptable threshold
- structured output contracts are not satisfied

## 8. Human Review Requirement

Evaluation is not only automated. Milestone gates require a human review of:

- recommendation plausibility
- finding quality
- residual blind spots in the rubric
- false confidence caused by incomplete evidence

