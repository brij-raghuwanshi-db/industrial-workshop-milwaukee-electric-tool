# 07 — Config, Deploy & Auth

> **VERIFIED — scaffold with the CLI, don't hand-wire (see 10). This is the #1 anti-endless-loop
> step.** Before hand-authoring `app.yaml`, `package.json`, or the plugin wiring, run the official
> scaffolder — it emits the *correct* resource keys, versions, and manifest for your workspace's
> installed AppKit, so you don't loop on invented shapes:
>
> ```bash
> databricks apps manifest --profile <PROFILE>          # discover plugins + resource keys + fields
> databricks apps init --name <name> --features <analytics,lakebase,genie,serving,...> \
>   --set analytics.sql-warehouse.id=<WAREHOUSE_ID> \
>   --set lakebase.postgres.branch=<projects/…/branches/…> \
>   --set lakebase.postgres.database=<…/databases/…> \
>   --run none --profile <PROFILE>
> npx @databricks/appkit docs                            # authoritative API signatures (createApp, plugins, hooks)
> databricks apps validate --profile <PROFILE>           # tsc --noEmit + lint gate BEFORE deploy
> ```
>
> App-name rules: ≤26 chars, lowercase letters/numbers/hyphens only (no underscores). NEVER pin the
> `@databricks/appkit` version in `package.json` — `init` sets the right one. Do NOT guess plugin
> names / resource keys — derive them from `databricks apps manifest`. The blocks below describe what
> the scaffolder produces and what to customize — treat them as the *shape*, and let `init` +
> `appkit docs` be the source of truth for exact syntax.


## `config/app.json` — the use-case knobs

Single JSONC file (comments + trailing commas), `${ENV}` / `${ENV:default}` substituted at load,
zod-validated at boot (see [02-backend-appkit.md](02-backend-appkit.md)). Everything domain-specific
that isn't schema or code lives here so the same skeleton reskins cleanly.

```jsonc
{
  "name": "…", "subtitle": "…",
  "persona": { "name": "…", "title": "…", "org": "…" },
  "story": { "headline": "…", "situation": "…", "goal": "…" },   // Home page narrative
  "theme": { "primary": "#…", "accent": "#…", "warning": "#…",
             "critical": "#…", "success": "#…", "text": "#…", "background": "#…" },
  "data": {                                                       // Delta source tables for the sync
    "catalog": "${CATALOG}", "schema": "${SCHEMA}",
    "tables": { "record_panel": "gold_*_panel", "open_atrisk": "gold_open_*",
                "recommendations": "gold_*_recommendations", "providers": "raw_providers" }
  },
  "genie_space_id": "${GENIE_SPACE_ID}",        // OR masEndpointName — the ask_data backend
  "dashboard_id": "${DASHBOARD_ID}",            // embedded AI/BI dashboard
  "agentModel": "${MODEL_ENDPOINT}",            // gateway-governed serving endpoint
  "agentMlflowExperimentPath": "/Shared/…/…-agent-traces",
  "hero_record": "…",                            // the spotlight record for the demo arc
  "starter_chips": ["…", "…", "…"]              // Home + chat quick-questions
}
```

## `app.yaml` — the Databricks Apps manifest

Declares the run command, env vars, and **resources** (which grant the app scoped access + inject
connection env at runtime).

```yaml
command: [ "npm", "run", "start" ]
env:
  - { name: CATALOG,        value: <catalog> }
  - { name: SCHEMA,         value: <schema> }
  - { name: GENIE_SPACE_ID, value: "<id>" }
  - { name: DASHBOARD_ID,   value: "<id>" }
  - { name: MODEL_ENDPOINT, value: <serving-endpoint> }
  - { name: DATABRICKS_WAREHOUSE_ID, value: <warehouse> }
  - { name: NODE_ENV,       value: production }
resources:
  - name: lakebase
    type: lakebase
    lakebase: { permission: read_write }          # the writable action table needs read_write
  - name: genie-space
    type: genie_space
    genie_space: { id: "<id>", permission: query }
  # declare the ai-gateway scope here so the agent's model calls are governed
```

`package.json` scripts: `dev` (concurrent `tsx watch server` + `vite`), `build` (`vite build` +
`tsc`/`tsdown` for the server), `start` (`node dist/server/index.js` or `tsx server/index.ts`).
`postinstall: npm run build` so the container has a built client. Bind on
`process.env.DATABRICKS_APP_PORT || PORT || 8000`.

## Two auth models

