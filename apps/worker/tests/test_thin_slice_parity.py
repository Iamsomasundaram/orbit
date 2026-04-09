from __future__ import annotations

import json
from pathlib import Path

import pytest

from orbit_worker.runner import run_review_pipeline


ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests" / "fixtures" / "parity-cases.json").read_text(encoding="utf-8"))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_python_thin_slice_matches_js_baseline(case: dict[str, str], tmp_path: Path) -> None:
    input_path = ROOT / case["input_path"]
    baseline_dir = ROOT / case["baseline_dir"]
    output_dir = tmp_path / case["case_id"]

    result = run_review_pipeline(str(input_path), str(output_dir))

    assert len(result["agent_reviews"]) == 15
    assert len(result["conflicts"]) >= 1

    assert read_json(output_dir / "canonical-portfolio.json") == read_json(baseline_dir / "canonical-portfolio.json")
    assert read_json(output_dir / "agent-reviews.json") == read_json(baseline_dir / "agent-reviews.json")
    assert read_json(output_dir / "conflicts.json") == read_json(baseline_dir / "conflicts.json")
    assert read_json(output_dir / "scorecard.json") == read_json(baseline_dir / "scorecard.json")
    assert read_json(output_dir / "committee-report.json") == read_json(baseline_dir / "committee-report.json")
    assert (output_dir / "committee-report.md").read_text(encoding="utf-8") == (baseline_dir / "committee-report.md").read_text(encoding="utf-8")
