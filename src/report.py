from __future__ import annotations

from html import escape
from pathlib import Path

from .analysis import Finding, metrics
from .briefs import build_store_briefs


def write_report(findings: list[Finding], output_path: Path, briefs: dict[str, str] | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(findings, briefs), encoding="utf-8")


def render_report(findings: list[Finding], briefs: dict[str, str] | None = None) -> str:
    summary = metrics(findings)
    if briefs is None:
        briefs = build_store_briefs(findings)
    rows = "\n".join(_row(finding) for finding in findings)
    brief_cards = "\n".join(
        f'<article class="brief"><h3>{escape(store)}</h3><p>{escape(brief)}</p></article>'
        for store, brief in briefs.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Surplus Review Assistant</title>
  <style>
    :root {{
      --ink: #172217;
      --muted: #5e685c;
      --paper: #fbf8f1;
      --surface: #ffffff;
      --green: #126847;
      --lime: #dde9bf;
      --high: #b53a22;
      --review: #ad6812;
      --low: #267159;
      --border: #e8e1d2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    header {{
      background: var(--green);
      color: white;
      padding: 40px max(24px, calc((100% - 1120px) / 2));
    }}
    header .tag {{
      color: var(--lime);
      font-size: 12px;
      font-weight: bold;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    h1 {{ font-size: clamp(32px, 5vw, 48px); margin: 10px 0 12px; }}
    header p {{ color: #e6ebdf; line-height: 1.5; max-width: 720px; margin: 0; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 26px 24px 52px; }}
    .notice {{
      background: var(--lime);
      border-radius: 12px;
      color: #304424;
      margin-bottom: 22px;
      padding: 14px 18px;
      font-size: 14px;
    }}
    .metrics {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(4, minmax(140px, 1fr));
      margin-bottom: 28px;
    }}
    .metric, .panel, .brief {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 15px;
    }}
    .metric {{ padding: 17px; }}
    .metric span {{ color: var(--muted); display: block; font-size: 13px; margin-bottom: 8px; }}
    .metric strong {{ font-size: 31px; }}
    h2 {{ font-size: 20px; margin: 0 0 15px; }}
    .panel {{ margin-bottom: 26px; overflow: hidden; padding: 20px; }}
    table {{ border-collapse: collapse; font-size: 14px; width: 100%; }}
    th {{
      border-bottom: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
      padding: 10px 8px;
      text-align: left;
      text-transform: uppercase;
    }}
    td {{ border-bottom: 1px solid #f1ecdf; padding: 12px 8px; }}
    tr:last-child td {{ border-bottom: none; }}
    .badge {{
      border-radius: 30px;
      display: inline-block;
      font-size: 12px;
      font-weight: bold;
      padding: 5px 10px;
      text-transform: uppercase;
    }}
    .badge.high {{ background: #fae4df; color: var(--high); }}
    .badge.review {{ background: #faedd8; color: var(--review); }}
    .badge.low {{ background: #dff0e9; color: var(--low); }}
    .briefs {{ display: grid; gap: 14px; grid-template-columns: repeat(3, 1fr); }}
    .brief {{ padding: 19px; }}
    .brief h3 {{ color: var(--green); font-size: 17px; margin: 0 0 10px; }}
    .brief p {{ color: #364136; font-size: 14px; line-height: 1.55; margin: 0; }}
    footer {{ color: var(--muted); font-size: 13px; line-height: 1.5; margin-top: 28px; }}
    @media (max-width: 840px) {{
      .metrics, .briefs {{ grid-template-columns: repeat(2, 1fr); }}
      .panel {{ overflow-x: auto; }}
    }}
    @media (max-width: 520px) {{
      .metrics, .briefs {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="tag">Illustrative prototype</div>
    <h1>Surplus Review Assistant</h1>
    <p>A transparent 17:00 review screen for store managers. It identifies unusually high possible surplus against historical remaining demand, then explains what to check before any action.</p>
  </header>
  <main>
    <div class="notice"><strong>Synthetic data only.</strong> No operational data, automatic preparation decision or automatic surplus listing is used in this demonstration.</div>
    <section class="metrics" aria-label="summary metrics">
      <div class="metric"><span>Stores checked</span><strong>{summary["stores_checked"]}</strong></div>
      <div class="metric"><span>Items checked</span><strong>{summary["items_checked"]}</strong></div>
      <div class="metric"><span>High-risk flags</span><strong>{summary["high_risk_items"]}</strong></div>
      <div class="metric"><span>Flagged portions</span><strong>{summary["projected_flagged_units"]}</strong></div>
    </section>
    <section class="panel">
      <h2>Flag review</h2>
      <table>
        <thead>
          <tr><th>Store</th><th>Item</th><th>Remaining now</th><th>Expected evening sales</th><th>Projected surplus</th><th>Status</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Manager briefs</h2>
      <div class="briefs">{brief_cards}</div>
    </section>
    <footer>
      Method: projected surplus equals portions remaining at 17:00 minus average units sold after 17:00 in synthetic prior shifts, floored at zero. High-risk flags require at least 8 projected portions and at least 25 percent of portions remaining. Operational action stays with store staff.
    </footer>
  </main>
</body>
</html>
"""


def _row(finding: Finding) -> str:
    return (
        "<tr>"
        f"<td>{escape(finding.store)}</td>"
        f"<td>{escape(finding.item)}</td>"
        f"<td>{finding.portions_remaining}</td>"
        f"<td>{finding.expected_remaining_sales:.1f}</td>"
        f"<td>{finding.projected_surplus:.1f}</td>"
        f'<td><span class="badge {finding.status}">{finding.status}</span></td>'
        "</tr>"
    )
