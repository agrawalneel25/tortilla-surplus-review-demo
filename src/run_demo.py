from __future__ import annotations

import argparse
import os
from pathlib import Path

from .analysis import analyse_shift, metrics
from .briefs import build_store_briefs
from .export import write_review_export
from .report import write_report


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the synthetic surplus review dashboard.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "index.html",
        help="HTML report output path.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "docs" / "review.json",
        help="Structured review export output path.",
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Use the Claude API to rewrite manager briefs from structured findings.",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model ID to use with --claude.",
    )
    args = parser.parse_args()

    findings = analyse_shift(
        ROOT / "data" / "historical_remaining_sales.csv",
        ROOT / "data" / "current_shift.csv",
    )
    briefs = build_store_briefs(findings)
    brief_mode = "deterministic"
    if args.claude:
        from .claude import generate_briefs

        briefs = generate_briefs(findings, args.model)
        brief_mode = "claude"
    json_href = Path(os.path.relpath(args.json_output, start=args.output.parent)).as_posix()
    write_review_export(findings, briefs, args.json_output, brief_mode)
    write_report(findings, args.output, briefs, json_href)
    summary = metrics(findings)
    print("Tortilla Close-Out Review Copilot: synthetic 17:00 snapshot")
    print(f"Stores checked: {summary['stores_checked']}")
    print(f"Items checked: {summary['items_checked']}")
    print(f"High-priority flags: {summary['high_risk_items']}")
    print(f"Monitor flags: {summary['review_items']}")
    print(f"Conservative portions in high-risk flags: {summary['conservative_flagged_units']}")
    print(f"Mean-estimate portions in high-risk flags: {summary['mean_flagged_units']}")
    print("")
    for brief in briefs.values():
        print(brief)
    print("")
    print(f"Dashboard written to {args.output}")
    print(f"Structured review written to {args.json_output}")


if __name__ == "__main__":
    main()
