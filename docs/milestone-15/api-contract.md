# ORBIT Milestone 15 API Contract Updates

## Human Review Capture

### POST `/api/v1/portfolios/{portfolio_id}/human-reviews`

Request body:

```
{
  "reviewer_name": "Human Reviewer",
  "final_recommendation": "Pilot Only",
  "score": 2.8,
  "identified_risks": ["integration complexity", "adoption friction"],
  "confidence": "Medium",
  "review_notes": "Short expert notes."
}
```

Response:

```
{
  "human_review": {
    "human_review_id": "human-strong-ai-saas-001-...",
    "portfolio_id": "strong-ai-saas-001",
    "reviewer_name": "Human Reviewer",
    "final_recommendation": "Pilot Only",
    "score": 2.8,
    "confidence": "Medium",
    "review_payload": { ... },
    "created_at": "2026-04-13T..."
  }
}
```

### GET `/api/v1/portfolios/{portfolio_id}/human-reviews`

Returns a list of human reviews for the portfolio.

### GET `/api/v1/human-reviews/{human_review_id}`

Returns a single human review record.

## Decision Validation

### GET `/api/v1/validation/portfolio/{portfolio_id}`

Returns:

- portfolio metadata
- latest review run id
- human reviews
- decision validations for the latest run
- reasoning consistency metrics

### GET `/api/v1/validation/review-runs/{run_id}`

Returns:

- ORBIT recommendation and score for the run
- human reviews for the portfolio
- validation metrics per human review
- reasoning consistency metrics

### GET `/api/v1/validation/summary`

Returns aggregated decision quality metrics:

```
{
  "summary": {
    "total_validations": 4,
    "recommendation_alignment_rate": 0.5,
    "average_agreement_score": 0.71,
    "average_score_difference": 0.62,
    "average_risk_overlap": 0.44,
    "average_risk_recall": 0.52,
    "average_risk_precision": 0.39,
    "average_confidence_alignment": 0.68
  },
  "updated_at": "2026-04-13T..."
}
```

## Validation Metrics

Decision validation metrics include:

- `recommendation_match`: match | partial | mismatch
- `score_difference`: absolute score delta
- `risk_overlap`: Jaccard overlap of human vs ORBIT risks
- `risk_recall`: overlap / human risks
- `risk_precision`: overlap / ORBIT risks
- `confidence_alignment`: normalized alignment between human and committee confidence
- `agreement_score`: weighted composite (0.5 recommendation match, 0.3 score alignment, 0.2 risk overlap)
