"""Domain read-layer: every po-actions.ts READ route ported to a Python function.

SQL is copied verbatim from server/routes/po-actions.ts (psycopg uses %s placeholders
instead of $1). All queue/kpi/analytics/scenario reads hit the Lakebase mirrors; forecast
+ what-if hit the SQL warehouse (ai_forecast over the Delta sdp_ table).
"""
from __future__ import annotations
from typing import Any

from lib import lakebase, warehouse, config

S = config.PG_SCHEMA
ORG = config.ORG

# ---------- queue ----------
def queue(limit: int = 200) -> list[dict[str, Any]]:
    limit = min(int(limit or 200), 500)
    return lakebase.query(
        f"""SELECT e.*, a.id AS action_id, a.action_type, a.status AS action_status, a.approved_by
              FROM {S}.mirror_exceptions e
              LEFT JOIN LATERAL (
                SELECT id, action_type, status, approved_by FROM {S}.action_request ar
                WHERE ar.item_id = e.item_id AND ar.organization_code = e.organization_code
                ORDER BY ar.created_at DESC LIMIT 1
              ) a ON true
             ORDER BY (a.status IS NOT NULL) ASC, e.stockout_risk_usd DESC
             LIMIT %s""",
        (limit,),
    )


# ---------- search (FTS -> trigram -> ILIKE) ----------
def search(q: str, caps: dict[str, bool]) -> dict[str, Any]:
    q = (q or "").strip()
    if not q:
        return {"mode": "empty", "rows": []}
    if caps.get("fts"):
        rows = lakebase.query(
            f"""SELECT item_id, item_description, stockout_risk_usd, is_chronic,
                       ts_rank(search_tsv, websearch_to_tsquery('simple',%s)) AS rank
                  FROM {S}.mirror_exceptions
                 WHERE search_tsv @@ websearch_to_tsquery('simple',%s)
                 ORDER BY rank DESC, stockout_risk_usd DESC LIMIT 20""",
            (q, q),
        )
        if rows:
            return {"mode": "fts", "rows": rows}
    if caps.get("trgm"):
        rows = lakebase.query(
            f"""SELECT item_id, item_description, stockout_risk_usd, is_chronic,
                       similarity(item_id || ' ' || coalesce(item_description,''), %s) AS sim
                  FROM {S}.mirror_exceptions
                 WHERE (item_id || ' ' || coalesce(item_description,'')) %% %s
                 ORDER BY sim DESC, stockout_risk_usd DESC LIMIT 20""",
            (q, q),
        )
        if rows:
            return {"mode": "trigram", "rows": rows}
    rows = lakebase.query(
        f"""SELECT item_id, item_description, stockout_risk_usd, is_chronic
              FROM {S}.mirror_exceptions
             WHERE item_id ILIKE '%%'||%s||'%%' OR item_description ILIKE '%%'||%s||'%%'
             ORDER BY stockout_risk_usd DESC LIMIT 20""",
        (q, q),
    )
    return {"mode": "ilike", "rows": rows}


# ---------- KPIs ----------
def kpis() -> dict[str, Any]:
    base = lakebase.query(f"SELECT * FROM {S}.mirror_kpi WHERE org=%s", (ORG,))
    actioned = lakebase.query(
        f"""SELECT COALESCE(SUM(dollar_at_risk),0)::float resolved_usd, COUNT(*)::int resolved_items
              FROM {S}.action_request WHERE status='executed'"""
    )
    return {"base": base[0] if base else None, "actioned": actioned[0] if actioned else None}


# ---------- record (trajectory + activity) ----------
def record(item_id: str) -> dict[str, Any]:
    traj = lakebase.query(
        f"""SELECT week_start, planned_pab, actual_end_on_hand, onhand_variance_pct, onhand_status,
                   actual_po_received, actual_shipped, planned_safety_stock
              FROM {S}.mirror_trajectory
             WHERE item_id=%s AND organization_code=%s
             ORDER BY week_start DESC LIMIT 12""",
        (item_id, ORG),
    )
    activity = lakebase.query(
        f"""SELECT at, actor, event, reason, tool FROM {S}.action_audit_event
             WHERE action_id IN (SELECT id FROM {S}.action_request WHERE item_id=%s AND organization_code=%s)
             ORDER BY at DESC LIMIT 50""",
        (item_id, ORG),
    )
    return {"trajectory": traj, "activity": activity}


