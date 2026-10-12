# P1 Actions App — Technical Design (roadmap step 3)

**Milwaukee Tool · Supply Chain on Databricks · the real-time, actionable App**
**Status:** DESIGN — for your approval before any build. Written 2026-08-31, profile `mke-rsc`
(adb-4482605715640778), warehouse `7bd33a82f4e92206`.

---

## 0b. Design principle (user directive 2026-08-31): the app must TEACH, not assume

> *"For someone to come to the app, they'd have to already know everything, then just do it. That's not
> how it works. You need to get the complete understanding of the business and the system through the app
> itself."* — and *"the design/capability is doubtful"* after seeing empty panels + leftover scaffold.

Re-scope: the app is **self-explanatory**. A planner who has never seen this project should, from the app
alone, understand (a) what problem they're looking at, (b) why it matters (the $ and the risk), (c) what
each number means, (d) what to do and what happens if they do. Concretely:
- **Every page opens with a one-line "what this is / why it matters"** context strip (not a bare table).
- **Every metric has an inline explainer** (hover/`?`): "stockout risk $ = (safety stock − on-hand) × unit
  cost; below-floor means you'll miss orders."
- **The Scenarios page is a guided tour** of the business situations we uncovered — story → reasoning →
  the live data/chart → recommended + probable actions — so the app itself onboards the user.
- **No empty states that look broken**: if data is loading/unavailable, say so with the reason, never a
  bare "0 / —".
- **No leftover scaffold**: the Dashboard tab shows OUR data, not the template's demo charts.

## 0. TL;DR

The dashboard and Genie **tell you what's wrong and what to do** — but a planner still has to leave the
screen and act somewhere else (Oracle, Excel, email). This App closes that loop: a planner sees the
ranked exception queue, asks *why*, gets a recommended PO action, **clicks approve, and the state changes
live and is recorded with a full audit trail** — a governed *proposed → approved → executed* workflow.
Per the project guardrail, the external Oracle push is **SIMULATED** (recorded in Lakebase + published to
`sandbox_operations.po_management`), never a real write to Oracle/prod.

It reuses everything we built: the `sdp_*` gold as the read-only truth, the Genie Space as the in-app
"ask why," and adds the ONE thing they lack — **a transactional write surface (Lakebase) with
human-in-the-loop actions.**

---

## 1. The problems we are solving (why this App exists)

| # | Problem today (dashboard + Genie) | What the App adds |
|---|---|---|
| P1 | **Insight without action.** The dashboard shows "2,240 items newly off-plan, $24M exposure"; Genie says "cancel this PO / alert this planner." But the planner must then go to Oracle/Excel to actually do it. The loop is broken. | A **click-to-act** surface: approve / reject / expedite / pull-in / push-out / cancel / rebalance, in-app. |
| P2 | **No memory of decisions.** Nothing records that a planner reviewed item X, chose to expedite, and why. No audit, no accountability, no learning signal. | An **append-only audit trail** per action (who, when, what, why, which tool) — a standalone timeline. |
| P3 | **No human-in-the-loop control.** Genie can *recommend* an action but there is no approval gate, no "proposed → approved → executed" state machine, no way to reject/override. | A **hard approval gate**: the agent drafts, the human approves; only then does the write fire. |
| P4 | **Weekly cadence ≠ operational cadence.** The dashboard is correctly weekly (plan changes weekly). But *actions* are per-click and must reflect instantly to every user. A weekly Delta table can't do that. | A **real-time OLTP plane (Lakebase Postgres)** for action state — sub-ms reads, instant writes, live cascade. |
| P5 | **No bulk / workflow.** Red Keychain B.4 requires acting on many exceptions at once; planners group POs. The dashboard is one-row-at-a-time read-only. | **Bulk actions** (select N exceptions → apply) + a per-action workflow state. |
| P6 | **No feedback loop.** Planner overrides and outcomes are lost — the recommender can't learn (Red Keychain NEW-18). | Every decision (accepted / overridden / rejected + reason) is captured, publishable back to Delta as a **learning signal**. |
| P7 | **No safe writeback path.** Requirements demand PO changes flow to Oracle (B.3, NEW-6); the guardrail forbids any real external/prod write in this engagement. | A **typed, auditable, SIMULATED writeback** (action_request → approval → outbox → result), all in sandbox — demonstrable and swappable for a real integration later, without touching prod now. |

