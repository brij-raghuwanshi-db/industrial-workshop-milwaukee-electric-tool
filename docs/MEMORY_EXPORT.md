# MKE Project — Exported Agent Memory

_Exported 2026-09-01 07:51 from the project memory store_
(`~/.claude/projects/-Users-brijendra-raghuwanshi-Downloads-mke-rsc-isaac/memory/`). **20 memories.** Raw copies are in `memory_export/files/`; this file consolidates them, organized by category, full content inline.

These are the persistent facts the agent recalls across sessions. Types: **reference** (how things are), **feedback** (how the user wants work done), **project** (ongoing work/decisions), **user** (who the user is).

---

## Contents at a glance

| # | Memory | Type | Created | One-line |
|---|--------|------|---------|----------|
| 1 | `mke-rsc-workspace-access` | reference | 2026-08-30 16:08 | How to access the mke-rsc Azure Databricks workspace (OAuth U2M profile), and M2M status |
| 2 | `databricks-v2-mcp-connection` | reference | 2026-08-30 16:08 | databricks-v2 MCP is connected to the mke-rsc workspace; caveats on default + warehouse |
| 3 | `mcp-servers-status` | reference | 2026-08-30 16:08 | Which MCP servers are connected/usable in this project (probed 2026-08-30) |
| 4 | `databricks-agent-skills-install` | reference | 2026-08-30 16:05 | Databricks agent skills are installed for Claude Code; two update channels and which version is authoritative |
| 5 | `prefer-latest-databricks-skills` | feedback | 2026-08-30 16:05 | Always use the latest/live Claude Code plugin version of the Databricks skills |
| 6 | `mke-workspace-dev-location` | project | 2026-08-31 01:12 | Where to do Databricks workspace development for the MKE project |
| 7 | `mke-project-guardrails` | project | 2026-08-31 03:42 | Non-negotiable base rules for the MKE supply-chain project — read-only prod, sandbox+Lakebase writes, no overengineering, handoff on threshold |
| 8 | `mke-operating-pattern` | feedback | 2026-08-30 18:54 | How the user wants Databricks development done on the MKE project — business-outcome-first, fit-for-purpose, workspace-first; encoded in the mke-supply-chain-fde skill |
| 9 | `mke-project-scope-sources` | project | 2026-08-30 18:55 | MKE authoritative scope lives in customer_requirements/ (3 docs) — they outrank any distilled summary; validate scope live before building |
| 10 | `mke-worklog-practice` | feedback | 2026-08-31 03:29 | Standing practice: after every accepted piece of work, append the decision trail to WORKLOG.md |
| 11 | `mke-lessons-learnt` | feedback | 2026-08-30 18:24 | MKE execution lessons — build a vertical slice before horizontal assets, label evidence, \"done\" means UAT-passed not deployed, treat past work as reference not gospel |
| 12 | `mke-data-profiling-facts` | project | 2026-08-30 20:26 | Workspace-verified facts about MKE P1-P4 source tables (profiled live 2026-08-30) |
| 13 | `mke-orgs-are-not-interchangeable` | project | 2026-08-31 02:58 | MKE orgs behave structurally differently; thresholds/bias/comparisons must be org-aware, not global |
| 14 | `mke-order-lifecycle-flow-slice` | project | 2026-08-31 03:25 | p1flow order-lifecycle slice: order-timing tables, the expected-date mirage, chronic-slipper signal |
| 15 | `mke-sdp-pipeline` | project | 2026-08-31 07:50 | MKE P1 SDP pipeline — parallel sdp_* tables + clone dashboard + weekly Job; pre-agg for scale; roadmap step 2 done |
| 16 | `mke-genie-space-built` | project | 2026-08-31 08:54 | MKE P1 Genie Space built on sdp_* tables; answers pinpoint the underlying SKU records; id 01f1a542c3f7132681b64d8ff08b4033 |
| 17 | `mke-genie-app-enablement` | project | 2026-08-31 03:27 | Gold tables are Genie's knowledge and the App's data/action surface; enablement notes are source-of-truth |
| 18 | `lakeview-dashboard-widget-binding` | feedback | 2026-08-31 02:00 | Lakeview/AI-BI dashboard widgets need query name \"main_query\"; copy working JSON, don't hand-invent |
| 19 | `dashboard-action-not-state` | feedback | 2026-08-31 05:47 | Operational dashboards must show change+verb+$, not levels; levels read as 'just another chart' |
| 20 | `databricks-streamlit-apps-skill` | reference | 2026-09-01 06:57 | Project skill for building Streamlit apps on Databricks Apps from scratch (fastpath + templates + symptom-fix register) |

---

## 1. Access, workspace & tooling setup

### mke-rsc-workspace-access
*type:* **reference**  ·  *created:* 2026-08-30 16:08  ·  *file:* `memory_export/files/mke-rsc-workspace-access.md`  
*summary:* How to access the mke-rsc Azure Databricks workspace (OAuth U2M profile), and M2M status

The target Azure Databricks workspace is accessed via the `mke-rsc` CLI profile.

- Host: `https://adb-4482605715640778.18.azuredatabricks.net`
- workspace_id: `4482605715640778`, account_id: `b623bce4-4061-4e08-8bcc-e167459ea675`
- `auth_type = databricks-cli` → genuine **OAuth U2M** (browser login, cached token auto-refreshes; no re-login needed).
- Authenticated identity: Brijendra Singh Raghuwanshi (brijendra.raghuwanshi@databricks.com).

Use it directly — do not re-run auth setup or ask which profile for this workspace:
- CLI: `databricks current-user me --profile mke-rsc`
- SDK: `WorkspaceClient(profile="mke-rsc")`
- databricks-v2 MCP: also connected to this workspace — see [[databricks-v2-mcp-connection]].

