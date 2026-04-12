from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from orbit_worker.runner import run_review_pipeline


ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests" / "fixtures" / "parity-cases.json").read_text(encoding="utf-8"))
BASELINE_MANIFEST = json.loads(
    (ROOT / "tests" / "fixtures" / "baselines" / "manifest.json").read_text(encoding="utf-8")
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_agent_reviews_for_baseline(agent_reviews: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for review in agent_reviews:
        copy = json.loads(json.dumps(review))
        review_metadata = copy.get("review_metadata") or {}
        for field in ("input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd"):
            review_metadata.pop(field, None)
        normalized.append(copy)
    return normalized


def test_archived_baseline_artifacts_match_manifest() -> None:
    discovered = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
        for path in sorted((ROOT / "tests" / "fixtures" / "baselines").rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }

    assert BASELINE_MANIFEST["version"] == "m8-archived-baseline-manifest-v1"
    assert discovered == BASELINE_MANIFEST["files"]


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_python_thin_slice_matches_js_baseline(case: dict[str, str], tmp_path: Path) -> None:
    input_path = ROOT / case["input_path"]
    baseline_dir = ROOT / case["baseline_dir"]
    output_dir = tmp_path / case["case_id"]

    result = run_review_pipeline(str(input_path), str(output_dir))

    assert len(result["agent_reviews"]) == 15
    assert len(result["conflicts"]) >= 1

    generated_reviews = read_json(output_dir / "agent-reviews.json")
    baseline_reviews = read_json(baseline_dir / "agent-reviews.json")

    for review in generated_reviews:
        review_metadata = review.get("review_metadata") or {}
        assert review_metadata.get("input_tokens", 0) == 0
        assert review_metadata.get("output_tokens", 0) == 0
        assert review_metadata.get("total_tokens", 0) == 0
        assert review_metadata.get("estimated_cost_usd", 0) == 0

    assert read_json(output_dir / "canonical-portfolio.json") == read_json(baseline_dir / "canonical-portfolio.json")
    assert normalize_agent_reviews_for_baseline(generated_reviews) == normalize_agent_reviews_for_baseline(
        baseline_reviews
    )
    assert read_json(output_dir / "conflicts.json") == read_json(baseline_dir / "conflicts.json")
    assert read_json(output_dir / "scorecard.json") == read_json(baseline_dir / "scorecard.json")
    assert read_json(output_dir / "committee-report.json") == read_json(baseline_dir / "committee-report.json")
    assert (output_dir / "committee-report.md").read_text(encoding="utf-8") == (baseline_dir / "committee-report.md").read_text(encoding="utf-8")
