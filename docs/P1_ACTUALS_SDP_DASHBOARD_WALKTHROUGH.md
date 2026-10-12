# P1 "Actuals Supply Plan" — SDP Dashboard: Team Walkthrough

**Audience:** Milwaukee Tool supply-planning team (planners + planning managers).
**What this is:** what the dashboard does, page-by-page and widget-by-widget, what data is behind it,
which business scenarios it covers, and pointers we learned digging through the data.

> **Dashboard to open:** "P1 Actuals — SDP (Rung 2)" — dashboard id `01f1a5371959178aa137d5551347afff`
> (Databricks → Dashboards → published). This is the **fast** version (runs on the SDP pipeline).
> There is a second, identical-looking dashboard "P1 Actuals — Olive Branch" kept only as a fallback;
> **share the SDP one.**

---

## 1. What the dashboard is for (the one-sentence version)

Every Monday, it shows **what we planned last week vs. what actually happened** for every SKU × org ×
week, tells you **which items went off-plan, by how much in $, and what to do about each** — replacing
the manual Excel reconciliation planners do today.

It answers the 6 questions from the requirements (UC1–UC6): POs expected vs received, why on-hand moved,
demand-driven vs supply-driven variance, plan-accuracy trend, what changed in the plan, and a per-SKU
history drill.

---

## 2. What data is loaded

**Grain:** one row per **item × organization × week** (Monday-start weeks).
**Window:** **180 days** — weekly snapshots **2026-03-09 → 2026-08-24** (25 weeks). *(Plan snapshots
start 2026-03-02; the comparison gold starts one week later because each week is compared to the
**prior** week's plan.)*
**Scope:** **2 organizations — 2012 (Olive Branch DC) and 2120 (Mexico DC)**, **~33,676 items**,
**924,987 item-week rows**.

**Where it comes from (all READ-ONLY production sources):**

| What | Source table | Role |
|---|---|---|
| The plan (what we projected) | `prod_edw.fact.20_supply_daily` | weekly plan snapshot: projected on-hand (PAB), safety stock, planned sales orders |
| On-hand actual | `prod_edw.fact.inventory_days_on_hand` | actual ending inventory (point-in-time each week) |
| PO receipts actual | `prod_edw.fact.purchase_receipt_line` | quantity actually received |
| Sales shipped actual | `prod_edw.fact.sales_order_line_transactions` | quantity actually shipped |
| PO timing (real) | `prod_operations.features.general_historical_purchase_order_lead_time_errors` | promised-vs-actual delivery (slip days, chronic-late %) |
| Transfer receipts | `prod_operations.manufacturing_sc.fact_transfer_order_receipt` | inter-org transfer timing into 2012 |
| Plant movements | `prod_edw.fact.inventory_material_transaction` | upstream plant activity (root-cause context) |
| Item / org / cost / planner | `items_scd1`, `inventory_organization_scd1`, `dim_series_ext_vw` | ABC class, planner name, standard cost |

**Org → plan rule (important):** org 2120 is compared against the **'20 Mexico Supply Plan'**; every other
org against the **'20 Global Supply Plan'**. This prevents 2120 being double-counted.

**How it's built (why it's fast):** a Lakeflow **SDP pipeline** (`p1_actuals_sdp`) pre-computes all the
heavy joins/aggregations **once per weekly run** into ~35 tables. The dashboard then just *filters* small
pre-aggregated tables (tens–hundreds of rows) instead of crunching 924,987 rows live on every click — so
it stays fast as we add more orgs. Refresh runs **weekly, Mondays ~08:00 CT** (job `p1_actuals_weekly_sdp`,
currently paused until go-live).

---

## 3. The variance math (how "off-plan" is defined)