**One-line framing:** Dashboard = *see it*. Genie = *ask why / what*. **App = *do it, safely, and remember it.***

> **The user's north star (2026-08-31):** *"After all this information and insight, one finds it hard to
> take action. The cockpit just sits in the dashboard. Only through the App and actions can one actually
> fly."* The dashboard is where you **sit and understand**; the App is where you **act**. Every dashboard
> tile currently dead-ends at "…now what?" — the App turns each dead-end into a governed action.

### Dashboard tile → App action (the "next level" mapping)

Each read-only insight on the SDP dashboard gets a matching *verb* in the App:

| Dashboard tile (where you get stuck) | App action (how you fly) |
|---|---|
| Monday Cockpit "your action list" (EXPEDITE/DEFER/FIX/REVIEW) — read-only | **Click the verb → propose → approve → executed** (audit + simulated PO push) |
| Overview "Stockout-risk $ below safety stock" | Queue filtered to stockout → **EXPEDITE / PULL-IN / NEW-PO** per item |
| Overview "Excess capital >3× SS" | Overstock queue → **PUSH-OUT / CANCEL** inbound |
| Exception Queue "$ at risk, chronic flag" | **Bulk-select → apply one action** to N items (Red Keychain B.4) |
| Page 6 "Long at 2012 / short at 2120" (rebalance candidate) | **REBALANCE / TRANSFER** action (order-vs-rebalance, NEW-3) |
| Page 7 "receipt timing % late, chronic supplier" | **FIX SUPPLIER** (systemic) vs **EXPEDITE** (one-off) decision |
| Accuracy "persistently biased items (correctable)" | **REVIEW / RE-PLAN** flag routed to the owning planner |
| Any tile "who owns this?" (planner) | Action is **OBO-attributed + routed**, audit trail per planner |
| "what changed / plan nervousness" | Every decision is **remembered** (audit) → feedback loop (NEW-18) |

The App also **embeds the dashboard** (analytics tab) and **the Genie space** (ask-why panel) — so "sit &
understand" and "act & fly" live in one surface, but the *acting* is what the App uniquely adds.

---

## 2. What we already have (the App stands on this — no rebuild)

| Asset | Role in the App |
|---|---|
| `sandbox_operations.po_management.sdp_plan_vs_actual` (gold, 180d, item×org×week) | Read-only source of the exception queue + record detail |
| `sdp_exceptions`, `sdp_order_stage_gold`, `sdp_agg_*` serving MVs | The at-risk subset, PO-timing/chronic-supplier, KPI tiles |
| SDP pipeline `p1_actuals_sdp` + weekly Job | Keeps the gold fresh (weekly) — the App reads its output |
| Genie Space `01f1a542c3f7132681b64d8ff08b4033` | The in-app "Ask Genie / why is this flagged?" panel |
| AI/BI dashboard `01f1a537…` | Embedded as the App's analytics tab (iframe, SSO) |
| Red Keychain requirements (18 exception types, PO actions, bulk, feedback) | The **action catalog** the App executes |

**Gap the App fills:** none of the above can *write*. Delta/UC tables are read-only for OLTP; Genie
recommends but can't execute. The App adds the write plane + the workflow + the governance.

---

## 3. Architecture — the two-plane model (from the app skill, mapped to MKE)

```
        UNITY CATALOG (governance boundary)
  PLANE A — OLAP (read-only truth)          PLANE B — OLTP (serving + WRITE)
  sandbox_operations.po_management.sdp_*     Lakebase Postgres  (NEW project: mke-po-actions)
   • sdp_plan_vs_actual  (fact)      ─sync─▶  schema  app_po.*
   • sdp_exceptions (at-risk queue)  ─sync─▶   • mirror_exceptions   (read-only copy)
   • sdp_order_stage_gold (PO timing)─sync─▶   • mirror_order_stage   (read-only copy)
   • sdp_agg_scorecard / _overview   ─sync─▶   • mirror_kpi           (read-only copy)
                                               • action_request  ◀── THE ONE WRITABLE TABLE
                                               • action_audit_event (append-only trail)
                                               • integration_outbox + integration_result (SIMULATED Oracle)
                                               • conversations / messages / feedback (chat state)
                          ▲                                    ▲
                    SQL Warehouse / Genie              Lakebase pool (pg, sub-ms)
                          └───────────────┬──────────────────┘
                     ┌───────────────────▼───────────────────┐
                     │  DATABRICKS APP (Node + Express + React)│
                     │  AppKit plugins: server, lakebase,      │
                     │   analytics, genie                      │
                     │  • Exception queue (reads mirror)       │
                     │  • Ask-Genie panel (why is X flagged?)  │
                     │  • Action workflow (proposed→approved→  │
                     │     executed; reject/override; bulk)    │
                     │  • Embedded AI/BI dashboard tab         │
                     └───────────────────┬────────────────────┘
             every model call ─▶ MLflow trace (+ optional AI Gateway)
             every write ─▶ OBO-stamped (planner email) + audit row + dataMutated → live UI
             publish step ─▶ writes action history back to sandbox_operations.po_management (Delta)
```

