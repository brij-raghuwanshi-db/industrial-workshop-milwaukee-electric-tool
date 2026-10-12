# Databricks Agentic Operational-Cockpit App — Build Skill

A self-contained skill for building a **governed, agentic operational-cockpit web app on Databricks
Apps** — the "read governed data → recommend an action → approve → write back → watch it update live,
all traced and governed" pattern. It is domain-agnostic: the same skeleton serves returns
management, supply-chain exceptions, fraud triage, population health, incident response, and similar
workloads.

## What it is

A full-stack **Node/TypeScript + React + Express (AppKit)** application that combines, in one
deployable Databricks App:

- **Lakebase Postgres** (OLTP) — low-latency reads of synced gold-table mirrors + a single writable
  transactional action table (drafts, approvals, audit) + chat state.
- **SQL Warehouse / Delta** (OLAP) — analytics charts + the source of truth.
- **Genie** — a natural-language `ask_data` investigation tool over the governed lakehouse.
- **Model serving** — real-time scoring to rank candidate actions against constraints.
- **An agent** (OpenAI Agents SDK streaming, or a hand-rolled tool loop) with a strict
  Discover → Draft → **Approve** → Act chain and a live UI cascade on write.
- **Unity AI Gateway** (spend cap, guardrails, inference logging) + **MLflow tracing** (per-turn
  spans, thumbs-feedback → assessments) + **OBO auth** (every write attributed to the operator).
- An **embedded AI/BI dashboard** for exploratory analytics.

## How to use

Read [SKILL.md](SKILL.md) first — it defines the pattern, the invariants, and the nine building
blocks, and routes you to the detailed reference for each. Then follow
[references/09-build-playbook.md](references/09-build-playbook.md) for the order of operations.

## Contents

```
SKILL.md                              entry point: pattern, invariants, block index, read order
references/
  01-architecture.md                  two-plane model, the read→recommend→approve→write→cascade contract, boot
  02-backend-appkit.md                Express + AppKit plugins, migration gate, config load, OBO auth, MLflow
  03-agent-and-tools.md               two runner styles, the tool catalog, 3-phase chain, SSE taxonomy, tracing
  04-lakebase-data-model.md           synced mirrors + the one writable table, Drizzle, sync, audit, search
  05-frontend.md                      pages, chat dock, the dataMutated live-cascade bus, charts, theming
  06-platform-integrations.md         Genie, MAS, model serving, AI Gateway, embedded dashboard, FTS/BM25, auth
  07-config-deploy-auth.md            config/app.json, app.yaml, DABs, deploy scripts, the two auth models
  08-data-ml-foundation.md            the data + ML stack the app assumes: data gen, SDP gold, metric view, model, Genie
  09-build-playbook.md                order of operations, ships-vs-build layering, acceptance checks, gotchas register
  10-verification-and-fallbacks.md    verified API shapes + how to re-verify live + a degrade-don't-loop fallback ladder per integration
```

> **Patterns in this skill were verified against live Databricks docs + the installed AppKit
> skills.** Where the live platform differs, [references/10-verification-and-fallbacks.md](references/10-verification-and-fallbacks.md)
> records the corrected shapes and a fallback ladder for each fragile integration so a build
> degrades to a working state instead of retrying a broken call. Always scaffold via the CLI
> (`databricks apps manifest` / `init` / `validate` + `npx @databricks/appkit docs`).

## The invariants (see SKILL.md for detail)

1. Two planes (Delta OLAP + Lakebase OLTP), one Unity Catalog governance boundary.
2. Exactly one writable table; every other Lakebase table is a read-only synced mirror.
3. Human-in-the-loop approval is a hard gate before any write.
4. Every write publishes `dataMutated` → the UI cascades live with no reload.
5. Attribute everything: OBO-stamped writes, MLflow spans, AI-Gateway-governed model calls.
6. Fail visibly, degrade gracefully (boot before DB ready, tolerate missing sources, surface real errors).
