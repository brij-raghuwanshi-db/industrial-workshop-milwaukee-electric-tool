# Rung 2 — Actuals Supply Plan, ALL items @ org 2012 Olive Branch

**Built 2026-08-31 · READ-ONLY on prod; writes only to `sandbox_operations.po_management.rung2_*` (NEW assets;
Rung 1 `p1slice_*` untouched).** Same SQL as Rung 1 with the **item filter dropped** — the only change. Proves
the set-based design generalizes without a rewrite.

## Scope probed first
Org 2012, 8 weeks (2026-07-06 → 08-24), plan '20 Global Supply Plan': plan 27,324 items / 1.85M rows/snapshot;
on-hand 126,401 items; receipts 3,441 items; shipments 11,299 items. Modest — no scale concern.

## Assets (NEW — nothing deleted)
- `sandbox_operations.po_management.rung2_planned_weekly` — 28,146 items / 4.87M rows.
- `sandbox_operations.po_management.rung2_actuals_weekly` — 126,404 items / 1.0M rows.
- `sandbox_operations.po_management.rung2_plan_vs_actual` — **219,938 rows = 219,938 distinct item×week (grain
  clean, no dupes)**, 28,146 items.

## Verification (done ≥ reconciled)
1. **Generalization proof — PASS (exact).** Hero item 48111850 in Rung 2 == Rung 1 row-for-row:
   wk 07-06 → 78,399 / −$429,729.77 / yellow; 07-13 → 94,512 / $539,137.10 / yellow; 07-20 → 95,570 /
   $1,096,499.78 / red. Dropping the item filter changed scope, not logic.
2. **Grain — PASS.** rows == distinct(item×week).
3. **Portfolio scorecard (the Rung-2 payoff):** status mix — red 15,104 items / green 14,506 / yellow 5,832 /
   no-data 5,102. Top A-item $ variances: M18 FUEL 2PC Combo Kit +$5.95M (wk 08-03, above plan); M18 Forge
   HD12.0 Battery −$3.94M (wk 08-24, below plan — a real supply-short signal).

## Pipeline decision (thinking, not yet built)
Deliberately still notebook SQL. Rationale: SDP earns its place once logic is stable + scheduled. Rung 1
reconciled; Rung 2 now proves all-items generalization. **Next: convert this exact SQL into an SDP pipeline
(CREATE STREAMING TABLE / materialized views) + weekly Lakeflow Job for Rung 3** (full year, bounded backfill
+ weekly MERGE). The CREATE OR REPLACE tables map to SDP definitions near-verbatim — no rewrite. Building the
pipeline before Rung 2 would productionize unproven-at-scale logic; after is on time.

## Rung 2 dashboard — 4 pages, question-driven (NEW; Rung 1 dashboard untouched, still ACTIVE)
- **ID `01f1a50aed891d5c85b5e64b2c3c5d5b`** · "P1 Actuals — Olive Branch (Rung 2, all items)" · published + tagged.
  Path: `/Workspace/Users/brijendra.raghuwanshi@databricks.com/mke_supply_chain/dashboards/`. Source: `rung2_dashboard.json`.
- Global filters page (status / week / ABC) + 4 canvas pages mapped to P1 use-cases:
  1. **Monday Overview** (UC1–3): KPIs (items, item-weeks off-plan, avg bias %, max $ var); status-mix bar by week; $ variance by ABC.
  2. **Plan Accuracy & Bias** (UC4): avg-bias-% drift line; red-vs-green count trend; bias by ABC. Story: systematic OVER-planning (+87%→+135%) and worsening red count (8,082→13,034 items).
  3. **Exception Queue** (UC1/6 + S5 lesson): full table, **cost-ranked** (Var $) not unit-ranked; filterable.
  4. **SKU Drill-down** (UC6): plan-vs-actual on-hand + flows for a filtered SKU (cross-filter from exceptions).
- 3 datasets: `ds_pva` (wide gold, cross-filter, 219,938 rows), `ds_week` (weekly rollup, 8), `ds_abc` (ABC bias, 4).
  **All 3 CLI-tested (SUCCEEDED) before deploy.** The `ds_week`/`ds_abc` aggregates double as **gold/metric-view
  definitions the Rung-3 pipeline will reuse** — building them now is pipeline-forward, not throwaway.
- Followed lakeview-dashboard-fastpath skill: main_query names, business logic (ABS/CASE) in dataset SELECT,
  %/$ formats on counter AND table, global-filters page, clean queryLines (built programmatically to avoid comma bugs).

