from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .analysis import Finding, HIGH_MIN_SHARE, HIGH_MIN_UNITS, REVIEW_MIN_UNITS, metrics


def build_review_payload(
    findings: list[Finding],
    briefs: dict[str, str],
    brief_mode: str = "deterministic",
) -> dict[str, object]:
    return {
        "metadata": {
            "prototype": "Tortilla Close-Out Review Copilot",
            "checkpoint": "17:00",
            "data_mode": "synthetic",
            "brief_mode": brief_mode,
            "decision_owner": "store_manager",
        },
        "method": {
            "baseline": "highest observed units sold after 17:00 across recent comparison shifts",
            "conservative_surplus_floor": "max(portions_remaining - highest_observed_remaining_sales, 0)",
            "high_rule": {
                "minimum_portions": HIGH_MIN_UNITS,
                "minimum_share_of_remaining": HIGH_MIN_SHARE,
            },
            "review_minimum_portions": REVIEW_MIN_UNITS,
        },
        "summary": metrics(findings),
        "findings": [_serialise_finding(finding) for finding in findings],
        "manager_briefs": briefs,
    }


def write_review_export(
    findings: list[Finding],
    briefs: dict[str, str],
    output_path: Path,
    brief_mode: str = "deterministic",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_review_payload(findings, briefs, brief_mode)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _serialise_finding(finding: Finding) -> dict[str, object]:
    result = asdict(finding)
    for field in (
        "expected_remaining_sales",
        "mean_surplus_estimate",
        "conservative_surplus_floor",
        "surplus_floor_share",
    ):
        result[field] = round(float(result[field]), 3)
    return result
