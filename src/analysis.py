from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


HIGH_MIN_UNITS = 8
HIGH_MIN_SHARE = 0.25
REVIEW_MIN_UNITS = 4


@dataclass(frozen=True)
class Finding:
    store: str
    item: str
    prepared_units: int
    sold_units_by_17_00: int
    portions_remaining: int
    expected_remaining_sales: float
    projected_surplus: float
    surplus_share: float
    status: str


def load_historical(path: Path) -> dict[tuple[str, str], list[int]]:
    history: dict[tuple[str, str], list[int]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["store"], row["item"])
            history.setdefault(key, []).append(int(row["sold_after_17_00"]))
    return history


def analyse_shift(historical_path: Path, current_path: Path) -> list[Finding]:
    history = load_historical(historical_path)
    findings: list[Finding] = []
    with current_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["store"], row["item"])
            if key not in history:
                raise ValueError(f"No historical baseline for {key[0]} / {key[1]}")
            prepared = int(row["prepared_units"])
            sold = int(row["sold_units_by_17_00"])
            if sold > prepared:
                raise ValueError(f"Sold units exceed prepared units for {key[0]} / {key[1]}")
            remaining = prepared - sold
            expected_sales = mean(history[key])
            surplus = max(remaining - expected_sales, 0.0)
            share = surplus / remaining if remaining else 0.0
            findings.append(
                Finding(
                    store=key[0],
                    item=key[1],
                    prepared_units=prepared,
                    sold_units_by_17_00=sold,
                    portions_remaining=remaining,
                    expected_remaining_sales=expected_sales,
                    projected_surplus=surplus,
                    surplus_share=share,
                    status=_classify(surplus, share),
                )
            )
    return sorted(findings, key=lambda item: (_status_order(item.status), -item.projected_surplus, item.store))


def metrics(findings: list[Finding]) -> dict[str, int]:
    flagged = [finding for finding in findings if finding.status == "high"]
    return {
        "stores_checked": len({finding.store for finding in findings}),
        "items_checked": len(findings),
        "high_risk_items": len(flagged),
        "projected_flagged_units": round(sum(item.projected_surplus for item in flagged)),
    }


def _classify(projected_surplus: float, surplus_share: float) -> str:
    if projected_surplus >= HIGH_MIN_UNITS and surplus_share >= HIGH_MIN_SHARE:
        return "high"
    if projected_surplus >= REVIEW_MIN_UNITS:
        return "review"
    return "low"


def _status_order(status: str) -> int:
    return {"high": 0, "review": 1, "low": 2}[status]

