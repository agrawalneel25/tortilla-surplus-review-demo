from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis import analyse_shift, metrics
from src.briefs import build_store_briefs
from src.claude import _validate_briefs, generate_briefs
from src.export import build_review_payload
from src.report import render_report


ROOT = Path(__file__).resolve().parents[1]


class SurplusReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.findings = analyse_shift(
            ROOT / "data" / "historical_remaining_sales.csv",
            ROOT / "data" / "current_shift.csv",
        )

    def test_conservative_high_risk_findings_are_flagged(self) -> None:
        high = {(item.store, item.item) for item in self.findings if item.status == "high"}
        self.assertEqual(high, {("Demo Store A", "Chicken"), ("Demo Store A", "Guacamole")})
        chicken = next(item for item in self.findings if item.item == "Chicken" and item.store == "Demo Store A")
        self.assertAlmostEqual(chicken.mean_surplus_estimate, 14.2)
        self.assertEqual(chicken.highest_observed_remaining_sales, 17)
        self.assertEqual(chicken.conservative_surplus_floor, 13)

    def test_metrics_distinguish_mean_estimate_from_conservative_floor(self) -> None:
        summary = metrics(self.findings)
        self.assertEqual(summary["stores_checked"], 3)
        self.assertEqual(summary["items_checked"], 9)
        self.assertEqual(summary["high_risk_items"], 2)
        self.assertEqual(summary["review_items"], 1)
        self.assertEqual(summary["conservative_flagged_units"], 21)
        self.assertEqual(summary["mean_flagged_units"], 23)

    def test_brief_explains_baseline_and_retains_manager_guardrail(self) -> None:
        briefs = build_store_briefs(self.findings)
        self.assertIn("manager decision", briefs["Demo Store A"])
        self.assertIn("chicken and guacamole", briefs["Demo Store A"])
        self.assertIn("highest demand across 5 recent comparison evenings", briefs["Demo Store A"])

    def test_html_report_exposes_evidence_and_structured_export(self) -> None:
        html = render_report(self.findings)
        self.assertIn("all inputs are synthetic", html)
        self.assertIn("Conservative portions to review", html)
        self.assertIn("Download structured review JSON", html)
        self.assertIn('data-status="high"', html)
        self.assertIn('href="review.json"', html)

    def test_json_handoff_has_decision_boundary_and_findings(self) -> None:
        payload = build_review_payload(self.findings, build_store_briefs(self.findings))
        self.assertEqual(payload["metadata"]["data_mode"], "synthetic")
        self.assertEqual(payload["metadata"]["decision_owner"], "store_manager")
        self.assertEqual(payload["summary"]["conservative_flagged_units"], 21)
        self.assertEqual(payload["findings"][0]["status"], "high")

    def test_missing_history_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "current.csv"
            current_path.write_text(
                "store,item,prepared_units,sold_units_by_17_00\nUnknown,Chicken,10,2\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                analyse_shift(ROOT / "data" / "historical_remaining_sales.csv", current_path)

    def test_duplicate_current_snapshot_item_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "current.csv"
            current_path.write_text(
                "store,item,prepared_units,sold_units_by_17_00\n"
                "Demo Store A,Chicken,84,54\n"
                "Demo Store A,Chicken,84,54\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate current snapshot"):
                analyse_shift(ROOT / "data" / "historical_remaining_sales.csv", current_path)

    @patch.dict("os.environ", {}, clear=True)
    def test_claude_option_requires_an_api_key(self) -> None:
        with self.assertRaises(RuntimeError):
            generate_briefs(self.findings, "claude-sonnet-4-6")

    def test_claude_narrative_must_retain_decision_guardrails(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "decision guardrails"):
            _validate_briefs({"Demo Store A": "List 12 portions immediately."}, ["Demo Store A"])


if __name__ == "__main__":
    unittest.main()
