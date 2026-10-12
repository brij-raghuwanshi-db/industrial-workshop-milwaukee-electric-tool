---
name: databricks-streamlit-apps
description: >
  Ground-truth fast path for building a Streamlit app on Databricks Apps right the FIRST time —
  from scratch. Use whenever building/deploying a Streamlit (or other non-AppKit Python) app on the
  Databricks Apps platform: reading a SQL warehouse, calling a model-serving LLM, connecting to
  Lakebase Postgres, wiring Genie, OBO user identity, and DABs deploy. Complements (does not replace)
  the databricks-apps + databricks-lakebase + databricks-genie-agents plugin skills — read those for
  the platform rules; THIS skill encodes the concrete Streamlit build recipe + a symptom→fix register
  learned by shipping a real one. Load it, then pull the matching reference file.
---

# Databricks Streamlit Apps — Fast Path

Built after shipping a full operational Streamlit app on Databricks Apps (a queue → click-to-explain
with a live-streaming LLM + deterministic fallback → forecast → what-if → approve → Lakebase write with
audit + simulated external push → analytics + Genie). This skill exists so the next agent builds it in
**one clean pass**, not by rediscovering the same handful of platform gotchas.

It complements the plugin skills — **`databricks-core`** (auth/profile/data discovery),
**`databricks-apps`** (platform rules, `references/other-frameworks.md`, `references/platform-guide.md`),
**`databricks-lakebase`** (Postgres provisioning/connectivity), **`databricks-genie-agents`** (Genie API).
Load those for depth; this skill is the recipe that ties them together for Streamlit specifically.

## The Iron Rules (every failure we hit broke one of these)

1. **Wrap the start command in a shell.** Databricks Apps exec's the `app.yaml` `command:` array
   **directly — no shell**, so `${DATABRICKS_APP_PORT}` is passed to Streamlit *literally* and the app
   crashes with `'${DATABRICKS_APP_PORT:-8000}' is not a valid integer`. Use
   `command: [bash, -c, "streamlit run app.py --server.port ${DATABRICKS_APP_PORT:-8000} --server.address 0.0.0.0 …"]`.
   This is the #1 Streamlit-on-Apps crash.
2. **Bind host `0.0.0.0` and the injected `$DATABRICKS_APP_PORT`.** Hardcoding `8080`/`localhost` → 502.
3. **Never hand-roll auth.** In a deployed app `WorkspaceClient()` / `Config()` pick up the service
   principal automatically. There is NO `DATABRICKS_TOKEN`. For per-user identity use OBO headers
   (below), not a token.
4. **Lakebase password = a short-lived OAuth token, not a secret.** Mint via the **Autoscaling** REST
   call `POST /api/2.0/postgres/credentials` body `{"endpoint": "<endpoint-path>"}` — NOT the SDK's
   `w.database.generate_database_credential` (that's the legacy Provisioned API and 404s the Autoscaling
   endpoint with "Database instance … not found"). Cache ~55 min, refresh on expiry / dropped connection.
   SSL required. (See `references/lakebase-connectivity.md`.)
5. **Declare every resource in `databricks.yml` with a `permission:`** — the platform auto-grants the
   app's SP on the RESOURCE (warehouse/serving/lakebase/genie). But **Unity Catalog SELECT/USE on the
   tables a warehouse query or Genie reads is NOT auto-granted** — a NEW app has its OWN SP that needs
   its own catalog grants; if you lack MANAGE, an owner must run them. Design catalog-dependent features
   (forecast, Genie) to degrade gracefully while the grant is pending. (See `references/deploy.md`.)
6. **Exclude the venv from bundle sync from the very first deploy** (`sync.exclude` + `.gitignore`), or
   the first deploy uploads thousands of dependency files.
7. **`st.dataframe` has no whole-row click.** Row-select fires only on the left-edge checkbox; a cell
   click does nothing. Give an explicit `selectbox` + `st.button("Analyze ▸")` to open a detail
   `@st.dialog`; keep the checkbox as a bonus path. (See `references/ui-patterns.md`.)