## Dashboard v2 — more P1 requirements answered + integrity-proven (2026-08-31)
Added per business-owner request (all from data we have; tested before deploy):
- **O8 alert tiers** (Monitor >15% / Alert >30% or >$50K / Escalate >50% or >$200K) — `alert_tier` col in gold + KPI + page-5 tier bar (colored by severity meaning). Distribution: OK 79,498 / Monitor 13,024 / Alert 10,829 / Escalate 46,436.
- **Bias by planner (2.4.3)** — `planner_name` joined into gold (LEFT JOIN dim_series_ext_vw, verified 1:1 at org 2012 → NO fanout); page-5 top-15-planners-by-$ bar; null planner → 'Unassigned'.
- **Shipped-vs-plan (2.3.4)** + **WoW delta (2.3.1)** — `wow_onhand_delta` (LAG) col in gold; page-5 WoW-movers table; overview coverage bar.
- **Root-cause 2.3.7 DEFERRED** (owner decision) — do it properly from `inventory_material_transaction` 27-type ledger, not a gold-row proxy (proxy left ~40% 'Other/Mixed' — low quality). Belongs with the P2 exception engine.
- **Fixed mislabel:** the 39,964 'no-data' rows are NOT 'No actual' — they are `planned_pab IS NULL` = **actual activity with no plan baseline that week (Unplanned)**. Relabeled band to '0 · Unplanned (no plan)'.
- **Fixed color/label integrity:** multi-series lines now pin colors to MEANING (off-plan→red, on-plan→green, etc.) via color.scale.mappings on displayName — no more 'Red items' drawn blue. Legend now teaches the business band, not the color name.
- **SKU drill-down** got a page-level single-select SKU filter.

### Integrity proof (no granularity/double-count/join issues) — all PASS
- Gold grain: 219,938 rows == 219,938 distinct item×week (planner join added a column, not rows).
- dim_series_ext_vw @ org 2012: 143,942 == distinct(item_number,org_code) → join is 1:1, safe.
- ds_week per-week counts SUM to 219,938 (= gold) → no agg leak.
- alert_tier: 4 tiers PARTITION exactly to 219,938 (no overlap/miss).
- ds_planner: 88 rows == 88 distinct planners (LIMIT 15 is display-only).

## Multi-org: added 2120 Mexico via org→plan mapping (2026-08-31)
The requirement's D-logic: 2120→'20 Mexico Supply Plan', all else→'20 Global Supply Plan'. Verified only 2120
is on the Mexico plan, and 2120 appears under BOTH plans in the raw fact → **double-count risk**. Killed it
with a single predicate: `(org=2120 AND plan='Mexico') OR (org<>2120 AND plan='Global')`.
- rung2_* now hold **2 orgs**: 2012→Global (219,938 rows, **identical to prior single-org build** = 2012 undisturbed)
  + 2120→Mexico (77,273 rows). Gold total **297,211 rows = 297,211 distinct item×ORG×week** (org now in grain + join).
- **Integrity (all PASS):** no join fanout; alert-tier 4 buckets partition to 297,211 (no double-count across orgs);
  dim_series 1:1; each org on exactly one plan.
- **Business insight surfaced:** 2120 Mexico is healthier (48,126 green vs 19,750 red) than 2012 (79,885 vs 86,350).
- **Dashboard now org-aware:** added **Org/DC global multi-select filter**; overview gained an **org-comparison row**
  (plan-fit band by org + $ variance by org — blending made explicit, not hidden); exception table gained an **Org column**.
- **Scale answer:** adding a *Global-plan* org later = widen the org IN-list (trivial). 2120 needed the plan-switch
  (done). Full 126-org network is the Rung-3 pipeline's job (bounded/incremental), not a CREATE OR REPLACE.

## Org 2120 behavior validation — orgs are NOT interchangeable (2026-08-31)
Two logged subagents + my own re-verification of every load-bearing number (grain re-checked clean at both
orgs). Full write-up: `data_understanding/data_stories/org2120_validation/` (INDEX + A validation, B new
scenarios, C synthesis). Key results:
- **All 7 identified P1 scenarios APPLY to 2120, but behave differently** — most importantly bias is
  ~5× smaller in MAGNITUDE (both over-plan by row-sign — 2012 +101% mean overage vs 2120 +21%; NOT
  "inverted", a sign test corrected the subagents) and 2120's extreme $ miss is p99 $9.6K vs
  2012's $141.5K → **fixed $-thresholds mis-fire; thresholds must be org-specific.**
- **3 genuinely NEW 2120-only findings** (verified): planner concentration (6 planners vs 92; 2 own 85%);
  41% Mexico-exclusive SKUs (4,041/9,758); net-receiving node (ship/receive 0.094 vs 0.377). Plus lean-yet-
  green (SS 120 vs 2,343 units, 62% vs 36% green) and 9× better plan coverage (2% vs 18% unplanned).
- **Data-model changes derived (min-sufficient, into the same gold/Rung-3 build):** (1) org-aware
  `threshold_config` table + **percentile-based bands** (auto-calibrate per org, absolute-$ floor);
  (2) **directional** per-org bias correction; (3) cross-org tiles **INNER JOIN on shared SKUs** (the S6
  imbalance tile is valid only for the 5,717 shared items); (4) first-class planner attribute + load view;
  (5) `org_role` (hub vs producer) so a hub's low ship-rate isn't flagged as a miss.
- **Correction logged:** subagents said avg SS ≈112.88; verified `>0` value is 120.0 — finding unchanged.
- **Deferred (needs data beyond gold):** confirming 2012→2120 intercompany transfer (material-transaction
  ledger); COO/FX-import exposure (add COO from items_scd1). Flagged, not fabricated.

