# 06 — Platform Integrations

How the app reaches each Databricks platform capability. All outbound calls use the OBO/SDK auth
header from `authHeaders(req)` (prod) or a self-minted OAuth token (manual boot).

## A. Genie (natural-language → SQL over the governed lakehouse)

Genie is the `ask_data` "why" backend. Its REST API is **poll-based** (no native streaming): start a
conversation, then poll the message until terminal.

```ts
// 1. start
POST /api/2.0/genie/spaces/{spaceId}/start-conversation   body: { content: question }
   → { conversation_id, message_id }
// 2. poll (2s interval; overall budget ~5 min = 150 × 2s; per-poll fetch capped 30s)
GET  /api/2.0/genie/spaces/{spaceId}/conversations/{conversation_id}/messages/{message_id}
   → { status, attachments[], error? }
```

- `status` (VERIFIED enum, see 10): the in-flight states are `SUBMITTED`, `FETCHING_METADATA`,
  `FILTERING_CONTEXT`, `ASKING_AI`, `PENDING_WAREHOUSE`, `EXECUTING_QUERY`; the terminal states are
  `COMPLETED`, `FAILED`, `CANCELLED`, `QUERY_RESULT_EXPIRED`. **Poll until a terminal state** — don't
  early-exit on `EXECUTING_QUERY` expecting text, and treat `QUERY_RESULT_EXPIRED` as terminal too.
- Collect `attachments[].text.content` + `attachments[].query.description` as the answer; also
  surface `attachments[].query.query` (the SQL it ran), `attachments[].query.statement_id` (to fetch
  full rows via the Statement Execution API), and any `attachments[].query.thoughts[]`
  (step-by-step reasoning — fold into the Thinking panel *before* the final answer). Text
  attachments carry `text.purpose` (`TEXT_ATTACHMENT_PURPOSE_ANSWER` vs `FOLLOW_UP_QUESTION`).
- On `FAILED`/`CANCELLED`, surface Genie's actual `error.error`/`error.type` (missing table,
  permission denied, ambiguous SQL) — not a generic "query failed".
- Emit a one-shot narration ("Querying Genie: …") while polling so the Thinking panel shows activity
  instead of dead air.
- Treat per-poll timeouts/network blips as transient (log + continue); the overall budget bounds the
  loop.

## B. MAS (Multi-Agent Supervisor) — alternative `ask_data` backend

A Mosaic Agent Framework supervisor that routes between sub-agents (data_analyst→Genie,
incident_expert→retrieval, …) and returns a synthesized answer. **Streaming** via
`POST /serving-endpoints/{name}/invocations` with `{ input:[{role:'user',content}],
databricks_options:{return_trace:true}, stream:true }`, `Accept: text/event-stream`.

Parse the SSE stream: `response.output_text.delta` (accumulate as fallback answer),
`response.output_item.done` items — `message` with a `<name>x</name>` tag (routes the next message to
sub-agent x), step-tagged `message` (supervisor narration; latest wins as final answer),
`function_call` (delegation — emit a tool_call event with the query), `function_call_output` (pair to
its call_id). `response.completed` carries `databricks_output.trace.info.trace_id`. Cap at ~10 min so
a stuck sub-agent can't wedge the turn; release the reader in `finally`.

## C. Model serving (real-time scoring — the `rank_actions` tool)

Call a UC-registered model's serving endpoint to score candidate actions in real time.

```ts
POST https://{host}/serving-endpoints/{model-endpoint}/invocations
  headers: { Authorization: Bearer {token}, 'Content-Type':'application/json' }
  body: { dataframe_records: [ /* one row per candidate action */
    { risk_at_intervention, days_since_discharge, coordinator_hours, severity_weight,
      has_open_followup, has_open_med_recon,
      is_<action_a>, is_<action_b>, is_<action_c> /* one-hot the candidate action */ } ] }
  → { predictions: [<benefit>, ...] }  // or { outputs: [...] }
```

Then compute **net value** = `predicted_benefit × unit_value − cost − capacity_penalty`, sort
descending, mark `fits_capacity` per option, and return the ranking (recommended + all options for
the what-if). **Always ship a cached-table fallback**: if the endpoint errors, read the batch-scored
`action_recommendations` mirror instead so the tool still answers (tag `scoring_method` so the UI
can show real-time vs cached). Keep the feature vector construction identical between `rank_actions`
and `what_if` so numbers are consistent.

## D. Unity AI Gateway (govern the agent's model calls)

Route the agent's model endpoint through an **AI Gateway**-fronted serving endpoint to get:
- **Spend cap** (usage/rate limit — the "AI spend bounded on thin margins" story), e.g. N calls/min
  or an annual $ ceiling.
- **Guardrails** — safety + PII/PHI blocking + optional custom guardrail functions (e.g. a
  `block_unbounded_data_read` function that refuses "dump everything" prompts at the gateway layer,
  complementing the system-prompt guardrail).
- **Inference logging** to a UC table — one row per model call.

Wiring: point `config/app.json` `agentModel` at the gateway-governed endpoint name; declare the
`ai-gateway` OBO scope in `app.yaml`. **Per-call attribution:** every write is OBO-stamped
(`approved_by`) and every turn is traced in MLflow; join the gateway's inference-log UC table with
`actions.record_id`/`approved_by`/`action_type` to attribute spend per record / operator / action
type. Optionally surface an "AI spend by action" panel deep-linking to the gateway usage dashboard.

## E. Embedded AI/BI dashboard

The `/dashboard` page embeds the managed Lakeview dashboard in an iframe (SSO — the operator's
session authenticates it). Compose the URL from `DATABRICKS_HOST` + `dashboard_id`
(`/sql/dashboardsv3/{id}`). This gives the governed, drill-down analytics surface without
rebuilding it in the app — the app owns the *interactive/action* surface, the dashboard owns the
*exploratory* one.

## F. Lakebase full-text / BM25 / hybrid search

In-Postgres search (no external service) — see [04-lakebase-data-model.md](04-lakebase-data-model.md)
for the SQL. Used by `search_records` (find records by NL) and `search_providers` (find a program for
a referral). Prefix-aware (`word:*`), ranked (`ts_rank`/`parserrank`), highlighted (`ts_headline`),
with an ILIKE fallback.

## G. AI functions (batch enrichment, upstream of the app)

The gold tables the app reads can be enriched with SQL AI functions during the pipeline — e.g.
`ai_classify` to turn free-text operator notes into a `risk_signal_score` (0–1) that the panel row
displays. This is a **pipeline** capability (see [08-data-ml-foundation.md](08-data-ml-foundation.md)),
surfaced in the app as a mirrored column — the app doesn't call it live.

## Auth token minting (manual-boot path)

When not using the AppKit SDK chain, mint an OAuth M2M token for outbound calls:

```ts
POST {host}/oidc/v1/token
  Content-Type: application/x-www-form-urlencoded
  grant_type=client_credentials&client_id={id}&client_secret={secret}&scope=all-apis
  → { access_token, expires_in }
```

Cache it with a 60s expiry buffer; refresh on demand. This same JWT is used **directly as the
Postgres password** for the Lakebase pool (Lakebase OAuth) — see [07-config-deploy-auth.md](07-config-deploy-auth.md).
