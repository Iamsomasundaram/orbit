# ORBIT Milestone 11 API Contract

Milestone 11 adds a persisted deliberation surface for completed review runs. The new endpoints read from stored `deliberation_entries`; they do not regenerate reasoning dynamically and they do not call the llm provider.

## New endpoints

### `GET /api/v1/review-runs/{run_id}/deliberation`

Returns the full ordered timeline for a review run.

Example response:

```json
{
  "review_run_id": "review-strong-ai-saas-001-20260411T180031109996Z",
  "portfolio_id": "strong-ai-saas-001",
  "lineage": {
    "portfolio_id": "strong-ai-saas-001",
    "review_run_id": "review-strong-ai-saas-001-20260411T180031109996Z",
    "debate_id": "debate-review-strong-ai-saas-001-20260411T180031109996Z",
    "resynthesis_id": null
  },
  "artifact_selection": {
    "active_artifact_source": "original",
    "has_resynthesized_artifacts": false,
    "score_change_required_count": 0
  },
  "final_recommendation": "Proceed with Conditions",
  "weighted_composite_score": 3.61,
  "entry_count": 53,
  "entries": [
    {
      "deliberation_entry_row_id": "review-strong-ai-saas-001-20260411T180031109996Z:0001",
      "run_id": "review-strong-ai-saas-001-20260411T180031109996Z",
      "portfolio_id": "strong-ai-saas-001",
      "sequence_number": 1,
      "phase": "opening_statements",
      "agent_id": "business_owner",
      "agent_role": "Business Owner",
      "statement_type": "opening_statement",
      "statement_text": "Proceed with Conditions. ...",
      "conflict_reference": null,
      "created_at": "2026-04-11T18:00:31.111996Z"
    }
  ]
}
```

Behavior:

- reads only persisted review, debate, re-synthesis, and deliberation records
- preserves review lineage and active artifact selection
- returns entries in persisted `sequence_number` order

### `GET /api/v1/review-runs/{run_id}/deliberation/summary`

Returns a condensed phase-oriented view of the same persisted timeline.

Example response:

```json
{
  "review_run_id": "review-strong-ai-saas-001-20260411T180031109996Z",
  "portfolio_id": "strong-ai-saas-001",
  "final_recommendation": "Proceed with Conditions",
  "weighted_composite_score": 3.61,
  "active_artifact_source": "original",
  "phase_summaries": [
    {
      "phase": "opening_statements",
      "label": "Opening Statements",
      "entry_count": 15,
      "representative_statement": "Proceed with Conditions. ...",
      "conflict_references": []
    }
  ]
}
```

Behavior:

- groups persisted deliberation entries into the five fixed phases
- summarizes from stored entries only
- does not mutate or recompute committee artifacts

## Materialization lifecycle

Milestone 11 adds automatic deliberation rematerialization when the persisted review state changes:

- `ReviewRunService.start_review`
  - creates the first timeline from review artifacts
- `DebateService.start_debate`
  - rewrites the timeline to include conflict discussion and moderator synthesis
- `ResynthesisService.start_resynthesis`
  - rewrites the final verdict to reflect the active artifact source

This keeps the timeline aligned with the approved lineage path:

portfolio submission  
-> review run  
-> conflict detection  
-> bounded debate  
-> optional re-synthesis  
-> artifact persistence  
-> deliberation retrieval

## Persistence impact

Milestone 11 adds one new durable table:

- `deliberation_entries`

Key constraints:

- primary key: `deliberation_entry_row_id`
- uniqueness: `run_id + sequence_number`
- index: `ix_deliberation_entries_run_id`

Schema change is managed through Alembic revision:

- `20260411_01_m11_deliberation_entries.py`

No existing review, conflict, scorecard, report, debate, or re-synthesis tables were redesigned.
