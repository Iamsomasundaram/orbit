from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .conflicts import detect_conflicts
from .ingestion import ingest_portfolio_document
from .reporting import build_committee_report
from .reviewer import run_specialist_reviews
from .scorecard import build_committee_scorecard


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def write_json(file_path: Path, value: Any) -> None:
    file_path.write_text(f"{json.dumps(to_jsonable(value), indent=2)}\n", encoding="utf-8")


def run_review_pipeline(input_path: str, output_dir: str | None = None) -> dict[str, Any]:
    canonical_portfolio = ingest_portfolio_document(input_path)
    run_id = f"thin-slice-{canonical_portfolio.portfolio_id}"
    agent_reviews = run_specialist_reviews(canonical_portfolio)
    conflicts = detect_conflicts(agent_reviews)
    scorecard = build_committee_scorecard(canonical_portfolio, run_id, agent_reviews, conflicts)
    committee_report = build_committee_report(canonical_portfolio, run_id, agent_reviews, conflicts, scorecard)

    if output_dir:
        resolved_output_dir = Path(output_dir).resolve()
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        write_json(resolved_output_dir / "canonical-portfolio.json", canonical_portfolio)
        write_json(resolved_output_dir / "agent-reviews.json", agent_reviews)
        write_json(resolved_output_dir / "conflicts.json", conflicts)
        write_json(resolved_output_dir / "scorecard.json", scorecard)
        write_json(resolved_output_dir / "committee-report.json", committee_report)
        (resolved_output_dir / "committee-report.md").write_text(committee_report.markdown, encoding="utf-8")

    return {
        "run_id": run_id,
        "canonical_portfolio": canonical_portfolio,
        "agent_reviews": agent_reviews,
        "conflicts": conflicts,
        "scorecard": scorecard,
        "committee_report": committee_report,
    }
