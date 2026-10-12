<div align="center">

# 🏛️ Data Architecture Decision — Serving the Root-Cause Workbench

### Should the UI read raw `prod_edw`, or a purpose-built model? (ADR)

**Companions:** [`supply_day3_ux_design_v2.md`](supply_day3_ux_design_v2.md) · [`supply_day3_gap_tables.md`](supply_day3_gap_tables.md) · [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md)
**Status:** **Proposed** — recommendation for review before UI build begins.
**Scope:** the *analytical serving* layer behind the Supply Root-Cause Workbench (Watchlist, Waterfall, Coming-Risk, Patterns, Scenario). Transactional state is settled separately (Lakebase).
**Guardrail context:** `prod_edw` / `prod_operations` are **READ-ONLY**; all derived/serving tables land in `sandbox_operations.po_management`; all app state in **Lakebase**.

</div>

---

> ## 🎯 Decision in one line
> **Don't point the UI straight at raw `prod_edw` (too slow/coupled at the aggregate screens), and don't
> build a grand new datamodel upfront (overengineering before validation). Build a thin, slice-scoped Gold
> serving layer in `sandbox_operations.po_management` that grows into the real pipeline as the UX validates —
> with Lakebase for all transactional state.** Least-regret, and it reuses the pattern the project already
> proved (`p1slice_*`, `sdp_*`).

---