## Dashboard page "5 · Cross-Org Contrast" — one dashboard, N orgs (2026-08-31)
Added a 6th canvas page (dashboard ID unchanged `01f1a50aed891d5c85b5e64b2c3c5d5b`; update+publish, not
re-create). **Design principle so it never needs per-org rebuilds:** every widget **GROUPS BY org** (never
filters to one) → a new org auto-renders when it lands in gold; and contrast is shown in **relative** terms
(%, ratios, per-item, percentiles) so a small org is comparable to a 24× larger one. 5 new datasets, all
long-format/group-by-org, each concatenated-query CLI-tested before deploy; new-page widgets self-audited
(main_query names, encoding refs bound, no func-in-expr) — AUDIT CLEAN.
- **Scorecard table** (`ds_scorecard`) = the **N-org backbone** (charts cap ~8 series; a table scales
  infinitely): 1 row/org — items, item-weeks, avg overage %, %green/red/unplanned/escalate, avg |var| $/row,
  safety-stock/item, ship/receive, planners.
- **Overage bar** — both orgs OVER-plan; 2012 ~5× harder (+101% vs +21%). (Corrected the subagents'
  "inverted bias" claim via a row-sign test: 2012 41% over/26% under, 2120 38% over/19% under — same
  direction, different magnitude. Fixed in A/C synthesis, memory, and this log.)
- **Variance-$ percentile grouped bar** (`ds_varpct_long`) — 2012 p99 $141K vs 2120 $9.6K → *why one fixed
  $ alert can't fit both* (the org-aware-threshold case, made visual).
- **Lean-yet-green scatter** — SS/item vs %green (2120: 120 units→62%; 2012: 2,343→36%).
- **Planner-concentration bar** (`ds_planner_conc`) — top planner share 53% @2120 (6 planners) vs 12% @2012
  (92) = key-person risk.
- **SKU shared/exclusive stacked bar** (`ds_sku_share_long`) — 5,717 shared core; 2120 4,041 excl / 2012
  22,429 excl.
- **Scale-context bar** (`ds_scale_ctx`) — the ONE raw-$ tile ($4.4B vs $181M) that explains *why* the rest
  is relative. Render to be confirmed in browser (CLI proves structure+data only).

## Decision-first redesign of pages 2/3/4 + overview money tile (2026-08-31)
User review flagged three pages as "how will anyone understand this?" — two were real bugs, one weak design.
Fixed + reframed from *showing data* to *supporting decisions* (dashboard ID unchanged; update+publish).
- **Page 3 Exception Queue — was BROKEN, now FIXED.** Table had bound to `ds_pva` (full 297,211-row wide
  table) → showed on-plan items ($0 variance, ABC null) at the top, item repeated 7× (once/week), 4000 pages.
  Rebuilt on new **`ds_exc_queue`**: red/yellow only, **1 row per item×org (worst $ week via QUALIFY)**,
  21,611 rows == distinct item×org, cost-ranked, ABC populated, `exception_type` (Stockout risk/Excess/
  Over-plan/Under-plan/Unplanned), + **`root_flag`** (Systemic chronic-supplier vs One-off, from p1flow
  chronic_pct_late). Now a "Monday Action List" with KPIs + $-at-risk-by-type bar.
- **Page 4 Drill-down — was dead-on-arrival, now defaults.** SKU single-select defaulted to "All" → ~28k
  SKUs overlaid, actual line crushed flat, truncation. Seeded `defaultSelections` to the worst-exception SKU
  (377120) so it lands on a readable single-item plan-vs-actual gap + flows.
- **Page 2 Accuracy — was misleading, now honest.** Replaced the outlier-inflated MEAN ("140% bias") with:
  (1) **SLA scorecard** (`ds_sla`) vs O6 targets — on-hand MAPE **2012 124% / 2120 37% vs <15% target**,
  % within ±15%, items below SS; (2) **over/under/on-plan stacked area** (`ds_accuracy_split`) = honest
  direction; (3) **ABC MEDIAN var% by org** (`ds_abc_median`) not mean.
- **Overview — added the exec headline:** **Money at risk** = stockout-risk $ vs excess-capital $
  (`ds_money_risk`): **2012 $662M short-risk / $843M excess capital; 2120 $7.8M / $40.4M.** Reframes the
  whole dashboard from variance% to dollars mispositioned.
- 6 new datasets, each concatenated query CLI-tested; new/changed widgets self-audited vs fastpath (the 4
  audit flags were pre-existing untouched overview bars). Render to be confirmed in browser.

## Page 7 · Plan Changes & Timing — the in-scope-but-unshown requirement gaps (2026-08-31)
Closed the dashboard-visible gaps vs the Actuals doc, each feasibility-probed first (built only what the data
truly supports; labeled the thin/proxy ones honestly):
- **UC5 / 2.4.1 (must-have) — plan evolution across snapshots.** `rung2_planned_weekly` carries snapshot_date
  /snapshot_week/target_week_start with **8 snapshots**; later target weeks are covered by all 8. New
  `ds_plan_evolution` (org × target_week × snapshot → SUM planned_pab) drives a multi-line "how the plan for
  each future week changed as it was re-forecast." Real signal: target wk 2026-09-07 plan 43.9M (Jul-06 snap)
  → 34.5M (Aug-24 snap) = −21% revision you can watch. + `ds_plan_change_items` table = biggest first→latest
  plan revisions (e.g. Inkzall marker late-Dec plan cut +1,072,948 → −71,807 = −1.14M).
- **2.3.2 (should-have) — month-over-month.** `ds_mom` median var% by org×month. HONEST LIMIT: only Jul & Aug
  exist in the 8-week window, so it shows one comparison; titled to say so. Widens automatically at Rung 3.
