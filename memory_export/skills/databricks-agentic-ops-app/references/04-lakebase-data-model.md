# 04 — Lakebase Data Model

Lakebase Postgres is the app's OLTP plane: **read-only synced mirrors** of the governed gold tables
+ **one writable operational table** + **chat state**. Schema is Drizzle ORM; migrations auto-apply
on boot; data is copied from Delta via a one-shot sync (or Lakebase Synced Tables in prod).

> **VERIFIED — how the app connects to Lakebase (see 10).** The first-class path is the AppKit
> `lakebase()` plugin: call `appkit.lakebase.query(sql, params)` — it owns the connection pool AND
> **auto-refreshes the OAuth token**, so you never manage a `pg.Pool` or a token yourself. Reach for
> a raw `pg.Pool` + JWT-as-password (§07 manual boot) ONLY in a non-AppKit app; if you use it, you
> own token refresh (Lakebase OAuth tokens expire ~1h — cache with a 60s buffer and reconnect). This
> skill's Drizzle examples still apply — point Drizzle at the AppKit pool
> (`createDb(appkit.lakebase.pool)`) rather than a self-made pool.
>
> **Managed synced tables have an access gotcha:** a `databricks postgres create-synced-table`
> table is owned by a system role, and the app's SP has `CAN_CONNECT_AND_CREATE` but NOT
> `pg_read_all_data`. The project owner must **explicitly grant the app SP read access** to each
> synced table (see the `databricks-lakebase` skill) or every `SELECT` on it returns permission
> denied. The one-shot SQL-Statements-API sync below sidesteps this (the app owns the tables it
> inserts into) at the cost of being a copy, not a live sync.

## The three table families (`app.*`)

### 1. Chat state (reusable across any build — keep as-is)

| Table | Key fields |
|-------|-----------|
| `conversations` | `id`, `user_email`, `title`, `kind` (`default`/`demo_dock`), `created_at`, `updated_at` |
| `messages` | `id`, `conversation_id → conversations`, `role`, `content`, `position`, `trace_id`, `thinking` (JSONB), `error`, `created_at` |
| `feedback` | `id`, `message_id → messages`, `value` (`up`/`down`), `rationale`, `trace_id`, `mlflow_assessment_id`, `created_at` |

### 2. Synced read-only mirrors (from Delta — domain-specific; app never writes these)

Representative shape (rename to your domain). The "position" table is the queue's backing row; the
"open" table is the actionable subset with capacity context; the "recommendations" table holds the
model's batch output; the "providers" table is the referral directory (search target).

| Table | Source (Delta) | Key fields |
|-------|----------------|-----------|
| `record_position` | `gold_*_panel` | `id` (PK), classifying dims (condition/category, band/tier, geo lat/lng), `summary_text` (de-identified), recency (`days_since_*`), **`risk_score`**, `open_gap_count`, boolean gap flags, `severity_weight`, **`exposure_usd`**, **`risk_band`** (`critical`/`elevated`/`watch`/`stable`) |
| `open_atrisk` | `gold_open_*` | `id` (PK), `risk_score`, `exposure_usd`, recency, gap flags, `severity_weight`, `capacity_headroom_hours`, `candidate_provider_id` |
| `action_recommendations` | `gold_*_recommendations` | `id` (PK), `recommended_action`, `recommended_provider_id`, `predicted_benefit` (double), `predicted_net_value_usd` (double), **`action_ranking`** (JSONB — all options with benefit+cost+hours), `scored_at` |
| `providers` | `raw_providers` | `provider_id` (PK), `provider_name`, `specialty`, `program_type`, **`description`** (searchable), `accepting_referrals` — indexed by **Lakebase Search** over (name, description) |

Enrichment tables a richer build also mirrors/derives: `record_search` (a `search_tsv` /
`tsvector`-backed search index), plus operational-domain tables (occupancy grids, provider
schedules, outcomes).

### 3. The writable operational table (the ONLY thing the app writes)

```ts
export const actions = appSchema.table('actions', {
  id: text('id').primaryKey(),                 // uuid
  recordId: text('record_id'),
  actionType: text('action_type'),             // domain enum
  providerId: text('provider_id'),             // nullable (referral)
  draftedNote: text('drafted_note'),           // the model-drafted summary
  predictedBenefit: doublePrecision('predicted_benefit'),
  status: text('status').default('proposed'),  // proposed → approved → executed | rejected | overridden
  approvedBy: text('approved_by'),             // OBO email
  auditTrail: jsonb('audit_trail').default([]),// append-only [{at, by, action, reason, tool}]
  version: integer('version').default(1),      // optimistic version bump on each state change
  createdAt: timestamp('created_at').defaultNow(),
  decidedAt: timestamp('decided_at'),
});
```

