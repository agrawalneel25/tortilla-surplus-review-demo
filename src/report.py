from __future__ import annotations

from html import escape
from pathlib import Path

from .analysis import Finding, metrics
from .briefs import build_store_briefs


def write_report(
    findings: list[Finding],
    output_path: Path,
    briefs: dict[str, str] | None = None,
    export_href: str = "review.json",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(findings, briefs, export_href), encoding="utf-8")


def render_report(
    findings: list[Finding],
    briefs: dict[str, str] | None = None,
    export_href: str = "review.json",
) -> str:
    summary = metrics(findings)
    if briefs is None:
        briefs = build_store_briefs(findings)
    rows = "\n".join(_row(finding) for finding in findings)
    high_findings = [finding for finding in findings if finding.status == "high"]
    queue_cards = "\n".join(_queue_card(finding) for finding in high_findings)
    brief_cards = "\n".join(
        f'<article class="brief"><h3>{escape(store)}</h3><p>{escape(brief)}</p></article>'
        for store, brief in briefs.items()
    )
    store_options = "\n".join(
        f'<option value="{escape(store)}">{escape(store)}</option>' for store in sorted(briefs)
    )
    safe_export_href = escape(export_href, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tortilla Close-Out Review Copilot</title>
  <style>
    :root {{
      --ink: #132218;
      --muted: #607064;
      --paper: #fbf8f1;
      --surface: #ffffff;
      --green: #104c39;
      --green-2: #166348;
      --lime: #dfe9bc;
      --lime-dark: #4f642e;
      --high: #af351d;
      --review: #97600c;
      --low: #24634d;
      --border: #e7e1d4;
      --shadow: 0 12px 34px rgba(25, 42, 25, 0.06);
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
      padding: 42px max(24px, calc((100% - 1160px) / 2)) 58px;
    }}
    .eyebrow {{
      align-items: center;
      color: var(--lime);
      display: flex;
      font-size: 12px;
      font-weight: bold;
      gap: 10px;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }}
    .dot {{
      background: var(--lime);
      border-radius: 50%;
      display: inline-block;
      height: 9px;
      width: 9px;
    }}
    h1 {{
      font-size: clamp(34px, 5vw, 51px);
      letter-spacing: -0.04em;
      line-height: 1.04;
      margin: 17px 0 14px;
      max-width: 750px;
    }}
    header p {{
      color: #e3ecdf;
      font-size: 16px;
      line-height: 1.55;
      margin: 0 0 27px;
      max-width: 730px;
    }}
    .button {{
      background: var(--lime);
      border-radius: 8px;
      color: #21351d;
      display: inline-block;
      font-size: 14px;
      font-weight: bold;
      padding: 12px 17px;
      text-decoration: none;
    }}
    main {{
      max-width: 1160px;
      margin: -26px auto 0;
      padding: 0 24px 52px;
      position: relative;
    }}
    .notice {{
      background: #f1f4df;
      border: 1px solid #d4dfa9;
      border-radius: 13px;
      color: #344528;
      margin-bottom: 20px;
      padding: 15px 18px;
      font-size: 14px;
      line-height: 1.5;
    }}
    .metrics {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(5, minmax(130px, 1fr));
      margin-bottom: 25px;
    }}
    .metric, .panel, .brief, .queue-card, .boundary-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 15px;
      box-shadow: var(--shadow);
    }}
    .metric {{ padding: 17px 16px; }}
    .metric span {{
      color: var(--muted);
      display: block;
      font-size: 12px;
      line-height: 1.35;
      margin-bottom: 9px;
    }}
    .metric strong {{ font-size: 30px; letter-spacing: -0.03em; }}
    .metric.featured {{ background: var(--green-2); border-color: var(--green-2); color: white; }}
    .metric.featured span {{ color: #e1eddc; }}
    section {{ margin-bottom: 25px; }}
    h2 {{
      font-size: 21px;
      letter-spacing: -0.02em;
      margin: 0 0 14px;
    }}
    .section-intro {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin: -6px 0 17px;
      max-width: 770px;
    }}
    .queue {{
      display: grid;
      gap: 13px;
      grid-template-columns: repeat(2, 1fr);
    }}
    .queue-card {{ border-top: 4px solid var(--high); padding: 18px; }}
    .queue-title {{
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
    }}
    .queue-title h3 {{ font-size: 18px; margin: 0; }}
    .evidence {{
      background: #faf8f3;
      border-radius: 10px;
      color: #344034;
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 12px;
      padding: 12px;
    }}
    .check {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      margin: 0;
    }}
    .panel {{ overflow: hidden; padding: 20px; }}
    .toolbar {{
      align-items: end;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
      margin-bottom: 14px;
    }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 9px; }}
    label {{
      color: var(--muted);
      display: block;
      font-size: 12px;
      font-weight: bold;
      text-transform: uppercase;
    }}
    select {{
      background: white;
      border: 1px solid var(--border);
      border-radius: 7px;
      color: var(--ink);
      display: block;
      margin-top: 6px;
      min-width: 150px;
      padding: 9px 10px;
    }}
    #visibleRows {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ border-collapse: collapse; font-size: 14px; min-width: 790px; width: 100%; }}
    th {{
      border-bottom: 1px solid var(--border);
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      padding: 10px 8px;
      text-align: left;
      text-transform: uppercase;
    }}
    td {{ border-bottom: 1px solid #f0ebdf; padding: 12px 8px; }}
    tr:last-child td {{ border-bottom: none; }}
    .number {{ font-variant-numeric: tabular-nums; }}
    .subtle {{ color: var(--muted); display: block; font-size: 12px; margin-top: 3px; }}
    .badge {{
      border-radius: 30px;
      display: inline-block;
      font-size: 11px;
      font-weight: bold;
      padding: 5px 10px;
      text-transform: uppercase;
    }}
    .badge.high {{ background: #f9e3de; color: var(--high); }}
    .badge.review {{ background: #f7ead4; color: var(--review); }}
    .badge.low {{ background: #dceee6; color: var(--low); }}
    #noResults {{ color: var(--muted); display: none; font-size: 14px; padding: 20px 8px 4px; }}
    .boundary {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(3, 1fr);
    }}
    .boundary-card {{ padding: 17px; }}
    .boundary-card strong {{ color: var(--green-2); display: block; font-size: 14px; margin-bottom: 8px; }}
    .boundary-card p {{ color: var(--muted); font-size: 13px; line-height: 1.5; margin: 0; }}
    .briefs {{ display: grid; gap: 13px; grid-template-columns: repeat(3, 1fr); }}
    .brief {{ padding: 18px; }}
    .brief h3 {{ color: var(--green-2); font-size: 17px; margin: 0 0 9px; }}
    .brief p {{ color: #354135; font-size: 14px; line-height: 1.58; margin: 0; }}
    footer {{
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
      margin-top: 28px;
      padding-top: 20px;
    }}
    @media (max-width: 920px) {{
      .metrics {{ grid-template-columns: repeat(3, 1fr); }}
      .queue, .boundary, .briefs {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
      header {{ padding-top: 30px; }}
      main {{ padding-left: 16px; padding-right: 16px; }}
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
      .metric.featured {{ grid-column: span 2; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow"><span class="dot"></span> Candidate prototype | Synthetic operations data</div>
    <h1>Tortilla Close-Out Review Copilot</h1>
    <p>A transparent 17:00 triage screen for store teams. It highlights ingredients that remain above even the strongest comparable recent evening demand, then presents evidence for a human decision.</p>
    <a class="button" href="{safe_export_href}" download>Download structured review JSON</a>
  </header>
  <main>
    <div class="notice"><strong>Demonstration boundary:</strong> all inputs are synthetic. This screen does not connect to Tortilla systems, change preparation plans or create surplus listings. A store manager remains responsible for any action.</div>
    <section class="metrics" aria-label="summary metrics">
      <div class="metric"><span>Stores scanned</span><strong>{summary["stores_checked"]}</strong></div>
      <div class="metric"><span>Components assessed</span><strong>{summary["items_checked"]}</strong></div>
      <div class="metric"><span>High-priority flags</span><strong>{summary["high_risk_items"]}</strong></div>
      <div class="metric"><span>Monitor flags</span><strong>{summary["review_items"]}</strong></div>
      <div class="metric featured"><span>Conservative portions to review</span><strong>{summary["conservative_flagged_units"]}</strong></div>
    </section>
    <section>
      <h2>Prioritised review queue</h2>
      <p class="section-intro">A high-priority flag appears only when remaining portions still exceed the highest evening demand observed in the comparison shifts by both the volume and share thresholds.</p>
      <div class="queue">{queue_cards}</div>
    </section>
    <section class="panel">
      <div class="toolbar">
        <div>
          <h2>Evidence explorer</h2>
          <div id="visibleRows">{len(findings)} components shown</div>
        </div>
        <div class="filters" aria-label="table filters">
          <label>Status
            <select id="statusFilter">
              <option value="">All statuses</option>
              <option value="high">High priority</option>
              <option value="review">Monitor</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label>Store
            <select id="storeFilter">
              <option value="">All stores</option>
              {store_options}
            </select>
          </label>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Store</th><th>Component</th><th>Remaining at 17:00</th><th>Recent mean demand</th><th>Highest recent demand</th><th>Conservative floor vs baseline</th><th>Status</th></tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <div id="noResults">No components match the selected filters.</div>
    </section>
    <section>
      <h2>AI and integration boundary</h2>
      <div class="boundary">
        <article class="boundary-card"><strong>1. Deterministic screening</strong><p>Python validates the snapshot and calculates every flag from visible comparison data. No model assigns risk.</p></article>
        <article class="boundary-card"><strong>2. Structured handoff</strong><p>The same results are emitted as JSON for a future BI, Qlik Cloud or MCP-connected workflow.</p></article>
        <article class="boundary-card"><strong>3. Optional Claude brief</strong><p>An LLM may rewrite manager-facing narrative only after classification, with required human-decision guardrails.</p></article>
      </div>
    </section>
    <section>
      <h2>Manager briefs</h2>
      <div class="briefs">{brief_cards}</div>
    </section>
    <footer>
      Method: the conservative surplus floor is remaining portions at 17:00 minus the highest post-17:00 demand observed across the five synthetic comparison shifts, floored at zero. High-priority flags require at least 8 portions and at least 25 percent of remaining portions on that conservative basis. For context, the high-priority items total {summary["mean_flagged_units"]} portions against the mean baseline and {summary["conservative_flagged_units"]} against the conservative baseline.
    </footer>
  </main>
  <script>
    const statusFilter = document.getElementById("statusFilter");
    const storeFilter = document.getElementById("storeFilter");
    const visibleRows = document.getElementById("visibleRows");
    const noResults = document.getElementById("noResults");
    const rows = document.querySelectorAll("tbody tr[data-status]");

    function applyFilters() {{
      let visible = 0;
      rows.forEach((row) => {{
        const showStatus = !statusFilter.value || row.dataset.status === statusFilter.value;
        const showStore = !storeFilter.value || row.dataset.store === storeFilter.value;
        const show = showStatus && showStore;
        row.hidden = !show;
        if (show) visible += 1;
      }});
      visibleRows.textContent = `${{visible}} component${{visible === 1 ? "" : "s"}} shown`;
      noResults.style.display = visible === 0 ? "block" : "none";
    }}

    statusFilter.addEventListener("change", applyFilters);
    storeFilter.addEventListener("change", applyFilters);
  </script>
</body>
</html>
"""


def _queue_card(finding: Finding) -> str:
    return (
        '<article class="queue-card">'
        '<div class="queue-title">'
        f"<h3>{escape(finding.store)} | {escape(finding.item)}</h3>"
        '<span class="badge high">High priority</span>'
        "</div>"
        '<div class="evidence">'
        f"<strong>{finding.portions_remaining}</strong> portions remain at 17:00. "
        f"Highest demand in {finding.baseline_shift_count} recent evenings was "
        f"<strong>{finding.highest_observed_remaining_sales}</strong>, leaving "
        f"<strong>{finding.conservative_surplus_floor:.1f}</strong> portions above that baseline."
        "</div>"
        '<p class="check"><strong>Manager check:</strong> validate live orders, walk-in demand and '
        "food-safety constraints before deciding whether any intervention is appropriate.</p>"
        "</article>"
    )


def _row(finding: Finding) -> str:
    status_label = {"high": "High priority", "review": "Monitor", "low": "Low"}[finding.status]
    return (
        f'<tr data-status="{finding.status}" data-store="{escape(finding.store, quote=True)}">'
        f"<td>{escape(finding.store)}</td>"
        f"<td>{escape(finding.item)}</td>"
        f'<td class="number">{finding.portions_remaining}</td>'
        f'<td class="number">{finding.expected_remaining_sales:.1f}<span class="subtle">'
        f"{finding.baseline_shift_count} shifts</span></td>"
        f'<td class="number">{finding.highest_observed_remaining_sales}</td>'
        f'<td class="number">{finding.conservative_surplus_floor:.1f}</td>'
        f'<td><span class="badge {finding.status}">{status_label}</span></td>'
        "</tr>"
    )