- **M4 — receipt timing.** `ds_po_timing` surfaces the p1flow slip as % late by lane×org (2012 transfer 78%,
  2120 PO 81%). First time M4 is a dashboard tile.
- **2.3.7 root-cause 5-category — still DEFERRED** (needs inventory_material_transaction ledger); page 3 keeps
  the symptom-type proxy, not the doc's 5 categories. Not faked.
- 4 new datasets CLI-tested; page self-audited AUDIT CLEAN; deployed+published same ID. Render = browser gate.
- Dashboard now 8 pages (Global filters + 7 canvas).

## Page 4 drill-down — real fix + explainability rebuild (2026-08-31)
- **BUG I had missed (and wrongly claimed fixed):** the default-SKU key was `defaultSelections` (plural);
  Lakeview's key is **`defaultSelection`** (singular) → silently ignored → filter defaulted to "All" → all
  ~28k SKUs overlaid (the spike-forest the user screenshotted). Root cause = I never confirmed the render,
  the exact gap the fastpath skill warns about. Fixed to the singular key; verified in DEPLOYED JSON
  (defaultSelection -> 377120).
- **Explainability rebuild (user: "show this in a better way, more explainable, supporting info"):** page 4
  went 4 → 8 widgets: how-to-read caption (what the gap MEANS); 2 KPI counters reacting to the SKU (peak
  on-hand, worst-week $ gap); plan-vs-actual line + safety-stock floor; **"the gap that matters" = on-hand $
  gap by week colored by plan-fit band** (draws the gap literally); flows line; **week-by-week evidence
  table**. Self-audited AUDIT CLEAN; default-selection key confirmed singular in deployed JSON.
- Lesson reinforced: CLI proves structure+data but NOT selection behavior/visual — must confirm render.

## Global-filter binding audit + fix — dashboard-wide (2026-08-31)
User asked to verify global filters are attached to the right widgets everywhere. Audit (reading **actual
dataset output columns**, not text) found a real silent bug: the **Org filter (`f_org` binds field
`organization_code`) was DEAD on most pages** because aggregated datasets aliased `organization_code AS org`
→ output column was `org`, so the filter query `SELECT organization_code FROM (ds)` matched nothing (Lakeview
global filters bind only to a dataset that outputs the exact filter field name; mismatch = silent no-op).
- **Fix:** surfaced a raw `organization_code` output column in every filterable aggregated dataset (kept `org`
  as the display alias so no widget reference broke). 3 CTE-based datasets (accuracy_split, exc_queue,
  plan_change_items) needed the column added at the OUTER select, not just the CTE — caught by re-auditing
  real output columns (a bindability spot-test gave a false pass; the output-column audit is the truth).
- **Result (verified in output columns): Org filter now binds on pages 1,2,3,4,6,7.** Page 5 Cross-Org left
  **intentionally global** (it exists to compare all orgs; filtering it away defeats its purpose). Week/ABC
  bind wherever the dataset grain carries them; datasets that legitimately don't carry a field (e.g.
  ds_exc_pareto = cross-org totals) stay global by grain, not by bug.
- Widget-contract audit across ALL pages AUDIT CLEAN; all datasets parse; deployed+published same ID.
- **Method note for future:** to check a global filter's reach, enumerate each canvas dataset's REAL output
  columns vs the filter field names — substring-on-SQL lies (matches aliased sources).

## 4-month reload + prior-week baseline + root cause + week slider (2026-08-31)
**4-month widen (2.3.2):** rebuilt `rung2_planned/actuals/plan_vs_actual` over ~18 Monday snapshots
(2026-05-04→08-24). Gold now **4 months / 16 weeks / 590,275 rows == distinct item×org×week** (integrity all
PASS — see below). Stored the exact build as a **runnable workspace notebook**
`/Workspace/…/mke_supply_chain/rung2_actuals_build` (+ local `workspace_assets/rung2_actuals_build.sql`) —
closes the reproducibility gap (rung2 previously existed only as tables + this log). All dashboard datasets
pick up 4 months automatically (same table names); MoM now shows 4 points.
**Prior-week baseline fix (doc §5.1) — surfaced by the widen:** the widen exposed that the old
"earliest-snapshot" plan pick gave an INCONSISTENT lookback (early weeks looked back 9+ wks, recent ~1). Changed
`plan_pick` to the **nearest snapshot STRICTLY BEFORE the target week** → uniform **7-day lookback** every week
(verified). Correctly drops the first week (2026-05-04: no prior snapshot). Grain stayed clean (baseline pick
changes WHICH plan row, not the count).
**Integrity re-verified at 4-mo (user challenge "joins not inflating? granularity?") — all PASS:**
`dim_series_ext_vw` 1:1 per item×org (0 dupes → cost/planner joins don't inflate SUMmed planned_pab or dup
rows); gold rows==distinct grain; planned_weekly no fanout beyond snapshot count; 0 item-weeks on >1 plan
(2120 double-count guard holds); each org on exactly one plan; actuals_weekly rows==distinct grain (on-hand
point-in-time not fanned).
**Root cause 2.3.7 — evidence-based finding + two labeled lenses:** the `inventory_material_transaction`
ledger (org via `location_scd1.organization_code`) **only carries PLANT orgs 1006-1021, NOT DC 2012/2120** —
so the doc's ledger-sourced 5-category can't be computed for our DC orgs (proven by direct count). Built BOTH:
`rootcause_dc` (per-signal dominant-driver attribution for 2012/2120: Unplanned/Stockout/Demand-change/
Supply-timing/Excess/Plan-drift — residual cut from a naive 80% to **41%**; $ at risk: Stockout $724M,
Plan-drift $571M, Excess $522M @2012) and `rootcause_plant` (true ledger 5-category for the plants that SUPPLY
the DCs — Production/Transfer/Receipts/Adjustment/Demand). Surfaced as page-3 DC tile + page-7 **labeled**
"upstream plant movements" tile (explicitly a different tier, NOT summable with DC numbers).
**Week slider:** added a **global range-slider on `week_start`** (`f_week_slider`) alongside the date picker;
binds to the 8 time-grained datasets (ds_pva/week/topexc/imbalance/exc_queue/accuracy_split/plan_evolution/
plan_change_items). Self-audit clean (pre-existing overview/scenarios bar-agg flags untouched); deployed+published.
**Consistency note (follow-up):** `p1flow_*` tables were built on the OLD 8-week window — now narrower than the
4-month gold; re-widen them when the flow tiles need the full window.

