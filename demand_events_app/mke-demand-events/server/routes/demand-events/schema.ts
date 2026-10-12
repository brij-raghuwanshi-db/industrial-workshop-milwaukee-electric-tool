// Lakebase schema for the MKE Demand Events App (P3).
// GUARDRAIL: this is the ONLY place the app persists transactional state.
// prod_edw is read-only (analytics plugin); Delta output goes to
// sandbox_operations.po_management via a separate publication Job.
// Schema owned by the app service principal (created on first startup).

export const SCHEMA = 'demand_events';

interface LakebaseQuery {
  query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }>;
}

// Idempotent DDL — safe to run on every startup.
const DDL: string[] = [
  `CREATE SCHEMA IF NOT EXISTS ${SCHEMA}`,

  // ---- Event core -------------------------------------------------------
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event (
     exp_id            BIGINT PRIMARY KEY,
     event_name        TEXT NOT NULL,
     event_type        TEXT NOT NULL DEFAULT 'non_repeating'
                        CHECK (event_type IN ('non_repeating','repeating','both')),
     status            TEXT NOT NULL DEFAULT 'IN_PROGRESS'
                        CHECK (status IN ('IN_PROGRESS','ACTIVE','DEACTIVATED','CLOSED')),
     organization_code TEXT NOT NULL DEFAULT '2012',
     record_version    INT  NOT NULL DEFAULT 1,
     created_by        TEXT,
     created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
     last_modified_by  TEXT,
     last_modified_at  TIMESTAMPTZ NOT NULL DEFAULT now()
   )`,

  // Sequence-free EXP ID allocator: max(exp_id)+1, seeded above any imported id.
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.exp_id_seq (
     one BOOLEAN PRIMARY KEY DEFAULT true CHECK (one),
     next_id BIGINT NOT NULL
   )`,
  `INSERT INTO ${SCHEMA}.exp_id_seq (one, next_id) VALUES (true, 1000)
     ON CONFLICT (one) DO NOTHING`,

  // One row per store-tranche (mirrors source file_index).
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_header (
     exp_id             BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     tranche_index      INT NOT NULL DEFAULT 0,
     number_of_stores   INT,
     ship_date          DATE,
     ship_month         TEXT,
     set_month          TEXT,
     load_per_store     NUMERIC,
     aspv               NUMERIC,
     confidence         TEXT,
     lift_pct           NUMERIC,
     PRIMARY KEY (exp_id, tranche_index)
   )`,

  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_tag (
     exp_id BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     tag    TEXT NOT NULL,
     PRIMARY KEY (exp_id, tag)
   )`,

  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_comment (
     comment_id  BIGSERIAL PRIMARY KEY,
     exp_id      BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     author      TEXT,
     body        TEXT NOT NULL,
     created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
   )`,

  // ---- Selection & grain -----------------------------------------------
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_customer (
     exp_id       BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     mkedg5       TEXT NOT NULL,
     input_level  TEXT,                       -- mkedg0..mkedg5 the planner entered at
     status       TEXT NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE','CLOSED')),
     PRIMARY KEY (exp_id, mkedg5)
   )`,

  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_item (
     exp_id                 BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     item_number            TEXT NOT NULL,      -- dashed, as entered
     item_id                TEXT,               -- dash-normalized
     validation_flag        TEXT,               -- OK | WARN
     validation_rule_version TEXT,              -- which criterion produced the flag
     item_status            TEXT,               -- observed status from item master
     status                 TEXT NOT NULL DEFAULT 'ACTIVE'
                            CHECK (status IN ('ACTIVE','CLOSED')),
     PRIMARY KEY (exp_id, item_number)
   )`,

  // The disaggregated output grain + manual-override store. Signed, sparse.
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_cell (
     exp_id      BIGINT NOT NULL REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     item_number TEXT NOT NULL,
     mkedg5      TEXT NOT NULL,
     month       DATE NOT NULL,                 -- first-of-month
     value       NUMERIC NOT NULL,              -- units, signed
     source      TEXT NOT NULL DEFAULT 'DIRECT'
                 CHECK (source IN ('DIRECT','BUILDER','DISAGGREGATED','OVERRIDE','SEED')),
     updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
     PRIMARY KEY (exp_id, item_number, mkedg5, month)
   )`,

  // ---- Concurrency, audit ----------------------------------------------
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_lock (
     exp_id     BIGINT PRIMARY KEY REFERENCES ${SCHEMA}.event(exp_id) ON DELETE CASCADE,
     locked_by  TEXT NOT NULL,
     locked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
     expires_at TIMESTAMPTZ NOT NULL
   )`,

  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.event_audit_event (
     audit_event_id BIGSERIAL PRIMARY KEY,
     exp_id         BIGINT,
     actor          TEXT,
     event_type     TEXT NOT NULL,              -- CREATED/EDITED/DISAGGREGATED/BULK/CLOSED/PUBLISHED...
     field          TEXT,                       -- item/month/field level granularity
     before_state   JSONB,
     after_state    JSONB,
     occurred_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
     batch_id       TEXT
   )`,

  // ---- Bulk edit (the requested capability) ----------------------------
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.bulk_edit_batch (
     batch_id       TEXT PRIMARY KEY,           -- also the idempotency key
     category_type  TEXT NOT NULL,              -- EVENT/CUSTOMER/TAG/ITEM/STATUS/ORG
     category_selector JSONB NOT NULL,
     operation      TEXT NOT NULL,              -- SET_STATUS/CLOSE/ADJUST_VALUE/APPLY_LIFT
     op_value       JSONB,
     requested_by   TEXT,
     requested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
     status         TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING/APPLIED/FAILED
     matched        INT DEFAULT 0,
     changed        INT DEFAULT 0
   )`,

  // Staging rows for one batch — the set-based apply reads from here.
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.bulk_edit_stage (
     batch_id    TEXT NOT NULL REFERENCES ${SCHEMA}.bulk_edit_batch(batch_id) ON DELETE CASCADE,
     exp_id      BIGINT NOT NULL,
     item_number TEXT,
     mkedg5      TEXT,
     month       DATE,
     new_value   NUMERIC,
     new_status  TEXT,
     submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
   )`,

  // ---- Publication acknowledgement -------------------------------------
  `CREATE TABLE IF NOT EXISTS ${SCHEMA}.publication_ack (
     run_id        TEXT PRIMARY KEY,
     published_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
     active_events INT,
     rows_published INT,
     hash_diff     TEXT,
     status        TEXT NOT NULL DEFAULT 'SUCCEEDED',  -- SUCCEEDED/FAILED/VERIFICATION_PENDING
     note          TEXT
   )`,

  `CREATE INDEX IF NOT EXISTS event_cell_by_event ON ${SCHEMA}.event_cell(exp_id)`,
  `CREATE INDEX IF NOT EXISTS audit_by_event ON ${SCHEMA}.event_audit_event(exp_id, occurred_at DESC)`,
];

export async function initDemandEventsSchema(lakebase: LakebaseQuery): Promise<boolean> {
  try {
    for (const stmt of DDL) {
      await lakebase.query(stmt);
    }
    console.log(`[demand-events] schema '${SCHEMA}' ready`);
    return true;
  } catch (err) {
    console.warn('[demand-events] schema setup failed:', (err as Error).message);
    console.warn('[demand-events] Deploy the app first so the SP owns the schema. See lakebase skill: Schema Permissions for Deployed Apps.');
    return false;
  }
}
