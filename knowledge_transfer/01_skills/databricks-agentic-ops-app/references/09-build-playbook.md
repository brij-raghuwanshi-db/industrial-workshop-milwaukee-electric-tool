# 09 — Build Playbook

Order of operations, the "ships working vs you build" layering, acceptance checks per layer, and the
gotchas register. Build a **vertical slice first** (one record, one action, end-to-end) before
widening horizontally (more pages, more tools, more charts).

## Order of operations

```
0. Foundation (ref 08): data → SDP gold → metric view → [heuristic recommendations] → Genie space.
   Acceptance: gold tables populated; Genie answers the headline question; metric-view measures match.

1. Lakebase (ref 04): provision project/branch/endpoint/db; model schema.ts (mirrors + writable
   actions + chat state); wire app.yaml lakebase resource; sync.ts (Delta→Lakebase); migrate on boot.
   Acceptance: app boots; `SELECT count(*)` on the mirror > 0; the writable table exists + empty.

2. Backend skeleton (ref 02): createApp + 3 plugins; migration gate; config load+validate; OBO auth;
   MLflow experiment bootstrap; register routes.
   Acceptance: `/api/config`, `/api/me` respond during boot; `/api/records`, `/api/kpis` return rows
   after init; a bad config fails fast with a clear message.

3. Layer 1 — Visualize (ref 05): Home + Panel pages; KPI cards; queue table; scatter/map; search box;
   detail drawer. Wire the `dataMutated` subscribe on every data view.
   Acceptance: the queue renders the at-risk records with the red cluster; KPIs match the dashboard.

4. Agent loop + ask_data (ref 03, 06): pick runner style; configure the model endpoint; register the
   ask_data backend (Genie or MAS) from config; SSE → chat dock; MLflow per-turn span.
   Acceptance: ask "why is <hero> flagged?" → the Thinking panel shows the ask_data investigation and
   a synthesized answer streams in; the turn is traced in MLflow.

5. Layer 2 — Assist (ref 03, 06): implement find_record, rank_actions (real-time model + cached
   fallback), what_if, search_providers, get_capacity. Encode the 3-phase system prompt.
   Acceptance: "rank the action for <hero>, can we absorb it?" → all options quoted with benefit +
   net value + capacity fit; recommends the top one with a reason; drafts a summary; STOPS.

6. Layer 3 — Act (ref 03, 04): implement execute_action/approve_action as one transaction (status,
   OBO approver, append-only audit); return the truth; emit dataMutated on turn-end.
   Acceptance: "yes, approve" → the write lands; the queue cascades LIVE (KPI −1, row flips, exposure
   drops, drawer Activity gains the action) with no reload.

7. Layer 4 — Govern (ref 06): route agentModel through an AI-Gateway endpoint (spend cap, guardrails,
   inference logging); declare the ai-gateway scope.
   Acceptance: the agent still answers; the gateway inference-log UC table has one row per call, the
   cap is enforced, and calls attribute to the record/operator/action.

8. Analytics + Dashboard + Ops (ref 05): warehouse chart routes; unit-economics P&L; embedded AI/BI
   iframe; app health-score page.
   Acceptance: charts render; the dashboard iframe loads under SSO; the health score reflects real
   component status.

9. Deploy (ref 07): DABs bundle OR deploy.sh; verify OBO identity, Lakebase read_write, model +
   genie scopes; smoke-test the full arc on the deployed URL.
```

## "Ships working vs you build" (if starting from a bootstrap)

A sane bootstrap ships the **plumbing** working (routing, OBO auth, MLflow tracing, SSE, chat dock),
**Layer 1 — Visualize** (the queue reading Lakebase), and the **agent loop + a working ask_data**.
It leaves the domain tools as registered stubs that throw "Not implemented" (so the model + tool
list know they exist) and the write path unwired. You implement, in order: the Assist tools (2), the
Act write (3), and the Gateway governance (4). This lets the app boot and demo the Visualize story
from day one while the higher layers land incrementally.

## Vertical-slice discipline

- Get **one record → one recommendation → one approved write → one live cascade** working before
  adding a second page, a second chart, or a fifth tool.
- Prove the `dataMutated` cascade early — it's the highest-risk, highest-payoff behavior.
- Keep the model call behind a cached-table fallback from the start so the demo never dead-ends on a
  cold/broken endpoint.

## Gotchas register (symptom → cause → fix)