## Money-at-risk counters not reacting to Org filter — FIXED (2026-08-31)
User caught the two overview "Money at risk" counters not changing with the Org filter. Root cause: they read
`ds_money_risk` which is **pre-aggregated (GROUP BY org)** — a field-based global filter CANNOT auto-inject a
WHERE into a GROUP BY dataset (skill 3-filters L245), so the filter had nothing to bind. NOT by design.
- **Fix:** repointed both counters to the raw plain-SELECT `ds_pva` (which the engine CAN auto-filter), after
  adding two derived cols to ds_pva — `stockout_gap_dollar`, `excess_capital_dollar` — so the counter does a
  plain `SUM(bare_col)` (no CASE in widget expr). Now Org filter AND week slider both reach them.
- Values rose ($669m→$1.22bn stockout, $883m→$2.04bn excess @2012) because gold is now 4 months, not 8 weeks —
  expected, more weeks of accumulated risk. Verified split by org. `ds_money_risk` retained (unused by these
  counters now; harmless).
- **General rule reinforced:** counters/tiles that must react to a global filter should read a raw
  (non-GROUP BY) dataset with the filter field present; pre-aggregated datasets need the parameter pattern.

## Page 2 deepened + weeks-ago slider + full time-filtering (2026-08-31)
User: 'not satisfied with the number of widgets / limited story.' Added 4 VERIFIED high-impact planning-quality
stories to page 2 (3→12 widgets), each a real/non-obvious finding:
- **Forecast Value Add (FVA):** plan vs naive 'next week=this week' benchmark. **NEGATIVE both orgs** (-3.7%
  @2012, -11.2% @2120) — planning is currently WORSE than doing nothing. The headline credibility metric.
- **Correctable bias:** ~26% of off-plan items are persistently one-sided (5,448 over @2012) = a fixable
  worklist, not noise.
- **Accuracy by lead time:** counterintuitive — SHORT-lead items slip MOST (2012 +22.6d, 94.8% late) while
  long-lead run early (-9.6d). Points planning effort where it pays back.
- **MAPE trend vs 15% target:** weekly, volatile (59→209%), not stabilizing.
- Datasets ds_fva/ds_bias_persist/ds_acc_leadtime/ds_mape_trend CLI-tested; page audit clean.
**Time filtering redone (prior sub-phase):** removed the broken DATE range-slider; built a correct NUMERIC
weeks-ago slider (weeks_ago=DENSE_RANK desc, 1=latest…16=oldest, WITH MIN/MAX bounds) on raw datasets; and
parameterized the aggregated datasets (ds_sla/abc_median/accuracy_split/exc_pareto/rootcause_dc via :wk DATE
RANGE param, displayName required) bound to the f_week date-picker — so both controls filter aggregated tiles.
MoM/Cross-Org/plant/plan-evolution left full-span BY DESIGN (captioned).

## Page 4 drill-down rebuilt — fixed dead lines + richer story (2026-08-31)
User saw flat 'dead lines' + 'Render more data' on page 4. ROOT CAUSE: line/bar/table were disaggregated:true
on raw ds_pva (590k rows) → plotted raw rows, not a clean weekly series; at All-SKUs it blew the render cap.
FIX: new **ds_drill_sku** = per-SKU WEEKLY-aggregated dataset (one row/week/org) driven by a **:sku
single-select param** (default 48111850, a rich item — not 377120 which is near-zero early) + :wk range param.
Rebuilt page 3→10 widgets: KPIs (peak on-hand, worst $ gap — abs pushed to dataset, not counter), plan-vs-
actual+safety-stock line, gap-$-by-week bar (band-colored), flows line, **weeks-of-cover trend** (NEW,
stockout/overstock signal), **cumulative drift area** (NEW), evidence table. SKU shown per-org if it lives at
both DCs. All CLI-tested (48111850 → 16 clean weekly rows, non-flat); audit clean (caught+fixed a
MAX(ABS()) counter). Deployed+published. Render = browser gate.

## Page 7 spaghetti chart replaced with nervousness + convergence (2026-08-31)
User: the plan-evolution multi-line was 'good but I don't understand it' — it was ~26 target-week series
overlaid (unreadable suspension-bridge). Replaced p7_evo with two READABLE charts:
- **Plan nervousness** (ds_plan_nervous): one bar per target week = net revision % (latest vs first forecast),
  org-aware. Shows 2012 systematically walks plans DOWN 5-10%.
