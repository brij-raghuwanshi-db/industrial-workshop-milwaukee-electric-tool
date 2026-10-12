# 03 — The Agent & Tools

The assistant is the heart of the app: it investigates, ranks, drafts, and (after approval) writes.
Two runner styles ship; pick per constraints. Both expose the **same tool catalog** and the **same
strict 3-phase chain**.

## Two agent-runner styles

### Style A — OpenAI Agents SDK, streaming (richest)

`@openai/agents` pointed at Databricks Foundation Model serving via the OpenAI-compatible interface.
Best when you want the SDK's event stream (normalized text deltas, reasoning summaries, tool
events) and a first-class tool abstraction with zod schemas.

```ts
import { Agent, run, setDefaultOpenAIClient, setTracingDisabled } from '@openai/agents';
import OpenAI from 'openai';

export function configureAgentsSdk(databricksHost: string, model: string, token: string) {
  // ✅ baseURL is the /serving-endpoints ROOT — NOT `${host}/serving-endpoints/${model}/invocations`.
  //    The OpenAI client appends the route (/responses, /chat/completions) itself, and the model
  //    name is passed as the `model` param on each call, not baked into the URL. (VERIFIED — see 10.)
  const client = new OpenAI({ baseURL: `${databricksHost}/serving-endpoints`,
                             apiKey: token, defaultHeaders: {} });
  setDefaultOpenAIClient(client);
  setTracingDisabled(true);  // we do our own MLflow tracing
}
// The Agent's `model` is the serving-endpoint name (must have the Responses API enabled).
// Gateway-governed alternative route: baseURL `${host}/ai-gateway/mlflow/v1`, model `system.ai.<name>`.
```

- Model must speak the **Responses API** (e.g. a GPT endpoint with `openai/v1/responses` enabled).
  Non-Responses models 400 on that route.
- Drive with `run(agent, input, { stream: true, signal })`; iterate events and translate to SSE
  (below). `await stream.completed` at the end.
- **Tool-authoring rules (SDK ships `strict: true`):** every zod field must be in `required` — use
  `.nullable()`, **never** `.optional()`. Every field needs `.describe(...)`. Property names stay
  `snake_case`. Wrap tools with a `loggedTool` that logs thrown errors + sanitizes the message
  before it reaches the model (Drizzle errors are huge and leak schema).

### Style B — hand-rolled chat-completions tool loop (simplest, most portable)

Plain `openai` client against `/serving-endpoints`; a `while` loop that probes for `tool_calls`,
executes them, appends results, and re-calls until the model emits final text — which it then
streams. Works with any tool-calling chat model (e.g. Llama-3.3-70B-instruct). Add a 429 retry.

```ts
const client = new OpenAI({ apiKey: token, baseURL: `${host}/serving-endpoints` });
let maxIterations = 8, dataMutated = false;
res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache',
                     'Connection': 'keep-alive', 'X-Accel-Buffering': 'no' });
const send = (event, data) => res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);

while (maxIterations-- > 0) {
  const probe = await withRetry(() => client.chat.completions.create({
    model, messages: allMessages, tools: TOOLS, tool_choice: 'auto', max_tokens: 2048 }));
  const msg = probe.choices[0].message; allMessages.push(msg);
  if (msg.tool_calls?.length) {
    for (const tc of msg.tool_calls) {
      send('thinking', { tool: tc.function.name, args: JSON.parse(tc.function.arguments || '{}') });
      const result = await executeTool(pool, tc.function.name, JSON.parse(tc.function.arguments||'{}'), userEmail);
      if (result.includes('dataMutated')) dataMutated = true;
      allMessages.push({ role: 'tool', tool_call_id: tc.id, content: result });
    }
    continue;                                  // loop for the next LLM call
  }
  allMessages.pop();                           // drop the non-streamed final; re-do streaming
  const stream = await withRetry(() => client.chat.completions.create({ model, messages: allMessages, max_tokens: 2048, stream: true }));
  for await (const chunk of stream) { const d = chunk.choices[0]?.delta?.content; if (d) send('token', { content: d }); }
  send('done', { dataMutated }); res.end(); return;
}
```

Trade-off: Style B streams only the final answer (tool phases are non-streamed probes surfaced as
`thinking` events); Style A streams reasoning + tool events continuously.

## The tool catalog

A full-featured build exposes ~9 tools. Group them by phase:

| Tool | Phase | What it does | Backs onto |
|------|-------|--------------|-----------|
| `ask_data` | Investigate | NL question over the governed lakehouse → SQL answer | **Genie** space (poll) OR a **MAS** endpoint (stream) |
| `find_record` | Discover | Live position for `{id}` (or the worst open by exposure) — score, open gaps, exposure, capacity headroom | Lakebase mirror (JOIN mirror ⨝ open_atrisk) |
| `search_records` | Discover | NL/free-text record lookup ("high-risk, discharged recently") | Lakebase **BM25/full-text** search (ILIKE fallback) |
| `search_providers` | Discover | Find a suitable program/provider for a referral | Lakebase **Search** over provider name+description |
| `rank_actions` | Assist | The **ML-in-the-loop** moment: rank candidate actions with predicted benefit + net value + capacity fit | **model-serving endpoint** (real-time) with cached-table fallback |
| `what_if` | Assist | Compare an alternative action vs the recommended one, all options side-by-side | model-serving endpoint |
| `get_capacity` | Assist | Team/resource capacity summary + open slots + warnings | Lakebase aggregate |
| `execute_action` | **Act (approval-gated)** | Propose/record the chosen action → **write** row (status, audit, provider) | Lakebase **WRITE** (the one writable table) |
| `approve_action` | **Act (approval-gated)** | Flip proposed → approved; append audit; record a value-ledger event | Lakebase **WRITE** |

