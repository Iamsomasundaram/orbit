from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .committee_engine import CommitteeRuntimeOptions
from .config import get_settings
from .runner import run_review_pipeline


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m orbit_worker.cli",
        usage="python -m orbit_worker.cli <markdown-file> [--output-dir <dir>]",
        add_help=True,
    )
    parser.add_argument("input_path")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--runtime-mode", choices=["deterministic", "llm"], default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    runtime_options = CommitteeRuntimeOptions.from_settings(get_settings())
    if args.runtime_mode:
        runtime_options = CommitteeRuntimeOptions(
            **{
                **runtime_options.model_dump(mode="python"),
                "runtime_mode": args.runtime_mode,
            }
        )
    result = run_review_pipeline(
        args.input_path,
        args.output_dir or None,
        runtime_options=runtime_options,
    )
    print(f"Run ID: {result['run_id']}")
    print(f"Portfolio: {result['canonical_portfolio'].portfolio_name}")
    print(f"Agents executed: {len(result['agent_reviews'])}")
    print(f"Conflicts detected: {len(result['conflicts'])}")
    print(f"Final recommendation: {result['scorecard'].final_recommendation}")
    print(f"Weighted composite score: {result['scorecard'].weighted_composite_score:.2f}")
    if args.output_dir:
        print(f"Artifacts written to: {Path(args.output_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