**M2M (machine-to-machine): parked, not set up.** User chose "just U2M for now". When wanted later: needs an account-admin to create a service principal + OAuth secret, then a profile with `client_id`/`client_secret` (Databricks-managed SP) or `azure_client_id`/`azure_client_secret`/`azure_tenant_id` (Entra ID SP). See [[databricks-agent-skills-install]].


### databricks-v2-mcp-connection
*type:* **reference**  ·  *created:* 2026-08-30 16:08  ·  *file:* `memory_export/files/databricks-v2-mcp-connection.md`  
*summary:* databricks-v2 MCP is connected to the mke-rsc workspace; caveats on default + warehouse

The **databricks-v2 MCP** server is connected to the working workspace `mke-rsc` (`https://adb-4482605715640778.18.azuredatabricks.net`). It reused the existing OAuth creds — no separate auth needed. Don't re-run `connect_to_workspace` unless it dropped.

Caveats:
- **Always pass the host/workspace explicitly** to databricks-v2 tools. The server's `default_workspace` still reports `central-logfood-prodtools-azure-westus` (a built-in fallback label), NOT mke-rsc. mke-rsc is the only connected workspace so calls resolve to it, but be explicit to be safe.
- Connection is **session-only** (dynamic host-based alias; lost if the MCP server restarts). The OAuth token is cached on disk, so reconnecting needs no re-auth.
- **No default SQL warehouse set** (`warehouse_id: null`). Anything running SQL through this MCP (Genie, ad-hoc queries) needs an explicit warehouse ID until one is chosen.

This is a SEPARATE auth surface from the `mke-rsc` CLI profile ([[mke-rsc-workspace-access]]) — the CLI/skills path and the MCP path are independent.


### mcp-servers-status
*type:* **reference**  ·  *created:* 2026-08-30 16:08  ·  *file:* `memory_export/files/mcp-servers-status.md`  
*summary:* Which MCP servers are connected/usable in this project (probed 2026-08-30)

MCP servers available in this project, all probed live on 2026-08-30 (9 total, all non-blocking):

- **confluence** — live (Databricks Confluence: Universe, Field Engineering, KB, etc.)
- **github** — live; PR read/write + CI/CD. Org defaults to `databricks-eng` for universe/runtime.
- **jira** — live; user is allow-listed for issue create ops. JQL search; ADF required for rich-text writes.
- **slack** — live; channels, messages, Lists, batch ops.
- **safe** — live; feature-flag read/write/merge (SAFE).
- **google** — live; Gmail/Calendar/Drive/Docs/Sheets/Slides/Tasks as brijendra.raghuwanshi@databricks.com.
- **storage-console** — live; DB-infra tooling.
- **web-search** — live; via Databricks AI Gateway.
- **databricks-v2** — live and connected to `mke-rsc`; see [[databricks-v2-mcp-connection]].

Note: databricks-v2 was the only one that needed wiring (was 0 workspaces connected); now pointed at mke-rsc.


### databricks-agent-skills-install
*type:* **reference**  ·  *created:* 2026-08-30 16:05  ·  *file:* `memory_export/files/databricks-agent-skills-install.md`  
*summary:* Databricks agent skills are installed for Claude Code; two update channels and which version is authoritative

Databricks **agent skills** are installed and enabled for Claude Code (the old "AI Dev Kit skills" are deprecated; content folded into these). Plugin: `databricks@claude-plugins-official`, enabled in `~/.claude/settings.json`. They auto-trigger by task and are driven by the `databricks` CLI.

**There are two independent distribution channels — always prefer the Claude Code plugin version (the one live in-session):**
- Claude Code plugin (marketplace): manage with `claude plugin update databricks@claude-plugins-official` and `claude plugin marketplace update`. This is the authoritative one for work done inside Claude Code (currently v0.2.12, 32 skills incl. databricks-genie-agents, doctor, setup).
- `databricks aitools` CLI (raw skill files for Codex/Cursor/etc.): manage with `databricks aitools update` / `list`. Publishes on its own slower cadence (was v0.2.10).

The two version numbers legitimately differ — neither command can pull the other channel forward. Not a bug; don't try to "reconcile" them. For anything in Claude Code, the plugin (higher) version is what matters.

To update everything: run BOTH `claude plugin update databricks@claude-plugins-official` and `databricks aitools update`.

Workspace this pairs with: [[mke-rsc-workspace-access]].


### prefer-latest-databricks-skills
*type:* **feedback**  ·  *created:* 2026-08-30 16:05  ·  *file:* `memory_export/files/prefer-latest-databricks-skills.md`  
*summary:* Always use the latest/live Claude Code plugin version of the Databricks skills

When Databricks skill/plugin versions differ across channels, always use the **latest** — specifically the Claude Code plugin version that is live in the session, not the older `databricks aitools` raw-file version.

**Why:** User explicitly said "remember to use the latest one." The two channels drift and the in-session plugin is the newer, authoritative one for Claude Code work.

**How to apply:** Default to the plugin skills already loaded in-session. If unsure whether something is current, `claude plugin update databricks@claude-plugins-official` (and `claude plugin marketplace update`) before relying on it. See [[databricks-agent-skills-install]].


### mke-workspace-dev-location
*type:* **project**  ·  *created:* 2026-08-31 01:12  ·  *file:* `memory_export/files/mke-workspace-dev-location.md`  
*summary:* Where to do Databricks workspace development for the MKE project

For the MKE supply-chain project, do Databricks **workspace development** (notebooks, SQL assets, the P1
vertical slice and beyond) under a folder in **`/Workspace/Users/brijendra.raghuwanshi@databricks.com/`**
(create a project subfolder there, e.g. `.../mke_supply_chain/`). User-directed 2026-08-31.

Still holds: local repo folder `data_understanding/` holds the analysis/story/architecture markdown + the
HTML dashboard; the Databricks *runnable* assets live in the workspace folder above. Guardrail unchanged —
`prod_edw`/`prod_operations` READ-ONLY; all writes to `sandbox_operations.po_management` (verified writable;
slice tables namespaced `p1slice_*`). See [[mke-data-profiling-facts]] and [[mke-project-guardrails]].