**Two-speed by design (the distinction we discussed):** heavy analytics precomputed **weekly** (SDP →
Delta → dashboard); operational action state **real-time** (Lakebase). The App layers real-time on top of
the weekly facts; the weekly pipeline never constrains it.

---

## 4. The core loop (the load-bearing contract — preserve exactly)

```
Planner opens App → exception queue (ranked by $ / unit-miss, from Lakebase mirror)
  → clicks a red item → detail drawer (plan vs actual, variance, chronic-supplier, weeks of cover)
  → "Why is this flagged?" → Genie investigates (NL→SQL over sdp_*) → explanation + the records
  → App proposes an ACTION (from the 18-type catalog) with $ impact + rationale
  → planner APPROVES  (hard human gate)
  → execute_action(): ONE Lakebase transaction — action_request.status=executed,
       approved_by=<OBO email>, append audit_event, enqueue integration_outbox (SIMULATED)
  → UI cascades LIVE: item flips to "actioned", exposure KPI drops, queue re-sorts (no reload)
  → publish step later writes the action to sandbox_operations.po_management.action_outcome_history (Delta)
```

**Three enforcement points (non-negotiable, from the skill):**
1. **Approval gate** — write tool never fires until the planner explicitly approves.
2. **`dataMutated` cascade** — the moment the write commits, the UI refetches and visibly updates. If it
   doesn't cascade live, "it's just another chart."
3. **Attribution + audit** — every write is OBO-stamped with the planner's email + an append-only audit row.

---

## 5. The action catalog (mapped from Red Keychain's 18 exception types)

The App's action enum, grounded in what our data can actually detect from `sdp_*`:

