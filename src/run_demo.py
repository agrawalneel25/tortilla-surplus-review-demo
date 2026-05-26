from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import analyse_shift, metrics
from .briefs import build_store_briefs
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
        "--claude",
        action="store_true",
        help="Use the Claude API to rewrite manager briefs from structured findings.",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model ID to use with --claude.",
    )
    args = parser.parse_args()

    findings = analyse_shift(
        ROOT / "data" / "historical_remaining_sales.csv",
        ROOT / "data" / "current_shift.csv",
    )
    briefs = build_store_briefs(findings)
    if args.claude:
        from .claude import generate_briefs

        briefs = generate_briefs(findings, args.model)
    write_report(findings, args.output, briefs)
    summary = metrics(findings)
    print("Surplus Review Assistant: synthetic 17:00 snapshot")
    print(f"Stores checked: {summary['stores_checked']}")
    print(f"Items checked: {summary['items_checked']}")
    print(f"High-risk flags: {summary['high_risk_items']}")
    print(f"Projected portions in high-risk flags: {summary['projected_flagged_units']}")
    print("")
    for brief in briefs.values():
        print(brief)
    print("")
    print(f"Dashboard written to {args.output}")


if __name__ == "__main__":
    main()
