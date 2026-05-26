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
    baseline_shift_count: int
    expected_remaining_sales: float
    highest_observed_remaining_sales: int
    mean_surplus_estimate: float
    conservative_surplus_floor: float
    surplus_floor_share: float
    status: str


def load_historical(path: Path) -> dict[tuple[str, str], list[int]]:
    history: dict[tuple[str, str], list[int]] = {}
    seen_shifts: set[tuple[str, str, str]] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["store"], row["item"])
            shift_key = (row["store"], row["item"], row["date"])
            if shift_key in seen_shifts:
                raise ValueError(f"Duplicate historical shift for {key[0]} / {key[1]} on {row['date']}")
            sold_after_checkpoint = int(row["sold_after_17_00"])
            if sold_after_checkpoint < 0:
                raise ValueError(f"Negative historical sales for {key[0]} / {key[1]}")
            history.setdefault(key, []).append(sold_after_checkpoint)
            seen_shifts.add(shift_key)
    return history


def analyse_shift(historical_path: Path, current_path: Path) -> list[Finding]:
    history = load_historical(historical_path)
    findings: list[Finding] = []
    seen_items: set[tuple[str, str]] = set()
    with current_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["store"], row["item"])
            if key in seen_items:
                raise ValueError(f"Duplicate current snapshot item for {key[0]} / {key[1]}")
            if key not in history:
                raise ValueError(f"No historical baseline for {key[0]} / {key[1]}")
            prepared = int(row["prepared_units"])
            sold = int(row["sold_units_by_17_00"])
            if prepared < 0 or sold < 0:
                raise ValueError(f"Negative current quantity for {key[0]} / {key[1]}")
            if sold > prepared:
                raise ValueError(f"Sold units exceed prepared units for {key[0]} / {key[1]}")

            remaining = prepared - sold
            baseline = history[key]
            expected_sales = mean(baseline)
            highest_observed_sales = max(baseline)
            mean_surplus = max(remaining - expected_sales, 0.0)
            conservative_floor = max(remaining - highest_observed_sales, 0.0)
            floor_share = conservative_floor / remaining if remaining else 0.0
            findings.append(
                Finding(
                    store=key[0],
                    item=key[1],
                    prepared_units=prepared,
                    sold_units_by_17_00=sold,
                    portions_remaining=remaining,
                    baseline_shift_count=len(baseline),
                    expected_remaining_sales=expected_sales,
                    highest_observed_remaining_sales=highest_observed_sales,
                    mean_surplus_estimate=mean_surplus,
                    conservative_surplus_floor=conservative_floor,
                    surplus_floor_share=floor_share,
                    status=_classify(conservative_floor, floor_share),
                )
            )
            seen_items.add(key)
    return sorted(
        findings,
        key=lambda item: (_status_order(item.status), -item.conservative_surplus_floor, item.store, item.item),
    )


def metrics(findings: list[Finding]) -> dict[str, int]:
    flagged = [finding for finding in findings if finding.status == "high"]
    return {
        "stores_checked": len({finding.store for finding in findings}),
        "items_checked": len(findings),
        "high_risk_items": len(flagged),
        "review_items": sum(finding.status == "review" for finding in findings),
        "conservative_flagged_units": round(sum(item.conservative_surplus_floor for item in flagged)),
        "mean_flagged_units": round(sum(item.mean_surplus_estimate for item in flagged)),
    }


def _classify(conservative_surplus_floor: float, surplus_floor_share: float) -> str:
    if conservative_surplus_floor >= HIGH_MIN_UNITS and surplus_floor_share >= HIGH_MIN_SHARE:
        return "high"
    if conservative_surplus_floor >= REVIEW_MIN_UNITS:
        return "review"
    return "low"


def _status_order(status: str) -> int:
    return {"high": 0, "review": 1, "low": 2}[status]