---

## 2. Project guardrails & operating pattern

### mke-project-guardrails
*type:* **project**  ·  *created:* 2026-08-31 03:42  ·  *file:* `memory_export/files/mke-project-guardrails.md`  
*summary:* Non-negotiable base rules for the MKE supply-chain project — read-only prod, sandbox+Lakebase writes, no overengineering, handoff on threshold

Non-negotiable rules for the Milwaukee Electric Tool supply-chain Databricks project:

- **`prod_edw` and `prod_operations` are READ-ONLY.** No INSERT/UPDATE/DELETE/MERGE/TRUNCATE/
  CREATE OR REPLACE/ALTER/DROP and no write-capable streaming sink against them.
- **All writes go to `sandbox_operations.po_management`** (derived Delta, snapshots, exception
  outputs, QA evidence, action/outcome history) **and Lakebase** (transactional App state).
  Lakebase→Delta publication writes only into `sandbox_operations.po_management`.
- External-system writeback (Oracle Fusion/SCC/WMS/TMS) goes through a separately approved,
  typed, auditable action path — never a direct write to a Databricks production schema.
- **NO real Oracle (or any external) write-back — ever, in this engagement.** Even when we reach
  the action/PO-execution stage (Red Keychain territory: approve/reject, PO cancel/resize/expedite),
  the write-back is **simulated in `sandbox_operations.po_management` + Lakebase**, not sent to
  Oracle. Model the typed action request, approval, outbox, and result as sandbox records so the
  full loop is demonstrable and auditable; the actual external push is explicitly out of scope until
  the business stands up the approved integration lane. (User directive 2026-08-31.)
- **The guardrail overrides the requirement docs on write location.** The customer docs name
  `prod_operations` (Actuals D5) and `prod_edw.staging_flat_files.expansion_dims`/`expansion_loads`
  (Demand Events output) — but we write ALL of these to `sandbox_operations.po_management`
  (including sandbox `expansion_dims`/`expansion_loads`, keeping the doc's column contract so they
  stay publish-compatible). Oracle Demand Planning Cloud Fusion receives the `expansion_*` data via
  a governed publish step from sandbox, never a direct `prod_edw` write.
- **Do not overengineer** — minimum sufficient architecture; a one-time query stays a query.
- **Challenge yourself**; **write a handoff doc** when chat memory nears its threshold.

**Why:** the user set these as the one-and-only hard boundaries for the project; violating the
write boundary risks corrupting authoritative EDW/operations data.

**How to apply:** before any create/modify command, confirm the fully qualified destination is
permitted; label read-only source queries as such. Full operating pattern is in the
[[mke-operating-pattern]] skill and project `CLAUDE.md`.


### mke-operating-pattern
*type:* **feedback**  ·  *created:* 2026-08-30 18:54  ·  *file:* `memory_export/files/mke-operating-pattern.md`  
*summary:* How the user wants Databricks development done on the MKE project — business-outcome-first, fit-for-purpose, workspace-first; encoded in the mke-supply-chain-fde skill

For the Milwaukee supply-chain project the user expects a senior Databricks FDE/architect
operating stance, not from-scratch coding:

- **Business-outcome-first, not language-first or product-first.** Start from workload/grain/
  consumers/freshness/source-of-truth and whether work is one-time/reusable/production — not
  "Python, PySpark, or SQL?"
- **Databricks-native, pipeline-first, but minimum sufficient** — reuse managed/declarative
  capabilities; choose products fit-for-purpose on evidence (SDP vs Job vs notebook, Lakebase vs
  Delta, Federation vs ingestion, Metric Views), never by fashion or familiarity.
- **Workspace-first, promotion-ready** — explore in place; promote to Git/DABs/CI-CD only when
  reusable/scheduled/shared/governed/SLA-backed/production-impacting.
- **Know the gotchas** for everything used; distinguish general patterns from Milwaukee-verified
  facts; label recommendations Validated/Preferred-with-assumptions/Prototype/Blocked/Rejected.

**Why:** the user codified this across the `development_pattern/` discussions and is frustrated
when work drifts back to generic-developer habits — it costs time.

**How to apply:** the [[mke-supply-chain-fde]] skill at `.claude/skills/mke-supply-chain-fde/`
encodes the full pattern — lean `SKILL.md` core plus on-demand `references/` (fit-for-purpose,
dimensional modeling, Databricks execution craft, workspace promotion, supply-chain domain,
platform gotchas, frontend/full-stack, MLflow/AI, governance/quality, tooling currency, lessons,
project scope). Use its own "when to go deep" index rather than a fixed list here — the reference
set grows. Load it for MKE work. Authoritative scope: [[mke-project-scope-sources]]. Hard
boundaries: [[mke-project-guardrails]].


### mke-project-scope-sources
*type:* **project**  ·  *created:* 2026-08-30 18:55  ·  *file:* `memory_export/files/mke-project-scope-sources.md`  
*summary:* MKE authoritative scope lives in customer_requirements/ (3 docs) — they outrank any distilled summary; validate scope live before building

The authoritative scope for the Milwaukee supply-chain project is the three requirement docs in
`customer_requirements/` (not the `development_pattern/` operating-pattern discussions, which are
about *how* to work):

- `Actuals_Supply_Plan_Requirements.md` → **P1** (confirmed sources incl.
  `prod_edw.fact.20_supply_daily`, `receiving_receipt_transactions`, `sales_order_line_transactions`,
  `inventory_days_on_hand`; decisions D1–D6; thresholds; 180-day backfill).
- `Red_Keychain_Supply_Planning_Requirements.md` → **P2** (supply exceptions) + **P4** (demand
  exceptions); 18-type taxonomy across 5 categories; broader ordering program is context, not scope.