The Panel derives a record's **live state** by `LEFT JOIN`-ing `record_position` → its latest
`actions` row: an approved action makes the row show "action assigned" + a badge, and the queue
re-sorts. The append-only `auditTrail` makes each action a standalone timeline the detail drawer's
Activity tab renders.

A build that tracks unit economics also writes a `value_ledger` (cost/savings/expected-value events
per action, feeding the P&L / ROI analytics) and a `workflow_state` (trigger source, decision,
linked action) — both written from action endpoints, both feeding the analytics page.

## Drizzle schema conventions

- `pgSchema('app')` → `appSchema.table(...)`. Types: `text`, `doublePrecision`, `integer`,
  `boolean`, `timestamp`, `jsonb`.
- `references(() => conversations.id)` for FKs; `.default(...)`, `.defaultNow()`, `.primaryKey()`.
- Migrations from `server/db/schema.ts` via drizzle-kit, auto-applied on boot (`runMigrations(db)`),
  safe to re-run. Some builds also run raw `CREATE TABLE IF NOT EXISTS` at boot for belt-and-braces.

## Delta → Lakebase sync

One-shot on boot when the mirror is empty (prod: replace with managed Lakebase Synced Tables — same
outcome on screen). Uses the **Databricks SQL Statements API** to read Delta, then chunked inserts.

```ts
async function syncTable(client, token, host, warehouseId, cfg) {
  const resp = await fetch(`${host}/api/2.0/sql/statements`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type':'application/json' },
    body: JSON.stringify({ statement: cfg.query, warehouse_id: warehouseId,
                           wait_timeout: '50s', disposition: 'INLINE', format: 'JSON_ARRAY' }),
  });
  const data = await resp.json();
  if (data.status?.state !== 'SUCCEEDED') { console.error('[sync] failed', data.status); return; }
  const rows = data.result?.data_array || [];
  for (let i = 0; i < rows.length; i += 2000) {                 // chunked, idempotent
    const batch = rows.slice(i, i + 2000);
    const placeholders = batch.map((_, idx) => `(${cfg.columns.map((__, ci) => `$${idx*cfg.columns.length + ci + 1}`).join(',')})`).join(',');
    await client.query(`INSERT INTO ${cfg.target} (${cfg.columns.join(',')}) VALUES ${placeholders} ON CONFLICT DO NOTHING`, batch.flat());
  }
}
```

Rules:
- **Guard on emptiness** — `SELECT COUNT(*)` the position table; skip sync if already populated.
- **Tolerate missing sources** — a not-yet-built gold table (e.g. the recommender output before the
  model runs) should be caught (`TABLE_OR_VIEW_NOT_FOUND`) and leave that mirror empty so the app
  still boots and the Visualize layer works.
- **Sample for scale** — mirror the full at-risk set + a bounded sample of "stable" rows (e.g.
  `WHERE risk_band IN ('critical','elevated','watch') UNION ALL (… risk_band='stable' LIMIT 500)`)
  so the scatter has context without copying millions of rows.
- **The writable table is never synced** — starts empty; it's the app's own state.
- Source table names come from `config/app.json` `data.tables`.

## Reset-demo

`resetDemo(pool)` → `TRUNCATE` the writable action table + the mirrors, then re-run the sync. All
agent writes are wiped; at-risk records return to baseline, KPIs return to full. Exposed as an admin
route (`POST /api/admin/reset`).

## Lakebase Search / full-text

The `providers` (and optionally `record_search`) tables support search inside Postgres — no external
ML dependency required:
- **Full-text (portable):** `to_tsvector`/`to_tsquery` (or `websearch_to_tsquery`), `@@` match,
  `ts_rank` ordering, `ts_headline` for highlighted snippets, prefix matching via `word:*`.
- **BM25 (if provisioned):** a `tsquery_bm25` column + `parserrank(search_tsv, $1::tsquery_bm25)`.
- **Hybrid text+vector (if a vector extension is provisioned):** add a vector-similarity clause for
  hybrid ranking over name + description.
- **Always ship an ILIKE fallback** so search degrades gracefully if the FTS index isn't present.
