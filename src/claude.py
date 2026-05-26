from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from .analysis import Finding


API_URL = "https://api.anthropic.com/v1/messages"


def generate_briefs(findings: list[Finding], model: str) -> dict[str, str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY to use --claude.")
    stores = sorted({finding.store for finding in findings})
    prompt = _prompt(findings, stores)
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Claude request failed: {exc.code} {detail}") from exc
    text = _response_text(result)
    briefs = _extract_json(text)
    if set(briefs) != set(stores) or not all(isinstance(briefs[store], str) for store in stores):
        raise RuntimeError("Claude brief response did not contain one text brief for every store.")
    return briefs


def _prompt(findings: list[Finding], stores: list[str]) -> str:
    evidence = [
        {
            "store": item.store,
            "item": item.item,
            "portions_remaining": item.portions_remaining,
            "expected_remaining_sales": round(item.expected_remaining_sales, 1),
            "projected_surplus": round(item.projected_surplus, 1),
            "status": item.status,
        }
        for item in findings
    ]
    return (
        "Draft short manager briefs for a synthetic restaurant surplus-review demo. "
        "Return only a JSON object mapping each exact store name to a brief of no more than 70 words. "
        "Use only the supplied figures. Do not invent quantities, recommend preparation amounts, "
        "or say that food has been listed. Each brief must say the manager should check live demand "
        "and decide any action. Stores: "
        + json.dumps(stores)
        + ". Findings: "
        + json.dumps(evidence)
    )


def _response_text(result: dict) -> str:
    parts = [
        str(block.get("text", ""))
        for block in result.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    if not parts:
        raise RuntimeError("Claude response did not contain text.")
    return "\n".join(parts)


def _extract_json(text: str) -> dict[str, str]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match is None:
            raise RuntimeError("Could not parse Claude brief response as JSON.")
        result = json.loads(match.group(0))
    if not isinstance(result, dict):
        raise RuntimeError("Claude brief response is not a JSON object.")
    return result
