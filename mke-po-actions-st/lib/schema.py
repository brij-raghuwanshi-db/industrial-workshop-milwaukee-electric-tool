"""Schema bootstrap for this app's INDEPENDENT copy of app_po (default: app_po_st).

Ported 1:1 from the React app's server/db/schema-sql.ts. At startup we (idempotently):
  1. CREATE SCHEMA app_po_st
  2. CREATE the mirror tables + the writable action tables + audit/outbox/result + decision_eval
  3. add the FTS tsvector column + GIN index, and pg_trgm index (tolerated if unavailable)
  4. COPY mirror data (exceptions/trajectory/kpi) FROM app_po — the read-only source both apps share
     (only if this app's mirrors are empty, so we never clobber on every boot)

The writable tables start EMPTY and stay this app's own — the React app is never touched.
"""
from __future__ import annotations

from lib import lakebase, config

S = config.PG_SCHEMA        # app_po_st
SRC = config.SOURCE_PG_SCHEMA  # app_po

DDL = [
    f"CREATE SCHEMA IF NOT EXISTS {S}",
    f"""CREATE TABLE IF NOT EXISTS {S}.mirror_exceptions (
        item_id TEXT, item_description TEXT, abc TEXT, organization_code TEXT, week_start DATE,
        planner_name TEXT, actual_end_on_hand DOUBLE PRECISION, planned_safety_stock DOUBLE PRECISION,
        applied_standard_cost DOUBLE PRECISION, stockout_gap_units DOUBLE PRECISION,
        stockout_risk_usd DOUBLE PRECISION, onhand_variance_pct DOUBLE PRECISION,
        exception_type TEXT, is_chronic INTEGER,
        PRIMARY KEY (item_id, organization_code, week_start))""",
    f"""CREATE TABLE IF NOT EXISTS {S}.mirror_trajectory (
        item_id TEXT, organization_code TEXT, week_start DATE, item_description TEXT,
        planned_pab DOUBLE PRECISION, actual_end_on_hand DOUBLE PRECISION,
        onhand_variance_abs DOUBLE PRECISION, onhand_variance_pct DOUBLE PRECISION, onhand_status TEXT,
        actual_po_received DOUBLE PRECISION, actual_shipped DOUBLE PRECISION,
        planned_safety_stock DOUBLE PRECISION, planner_name TEXT, applied_standard_cost DOUBLE PRECISION,
        PRIMARY KEY (item_id, organization_code, week_start))""",
    f"""CREATE TABLE IF NOT EXISTS {S}.mirror_kpi (
        org TEXT PRIMARY KEY, total_stockout_items INTEGER, total_stockout_risk_usd DOUBLE PRECISION,
        chronic_supplier_items INTEGER, distinct_planners INTEGER, refreshed_at TIMESTAMPTZ DEFAULT NOW())""",
    f"""CREATE TABLE IF NOT EXISTS {S}.action_request (
        id TEXT PRIMARY KEY, item_id TEXT NOT NULL, item_description TEXT,
        organization_code TEXT NOT NULL, week_start DATE, exception_type TEXT, action_type TEXT NOT NULL,
        dollar_at_risk DOUBLE PRECISION, systemic_flag TEXT, planner_name TEXT, drafted_note TEXT,
        requested_qty DOUBLE PRECISION, confirmed_qty DOUBLE PRECISION, decision_mode TEXT,
        recommended_action TEXT, recommended_qty DOUBLE PRECISION, final_action TEXT, final_qty DOUBLE PRECISION,
        override_reason TEXT, was_overridden BOOLEAN DEFAULT FALSE, status TEXT NOT NULL DEFAULT 'proposed',
        approved_by TEXT, audit_trail JSONB NOT NULL DEFAULT '[]'::jsonb, version INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), decided_at TIMESTAMPTZ)""",
    f"""CREATE TABLE IF NOT EXISTS {S}.action_audit_event (
        id BIGSERIAL PRIMARY KEY, action_id TEXT NOT NULL, at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        actor TEXT, event TEXT NOT NULL, reason TEXT, tool TEXT, detail JSONB)""",
    f"""CREATE TABLE IF NOT EXISTS {S}.integration_outbox (
        id BIGSERIAL PRIMARY KEY, action_id TEXT NOT NULL,
        target_system TEXT NOT NULL DEFAULT 'ORACLE_FUSION_SIMULATED', payload JSONB NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    f"""CREATE TABLE IF NOT EXISTS {S}.integration_result (
        id BIGSERIAL PRIMARY KEY, outbox_id BIGINT NOT NULL, action_id TEXT NOT NULL,
        result TEXT NOT NULL, detail JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    f"""CREATE TABLE IF NOT EXISTS {S}.decision_eval (
        id BIGSERIAL PRIMARY KEY, action_id TEXT NOT NULL, item_id TEXT, organization_code TEXT,
        recommended_action TEXT, recommended_qty DOUBLE PRECISION, final_action TEXT, final_qty DOUBLE PRECISION,
        was_overridden BOOLEAN, override_reason TEXT, forecast_context JSONB, decided_by TEXT,
        mlflow_run_id TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    f"""CREATE TABLE IF NOT EXISTS {S}.conversations (
        id TEXT PRIMARY KEY, user_email TEXT, title TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    f"""CREATE TABLE IF NOT EXISTS {S}.messages (
        id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT,
        trace_id TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
]

INDEXES = [
    f"CREATE INDEX IF NOT EXISTS ix_stexc_risk ON {S}.mirror_exceptions (organization_code, stockout_risk_usd DESC)",
    f"CREATE INDEX IF NOT EXISTS ix_staction_item ON {S}.action_request (item_id, organization_code, status)",
]

ADD_SEARCH_COLUMN = (
    f"ALTER TABLE {S}.mirror_exceptions ADD COLUMN IF NOT EXISTS search_tsv tsvector "
    f"GENERATED ALWAYS AS (to_tsvector('simple', coalesce(item_id,'') || ' ' || "
    f"coalesce(item_description,''))) STORED"
)
CREATE_FTS_INDEX = f"CREATE INDEX IF NOT EXISTS ix_stexc_tsv ON {S}.mirror_exceptions USING GIN (search_tsv)"
CREATE_TRGM_EXT = "CREATE EXTENSION IF NOT EXISTS pg_trgm"
CREATE_TRGM_INDEX = (
    f"CREATE INDEX IF NOT EXISTS ix_stexc_trgm ON {S}.mirror_exceptions "
    f"USING GIN ((item_id || ' ' || coalesce(item_description,'')) gin_trgm_ops)"
)

# copy mirror data from the shared read-only source (only when our mirror is empty)
COPY_SQL = [
    (f"INSERT INTO {S}.mirror_exceptions SELECT item_id,item_description,abc,organization_code,week_start,"
     f"planner_name,actual_end_on_hand,planned_safety_stock,applied_standard_cost,stockout_gap_units,"
     f"stockout_risk_usd,onhand_variance_pct,exception_type,is_chronic FROM {SRC}.mirror_exceptions "
     f"ON CONFLICT DO NOTHING"),
    (f"INSERT INTO {S}.mirror_trajectory SELECT item_id,organization_code,week_start,item_description,"
     f"planned_pab,actual_end_on_hand,onhand_variance_abs,onhand_variance_pct,onhand_status,"
     f"actual_po_received,actual_shipped,planned_safety_stock,planner_name,applied_standard_cost "
     f"FROM {SRC}.mirror_trajectory ON CONFLICT DO NOTHING"),
    (f"INSERT INTO {S}.mirror_kpi SELECT org,total_stockout_items,total_stockout_risk_usd,"
     f"chronic_supplier_items,distinct_planners,refreshed_at FROM {SRC}.mirror_kpi "
     f"ON CONFLICT (org) DO NOTHING"),
]


def bootstrap() -> dict:
    """Idempotently create this app's schema + tables, then copy mirror data if empty.
    Returns a small status dict. Safe to call on every startup."""
    status = {"schema": S, "created": False, "copied": 0, "fts": False, "trgm": False}
    for stmt in DDL:
        lakebase.execute(stmt)
    for stmt in INDEXES:
        lakebase.execute(stmt)
    status["created"] = True
    # search caps
    try:
        lakebase.execute(ADD_SEARCH_COLUMN)
        lakebase.execute(CREATE_FTS_INDEX)
        status["fts"] = True
    except Exception:
        pass
    try:
        lakebase.execute(CREATE_TRGM_EXT)
        lakebase.execute(CREATE_TRGM_INDEX)
        status["trgm"] = True
    except Exception:
        pass
    # copy mirror data only if our exceptions mirror is empty
    n = lakebase.query(f"SELECT COUNT(*)::int AS c FROM {S}.mirror_exceptions")
    if not n or n[0]["c"] == 0:
        for stmt in COPY_SQL:
            try:
                lakebase.execute(stmt)
            except Exception:
                pass
        n2 = lakebase.query(f"SELECT COUNT(*)::int AS c FROM {S}.mirror_exceptions")
        status["copied"] = n2[0]["c"] if n2 else 0
    else:
        status["copied"] = n[0]["c"]
    return status