### OBO (recommended for prod) — SDK chain + forwarded user token
Databricks Apps injects `x-forwarded-access-token`/`-email`/`-preferred-username` per request. The
`authHeaders(req)` helper prefers the forwarded token (attributes calls to the viewing user) and
falls back to the SDK credential chain (CLI profile in dev, service principal / OAuth M2M in
deploy). The Lakebase plugin resolves the pool + credentials from injected PG env. **Keep auth
logic dumb** — the environment (auth type + client id/secret, or a forwarded token) is the single
source of truth; do not pin a WorkspaceClient in code.

### OAuth M2M + JWT-as-password (manual boot) — self-contained
The server mints its own token and uses it directly as the Postgres password (Lakebase OAuth V1):

```ts
async function getOAuthToken() {                       // cache with 60s expiry buffer
  const resp = await fetch(`${host}/oidc/v1/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type:'client_credentials', client_id, client_secret, scope:'all-apis' }).toString() });
  const { access_token, expires_in } = await resp.json(); return access_token;
}
const pool = new pg.Pool({ host: PGHOST, database: PGDATABASE, port: 5432,
  ssl: { rejectUnauthorized:false }, user: PGUSER, password: await getOAuthToken(), max: 10 });
```

Start the HTTP listener FIRST, then boot the DB in the background so a DB failure never blocks
serving. Expose `/health` returning `{ status, db, lakebase }`.

## Deploy — DABs bundle (recommended)

`databricks.yml` provisions the workspace resources and (optionally) the app:

```yaml
bundle: { name: <app>-bundle }
variables:
  catalog: { default: <catalog> }
  schema:  { default: <schema> }
resources:
  schemas: { demo_schema: { catalog_name: ${var.catalog}, name: ${var.schema} } }
  volumes: { raw_data:  { catalog_name: ${var.catalog}, schema_name: ${var.schema}, name: raw_data, volume_type: MANAGED } }
  jobs:    { setup: { tasks: [ { notebook_task: { notebook_path: ./data_generation/generate_data.py }, environment_key: sdk_default } ], environments: [ { environment_key: sdk_default, spec: { client: "4", dependencies: [numpy, pandas, faker] } } ] } }
  # optionally: apps, pipelines, dashboards
sync: { exclude: [ "**/.env", app/.env, .databricks/** ] }
targets:
  dev:  { default: true, workspace: { host: <host>, root_path: /Workspace/Shared/<app> } }
  prod: { mode: production, workspace: { host: <host>, root_path: /Workspace/Shared/<app> } }
```

- `databricks bundle deploy` → resources; `databricks bundle run <setup-job>` → generate data.
- Don't use `mode: development` on a `/Workspace/Shared/...` root (that mode requires a per-user path).
- Never auto-select a `.databrickscfg` profile — pass `--profile <name>`.

## Deploy — scripted (the app's own scripts)

`scripts/lakebase_setup_db.sh --db-name <name> [--project-id <id>] [--branch-id <id>]` — idempotent:
ensures a Lakebase project + branch + endpoint + database exist (auto-falls-back across shared
projects when one is full), prints the resource paths the app's `postgres` binding needs.

`scripts/deploy.sh` — idempotent end-to-end: rebuild `dist/`, load `.env`, upload source, `databricks
apps create` (skip if exists), `databricks apps deploy` (applies `app.yaml` scopes incl.
model-serving), wait for the app's Postgres SP role, reassign stale prior-SP ownership + GRANT, start
the app, print URL + log-tail. It recognizes common failures (apps quota, name taken,
permission-denied) and prints an actionable message. Guards against deploying over reserved app
names.

## `.env` (local dev) — the classic confusions to prevent

- `LAKEBASE_ENDPOINT` is a **resource path** (`projects/<id>/branches/<id>/endpoints/<id>`); `PGHOST`
  is a **DNS hostname** (`*.database.…cloud.databricks.com`). Do not swap them; `PGHOST` must not
  contain a port (use `PGPORT`).
- Lakebase uses **OAuth**, not password auth — don't put a static PG password in `.env`.
- `DATABRICKS_HOST` needs a scheme; the server force-normalizes it at module load anyway.
- Don't put `DATABRICKS_CONFIG_FILE`/`_PROFILE` in `.env` (the launcher injects them; process env
  wins) — it's confusing and brittle.
- Validate `.env` at startup with greppable, actionable errors (unreplaced `<placeholders>`, host
  format, endpoint-vs-host mixups).
