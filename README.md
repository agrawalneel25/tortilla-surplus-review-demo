# Surplus Review Assistant

An illustrative prototype for a restaurant operations team. It flags menu components that may be at unusual risk of end-of-shift surplus, then produces a short manager brief explaining what should be checked.

This demo uses synthetic data only. It is not connected to Tortilla systems, does not make preparation decisions, and does not automatically list surplus food.

**Live dashboard:** https://agrawalneel25.github.io/tortilla-surplus-review-demo/

![Generated dashboard preview](docs/dashboard.png)

## Why This Scope

For a restaurant manager, a useful first version should be easy to question:

1. Compare portions currently remaining with the store's historical remaining demand at the same checkpoint.
2. Flag only material projected surplus.
3. Show the supporting figures.
4. Leave any operational action with the manager.

The numerical flag is deterministic. By default the brief is deterministic too, so the demo is easy to inspect. An optional Claude API path can rewrite only the manager brief from structured findings. The model is told not to invent quantities or take actions.

## Run

From the repository root:

```powershell
python -m src.run_demo
start docs\index.html
```

Run tests:

```powershell
python -m unittest discover -s tests
```

Optional Claude-written briefs:

```powershell
$env:ANTHROPIC_API_KEY="your-key"
python -m src.run_demo --claude
start docs\index.html
```

The optional route calls Anthropic's Messages API directly with Python's standard library. It was added as an integration boundary; the committed dashboard uses deterministic briefs and does not require a key.

## Data

`data/historical_remaining_sales.csv` contains synthetic prior shifts. Each row records portions sold after 17:00 for one store and item.

`data/current_shift.csv` contains a synthetic 17:00 snapshot: portions prepared and portions already sold.

For each store and item:

```text
portions_remaining = prepared_units - sold_units_by_17_00
expected_remaining_sales = mean(prior portions sold after 17:00)
projected_surplus = max(portions_remaining - expected_remaining_sales, 0)
```

The demo flags `high` risk only where projected surplus is at least 8 portions and at least 25 percent of portions remaining. Smaller excesses are shown as `review` or `low`.

## Structure

```text
data/             synthetic CSV inputs
docs/index.html   generated dashboard for review
src/analysis.py   baseline and flagging logic
src/briefs.py     deterministic manager-facing brief
src/claude.py     optional Claude API brief rewriter
src/report.py     standalone HTML report generator
src/run_demo.py   CLI entry point
tests/            unit tests
```

## Limitations

- Synthetic data is useful for testing the interface, not for estimating business impact.
- A historical mean is deliberately simple. Real validation would test seasonal, weather, promotion and channel effects.
- The tool surfaces a review signal only. Food safety, demand changes and Too Good To Go listing decisions remain with staff.