| Exception (Red Keychain) | Detected from | Recommended action(s) |
|---|---|---|
| Demand exceeds supply / stockout (SS violation #1,#8) | actual_end_on_hand < planned_safety_stock | **EXPEDITE**, **PULL-IN PO**, **NEW PO** |
| Excess inventory vs target (#2) | actual > 3× safety stock | **PUSH-OUT PO**, **CANCEL PO**, **REBALANCE** |
| PO past due (#12) / supplier late (#7) | sdp_order_stage_gold slip_days, chronic_pct_late | **EXPEDITE**, **FIX SUPPLIER** (systemic) |
| Plan vs actual receipt variance (#18) | onhand_variance_* off-plan | **REVIEW**, reconcile |
| Inventory imbalance across DCs (#15) | long at 2012 / short at 2120 (shared item) | **REBALANCE / TRANSFER** |
| Demand forecast changed (#14) | wow_onhand_delta, plan nervousness | **REVIEW / RE-PLAN** |

Every action carries: `$ at risk`, `systemic vs one-off`, planner, and a drafted rationale. **Bulk** =
select many queue rows → apply one action type → one batched transaction (Red Keychain B.4).
**Requested-vs-Confirmed (NEW-1)** and **Order-vs-Rebalance (NEW-3)** are modeled as fields on the action
so the workflow is realistic and future-ready.

### Full action verb set (creative, forecast-driven — user ask 2026-08-31)

Beyond cancel/expedite, the agent reasons over a richer verb set, choosing by the forecast + gap:

| Verb | When (often forecast-driven) |
|---|---|
| `EXPEDITE` | below safety stock now / forecast breaches SS soon → pull inbound in |
| `PULL_IN` | forecast dips before the next PO lands → move a PO earlier |
| `PUSH_OUT` | forecast shows demand dropped / overstock building → delay inbound |
| `CANCEL` | forecast well above 3× SS through horizon → cancel inbound |
| `NEW_PO` | coverage gap with no open PO in the forecast window |
| `INCREASE_QTY` | forecast trending **up** → order more than planned |
| `DECREASE_QTY` | forecast trending **down** → trim the planned order (the 100→75 case) |
| `WAIT_HOLD` | forecast uncertain / wide interval → hold a week, re-evaluate (avoid churn) |
| `SPLIT_SHIPMENT` | partial-now + rest-later beats one late truck |
| `REBALANCE` | long at 2012 / short at 2120 same item → transfer instead of buy |
| `SUBSTITUTE` | transition SKU / obsolescence — run down old, cover with new |
| `ESCALATE` | frozen-zone violation or > Tier-3 → route to supply leader |
| `REVIEW` | not clearly actionable — flag for planner judgment |

The agent's `rank_actions` proposes; `what_if` quantifies each with the live forecast; the planner picks.

### Decision capture → MLflow evaluation dataset (the learning loop — user ask 2026-08-31)

**Every action records what the agent recommended AND what the human actually did, with a reason.** This is
the highest-value data the App produces (Red Keychain NEW-11 "codify tribal knowledge" + NEW-18 feedback).

`action_request` carries: `recommended_action`, `recommended_qty` (what the agent proposed),
`final_action`, `final_qty` (what the planner committed), `override_reason` (free text: *"cut 100→75,
launch demand not real yet"*), `was_overridden` (bool). On execute, we also **log an MLflow evaluation
record** — inputs (item context + forecast), the agent's recommendation, the human's final decision, and
the reason — to a dedicated MLflow experiment. Two payoffs:
1. **Evaluation dataset**: agent-recommendation vs human-decision pairs → measure agreement rate, where the
   agent is trusted vs overridden, by action type / planner / ABC.
2. **Improvement signal**: the override reasons are training/eval material to tune the recommender and the
   agent prompt over time. Even before any model retrain, you *have* the labeled dataset.

These override+reason rows also publish to Delta (`action_outcome_history`) so the learning signal is
durable and queryable alongside the plan-vs-actual gold.

---

## 5b. Chat + agentic AI + live forecasting (what-if) — the "fly" engine

The App ships an **in-app chat dock** (SSE streaming) driven by a **tool-calling agent** (AppKit `agents`
plugin → `databricks-gpt-oss-120b`, Claude Opus fallback). The agent runs a strict **Discover → Draft →
Act** chain and never writes until the planner approves. Tool catalog:

| Tool | What it does | Backed by |
|---|---|---|
| `ask_data` | Natural-language "why is this flagged?" → SQL over `sdp_*` | our **Genie space** `01f1a542…` (poll loop) |
| `find_record` | Pull one item's live state + trajectory | Lakebase `mirror_trajectory` |
| `forecast_item` | **Live forecast** of on-hand / weeks-of-cover forward N weeks | **`ai_forecast()`** on the SQL warehouse |
| `what_if` | Simulate an action's effect: re-forecast with the candidate PO change applied, return the **projected stockout date shift + $ delta** | `ai_forecast()` on a *modified* series |
| `rank_actions` | Score candidate actions (EXPEDITE/CANCEL/…) by benefit + capacity | heuristic now; UC model-serving later |
| `draft_note` | Write the rationale that goes on the action | the LLM |
| `execute_action` | **The write** (behind the approval gate) | Lakebase `action_request` txn |

### Live forecasting with `ai_forecast()` (the what-if core)

`ai_forecast()` is a Databricks SQL TVF: given a time series (time_col, value_col) it returns a forecast
with prediction intervals. The App uses it two ways:

1. **Baseline forecast** — `forecast_item`: feed the item's weekly `actual_end_on_hand` history →
   forecast the next ~8 weeks → overlay the **safety-stock floor** → the chart shows *"projected to breach
   safety stock in week N"* (turns a static trajectory into a forward-looking risk).
2. **What-if simulation** — `what_if`: take the SAME history but **apply the candidate action** to the
   forward supply signal (e.g. *CANCEL* removes an expected inbound receipt; *EXPEDITE* pulls one earlier;
   *PUSH-OUT* delays it), re-run `ai_forecast()`, and return **baseline vs simulated**: the projected
   stockout-week shift and the $ exposure delta. This is *"what if I cancel this — what happens"* answered
   with a live model, not a guess.

**VERIFIED signature (live-tested 2026-08-31 on wh 7bd33a82f4e92206, hero item 48111881X):**
`ai_forecast(TABLE(...), horizon => <END-DATE string, NOT an int count>, time_col => '<timestamp col>',
value_col => '<double col>')` → returns `ds, y_forecast, y_lower, y_upper`. Gotchas found: `time_col`
must be a **timestamp** (use `to_timestamp(week_start)`), `value_col` must be **DOUBLE** (`CAST(... AS
DOUBLE)`), and `horizon` is a **target end date** (e.g. `'2026-10-05'`), not `8`. Baseline on the hero
item projects on-hand ~137K→144K over 5 weeks with intervals — the safety-stock floor overlay is what
turns it into a stockout-risk forecast.
```sql
-- baseline (VERIFIED shape)
SELECT ds, y_forecast, y_lower, y_upper FROM ai_forecast(
  TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
        FROM sandbox_operations.po_management.sdp_plan_vs_actual
        WHERE item_id = :item AND organization_code='2012' AND actual_end_on_hand IS NOT NULL),
  horizon => :end_date, time_col => 'ds', value_col => 'y') ORDER BY ds;
-- what-if: same call over a series with the candidate action applied to future supply
```
The what-if result feeds the agent's recommendation ("cancelling delays stockout 3 wks and frees $X; but
you breach safety stock in wk 6 — recommend PUSH-OUT instead") and is shown as a **baseline-vs-simulated
chart** in the detail drawer before the planner approves.

**Fallback ladder (degrade, don't loop):** if `ai_forecast()` isn't available or errors, `forecast_item`
falls back to a naive trend (last-value / linear) so the what-if still renders with a clear "heuristic,
not modeled" badge — never a dead panel.

## 6. Lakebase data model (schema `app_po`)

**Read-only mirrors** (synced/copied from Delta; app never writes):
`mirror_exceptions` (from sdp_exceptions), `mirror_plan_vs_actual` (bounded: at-risk + sample),
`mirror_order_stage` (from sdp_order_stage_gold), `mirror_kpi` (from sdp_agg_scorecard/overview).

**The ONE writable table — `action_request`:**
`id, item_id, organization_code, week_start, exception_type, action_type, dollar_at_risk,
systemic_flag, planner_name, drafted_note, requested_qty, confirmed_qty (NEW-1),
decision_mode (order|rebalance, NEW-3), status (proposed→approved→executed|rejected|overridden),
approved_by (OBO email), audit_trail (jsonb, append-only), version, created_at, decided_at.`

**Supporting writable tables:** `action_audit_event` (append-only), `integration_outbox` +
`integration_result` (SIMULATED Oracle push — typed request, never a real Oracle call),
`conversations`/`messages`/`feedback` (chat state).

**Publish-back:** a governed step writes executed actions to
`sandbox_operations.po_management.action_outcome_history` (Delta) — the durable history + feedback signal
(Red Keychain NEW-18). Never writes prod.

---

## 7. Governance & guardrails (how this stays inside the lines)

- **prod_edw / prod_operations: READ-ONLY.** The App reads only `sandbox_operations.po_management.sdp_*`.
  It never queries prod directly and never writes prod.
- **All App writes → Lakebase (`app_po.*`) + publish only to `sandbox_operations.po_management`.**
- **NO real Oracle/external writeback — ever, this engagement.** The `integration_outbox`/`_result`
  tables *model* the typed action request + result so the full loop is demonstrable and auditable; the
  actual external push is explicitly out of scope (guardrail 2026-08-31). This satisfies Red Keychain B.3
  / NEW-6 *as a simulated, swappable lane*, not a live integration.
- **OBO auth** stamps every write with the planner's identity; **MLflow** traces every agent turn;
  **AI Gateway** (optional, layer 4) caps spend + logs model calls.
- **New Lakebase project only** — `mke-po-actions`. The 6 existing projects (data-audit-app, milwaukee-led,
  operations-lakebase, app-shared, metadata-app, vn-tag-nailer-raw) are OFF-LIMITS (user directive).
- **Deploy-before-run**: the app SP must create/own the `app_po` schema (Lakebase ownership rule) — deploy
  first, then any local dev.

---

## 8. Build plan (vertical slice first, then widen — from the skill's playbook)

| Phase | What | Acceptance |
|---|---|---|
| **0. Foundation** | Already done (sdp_* gold, Genie, dashboard). | ✅ exists |
| **1. Lakebase** | Create NEW project `mke-po-actions`; schema `app_po` (mirrors + action_request + audit + outbox + chat); sync from sdp_*. | app boots; mirror rows > 0; action_request empty |
| **2. Backend skeleton** | AppKit `server+lakebase+analytics+genie`; migration gate; OBO; MLflow; routes. | /api/config, /api/records, /api/kpis respond |
| **3. Visualize** | Exception queue + KPI tiles + detail drawer, reading the mirror; `dataMutated` wired. | queue shows the red cluster; KPIs match dashboard |
| **4. Ask-why** | Genie panel in the drawer (our Space) → "why is X flagged?" streams + cites records. | ask "why 369229?" → explanation + rows |
| **5. Act (the vertical slice)** | ONE action end-to-end: propose → approve → execute_action() transaction → audit → dataMutated → live cascade. | approve → queue re-sorts, KPI −$, audit gains a row, no reload |
| **6. Workflow + bulk** | reject/override + reason; bulk select→apply; requested-vs-confirmed; order-vs-rebalance. | multi-select 5 → apply → 5 actions in one txn |
| **7. Simulated writeback** | integration_outbox enqueue on execute; integration_result mock; publish action_outcome_history to Delta. | outbox row per executed action; Delta history grows |
| **8. Analytics tab + govern** | embed AI/BI dashboard (iframe SSO); route model calls via AI Gateway; MLflow feedback. | dashboard loads under SSO; calls logged/capped |
| **9. Deploy** | DABs/CLI; verify OBO, Lakebase read_write, genie scope; smoke-test full arc on the deployed URL. | full loop works on the app URL |

**Vertical-slice discipline:** get ONE item → one recommendation → one approved write → one live cascade
working (phase 5) before widening to bulk/analytics. The `dataMutated` cascade is the highest-risk,
highest-payoff behavior — prove it early.

---

## 9. What I will create (resources), pending your OK

1. **Lakebase project** `mke-po-actions` (new; auto-creates `production` branch + `databricks_postgres`).
2. **Databricks App** `mke-po-actions` (AppKit; features: server, lakebase, analytics, genie).
3. **App SP wiring**: lakebase resource (read_write on the new project), the Genie space scope, the
   warehouse (7bd33a82f4e92206) for sync/analytics, MLflow experiment. (You authorized SP access wiring.)
4. **Delta publish target**: `sandbox_operations.po_management.action_outcome_history` (new table, sandbox).

**I will NOT:** touch prod, touch the 6 existing Lakebase projects, write to Oracle, or disturb the live
dashboard / Genie space / SDP pipeline (all stay as the read-only foundation).

---

## 10. Risks & how the design handles them (challenge-myself section)

| Risk | Mitigation |
|---|---|
| SP schema-ownership permission errors (the #1 Lakebase-app trap) | Deploy the app FIRST so the SP creates+owns `app_po`; only then dev locally. |
| Synced-table read-permission gotcha | Use the one-shot SQL-Statements sync into app-owned mirror tables (app owns them) rather than managed synced tables that need an explicit grant. |
| Live cascade doesn't fire | Follow the skill's contract exactly: write tool returns dataMutated; client emits on turn-end; every view subscribes. Prove in phase 5. |
| Overbuilding | Vertical slice first; bulk/govern/analytics are later phases, not day one. Minimum sufficient architecture (project guardrail). |
| Guardrail drift toward a real Oracle write | The outbox is explicitly a SIMULATED sink; no Oracle credentials exist in the app; documented + logged. |
| Two dashboards / which data | App reads `sdp_*` only (the fast, verified stack); embeds the SDP dashboard. Legacy stack untouched. |

---

## 11. Open decisions for you (before I start phase 1)

1. **App + project name** — proposed `mke-po-actions` (≤26 chars, hyphens). OK, or prefer another?
2. **Scope of the slice** — start with the **stockout/expedite** action on org 2012 (biggest $), then widen
   to the other exception types? (Recommended.)
3. **Agent runner** — Genie-only "ask why" first (simplest, reuses our Space), add a full tool-calling
   agent (rank_actions via a model endpoint) in a later phase? (Recommended: Genie-first.)
4. **AI Gateway governance** — include in the first build, or add in phase 8? (Recommended: phase 8.)

On your OK to this document, I start at **Phase 1 (create the new Lakebase project)** and build the
vertical slice through **Phase 5 (one approved action cascading live)** before widening.
