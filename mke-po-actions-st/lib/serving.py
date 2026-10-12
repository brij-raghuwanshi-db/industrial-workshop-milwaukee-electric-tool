"""The agentic explanation engine — BOTH options, ported 1:1 from the React app.

- rules_explain(facts): deterministic reasoning over the real numbers. ALWAYS available;
  the guaranteed answer and the fallback for the LLM path.
- llm_explain(facts): calls the real model-serving endpoint (Claude Sonnet 4.5), parses a
  machine-readable @@REC trailer into a structured recommendation.
- explain(item_facts, engine): 'rules' | 'llm' | 'auto' — auto uses LLM when reachable,
  else rules. Returns the same dict shape either way.
- stream_words(text): a generator for st.write_stream so the answer types out live.

The prompt + trailer format + heuristic text match server/routes/po-actions.ts exactly.
"""
from __future__ import annotations
import re
import time
from typing import Any, Iterator

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from lib import config

REC_VERBS = "EXPEDITE|PULL_IN|NEW_PO|INCREASE_QTY|DECREASE_QTY|PUSH_OUT|CANCEL|WAIT_HOLD|FIX_SUPPLIER|REVIEW"

LLM_SYS = (
    "You are a Milwaukee Tool supply-planning copilot analyzing ONE item's plan-vs-actual facts. "
    "Write 3-4 short, plain-English sentences explaining WHY it is flagged, WHAT the trajectory shows, "
    "and the business risk. On-hand is point-in-time; $ at risk = (safety_stock - on_hand) x unit cost; "
    "a chronic supplier means fix the SOURCE, not just expedite. After the prose, output EXACTLY ONE "
    "final line, nothing after it:\n"
    f"@@REC action=<{REC_VERBS}> qty=<integer or none> confidence=<high|medium|low> reason=<one short clause>"
)


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def rules_explain(facts: dict) -> dict:
    """Deterministic explanation + recommendation over the real facts. Never fails."""
    desc = facts.get("description") or facts.get("item")
    item = facts.get("item")
    abc = facts.get("abc")
    on_hand = _num(facts.get("on_hand"))
    ss = _num(facts.get("safety_stock"))
    gap = max(0, round(_num(facts.get("gap_units"))))
    risk = round(_num(facts.get("dollar_at_risk")))
    var = facts.get("variance_pct")
    chronic = bool(facts.get("chronic_supplier"))
    below = on_hand < ss
    expl = (
        f"{desc} ({item}, ABC {abc}) is {gap:,} units below its safety-stock floor "
        f"— ${risk:,} of stockout risk. "
        f"On-hand is {round(on_hand):,} vs a {round(ss):,} floor ({var}% vs plan). "
        + (
            "Its supplier is chronically late (>60% of receipts), so repeated expediting only "
            "treats the symptom — the root cause is upstream."
            if chronic
            else "This reads as a one-off shortfall rather than a systemic supplier problem."
        )
        + f" Planner: {facts.get('planner')}."
    )
    return {
        "source": "rules",
        "explanation": expl,
        "recommended_action": "FIX_SUPPLIER" if chronic else "EXPEDITE" if below else "REVIEW",
        "recommended_qty": gap,
        "confidence": "medium",
        "reason": (
            "chronic supplier — fix the source, then expedite to cover"
            if chronic
            else "below safety stock — pull inbound in"
            if below
            else "not below floor — confirm before acting"
        ),
    }


def _parse_rec(full: str) -> dict:
    m = re.search(r"@@REC\s+(.*)", full, re.S)
    if not m:
        return {}
    line = m.group(1).strip()
    action = (re.search(r"action=([A-Z_]+)", line) or [None, None])[1]
    qty_raw = (re.search(r"qty=([0-9]+|none)", line, re.I) or [None, None])[1]
    conf = (re.search(r"confidence=(high|medium|low)", line, re.I) or [None, None])[1]
    reason = (re.search(r"reason=(.+)$", line) or [None, None])[1]
    out: dict = {}
    if action:
        out["recommended_action"] = action
    if qty_raw and qty_raw.lower() != "none":
        out["recommended_qty"] = float(qty_raw)
    if conf:
        out["confidence"] = conf.lower()
    if reason:
        out["reason"] = reason.strip()
    return out


def llm_explain(facts: dict) -> dict | None:
    """Call the real serving endpoint. Returns dict or None on any failure (caller falls back)."""
    try:
        w = WorkspaceClient()
        resp = w.serving_endpoints.query(
            name=config.SERVING_ENDPOINT,
            messages=[
                ChatMessage(role=ChatMessageRole.SYSTEM, content=LLM_SYS),
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content="Item facts:\n" + _facts_json(facts),
                ),
            ],
            temperature=0.2,
            max_tokens=600,
        )
        raw = ""
        if resp and resp.choices:
            raw = (resp.choices[0].message.content or "") if resp.choices[0].message else ""
        if not raw.strip():
            return None
        rec = _parse_rec(raw)
        prose = raw.split("@@REC")[0].strip()
        heur = rules_explain(facts)
        return {
            "source": "llm",
            "explanation": prose or heur["explanation"],
            "recommended_action": rec.get("recommended_action", heur["recommended_action"]),
            "recommended_qty": rec.get("recommended_qty", heur["recommended_qty"]),
            "confidence": rec.get("confidence", heur["confidence"]),
            "reason": rec.get("reason", heur["reason"]),
        }
    except Exception:
        return None


def _facts_json(facts: dict) -> str:
    import json
    return json.dumps(facts, indent=2, default=str)


def explain(facts: dict, engine: str = "auto") -> dict:
    """Return the explanation dict for the chosen engine, with graceful fallback to rules."""
    if engine in ("llm", "auto"):
        out = llm_explain(facts)
        if out:
            return out
    return rules_explain(facts)


def stream_words(text: str, delay: float = 0.012) -> Iterator[str]:
    """Yield the text word-by-word for st.write_stream (the live-typing effect)."""
    for tok in re.split(r"(\s+)", text):
        if tok:
            yield tok
            time.sleep(delay)