- **Plan convergence** (ds_plan_converge): avg |weekly plan revision| by weeks-to-target — the funnel;
  healthy = shrinks toward 0 as the week nears (2012: ~2.4M@24wk -> 0.9M@1wk). The strongest single
  plan-stability insight.
Both CLI-tested, audit clean, deployed+published. The 'biggest revisions' table (item-level detail) kept.

## Page 4 → field-based (All option + org/time reactive) (2026-08-31)
User: SKU picker needs an 'All' option, and page 4 must react to Org + timeline. Both stemmed from the
param-based design (a parameter needs ONE value → no 'All'; and global field-filters can't reach a
parameterized dataset). FIX: replaced ds_drill_sku (param) with **ds_drill_field** = raw item×org×week +
row-level precomputes (gap, cum_gap_units, weeks_of_cover, weeks_ago, band). Charts now SUM/AVG **by week**
(disaggregated:false) so: one SKU = its line, blank = portfolio 'All', no spaghetti. SKU picker is a
**field-based single-select on item_id** (blank=All). Wired ds_drill_field into the weeks-ago slider,
date-picker, and org filter → all three now react. Audit clean; deployed+published. weeks_of_cover is AVG-by-
week (valid per-SKU; portfolio = avg cover).

## MAPE-trend dead-line fix (2026-08-31)
The weekly MAPE line rendered flat. Cause: invalid encoding — TWO y-fields (mape + target_mape constant) AND
a color=org dimension on one line chart; Lakeview can't resolve multi-y + color, collapsed to a flat line.
(Data was fine: 2012 MAPE 59→75→149…) Fix: single y-field `mape`, color by org (2 clean lines), 15% target
moved to the title. **General rule now:** a line chart is EITHER multi-y (no color) OR single-y + color —
never both; put constant target/reference lines in the title/caption, not as a phantom y-series.

## Page 0 · Monday Cockpit — the action surface (2026-08-31)
User challenge: 'I look at the overview Monday and derive NOTHING — just another chart.' Correct: it showed
STATE (levels that barely move WoW). Built a new FIRST page that answers Monday: what CHANGED, what to DO,
what is escalating. Two new datasets:
- ds_cockpit_change (per-org WoW): newly-red count/$, resolved, escalations, stockout$ now vs prior Monday.
  Verified: this Monday 2,243 newly red = $23.7M new exposure (2012 1,777/$22.7M + 2120 466/$1.04M), 1,486
  recovered.
- ds_cockpit_actions: newly-red ranked by $ with a VERB (Expedite below-SS / Defer-cancel overstock /
  Fix-supplier chronic / Review) + systemic flag + named planner. e.g. M18 Chainsaw $1.03M, M18 Circ Saw
  $739K EXPEDITE.
Page 0 = headline + what-changed KPIs + ranked action list + action-mix bar + new-exposure-by-org. ALSO added
a 3-KPI what-changed strip to page 1 Overview (honors all 3 sub-options the user picked). Datasets CLI-tested,
audit clean, deployed+published. Step 1 of roadmap (Dashboard -> pipeline -> App).

### What I learned (user asked to record learnings)
A dashboard that shows a LEVEL ('13,146 red', '$1bn at risk') reads as 'just another chart' because the
number barely moves week to week — the planner has no trigger to act. The fix is to show the **delta** (what
newly changed since last period) + a **verb** (what to do) + a **$** (why it matters) + a **systemic flag**
(fix the order vs fix the source). State informs; change-plus-verb drives action. This is now a design rule:
an operational page should open with 'what changed and what to do', with the levels/analytics as the drill-down 'why'.

## Cockpit KPIs expanded — 4 more, each a DIFFERENT Monday question (2026-08-31)
Added a 2nd KPI row (ds_cockpit_kpi, single-row) so the cockpit answers more than 'how bad is the new stuff':
- **Net exposure swing:** stockout $ this wk vs last = **+$4.44M (worse)** — winning/losing gut-check.
- **Top-10 concentration:** top 10 items = **20.1%** of new $ at risk — makes a 2,243-item list tractable.
- **% systemic:** only **2.8%** of new $ is chronic-supplier — this week = work the orders, not escalate a supplier.
- **Excess capital:** **$113.5M** tied up in overstock (>3x SS) — the OTHER failure tail beside stockout.
All CLI-verified, audit clean, deployed. KPI counters do plain MAX on precomputed single-row cols.

### What I learned
Adding KPIs is only valuable if each answers a DIFFERENT question. The first 4 (newly-red / new-$ / recovered
/ escalations) all describe 'the new bad stuff'. The impactful additions changed the AXIS of the question:
direction (better/worse), tractability (concentration), targeting (systemic vs one-off), and the opposite
failure mode (excess vs stockout). Rule: before adding a KPI, name the decision it changes; if it duplicates
an existing tile's decision, it's noise.

## Cockpit made filterable — Org + ABC + week-replay (2026-08-31)
User: 'can the cockpit be filtered?' Audit: NO global filter reached ANY of the 3 cockpit datasets (my
earlier 'reacts to Org+week' caption was FALSE — corrected). Fix:
- Reworked ds_cockpit_change/actions/kpi to compute 'this vs prior Monday' from a **filtered-week rank**
  (DENSE_RANK over the surviving weeks; r=1=this, r=2=prior) instead of hard-coded MAX(week_start), + a :wk
  DATE-RANGE param. Verified: window <=2026-08-10 -> this=08-10/prior=08-03 (week REPLAY).