| Symptom | Cause | Fix |
|---|---|---|
| Every chat turn returns empty / dies moments after send | Aborting on `req` `'close'` (fires when the small JSON body is consumed) | Bind the abort to **`res` `'close'`**, not `req` |
| "400 status code (no body)" in the chat bubble | OpenAI SDK strips the response body before throwing | Install a fetch shim capturing the body to `ctx.modelError`; prefer it in the error message |
| Responses API 502 "invalid response from upstream" | An assistant history item sent as a bare string, or an empty `output_text` | Map assistant messages to `[{type:'output_text', text}]`; drop empty-content rows before sending |
| Model 400 BAD_REQUEST on the agent route | The endpoint isn't Responses-API capable (e.g. a Claude/non-Responses model) | Use a serving endpoint with `openai/v1/responses` enabled; use the exact endpoint name |
| Tool schema rejected by the SDK | Used `.optional()` (SDK ships `strict:true`, every field must be required) | Use `.nullable()` instead; `.describe()` every field; keep `snake_case` names |
| "No trace ID found for span lakebase.query. Skipping." every query | Lakebase pool auto-creates OTel spans; queries outside a withSpan have no parent | Wrap the agent turn in `mlflow.withSpan(...AGENT...)` so DB spans are adopted; silence the specific warn for non-agent queries |
| Chat "View trace" stuck on "Trace pending…" forever | No MLflow experiment path resolved | Set `agentMlflowExperimentPath` or rely on the `DATABRICKS_APP_NAME` derivation; ensure the SP has CAN_EDIT on the parent folder |
| MLflow "cannot configure default credentials" on trace upload | Bundled MLflow SDK resolves the default `~/.databrickscfg`, ignores the app's config file | Pass explicit `host` + `databricksToken` (from the authenticated header) to `mlflow.init` |
| App boots but the Panel is empty | Sync skipped (no warehouse/creds) or a source gold table missing | Verify `DATABRICKS_WAREHOUSE_ID` + creds; catch `TABLE_OR_VIEW_NOT_FOUND` and leave that mirror empty so the app still boots |
| Write happens but the UI doesn't update | `dataMutated` not emitted on turn-end, or the write didn't commit | Confirm the runner sets `dataMutated:true` and the client emits on `done`; confirm the transaction committed |
| App can't write to Lakebase | UC-synced table is read-only in Postgres, or the lakebase resource is `read` only | Write only the **separate writable table**; set the `lakebase` resource `permission: read_write` |
| `PGHOST` / `LAKEBASE_ENDPOINT` confusion at boot | Swapped a DNS host with a resource path | `PGHOST` = DNS hostname (no port); `LAKEBASE_ENDPOINT` = `projects/…/branches/…/endpoints/…` |
| `DATABRICKS_APP_PORT` ignored / preview stuck "Booting" | `.env` overwrote the launcher-injected port | Strip `DATABRICKS_APP_PORT` from `.env` before sourcing when the launcher injected it |
| Terminal floods on a bulk-insert failure | Drizzle stuffs the full SQL + every param into `err.message` | Compact error logger: truncate hard, extract pg code/constraint/detail, ≤12 stack frames |
| Agent loops discover→act forever | System prompt doesn't say "STOP after an action" | Add the explicit "after an action, STOP and wait; don't auto-advance" rule |
| Genie tool returns "query failed" with no detail | Not surfacing Genie's `error` object on FAILED/CANCELLED | Read `error.error`/`error.type` from the poll response and return it |
| Deploy fails: name reserved / quota / permission | Reused a reserved app name, apps quota hit, or missing role | The deploy script recognizes these — pick a new `APP_NAME`, free a slot, or fix the profile's Apps role; preview works without a deploy |
| OpenAI client 404/400 on every agent call | `baseURL` includes the model + `/invocations` | `baseURL` is the `/serving-endpoints` ROOT; pass the endpoint name as the `model` param (see 10) |
| `POST /api/2.0/…/assessments` 404 | Old MLflow assessments API version | Use **`/api/3.0/mlflow/traces/{id}/assessments`** with `feedback:{name,value}` + `source.source_type:'HUMAN'` (see 10) |
| `SELECT` on a synced table → permission denied | App SP has `CAN_CONNECT_AND_CREATE` but not `pg_read_all_data` | Project owner grants the SP read on the synced table, OR use the one-shot copy into an app-owned table (see 04/10) |
| Hand-rolled `pg.Pool` dies after ~1h | Lakebase OAuth token expired, not refreshed | Use `appkit.lakebase.query()` (auto-refresh); if manual, cache the token with a 60s buffer + refresh on 401 (see 10) |
| Invented AppKit signature fails `validate` | Guessed API shape from memory | Run `npx @databricks/appkit docs` + `databricks apps manifest`; scaffold via `databricks apps init` (see 07/10) |

## Definition of done

- The full arc runs on the deployed URL: open Panel → see the cluster → ask why → get the ranked
  recommendation with the capacity tradeoff → approve → the queue cascades live.
- Every model call is traced (MLflow) and governed (AI Gateway inference log shows the calls, cap
  enforced); writes are OBO-attributed with an audit trail.
- The app boots even when a source table or the model endpoint is missing (degrades, doesn't crash),
  and surfaces real failures visibly instead of silent empty turns.
- Reset-demo returns the app to baseline.