For each item × org × week:
- **Absolute variance** = actual on-hand − planned on-hand (PAB)
- **% variance** = (actual − planned) / |planned| × 100
- **$ variance** = variance × item standard cost
- **Status band:** green ≤15% | yellow 15–30% | red >30%
- **Alert tier** (from the requirements): Tier-1 Monitor >15% · Tier-2 Alert >30% or >$50K · Tier-3
  Escalate >50% or >$200K or below safety stock.

---

## 4. Global filters (top of every page)

These apply across the whole dashboard (a filter only affects a widget that carries that field):
- **Org** — 2012 / 2120 (multi-select; blank = both).
- **Week range** — defaults to the full 180-day window; narrow to focus a period.
- **Plan-fit status** — green / yellow / red.
- **ABC class** — A / B / C / D (value tiers; A = vital few).
- **Weeks-ago slider** — quick "last N weeks" replay.
- **How-to-use panel** — a text tile explaining the filters.

---

## 5. Page-by-page, widget-by-widget

### Page 0 · Monday Cockpit — *"what do I do this morning?"*
The action surface. Opens with **change + verb + $**, not static levels.
- **⚠ Items newly off-plan this week** — items that flipped to red since last Monday (the new fires).
- **$ of NEW exposure this week** — dollar value of those new reds.
- **Items that recovered** — were red, now aren't (progress).
- **Tier-3 escalations open now** — the must-escalate count.
- **Your action list (table)** — newly-red items ranked by $ at risk, each with a **recommended action**
  (EXPEDITE / DEFER-CANCEL / FIX-SUPPLIER / REVIEW) and a **systemic-vs-one-off** flag. *This is the
  planner's Monday to-do list.*
- **Where the new $ is — by required action** / **by org** — where to spend the morning.
- **Stockout-risk $ swing vs last Monday / right now / % chronic-supplier / $ in overstock** — four KPIs
  sizing the money at stake and how much is a recurring supplier problem.
- **Is this week normal? (line)** — new-exposure $ by week (~$25M baseline; watch spikes).
- **Who owns the new fires? (by planner)** · **Is the work-mix worsening? (action-mix by week)** ·
  **Fresh vs festering** — red items by weeks-stuck-red (6+ weeks = chronic neglect).

### Page 1 · Monday Overview — *the portfolio state*
- **KPIs:** items tracked · item-weeks off-plan · avg on-hand bias · max $ variance.
- **Plan-fit band mix by week** · **$ variance by ABC** (where the money concentrates).
- **Net $ variance by week** (is the portfolio over- or under-planned overall).
- **Top 25 misses by $** (table).
- **Plan-fit band by org** · **$ variance by org** (2012 vs 2120 side by side).
- **Stockout-risk $** (below safety stock) · **Excess capital $** (>3× safety stock) — the two money-at-risk
  poles.
- **Newly off-plan / $ new exposure / recovered** — the cockpit delta strip repeated here for context.

### Page 2 · Plan Accuracy & Bias — *"how good is our planning?"*
- **Accuracy vs SLA (table):** MAPE target <15% — both orgs currently miss it.
- **Direction of drift (area):** over/under/on-plan share by week (honest — not just the average).
- **A-items planned tighter than C/D? (median var % by ABC)** — should be yes; shows if discipline scales
  with value.
- **Forecast Value Add % (bar + table):** compares plan error to a naive "same-as-last-week" forecast.
  **Both orgs are NEGATIVE** — the current plan is *worse* than doing nothing. This is the headline finding.
- **Persistently biased items (correctable):** items over- or under-planned almost every week — the
  fixable list.
- **Short vs long lead-time slip:** counterintuitively, **short-lead items slip most** (2012 +22 days);
  long-lead run early.
- **Weekly MAPE by org (line):** the accuracy trend vs the 15% target.

### Page 3 · Exception Queue — *the cost-ranked worklist*
- **Items on the queue** · **Total $ at risk (top 500)**.
- **$ at risk by exception type (pareto):** Unplanned / Stockout risk / Excess / Over-plan / Under-plan —
  where to spend the morning.