Design rules:
- **`ask_data` is config-driven.** Register whichever backend is set (`genieSpaceId` → `ask_genie`,
  `masEndpointName` → `ask_mas`) — no code change to switch. To use both, register both with
  distinct names and tell the model when to prefer each.
- **Reads never throw** — return `{ found: false, note }` / `{ scored: false, note }` so the model
  can explain a gap instead of crashing the turn.
- **Bound every query.** The system prompt forbids unbounded reads (no "dump all records"); tools
  cap at LIMIT ≤ 20 and require a filter. This is a governance guardrail, not just perf.
- **The write is filter-driven + transactional** — inputs are a filter + drafted text (never a list
  of ids); wrap in `db.transaction`; insert the row with `status`, `approved_by` (OBO email), and an
  append-only `audit_trail` JSONB entry; return `{ recorded/approved: true, actionId, ... }` so the
  agent quotes the truth from the write, not its memory.
- Wrap every tool body in `mlflow.withSpan(fn, { name, spanType: mlflow.SpanType.TOOL, inputs })`.

## The strict 3-phase chain (system prompt)

The system prompt is where the human-in-the-loop gate lives. Encode it explicitly:

```
PHASE 1 — DISCOVER: call ask_data to investigate drivers; call find_record for the live position;
  optionally get_capacity. Synthesize "X is flagged because [reasons], score [n]."
PHASE 2 — DRAFT + CONFIRM: call rank_actions; quote ALL options with predicted benefit + net value +
  capacity fit; recommend the top one and explain WHY; offer a what_if; draft a brief summary.
  ** STOP. Wait for approval. Do NOT call execute_action / approve_action yet. **
PHASE 3 — EXECUTE (only after the user says yes/approve/do it): call the write tool with the
  approved details; confirm what was done; then STOP — do NOT auto-advance to the next record.

GUARDRAILS:
- Never retrieve ALL records at once (max ~20). Deny "dump/export everything" with a governance msg.
- After an action, STOP and wait. Do not loop back to discovery or say "want the next one?".
- Be concise, evidence-based, action-oriented. One record per turn unless asked for a batch.
```

The "STOP after action / no auto-loop" rule matters: without it the agent creates an infinite
discover→act loop that burns tokens and confuses the operator.

## SSE event taxonomy (Style A)

One taxonomy the browser parses, emitted from the runner:

```
response.output_text.delta              — final-answer token
response.reasoning_summary_text.delta   — live reasoning token (Responses API models with reasoning)
response.reasoning_summary_text.done    — authoritative reasoning text (persist into thinking[])
response.output_item.done               — a function_call / function_call_output / message
response.completed                      — end of turn (carries trace_id for the "View trace" link)
error                                   — upstream error string (rendered in the red bubble)
```

The runner taps three SDK sources: (1) SDK-normalized `output_text_delta` (works for Responses AND
chat-completions — the canonical text path); (2) `model`-wrapped Responses events for reasoning
summaries (drop the duplicate text delta); (3) SDK `tool_called`/`tool_output` events → mapped to
`response.output_item.done`. Sub-agent activity from inside `ask_data` (MAS sub-agents, Genie
reasoning traces) is forwarded via an `onToolProgress` callback and both persisted into `thinking[]`
and streamed. `sseWrite` no-ops once `res.writableEnded` (client disconnect is expected, not a bug).

## Robustness (both styles)

- **Persist the user message FIRST** so a mid-stream crash still shows it on reload.
- **Sanitize history** before sending to the model: only `user`/`assistant` roles, drop empty
  content, map assistant messages to the structured `[{type:'output_text', text}]` shape (a bare
  string 502s the Responses API; empty `output_text` 502s too).
- **Abort on client disconnect** — bind to `res` `'close'` (NOT `req` `'close'`, which fires as soon
  as the small JSON body is consumed and would kill every turn). On abort → `canceled=true`,
  persist a "Canceled by the user" row, don't flag the MLflow span as error.
- **Surface the real upstream error.** The SDK strips response bodies before throwing ("400 no
  body"); install a fetch shim that captures the body to `ctx.modelError` and prefer it in the
  chat bubble so the message is actionable.
- **Wrap the whole turn** in `mlflow.withSpan(..., { spanType: AGENT })` so OTel-instrumented
  Lakebase `lakebase.query` spans are adopted as children (DB latency shows up in the trace tree)
  instead of logging "No trace ID found for span lakebase.query. Skipping." every query.
- Persist the assistant row (finalText / error / `thinking[]` JSONB / traceId) after the turn so
  reload shows exactly what the user saw, including "▸ Reasoning · N tools".

## Feedback → MLflow assessments

Thumbs up/down on a message writes a local `feedback` row AND best-effort posts a HUMAN-source
assessment to the trace. **VERIFIED current API (see 10):** `POST /api/**3.0**/mlflow/traces/{traceId}/assessments`
(note **3.0**, not 2.0) with:

```jsonc
{ "feedback": { "name": "user_feedback", "value": true },   // feedback.name + feedback.value (bool/number)
  "rationale": "…",
  "source": { "source_type": "HUMAN", "source_id": "alice@example.com" } }
```

Prefer the MLflow Python/TS helper (`mlflow.log_feedback` / `log_assessment` with
`AssessmentSourceType.HUMAN`) which wraps the REST call. Best-effort: log + keep going on failure
(the local `feedback` row is still written). If you see 404s on `/api/2.0/...assessments`, you're on
the old path — switch to `3.0`. The `response.completed` SSE event still carries `trace_id` for the
"View trace" deep-link.