# ---------- facts (for the explain engine) ----------
def facts(item_id: str) -> dict[str, Any] | None:
    ctx = lakebase.query(
        f"""SELECT item_id,item_description,abc,planner_name,actual_end_on_hand,planned_safety_stock,
                   applied_standard_cost,stockout_gap_units,stockout_risk_usd,onhand_variance_pct,is_chronic
              FROM {S}.mirror_exceptions WHERE item_id=%s AND organization_code=%s""",
        (item_id, ORG),
    )
    if not ctx:
        return None
    c = ctx[0]
    traj = lakebase.query(
        f"""SELECT week_start, planned_pab, actual_end_on_hand, planned_safety_stock,
                   actual_po_received, actual_shipped
              FROM {S}.mirror_trajectory WHERE item_id=%s AND organization_code=%s
             ORDER BY week_start DESC LIMIT 8""",
        (item_id, ORG),
    )
    return {
        "item": c["item_id"], "description": c["item_description"], "abc": c["abc"],
        "planner": c["planner_name"], "on_hand": c["actual_end_on_hand"],
        "safety_stock": c["planned_safety_stock"], "gap_units": c["stockout_gap_units"],
        "dollar_at_risk": c["stockout_risk_usd"], "variance_pct": c["onhand_variance_pct"],
        "chronic_supplier": c["is_chronic"] == 1, "recent_weeks": traj,
        "_cost": c["applied_standard_cost"],  # kept for what-if exposure math
    }


# ---------- forecast (ai_forecast on the warehouse) ----------
def forecast(item_id: str) -> dict[str, Any]:
    safe = item_id.replace("'", "''")
    sql = f"""SELECT CAST(ds AS STRING) ds, ROUND(y_forecast,0) y_forecast,
                     ROUND(y_lower,0) y_lower, ROUND(y_upper,0) y_upper
      FROM ai_forecast(
        TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
              FROM {config.SDP_PLAN_VS_ACTUAL}
              WHERE item_id='{safe}' AND organization_code='{ORG}' AND actual_end_on_hand IS NOT NULL),
        horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y') ORDER BY ds"""
    rows = warehouse.run_sql(sql)
    ss = lakebase.query(
        f"SELECT planned_safety_stock FROM {S}.mirror_exceptions WHERE item_id=%s AND organization_code=%s",
        (item_id, ORG),
    )
    return {
        "method": "ai_forecast" if rows else "unavailable",
        "forecast": rows,
        "safety_stock": ss[0]["planned_safety_stock"] if ss else None,
    }


# ---------- what-if ----------
def whatif(item_id: str, action: str, qty: float | None = None) -> dict[str, Any]:
    safe = item_id.replace("'", "''")
    base_sql = f"""SELECT ROUND(MIN(y_forecast),0) min_fc FROM ai_forecast(
        TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
              FROM {config.SDP_PLAN_VS_ACTUAL}
              WHERE item_id='{safe}' AND organization_code='{ORG}' AND actual_end_on_hand IS NOT NULL),
        horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y')"""
    b = warehouse.run_sql(base_sql)
    ctx = lakebase.query(
        f"""SELECT planned_safety_stock, actual_end_on_hand, applied_standard_cost
              FROM {S}.mirror_exceptions WHERE item_id=%s AND organization_code=%s""",
        (item_id, ORG),
    )
    c = ctx[0] if ctx else {}
    ss = float(c.get("planned_safety_stock") or 0)
    oh = float(c.get("actual_end_on_hand") or 0)
    cost = float(c.get("applied_standard_cost") or 0)
    gap = qty if qty is not None else max(0.0, ss - oh)
    direction = config.ACTION_DIR.get(action, 0)
    base_min = float((b[0].get("min_fc") if b else 0) or 0)
    sim_min = base_min + direction * gap
    return {
        "action": action, "simulated_units": gap,
        "baseline_min_onhand": base_min, "simulated_min_onhand": sim_min,
        "safety_stock_floor": ss,
        "baseline_breaches_ss": base_min < ss, "simulated_breaches_ss": sim_min < ss,
        "exposure_delta_usd": round((sim_min - base_min) * cost),
    }


