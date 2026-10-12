// Lakebase schema `app_po` for the MKE PO-actions app.
// Two families: (1) read-only MIRRORS copied from sandbox_operations.po_management.sdp_* (Delta),
// (2) the ONE writable action table + audit + simulated-integration outbox + chat state.
// The app writes ONLY app_po.action_request / action_audit_event / integration_* / chat tables.
// prod is never touched; the sdp_* gold is read via the SQL Warehouse and copied here.

export const SCHEMA = 'app_po';

export const CREATE_SCHEMA_SQL = `CREATE SCHEMA IF NOT EXISTS ${SCHEMA}`;

// ---- read-only mirrors (app never writes; refreshed from Delta by sync.ts) ----
export const CREATE_MIRROR_EXCEPTIONS = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.mirror_exceptions (
    item_id TEXT,
    item_description TEXT,
    abc TEXT,
    organization_code TEXT,
    week_start DATE,
    planner_name TEXT,
    actual_end_on_hand DOUBLE PRECISION,
    planned_safety_stock DOUBLE PRECISION,
    applied_standard_cost DOUBLE PRECISION,
    stockout_gap_units DOUBLE PRECISION,
    stockout_risk_usd DOUBLE PRECISION,
    onhand_variance_pct DOUBLE PRECISION,
    exception_type TEXT,
    is_chronic INTEGER,
    PRIMARY KEY (item_id, organization_code, week_start)
  )`;

export const CREATE_MIRROR_TRAJECTORY = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.mirror_trajectory (
    item_id TEXT,
    organization_code TEXT,
    week_start DATE,
    item_description TEXT,
    planned_pab DOUBLE PRECISION,
    actual_end_on_hand DOUBLE PRECISION,
    onhand_variance_abs DOUBLE PRECISION,
    onhand_variance_pct DOUBLE PRECISION,
    onhand_status TEXT,
    actual_po_received DOUBLE PRECISION,
    actual_shipped DOUBLE PRECISION,
    planned_safety_stock DOUBLE PRECISION,
    planner_name TEXT,
    applied_standard_cost DOUBLE PRECISION,
    PRIMARY KEY (item_id, organization_code, week_start)
  )`;

export const CREATE_MIRROR_KPI = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.mirror_kpi (
    org TEXT PRIMARY KEY,
    total_stockout_items INTEGER,
    total_stockout_risk_usd DOUBLE PRECISION,
    chronic_supplier_items INTEGER,
    distinct_planners INTEGER,
    refreshed_at TIMESTAMPTZ DEFAULT NOW()
  )`;

// ---- THE ONE WRITABLE TABLE: action_request ----
// status flow: proposed -> approved -> executed | rejected | overridden
export const CREATE_ACTION_REQUEST = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.action_request (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    item_description TEXT,
    organization_code TEXT NOT NULL,
    week_start DATE,
    exception_type TEXT,               -- e.g. 'Stockout / below safety stock'
    action_type TEXT NOT NULL,         -- EXPEDITE | PULL_IN | PUSH_OUT | CANCEL | NEW_PO | REBALANCE | REVIEW
    dollar_at_risk DOUBLE PRECISION,
    systemic_flag TEXT,                -- 'Systemic (chronic supplier)' | 'One-off'
    planner_name TEXT,
    drafted_note TEXT,                 -- agent-drafted rationale
    requested_qty DOUBLE PRECISION,    -- NEW-1 requested vs confirmed
    confirmed_qty DOUBLE PRECISION,
    decision_mode TEXT,                -- NEW-3 order | rebalance
    -- decision-capture (learning loop): what the agent recommended vs what the human committed
    recommended_action TEXT,           -- agent's proposed verb
    recommended_qty DOUBLE PRECISION,  -- agent's proposed quantity (e.g. 100)
    final_action TEXT,                 -- what the planner actually executed
    final_qty DOUBLE PRECISION,        -- what the planner committed (e.g. 75)
    override_reason TEXT,              -- free text: why the human changed it
    was_overridden BOOLEAN DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'proposed',
    approved_by TEXT,                  -- OBO email of the planner who approved
    audit_trail JSONB NOT NULL DEFAULT '[]'::jsonb,  -- append-only [{at,by,action,reason,tool}]
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMPTZ
  )`;

