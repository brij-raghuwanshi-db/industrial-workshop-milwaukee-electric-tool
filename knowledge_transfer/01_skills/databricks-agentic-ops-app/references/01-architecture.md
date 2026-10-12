# 01 — Architecture & Data Flow

## The two-plane model

The app straddles two data planes that share one governance boundary (Unity Catalog):

```
┌─────────────────────────── UNITY CATALOG (governance) ───────────────────────────┐
│                                                                                    │
│   PLANE A — OLAP (read-only source of truth)     PLANE B — OLTP (serving + write)  │
│   ┌────────────────────────────────────┐        ┌──────────────────────────────┐  │
│   │ Delta tables (medallion)           │        │ Lakebase Postgres (`app.*`)  │  │
│   │  • gold_* fact/panel tables        │  sync  │  • synced READ-ONLY mirrors  │  │
│   │  • metric view (governed KPIs)     │───────▶│    of the gold tables        │  │
│   │  • Volumes (raw landing zone)      │        │  • ONE WRITABLE action table │  │
│   │                                    │        │  • chat state (conv/msg/fb)  │  │
│   │ Read by: SQL Warehouse, Genie,     │        │ Read+written by: the App     │  │
│   │          model batch-scoring       │        │ Sub-ms per-record reads      │  │
│   └────────────────────────────────────┘        └──────────────────────────────┘  │
│              ▲                    ▲                          ▲                      │
│              │                    │                          │                      │
│      SQL Warehouse          Genie space              Lakebase pool (pg)             │
│      (analytics charts)     (ask_data tool)          (panel reads + writes)         │
│              └──────────────────┴──────────────┬───────────┘                        │
│                                                 │                                    │
│                       ┌─────────────────────────▼──────────────────────────┐        │
│                       │  DATABRICKS APP (Node + Express + React)            │        │
│                       │  • serves the SPA + /api/*                          │        │
│                       │  • runs the streaming agent (tool-calling)          │        │
│                       │  • calls model-serving endpoint for scoring         │        │
│                       │  • embeds the AI/BI dashboard (iframe, SSO)         │        │
│                       └─────────────────────────┬──────────────────────────┘        │
│                          model calls ──▶ Unity AI Gateway (cap/guardrails/log)      │
│                          every turn   ──▶ MLflow experiment (traces + feedback)     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Why two planes

- **Delta / SQL Warehouse** is columnar, great for aggregate analytics and Genie's generated SQL,
  but latency (seconds) is wrong for a click-responsive operator screen, and UC tables are not
  transactional.
- **Lakebase Postgres** gives sub-millisecond per-record reads AND a real transactional write
  surface (the app's action/approval/audit state). It is still governed by Unity Catalog.
- **The bridge:** at boot the app copies the read-only gold tables into Lakebase mirrors (one-shot
  in the demo build; **Lakebase Synced Tables** — managed, continuous — in production). The app
  reads the mirrors for the live queue and writes only its own operational table.

## The core contract: read → recommend → approve → write → cascade

This is the load-bearing loop the whole app exists to deliver. Preserve it exactly.

```
 operator                app (client)            app (server/agent)         data planes
    │                        │                        │                        │
    │  opens Panel           │  GET /api/records ─────▶│  SELECT ... ──────────▶│ Lakebase mirror
    │  sees ranked queue ◀───│◀── rows                 │◀── rows                │
    │                        │                        │                        │
    │  "why is X flagged?"   │  POST /api/chat/stream ▶│  agent turn starts     │
    │                        │  (SSE opens)            │  ├ ask_data ──────────▶│ Genie (NL→SQL, poll)
    │  watches Thinking ◀────│◀── tool spans (SSE)     │  ├ find_record ───────▶│ Lakebase mirror
    │                        │                        │  ├ rank_actions ──────▶│ model-serving endpoint
    │  reads recommendation ◀│◀── streamed tokens      │  └ drafts summary, STOPS│
    │                        │                        │                        │
    │  clicks Approve  ──────│  (chat "yes, approve") ▶│  execute_action ──────▶│ Lakebase WRITE
    │                        │                        │    (transaction+audit) │  (the one writable table)
    │                        │◀── done{dataMutated}    │                        │
    │  queue updates LIVE ◀──│  emits `dataMutated`    │                        │
    │  (KPI −1, row flips,   │  → refetch /api/records,│                        │
    │   exposure drops)      │    /api/kpis            │                        │
