---
name: databricks-agentic-ops-app
description: >
  Build a governed, agentic operational-cockpit web app on Databricks Apps: a full-stack
  Node/TypeScript + React + Express (AppKit) application that turns governed lakehouse data
  into an operator action. It ships a KPI/overview home, a live "at-risk queue" panel backed by
  Lakebase Postgres, warehouse-backed analytics charts, an embedded AI/BI dashboard, and a
  streaming chat assistant (OpenAI Agents SDK or a hand-rolled tool loop) that investigates via
  Genie, ranks options via a UC model-serving endpoint, and performs a human-approved write-back
  to Lakebase that cascades live into the UI. Every model call is traced in MLflow and can be
  governed by Unity AI Gateway. Invoke when building a "read governed data → recommend an action
  → approve → write back → see it update live" application on Databricks.
---

# Databricks Agentic Operational-Cockpit App

## What this skill builds

A **single deployable Databricks App** that implements a repeatable pattern:

> **See it → Ask why → Get the recommendation → Act (with approval) → Watch it update live → all governed & traced.**

It is a **full-stack web app** (not a notebook, not a managed dashboard) that sits on top of the
Databricks lakehouse and gives a non-technical operator a screen where they:

1. **Visualize** a live operational queue — records ranked by a risk/priority score, KPI tiles for
   $-exposure / open-items / critical-count, a scatter or map, filters and full-text search.
2. **Assist** — a chat assistant investigates *why* a record is flagged (natural-language →
   Genie SQL over the governed lakehouse), ranks candidate actions against capacity/constraints
   (real-time call to a UC model-serving endpoint), and drafts a summary.
3. **Act** — after explicit human approval, the assistant writes the chosen action to a
   transactional Lakebase table; the UI **cascades live** (KPIs tick, the row flips to "assigned",
   the queue re-sorts) with no page reload.
4. **Govern & observe** — every turn is traced in MLflow (tool spans, thumbs feedback →
   assessments); model calls run through Unity AI Gateway (spend cap, guardrails, inference
   logging); OBO auth stamps every write with the operator's identity; PHI/sensitive fields stay
   inside the boundary.

This is a **template pattern**, not one app. The domain (records, scores, actions, providers) is
config- and schema-driven. Swap the Lakebase schema, the agent tools, the analytics SQL, and the
theme, and the same skeleton serves returns-management, supply-chain exception handling, fraud
triage, population health, incident response, or any "governed data → recommended action →
approved write-back" workload.

## When to use / not use

**Use when** the ask is a custom interactive app that: reads governed lakehouse data at low
latency, needs a **writable transactional surface** (drafts, approvals, audit, locks) alongside
read-only analytics, wants an **agentic chat assistant** with tool-calling over that data, needs
**human-in-the-loop approval before a write**, and must show the write **cascade live** into the
UI. It combines OLTP (Lakebase) + OLAP (SQL Warehouse/Delta) + Genie + model serving + Apps in one
governed surface.

**Do NOT use when**: a plain managed **AI/BI (Lakeview) dashboard** satisfies the ask (no custom
interactivity, no write-back) — build that instead; or the app is a pure Python data app
(Streamlit/Dash/Gradio) with no agent/write surface; or there is no governed data behind it.

## The nine building blocks (and their reference files)