- `01_Requirements.md` → **P3** Demand Events App (lifecycle, locking, mkedg5 disaggregation,
  Forecast Builder, output contract).

Priority order P1→P2→P3→P4; **PO Exceptions OUT of scope** (verify — it flipped once historically).

**Why:** these docs are the customer source of record and are more concrete/current than the
skill's distilled summary; treating a paraphrase as authoritative caused prior rework.

**How to apply:** the skill's `references/project-scope-and-delivery.md` is a **validate-first
snapshot** (as-of date, [req-confirmed] vs [synthesized] tags) — re-read the real docs and verify
table names/grains/thresholds against live Unity Catalog before building; a newer requirement
always wins over the summary. Two open boundaries to confirm with the owner: the P2 supply-vs-PO
exception split, and that PO Exceptions are still excluded. Write locations follow
[[mke-project-guardrails]] (sandbox, not the `prod_operations`/`prod_edw` locations the docs name).
See the full operating pattern in [[mke-operating-pattern]] and lessons in [[mke-lessons-learnt]].


### mke-worklog-practice
*type:* **feedback**  ·  *created:* 2026-08-31 03:29  ·  *file:* `memory_export/files/mke-worklog-practice.md`  
*summary:* Standing practice: after every accepted piece of work, append the decision trail to WORKLOG.md

After every accepted piece of work, append an entry to `WORKLOG.md` (repo root) — an append-only work log &
decision journal. Entry = **date · the ask in the user's own words · decision & why · artifacts (paths/IDs) ·
evidence/reconcile result · corrections · follow-ups.**