export const CREATE_AUDIT_EVENT = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.action_audit_event (
    id BIGSERIAL PRIMARY KEY,
    action_id TEXT NOT NULL,
    at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor TEXT,                        -- OBO email or 'agent'
    event TEXT NOT NULL,               -- proposed | approved | executed | rejected | overridden | note
    reason TEXT,
    tool TEXT,
    detail JSONB
  )`;

// ---- SIMULATED external writeback (never a real Oracle call — guardrail) ----
export const CREATE_INTEGRATION_OUTBOX = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.integration_outbox (
    id BIGSERIAL PRIMARY KEY,
    action_id TEXT NOT NULL,
    target_system TEXT NOT NULL DEFAULT 'ORACLE_FUSION_SIMULATED',
    payload JSONB NOT NULL,            -- the typed PO-change request we WOULD send
    status TEXT NOT NULL DEFAULT 'queued',   -- queued | simulated_sent | failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;

export const CREATE_INTEGRATION_RESULT = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.integration_result (
    id BIGSERIAL PRIMARY KEY,
    outbox_id BIGINT NOT NULL,
    action_id TEXT NOT NULL,
    result TEXT NOT NULL,              -- 'SIMULATED_ACK' — proof the loop ran, no real Oracle
    detail JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;

// ---- decision-evaluation log (agent-recommendation vs human-decision → MLflow eval dataset) ----
export const CREATE_DECISION_EVAL = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.decision_eval (
    id BIGSERIAL PRIMARY KEY,
    action_id TEXT NOT NULL,
    item_id TEXT,
    organization_code TEXT,
    recommended_action TEXT,           -- what the agent proposed
    recommended_qty DOUBLE PRECISION,
    final_action TEXT,                 -- what the human committed
    final_qty DOUBLE PRECISION,
    was_overridden BOOLEAN,
    override_reason TEXT,
    forecast_context JSONB,            -- the ai_forecast inputs/outputs the rec was based on
    decided_by TEXT,                   -- OBO email
    mlflow_run_id TEXT,                -- link to the MLflow eval record (if logged)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;

// ---- chat state (reusable) ----
export const CREATE_CONVERSATIONS = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.conversations (
    id TEXT PRIMARY KEY,
    user_email TEXT,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;

export const CREATE_MESSAGES = `
  CREATE TABLE IF NOT EXISTS ${SCHEMA}.messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    trace_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`;

export const ALL_DDL = [
  CREATE_SCHEMA_SQL,
  CREATE_MIRROR_EXCEPTIONS,
  CREATE_MIRROR_TRAJECTORY,
  CREATE_MIRROR_KPI,
  CREATE_ACTION_REQUEST,
  CREATE_AUDIT_EVENT,
  CREATE_INTEGRATION_OUTBOX,
  CREATE_INTEGRATION_RESULT,
  CREATE_DECISION_EVAL,
  CREATE_CONVERSATIONS,
  CREATE_MESSAGES,
];

// index for the queue sort (idempotent)
export const CREATE_INDEXES = [
  `CREATE INDEX IF NOT EXISTS ix_mirror_exc_risk ON ${SCHEMA}.mirror_exceptions (organization_code, stockout_risk_usd DESC)`,
  `CREATE INDEX IF NOT EXISTS ix_action_item ON ${SCHEMA}.action_request (item_id, organization_code, status)`,
];

// ---- SEARCH (capability-detected): native FTS tsvector + pg_trgm fuzzy; ILIKE always works.
// BM25 (tsquery_bm25/parserrank) is NOT provisioned on this branch — verified 2026-08-31 (only
// pg_trgm + vector available). Code is structured so BM25 drops in later if the extension is enabled.
// A generated tsvector over item_id + description makes ts_rank relevance ranking available today.
export const ADD_SEARCH_COLUMN = `
  ALTER TABLE ${SCHEMA}.mirror_exceptions
    ADD COLUMN IF NOT EXISTS search_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('simple', coalesce(item_id,'') || ' ' || coalesce(item_description,''))) STORED`;
export const CREATE_SEARCH_FTS_INDEX =
  `CREATE INDEX IF NOT EXISTS ix_mirror_exc_tsv ON ${SCHEMA}.mirror_exceptions USING GIN (search_tsv)`;
// trigram index (only if pg_trgm is installable on this branch — attempted, tolerated if it fails)
export const CREATE_TRGM_EXT = `CREATE EXTENSION IF NOT EXISTS pg_trgm`;
export const CREATE_SEARCH_TRGM_INDEX =
  `CREATE INDEX IF NOT EXISTS ix_mirror_exc_trgm ON ${SCHEMA}.mirror_exceptions USING GIN ((item_id || ' ' || coalesce(item_description,'')) gin_trgm_ops)`;