- Exposed organization_code (all 3) + abc (actions) as output cols; wired **f_org -> all 3, f_abc -> action
  list, f_week(:wk) -> all 3**. Weeks-ago slider intentionally NOT wired (relative-window concept conflicts
  with this/prior replay; date-picker is the clean control) — stated in caption.
- KPI widgets repointed to per-org cols (swing/excess SUM; systemic AVG; dropped portfolio-only top-10,
  replaced with current stockout-$). All CLI-tested, audit clean, deployed.

### What I learned
(1) A delta/'what-changed' page can't be week-filtered with a naive field filter — the period boundary is
computed INSIDE the query (MAX week), so filtering must be *relative to the surviving rows* (rank the filtered
weeks). That turns a filter into a **replay** control (pick any week = its Monday), which is more useful than
a plain filter. (2) Not every global filter belongs on every page — weeks-ago (relative) conflicts with a
this/prior page; matching the control's semantics to the page's logic matters more than wiring everything.

## Cockpit supporting visuals — the story behind the numbers (2026-08-31)
User: 'the cockpit is just numbers — where are the visualizations to support them? a number gets attention but
then "what do I look at now" has no answer.' Added a 'story behind the numbers' band (4 charts, page 0 now 18
widgets):
- **New-exposure trend** (weekly newly-red $, org-lined): reframes the $24M KPI — baseline is ~$25M/wk, the
  real anomaly is a $509M spike on 2026-06-15. Stops over-reacting to a normal week.
- **Newly-red $ by planner**: routes the fires (Bartholf $1.69M, Cotteleer $1.44M…) — 'who do I hand these to'.
- **Action-mix over time** (stacked area by verb): is the Expedite/Review pile growing?
- **Aging** (red-weeks-in-last-8 bands): 9,102 items festering 6+ wks vs 6,073 fresh — chronic vs new.
All CLI-tested, audit clean, deployed.

### What I learned
A KPI is a hook, not an answer. Each headline number must be paired with the ONE visual that answers the
question it provokes: $24M -> 'is that normal?' (trend); big number -> 'who owns it?' (by-owner); a level ->
'is it getting worse?' (over-time); a count -> 'fresh or chronic?' (aging). Design rule: a number without its
supporting picture leaves the planner at 'okay, now what?'. Pair every attention-grabbing KPI with its
because-visual.

## Page 7 Org-filter wiring + caption (2026-08-31)
User: 'ensure page 7 is attached to the filters.' Honest scope (not blind wire-all): f_org wired to the 5
DC-org tiles (nervousness, convergence, MoM, plan-change-items, PO-timing — all output organization_code).
LEFT full-span BY DESIGN: plant-movements (plant orgs 1006-1021, a different org universe from 2012/2120 —
filtering to DC orgs would blank it) and the time controls (nervousness/convergence/MoM span all forecast
horizons/months by definition). Caption corrected to state exactly what reacts. Audit clean, deployed.

## Systematic filter-coverage completion + in-dashboard help (2026-08-31)
User caught that filters didn't reach all widgets. Ran a full 8-page reach audit; found gaps were incremental-
build debt, not design. Fixed via the robust (all)-sentinel :param pattern (aggregated datasets can't be
field-filtered reliably):
- Org now reaches: cockpit supporting visuals (trend/planner/mixwk/aging), page-2 FVA/bias/leadtime/mape/SLA/
  accuracy-split/abc-median, page-3 rootcause_dc, page-1 net-trend. Each CLI-tested BOTH ways (:org_f='2120'
  -> 1 org; '(all)' -> both) so filtering AND 'All' both work.
- Week (:wk) added to cp_trend/actionmix where grain fits.
- Left NONE BY DESIGN: Cross-Org page (compares all orgs), plant-movements (plant org universe), ds_topexc &
  ds_exc_pareto (no org grain — cross-org top-N/totals).
**In-dashboard help (simpler explanations):** added a 'How to use this dashboard' panel on the filter page
(what each filter does + its reach + page roles + ABC meaning in plain words) and per-chart '_How to read_'
italic lines under the 8 non-obvious charts (nervousness, convergence, FVA, bias, lead-time, cockpit
trend/aging, cumulative drift). Audit clean, deployed.

### Coverage rule (learned)
Filter reach is a per-dataset contract, not global: a field-filter only reaches a dataset that OUTPUTS the
field AND isn't GROUP BY (else it silently no-ops). For aggregated datasets use a param with an (all)-sentinel
guard: (:p='(all)' OR col=:p). And match filter→page semantics: don't wire a filter where it blanks/distorts
(cross-org compare, different org universe, cross-horizon analytics). Audit reach by reading each widget's
dataset vs each filter's bound-datasets — the only reliable check.