7. **Deploy-first for Lakebase writes.** The app SP must OWN (or be granted on) the schema it writes.
   If you dev locally first, your user creds own the schema and the deployed SP hits `permission denied`.
   Either deploy first, or (cleaner) create + grant the schema explicitly to the SP up front.

## The build loop (do in order, every time)

1. **Discover** — `databricks-core`: pick the profile (`--profile <name>`, never auto-select), find the
   warehouse (`databricks warehouses list`), the Lakebase project/branch/endpoint/db
   (`databricks postgres list-*` / `get-endpoint`), the Genie space (`databricks genie list-spaces`),
   the serving endpoint (`databricks serving-endpoints list` → pick a READY `llm/v1/chat` model). Profile
   the tables you'll read (`discover-schema`). Write the fully-qualified names down.
2. **Decide the data plane** (Decision Gate, `references/architecture.md`): warehouse SQL (dashboards,
   aggregations, `ai_forecast`) vs Lakebase (sub-second lookups, full-text search, write-back state).
   Most operational apps are BOTH — warehouse for the heavy read-only compute, Lakebase for interactive
   state + writes.
3. **Scaffold** the file tree (`references/project-structure.md`; copy `templates/`). One `lib/` module
   per concern (config, lakebase, warehouse, serving, domain, actions, identity, theme), thin `pages/`.
4. **Author `lib/` first, `pages/` last** — the data layer is the risk; get it connecting before any UI.
5. **Verify the SQL against the real backend BEFORE the UI** — run each query via `psql` (Lakebase) or
   the CLI (`databricks experimental aitools tools query`, warehouse). A page built on unverified SQL is
   a guess. (See `references/verification.md`.)
6. **Write `app.yaml` + `databricks.yml`** (`references/deploy.md`; copy `templates/`). Shell-wrapped
   command, `sync.exclude`, all resources with permissions.
7. **Deploy** — `databricks bundle deploy` (creates app + binds resources), then
   `databricks apps deploy <name>` (uploads code + starts). If the app isn't RUNNING yet,
   `databricks apps start <name>` first.
8. **Verify live** — `databricks apps get` (state RUNNING), `databricks apps logs --tail-lines` (clean
   Streamlit start, no traceback), HTTP 200. The UI itself sits behind SSO (headless screenshot hits the
   login wall — that's expected); verify the data layer as the deployed SP via psql/CLI.

## Reference routing

| When you're… | Read |
|---|---|
| Choosing warehouse vs Lakebase, laying out the two-plane architecture | `references/architecture.md` |
| Scaffolding the directory + `lib/`/`pages/` split | `references/project-structure.md` |
| Connecting to Lakebase (OAuth token, psycopg, refresh, transactions, schema fork) | `references/lakebase-connectivity.md` |
| Querying the warehouse / calling a serving LLM / streaming / Genie / OBO identity | `references/integrations.md` |
| Building the UI (KPIs, tables-as-clickable-rows, dialogs, charts, live cascade, required states) | `references/ui-patterns.md` |
| Writing `app.yaml` + `databricks.yml` + deploying + verifying | `references/deploy.md` |
| Anything breaks | `references/symptom-fix.md` (the register — check here FIRST when debugging) |

## Templates (copy, don't hand-invent)
`templates/` is a complete minimal app: `app.yaml`, `databricks.yml`, `requirements.txt`,
`.gitignore`, `app.py`, `lib/{config,lakebase,warehouse,serving,identity}.py`, `pages/1_Example.py`.
Copy the tree, rename, fill in your fully-qualified names + SQL. The connectivity + deploy plumbing is
the part that's hard to get right; the templates have it correct.

## Non-negotiables to carry through
- Respect the project's data-write boundary (read-only prod; writes only to the approved sandbox schema
  + Lakebase; simulate external writeback). If a governance guardrail exists, it OVERRIDES convenience.
- One writable table/schema owned by the app; read mirrors are read-only.
- Deterministic answer first, LLM as enhancement with graceful fallback — never hard-depend on the model.
