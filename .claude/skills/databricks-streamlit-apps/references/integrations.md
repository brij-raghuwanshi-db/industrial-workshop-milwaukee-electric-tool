# Integrations — warehouse SQL, model-serving LLM, streaming, Genie, OBO

All authenticate as the app's **service principal** automatically in a deployed app (or your profile
locally). Declare each as a resource in `databricks.yml` with the right `permission:` so the SP is
auto-granted on deploy.

## 1. SQL Warehouse (read-only heavy compute: aggregations, `ai_forecast`, Delta reads)
Use `databricks-sql-connector`. The SP credential provider comes from the SDK `Config`.
```python
from databricks import sql as dbsql
from databricks.sdk.core import Config
cfg = Config()   # SP when deployed, profile locally
def run_sql(q: str) -> list[dict]:
    with dbsql.connect(
        server_hostname=HOST.replace("https://",""),
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    ) as c, c.cursor() as cur:
        cur.execute(q)
        cols=[d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols,r)) for r in cur.fetchall()]
```
- Resource: `sql_warehouse` with `permission: CAN_USE`, env `DATABRICKS_WAREHOUSE_ID` `valueFrom: sql-warehouse`.
- `ai_forecast` example (forecast a per-key series forward):
```sql
SELECT CAST(ds AS STRING) ds, ROUND(y_forecast,0) y_forecast, ROUND(y_lower,0) y_lower, ROUND(y_upper,0) y_upper
FROM ai_forecast(
  TABLE(SELECT to_timestamp(week_start) AS ds, CAST(metric AS DOUBLE) AS y
        FROM catalog.schema.gold WHERE key='<id>' AND metric IS NOT NULL),
  horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y') ORDER BY ds
```
Verify the inner `TABLE(...)` returns rows before trusting the forecast. Warehouse queries take seconds —
fine for a drawer chart, wrong for a typeahead (use Lakebase for sub-second).

## 2. Model Serving (LLM chat)
Simplest path — the SDK's typed call:
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
def llm(system: str, user: str) -> str:
    w = WorkspaceClient()
    r = w.serving_endpoints.query(
        name=SERVING_ENDPOINT,   # a READY llm/v1/chat endpoint, e.g. databricks-claude-sonnet-4-5
        messages=[ChatMessage(role=ChatMessageRole.SYSTEM, content=system),
                  ChatMessage(role=ChatMessageRole.USER, content=user)],
        temperature=0.2, max_tokens=600)
    return r.choices[0].message.content or ""
```
- Resource: `serving_endpoint` with `permission: CAN_QUERY`, env `DATABRICKS_SERVING_ENDPOINT_NAME`
  `valueFrom: serving-endpoint`. Pick the endpoint from `databricks serving-endpoints list` (task
  `llm/v1/chat`, `ready=READY`). Foundation-model endpoints are workspace-shared, pay-per-token — there
  is no per-app copy.
- **Rules-first pattern (do this):** compute a deterministic answer from the real data as the GUARANTEED
  result; try the LLM as an enhancement; on any exception fall back to the deterministic one. Never let a
  feature hard-depend on the model. Offer an engine toggle (`Auto | LLM | Rules`) so the user can choose.
- **Structured output without brittle JSON-in-stream:** have the model write prose, then ONE trailer line
  `@@REC action=<VERB> qty=<int|none> confidence=<high|med|low> reason=<clause>`; strip + regex-parse the
  trailer. Prose streams cleanly; structure is recoverable.

## 3. "Streaming" the answer in Streamlit
`serving_endpoints.query` is one-shot. For the live-typing feel, invoke, then re-emit word-by-word with
`st.write_stream` over a generator:
```python
import re, time
def stream_words(text, delay=0.012):
    for tok in re.split(r"(\s+)", text):
        if tok: yield tok; time.sleep(delay)
# in the page:
st.write_stream(stream_words(result_text))
```
Persist the finished text in `st.session_state` so a rerun doesn't re-stream it (see symptom-fix).
(True server-token streaming exists via the REST `/serving-endpoints/.../invocations` with `stream=true`,
but the invoke-then-restream approach is simpler and visually identical.)

## 4. Genie (natural-language → SQL) — poll-based, no native streaming
```python
w = WorkspaceClient()
conv = w.genie.start_conversation(space_id=SPACE_ID, content=question)  # → conversation_id, message_id
TERMINAL = {"COMPLETED","FAILED","CANCELLED","QUERY_RESULT_EXPIRED"}
for _ in range(150):                       # ~5-min budget @ 2s
    m = w.genie.get_message(space_id=SPACE_ID, conversation_id=conv.conversation_id, message_id=conv.message_id)
    if any(t in str(m.status) for t in TERMINAL): break
    time.sleep(2)
# On COMPLETED: iterate m.attachments → text.content (answer) + query.query (generated SQL);
#   fetch rows via w.genie.get_message_attachment_query_result(...).statement_response
# On FAILED/CANCELLED: surface m.error.error (missing table / permission / ambiguous) — not a generic msg
```
- Resource: `genie_space` with `permission: CAN_RUN` **and a `name:`** (validate warns without it),
  env `DATABRICKS_GENIE_SPACE_ID` `valueFrom: genie-space`. App-level `user_api_scopes: [dashboards.genie]`.
- Poll to a TERMINAL status — don't early-exit on `EXECUTING_QUERY`. Treat per-poll timeouts as transient.

## 5. OBO — the signed-in user's identity
Databricks Apps forward the user identity in request headers. In Streamlit:
```python
import streamlit as st
def planner_email():
    h = getattr(st.context, "headers", {}) or {}
    return (h.get("x-forwarded-email") or h.get("x-forwarded-preferred-username")
            or "local-dev@example.com")
```
Stamp this as `approved_by` / `decided_by` on every write so the audit trail is attributable. For
user-scoped **data access** (not just identity), build a user-token client:
`WorkspaceClient(token=h["x-forwarded-access-token"], auth_type="pat")` and declare the matching
`user_api_scopes`. Default to SP for shared reads; use OBO when per-user permissions must be enforced.

## Discovery cheat-sheet (run before wiring anything)
```bash
databricks warehouses list --profile <p>
databricks serving-endpoints list --profile <p> -o json      # pick READY llm/v1/chat
databricks genie list-spaces --profile <p>
databricks postgres list-projects --profile <p>              # then list-branches / list-databases / get-endpoint
databricks experimental aitools tools discover-schema catalog.schema.table   # profile before you query
```
