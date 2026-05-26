from __future__ import annotations

from collections import defaultdict

from .analysis import Finding


def build_store_briefs(findings: list[Finding]) -> dict[str, str]:
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.store].append(finding)
    return {store: _brief_for_store(store, items) for store, items in sorted(grouped.items())}


def _brief_for_store(store: str, findings: list[Finding]) -> str:
    high = [finding for finding in findings if finding.status == "high"]
    review = [finding for finding in findings if finding.status == "review"]
    if high:
        lines = [
            f"{store}: review possible surplus for {_join_items(high)} before close.",
            _supporting_figures(high),
        ]
    elif review:
        lines = [
            f"{store}: no high-risk flag, but monitor {_join_items(review)}.",
            _supporting_figures(review),
        ]
    else:
        lines = [f"{store}: no material surplus flag at the 17:00 checkpoint."]
    lines.append(
        "Before acting, check live orders, in-store demand and food-safety constraints. "
        "Any surplus listing remains a manager decision."
    )
    return " ".join(lines)


def _join_items(findings: list[Finding]) -> str:
    names = [finding.item.lower() for finding in findings]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _supporting_figures(findings: list[Finding]) -> str:
    figures = []
    for finding in findings:
        figures.append(
            f"{finding.item}: {finding.portions_remaining} portions remain, "
            f"highest demand across {finding.baseline_shift_count} recent comparison evenings is "
            f"{finding.highest_observed_remaining_sales}, "
            f"leaving a conservative surplus floor of {finding.conservative_surplus_floor:.1f}"
        )
    return "; ".join(figures) + "."

