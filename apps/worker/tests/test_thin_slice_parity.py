from __future__ import annotations

import json
from pathlib import Path

from orbit_worker.runner import run_review_pipeline


ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"
BASELINE_DIR = ROOT / "tests" / "fixtures" / "baselines" / "procurepilot-js"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_python_thin_slice_matches_js_baseline(tmp_path: Path) -> None:
    result = run_review_pipeline(str(INPUT_PATH), str(tmp_path))

    assert len(result["agent_reviews"]) == 15
    assert len(result["conflicts"]) >= 1
    assert result["scorecard"].final_recommendation == "Proceed with Conditions"
    assert result["scorecard"].weighted_composite_score == 3.61

    assert read_json(tmp_path / "canonical-portfolio.json") == read_json(BASELINE_DIR / "canonical-portfolio.json")
    assert read_json(tmp_path / "agent-reviews.json") == read_json(BASELINE_DIR / "agent-reviews.json")
    assert read_json(tmp_path / "conflicts.json") == read_json(BASELINE_DIR / "conflicts.json")
    assert read_json(tmp_path / "scorecard.json") == read_json(BASELINE_DIR / "scorecard.json")
    assert read_json(tmp_path / "committee-report.json") == read_json(BASELINE_DIR / "committee-report.json")
    assert (tmp_path / "committee-report.md").read_text(encoding="utf-8") == (BASELINE_DIR / "committee-report.md").read_text(encoding="utf-8")