- **Action list (table):** one row per item, sorted by $ at risk, with chronic-supplier flag.
- **Root cause of DC plan misses:** $ at risk by category & org (demand change / supply timing / stockout /
  excess / plan drift).

### Page 4 · SKU Drill-down — *investigate one item*
Pick a SKU (blank = all). Then:
- **Total actual on-hand** · **Largest single weekly $ gap** (KPIs).
- **Plan vs actual on-hand (+ safety-stock floor) (line).**
- **On-hand $ gap by week (bar).**
- **What moved on-hand: demand (planned SO / shipped) vs supply (received) (line).**
- **Weeks of cover (line):** heading to stockout (low) or overstock (high)?
- **Cumulative drift (area):** is the gap compounding week over week?
- **Week-by-week evidence (table).**

### Page 5 · Cross-Org Contrast — *why one dashboard scales to N orgs*
- **Org behavior scorecard (table):** the backbone — one row per org; **designed to add rows as more orgs
  onboard, not more dashboards.**
- **Plan overage:** both over-plan; **2012 is ~5× harder** (+101% vs +21% avg overage).
- **Why a fixed $ alert can't fit both:** 2012 p99 $141K vs 2120 p99 $9.6K — thresholds must be org-aware.
- **Lean vs healthy (scatter):** 2120 holds ~19× less buffer per item yet is greener (66% vs 40% on-plan).
- **Key-person risk:** 2120's top planner owns 53% of items (6 planners); 2012 spreads across 92.
- **Portfolio distinctness:** ~5,717 shared items; 2012 has 22,429 exclusive, 2120 has 4,041.
- **Scale context (raw $):** 2012 $4.4B vs 2120 $181M — why the comparisons above are in *relative* terms.

### Page 6 · Scenarios — *named situations to watch*
- **Long at Olive, short at Mexico:** same item overstocked at 2012, understocked at 2120 — a rebalancing
  candidate.
- **Off-plan vs on-plan baseline** · **Extreme variance — top misses by $.**

### Page 7 · Plan Changes & Timing — *plan stability + supply timing*
- **Biggest plan revisions (table):** first snapshot → latest — the "what changed" list.
- **Month-over-month accuracy** (req 2.3.2).
- **Receipt timing (M4):** % late vs promised, by lane & org.
- **Plant material movements by type & plant:** upstream supply tier (context — a different tier than the
  DC numbers, not additive with them).
- **Plan nervousness:** net revision per week (negative = plan walked down).
- **Plan convergence:** do revisions shrink as the target week nears? (healthy = funnel to zero.)

---

## 6. Scenarios the dashboard covers (checklist for the team)

- **On-hand plan-vs-actual** (the core) — every page.
- **PO receipts vs plan** (qty + timing / % late) — pages 3, 7.
- **Sales shipped vs plan** — variance + drill flows.
- **Stockout risk** (below safety stock, in $) — cockpit, overview, exceptions.
- **Excess / overstock** (>3× safety stock, in $) — cockpit, overview.
- **Root-cause attribution** (demand vs supply vs plan drift) — page 3.
- **Chronic-late suppliers** (systemic vs one-off) — cockpit action list, exceptions.
- **Plan accuracy / FVA / bias** (is planning adding value?) — page 2.
- **Plan nervousness & convergence** (is the plan stable?) — page 7.
- **Cross-org contrast** (2012 vs 2120 behavioral difference) — page 5.
- **Inter-org imbalance** (long here / short there) — page 6.
- **Weeks-of-cover / drift trajectory** per SKU — page 4.

---

## 7. Additional pointers we learned from the data (read before drawing conclusions)

These are **data-verified gotchas** — worth telling the team so nobody misreads a widget:

1. **The two orgs are structurally different, not just bigger/smaller.** 2012 is a large, hard-to-plan DC
   (+101% avg overage, 92 planners, $4.4B); 2120 is lean and greener (+21%, 6 planners, $181M). **Don't use
   one $ threshold for both** — the dashboard shows why (2012 p99 is ~15× 2120's). Thresholds/alerts should
   be org-aware (and ideally ABC-aware).

2. **Planning is currently worse than a naive forecast (negative FVA, both orgs).** This is the single most
   important finding: a "same as last week" guess beats the plan on on-hand. It's the strongest argument for
   this tool and for re-tuning the planning parameters.

3. **Short-lead items slip the most, not long-lead.** Counterintuitive but consistent — likely because
   long-lead items get more attention/buffer. Watch the short-lead queue.

4. **PO "expected receipt date" in the raw receipts table is a same-day mirage** (it equals the receipt date
   100% of the time). Real timing comes from the historical lead-time-error feature table — that's what
   powers the % late / chronic-supplier signals. Don't compute timing off the raw receipts.

5. **On-hand is point-in-time — never sum it across weeks.** It's a stock level, not a flow. Received and
   shipped ARE additive; on-hand is the latest reading in the week.

6. **The plant-movements tile (page 7) is a different tier.** The material-ledger only covers **plant** orgs
   (1006–1021), not the DCs (2012/2120). It's upstream *context*, not summable with DC variance.

7. **2120 is a leaf, 2012 is the network hub.** 2120 has zero inbound transfers; 2012 receives from 19
   source orgs. Timing/flow analysis differs by role.

8. **"Newly-red" is edge-sensitive to the window.** It compares the latest week to the prior week; widening
   the window can shift a couple of items at the boundary. The **latest-week action count is the stable
   operational number** (~2,240 items / ~$24M new exposure).

9. **Weekly cadence is intentional.** The plan only changes weekly (Monday snapshot), so the dashboard
   refreshes weekly. Real-time interactivity is the job of the App (next phase), not this dashboard.

---

## 8. How to give the walkthrough (suggested 15-min flow)

1. **Start on the Monday Cockpit** — "this is your Monday to-do list." Show the action table + the four
   change KPIs. (2 min)
2. **Overview** — "here's the whole portfolio state and where the money is." (2 min)
3. **Accuracy & Bias** — land the FVA finding: "our plan is currently worse than naive — here's the proof."
   (3 min)
4. **Exception Queue** — "cost-ranked worklist + root cause." (2 min)
5. **SKU Drill** — pick one real SKU and walk its story. (3 min)
6. **Cross-Org Contrast** — "why 2012 and 2120 need different thresholds, and how this scales to more orgs
   without new dashboards." (2 min)
7. **Pointers (section 7)** — call out #1, #2, #4 so nobody misreads the numbers. (1 min)

---

## 9. What's next (roadmap)

- **Done:** dashboard + stable weekly SDP pipeline (180-day history, verified).
- **Next — the App (phase 3):** turn the read-only action list into **clickable actions** — approve /
  reject / expedite / defer, add comments, assign, with a full audit trail (Lakebase). Writeback to Oracle
  is **simulated** in the sandbox for now (governed real integration is a separate approved lane).
- **Later:** widen beyond 2012+2120 to the full network (the pipeline is built to do this by changing one
  config value), and ABC-tiered thresholds.

---

## 10. Reference (for the data/BI folks on the team)

- Pipeline: `p1_actuals_sdp` — 35 materialized views in `sandbox_operations.po_management` (`sdp_*`).
- Core gold table: `sandbox_operations.po_management.sdp_plan_vs_actual` (924,987 rows).
- Weekly job: `p1_actuals_weekly_sdp` (Mondays 07:57 CT, paused).
- Evidence & test queries: `data_understanding/workspace_assets/SDP_VERIFICATION_LOG.md`.
- Requirement mapping / gaps: `data_understanding/workspace_assets/P1_STATUS.md`.
- Genie question bank (natural-language Qs the data can answer): `data_understanding/GENIE_QUESTION_BANK.md`.