**Why:** the user asked for this explicitly ("after every acceptable work, you need to log it so history of
the work is not lost — I can't find my very first question and the trails in this chat"). The chat transcript
is NOT a durable record: this session already lost its earliest turns to compaction. Build logs
(RUNG2/P1FLOW/P1_SLICE _BUILDLOG.md) capture *how a thing was built*; WORKLOG.md captures the *trail of intent
and decisions*; memory files hold durable cross-session facts. All three are needed.

**How to apply:** don't wait to be reminded — when a deliverable is accepted/reconciled, log it before moving
on. Keep build-mechanics in the matching BUILDLOG, intent/decisions in WORKLOG.md. Reconstruct from the
compaction summary + artifacts if history was lost.

**Backups (user asked explicitly):** after appending a WORKLOG.md entry, copy it to
`worklog_backups/WORKLOG_<YYYYMMDD_HHMMSS>.md` — timestamped, append-only, never edited — so the single root
file isn't a single point of failure. First backup taken 2026-08-31. See [[mke-lessons-learnt]],
[[mke-project-guardrails]].


### mke-lessons-learnt
*type:* **feedback**  ·  *created:* 2026-08-30 18:24  ·  *file:* `memory_export/files/mke-lessons-learnt.md`  
*summary:* MKE execution lessons — build a vertical slice before horizontal assets, label evidence, \"done\" means UAT-passed not deployed, treat past work as reference not gospel

Execution lessons from prior Milwaukee work, to prevent recurrence:

- **Core failure:** too many horizontal platform assets built before one end-to-end user
  workflow was proven. Counter with: probe → walking skeleton → one vertical slice → validate →
  add intelligence → add live actions → harden. Don't let deployment be the test loop.
- **Label every claim** on the evidence ladder (Mentioned → Discovered → Accessible → Profiled →
  Semantically validated → Accepted-for-prototype → Reconciled → UAT-accepted → Production-approved).
  A schema in an old chat ≠ current metadata; a mimic table ≠ a Milwaukee source; a green job run
  ≠ business reconciliation.
- **"Done" means at least UAT-passed, not deployed.** Report status honestly (designed/implemented/
  tested/reconciled/accepted); surface fallbacks (`DEMO_FALLBACK` etc.) — never let the UI imply a
  real model/Genie result when a fallback was used.
- **Treat past work as reference, not instructions** — validate current workspace facts before
  acting on historical claims; classify findings reuse/reuse-with-validation/questionable/
  superseded/archive-as-lesson.
- Watch specific traps: summing inventory snapshots across time; recomputing metrics in the UI
  instead of the semantic layer; confusing P1 supply-execution with P4 demand exceptions; treating
  proposed KPI thresholds as Milwaukee policy; debugging auth with random credentials.

**Why:** a prior workshop burned large effort on churn/re-audits by inflating status and building
breadth before proving one workflow; the user explicitly wants this not repeated.

**How to apply:** full detail in the [[mke-operating-pattern]] skill at
`references/lessons-and-evidence.md` and `references/frontend-fullstack.md`. Hard boundaries:
[[mke-project-guardrails]].


---

## 3. Domain & data facts

### mke-data-profiling-facts
*type:* **project**  ·  *created:* 2026-08-30 20:26  ·  *file:* `memory_export/files/mke-data-profiling-facts.md`  
*summary:* Workspace-verified facts about MKE P1-P4 source tables (profiled live 2026-08-30)

Live-profiled the MKE source tables on profile `mke-rsc` (warehouse `7bd33a82f4e92206`) on
2026-08-30. Findings live in `data_understanding/` (README, 00_table_priority_map.md, SYNTHESIS.md,
subagent_findings/A–E). Key verified facts (supersede doc assumptions):

- **`prod_edw.fact.20_supply_daily`**: 13.4B rows, 366 daily snapshots (process_date 20250628→20260829,
  yyyyMMdd INT). Within one snapshot, `date_key` buckets are **WEEKLY, Monday-aligned**, forward
  horizon ~**111 weeks (~2 yrs)** — NOT 55 years (subagent A miscalc; my direct query is authoritative).
  True grain = plan_id × date_key × product_bigint_key × inventory_organization_bigint_key ×
  series_bigint_key × order_type_bigint_key (41M rows/snapshot vs 27.5M for the 4-col key). on_hand/
  PAB/safety_stock are point-in-time (semi-additive; never sum across date_key). Plans `20 Global
  Supply Plan` + `20 Mexico Supply Plan` confirmed (plan_type 2). Plan filter column = `plan_name`.
- **Item "Status 20"** (P3/P4 validation): literal is **`item_status = 'PurchPlan'`** (= `item_status_name`
  '20.Ready to Purchase or Plan Production'); 8,716 of 299,966 items. The doc's `item_status_description`
  is truncated ("Productio") — filter on `item_status`, not the description. Resolves open-item #1.
- **Orgs**: `inventory_organization_scd1` has org_code; 2012 = Olive Branch (US), 2120 = Mexico both confirmed.
- **`receiving_receipt_transactions`** (PO receipts actual) uses **RAW Oracle ids** (organization_id ~3e14,
  po_header_id, item_id) NOT EDW bigint keys → **crosswalk required** before joining to plan/dims.
  transaction_type RECEIVE 49.7% + DELIVER 49.7% (pick ONE to avoid double count). 72.8% null po_header_id.
- **`inventory_days_on_hand`**: 2.73B rows, item×org×date_key, 699 daily dates, ZERO negatives (clean);
  point-in-time. **`inventory_material_transaction`** = the 27-type root-cause ledger (Sales Order Issue,
  Subinventory Transfer, PO Receipt, Cycle Count Adj, Scrap…) — P0 for P1 variance categories + P2.
- **`10_demand_daily`**: 17.8B rows; measure column is **`planner_baseline`** (doc said `planner_baseline_forecast`)
  + `working_final_forecast`; already carries `expansions_loadin`/`expansions_runrate`/`non_repeating_events`.
  `dg5_customer_scd1` = 56 mkedg5 customers, mkedg0=4→mkedg5=56. `expansion_loads` populated (8.09M rows),
  `expansion_dims` (19,594). See [[mke-project-scope-sources]] and [[mke-project-guardrails]].

Data-story walkthrough findings (data_understanding/data_stories/, 2026-08-30):
- **Clean PO-receipt fact exists: `prod_edw.fact.purchase_receipt_line`** (2.72M rows, 69,871 items, 2023–2026,
  0 null item keys) — has item_bigint_key + purchase_order_number/line + received/shipped/accepted_quantity +
  expected/receipt dates. **Use this for P1 receipts, NOT the raw-id `receiving_receipt_transactions`** (which
  has NO item column). Resolves the crosswalk blocker. Joins purchase_orders on (po_number, line).
- **P3 item validation = dash-normalization**: expansion_loads.item_number is dashed (`49-56-0507`),
  items_scd1.item_id is dash-less; `REPLACE(item_number,'-','')` join → 98.7% match vs 4.8% raw.
- **P4 `frozen_*` columns in 10_demand_daily are 100% NULL** → use process_date day-over-day deltas for drift;
  reason/audit lives in Lakebase not the warehouse.
- **P2 raw unit-miss over-ranks cheap parts**: top "breach" was a $0.0134 carbide component at a plant (org
  1019), ~$235K real impact → must weight by applied_standard_cost + ABC + org-role.
- inventory_material_transaction transfer rows double-count across subinventories → net inter-org before tie-out.
- Hero item for P1/P2 tracing: item_bigint_key 3879620845706693458 / item_id 48111850 (M18 XC5.0 Battery).


### mke-orgs-are-not-interchangeable
*type:* **project**  ·  *created:* 2026-08-31 02:58  ·  *file:* `memory_export/files/mke-orgs-are-not-interchangeable.md`  
*summary:* MKE orgs behave structurally differently; thresholds/bias/comparisons must be org-aware, not global

Validated 2026-08-31 against Rung-2 gold (`sandbox_operations.po_management.rung2_plan_vs_actual`): org 2120
Mexico is a **structurally different** operating environment from org 2012 Olive Branch, not a smaller copy.
The plan-vs-actual **logic generalized to 2120 with zero rewrite** (grain re-verified clean, org→plan
predicate prevents double-count), but the **judgement layer does not transfer**:
- **Bias magnitude differs ~5× (NOT inverted):** by row-sign BOTH orgs over-plan (actual on-hand > planned
  PAB) — 2012 41% over/26% under, 2120 38% over/19% under, medians 0% both. Mean onhand_variance_pct +101%
  (2012) vs +21% (2120) measures the overage-tail SIZE, not direction. (Both subagents initially said
  "inverted/opposite"; a sign test refuted it — a caution that outlier-inflated means aren't a direction.)
- **$-thresholds don't scale:** 2120 p99 miss is $9.6K vs 2012 $141.5K → the >$200K escalate never fires
  at 2120. Fixed $ bands mis-fire; a 2120 planner would see zero escalations and wrongly read "all clear."
- **3 NEW 2120-only facts** (only visible after loading 2120): planner concentration (6 planners vs 92; 2
  own ~85%), 41% Mexico-exclusive SKUs (4,041/9,758 — so cross-org "same item" tiles must INNER JOIN on the
  5,717 shared items, never union), and 2120 is a net-receiving node (ship/receive 0.094 vs 0.377 → hub fed
  by intercompany transfer/local suppliers). Plus lean-yet-green (SS 120 vs 2,343 units, 62% vs 36% green).

**Why:** the user pushed back — "we can't blindly say all orgs show same behavior" — and the data proved
them right.

**How to apply:** treat `organization_code` as a **judgement context, not just a filter**. Concrete
data-model changes (min-sufficient, fit inside the existing gold + Rung-3 pipeline): (1) org-keyed
`threshold_config` table with **percentile-based bands** that auto-calibrate per org (+ an absolute-$
floor); (2) **directional** per-org bias correction (read the org's bias sign; never a global correction);
(3) cross-org comparisons INNER JOIN on shared SKUs; (4) first-class planner attribute + a planner-load
view; (5) an `org_role` (hub vs producer) tag so a hub's low ship-rate isn't flagged as a miss. Deferred
(needs data beyond gold): confirming 2012→2120 intercompany transfer (material-transaction ledger);
COO/FX-import exposure (add COO from items_scd1). Full write-up:
`data_understanding/data_stories/org2120_validation/` (INDEX + A/B/C). See [[mke-data-profiling-facts]],
[[mke-lessons-learnt]].


### mke-order-lifecycle-flow-slice
*type:* **project**  ·  *created:* 2026-08-31 03:25  ·  *file:* `memory_export/files/mke-order-lifecycle-flow-slice.md`  
*summary:* p1flow order-lifecycle slice: order-timing tables, the expected-date mirage, chronic-slipper signal

Built 2026-08-31 (READ-ONLY prod; writes to `sandbox_operations.po_management.p1flow_*`): an order-lifecycle
/ stage-timing slice for **preemptive** action (expected-vs-actual per stage, org-aware timing bands,
recommended maneuver, chronic-slipper signal) — a NEW fact distinct from the P1 on-hand plan-vs-actual.

**Tables (verified populated):** `p1flow_transfer_stages` (19,024; 2012 transfer lane), `p1flow_po_stages`
(6,638; both orgs), `p1flow_order_stage_gold` (25,662; unified long-format item×org×order×lane×stage with
timing_band, recommended_maneuver, chronic_pct_late).

**Key data facts learned (verify before reuse):**
- **`prod_edw.fact.purchase_receipt_line.expected_receipt_date` is a MIRAGE for timing** — equals
  receipt_creation_date same-day 100%. Real PO timing = `prod_operations.features.
  general_historical_purchase_order_lead_time_errors` (requested_delivery_date vs delivery_date, 89–92%
  differ, `lead_time_error_days` precomputed; 13mo@2012 / 3yr@2120). `order_date_adjusted_during_P2` is 0%
  populated (don't use).
- **`fact_transfer_order_receipt` fans out ~1.45×** (167,038 rows vs 114,901 distinct receipt_line_bigint_key)
  → dedup with QUALIFY ROW_NUMBER before aggregating.
- **Only 2 real stages populated**: receipt_accept_date 0%, putaway 0 days → honest ladder is
  ordered→in-transit→received, NOT a 5-gate flow. No live "where is it now" feed (shipments all Closed).
- **No SCD2 on these facts** (only valid_partition load flag) → don't hand-build snapshot history;
  re-promise history is a Rung-3 accrual (pipeline stamps weekly).

**Signal that made it valuable:** cross timing_band with chronic_pct_late → 2120 has 345/453 (76%) of
"expedite" orders on chronically-late suppliers = systemic (fix the source), vs 76 at 2012 = one-off. 2120's
PO base is 3 suppliers, 80.6% late. Reinforces [[mke-orgs-are-not-interchangeable]]. Build log:
`data_understanding/workspace_assets/P1FLOW_BUILDLOG.md`; network-table discovery:
`data_understanding/data_stories/org2120_validation/D_network_flow_tables.md`. See [[mke-data-profiling-facts]].


---

## 4. Build knowledge & design principles

### mke-sdp-pipeline
*type:* **project**  ·  *created:* 2026-08-31 07:50  ·  *file:* `memory_export/files/mke-sdp-pipeline.md`  
*summary:* MKE P1 SDP pipeline — parallel sdp_* tables + clone dashboard + weekly Job; pre-agg for scale; roadmap step 2 done

Roadmap step 2 (stable pipeline) is BUILT and verified for MKE P1 "Actuals Supply Plan". A Lakeflow
Declarative Pipeline `p1_actuals_sdp` (id b6f16cf7-b17e-4b08-beaa-6c8e7fb97585, serverless/triggered) writes
**35 materialized views** to `sandbox_operations.po_management.sdp_*` — a fully PARALLEL copy that never
touches the live rung2_*/p1flow_* tables or the original dashboard (01f1a50aed891d5c85b5e64b2c3c5d5b), which
stay as the safety net. 4 silver + 3 gold (source-equivalent to the existing builds, read live from prod,
zero literals) + 28 per-widget-grain serving aggregates. Weekly Job `p1_actuals_weekly_sdp` (id
418760739520160, Mon 07:57 CT, PAUSED, on_failure email) triggers it. Clone dashboard "P1 Actuals — SDP
(Rung 2)" id **01f1a5371959178aa137d5551347afff** runs THIN queries over the serving tables.

**Verified (all in `workspace_assets/SDP_VERIFICATION_LOG.md` with queries):** sdp gold == live gold EXACT
(590,275 rows, per-org $ and counts 0-diff); newly-red 2,243/$23.72M and FVA −3.7%/−11.2% identical; DQ 4
EXPECT constraints 0 violations; perf gate overview/KPI serving tables 2–160 rows (was 590,275 live →
~18,000× cut); overview cube (sdp_agg_overview, 626 rows) bit-exact after full-precision fix; 42/42 clone
datasets return rows; 0 multi-y / 0 binding breaks; originals unchanged.

**Durable learnings (apply to any pre-agg/serving layer):**
- Pre-aggregate to per-WIDGET grain and store **additive components** (sum + count), never pre-divided
  averages — the thin query does SUM/SUM to reconstruct the exact average over any filtered window.
- A Lakeview counter/bar does ONE aggregation over one field → **COUNT DISTINCT and weighted-AVG tiles
  cannot be served from a rollup**; they must read a raw (narrow) dataset. Not every tile collapses to 32 rows.
- **Never ROUND inside a serving table** — round only at display; re-summing rounded cells drifts vs base.
- A pipeline MOVES computation, it does not add data (same prod reads, materialized once).
- Weekly batch vs real-time is per-SURFACE: analytics=weekly MVs, App=Lakebase real-time. Match freshness to
  the signal's change rate; don't stream a weekly fact.

Window stays 4-month (2012+2120) for the equivalence check; widen to 180d/full-network = flip `pd_lo` +
full-refresh (verify-then-widen, user's call). Gap scorecard vs the requirement doc: `P1_STATUS.md`
(carried-forward gaps — PO-qty-accuracy%, demand-accuracy%, ABC-tiered thresholds — are pre-existing, NOT
introduced by SDP). Next: roadmap step 3, the App (Lakebase real-time state, SIMULATED writeback — no real
Oracle per [[mke-project-guardrails]]). See [[dashboard-action-not-state]], [[mke-genie-app-enablement]],
[[mke-worklog-practice]].


### mke-genie-space-built
*type:* **project**  ·  *created:* 2026-08-31 08:54  ·  *file:* `memory_export/files/mke-genie-space-built.md`  
*summary:* MKE P1 Genie Space built on sdp_* tables; answers pinpoint the underlying SKU records; id 01f1a542c3f7132681b64d8ff08b4033

The Genie Agent for MKE P1 is BUILT (roadmap: it came before the App, at the user's request). It's a
**Genie Space** (not a custom agent) — "P1 Actuals — Supply Plan vs Actual (SDP)", id
**`01f1a542c3f7132681b64d8ff08b4033`**, warehouse 7bd33a82f4e92206, under
`/Workspace/Users/brijendra.raghuwanshi@databricks.com/genie_spaces`. Definition on disk:
`data_understanding/workspace_assets/genie_agent.json` (5 tables, 8 sample Qs, 15 example SQLs, 1 merged
text_instructions). Regenerate/iterate via `databricks genie update-space <id> --json ...`.

Grounded on 5 `sdp_*` tables (fact + key serving): sdp_plan_vs_actual (item×org×week fact — the record-level
answers), sdp_agg_scorecard, sdp_exceptions, sdp_order_stage_gold, sdp_rootcause_plant.

**Hard requirement the user set: answers must PINPOINT the exact records.** Implemented as (a) a text rule
"ALWAYS SHOW THE RECORDS BEHIND A NUMBER" and (b) every example SQL returns item_id/item_description/
organization_code/week_start ranked by $ (LIMIT 50-100). Ground record-level questions on the FACT, not the
pre-agg serving tables (those lose item keys). Verified live: off-plan-by-$ returned named SKUs; the
"on-hand value by org" guardrail correctly used MAX(week_start) (no cross-week sum → avoided the 5.48× trap);
bias 2012 vs 2120 = 74.0% vs 28.8% (exact scorecard match, framed as both-over-plan not "inverted").

Built by RETARGETING the pre-written [[mke-genie-app-enablement]] assets (GENIE_ENABLEMENT_NOTE Parts C/D
rules + GENIE_QUESTION_BANK 7 parts incl. plan-vs-actual + guardrails) from rung2_/ds_/p1flow_ to sdp_*.
Space-JSON gotchas: 32-hex ids unique across all 3 lists; tables + example_sqls sorted; text_instructions
exactly ONE merged item; text fields are arrays. Next roadmap step: the App (Lakebase actions, simulated
writeback — no real Oracle per [[mke-project-guardrails]]). See [[mke-sdp-pipeline]], [[dashboard-action-not-state]].


### mke-genie-app-enablement
*type:* **project**  ·  *created:* 2026-08-31 03:27  ·  *file:* `memory_export/files/mke-genie-app-enablement.md`  
*summary:* Gold tables are Genie's knowledge and the App's data/action surface; enablement notes are source-of-truth

The three consumption surfaces over the reconciled gold in `sandbox_operations.po_management` are
deliberately split (fit-for-purpose): **AI/BI dashboard = read/show** (Rung-1/2 + Cross-Org page),
**Genie space = read/ask via AI**, **Databricks App = act** (search, write-back, on-click approve/reject,
alerts, supplier cases). The App is the ONLY surface that takes actions.

**Source-of-truth docs (all in `data_understanding/`):**
- `GENIE_ENABLEMENT_NOTE.md` — data surface + reasoning playbook + build recipe for a Genie space.
- `GENIE_QUESTION_BANK.md` — every question our observed scenarios imply, tied to answering table/measure +
  expected answer/gotcha, plus guardrail (wrong-if-naive) questions from the anti-patterns.
- `APP_ENABLEMENT_NOTE.md` — maps each read-signal → the App action it enables; the Lakebase entity list;
  the safe write-back path.

**Non-negotiable action-layer guardrail:** App reads Delta gold; transactional state → Lakebase (drafts,
locks, approvals, action_request, outbox, audit); Lakebase→Delta publish only into
`sandbox_operations.po_management`; external writeback (Oracle/SCC/WMS/TMS) via a separately-approved typed
auditable action path — NEVER a direct prod write, never App→Oracle directly. Search = Lakebase BM25, not
Vector. Genie/App both scope ONLY to the gold tables. See [[mke-project-guardrails]],
[[mke-orgs-are-not-interchangeable]], [[mke-order-lifecycle-flow-slice]].


### lakeview-dashboard-widget-binding
*type:* **feedback**  ·  *created:* 2026-08-31 02:00  ·  *file:* `memory_export/files/lakeview-dashboard-widget-binding.md`  
*summary:* Lakeview/AI-BI dashboard widgets need query name \"main_query\"; copy working JSON, don't hand-invent

When building a Databricks AI/BI (Lakeview) dashboard by authoring the serialized JSON: **every widget's
query must be named `"main_query"`** (`layout[].widget.queries[].name = "main_query"`). Naming it anything
else (e.g. `"q"`) makes the encodings fail to bind — the UI shows **"Select fields to visualize"** on every
tile even though the dataset resolves and the query returns rows. This is NOT a grant, data, catalog/schema,
or publish issue; those are the wrong things to chase.

**Why:** I hit exactly this on the MKE P1 dashboard (2026-08-31) — hand-wrote widget JSON with `name:"q"`,
every tile empty, and wasted cycles on grants + fully-qualified tables + republish before finding the real
cause by diffing against the skill's working example (`databricks-aibi-dashboards/references/4-examples.md`),
where all 10 data widgets use `main_query`.

**Second gotcha (same project, same day):** widget field expressions may ONLY be a plain aggregation of a
BARE column — `COUNT(x)`, `AVG(x)`, `MAX(x)`, `SUM(x)`, `MIN(x)`, `COUNT(DISTINCT x)`, `DATE_TRUNC('WEEK',x)`.
A wrapped expression like `AVG(ABS(x))`, `MAX(ABS(x))`, or `SUM(CASE WHEN ...)` is silently rejected → that
counter shows "No data" while a sibling `COUNT(bare)` counter works. Fix: push ABS/CASE/ratios into the
DATASET SELECT as aliased columns, then aggregate the bare alias in the widget. All business logic lives in
dataset SQL, never in widget expressions.

**How to apply:** Don't hand-invent Lakeview widget JSON. Start from a KNOWN-GOOD serialized dashboard
(the skill's `4-examples.md`, or `lakeview get` on a working dashboard) and copy its exact widget
query/encoding structure — then swap dataset/fields. Verify the field-name contract holds:
`queries[].query.fields[].name` == `spec.encodings.*.fieldName`, query name == `main_query`. Deploy with
`--dataset-catalog`/`--dataset-schema` flags (bare or fully-qualified table both work once binding is right),
then `update`+`publish` on the same ID. The CLI can only verify structure/data — the visual render must be
confirmed in the browser. See [[mke-workspace-dev-location]].

**A project skill now encodes all of this:** `.claude/skills/lakeview-dashboard-fastpath/` (SKILL.md + a
known-good `templates/dashboard_skeleton.json`). It has the 7-step loop, the symptom→cause→fix register (all
five gotchas: main_query, no-func-in-widget-expr, missing-comma-breaks-dataset, global-filters-page,
%-suffix-not-number-percent), and the field-name contract. For any future Lakeview dashboard: invoke that
skill + `databricks-aibi-dashboards`, copy the skeleton, swap fields, TEST the concatenated dataset query via
CLI, then create/update+publish. Don't relearn this from scratch.


### dashboard-action-not-state
*type:* **feedback**  ·  *created:* 2026-08-31 05:47  ·  *file:* `memory_export/files/dashboard-action-not-state.md`  
*summary:* Operational dashboards must show change+verb+$, not levels; levels read as 'just another chart'

A dashboard tile that shows a **level/state** ("13,146 items red", "$1bn at risk", "242k item-weeks
off-plan") reads to an operator as *"okay, just another chart"* — because the number barely moves week to
week, so there's no trigger to act. The MKE planner said exactly this looking at the Rung-2 overview.

**The fix (now a design rule for operational pages):** open with **what CHANGED** since last period + a
**VERB** (what to do) + the **$** (why it matters) + a **systemic flag** (fix this order vs fix the source).
- Delta, not level: "2,243 items newly RED = $23.7M NEW exposure this week (1,486 recovered)" — not
  "13,146 red".
- Ranked action list with a verb: item · $ at risk · EXPEDITE / DEFER-CANCEL / FIX-SUPPLIER / REVIEW ·
  systemic-vs-one-off · planner. That IS a planner's Monday to-do, top-down by $.
- Levels & analytics become the drill-down "why" behind the action surface, not the front door.

**Why:** built as page "0 · Monday Cockpit" (first page of the Rung-2 dashboard) after the user challenged
"what's my next action from this? currently nothing." Verified the delta signal exists: WoW newly-red count/$,
resolved, escalations, stockout-$ swing all compute from the two latest `week_start` snapshots; the verb comes
from the same band logic used for exceptions; the systemic flag from p1flow chronic_pct_late≥60.

**How to apply:** for any operational/Monday-style dashboard or the future App, lead with an action surface
(change + verb + $), not a state summary. Pairs with the FVA finding (planning worse than naive) and the
org-aware thresholds. Roadmap context: Dashboard (done) → stable SDP+Job pipeline → App (clickable actions,
Lakebase, simulated writeback — no real Oracle). See [[mke-genie-app-enablement]], [[mke-worklog-practice]],
[[mke-order-lifecycle-flow-slice]].


### databricks-streamlit-apps-skill
*type:* **reference**  ·  *created:* 2026-09-01 06:57  ·  *file:* `memory_export/files/databricks-streamlit-apps-skill.md`  
*summary:* Project skill for building Streamlit apps on Databricks Apps from scratch (fastpath + templates + symptom-fix register)

`.claude/skills/databricks-streamlit-apps/` — a build-from-scratch fastpath skill for Streamlit on
Databricks Apps, distilled from the real `mke-po-actions-st` build. Load it for ANY Streamlit (or
non-AppKit Python) Databricks App work; it complements the plugin skills (databricks-core / -apps /
-lakebase / -genie-agents), doesn't replace them.

Structure: SKILL.md (iron rules + 8-step loop + reference routing), 7 references (architecture,
project-structure, lakebase-connectivity, integrations, ui-patterns, deploy, symptom-fix), and a
complete copyable `templates/` app (app.yaml, databricks.yml, requirements.txt, .gitignore, app.py,
lib/{config,lakebase,warehouse,serving,identity}.py, pages/1_Example.py).

Highest-value load-bearing rules it encodes: shell-wrap the app.yaml command (`bash -c`) or
`${DATABRICKS_APP_PORT}` is literal and the app crashes; Lakebase password = a refreshing OAuth token;
declare resources with permissions for SP auto-grant; sync.exclude the venv from deploy #1; rules-first
LLM-as-enhancement; `st.rerun` is the live cascade; `LIKE … INCLUDING ALL` forks a Lakebase schema.
The `symptom-fix.md` register is the turn-by-turn debugging of the real build. See [[mke-genie-app-enablement]].


---
