# 02 — AppKit Backend

The backend is an Express app assembled through `@databricks/appkit`. Two variants ship in
practice — an **AppKit-managed** boot (plugins resolve resources, SDK auth chain, migration gate)
and a **manual** boot (self-minted OAuth token, JWT-as-Postgres-password). Both serve the same SPA
+ `/api/*` surface. Prefer AppKit-managed for production; manual is a fine minimal fallback.

## The three AppKit plugins

```ts
import { createApp, server, lakebase, analytics, getExecutionContext } from '@databricks/appkit';

await createApp({
  plugins: [
    server(),      // Express + static SPA serving + OBO header forwarding; auto-starts after onPluginsReady
    lakebase(),    // Postgres pool from PGHOST/PGDATABASE/PGPORT/PGSSLMODE + LAKEBASE_* env (no args in 0.41+)
    analytics({}), // typed SQL execution against a SQL Warehouse (DATABRICKS_WAREHOUSE_ID)
    // optional: genie(), files()
  ],
  onPluginsReady(appkit) {
    const db = createDb(appkit.lakebase.pool);      // Drizzle handle
    appkit.server.extend((app) => { /* gate + routes here */ });
    startBackgroundInit();                          // migrations → sync → mlflow (fire-and-forget)
  },
});
```

Plugin notes:
- `server()` auto-starts listening **after** `onPluginsReady` returns — so register all routes
  *inside* `onPluginsReady` (via `appkit.server.extend`), not after `createApp`.
- Inline the route registration inside `onPluginsReady` so `appkit` keeps its precise `PluginMap<T>`
  type. Hoisting it to a helper typed as the generic `createApp` return collapses
  `appkit.server`/`appkit.analytics` to `never`.
- `lakebase()` reads standard PG env; the platform injects those at deploy time. Pre-0.41 it took
  `branch`/`database` args — those were removed.
- `analytics.query(sql, params)` runs on the warehouse but **cannot template identifiers**
  (catalog/schema). For charts that need `${catalog}.${schema}` interpolation, use a custom route
  that substitutes the identifiers and reads the SQL from `config/queries/*.sql`.

## Boot order & the migration gate

The server must accept traffic immediately (so the shell renders) but block DB-dependent routes
until init completes. Pattern:

```ts
let migrationsDone = false;
let migrationsFailure: Error | null = null;
let migrationsReady: Promise<void> = new Promise(() => {}); // replaced by startBackgroundInit

const STARTUP_SAFE_PATHS = new Set(['/api/config', '/api/me', '/api/warehouse']);
const STARTUP_SAFE_PREFIXES = ['/api/log/'];

app.use('/api', async (req, res, next) => {
  if (migrationsDone) return next();
  if (STARTUP_SAFE_PATHS.has(req.path)) return next();
  if (STARTUP_SAFE_PREFIXES.some(p => req.path.startsWith(p))) return next();
  if (migrationsFailure) {                               // real bug — surface it in the browser
    return res.status(503).json({ error: `Database initialization failed: ${migrationsFailure.message}` });
  }
  try {
    await Promise.race([migrationsReady, new Promise((_, r) => setTimeout(() => r(new Error('startup-timeout')), 5000))]);
    next();
  } catch (e) {
    const isTimeout = e instanceof Error && e.message === 'startup-timeout';
    res.set('Retry-After', '2').status(503).json({
      error: isTimeout ? 'Database is still initializing — please retry in a moment.'
                       : `Database initialization failed: ${(e as Error).message}`,
    });
  }
});
```

`startBackgroundInit()` runs (fire-and-forget): `runMigrations(db)` → `syncFromDelta(db, data)` →
`migrationsDone = true`. On failure it sets `migrationsFailure` (which the gate returns) and
re-throws; the top-level `.catch(()=>{})` swallows the duplicate rejection. In parallel it resolves
the MLflow experiment id and calls `mlflow.init(...)` **after** sync (so sync queries aren't traced
as orphan spans).

## Config loading (JSONC + env substitution + zod)

`config/app.json` is parsed as **JSONC** (comments + trailing commas allowed) after `${VAR}` /
`${VAR:default}` substitution against `process.env`, then validated with a **zod** schema that
mirrors the `AppConfig` type. Fail fast with one clear message. Two tiers of placeholder checks:

- **WARN** for optional fields with graceful fallback (MLflow paths → "trace pending" but app boots).
- **ERROR** for fields the boot depends on (dashboard id, branding, `data.catalog/schema`) — an
  unfilled `<placeholder>` there means the app will half-work confusingly, so refuse to boot.

