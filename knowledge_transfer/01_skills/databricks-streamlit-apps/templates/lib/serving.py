"""LLM explanation engine — rules-first, model as enhancement, with a live-typing generator.

- rules_explain(facts): deterministic answer over the real numbers. ALWAYS available; the guaranteed
  result and the fallback if the model call fails.
- llm(system, user): one-shot call to the serving endpoint.
- explain(facts, engine): 'rules' | 'llm' | 'auto' — auto uses the LLM when reachable, else rules.
- stream_words(text): generator for st.write_stream (the live-typing effect).

Structured output without brittle JSON: the model writes prose then ONE `@@REC` trailer line we parse.
"""
from __future__ import annotations
import re
import time
from typing import Any, Iterator

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from lib import config

REC_VERBS = "APPROVE|REJECT|EXPEDITE|CANCEL|REVIEW"  # <-- your action vocabulary
LLM_SYS = (
    "You are a domain copilot. Given ONE record's facts, explain in 3-4 short sentences WHY it is "
    "flagged and the business risk, then output EXACTLY ONE final line:\n"
    f"@@REC action=<{REC_VERBS}> qty=<integer or none> confidence=<high|medium|low> reason=<one clause>"
)


def rules_explain(facts: dict) -> dict:
    """Deterministic explanation + recommendation over the real facts. Never fails. CUSTOMIZE."""
    # Replace with your real rule over facts. This is the guaranteed answer.
    return {
        "source": "rules",
        "explanation": f"{facts.get('id')} is flagged. Customize rules_explain() with your domain logic.",
        "recommended_action": "REVIEW",
        "recommended_qty": None,
        "confidence": "medium",
        "reason": "deterministic rule",
    }


def llm(system: str, user: str) -> str:
    w = WorkspaceClient()
    r = w.serving_endpoints.query(
        name=config.SERVING_ENDPOINT,
        messages=[ChatMessage(role=ChatMessageRole.SYSTEM, content=system),
                  ChatMessage(role=ChatMessageRole.USER, content=user)],
        temperature=0.2, max_tokens=600,
    )
    return (r.choices[0].message.content or "") if r and r.choices else ""


def _parse_rec(full: str) -> dict:
    m = re.search(r"@@REC\s+(.*)", full, re.S)
    if not m:
        return {}
    line = m.group(1).strip()
    out: dict = {}
    if (a := re.search(r"action=([A-Z_]+)", line)):
        out["recommended_action"] = a.group(1)
    if (q := re.search(r"qty=([0-9]+|none)", line, re.I)) and q.group(1).lower() != "none":
        out["recommended_qty"] = float(q.group(1))
    if (c := re.search(r"confidence=(high|medium|low)", line, re.I)):
        out["confidence"] = c.group(1).lower()
    if (rs := re.search(r"reason=(.+)$", line)):
        out["reason"] = rs.group(1).strip()
    return out


def explain(facts: dict, engine: str = "auto") -> dict:
    heur = rules_explain(facts)
    if engine in ("llm", "auto"):
        try:
            import json
            raw = llm(LLM_SYS, "Facts:\n" + json.dumps(facts, indent=2, default=str))
            if raw.strip():
                rec = _parse_rec(raw)
                return {"source": "llm", "explanation": raw.split("@@REC")[0].strip() or heur["explanation"],
                        "recommended_action": rec.get("recommended_action", heur["recommended_action"]),
                        "recommended_qty": rec.get("recommended_qty", heur["recommended_qty"]),
                        "confidence": rec.get("confidence", heur["confidence"]),
                        "reason": rec.get("reason", heur["reason"])}
        except Exception:
            pass
    return heur


def stream_words(text: str, delay: float = 0.012) -> Iterator[str]:
    for tok in re.split(r"(\s+)", text):
        if tok:
            yield tok
            time.sleep(delay)
