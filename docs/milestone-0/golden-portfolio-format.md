# ORBIT Golden Portfolio Format

## 1. Canonical Portfolio Sections

Every portfolio must normalize into these sections:

1. Problem Discovery
2. Product Vision
3. Competitive Landscape
4. Business Requirements
5. Product Requirements
6. Architecture and System Design
7. AI Agents and Ethical Framework
8. Operational Resilience
9. MVP Roadmap
10. Success Metrics
11. Post Launch Strategy

## 2. Canonical Fixture Shape

Milestone 0 uses YAML fixtures with this top-level structure:

```yaml
portfolio_id: string
portfolio_name: string
portfolio_type: startup | product | innovation
owner: string
submitted_at: YYYY-MM-DD
source_documents:
  - id: string
    kind: brd | prd | architecture | memo
    title: string
evaluation_expectations:
  target_recommendation_band:
    - string
    - string
  expected_strengths:
    - string
  expected_risks:
    - string
problem_discovery:
  summary: string
  key_points: []
product_vision:
  summary: string
  key_points: []
competitive_landscape:
  summary: string
  key_points: []
business_requirements:
  summary: string
  key_points: []
product_requirements:
  summary: string
  key_points: []
architecture_system_design:
  summary: string
  key_points: []
ai_agents_ethical_framework:
  summary: string
  key_points: []
operational_resilience:
  summary: string
  key_points: []
mvp_roadmap:
  summary: string
  key_points: []
success_metrics:
  summary: string
  key_points: []
post_launch_strategy:
  summary: string
  key_points: []
```

## 3. Fixture Design Rules

- each section must contain enough detail for specialists to reason independently
- missing evidence should be represented explicitly, not silently omitted
- evaluation expectations must not leak into the actual review prompts
- fixtures should reflect realistic ambiguity rather than perfect documentation

## 4. Starter Fixture Inventory

- `tests/fixtures/portfolios/strong-ai-saas.yaml`
- `tests/fixtures/portfolios/promising-devtool-gaps.yaml`
- `tests/fixtures/portfolios/weak-startup-idea.yaml`

## 5. Future Expansion

Later milestones may add:

- raw source documents paired with canonical outputs
- expected structured review outputs per agent
- expected conflict clusters
- score stability baselines by model family