```ts
raw = raw.replace(/\$\{([A-Z_][A-Z0-9_]*)(?::([^}]*))?\}/g,
  (_, name, dflt) => { const v = process.env[name]; return v ?? dflt ?? ''; });
const parsed = parseJsonc(raw, errors, { allowTrailingComma: true });
const result = appConfigSchema.safeParse(parsed);  // zod
```

`AppConfig` fields (representative): `masEndpointName?` XOR `genieSpaceId?` (the ask_data backend),
`agentMlflowExperimentPath?`, `agentModel?`, `dashboardId`, `pipelineId?`, `warehouseId?`,
`lakebaseProjectId?`, `appUrl?`, `mlModelName?`, `branding.appName`, `assistantScript[]` (scripted
demo prompts), `data.{catalog,schema,tables{...}}`. Note `data.catalog/schema` are **not** `.min(1)`
— in local/preview they may be empty and the sync no-ops rather than crashes.

## OBO auth — the outbound Authorization header

Keep auth **dumb** — one helper, no service-principal special-casing. The environment is the single
source of truth (the launcher sets `DATABRICKS_AUTH_TYPE=oauth-m2m` + client id/secret and removes
`DATABRICKS_TOKEN` for cross-workspace deploys, so the SDK chain resolves correctly on its own).

```ts
export async function authHeaders(req: Request): Promise<Headers> {
  const h = new Headers();
  const userToken = req.headers['x-forwarded-access-token'] as string | undefined;
  if (userToken) { h.set('Authorization', `Bearer ${userToken}`); return h; }  // OBO in prod
  const { client } = getExecutionContext();                                     // SDK chain in dev/M2M
  await client.config.authenticate(h);
  return h;
}
```

- **Prod:** Databricks Apps injects `x-forwarded-access-token` (+ `x-forwarded-email`,
  `x-forwarded-preferred-username`) per request → outbound calls (Genie, MLflow, model serving) are
  attributed to the viewing user; UC permissions + audit logs reflect them.
- **Dev / M2M:** delegate to the SDK auth chain (CLI profile, OAuth refresh, service principal).

User identity resolution (`lib/user.ts`): `getCurrentUserEmail(req)` reads `x-forwarded-email` →
`x-forwarded-user` → `DEV_USER_EMAIL` → placeholder. `getCurrentUserInfo(req)` returns name + email
+ workspace url/id for `/api/me`.

## MLflow experiment bootstrap

`ensureMlflowExperiment(host, path)` (REST, `lib/mlflow.ts`):
1. `GET /api/2.0/mlflow/experiments/get-by-name` (treat 404/400 as "missing").
2. `POST /api/2.0/mlflow/experiments/create`. On `RESOURCE_ALREADY_EXISTS` → re-GET (boot race). On
   `Parent directory does not exist` (nested path, first deploy) → `POST /api/2.0/workspace/mkdirs`
   for the parent, then retry create.
3. 30s cap per REST call so a hung workspace API can't block boot.

The experiment path is derived so tracing works out of the box: explicit `agentMlflowExperimentPath`
→ else `/Shared/solution_builder/${DATABRICKS_APP_NAME}-agent-traces` → else degrade with a loud
warning ("View trace" shows "Trace pending…").

Pass the app's resolved bearer token to `mlflow.init({ trackingUri:'databricks', experimentId, host,
databricksToken })` — the bundled MLflow SDK otherwise resolves the default `~/.databrickscfg` and
ignores the app's config file, so trace uploads throw "cannot configure default credentials". Read
the token from the authenticated header (works for PAT and OAuth alike).

## Route surface (representative)

Domain CRUD (`/api/records`, `/api/records/:id`), KPIs (`/api/kpis`), capacity (`/api/capacity`),
action lifecycle (`POST /api/actions`, `PATCH /:id/approve|reject|override`), feedback
(`/api/feedback`, `/feedback/stats`), search (`/api/search` — BM25/FTS + ILIKE fallback), analytics
(`/api/analytics/:queryName`, `/api/dashboard-data`), chat (`POST /api/chat/stream` SSE +
`POST /api/chat` non-streaming fallback), config/identity/health (`/api/config`, `/api/identity`,
`/api/health-score`, `/api/ops-health`), Genie proxy (`POST /api/genie/query`), model scoring
(`POST /api/score-intervention`, `GET /api/score-record/:id`), value/economics ledger
(`/api/value/summary|trend|ledger`), and any domain-specific operational routes (e.g. bed/slot
reservation, scheduling).

## Error logging

Compact by default — Drizzle stuffs the full SQL + every bound param into `err.message` (100k+ chars
on bulk inserts), which floods the terminal. Truncate hard, extract pg `code`/`constraint`/`detail`,
print header + ≤12 stack frames in one `console.error`. Register a global Express error handler
(Express 5 forwards async rejections) so routes don't need per-handler try/catch.