## 📑 Contents
1. [The question — and why it's a false binary](#1--the-question-and-why-its-a-false-binary)
2. [The three data roles the UI actually needs](#2--the-three-data-roles-the-ui-needs)
3. [Option A — UI directly on raw prod_edw](#3--option-a--ui-directly-on-raw-prod_edw)
4. [Option B — big new datamodel upfront](#4--option-b--a-big-new-datamodel-upfront)
5. [Option C — thin slice-scoped serving layer (recommended)](#5--option-c--thin-slice-scoped-serving-layer-recommended)
6. [Why C wins — the decision matrix](#6--why-c-wins--decision-matrix)
7. [The serving model — concretely](#7--the-serving-model-concretely)
8. [Refresh, freshness & the hybrid live-drill](#8--refresh-freshness--the-hybrid-live-drill)
9. [Sequencing — slice before pipeline](#9--sequencing--slice-before-pipeline)
10. [Risks, caveats & the throwaway-demo exception](#10--risks-caveats--the-throwaway-demo-exception)
11. [Decision & next actions](#11--decision--next-actions)

---

## 1 · The question — and why it's a false binary

The question posed:

> *"Do we build the UI directly on the existing tables, or create a pipeline / a transactional-newer datamodel
> to make it available in a better way and make the UI faster — or not go that route and just build the UI first?"*

This looks like a two- or three-way choice, but it conflates **two different data problems** that have
**different right answers**:

- **Reading data fast for charts** (analytical serving) — this is where the "raw vs modeled" tension is real.
- **Writing workflow state** (drafts, actions, the log) — this is *not* a choice; the write guardrail already
  dictates **Lakebase**, and the project has it wired for the demand + PO-actions apps.

So the real decision is narrower and answerable: **for the analytical serving layer, do we query raw
`prod_edw` live, pre-shape it into a serving model, or something in between?** The sections below answer
exactly that.

---

## 2 · The three data roles the UI needs

The workbench touches data in three distinct roles. They **coexist** — they don't compete:

```
┌──────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
│  1. SOURCE OF TRUTH       │   │  2. ANALYTICAL SERVING    │   │  3. TRANSACTIONAL STATE   │
│  prod_edw / prod_ops      │──►│  sandbox_operations.      │   │  Lakebase (Postgres)      │
│  (READ-ONLY, guardrail)   │   │  po_management (Gold/MV)  │   │                           │
│  13.4B / 17.8B row facts  │   │  small, denormalized,     │   │  drafts, locks, comments, │
│  the plan snapshots,      │   │  screen-shaped read model │   │  action_request, scenario │
│  demand, POs, inventory   │   │  ← THE DECISION IS HERE   │   │  inputs, the action log   │
└──────────────────────────┘   └──────────────────────────┘   └──────────────────────────┘
        read/derive                  refresh via Job                 app reads/writes live
```

| Role | What it holds | Where | Decision status |
|---|---|---|---|
| **Source of truth** | raw plan/demand/PO/inventory facts | `prod_edw`, `prod_operations` | **Settled** — read-only, never write |
| **Analytical serving** | the screen-shaped read model (waterfall buckets, rankings, forward risk) | `sandbox_operations.po_management` | **← this ADR** |
| **Transactional state** | drafts, actions, scenarios, log | Lakebase | **Settled** — write guardrail + existing apps |

**Key insight:** "make the UI faster" is a *role-2* concern. It is **not** solved by a transactional datamodel
(role 3) — a transactional/OLTP model is for *writes*, and Lakebase already owns that. Confusing "faster reads"
with "transactional model" is the subtle trap in the original question. Fast reads come from a **pre-shaped
analytical serving layer**, not from an OLTP schema.

---

## 3 · Option A — UI directly on raw `prod_edw`

*Every screen issues live SQL against the 13.4B / 17.8B-row facts.*

### Where it's actually fine
- **Single-SKU deep-drill.** An investigation filtered to `latest process_date + plan + item + org` touches a
  tiny slice — fast and cheap. The v1 hero path *for one SKU* works live.

### Where it breaks
| Problem | Detail | Which screens hit it |
|---|---|---|
| **Aggregate scans** | "rank *all* at-risk SKUs by $", forward-risk across ~110 weeks, patterns across the book, chronic across 55 snapshots — these scan **across all SKUs × many snapshots**, not one slice | Watchlist, Coming-Risk, Patterns, Chronic |
| **Cost per page load** | every visit re-runs heavy aggregation on a warehouse — real $ and seconds, repeated | all overview screens |
| **Semantic drift** | waterfall buckets, "likely cause", two-tone gap, SS-at-lead-time are *derivations*; if every screen (and Genie, and the next app) re-derives them in its own SQL, they diverge | everywhere |
| **Coupling** | app latency/availability tied to the raw EDW; no clean home for *derived* history (chronic counts, snapshot diffs) which by guardrail must live in `sandbox_operations.po_management` anyway | architectural |

**Verdict:** ✅ fine for a **single-SKU demo**; ❌ not for the aggregate screens that make the product valuable.

---

## 4 · Option B — a big new datamodel upfront

*Design a full transactional/dimensional remodel (star schema, conformed dims, the works) before building screens.*

### Why it's tempting
- Clean semantics, one place, "enterprise-grade."

### Why it's the wrong first move
| Problem | Detail |
|---|---|
| **Overengineering** | violates the project's core rule — *minimum sufficient architecture, don't overengineer.* You'd model for screens planners haven't reacted to yet. |
| **Premature — requirements are still moving** | they moved **twice in this very session** (org rollup, promo/base). Modeling before UX validation bakes in assumptions that will change. |
| **Slow to first value** | weeks of modeling before a planner sees anything — the opposite of the 2-week-sprint, rapid-iteration mandate. |
| **A transactional model is the wrong tool anyway** | OLTP normalization optimizes writes/consistency; the read screens want *denormalized, pre-aggregated* data. A transactional datamodel would make the UI **slower**, not faster, for these reads. |

**Verdict:** ❌ premature and mis-targeted. The right *analytical* model emerges *after* the slice validates the semantics — and it's a **serving (denormalized) model, not a transactional one.**

---

## 5 · Option C — thin slice-scoped serving layer (recommended)

*A small set of purpose-built Gold tables / materialized views in `sandbox_operations.po_management` that
pre-compute exactly what the screens read — nothing more. Lakebase for all state. Exactly the pattern the
project already proved with `p1slice_*` and the `sdp_*` MVs.*

```
  prod_edw (read-only)                sandbox_operations.po_management            the UI
  ┌────────────────────┐   weekly     ┌──────────────────────────────────┐      ┌──────────────┐
  │ 20_supply_daily     │──Lakeflow──► │ rc_serving_sku_week   (hero/watchlist)│─►│ Watchlist     │
  │ 10_demand_daily     │   Job        │ rc_forward_risk       (coming-risk)   │  │ Waterfall     │
  │ purchase_orders/…   │  (Monday     │ rc_snapshot_history   (chronic/gap)   │  │ Coming-Risk   │
  │ dim_series_ext_vw   │   snapshot)  │ rc_pattern_rollup     (patterns)      │  │ Patterns      │
  │ fact_sop_commitment │              │ rc_supplier_scorecard (supply drill)  │  │ Drills        │
  └────────────────────┘              └──────────────────────────────────┘      └──────┬───────┘
                                                                                        │ writes
                                        ┌──────────────────────────────────┐           ▼
                                        │ Lakebase: action_request, scenario,│◄──────────┘
                                        │ event_draft, log, outbox …         │
                                        └──────────────────────────────────┘
        (single-SKU deep-drill for a column not in the serving table → live prod_edw with tight filter)
```

### The principle
- **Denormalized, keyed to the grain the screens use** — the UI reads *one small table per screen*, instantly.
- **Semantics computed once** — waterfall buckets, likely-cause, SS-at-lead-time, gap-decomposition live in the
  serving layer (or governed views / a UC Metric View), so Genie and the next app reuse the same definitions.
- **Derived history has a home** — chronic counts, forward-risk crossings, snapshot diffs land where the
  guardrail requires (`sandbox_operations.po_management`).
- **Minimum sufficient** — it's *thin*: a handful of tables shaped to the confirmed screens, not a speculative
  warehouse.

**Verdict:** ✅ fast UI *and* no over-investment before validation. Reuses an in-project, already-proven pattern.

---

## 6 · Why C wins — decision matrix

| Criterion | A: raw prod_edw | B: big model upfront | **C: thin serving layer** |
|---|:--:|:--:|:--:|
| Aggregate-screen speed | ❌ slow | ✅ | ✅ |
| Single-SKU drill speed | ✅ | ✅ | ✅ (or live-drill) |
| Warehouse cost per load | ❌ high | 🟡 | ✅ low |
| Semantic consistency (across screens/Genie) | ❌ drifts | ✅ | ✅ |
| Time to first planner value | ✅ fast | ❌ slow | ✅ fast (slice) |
| Respects "don't overengineer" | ✅ | ❌ | ✅ |
| Respects write guardrail / derived-history home | 🟡 | ✅ | ✅ |
| Survives moving requirements | ✅ (nothing built) | ❌ (baked in) | ✅ (grows with UX) |
| Reuses proven project pattern (`p1slice_`/`sdp_`) | — | — | ✅ |

**C dominates** on every axis that matters once you move past a 2-SKU demo.

---

## 7 · The serving model — concretely

*The "read model" the UI wants — denormalized, screen-shaped. Names illustrative; all in `sandbox_operations.po_management`.*

### 7.1 · `rc_serving_sku_week` — the spine (Watchlist + Waterfall hero)
Latest snapshot, one row per **SKU × org × forward-week**, with derivations pre-computed.

| Column group | Columns (pre-computed) | Sourced from |
|---|---|---|
| Keys | `item_id`, `org_code`, `designated_org_code`, `date_key`, `process_date` | dims |
| Position | `projected_available_balance`, `on_hand`, `safety_stock` | `20_supply_daily` |
| **Derived: gap** | `ss_gap` (= PAB − SS), `shortfall_units` (= max(0, SS − PAB)) | computed |
| **Derived: waterfall buckets** | `demand_variance`, `supply_variance`, `holds_variance` | computed (demand/PO/hold facts) |
| **Derived: likely cause + confidence** | `likely_cause` (Demand/Supply/Holds), `cause_confidence` | dominance ratio |
| **Derived: SS-at-lead-time** | `ss_at_lead_time`, `gap_at_lead_time` | `safety_stock` @ (snap + `complete_lead_time`) |
| Stakes | `std_cost`, `committed_value` | `dim_series_ext_vw`, `fact_sop_commitment` |
| **Derived: CLASSIFIER LAYER** ⭐ | `severity_class`, `temporal_class`, `recoverability_class`, `action_verdict`, `convergence_score`, `damage_control_path` | see below |
| Meta | `snapshot_date`, `freshness_ts`, `plan_name`, `<measure>_tier` (provenance) | provenance |

> One `SELECT ... WHERE item_id = ?` returns the whole hero screen. No 13.4B-row scan.

#### 7.1a · The classifier layer (the validation's structural contribution)
The validation (V10–V13) proved the biggest quality lever is **not another measure — it's a set of tags that
sit between "flag" and "action"** and decide *whether and how* to act. These are **pre-computed serving columns**
so the badge/verdict is data-driven, not re-derived per screen. This is the ADR's home for DK-13/14/15 + V10:

| Column | Values | Formula / source | From |
|---|---|---|---|
| `severity_class` | below-SS-target / projected-negative-PAB | `MIN(PAB)>=0` vs `<0` | V1 |
| `temporal_class` | acute / chronic / nervous | recurrence over snapshots; SS-target thrash | V10 |
| `recoverability_class` | RECOVERABLE / UNRECOVERABLE | `first_cross_week > today + complete_lead_time` — **per-SKU lead time, NEVER an average (bimodal 2d/122d)** | V13 |
| `action_verdict` | ACT / WATCH / DISMISS | near-term+physical=ACT; real-but-not-yet=WATCH; cushion-dip/transient=DISMISS | V12 |
| `convergence_score` | # active causes (1–3) | demand+supply+holds co-firing | V11 |
| `damage_control_path` | TRANSFER / ALLOCATE-ACCEPT | UNRECOVERABLE + in-network excess = TRANSFER (20%); else ALLOCATE (80%) | V13 (live: 1,845 vs 7,465) |
| `criticality_class` | A / B / C / Unclassified | `dim_series_ext_vw.inventory_abc_class` | V22 (A-class $67.8k/SKU = 2.1× C) |
| `demand_class` | smooth / erratic / intermittent / no-demand | ADI proxy (share of periods with demand) | V24 (~24% intermittent → SS/consumption low-confidence) |
| `lifecycle_class` | mature / transition / NPD | `items_scd1.transition_sku_flag` / `is_npd_item` | V15 (NPD ~9× over-represented) |
| `dormant_flag` | active / slow / dormant / never-shipped | last-ship recency (NOT `obsolete_date` — too sparse) | V23 ($545M never-shipped) |
| `intentional_hold` | Yes / No | `safety_stock_managed_flag='Yes'` (partial) — suppresses false dormant/excess flags | V26 ($450M managed) |

> **Verified impact (live):** these tags turn a **10,700-flag alarm** (of which only ~3,634 ever stock out,
> $372.5M unrecoverable) into a **triaged worklist** — `action_verdict=ACT` + `recoverability_class` +
> `convergence_score` are the columns the watchlist sorts and filters on. **The Job computes them once; every
> screen reads them.** Also feeds RCA-gating: run deep RCA only where `recoverability_class=UNRECOVERABLE` &
> material, or `temporal_class=chronic`.

### 7.2 · `rc_forward_risk` — Coming-Risk (G1)
One row per SKU×org with **first future SS-crossing**: `crosses_week`, `weeks_to_crossing`, `depth_at_low_point`,
`within_lead_time` (bool), `likely_cause`, `committed_value`. Pre-computed from the forward PAB curve.

### 7.3 · `rc_snapshot_history` — Chronic + Gap-decomposition (G5, G6)
Per SKU×org×target-week across snapshots: `weeks_below_ss_last_8`, `is_chronic`, and the
**gap split** `delta_from_consumption` vs `delta_from_target_refresh` (the SS-target movement across
`process_date` — proved live: 68→420). This is the one that *must* be pre-aggregated (multi-snapshot scans).

### 7.4 · `rc_pattern_rollup` — Patterns (G4)
Driver contribution aggregated by `supplier`, `mkedg5_customer`, `plant/org`, `planner` — ranked by total
$-at-risk across all at-risk SKUs. Refreshed with the spine.

### 7.4a · `rc_cause_week_heat` — Cause × week heatmap navigator (DK-22)
The pre-agg behind the recursive heatmap (UX v3 §S12). Grain = **(level, row_key, week) × one fixed
`process_date`**, cell = **commitment-$-weighted, signed** variance. It's a sibling of `rc_pattern_rollup` (same
cause/supplier/org rollup) but **retains the week axis** and is **level-stacked** so a click can re-query a
tighter subset instead of hitting the raw fact.

| Column | Meaning |
|---|---|
| `level` | `portfolio` / `product_line` / `supplier` / `pool` / `inv_org` — the drill tier |
| `row_key`, `row_label` | the heatmap row at that level (cause bucket / supplier / designated pool / member org) |
| `parent_filter` | inherited filters from the drill path (cause + week + org) — how a child subset is scoped |
| `week` (`date_key`) | column axis |
| `cell_value_signed` | `Σ (safety_stock − PAB) × committed_unit_value`, **sign preserved** (short<0-cover / excess) |
| `at_risk_flags` | raw count (for the "weeks-uniform-by-volume" honesty note, not the color) |
| `process_date` | the frozen vintage (no shimmer between levels) |
| `child_row_count` | # populated banding rows one level down → drives the **stop-rule** (< ~4 ⇒ leaf = SKU list) |

- **Refresh:** with the spine (weekly Monday snapshot). Convergence cells split fractionally by contribution
  (measures §4.5) so multi-cause weeks don't inflate.
- **Drill hops re-query this table** with a tighter `parent_filter`; the **leaf** (a cell with `child_row_count`
  below threshold, or the `inv_org` level) drops to the **live single-org SKU detail** — not stored here, keeping
  the pre-agg thin (the same hybrid rule as §8).
- **⚠ Populated-child rule:** `row_key` at the criticality level comes from the `dim_series_ext_vw` join, **never**
  the all-NULL `local_planning_abc_code` fact column (verified live). An all-null child is skipped, not rendered.

### 7.5 · `rc_supplier_scorecard` — Supply drill (G8)
Per supplier: `fill_rate`, `supply_miss_count`, `supplier_initiated_slips`, `chronic_slip` — from
`ops_scorecard_fill_rate_vw` + `purchase_order_change_orders`.

### 7.6 · Lakebase (state — not this layer, but named for completeness)
`action_request`, `action_audit_event`, `decision_eval`, `scenario`, `event_draft/lock`, `integration_outbox`,
`notification_delivery` — existing schema (Activity 9), extended with `scenario` + session timers.

**DK-21 extension — the suggested-vs-actual + savings fields** (on `action_request` / `action_outcome_history`):

| Field | Type | Purpose |
|---|---|---|
| `suggested_action` | text | the lever the recommender proposed |
| `suggested_value` | numeric | its projected Δ$ (had it been taken) |
| `actual_action` | text (typed) | the lever the planner actually took |
| `actual_value` | numeric | the taken action's Δ$ |
| `reasoning` | text | the planner's free-text thought process |
| `override_reason_code` | text | reuses the **DK-8 12-reason taxonomy** → `ai_classify`-able |
| `diverged` | boolean | suggested ≠ actual (drives the adoption-learning loop) |
| `savings_state` | enum | `projected` / `committed` / `realized` / `loss_avoided` / `dismissed` |
| `baseline_snapshot_id` | text | FK to the day's `rc_value_baseline_daily` row |

> **Capture is mandatory on action-close** (Screen G modal) — no silent logging. `override_reason_code` is a
> closed list so it stays classifiable; `reasoning` is free text for the human "why."

### 7.7 · `rc_value_baseline_daily` — Value-Ledger baseline (DK-21, Screen G)
The **only new serving table** for DK-21, in `sandbox_operations.po_management`. Start-of-day Job freezes the
watchlist exposure so the ledger has an honest 08:00 anchor and the day's incremental savings are measured
against a fixed point (not a moving one).

| Column | Source | Note |
|---|---|---|
| `baseline_snapshot_id` | generated (date + run) | PK; referenced by every action logged that day |
| `as_of_date` | run date | the "08:00" anchor |
| `at_risk_dollars` | Σ `shortfall_units × committed_unit_value` over ACT-worthy flags | commitment-weighted (`fact_sop_commitment`) |
| `at_risk_sku_count` | COUNT | headline SKU count |
| `unrecoverable_dollars` | Σ over `recoverability_class=UNRECOVERABLE` | the separate loss-avoidable pool (never "savings") |
| `process_date` | latest `20_supply_daily` snapshot | provenance |

**Realization publication:** a Lakebase→Delta Job (weekly, on the new snapshot) recomputes `savings_state` from
`projected`→`realized` by reading the forward low-point back and **subtracting found-inventory** (S10), writing
the confirmed outcome into `…action_outcome_history`. This is the *only* place the ✅ number is minted — the app
never mints it on click.

> **Semantic-layer note:** the derivations (gap, buckets, SS-at-lead-time, likely-cause) should be **defined
> once** — ideally as governed views or a **UC Metric View** feeding these tables — so Genie and any future app
> use identical definitions. This is the domain pattern's "define-once" rule.

---

## 8 · Refresh, freshness & the hybrid live-drill

### Refresh cadence
- **Weekly Lakeflow Job on the Monday snapshot** — matches the plan's own cadence. `20_supply_daily` /
  `10_demand_daily` update per snapshot; there is **no reason to serve fresher than the plan updates.**
- **On-hand** can refresh daily if the on-hand-sensitive tiles need it (cheap incremental).
- Snapshot-diff for **alerts** (G9) runs as part of the same Job (compare new vs prior `process_date`).

### The hybrid — don't over-stuff the serving tables
- A single-SKU deep-drill that needs a **column not in the serving model** can still hit `prod_edw` **live with
  a tight filter** (one SKU × one org × latest snapshot = fast). This keeps the serving tables *thin* — they
  hold what the *aggregate* screens need, not every column any drill might want.
- **Rule of thumb:** aggregate/ranked/multi-snapshot → serving table; single-entity raw detail → live drill.

### Why this is the freshness sweet spot
Serving weekly ≠ stale, because the *plan itself* is weekly. Showing the plan's Monday state is *correct*, not
lagging. On-hand and alerts get the finer cadence where it changes the decision.

---

## 9 · Sequencing — slice before pipeline

The project's own hard-won lesson (memory): **vertical slice before horizontal assets.** So even Option C is
**not** "build the whole serving layer first."

```
  WAVE 0 — SLICE (days)                WAVE 1 — WIDEN (after UAT)          WAVE 2 — INDUSTRIALIZE
  ┌────────────────────────┐          ┌────────────────────────┐         ┌────────────────────────┐
  │ rc_serving_sku_week for │          │ scale Job to ALL SKUs   │         │ add rc_forward_risk,    │
  │ ~12 hero SKUs only      │          │ validate buckets +      │         │ rc_pattern_rollup,      │
  │ (3697-22, 2941, …)      │   ──►     │ likely-cause survive    │  ──►    │ rc_snapshot_history,    │
  │ Watchlist→Waterfall→    │          │ planner UAT             │         │ rc_supplier_scorecard   │
  │ Demand drill→Escalation │          │                         │         │ + alerts Job            │
  │ + Lakebase session timers│          │                         │         │                         │
  └────────────────────────┘          └────────────────────────┘         └────────────────────────┘
   proves UX + semantics fast           semantics validated                 v2.1 capabilities light up
   on real data, low cost               BEFORE industrializing
```

1. **Wave 0 — slice, on a thin serving table for hero SKUs only.** Build the v1 hero path against a *small*
   Gold table populated for ~a dozen SKUs. Proves the UX and the semantics with real planners in **days**.
   **Start Lakebase session timers immediately** (can't reconstruct before/after later).
2. **Wave 1 — widen.** Once buckets + likely-cause survive planner UAT, scale the Job to all SKUs. Now the
   semantics are validated *before* you industrialize them.
3. **Wave 2 — industrialize the v2 capabilities.** Add the forward-risk, pattern, snapshot-history, and
   scorecard tables + the alerts Job — the L2/L3 screens.

**The point:** you get a fast UI from day one *and* you don't over-invest in a serving model before planners
confirm the semantics are right.

---

## 10 · Risks, caveats & the throwaway-demo exception

| Risk / caveat | Mitigation |
|---|---|
| Serving tables drift from source | idempotent weekly Job + reconciliation totals vs `prod_edw` (QA layer); label freshness in UI |
| Over-building the serving model too early | keep it *thin* — only screen-shaped tables; hybrid live-drill for long-tail columns |
| Semantic definitions still duplicated | define derivations once (governed view / UC Metric View) feeding the tables |
| Weekly refresh feels stale for on-hand | finer cadence only for on-hand/alerts tiles, not the whole model |
| Guardrail slip | serving tables **only** in `sandbox_operations.po_management`; state **only** in Lakebase; never write `prod_edw` |

### The one exception — throwaway demo
If the *only* near-term goal is a **demo for the next session** (not planners using it on their book), then
**skip even the serving table** and query `prod_edw` live for the 2 hero SKUs. Filtered to one SKU it's fast
enough, and you save a day. **The serving layer earns its keep the moment you go from "demo on 2 SKUs" to
"planners using it on their whole book"** — which is where the aggregate screens (Watchlist/Coming-Risk/Patterns)
live, and where live raw queries fall over.

---

## 11 · Decision & next actions

### Decision
**Adopt Option C — a thin, slice-scoped Gold serving layer in `sandbox_operations.po_management`, Lakebase for
all transactional state, refreshed by a weekly Lakeflow Job on the Monday snapshot, with a hybrid live-drill for
single-SKU long-tail columns. Build it slice-first (hero SKUs), widen after planner UAT, industrialize the v2
capabilities last.**

Rejected: Option A (raw-only — dies at the aggregate screens) and Option B (big model upfront — overengineered,
premature, mis-targeted for reads).

### Why (one paragraph)
"Faster UI" is an *analytical-serving* problem, not a *transactional-model* one — Lakebase already owns writes.
Raw `prod_edw` is fine for a single-SKU drill but can't serve the ranked/forward/pattern screens over 13.4B+
rows without cost and drift. A full new datamodel first would overengineer against still-moving requirements and
would be the wrong *shape* (OLTP) for read-heavy screens. A thin, denormalized serving layer — the pattern the
project already proved with `p1slice_*`/`sdp_*` — gives fast reads, once-computed semantics, a guardrail-clean
home for derived history, and (built slice-first) fast planner value without premature investment.

### Next actions
1. **Confirm intent:** planner-facing product (→ Option C) vs one-session demo (→ live-drill exception)?
2. Define `rc_serving_sku_week` DDL + the derivation SQL for buckets / likely-cause / SS-at-lead-time (semantic
   layer, define-once).
3. Populate it for the ~12 hero SKUs; build the v1 hero path against it; wire Lakebase session timers.
4. After UAT: scale the Job to all SKUs; add the v2 serving tables + alerts Job.

---

<div align="center">

### 📌 ADR in one line
**Serve the UI from a thin, denormalized Gold read-model in `sandbox_operations.po_management` (not raw
`prod_edw`, not a big upfront datamodel), keep all state in Lakebase, refresh weekly on the plan snapshot, and
build it slice-first so semantics are validated before the pipeline is industrialized.**

*All source reads READ-ONLY on `prod_edw`/`prod_operations`; all serving tables in
`sandbox_operations.po_management`; all transactional state in Lakebase. No production schema is written.*

</div>
