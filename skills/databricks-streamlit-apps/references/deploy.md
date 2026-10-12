# Deploy + verify

Two files govern deployment: **`app.yaml`** (runtime: start command + env) and **`databricks.yml`**
(DAB: the app resource + its bound resources). You need BOTH. Copy the templates and fill in ids.

## `app.yaml` — runtime (the shell-wrap is mandatory)
```yaml
command:
  - bash
  - -c
  - streamlit run app.py --server.port ${DATABRICKS_APP_PORT:-8000} --server.address 0.0.0.0 --server.headless true
env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse
  - name: DATABRICKS_GENIE_SPACE_ID
    valueFrom: genie-space
  - name: LAKEBASE_ENDPOINT
    valueFrom: postgres
  - name: DATABRICKS_SERVING_ENDPOINT_NAME
    valueFrom: serving-endpoint
```
- **`bash -c`** so `${DATABRICKS_APP_PORT}` expands — the array form is exec'd without a shell (the #1
  crash). `${VAR:-8000}` gives a local fallback.
- `valueFrom: <resource-name>` injects the resource's identifier as that env var at runtime. The name
  must match a resource `name:` in `databricks.yml`.

## `databricks.yml` — the bundle + resources
```yaml
bundle:
  name: my-app
sync:
  exclude:                       # keep the deploy lean — never upload the venv
    - ".venv/**"
    - "**/__pycache__/**"
    - "*.pyc"
variables:
  sql_warehouse_id: {description: SQL Warehouse ID}
  genie_space_id: {description: Genie Space ID}
  genie_space_name: {description: Genie Space display name}
  postgres_branch: {description: Lakebase branch resource path}
  postgres_database: {description: Lakebase database resource path}
  serving_endpoint_name: {description: LLM serving endpoint}
resources:
  apps:
    app:
      name: "my-app"                       # ≤26 chars, lowercase/digits/hyphens, no underscores
      source_code_path: ./
      user_api_scopes: [dashboards.genie]  # only if using Genie/OBO scopes
      resources:
        - {name: sql-warehouse, sql_warehouse: {id: "${var.sql_warehouse_id}", permission: CAN_USE}}
        - {name: genie-space,  genie_space: {name: "${var.genie_space_name}", space_id: "${var.genie_space_id}", permission: CAN_RUN}}
        - {name: postgres,     postgres: {branch: "${var.postgres_branch}", database: "${var.postgres_database}", permission: CAN_CONNECT_AND_CREATE}}
        - {name: serving-endpoint, serving_endpoint: {name: "${var.serving_endpoint_name}", permission: CAN_QUERY}}
targets:
  default:
    default: true
    workspace: {host: https://<workspace-host>}
    variables:
      sql_warehouse_id: <id>
      genie_space_id: <id>
      genie_space_name: <display name>     # genie_space needs BOTH id and name or validate warns
      postgres_branch: projects/<p>/branches/<b>
      postgres_database: projects/<p>/branches/<b>/databases/<db>
      serving_endpoint_name: <endpoint>
```
- **Declare every resource with a `permission:`** → the platform auto-grants the app SP on deploy. This is
  how the SP gets CAN_USE/CAN_QUERY/CAN_CONNECT without manual grants.
- App name: ≤26 chars, lowercase letters/digits/hyphens (no underscores).

## Deploy sequence
```bash
databricks bundle validate --profile <p>          # fix warnings (e.g. genie_space needs name)
databricks bundle deploy   --profile <p>          # uploads code + creates app + binds resources
# a brand-new app's compute may be stopped:
databricks apps start  my-app --profile <p>       # wait until app_status/compute ACTIVE
databricks apps deploy my-app \
  --source-code-path /Workspace/Users/<you>/.bundle/my-app/default/files --profile <p>
```
- `bundle deploy` uploads + binds but may leave the app not-RUNNING on first create → `apps start` then
  `apps deploy`. `apps deploy` installs `requirements.txt`, uploads the snapshot, and starts the process.
- If `bundle deploy` throws `failed to update app's compute size … try again later` — transient; re-run.

## SP grants — TWO kinds, don't conflate them
1. **Resource grants (auto).** Declaring a resource with `permission:` auto-grants the app SP on the
   warehouse / serving endpoint / genie space / lakebase database. No manual step.
2. **Unity Catalog data grants (NOT auto).** SELECT/USE on the *tables* a warehouse query or Genie reads
   is a separate UC grant. The `CAN_USE` on the warehouse lets the SP run queries; it does NOT grant
   access to the data. A **brand-new app has its OWN service principal** — even if you granted a *previous*
   app's SP, the new one needs its own grants:
   ```sql
   GRANT USE CATALOG ON CATALOG <cat>                 TO `<new-sp-client-id>`;
   GRANT USE SCHEMA  ON SCHEMA  <cat>.<schema>         TO `<new-sp-client-id>`;
   GRANT SELECT      ON SCHEMA  <cat>.<schema>         TO `<new-sp-client-id>`;  -- or per-table
   ```
   Get the id from `databricks apps get <name>` → `service_principal_client_id`. **If you lack MANAGE on
   the catalog, you cannot self-serve — an owner/metastore admin runs it.** So: design catalog-dependent
   features (ai_forecast charts, Genie) to **degrade gracefully** (warehouse helper returns `[]` → the UI
   shows "unavailable") so the rest of the app (Lakebase-backed queue, KPIs, search, write-back, LLM
   explain via the shared serving endpoint) ships and works while the grant is pending.
3. **Lakebase schema grants.** `CAN_CONNECT_AND_CREATE` lets the SP create+own new schemas, but NOT read
   schemas someone else owns. If the app reads an existing/forked schema, grant its SP explicitly — see
   `lakebase-connectivity.md` §"Owning / forking a schema". If the app creates its own schema at startup,
   deploy-first so the SP owns it.

**Two apps ≠ shared identity.** When you fork an app (e.g. a Streamlit twin of a React app), it gets a
NEW SP. Re-run BOTH the Lakebase grants (on its schema) AND the UC catalog grants (on the source tables)
for the new SP — the old app's grants do not transfer.

## Verify live
```bash
databricks apps get  my-app --profile <p> -o json   # app_status.state == RUNNING, compute ACTIVE, note .url
databricks apps logs my-app --tail-lines 100 --profile <p>   # past [BUILD] pip lines: a clean Streamlit
                                                             #   "You can now view your Streamlit app", no traceback
TOK=$(databricks auth token --profile <p> -o json | jq -r .access_token)
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOK" "<url>/"   # expect 200
```
- The UI is behind SSO — a headless screenshot hits the login wall (expected). To prove the DATA works as
  the deployed SP, run the exact queries via psql (Lakebase) / CLI (warehouse) as shown in the other refs.
- `apps logs` needs OAuth (not PAT). Use `apps get` for status if on PAT.

## Local dev
`pip install -r requirements.txt` (Python 3.11/3.12 to match the Apps runtime) → `streamlit run app.py`
with a profile in the env (`DATABRICKS_CONFIG_PROFILE=<name>`). Needs egress to PyPI + the workspace. If
your environment blocks PyPI, skip local run and verify via the data-layer checks + deploy (that's how the
reference app was validated).