| # | Block | What it is | Reference |
|---|-------|-----------|-----------|
| 1 | **Architecture & data flow** | The two-plane model (Delta OLAP + Lakebase OLTP), boot sequence, the live-cascade contract | [references/01-architecture.md](references/01-architecture.md) |
| 2 | **AppKit backend** | Express server, the 3 AppKit plugins (server/lakebase/analytics), boot order, migration gate, OBO auth, error logging | [references/02-backend-appkit.md](references/02-backend-appkit.md) |
| 3 | **The agent & tools** | Two agent-runner styles (OpenAI Agents SDK streaming vs hand-rolled tool loop), the tool catalog, the strict 3-phase Discover→Draft→Act chain, SSE event taxonomy, MLflow tracing | [references/03-agent-and-tools.md](references/03-agent-and-tools.md) |
| 4 | **Lakebase data model** | The read-only synced mirrors + the writable action table, Drizzle schema, Delta→Lakebase sync, versioned audit trail, reset-demo | [references/04-lakebase-data-model.md](references/04-lakebase-data-model.md) |
| 5 | **Frontend** | React SPA, page inventory (Home/Panel/Analytics/Dashboard/Ops/Beds+Schedule), the chat dock, the `dataMutated` live-refresh cascade, Recharts, theming | [references/05-frontend.md](references/05-frontend.md) |
| 6 | **Platform integrations** | Genie conversation API (poll loop), model serving (real-time scoring), Unity AI Gateway (spend cap/guardrails/inference logging), embedded AI/BI dashboard, Lakebase full-text/BM25 search, AI functions | [references/06-platform-integrations.md](references/06-platform-integrations.md) |
| 7 | **Config, deploy & auth** | `config/app.json` + JSONC env-substitution + zod validation, `app.yaml` resources/scopes, DABs bundle, the deploy/lakebase-setup scripts, the two auth models (OBO vs OAuth M2M) | [references/07-config-deploy-auth.md](references/07-config-deploy-auth.md) |
| 8 | **Data & ML foundation** | What the app assumes underneath: synthetic data generator, medallion SDP pipeline, UC metric view, the regression recommender model + batch scoring, the Genie space | [references/08-data-ml-foundation.md](references/08-data-ml-foundation.md) |
| 9 | **Build playbook** | End-to-end order of operations, the "ships working vs you build" layering, acceptance checks, and the gotchas register | [references/09-build-playbook.md](references/09-build-playbook.md) |
| 10 | **Verification & fallbacks** | Verified API shapes (Genie/MLflow/serving/Gateway/Lakebase), how to re-verify against live docs, and a fallback ladder per integration so builds degrade instead of looping | [references/10-verification-and-fallbacks.md](references/10-verification-and-fallbacks.md) |

> **Verify before you build.** The exact API surfaces drift. Scaffold with the CLI
> (`databricks apps manifest` → `databricks apps init --features …` → `npx @databricks/appkit docs`
> → `databricks apps validate`) rather than hand-authoring plugin wiring, and consult
> **[10-verification-and-fallbacks.md](references/10-verification-and-fallbacks.md)** for the
> verified shapes + the degrade-don't-loop ladders whenever an integration fights the platform.

## Read order

1. Start with **[01-architecture.md](references/01-architecture.md)** to internalize the two-plane
   model and the live-cascade contract — everything else hangs off it.
2. Then **[09-build-playbook.md](references/09-build-playbook.md)** for the order of operations.
3. Pull the block-specific references as you implement each layer.

## Non-negotiable invariants (carry these into every build)

- **Two planes, one governance.** Delta (Unity Catalog) is the read-only source of truth for
  analytics + Genie. Lakebase Postgres is the low-latency serving + **write** surface. UC-synced
  tables are **read-only in Postgres** — you MUST model a *separate writable table* for actions.
- **One writable table.** The app writes to exactly one operational table (plus chat state). Every
  other Lakebase table is a synced read-only mirror. Never let the app write a synced mirror.
- **Human-in-the-loop is a hard gate.** The agent may investigate and draft freely, but the write
  tool MUST NOT fire until the operator explicitly approves. Encode this in the system prompt AND
  keep the write behind a distinct tool.
- **Every write publishes `dataMutated`.** The moment a write commits, the client must refetch and
  visibly cascade (KPI −1, row flips, queue re-sorts) with no reload. That live update is the
  payoff — if it doesn't fire, the app is "just another chart".
- **Attribute everything.** OBO-stamp writes with the operator's email; wrap each turn + tool in an
  MLflow span; route model calls through AI Gateway so spend + calls are logged and capped.
- **Fail visibly, degrade gracefully.** Boot the server before the DB is ready (gate DB routes with
  a 503+Retry-After), catch missing source tables during sync, surface the real upstream error to
  the chat bubble — never a silent empty turn.

## Tech stack (fixed skeleton, swappable domain)

- **Runtime:** Node 20+, TypeScript (ESM), Express 4/5.
- **App framework:** `@databricks/appkit` (plugins: `server`, `lakebase`, `analytics`; optional
  `genie`, `files`).
- **DB:** Lakebase Postgres via `pg` + `drizzle-orm` (+ `drizzle-kit` migrations).
- **Agent:** `@openai/agents` SDK pointed at Databricks Foundation Model serving (Responses API),
  OR a hand-rolled `openai` chat-completions tool loop. `mlflow-tracing` for spans. `zod` for tool
  schemas.
- **Frontend:** React 18 + `react-router-dom` + `recharts`, Vite build. SSE for streaming chat.
- **Deploy:** Databricks Asset Bundle (`databricks.yml`) + `databricks apps` CLI, or the scripted
  `deploy.sh` / `lakebase_setup_db.sh`.
