# 10 — Verification & Fallbacks (don't loop endlessly)

Platform APIs drift. This file records what was **verified against live Databricks docs/skills**,
the exact API shapes, and — for each fragile integration — a **fallback ladder** so a build degrades
to a working state instead of retrying a broken call forever. When a pattern in this skill fights
the live platform, **trust the live source, apply the fallback, and move on.**

## How to re-verify before building (run these first)

| To confirm… | Authoritative source (run/read this) |
|---|---|
| AppKit API signatures (`createApp`, plugin shapes, `lakebase.query`, hooks) | `npx @databricks/appkit docs` then `npx @databricks/appkit docs <section>` |
| Plugin names, resource keys, `--set` fields for your workspace's AppKit | `databricks apps manifest --profile <P>` |
| Whether the code compiles against the installed AppKit | `databricks apps validate --profile <P>` (tsc --noEmit + lint) |
| Lakebase project/branch/database/endpoint resource names | `databricks postgres list-projects|list-branches|list-databases|get-endpoint` |
| Genie space + serialized shape | `databricks genie list-spaces` / `get-space <id> --include-serialized-space` |
| A serving endpoint exists + its name | `databricks serving-endpoints list` |
| Any REST surface below | the `databricks-docs` skill → fetch `https://docs.databricks.com/llms.txt`, then the specific page |

## Verified API shapes (as of this skill's authoring)

### Genie Conversation API ✓ (paths exact)
- `POST /api/2.0/genie/spaces/{space_id}/start-conversation` → `{ conversation_id, message_id }`
- `GET  /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}`
- **status enum:** in-flight `SUBMITTED|FETCHING_METADATA|FILTERING_CONTEXT|ASKING_AI|PENDING_WAREHOUSE|EXECUTING_QUERY`;
  terminal `COMPLETED|FAILED|CANCELLED|QUERY_RESULT_EXPIRED`. Poll until terminal.
- **attachments[]:** `text.content` + `text.purpose` (`TEXT_ATTACHMENT_PURPOSE_ANSWER`/`FOLLOW_UP_QUESTION`);
  `query.{title,query,description,statement_id,query_result_metadata.row_count/is_truncated,thoughts[]}`.
  Full rows via the Statement Execution API using `query.statement_id`.

### MLflow trace assessments ✓ (version bumped)
- **`POST /api/3.0/mlflow/traces/{trace_id}/assessments`** (was 2.0 — use **3.0**).
- Body: `{ feedback:{ name, value }, rationale?, source:{ source_type:'HUMAN', source_id }, metadata? }`.
- Prefer the MLflow helper `mlflow.log_feedback` / `log_assessment` (`AssessmentSourceType.HUMAN`).

### Model serving invocation ✓
- Custom/ML model: `POST /serving-endpoints/{name}/invocations` with `{ dataframe_records:[...] }`
  (also accepts `dataframe_split` / `inputs` / `instances`) → `{ predictions:[...] }`.
- Foundation model via OpenAI client: `baseURL = ${host}/serving-endpoints` (root!), pass the
  **endpoint name as `model`**. Gateway route alt: `baseURL = ${host}/ai-gateway/mlflow/v1`, model
  `system.ai.<name>`. Responses API requires an endpoint that supports it.

### Unity AI Gateway ✓ (name + features)
- Called **Unity AI Gateway** (built on Unity Catalog). Confirmed features: **rate limits / spend
  caps / budgets**, **guardrails** (service policies: PII/safety, built-in + custom), **inference
  logging** to UC Delta tables (audit requests/responses). Attach via a service policy on the
  endpoint. Migration note: gateway routes may need an `ai-gateway`-scoped token and the
  fully-qualified `system.ai.<model>` name.

### Lakebase access ✓ (use the plugin)
- First-class: `appkit.lakebase.query(sql, params)` — plugin owns pool + OAuth refresh. Env
  auto-injected when the `postgres` resource is declared; only `LAKEBASE_ENDPOINT` is set explicitly
  (`valueFrom: postgres`).
- Synced tables (`databricks postgres create-synced-table`) are **read-only**, owned by a system
  role; the app SP needs an **explicit read grant** (it has `CAN_CONNECT_AND_CREATE`, not
  `pg_read_all_data`). They do **not** propagate UC row/column FGAC — if that matters, serve via DBSQL
  with user authorization instead.

### Two-plane model & separate writable table ✓
- Confirmed by the official AppKit Lakebase guide: read synced/mirrored tables, **write to a
  separate app-owned table** ("direct writes corrupt the sync state"). This skill's core invariant
  holds.

## Fallback ladders (degrade, don't loop)

Each integration: try the primary; on repeated failure, drop to the next rung. **Cap retries at 2**
and log which rung you landed on — never retry the same failing call endlessly.

- **Lakebase connection:** `appkit.lakebase.query` → (non-AppKit) `pg.Pool` with self-minted OAuth
  JWT (cache 60s buffer, refresh on 401) → local dev PG env from `databricks postgres get-endpoint`.
- **Reading gold into the app:** Lakebase synced table (+ SP read grant) → one-shot SQL-Statements-API
  copy into an app-owned table (§04) → skip the mirror and query the SQL warehouse directly for that
  view (slower, but unblocks). If the source gold table is missing, **catch `TABLE_OR_VIEW_NOT_FOUND`
  and leave the mirror empty** so the app still boots.
- **`ask_data` backend:** Genie space (poll) → MAS endpoint (stream) → a plain warehouse SQL route
  with canned aggregate queries (the app still answers "how many / average / exposure" without NL).
- **`rank_actions` scoring:** real-time model-serving call → cached `*_recommendations` mirror (batch
  scores) → pipeline heuristic table (rank by `benefit×value − cost − penalty`). All three write the
  *same* table shape, so the tool/UI never changes. **The app must work with zero ML** (heuristic).
- **Agent model / Responses API:** if the endpoint 400s on `/responses`, fall back to the hand-rolled
  **chat-completions tool loop** (§03 Style B) which works on any tool-calling chat model.
- **MLflow assessment:** `/api/3.0/...assessments` → if 404, try the MLflow SDK helper → if that
  fails, keep only the local `feedback` row (never block the turn on telemetry).
- **AI Gateway governance:** gateway-fronted endpoint → plain serving endpoint + app-side spend
  guard (the system-prompt "no unbounded reads" rule + a per-session call cap) as an interim.
- **Deploy:** `databricks apps deploy` → if apps quota/permission blocks it, run via the **Preview**
  button (no deploy needed) and note it; don't retry-loop the deploy.

## Standing rule

Prefer **managed/declarative Databricks capabilities** (AppKit plugins, synced tables, metric views,
AI Gateway, the pipeline heuristic) over hand-rolled equivalents. The hand-rolled versions in this
skill exist so the app still runs when a managed capability isn't provisioned — they are fallbacks,
not the target. Always leave a `console`/log breadcrumb naming which rung you're on so the operator
can see the degraded path.