```

**The three enforcement points:**

1. **Approval gate** — the system prompt defines a strict 3-phase chain (Discover → Draft+Confirm →
   Execute); the write tool is only called after the operator says "yes/approve/do it". The write
   lives behind its own tool so the model can't accidentally fold it into a read.
2. **`dataMutated` event** — the write tool returns a payload the runner recognizes; the client
   emits a `dataMutated` browser event on turn-end; every data-bearing view subscribes and
   refetches. This is what makes the update *visible without a reload*.
3. **Audit + attribution** — the write is one DB transaction that inserts the action row (status,
   approver email from OBO, an append-only audit-trail JSONB entry) so each action is a standalone,
   attributable timeline.

## Boot sequence (server)

The server must start serving before the DB is ready so the shell renders; DB-dependent routes are
gated until migrations + sync finish.

```
1. Normalize DATABRICKS_HOST (force https://, strip trailing slash) — many URL() calls depend on it.
2. Load + validate config/app.json (JSONC + ${ENV} substitution + zod). Fail fast on placeholders.
3. createApp({ plugins: [server(), lakebase(), analytics()] }).
4. onPluginsReady:
     a. create the Drizzle handle from the lakebase pool.
     b. register a gate middleware on /api/* that awaits `migrationsReady`
        (STARTUP_SAFE paths like /api/config, /api/me bypass it).
     c. register all routes (config, chat, domain CRUD, admin, charts).
     d. kick off background init (fire-and-forget):
          runMigrations() → syncFromDelta() → set migrationsDone=true
          in parallel: resolve/create the MLflow experiment, then mlflow.init().
5. Server auto-starts listening. Gate returns 503+Retry-After until init done;
   returns the real error if init FAILED (so the failure is visible in the browser).
```

Two boot styles exist in practice (VERIFIED — prefer the first; see [10-verification-and-fallbacks.md](10-verification-and-fallbacks.md)):

- **AppKit-managed boot** (recommended): plugins resolve the Lakebase pool + credentials from env;
  `appkit.lakebase.query()` handles pooling AND OAuth token refresh; auth uses the SDK credential
  chain (OBO in prod). See [02-backend-appkit.md](02-backend-appkit.md).
- **Manual boot** (portable fallback for non-AppKit stacks — you then own token refresh): the server mints an OAuth M2M token itself
  (`/oidc/v1/token`, `grant_type=client_credentials`, `scope=all-apis`) and uses the **JWT directly
  as the Postgres password** (Lakebase OAuth), then `CREATE TABLE IF NOT EXISTS` + sync. Start the
  HTTP listener FIRST, then boot the DB in the background so a DB failure never blocks serving. See
  [07-config-deploy-auth.md](07-config-deploy-auth.md).

## What lives where (canonical layout)

```
app/
  app.yaml                    # Databricks Apps manifest: command, env, resources (lakebase, genie…)
  config/
    app.json                  # use-case knobs: branding, genie/dashboard ids, data.tables, model, chips
    queries/*.sql             # warehouse-backed analytics queries (one file per chart)
  server/
    server.ts | index.ts      # boot + wiring (AppKit-managed OR manual)
    agent/
      <agent>.ts              # the agent: tools + system prompt + SDK config
      tools/{genie,mas}.ts    # ask_data backends (Genie poll loop OR MAS stream)
      tools/logged-tool.ts    # tool() wrapper that logs thrown errors + sanitizes for the model
    chat-stream/
      agent-stream.ts         # drives the SDK loop, maps events → SSE taxonomy, MLflow span/turn
      sse.ts                  # sseWrite/sseError helpers (writableEnded guard)
      index.ts                # /api/chat/stream handler: persist msg, sanitize history, abort on close
    db/
      schema.ts               # Drizzle: mirrors + the writable action table + chat state
      sync.ts                 # Delta→Lakebase one-shot sync (SQL Statements API) + resetDemo
      migrate.ts              # drizzle migrations, safe to re-run
      queries/*.ts            # domain query helpers (read + transactional write)
    lib/{auth,user,mlflow,endpoint,logger}.ts
    routes/*.ts               # config, chat, domain CRUD, admin, charts, activity
  client/src/
    App.tsx main.tsx          # SPA shell + routing + chat dock
    pages/*.tsx               # Home, Panel, Analytics, Dashboard, (Ops, Beds+Schedule)
    <feature>/*.tsx           # KPI cards, queue table, detail drawer, chat components, charts
    lib/events.ts             # dataMutated emitter (the live-cascade bus)
```

## Design altitude

Keep the **structural wiring** (boot order, plugin set, route registration, SSE taxonomy,
`dataMutated` bus) use-case-agnostic and stable. Do all customization in five places:

1. `config/app.json` — branding, ids, source tables, starter chips, agent model.
2. `db/schema.ts` — the Lakebase tables (mirrors + the writable action table).
3. `db/sync.ts` — the Delta→Lakebase table list.
4. `db/queries/*.ts` + `agent/<agent>.ts` — domain query helpers + agent tools + system prompt.
5. `client/**` shared types + page content + theme.
