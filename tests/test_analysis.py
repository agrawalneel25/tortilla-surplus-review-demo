from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis import analyse_shift, metrics
from src.briefs import build_store_briefs
from src.claude import generate_briefs
from src.report import render_report


ROOT = Path(__file__).resolve().parents[1]


class SurplusReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.findings = analyse_shift(
            ROOT / "data" / "historical_remaining_sales.csv",
            ROOT / "data" / "current_shift.csv",
        )

    def test_expected_high_risk_findings_are_flagged(self) -> None:
        high = {(item.store, item.item) for item in self.findings if item.status == "high"}
        self.assertEqual(high, {("Demo Store A", "Chicken"), ("Demo Store A", "Guacamole")})

    def test_metrics_only_sum_high_risk_items(self) -> None:
        summary = metrics(self.findings)
        self.assertEqual(summary["stores_checked"], 3)
        self.assertEqual(summary["items_checked"], 9)
        self.assertEqual(summary["high_risk_items"], 2)
        self.assertEqual(summary["projected_flagged_units"], 23)

    def test_brief_includes_guardrail(self) -> None:
        briefs = build_store_briefs(self.findings)
        self.assertIn("manager decision", briefs["Demo Store A"])
        self.assertIn("chicken and guacamole", briefs["Demo Store A"])

    def test_html_report_states_synthetic_data(self) -> None:
        html = render_report(self.findings)
        self.assertIn("Synthetic data only", html)
        self.assertIn("High-risk flags", html)
        self.assertIn("Demo Store A", html)

    def test_missing_history_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "current.csv"
            current_path.write_text(
                "store,item,prepared_units,sold_units_by_17_00\nUnknown,Chicken,10,2\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                analyse_shift(ROOT / "data" / "historical_remaining_sales.csv", current_path)

    @patch.dict("os.environ", {}, clear=True)
    def test_claude_option_requires_an_api_key(self) -> None:
        with self.assertRaises(RuntimeError):
            generate_briefs(self.findings, "claude-sonnet-4-20250514")


if __name__ == "__main__":
    unittest.main()