# ---------- analytics ----------
def by_abc() -> list[dict]:
    return lakebase.query(
        f"""SELECT COALESCE(abc,'—') AS abc, COUNT(*)::int AS items,
                   ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
              FROM {S}.mirror_exceptions GROUP BY abc ORDER BY abc"""
    )


def by_planner() -> list[dict]:
    return lakebase.query(
        f"""SELECT COALESCE(planner_name,'Unassigned') AS planner, COUNT(*)::int AS items,
                   ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
              FROM {S}.mirror_exceptions GROUP BY planner
             ORDER BY dollar_at_risk DESC LIMIT 12"""
    )


def chronic_split() -> list[dict]:
    return lakebase.query(
        f"""SELECT CASE WHEN is_chronic=1 THEN 'Systemic (chronic supplier)' ELSE 'One-off' END AS kind,
                   COUNT(*)::int AS items, ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
              FROM {S}.mirror_exceptions GROUP BY kind ORDER BY dollar_at_risk DESC"""
    )


def risk_bands() -> list[dict]:
    return lakebase.query(
        f"""SELECT band, COUNT(*)::int items, ROUND(SUM(stockout_risk_usd))::float dollar_at_risk FROM (
              SELECT CASE WHEN stockout_risk_usd>=1000000 THEN '4 · ≥$1M'
                          WHEN stockout_risk_usd>=100000 THEN '3 · $100K–1M'
                          WHEN stockout_risk_usd>=10000 THEN '2 · $10–100K'
                          ELSE '1 · <$10K' END AS band, stockout_risk_usd
                FROM {S}.mirror_exceptions) t GROUP BY band ORDER BY band"""
    )


def progress() -> dict:
    r = lakebase.query(
        f"""SELECT
              (SELECT COUNT(*)::int FROM {S}.mirror_exceptions) AS total_items,
              (SELECT COUNT(*)::int FROM {S}.action_request WHERE status='executed') AS executed,
              (SELECT COALESCE(SUM(dollar_at_risk),0)::float FROM {S}.action_request WHERE status='executed') AS resolved_usd,
              (SELECT COALESCE(SUM(stockout_risk_usd),0)::float FROM {S}.mirror_exceptions) AS total_usd"""
    )
    return r[0] if r else {}


# ---------- scenarios ----------
def scenario_cost_vs_units() -> dict:
    by_dollar = lakebase.query(
        f"""SELECT item_id, item_description, ROUND(stockout_gap_units)::int gap_units,
                   ROUND(stockout_risk_usd)::float dollar
              FROM {S}.mirror_exceptions ORDER BY stockout_risk_usd DESC LIMIT 5"""
    )
    by_units = lakebase.query(
        f"""SELECT item_id, item_description, ROUND(stockout_gap_units)::int gap_units,
                   ROUND(stockout_risk_usd)::float dollar
              FROM {S}.mirror_exceptions ORDER BY stockout_gap_units DESC LIMIT 5"""
    )
    return {"by_dollar": by_dollar, "by_units": by_units}


def scenario_chronic() -> dict:
    rows = lakebase.query(
        f"""SELECT item_id, item_description, ROUND(stockout_risk_usd)::float dollar, planner_name
              FROM {S}.mirror_exceptions WHERE is_chronic=1 ORDER BY stockout_risk_usd DESC LIMIT 10"""
    )
    tot = lakebase.query(
        f"""SELECT COUNT(*)::int items, ROUND(SUM(stockout_risk_usd))::float dollar
              FROM {S}.mirror_exceptions WHERE is_chronic=1"""
    )
    return {"rows": rows, "total": tot[0] if tot else {}}


def scenario_hero() -> dict:
    hero = lakebase.query(
        f"SELECT item_id FROM {S}.mirror_exceptions ORDER BY stockout_risk_usd DESC LIMIT 1"
    )
    if not hero:
        return {"item_id": None, "rows": []}
    iid = hero[0]["item_id"]
    rows = lakebase.query(
        f"""SELECT week_start, planned_pab, actual_end_on_hand, planned_safety_stock,
                   actual_po_received, actual_shipped
              FROM {S}.mirror_trajectory WHERE item_id=%s ORDER BY week_start""",
        (iid,),
    )
    return {"item_id": iid, "rows": rows}
