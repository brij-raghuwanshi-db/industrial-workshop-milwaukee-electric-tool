"""Write-path: propose -> execute (ONE transaction) -> reject, plus decision-eval capture.

Ports server/routes/po-actions.ts writes exactly:
- propose: insert action_request (status='proposed') + one audit event.
- execute (the HUMAN GATE): one transaction — flip to executed, stamp OBO approver, append
  audit_trail, insert audit_event + SIMULATED Oracle outbox + SIMULATED_ACK, capture
  decision_eval (recommended vs final + reason). No real Oracle call, ever.
- reject: flip to rejected (if not executed) + audit.
"""
from __future__ import annotations
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from lib import lakebase, config
from lib.identity import planner_email

S = config.PG_SCHEMA


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"act-{int(time.time()*1000):x}-{uuid.uuid4().hex[:8]}"


def propose(item_id: str, action_type: str, drafted_note: str | None,
            requested_qty: float | None, decision_mode: str = "order") -> dict[str, Any]:
    who = planner_email()
    aid = _new_id()
    ctx = lakebase.query(
        f"""SELECT item_description, week_start, planner_name, stockout_risk_usd, is_chronic, exception_type
              FROM {S}.mirror_exceptions WHERE item_id=%s AND organization_code=%s""",
        (item_id, config.ORG),
    )
    c = ctx[0] if ctx else {}
    systemic = "Systemic (chronic supplier)" if c.get("is_chronic") in (1, True) else "One-off"
    audit = [{"at": _now_iso(), "by": who, "action": "proposed", "reason": drafted_note, "tool": "propose"}]
    rows = lakebase.query(
        f"""INSERT INTO {S}.action_request
              (id, item_id, item_description, organization_code, week_start, exception_type, action_type,
               dollar_at_risk, systemic_flag, planner_name, drafted_note, requested_qty, decision_mode,
               status, audit_trail)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'proposed',%s::jsonb)
            RETURNING *""",
        (aid, item_id, c.get("item_description"), config.ORG, c.get("week_start"),
         c.get("exception_type") or "Stockout / below safety stock", action_type,
         c.get("stockout_risk_usd"), systemic, c.get("planner_name"), drafted_note,
         requested_qty, decision_mode, json.dumps(audit)),
    )
    lakebase.execute(
        f"""INSERT INTO {S}.action_audit_event (action_id, actor, event, reason, tool)
            VALUES (%s,%s,'proposed',%s,'propose')""",
        (aid, who, drafted_note),
    )
    return rows[0] if rows else {"id": aid}


def execute(action_id: str, *, reason: str | None = None,
            recommended_action: str | None = None, recommended_qty: float | None = None,
            final_action: str | None = None, final_qty: float | None = None,
            forecast_context: dict | None = None) -> dict[str, Any]:
    who = planner_email()
    cur = lakebase.query(f"SELECT * FROM {S}.action_request WHERE id=%s", (action_id,))
    if not cur:
        raise ValueError("action not found")
    a = cur[0]
    if a.get("status") == "executed":
        return {**a, "dataMutated": True, "note": "already executed"}

    overridden = bool(
        (recommended_action and final_action and recommended_action != final_action)
        or (recommended_qty is not None and final_qty is not None and recommended_qty != final_qty)
    )
    with lakebase.transaction() as cur_tx:
        cur_tx.execute(
            f"""UPDATE {S}.action_request
                   SET status='executed', approved_by=%s, decided_at=NOW(), version=version+1,
                       final_action=%s, final_qty=%s, recommended_action=%s, recommended_qty=%s,
                       override_reason=%s, was_overridden=%s,
                       audit_trail = audit_trail || %s::jsonb
                 WHERE id=%s RETURNING *""",
            (who, final_action, final_qty, recommended_action, recommended_qty, reason, overridden,
             json.dumps([{"at": _now_iso(), "by": who, "action": "executed", "reason": reason, "tool": "execute"}]),
             action_id),
        )
        updated = cur_tx.fetchone()
        cur_tx.execute(
            f"""INSERT INTO {S}.action_audit_event (action_id, actor, event, reason, tool)
                VALUES (%s,%s,'executed',%s,'execute')""",
            (action_id, who, reason),
        )
        # SIMULATED external writeback — typed request enqueued + immediately acked. NO real Oracle.
        cur_tx.execute(
            f"""INSERT INTO {S}.integration_outbox (action_id, payload, status)
                VALUES (%s,%s::jsonb,'simulated_sent') RETURNING id""",
            (action_id, json.dumps({
                "system": "ORACLE_FUSION_SIMULATED", "po_action": a.get("action_type"),
                "item_id": a.get("item_id"), "org": a.get("organization_code"),
                "requested_qty": final_qty if final_qty is not None else a.get("requested_qty"),
                "note": a.get("drafted_note"), "simulated": True,
                "disclaimer": "No real Oracle call — sandbox simulation per project guardrail",
            })),
        )
        outbox_id = cur_tx.fetchone()["id"]
        cur_tx.execute(
            f"""INSERT INTO {S}.integration_result (outbox_id, action_id, result, detail)
                VALUES (%s,%s,'SIMULATED_ACK',%s::jsonb)""",
            (outbox_id, action_id, json.dumps({"acknowledged_at": _now_iso(), "simulated": True})),
        )
        # decision-eval capture (recommended vs final → MLflow eval dataset)
        cur_tx.execute(
            f"""INSERT INTO {S}.decision_eval
                  (action_id, item_id, organization_code, recommended_action, recommended_qty,
                   final_action, final_qty, was_overridden, override_reason, forecast_context, decided_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""",
            (action_id, a.get("item_id"), a.get("organization_code"), recommended_action, recommended_qty,
             final_action, final_qty, overridden, reason,
             json.dumps(forecast_context or {}), who),
        )
    return {**(updated or a), "dataMutated": True, "was_overridden": overridden}


def reject(action_id: str, reason: str | None = None) -> dict[str, Any]:
    who = planner_email()
    rows = lakebase.query(
        f"""UPDATE {S}.action_request
               SET status='rejected', approved_by=%s, decided_at=NOW(), version=version+1,
                   audit_trail = audit_trail || %s::jsonb
             WHERE id=%s AND status <> 'executed' RETURNING *""",
        (who, json.dumps([{"at": _now_iso(), "by": who, "action": "rejected", "reason": reason, "tool": "reject"}]),
         action_id),
    )
    if not rows:
        raise ValueError("not rejectable")
    lakebase.execute(
        f"""INSERT INTO {S}.action_audit_event (action_id, actor, event, reason, tool)
            VALUES (%s,%s,'rejected',%s,'reject')""",
        (action_id, who, reason),
    )
    return {**rows[0], "dataMutated": True}


def reset_demo() -> None:
    """Truncate the writable tables (same as the React /admin/reset). Mirrors are untouched."""
    lakebase.execute(
        f"TRUNCATE {S}.action_request, {S}.action_audit_event, "
        f"{S}.integration_outbox, {S}.integration_result, {S}.decision_eval"
    )