## REGRESSION + FIX: whole dashboard went blank (2026-08-31)
My prior filter-coverage change blanked every tile. **Data was never lost** (gold intact: 590,275 rows / 2
orgs — verified first). Root cause: I bound a **scalar STRING param with an (all)-sentinel** (`(:org_f='(all)'
OR org=:org_f)`) to `f_org`, but **f_org is a filter-MULTI-select** — a multi-select emits an ARRAY, so a
scalar param binding is invalid and a broken global filter blanks every tile it touches.
**Fix:** switched the org param to `complexType: MULTI` with the correct guard
`(size(:org_f)=0 OR array_contains(:org_f, organization_code))` and an **empty-array default** (= all), on all
13 affected datasets. Verified both ways (empty->2 orgs, ['2120']->1). Cockpit datasets were field-bound (not
affected). **Functionality check:** ALL 40 datasets return rows at default filter state. Deployed+published.

### What I learned (critical)
Match the param's complexType to the FILTER WIDGET type: a filter-multi-select needs a **MULTI (array)** param
with `size()=0 OR array_contains(...)` and an **empty-array** default; a scalar `=:p`/sentinel only works for a
single-select. A mismatched param binding on a GLOBAL filter doesn't just fail its own tile — it blanks the
whole dashboard. New pre-deploy gate: after any filter/param change, run the 'every dataset returns rows at
default params' check BEFORE publish (not after the user sees blanks).

## Page-4 flat lines (p4_line, p4_flow) — the multi-y bug, fixed + swept (2026-08-31)
Distinct from the filter regression (that was fixed; data intact). p4_line and p4_flow rendered flat because
they had **multiple y-fields** (3 each; p4_line also had color) — the same 'multi-y line collapses' bug as the
earlier MAPE chart. I had NOT swept for it dashboard-wide. Fix: built long-format datasets
ds_drill_onhand_long / ds_drill_flows_long (week × series × units) and rebuilt both as **single-y (units) +
color(series)** — the correct multi-series pattern. Wired both to f_org/f_week + the SKU picker (raw
field-binding) so they stay filterable. Then **swept ALL line/area charts**: 0 multi-y remain. All 42 datasets
return rows at default. Deployed.

### Rule reinforced (now applied proactively, not reactively)
A multi-series line/area = ONE y-field + a series column via color (long format). NEVER multiple y-fields
(collapses to flat) and never multi-y + color together. Added to the pre-deploy sweep: scan every line/area
widget for >1 y-field before publish. I should have done this sweep when I first hit it on the MAPE chart —
doing it reactively cost the user two catches.

## Open items unchanged (business owner)
Canonical receipt source (purchase_receipt_line vs deprecated purchase_order_delivery); planned-receipts from
PO promised dates (plan measure empty); variance % bands; prior-week vs same-week comparison snapshot.

## SDP pipeline (parallel build) — 2026-08-31
Built Lakeflow Declarative Pipeline `p1_actuals_sdp` (id b6f16cf7-b17e-4b08-beaa-6c8e7fb97585), serverless
+ triggered, catalog/schema sandbox_operations/po_management, PREVIEW channel. 35 materialized views:
- **Silver (4):** sdp_planned_weekly, sdp_actuals_weekly, sdp_transfer_stages, sdp_po_stages (+_load_ts).
  Source-equivalent to rung2_/p1flow_ builds, read live from prod; transfer/PO stages WIDENED to the full
  4-month window (were 8-week) — closes the earlier consistency note.
- **Gold (3):** sdp_plan_vs_actual (prior-week baseline, variance/$/status/tier/planner/WoW; CLUSTER BY
  item_id for sku-drill pruning; 4 EXPECT DQ constraints), sdp_order_stage_gold (org-aware bands + maneuver +
  chronic), sdp_rootcause_plant (re-derived from inventory_material_transaction; 99.95% recon to prior table).
- **Serving (28):** per-widget-grain aggregates (sdp_agg_week_org 32r, _scorecard 2r, _fva 2r, _sla_ow,
  _accuracy_split, _rootcause_dc, _money_ow, _transitions [cockpit], _plan_nervous/converge/evolution/
  change_items, _po_timing, _acc_leadtime, _mom, _abc/_abc_median, _tier, _varpct_long, _sku_share,
  _planner/_planner_conc, _scale_ctx, _exc_pareto, _orgcmp, sdp_exceptions, sdp_agg_overview [626r cube]).
  Fidelity: additive COMPONENTS stored (sum+cnt), not pre-divided averages; percentile tiles whole-window;
  NO per-cell ROUND (round at display). Overview cube week×org×abc×status keeps filter dims as columns.
Pipeline: 3 updates (initial 34 MVs; +sdp_agg_overview; +full-precision fix) all COMPLETED, 0 ERROR events.
Job `p1_actuals_weekly_sdp` (id 418760739520160): quartz `0 57 7 ? * MON` America/Chicago, PAUSED,
on_failure email; manual run-now proved Job→pipeline wiring (update 8d6f641c COMPLETED). full_refresh=false
(incremental); first run backfilled the 4-month window.
Clone dashboard "P1 Actuals — SDP (Rung 2)" id 01f1a5371959178aa137d5551347afff — 42 thin datasets over
sdp_* (map in SDP_THIN_QUERY_MAP.md), same 8 pages/widgets/params/theme; only queryLines simplified.
Verification (full queries+results in SDP_VERIFICATION_LOG.md): equivalence bit-exact; DQ 0 violations;
perf gate overview/KPI 2–160 rows (was 590,275); 42/42 datasets return rows; 0 multi-y / 0 binding breaks;
originals unchanged. Window stays 4-month (verify-then-widen to 180d = flip pd_lo + full-refresh, user's call).
