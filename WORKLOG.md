# MKE Supply-Chain — Work Log & Decision Journal

**Purpose:** a durable, append-only record of the work — *what was asked, what we decided, what we built, and
why* — so the history survives chat compaction and new sessions. The chat transcript is NOT a reliable record
(this project already lost its earliest turns to compaction). **Standing practice: after every accepted piece
of work, append an entry here** (date, the ask in the user's words, decision, artifacts, evidence, follow-ups).

Build logs hold *how a thing was built* (RUNG2_BUILDLOG, P1FLOW_BUILDLOG, P1_SLICE_BUILDLOG). This log holds
the *trail of intent and decisions* across the whole engagement. Reconstructed from the session compaction
summary + artifacts on 2026-08-31; entries after that were logged live.

---

## Phase 0 — Understanding & data stories (earlier session; reconstructed)
- **Ask (trail):** understand MKE supply-chain data by P1–P4; build ID-anchored data stories (positive/
  negative, anti-patterns, hidden patterns, lineage); solution architecture; an interactive HTML dashboard;
  a session log.
- **Built:** the full `data_understanding/data_stories/` library (S1–S9, G, R, V, T, C, RW, LG, EM, N, O, P,
  AP anti-patterns, HOP/STATE/QTY, GEO, CAUSES, IMPACT, lineage, catalog + synthesis), a solution
  architecture capstone, an interactive HTML dashboard.
- **Key decision:** `prod_edw.fact.purchase_receipt_line` is the P1 receipt source (the raw-Oracle crosswalk
  "blocker" dissolved) — `KEY_FINDING_receipt_source.md`.

## Phase 1 — P1 vertical slice (Rung 1)
- **Ask:** "what should be our next step?" → build the P1 slice; "source is read only… we will scale to the
  last 8 weeks… design so we can load the whole year… step by step."
- **Decision:** scale-aware rungs (1 item → all items → full year); READ-ONLY prod; writes to
  `sandbox_operations.po_management.p1slice_*`; develop in workspace, promote later.
- **Built:** `p1slice_planned_weekly / actuals_weekly / plan_vs_actual` (gold, 8 rows hero item), reconciled
  (receipt tie-out exact; semi-additive 538,116-vs-83,254 guard). Notebook + `P1_SLICE_BUILDLOG.md`.
- **Correction:** notebook SQL first rendered as markdown (each SQL must be its own cell) — user flagged; fixed.

## Phase 2 — Native AI/BI (Lakeview) dashboard, Rung 1
- **Ask:** "Build the native Lakeview dashboard on p1slice_plan_vs_actual." Then a chain of "no data" / "empty
  framework" / "go to docs" pushes.
- **Root causes fixed (now the fastpath skill):** widget query must be named `main_query`; no functions in
  widget expressions (push ABS/CASE into dataset SELECT); missing comma between queryLines breaks the dataset;
  filters on a global-filters page; % on 0–100 uses number-plain+suffix.
- **Built:** Rung-1 dashboard (ID 01f1a504e3a31d6097591184469039b4) + `lakeview-dashboard-fastpath` skill +
  memory. **Lesson:** copy known-good widget JSON, TEST the concatenated dataset query via CLI before deploy.

## Phase 3 — Rung 2 (all items) + multi-org 2120
- **Ask:** "work with org 2012 for Rung 2 … do not delete current ones, create new assets"; "think creatively
  on what questions the dashboard can answer … tackle the data_stories"; "what if I add more orgs — can the
  query/dashboard cater to it?"; "there was one more org (2120) — let's go with the recommendation."
- **Decisions:** drop the item filter (same SQL proves generalization — hero item numbers identical R1↔R2);
  org→plan mapping (2120→Mexico plan, else Global) with a single predicate to kill the 2120 double-count.
- **Built:** `rung2_planned_weekly / actuals_weekly / plan_vs_actual` (297,211 rows = distinct item×org×week),
  Rung-2 dashboard (ID 01f1a50aed891d5c85b5e64b2c3c5d5b) — org-aware, 6 pages. `RUNG2_BUILDLOG.md`.
- **Corrections caught by self-review:** "no-data" band was really "Unplanned (no plan)"; color/label
  inversion fixed by pinning semantic colors; %/$ column mislabels fixed.

## Phase 4 — "orgs are not interchangeable" (2120 validation)
- **Ask:** "we can't blindly say all orgs behave the same … find NEW scenarios for the new org, validate the
  identified ones, derive learnings + data-model changes, use subagents, log their activities."
- **Method:** 2 logged subagents (A: validate scenarios on 2120; B: hunt new 2120 scenarios) + **I
  re-verified every load-bearing number myself.**
- **Findings:** all 7 scenarios apply but behave differently → **thresholds must be org-specific**; 3 NEW
  verified findings (planner concentration 6 vs 92; 41% Mexico-exclusive SKUs; net-receiving pattern).
- **Correction:** subagents' "inverted bias" was refuted by a row-sign test — both orgs OVER-plan, 2012 ~5×
  harder (fixed in artifacts + memory).
- **Built:** `data_stories/org2120_validation/` INDEX + A + B + C (synthesis w/ 5 data-model changes).
  Memory: [[mke-orgs-are-not-interchangeable]].

## Phase 5 — More dashboard stories, scale-to-N-orgs
- **Ask:** "can we tell more stories with the new info … tomorrow there might be many orgs, we won't build
  separate dashboards … show contrast … but one can't say until they see the data … scope for tomorrow is
  these two orgs."
- **Decision:** every story widget GROUPS BY org (auto-renders new orgs); contrast in RELATIVE terms
  (%, ratios, per-item, percentiles) so a small org is comparable; scorecard table = the N-org backbone.
- **Built:** dashboard page "5 · Cross-Org Contrast" (scorecard, overage bar, variance-percentile grouped
  bar, lean-yet-green scatter, planner concentration, SKU shared/exclusive, scale context) + 5 datasets, all
  CLI-tested, self-audited clean.
- **Correction:** re-fixed the "inverted bias" framing on the chart (both over-plan, 2012 ~5×).

## Phase 6 — Network/flow discovery + order-lifecycle slice (preemptive timing)
- **Ask:** "individual item behavior across orgs at different scales … planners who control the chain — could
  they meet? hops/routes/spending double? maybe there are tables we haven't explored." Then: "are we showing
  hops / the current stage?" Then: "expected/actual per stage → preemptive maneuvers (skip/cancel/resize) not
  just a bottleneck threshold." Then: "maybe SCD2 for history — necessary or over-engineered?"
- **Discovery (metadata sweep):** found the network tables (transfer_order_receipt/shipment,
  inventory_rebalance_*, sourcing rules, freight). **Corrected a wrong hypothesis:** 2120 is NOT a
  transfer-fed hub — it has ZERO transfers (Buy/Make leaf); **2012** is the transfer hub. Coordination signal
  verified: 99.9% of dual-org SKUs have different planners per org.
- **Decision:** "prove it as a slice first" (user chose). Honest scope: 2 real stages
  (ordered→in-transit→received), NOT a 5-gate flow (accept/putaway empty); no live feed; **no hand-built
  SCD2** (over-engineering; none exists) — reuse the historical lead-time-error table instead.
- **Correction:** `purchase_receipt_line.expected_receipt_date` is a same-day MIRAGE; real PO timing =
  `features.general_historical_purchase_order_lead_time_errors`.
- **Built:** `p1flow_transfer_stages / p1flow_po_stages / p1flow_order_stage_gold` (org-aware timing bands,
  recommended maneuver, chronic-slipper signal) — reconciled (gold slip == source slip exactly).
  `P1FLOW_BUILDLOG.md`, `D_network_flow_tables.md`, notebook mirror. **Payoff:** 76% of 2120's "expedite"
  orders are chronic-supplier problems (fix the source, not the order). Memory:
  [[mke-order-lifecycle-flow-slice]].

## Phase 7 — Consumption-surface enablement (Genie, then App)
- **Ask:** "note all our interactions/activities — Genie will need to do the same via AI over this data";
  "Genie should know what questions might be asked, based on all observed scenarios"; "these will also be part
  of Databricks App development — interactive, searchable, write-backable, approve/reject, alerts."
- **Built (design, not deployment):** `GENIE_ENABLEMENT_NOTE.md` (data surface + reasoning playbook + build
  recipe), `GENIE_QUESTION_BANK.md` (every scenario → questions + guardrail Q&A), `APP_ENABLEMENT_NOTE.md`
  (read-signal → App action mapping, Lakebase entities, safe write-back path). Memory:
  [[mke-genie-app-enablement]]. Three surfaces: dashboard=show, Genie=ask, App=act.
- **Ask (this entry's trigger):** "after every acceptable work, log it, so history isn't lost." → created
  this WORKLOG.md as the standing decision journal.

---

## Phase 8 — Decision-first dashboard redesign (pages 2/3/4 + money tile)
- **Ask:** "Can we not show something more… how will this make anyone understand! What ways can these be
  re-shown; what new things make great impacts!" + "think!!!" (on screenshots of pages 2/3/4).
- **Diagnosis (honest):** page 3 Exception Queue was **BROKEN** (bound to full wide table → on-plan items on
  top, 7×-per-item repeats); page 4 Drill-down **dead-on-arrival** (SKU default "All" → 28k-SKU crush); page 2
  showed the **outlier-inflated mean** ("140% bias"). Root problem: showed *data*, not *decisions*.
- **Decision:** user chose "decision-first, all 3 pages." Rebuilt around what a planner/manager must DECIDE.
- **Built (verified numbers, all reconciled):** 6 new datasets; Page 2 = SLA scorecard (MAPE 2012 124% /
  2120 37% vs <15%) + over/under/on-plan area + ABC median; Page 3 = Monday Action List (cost-ranked, 1
  row/item, exception_type + Systemic-vs-one-off root flag) + $-by-type bar + KPIs; Page 4 = default worst
  SKU + plan-vs-actual gap + flows; Overview = **Money at risk** ($662M stockout-risk vs $843M excess capital
  @2012). Deployed + published same ID `01f1a50aed891d5c85b5e64b2c3c5d5b`. Log: RUNG2_BUILDLOG.md.
- **Guardrail added to memory (user):** NO real Oracle write-back ever — simulate in sandbox when we reach
  the action stage. ([[mke-project-guardrails]] updated.)
- **Follow-up:** user to confirm render in browser (CLI proves structure+data only).

## Phase 9 — Close the in-scope-but-unshown dashboard gaps (page 7)
- **Ask:** "Work on the IN-SCOPE but NOT YET SHOWN on the dashboard (the real gaps)" → "add these."
- **Feasibility-probed first** (won't build on absent data): confirmed `rung2_planned_weekly` has 8 snapshots
  covering shared target weeks (enables UC5/2.4.1); MoM only 2 months; root-cause still needs the ledger.
- **Built page "7 · Plan Changes & Timing":** plan-evolution-across-snapshots multi-line (UC5/2.4.1 must-have)
  + biggest-plan-revisions table + month-over-month (2.3.2, labeled thin) + receipt-timing M4 by lane×org.
  4 new datasets CLI-tested, page audit-clean, deployed+published same ID. Dashboard now 8 pages.
- **Honest scope note:** 2.3.7 five-category root-cause remains DEFERRED (needs inventory_material_transaction);
  page 3 keeps the symptom proxy, not faked. Render to be confirmed in browser.
- **Also this session:** confirmed a PRIOR pipeline build exists in the workspace (redkeychain-actuals-customer
  + rk_actual_sdp + paused rk_actuals_weekly job) — user said set it aside for now; not built upon.

## Phase 10 — Drill-down real fix + global-filter binding audit
- **Ask:** page 4 "show this in a better way, more explainable, supporting info" → then "verify Global filter
  is attached to all required/connected widgets, wherever applicable."
- **Page 4:** found the default-SKU bug I had wrongly claimed fixed — key was `defaultSelections` (plural);
  Lakeview wants `defaultSelection` (singular) → filter defaulted to "All" → 28k-SKU overlay. Fixed +
  rebuilt page to teach (how-to-read caption, 2 reactive KPIs, plan-vs-actual line, dollarized gap bar,
  flows, week-by-week evidence table). Verified singular key in deployed JSON.
- **Global filters:** audited by READING each canvas dataset's real output columns vs filter field names.
  Found the **Org filter silently dead on pages 2/3/5/7** (datasets output `org`, filter binds
  `organization_code`). Fixed: surfaced raw `organization_code` in every filterable aggregated dataset (kept
  `org` alias so widgets unbroken); 3 CTE datasets needed it at the outer select. Result: Org binds on pages
  1,2,3,4,6,7; page 5 left intentionally global (compare-all-orgs). Widget audit clean; deployed+published.
- **Lesson reinforced twice:** CLI proves structure+data but NOT selection behavior or filter reach — must
  verify render + read real output columns (substring-on-SQL lies on aliased sources).

## Phase 11 — 4-month reload, prior-week baseline, root cause (2.3.7), week slider
- **Asks:** "load 4 months, store the query in a notebook, reflect in all dashboards"; "2.3.7 root cause —
  go for it, are you stuck?"; "what will doing both do?"; "are joins inflating / granularity issues?";
  "add a weekly slider, global, in dashboard".
- **4-month widen:** rebuilt rung2 gold over 16 weeks (590,275 rows); stored runnable workspace notebook
  `rung2_actuals_build` (closes the reproducibility gap — rung2 was tables-only before). MoM now 4 months.
- **Prior-week baseline (doc §5.1):** the widen exposed an inconsistent lookback in the old earliest-snapshot
  pick; changed to nearest-snapshot-before-target → uniform 7-day lookback. Approved by user.
- **Integrity (user challenge):** re-verified at 4-mo — dim_series 1:1 (no inflation), grain clean, 2120
  double-count guard holds, on-hand not fanned. All PASS.
- **Root cause 2.3.7:** proved with evidence the ledger covers PLANT orgs only (not DC 2012/2120). Built BOTH
  lenses: rootcause_dc (per-signal, residual 80%→41%) + rootcause_plant (true ledger 5-cat, upstream tier).
  Surfaced as page-3 DC tile + page-7 labeled plant-movement tile (never summed).
- **Week slider:** global range-slider on week_start added; deployed+published. Dashboard datasets = 25.
- **Follow-up logged:** p1flow_* still on old 8-week window — re-widen when flow tiles need it.

## Phase 12 — Money-at-risk counters not org-reactive (fix)
- **Ask:** user noticed the two overview Money-at-risk counters do not change when Org filter changes; "by design?"
- **Answer:** no, a bug. They read a GROUP-BY-org dataset (ds_money_risk) which a field-based filter can't
  auto-WHERE. Fixed by repointing to raw ds_pva + derived stockout_gap_dollar/excess_capital_dollar cols;
  now Org filter + week slider both reach them. Values higher because gold is now 4 months. Deployed+published.

## Phase 13 — Deeper page 2 (FVA + bias + lead-time + MAPE trend) + time-filter redo
- **Ask:** 'not satisfied with number of widgets / limited story — anything else impactful?'
- Added 4 verified planning-quality stories to page 2 (3→12 widgets): **Forecast Value Add (NEGATIVE both
  orgs — planning worse than naive)**, correctable-bias worklist (~26%), accuracy-by-lead-time (short-lead
  slips most, counterintuitive), MAPE-trend-vs-15%-target.
- **Time filter redone (user caught my broken slider):** range-slider on a DATE with no MIN/MAX was
  misconfigured; user reframed to a numeric weeks-lookback slider — built correctly (weeks_ago rank + MIN/MAX
  bounds). Kept date-picker too; parameterized aggregated datasets so both controls filter them. Deployed.
- All datasets CLI-tested, audits clean. Render = browser gate (slider must show 1–16, not epoch).

## Phase 14 — Page 4 drill-down rebuild (dead-lines fix + richer story)
- **Ask:** page 4 shows 'dead lines' (single SKU) + 'Render more data' (All); too few widgets; better visuals.
- **Root cause:** charts were disaggregated:true on raw 590k-row ds_pva. Fix: per-SKU WEEKLY-aggregated
  ds_drill_sku (:sku + :wk params), default SKU 48111850 (rich, not near-zero 377120).
- Rebuilt 3→10 widgets: KPIs, plan-vs-actual+SS line, gap-$ bar, flows, weeks-of-cover trend (new),
  cumulative drift area (new), evidence table. CLI-tested clean; caught+fixed MAX(ABS()) counter. Deployed.

## Phase 15 — Replace unreadable plan-evolution spaghetti (page 7)
- **Ask:** first chart on page 7 'good but I don't understand it' (26 overlaid target-week lines).
- Replaced with two readable charts: **plan nervousness** (net revision % per week, bar) + **plan
  convergence** (avg |revision| by weeks-to-target, funnel line). Both org-aware, CLI-tested, deployed.
  Detail table kept. Story now readable in 2 seconds: do our plans stabilize as they firm up?

## Phase 16 — Page 4 field-based (All + org/time reactive)
- **Ask:** SKU picker needs 'All'; page must change with Org + timeline.
- **Cause:** param-based SKU picker (a param needs one value → no All; global filters can't reach a
  parameterized dataset). Fix: raw ds_drill_field + charts SUM-by-week (disaggregated:false); field-based
  SKU single-select (blank=All); wired org/slider/date-picker to it. All reactive now. Deployed.

## Phase 17 — Monday Cockpit (page 0): the action surface (roadmap step 1/3)
- **Ask:** 'I look at the overview Monday and derive nothing — I wish it told me the impact / raised a flag /
  told me what to do.' + 'next level!' + roadmap: Dashboard now -> stable pipeline -> App (keep logging +
  learnings).
- **Built:** new FIRST page '0 · Monday Cockpit' — what-changed KPIs (2,243 newly red=$23.7M this Monday),
  ranked verb action list (Expedite/Defer-cancel/Fix-supplier + systemic flag + planner), action-mix bar,
  new-exposure-by-org. Plus a what-changed delta strip on page 1 (honored all 3 sub-options user chose).
  ds_cockpit_change + ds_cockpit_actions CLI-tested, audit clean, deployed.
- **What I learned:** a LEVEL reads as 'just another chart' (barely moves WoW, no trigger). Action needs the
  DELTA + a VERB + $ + systemic flag. Design rule now: operational pages open with 'what changed & what to
  do'; analytics are the drill-down 'why'.
- **Next (roadmap):** step 2 = stable SDP+Job pipeline; step 3 = the App (clickable actions, Lakebase,
  simulated writeback). Not this pass.

## Phase 18 — Monday Cockpit: 4 additional KPIs (different-axis)
- **Ask:** 'add something more / additional KPIs?'
- Added net-exposure-swing (+$4.44M worse), top-10 concentration (20.1%), %systemic (2.8%), excess-capital
  ($113.5M) as a 2nd KPI row on page 0. All verified/audit-clean/deployed.
- **Learned:** a new KPI earns its place only if it changes a DIFFERENT decision than the existing ones —
  direction / tractability / targeting / opposite-tail here. Name the decision before adding; else it's noise.

## Phase 19 — Cockpit filterable (Org + ABC + week-replay)
- **Ask:** 'can the cockpit be filtered?' (+ 'what is ABC in business terms?' — answered: value-based Pareto
  tiering, A=vital few $268M / D=long tail).
- **Found:** cockpit reacted to NOTHING (my caption was wrong; fixed). Reworked 3 cockpit datasets to rank
  the FILTERED weeks for this/prior (week-REPLAY, verified <=08-10 -> 08-10/08-03) + :wk param; exposed
  org/abc; wired f_org(all3)/f_abc(actions)/f_week(all3). Weeks-ago slider deliberately not wired.
- **Learned:** delta pages need period logic relative to surviving rows (not hard MAX) -> filtering becomes
  replay; and match each control's semantics to the page (don't wire every filter everywhere).

## Phase 20 — Cockpit supporting visuals (story behind the numbers)
- **Ask:** 'cockpit is just numbers — where are the supporting visualizations? a number gets attention but
  "what do I look at now" is limited.'
- Added 4 because-visuals on page 0: new-exposure TREND (reframes $24M as normal vs the $509M Jun-15 spike),
  newly-red $ BY PLANNER (routing), action-mix OVER TIME (is it worsening), AGING (9,102 festering 6+ wks).
  All CLI-tested/audit-clean/deployed.
- **Learned:** a KPI is a hook not an answer — pair each headline number with the ONE visual answering the
  question it provokes (normal? who? worsening? fresh/chronic?). Number without its because-visual = 'now what?'.

## Phase 21 — Page 7 Org filter + explained the nervousness/convergence charts
- **Ask:** attach page 7 to filters; also explain the first two charts.
- Wired f_org to the 5 DC-org tiles; left plant-movements + time controls full-span BY DESIGN (different org
  universe / need full horizon). Caption corrected. Deployed.
- Explained (verbally) the two hardest charts: NERVOUSNESS = net revision per target week (2012 over-plans
  then walks down); CONVERGENCE = does weekly revision shrink as the week nears (2012 never funnels to 0 =
  chronically unstable). Both tie to the negative-FVA finding = plan over-optimism/instability.
- **Learned:** 'attach to filters' isn't wire-everything — match filter to dataset grain/org-universe; a
  filter that blanks or distorts a chart is worse than no filter. State what reacts in the caption.

## Phase 22 — Complete filter coverage (robust :param) + in-dashboard help
- **Ask:** 'not all filters reach all widgets' + 'put these details in the dashboard simply'.
- Audited all 8 pages; closed the gaps with the (all)-sentinel :param pattern so Org truly reaches all
  meaningful DC tiles (cockpit visuals, page-2 analytics, page-3 rootcause, page-1 net-trend) — CLI-tested
  both ways. Left Cross-Org/plant/top-N NONE by design.
- Added a 'How to use this dashboard' panel (plain-language filter guide + page roles + ABC meaning) and
  per-chart 'How to read' lines under the 8 hard charts.
- **Learned:** filter reach is a per-dataset contract (output-the-field + not-GROUP-BY, else param with
  (all)-sentinel); match filter to page semantics; audit by reading widget-dataset vs filter-bindings.

## Phase 23 — REGRESSION FIX: dashboard blanked (scalar param on multi-select filter)
- **Ask:** 'where did my data go? what change impacted this; resolve it + ensure functionality not broken.'
- **Data intact** (gold 590,275 rows verified first). Cause: bound a scalar (all)-sentinel STRING param to
  f_org which is a filter-MULTI-select -> invalid ARRAY-vs-scalar binding -> broken global filter blanked
  every tile. Fixed: MULTI param + (size()=0 OR array_contains(...)) + empty-array default on 13 datasets.
  Verified both ways; ALL 40 datasets return rows at default. Deployed.
- **Learned:** param complexType MUST match the filter widget (multi-select -> MULTI array + array_contains +
  empty default; single -> scalar). A bad param binding on a GLOBAL filter blanks the WHOLE dashboard, not
  just one tile. New gate: run 'every dataset returns rows at default params' before every publish.

## Phase 24 — Page-4 flat lines fixed + dashboard-wide multi-y sweep
- **Ask:** 'first two charts on page 4 still dead lines — thought we resolved it.'
- Separate bug from the filter regression: p4_line/p4_flow had MULTIPLE y-fields (multi-y line collapses).
  Rebuilt as long-format single-y + color(series) datasets (ds_drill_onhand_long/flows_long), wired to
  org/week/SKU filters. SWEPT all line/area charts -> 0 multi-y remain. All 42 datasets return data. Deployed.
- **Learned:** apply the multi-y rule PROACTIVELY — sweep every line/area for >1 y-field before publish, don't
  wait to be caught chart-by-chart. Added to pre-deploy gate alongside the 'every dataset returns rows' check.

## Standing practice (do this every time)
After each accepted deliverable, append: **date · the ask (user's words) · decision & why · artifacts
(paths/IDs) · evidence/reconcile result · corrections · follow-ups.** Keep build-mechanics in the relevant
BUILDLOG; keep intent/decisions here. Memory files hold the durable cross-session facts.

**Backups:** after appending an entry, copy this file to `worklog_backups/WORKLOG_<YYYYMMDD_HHMMSS>.md` so
the history survives an accidental overwrite/delete of the single root file. The `worklog_backups/` dir is
append-only, timestamped snapshots — never edited.

## Phase 25 — SDP pipeline (roadmap step 2): parallel build, clone dashboard, thin queries
- **Ask:** "go ahead with the SDP path — clone the dashboard, write into a NEW set of tables so I keep the
  working dashboard + its data; create an SDP pipeline that materializes ALL datasets (silver, gold,
  aggregates, views) so the dashboard runs SIMPLIFIED queries and gets the same outcome." + "do aggregations
  FIRST so the dashboard doesn't lag at scale — challenge me but make it better." + "no hardcoded data — build
  from what we have" + "are we sure we have all the data?" + "log the test cases and queries too."
- **Decision & why:** built a PARALLEL Lakeflow SDP pipeline `p1_actuals_sdp` (serverless, triggered) writing
  35 MVs to `sandbox_operations.po_management.sdp_*` — never touching the live rung2_*/p1flow_* tables or the
  working dashboard (safety net). Layers: 4 silver + 3 gold (source-equivalent to the existing builds, read
  live from prod — zero literals) + 28 per-widget-grain serving aggregates. Cloned the dashboard to thin
  queries over the serving tables. Cadence = WEEKLY triggered batch (NOT streaming/daily): the plan grain is
  weekly (Monday snapshot); MVs over batch facts per the skill decision tree. The App (step 3) is the
  real-time surface via Lakebase — different clock, not this pipeline.
- **Artifacts:** pipeline `p1_actuals_sdp` id b6f16cf7-b17e-4b08-beaa-6c8e7fb97585 (35 MVs);
  Job `p1_actuals_weekly_sdp` id 418760739520160 (Mon 07:57 CT, PAUSED, on_failure email);
  clone dashboard "P1 Actuals — SDP (Rung 2)" id 01f1a5371959178aa137d5551347afff (published);
  source `workspace_assets/p1_actuals_sdp.sql` (+workspace mirror), `rung2_dashboard_sdp.json`,
  `SDP_THIN_QUERY_MAP.md`, `SDP_VERIFICATION_LOG.md` (all test queries+results), `P1_STATUS.md` (gap scorecard).
- **Evidence/reconcile:** sdp gold == live gold EXACT — 590,275 rows, per-org row/net-$/red diffs all 0;
  planned_weekly 16,464,696 identical; newly-red 2,243/$23.72M and FVA −3.7%/−11.2% identical to live;
  DQ 4 EXPECT constraints 0 violations, org_plan_pairs=2; pipeline 0 ERROR events. Perf gate: overview/KPI
  serving tables 2–160 rows (was 590,275 live → ~18,000× cut). 42/42 clone datasets return rows at default;
  0 multi-y, 0 binding breaks. Originals intact (rung2 gold still 590,275; original dashboard ACTIVE/unchanged).
- **Corrections:** (1) rootcause_plant had no saved build SQL → re-DERIVED from inventory_material_transaction
  + location_scd1; reconciled to 99.95% (residual = the "PO Receipt Adjustment" label boundary; chose
  adjustment-first). (2) ds_sla referenced organization_code but serving MV outputs `org` → fixed. (3) User
  caught the OVERVIEW page still scanning raw 590k (its counters/bars aggregate in-widget); built
  sdp_agg_overview cube (626 rows), repointed 9 additive tiles, kept c_bias(AVG)/c_items(COUNT DISTINCT) on
  raw (widget can't reconstruct from a rollup); a per-cell ROUND caused a $9-on-$2.5bn drift → stored
  full-precision, round at display → diff now exactly 0.
- **Learned:**
  1. **Pre-aggregate to per-WIDGET grain, and store ADDITIVE COMPONENTS, never pre-divided averages.** MAPE/SLA
     store sum_abs_var_pct + cnt; the thin query does SUM/SUM over picked weeks → exact AVG, tiny scan. This is
     the mechanism that makes "aggregate-first" both fast AND bit-exact.
  2. **A Lakeview counter/bar does ONE aggregation over one field** — so COUNT DISTINCT and weighted-AVG tiles
     CANNOT be served from a rollup; they must read a raw (narrow) dataset. Know which measures are additive
     before you pre-agg. Not every tile can be collapsed to 32 rows, and that's correct, not a failure.
  3. **Never ROUND inside a serving/pre-agg table.** Rounding per-cell then re-summing drifts vs the base fact
     (here $9 on $2.5bn). Keep full precision in the cube; round only at display.
  4. **A pipeline is the place to MOVE computation, not add data.** The SDP layer introduced zero new source
     reads — same prod tables the live dashboard already used; it just materializes the heavy joins/windows once.
  5. **Weekly batch vs real-time is a per-SURFACE choice.** Analytics (weekly plan) = batch MVs; App
     interactions = Lakebase real-time. Match freshness to the signal's actual change rate; don't stream a
     weekly fact.

## Phase 26 — Widen to 180-day backfill (doc D4/P4) + make the window ONE KNOB
- **Ask:** "do the 180-day load from the pipeline AND in both dashboards" + "if changing the date is so
  tedious, there needs to be a better way!" + "why were we running p1flow?"
- **Decision & why:** requirement doc D4/P4/O10 = backfill 180 days (~26 weekly snapshots), do not exceed.
  Cutoff = 2026-03-02 (clean Monday, ~175d, under the 180 cap). Widened BOTH stacks so they stay identical:
  SDP pipeline (sdp_*) AND the original rung2_*/p1flow_*/rootcause_plant. **Root-caused the tedium:** the
  window was 7 hardcoded literals across 3 files. Refactored the SDP SQL so the window lives in ONE place —
  pipeline `configuration` keys (p1.pd_lo/pd_hi/wk_lo/wk_hi/ledger_hi) referenced via ${...} substitution.
  Future window change = one `databricks pipelines update --json` + full-refresh. No SQL edits, no re-upload.
  p1flow was widened because the dashboard's PO-timing / lead-time-band / chronic-slipper tiles read it; if
  left at the old 8-week window while gold ran 180d, pages would silently disagree (e.g. an item wrongly
  flagged "not chronic" because its late history was cut off). Also closed the pre-existing 8-week stale-window
  debt flagged in the build log.
- **Artifacts:** SDP config knobs set on pipeline b6f16cf7; parameterized `p1_actuals_sdp.sql` (${p1.*});
  widened `rung2_actuals_build.sql` + `p1flow_order_lifecycle.sql`; both dashboards' default f_week lower
  bound 2026-05-11 → 2026-03-02 (11 param defaults each); redeployed+published both (ids 01f1a50a… original,
  01f1a537… SDP clone).
- **Evidence:** SDP full-refresh COMPLETED via config knob; sdp gold 924,987 rows, 25 weeks, 2026-03-09→08-24,
  DQ 0 violations, cube 980r (perf holds). Original tables rebuilt: planned 28,799,124 / actuals 3,775,148 /
  gold 924,987. **Equivalence at 180d EXACT: rung2 gold == sdp gold (924,987), per-org row/net-$/red diffs all
  0.** Clone thin queries at new default: 25-week rollup, SLA 2 rows, cockpit newly-red 2,236 latest week.
  (Gold starts 2026-03-09 not 03-02 because prior-week baseline needs one preceding snapshot — correct.)
- **Learned:**
  1. **A load window must be ONE knob, not N literals.** Put it in pipeline `configuration` and read via
     `spark.conf`/${...}. If a "small" change touches many files, that's a design smell — fix the root, don't
     grind through the edit. (User was right to push.)
  2. **Widen the WHOLE dependency set together.** Supporting tables (p1flow timing, chronic signal) must share
     the same window as the core fact, or the dashboard tells a self-contradictory story across pages.
  3. **"Newly-red" is boundary-sensitive** — widening the window can shift a few items between newly-red vs
     already-red at the edge; the latest-week action count stays stable (~2,240), which is what's operational.
  4. **The doc's 180d is a CEILING** ("do not load beyond"); data supports back to 2025-06-28 (14mo) if ever
     needed, but we honor the cap.
  5. `CREATE OR REPLACE` is atomic — a client-side timeout on a heavy rebuild does NOT corrupt the table (it
     keeps the old data until the new one commits). Run heavy rebuilds as background tasks; poll the table, not
     the client.

## Phase 27 — Genie Space (NL Q&A over the SDP tables), record-pinpointing
- **Ask:** "before the App, I want the Genie Agent done." + "should pinpoint to the exact/set of records the
  question is about" + "include actual-vs-planned tables/questions." Decided (via AskUserQuestion): a Genie
  SPACE (not custom agent), grounded on gold fact + key serving tables, tuned for BOTH planner & manager,
  default = always show records + total.
- **Decision & why:** Genie Space is fit-for-purpose for read-only NL Q&A now (no code, governed, fast);
  wrap in a ResponsesAgent later only when the App needs tool-calling. Grounded on 5 sdp_* tables so the
  record-level drill always exists: sdp_plan_vs_actual (the item×org×week fact — record answers),
  sdp_agg_scorecard (org KPIs), sdp_exceptions (ranked worklist + chronic flag), sdp_order_stage_gold (PO
  timing + chronic supplier), sdp_rootcause_plant (upstream tier). Reused the existing GENIE_ENABLEMENT_NOTE
  (Parts C/D reasoning rules) + GENIE_QUESTION_BANK (7 parts incl. Part 1 plan-vs-actual + Part 7 guardrails),
  retargeted from rung2_/ds_/p1flow_ to sdp_*.
- **Artifacts:** `data_understanding/workspace_assets/genie_agent.json` (5 tables, 8 sample questions, 15
  example SQLs, 1 merged text_instructions). Space "P1 Actuals — Supply Plan vs Actual (SDP)" id
  **01f1a542c3f7132681b64d8ff08b4033**. Generator `/tmp/gen_genie.py`.
- **Record-pinpoint design:** text_instructions rule "ALWAYS SHOW THE RECORDS BEHIND A NUMBER" + every
  example SQL returns item_id/item_description/organization_code/week_start ranked by $ (LIMIT 50-100).
  Plan-vs-actual leads (planned_pab vs actual_end_on_hand, planned_sales_orders vs actual_shipped,
  actual_po_received; variance abs/pct/$).
- **Evidence (Conversation API):** (1) "off-plan items this week ranked by $" → returned named SKUs w/ $
  (369229 M18 Combo −$8.8M, 369722 −$2.6M, …), correct table/week/rank. (2) GUARDRAIL "on-hand value by org"
  → Genie used week_start=MAX(week_start), did NOT sum across weeks (avoided the 5.48× trap). (3) "compare
  bias 2012 vs 2120" → both over-plan 74.0% vs 28.8%, green 39.9% vs 65.5% — EXACT match to sdp_agg_scorecard,
  framed correctly (not "inverted"). All 15 example SQLs CLI-tested return rows before creation.
- **Learned:**
  1. **Grounding for "pinpoint to records" = ground on the FACT, not only the pre-agg serving tables.**
     Aggregated tables lose the item keys; the item×org×week gold keeps them, so any total drills down. Teach
     the pattern via example SQLs that all return keys+rank — Genie generalizes it.
  2. **Guardrails as instructions + examples actually work** — the "never sum on-hand" rule survived a
     naive-phrased question ("total on-hand value by org") because both the text rule and an example modeled
     MAX(week_start). Instruction alone is weaker than instruction+example.
  3. **Reuse beats regenerate** — the enablement note + question bank (written earlier for this exact moment)
     made the build a retarget, not a fresh design. The prior "note everything for Genie" work paid off.
  4. Space JSON format gotchas (skill): 32-hex ids unique across all 3 lists; tables+example_sqls sorted;
     text_instructions must be exactly ONE merged item; text fields are arrays.

## Phase 28 — Genie ↔ Dashboard link + action chips + test evidence
- **Ask:** test Genie on anti-patterns / all scenarios / P1 requirement Qs / action Qs (cancel, alert
  planner) / "mirage data"; then attach Genie to the dashboard; then (a) capture evidence + (b) add chips.
- **Did:**
  - **Attached Genie to the SDP dashboard** via `uiSettings.genieSpace` {isEnabled, overrideId
    01f1a542c3f7132681b64d8ff08b4033, ENABLED} — "Ask Genie" button now on dashboard 01f1a537…; verified on
    the deployed dashboard (not just local JSON). Theme preserved. Legacy dashboard intentionally NOT linked
    (Space is grounded on sdp_*). Genie is linked, NOT a widget (no assistant widgetType).
  - **Added 3 action starter chips** + 2 example SQLs (cancel/defer overstock, alert-planner-by-new-$),
    CLI-tested (100 / 20 rows), pushed via `genie update-space`. Space now 11 sample Qs, 17 example SQLs.
  - **GENIE_TEST_EVIDENCE.md** — captured every validated Q&A (per-item, anti-patterns, scenarios, P1
    UC1-UC6/M1-M5, action decisions) with Genie's actual answers + verdicts.
- **Evidence highlights (all ✅, records returned):** off-plan-by-$ named SKUs (369229 −$8.8M); AP-1 refused
  cross-week on-hand sum (used MAX week); AP-5 ranked by stockout_risk_usd not unit-miss; bias 2012 74.0% vs
  2120 28.8% (exact scorecard); "cancel?" → M18 RL HO XC5 $8.4M excess + specific POs; "alert?" → Bartholf,
  Nick $1.69M; "mirage?" → correctly recalled expected_receipt_date same-day mirage + on-hand-sum +
  raw-$ org compare.
- **Learned:**
  1. **Genie attaches to an AI/BI dashboard via `uiSettings.genieSpace`, not as a widget** — one JSON block
     + redeploy. Gives an in-dashboard "Ask Genie" without leaving the page (charts for the eye, Genie for
     the follow-up).
  2. **Genie can REASON to an action recommendation (cancel this PO / alert this planner) but cannot EXECUTE
     it.** That's the clean line between Genie (what/why/who) and the App (do it) — worth stating to the team
     so expectations are right.
  3. Guardrail knowledge (the "mirage" answer) transfers through text_instructions — Genie can tell you what
     data to distrust, which is a genuinely useful data-literacy feature, not just Q&A.

## Phase 29 — P1 Actions App (roadmap step 3): built, deployed, data-loaded, verified
- **Ask:** the actionable App — see off-plan → ask why → forecast/what-if → approve → live cascade →
  audit → simulated Oracle push. Plus (user, mid-build): chat + agentic tool-calling; ai_forecast what-if
  ("what if I cancel"); capture recommended-vs-final + reason → MLflow eval dataset; creative action verbs;
  actions in Lakebase, dashboard live-refreshed, publishable to Delta; modern/interactive UI; the app must
  TEACH the business (not assume); put the dashboard + a scenarios storytelling page in the app.
- **Built:** NEW Lakebase project `mke-po-actions` (6 existing untouched); AppKit app (lakebase+analytics+
  genie+agents) deployed & RUNNING at https://mke-po-actions-4482605715640778.18.azure.databricksapps.com;
  schema `app_po` (mirrors + ONE writable action_request + audit + SIMULATED integration_outbox/result +
  decision_eval + chat + FTS/pg_trgm search); propose→approve→execute transaction (OBO, audit, sim-push);
  7-tool agent (ask_data/find_record/forecast_item/what_if/rank_actions/draft/execute, effect:'destructive'
  → HITL gate); ai_forecast what-if (VERIFIED signature: horizon=end-date, time_col=timestamp, value_col=
  double); polished cockpit (echarts forecast, semantic KPIs, what-if cards, decision capture, live flash).
  Validates clean; deployed via DAB.
- **Bugs hit & fixed (the hard part):** (1) hand-rolled SQL-Statements fetch with DATABRICKS_TOKEN — Apps
  don't inject a token; rewired to appkit.analytics.query (SP credential chain). (2) DATABRICKS_HOST had no
  https:// scheme → URL parse error; normalized. (3) app SP INSUFFICIENT_PRIVILEGES on
  sandbox_operations.po_management — catalog owned by group red-keychain-workshop; I lack MANAGE + not ws
  admin, so couldn't GRANT USE CATALOG or add SP to the group. **Resolution = the RIGHT architecture:** load
  the Lakebase mirrors from MY creds (superuser on the project I created) via psql; the app then reads ONLY
  its own app_po tables and never needs catalog access. Loaded 2,516 exceptions / 62,211 trajectory / KPI
  ($91.2M, 208 chronic, 64 planners). Hero item 48111881X M18 Forge XC8.0 Battery $3.07M.
- **Verified:** queue join returns ranked real items; simulated execute → resolved KPI math works (cascade
  sound). Core loop proven at the data layer.
- **What the user (rightly) called out & still open:** app looked empty (data now loaded — fixed); leftover
  scaffold Dashboard tab shows fake "Sales Trend/hello world" (must replace with our data); app assumes
  domain knowledge — needs self-teaching context strips + metric explainers + a scenarios storytelling page.
- **Learned:**
  1. **Databricks Apps auth: never hand-roll a token.** Use appkit.analytics.query / appkit.lakebase.query —
     they carry the SP credential chain. A raw DATABRICKS_TOKEN doesn't exist in the Apps runtime.
  2. **App SP catalog access is a governance boundary you may not control.** If the source catalog is owned
     by a group you can't manage, don't fight it — load the Lakebase OLTP mirrors from an authorized identity;
     the app reading only its own OLTP plane is the cleaner two-plane design anyway.
  3. **Deploy-first is real** — the SP must own app_po (it did: schema created, FTS+trgm caps true).
  4. **An empty app reads as broken even when the architecture is sound.** Load real data + kill scaffold
     BEFORE showing it. And an operational app must teach its domain, not assume it (user's core critique).

## Phase 30 — App polish + true-agentic explain + FTS search + full write-back, all verified on the DEPLOYED app
- **Asks (this session):** make the FrontEnd dashboards work; on click, an LLM explains everything about the
  item AND recommends order/reject/etc.; ensure Lakebase search works; confirm all Lakebase write-backs work;
  and make the app self-teaching / business-ready.
- **Dashboard (native) fixed:** the AppKit data-mode `BarChart` rendered axes but no bars with our JSON. Root
  cause: data-mode bar series didn't bind. **Fix = a deterministic CSS `Bars` component** (label · scaled bar ·
  $-formatted value) — replaces BarChart for the 3 bar cards; `PieChart` (systemic vs one-off) kept (works).
  Screenshot-verified: $ by ABC (A=$63.9M), by-planner (Rowe $9.2M → Shah $2.1M), by-$ band ($100K–1M=$46.5M),
  pie 91.6% one-off. Every card has a teaching caption. Closes "dashboards on the FrontEnd not working".
- **True-agentic explain-on-click:** new `/api/po/explain/:itemId`. Deterministic reasoning over the REAL row
  (gap, $ risk, on-hand vs floor, chronic flag, planner) is the GUARANTEED answer (source:"rules"); an LLM
  path via the AppKit `serving('llm')` plugin is tried first and gracefully falls back (runtime type-guard
  `hasServing`, not a cast — passes appkit lint's no-double-type-assertion). Output includes a narrative +
  a recommended_action (EXPEDITE / FIX_SUPPLIER / REVIEW / …) + recommended_qty + confidence + reason. The
  cockpit DetailDrawer auto-runs it on open (Sparkles panel), shows the explanation + a recommendation badge,
  and PRE-FILLS the chosen action + qty. Verified on deploy: 48111881X → "M18 Forge XC8.0 Battery, ABC A,
  50,336 u below floor, $3.07M risk, one-off, planner Rowe" → **EXPEDITE 50,336 / medium**.
  (Honest state: it's the rules engine today — the `serving` resource isn't wired into this app; the LLM path
  is ready and will engage once a serving endpoint is added + redeployed.)
- **Search: full ladder live.** On the DEPLOYED app the SP-owned `app_po` schema has the GIN full-text index,
  so `q=battery` returns **mode:"fts"** (20 ranked hits); `q=48111` uses **mode:"ilike"** (id-prefix, 12 hits).
  The FTS→trigram→ILIKE ladder degrades correctly. (Local dev instance falls to ILIKE — schema/index owned
  differently there; deploy is the source of truth.)
- **Write-back: full loop proven on deploy.** propose→execute on 48111813B: status proposed→executed,
  `approved_by` = OBO planner email, override captured (final 5,000 vs recommended 50,336 + reason), audit_trail
  = 2 events (proposed, executed) each with actor/ts/reason/tool, SIMULATED Oracle outbox+ack enqueued in one
  txn. Then `/api/po/admin/reset` restored clean demo state (resolved $0, base 2,516/$91.2M intact).
- **Deploy:** `databricks sync` → `databricks apps deploy` (SNAPSHOT) SUCCEEDED, app RUNNING. Validate clean
  (typecheck + ast-grep lint + tests). Guardrails held: prod read-only, writes only to Lakebase app_po +
  (later) sandbox_operations.po_management, Oracle SIMULATED, only the new mke-po-actions project touched.
- **Learned:**
  1. **AppKit data-mode BarChart is unreliable with dynamic JSON — a CSS bar you control always renders.**
     Pie was fine; bars weren't. When a managed component fights you, a 20-line deterministic component beats
     debugging the black box for an operational surface.
  2. **Make the deterministic answer the product, the LLM an enhancement.** The rules-based explain reasons
     over real facts and is genuinely useful; wiring the LLM is then a pure upgrade, never a dependency. Ship
     the guaranteed-correct path first, gate the model path behind graceful fallback.
  3. **The deployed app ≠ local dev for identity-scoped features.** FTS engaged on deploy (SP owns the schema
     + index) but not locally. Verify identity-dependent behavior against the deployed SP, not the dev shell.
  4. **Lint is a real gate:** `as unknown as` fails `appkit validate`. Use a runtime type guard for optional
     plugins — it's both correct and lint-clean.
- **Still open:** Phase 7 (publish executed actions Lakebase→Delta sandbox_operations.po_management.
  action_outcome_history — the NEW-18 feedback loop); optionally wire a `serving` endpoint so explain uses a
  real LLM; MLflow eval over the captured recommended-vs-final decisions.

## Phase 31 — Real LLM engine wired (both options kept: live LLM stream ⇄ deterministic rules)
- **Ask:** make the explain-on-click a TRUE LLM call (not just the rules engine), and KEEP BOTH options
  (user: "keep both options"; "live streaming outcome looks better").
- **Row-click first:** made the whole queue row clickable (violet hover) → opens the drawer; header hint
  "✨ Click any row for AI analysis + recommended action"; button relabeled Explain ▸ (stopPropagation so it
  doesn't double-fire). So a single click on any item surfaces the analysis — the requested UX.
- **Serving plugin wired:** added AppKit `serving()` plugin (alias `llm` → env DATABRICKS_SERVING_ENDPOINT_NAME)
  in server.ts; `serving-endpoint` resource (type serving_endpoint, CAN_QUERY) added to databricks.yml +
  app.yaml env; bundle deployed so the app SP has CAN_QUERY on `databricks-claude-sonnet-4-5`. Endpoint chosen
  from `serving-endpoints list` (many foundation models READY; Claude Sonnet 4.5 is the default).
- **Both engines, selectable:** `/api/po/explain/:itemId` and `/api/po/explain-stream/:itemId` now take
  `?engine=rules|llm|auto` (auto = LLM when wired, else rules). LLM path calls the real model via
  `appkit.serving('llm').invoke()`, then re-emits the answer word-by-word over SSE for the live-typing feel;
  rules path streams the deterministic text. LLM ALWAYS falls back to rules on any failure (never hard-depends).
  Drawer has an Auto/LLM/Rules toggle + Re-run; badge shows which engine produced the shown answer.
- **The prompt:** model writes 3–4 plain-English sentences, then a machine-parseable `@@REC action= qty=
  confidence= reason=` trailer (stripped from the visible stream, parsed into the recommendation). Prose-first
  streams naturally; the trailer gives structured pre-fill without JSON-in-stream fragility.
- **Verified on the DEPLOYED app (real Claude Sonnet 4.5):** engine=llm →
  "…safety stock climbing sharply over the past eight weeks (104K→194K) while actual inventory stayed flat…
  no PO receipts in the last five weeks despite ~4–5K units/week demand… imminent stockout on a critical
  battery platform…" → EXPEDITE/NEW_PO, 60–75K, high. It genuinely reasoned over the 8-week trajectory (spotted
  the SS ramp AND the zero-receipts streak) — not a template. engine=rules → deterministic one-liner, EXPEDITE
  50,336, medium. engine=auto → picks LLM. All three confirmed live via OAuth-authed curl.
- **Bug fixed:** the programmatic `serving('llm').invoke()` wraps its result in ExecutionResult `{ ok, data }` —
  reading `out.choices` directly gave empty content and silently fell back to rules. Unwrap `.data ?? out`
  first. (Also: the serving handle exposes `invoke` only, NOT `stream` — true SSE streaming is on the plugin's
  own /api/serving/:alias/stream HTTP route; server-side we invoke then re-stream. Confirmed against the
  installed AppKit types, not guessed.) Also: dev server loads `.env` (not `.env.local`) via
  --env-file-if-exists, so the endpoint env must live in `.env`.
- **Deploy:** validate clean (lint incl. no-double-type-assertion via the hasServing runtime guard; typecheck;
  tests). `bundle deploy` (one transient "failed to update app's compute size" — succeeded on retry) +
  `apps deploy`; app RUNNING with all 4 resources attached (sql-warehouse, genie-space, postgres,
  serving-endpoint). Guardrails intact.
- **Learned:**
  1. **AppKit programmatic invoke ≠ the HTTP route shape.** The HTTP `/api/serving/:alias/invoke` returns the
     raw completion; the in-process `serving().invoke()` wraps it in ExecutionResult `{ ok, data }`. Unwrap, or
     you silently get empty content. Verify the return shape from the installed .d.ts, don't assume OpenAI shape.
  2. **Keep the deterministic engine as a first-class option, not just a fallback.** Two selectable engines +
     auto gives trust (rules = reproducible, instant, auditable) AND depth (LLM = reads the trajectory, infers
     root cause). The user explicitly wanted both; it's also the safer product.
  3. **Prose + a parseable trailer beats JSON-in-stream.** Streaming raw JSON tokens looks broken mid-flight;
     prose streams beautifully and the `@@REC` trailer (held back from the visible stream) carries structure.
  4. **A row-level click is the natural "tell me everything" gesture** — gating it behind a button was the miss;
     the whole row now opens the analysis.
- **Still open:** Phase 7 (publish executed actions Lakebase→Delta action_outcome_history, NEW-18); MLflow eval
  over captured recommended-vs-final decisions; (optional) surface an in-drawer note when LLM fell back to rules.

## Phase 32 — App SP granted direct catalog access; agentic-loop unlocked (verification + analysis, no new build)
- **Context:** post-Phase-31 health check + the user reported "I just got it" (new access). No code change this
  phase — verification + architectural read-out only.
- **Health check (deployed app, OAuth-authed curl):** state RUNNING / compute ACTIVE; every endpoint 200 —
  queue, kpis, analytics/by-abc, analytics/by-planner, search(battery), forecast, explain(rules),
  scenario/chronic. App is fully working.
- **THE grant landed (resolves the Phase-29 blocker permanently):** app SP `06ae418f-5604-498d-82c9-73e413650a53`
  now has **SELECT + USE_SCHEMA directly on `sandbox_operations.po_management`** (effective shows ALL_PRIVILEGES
  inherited). Verified LIVE, not just on paper: the deployed forecast endpoint ran `ai_forecast()` over
  `sandbox_operations.po_management.sdp_plan_vs_actual` via `appkit.analytics.query` (SP chain) and returned 8
  real points (y_forecast 137,206; bounds 71,040–175,203). That query only succeeds if the SP can read the
  catalog. Catalog still owned by group `red-keychain-workshop` (ALL_PRIVILEGES) — the SP grant is additive.
- **What this unlocks (agentic-app perspective):**
  1. Tools become autonomous — the SP reads its grounding + writes outputs AS ITSELF; no human pre-load in the
     credential loop (kills the demo crutch where I hand-loaded mirrors from my superuser creds).
  2. Real closed learning loop — SP can WRITE executed decisions back to Delta (action_outcome_history), turning
     recommendation-vs-final(+reason) into an MLflow eval set; makes NEW-11 (codify planner knowledge) / NEW-18
     (feedback loop) mechanically possible. This is the capability that distinguishes an agent from a chatbot.
  3. Fresh grounding — the startup `syncFromDelta` (already coded, previously failing silently on privileges) can
     now self-sync from the live `sdp_*` tables, so the cockpit moves with the weekly SDP pipeline instead of a
     one-time snapshot.
  4. One governed identity for the whole audit chain (read fact → ai_forecast → write outcome) under UC grants +
     lineage — trustable in production, not just sandbox.
  5. Tool surface can safely expand — "publish to the analytical plane" becomes a permissioned agent verb
     (snapshot exception set, materialize decision log, emit QA evidence) inside guardrails.
- **Guardrail check:** unlock is entirely within `sandbox_operations` (the approved writable schema).
  prod_edw/prod_operations remain READ-ONLY; Oracle writeback still SIMULATED. No boundary crossed.
- **Caveat to confirm before relying on WRITES:** schema listing showed explicit `SELECT, USE_SCHEMA` but
  effective `ALL_PRIVILEGES` — slightly disagree. Before Phase 7 writes, confirm the SP can actually
  CREATE/INSERT into `sandbox_operations.po_management` (user declined to run this now).
- **Known cosmetic issue:** the Databricks Apps UI still shows a stale "Update failed 1 hour ago — Unexpectedly
  failed to update app's compute size" banner from the Phase-31 transient control-plane hiccup. The app is
  Running and the later deploy went green; a fresh clean Deploy clears the banner. Not a code bug. (User has not
  asked to clear it yet.)
- **Decisions this phase:** user explicitly declined (a) triggering a live re-sync and (b) confirming write
  capability / building Phase 7 right now. So Phase 7 + MLflow eval remain open by choice, not by blocker —
  the access that was blocking them is now in place.
- **Learned:** the governance boundary that forced the two-plane workaround (Phase 29) was never architectural —
  it was a missing grant. Once granted, the same two-plane design becomes a *choice* (OLTP write surface + OLAP
  truth) rather than a workaround, and the closed feedback loop it always implied is now buildable.

## Phase 33 — Parallel Streamlit app (functional twin of the React cockpit), independent end-to-end
- **Ask:** distill everything (the agentic-ops-app UI skill, the deployed mke-po-actions app, the whole MKE
  project), reference the Databricks Apps Streamlit cookbook + Streamlit docs, and build a PARALLEL Databricks
  App on Streamlit with the current functionality. Then (mid-build): make it independent — its own schema, its
  own ymls/deployment, its own assets end-to-end.
- **Distillation:** 3 subagents produced dense briefs — (1) the agentic-ops skill (load-bearing loop
  see→ask-why→recommend→approve→act→cascade→audit; two-plane OLTP+OLAP; one writable table; HITL gate;
  rules-first-LLM-enhancement; degrade-don't-loop), (2) the full app spec (every route SQL, the app_po schema,
  the 10 action verbs, explain @@REC prompt), (3) whole-project context (P1 scope, sdp_* spine, scenarios,
  guardrails, the anchor numbers). Cookbook confirmed the Databricks-Streamlit patterns: WorkspaceClient SP
  auth, serving_endpoints.query(ChatMessage), OBO via x-forwarded-* headers, port=${DATABRICKS_APP_PORT}.
- **Built `mke-po-actions-st/`** (Streamlit multipage): app.py + 4 pages (Cockpit, Ask-Genie, Dashboard,
  Scenarios) + lib/ (lakebase psycopg w/ OAuth-token cache+refresh; warehouse databricks-sql-connector for
  ai_forecast; serving: real Sonnet-4.5 llm_explain + deterministic rules_explain + word-stream; domain: every
  READ route ported verbatim SQL; actions: propose/execute(ONE txn)/reject + decision_eval; schema bootstrap;
  identity OBO; theme). Full parity: queue, 4 KPI tiles, FTS→trigram→ILIKE search, click-row → streaming AI
  analysis with LLM/Rules/Auto engine radio + recommendation, forecast (Plotly band), what-if, decision
  capture, approve→execute write-back (audit + SIMULATED Oracle + decision_eval), analytics (Plotly bars/pie +
  teaching captions), scenarios playbook (live), Genie NL Q&A.
- **Independence (user's explicit requirement) — end to end:** own directory, own app.yaml + databricks.yml +
  bundle (`mke-po-actions-st`), own deployed app + **own Service Principal** (`d630d5ba…` ≠ React app's
  `06ae418f…`), own URL, and own Lakebase **schema `app_po_st`**. Built app_po_st as a `LIKE app_po INCLUDING
  ALL` structural clone (carried the generated search_tsv + FTS/trigram indexes + PKs), copied the mirror data
  (2,516 / 62,211 / 1) from app_po, left the writable tables EMPTY. **Write-independence PROVEN:** an INSERT
  into app_po_st.action_request is visible only in app_po_st (n=1), never in app_po (n=0); after cleanup
  app_po_st actions=0 while the React app's app_po still holds its 2. Granted the NEW SP read+write on
  app_po_st (+ read-only on app_po mirrors for the bootstrap safety net). Shared by user's choice: the Lakebase
  project compute, SQL warehouse, Genie space, serving endpoint (foundation models are workspace-shared —
  no per-app copy exists).
- **Verified live:** every ported SQL run against real Lakebase (queue top item 48111881X $3.07M; KPIs
  2,516/$91.2M/208/64; FTS 'battery' works; by-ABC A=$63.9M; execute-transaction shape via BEGIN…ROLLBACK left
  zero rows). ai_forecast verified via CLI (8 weekly points). Deployed: bundle deploy + apps deploy →
  **App started successfully / RUNNING**, HTTP 200, Streamlit clean in logs. app_po_st serves the correct
  ranked queue as the deployed SP.
- **Bugs fixed:** (1) `.venv` swept into the deploy (881 files) → added bundle `sync.exclude` + .gitignore,
  redeployed lean (25 files). (2) First app boot CRASHED: `--server.port ${DATABRICKS_APP_PORT:-8000}` was
  passed literally (Apps command list isn't shell-expanded) → wrapped the command in `bash -c` so the env var
  expands. Deps + build had succeeded; only the start command was wrong.
- **Learned:**
  1. **Streamlit on Databricks Apps needs a shell for env expansion.** A command *array* is exec'd directly, so
     `${DATABRICKS_APP_PORT}` never expands — wrap in `bash -c "streamlit run … --server.port ${…}"`. (The #1
     Streamlit-on-Apps gotcha, distinct from the React/Node path.)
  2. **`CREATE TABLE … LIKE src INCLUDING ALL` is the cleanest way to fork a Lakebase schema** — it clones
     columns, generated tsvector, indexes, and PKs in one step; then copy data (enumerate columns to skip the
     GENERATED search_tsv). An independent schema + a distinct app SP is what actually decouples two apps.
  3. **A parallel app is a portability proof.** The exact same SQL, guardrails, action verbs, rules/LLM engine,
     and write-transaction reproduce faithfully in Python/Streamlit — the *architecture* (two-plane, one
     writable table, HITL, rules-first) is framework-independent; only the UI idioms and the port/serving glue
     differ. st.dataframe row-select = the React "click"; st.write_stream = the SSE token stream.
  4. **Exclude the venv from bundle sync from the start** — otherwise the first deploy uploads thousands of
     dependency files. `sync.exclude` in databricks.yml is the fix.
- **Two apps now run side-by-side on the same data spine, fully independent:**
  React `mke-po-actions` (app_po) + Streamlit `mke-po-actions-st` (app_po_st).
- **Still open (unchanged):** Phase 7 (Lakebase→Delta action_outcome_history), MLflow eval. Not part of this
  parallel-UI pass.

## Phase 34 — Authored the `databricks-streamlit-apps` skill (build-from-scratch fastpath)
- **Ask:** create a detailed skill so another agent can build a Streamlit app on Databricks Apps from
  scratch — "that's how evolution works." Distilled from the real Phase-33 build.
- **Built** `.claude/skills/databricks-streamlit-apps/` (same shape as lakeview-dashboard-fastpath): a
  SKILL.md (iron rules + 8-step build loop + reference routing) + 7 references + 11 template files (a
  complete, syntax-checked minimal app).
  - **references/**: architecture (data-plane decision gate + two-plane OLTP/OLAP pattern),
    project-structure (lib/pages split), lakebase-connectivity (OAuth-token psycopg cache/refresh, Tx,
    FTS ladder, LIKE-INCLUDING-ALL schema fork + SP grants, psql verification), integrations (warehouse
    SQL + ai_forecast, serving LLM, invoke-then-restream streaming, Genie poll, OBO headers, discovery
    cheat-sheet), ui-patterns (KPIs, dataframe-selection-as-click, st.dialog drawer, streaming+engine
    toggle, Plotly charts, live cascade via st.rerun, required states), deploy (app.yaml+databricks.yml,
    the shell-wrap rule, sync.exclude, deploy sequence, live verification), symptom-fix (the register —
    ~18 symptom→cause→fix rows, every one hit or avoided on the real build).
  - **templates/**: app.yaml (bash -c wrapped), databricks.yml (sync.exclude + 4 resource blocks),
    requirements.txt, .gitignore, app.py, lib/{config,lakebase,warehouse,serving,identity}.py,
    pages/1_Example.py (the full see→explain→act loop). All Python parses clean.
- **The load-bearing lessons encoded (so the next agent skips the pain):** (1) shell-wrap the start
  command or `${DATABRICKS_APP_PORT}` is passed literally and the app crashes; (2) bind 0.0.0.0 + the
  injected port; (3) Lakebase password = a refreshing OAuth token, not a secret; (4) declare every
  resource with a permission so the SP is auto-granted; (5) sync.exclude the venv from deploy #1;
  (6) deploy-first (or explicit GRANT) for Lakebase writes; (7) rules-first, LLM-as-enhancement;
  (8) st.rerun IS the live cascade; (9) LIKE…INCLUDING ALL to fork a schema independently.
- **Verified:** all 11 templates syntax-check; SKILL.md frontmatter valid (name + single description);
  skill auto-registered (appeared in the available-skills list). Complements databricks-core / -apps /
  -lakebase / -genie-agents rather than duplicating them.
- **Learned:** a skill authored straight from a just-shipped build is the highest-fidelity kind — the
  symptom→fix register is literally the turn-by-turn debugging of Phase 33, so the next agent inherits
  the scar tissue, not just the happy path. Evolution: each build hardens the skill that makes the next
  one one clean pass.

## Phase 35 — Hardened the Streamlit skill from the live-bug fixes (evolution loop)
- Three real bugs from running mke-po-actions-st were fed back into `databricks-streamlit-apps`:
  1. **Lakebase token-mint call.** SDK `w.database.generate_database_credential(instance_names=[endpoint])`
     is the legacy Provisioned API → 404 "Database instance … not found" on every page. Correct call is
     the Autoscaling REST `POST /api/2.0/postgres/credentials` body `{"endpoint": "<path>"}` (verified via
     `--debug`). Fixed the live app's lib/lakebase.py + the skill template + SKILL rule 4 + symptom-fix row.
  2. **New app = new SP = its own UC grants.** The Streamlit app's SP (d630d5ba…) ≠ the React app's
     (06ae418f…, granted in Phase 32); it hit PERMISSION_DENIED on sandbox_operations.sdp_* for Genie +
     forecast. Resource-permission auto-grant covers the warehouse/serving/lakebase/genie RESOURCE but NOT
     UC SELECT/USE on the tables. I lack MANAGE on the catalog → owner must grant. Encoded: SKILL rule 5,
     deploy.md "TWO kinds of grants", symptom-fix row, and the design rule to degrade catalog-dependent
     features gracefully.
  3. **st.dataframe has no whole-row click.** Row-select fires only on the left checkbox; a cell click
     does nothing → the detail dialog never opened (user caught it). Fix = explicit selectbox + "Analyze ▸"
     button opens the @st.dialog, checkbox kept as bonus. Encoded: SKILL rule 7, ui-patterns rewrite,
     symptom-fix row, and the template page now ships the picker+button by default.
- Also fixed the live app for #1 (deployed, RUNNING, mirror-backed pages recovered) and #3 (deployed).
  #2 remains pending a catalog owner's GRANT (forecast/Genie degrade gracefully meanwhile; Cockpit queue,
  KPIs, search, LLM-explain, write-back all work).
- **Learned:** the tightest evolution loop is fix-live-then-write-the-skill in the same pass — every fix
  became a rule + a symptom-fix row + a corrected template line, so the next agent never rediscovers it.

---

## 2026-09-01 — P3 Demand Events App: design → live data profile → AppKit build

**Ask (user's words):** "build the app for this [demand requirement]… bulk edit from the app directly to
Lakebase… development needs to be modularized… convert all requirements into a detailed technical document…
what data we need… explore the data by going to the source… find a hero item… the app should do writes to
lakebase, create a new lakebase project if required… include bulk insert/update… start to build the app."
React (AppKit) confirmed; reference: github.com/databricks/appkit.

**Decisions:**
- **Modular, not shared with supply (P1/P2):** own repo/app (`mke-demand-events`), own Lakebase project
  (`projects/mke-demand-events`, separate from supply's `mke-po-actions`), own Delta namespace
  (`sandbox_operations.po_management.demand_events_*`), own domain services. Shared = operating pattern +
  transactional/bulk patterns only.
- **STRICT write boundary (user-hardened):** all outputs → `sandbox_operations.po_management` only.
  `prod_edw` (incl. `staging_flat_files.expansion_*`) is READ-ONLY **source** (schema ref + seed existing
  events to adjust). Oracle-inbound hop is the DW team's job, reads our sandbox output; never app→prod.
- **Stack = AppKit** (analytics plugin reads prod_edw; lakebase plugin writes transactional state). No
  hand-rolled FastAPI BFF.

**Live data profile (profile mke-rsc, wh 7bd33a82f4e92206) — all 6 requirement tables:**
- expansion_loads 8.09M rows / 1,462 events / 53 customers; **negatives real** (6,883, min −8,640);
  ~88% zero (store sparse); **`variable` mixed ISO + Excel-serial** (8,137 rows) → normalize-on-read;
  **event = multi-tranche** (file_index); existing events single-customer (confirms the pain).
- **items_scd1 finding:** `item_status='PurchPlan'` (requirements' rule) flags **100% of a real event**
  (EXP001442 = 22 ShipSO/2 DiscExtrnl/0 PurchPlan). → validation kept non-blocking + rule-versioned;
  criterion to reconfirm with analytics eng (top open risk).
- Confirmed: planner_baseline (not …_forecast), organization_code (not org_code), 2012 Olive Branch/2120
  Mexico, dg5 6-level hierarchy, dash-normalize item join (100% match).
- **Hero item: `3697-22` = item_id 369722 (M18 FUEL 2PC COMBO KIT)** — named by planner in the call ("20%
  lift on 3697"), 156 events/43 customers, present in 10_demand_daily.

**Artifacts:** `demand_events_app/TECHNICAL_DESIGN.md`, `DATA_PROFILE.md`, `HERO_ITEM.md`, `BUILD_NOTES.md`;
app at `demand_events_app/mke-demand-events/` (AppKit). Backend: full `demand_events` Lakebase schema +
routes (event CRUD, lock, disaggregation, **bulk-edit stage→one set-based apply, idempotent+audited**,
publish+ack). Reads: 3 typed SQL queries. Frontend: Events + Bulk Edit pages.

**Evidence:** `databricks apps validate` **PASSES** (typegen, ast-grep lint, typecheck, build, tests). Lakebase
project created & branch/db/endpoint verified. **Not yet deployed** → next gate is deploy-first (SP owns
`demand_events` schema), then real smoke test on hero 3697-22. Status = implemented+build-validated, not UAT.

**Follow-ups:** deploy; publication Delta-MERGE Job; seed/normalize existing expansion_* events; reconfirm
item-validation criterion.

### 2026-09-01 (cont.) — P3 Demand Events App DEPLOYED + smoke-tested

**Ask:** "create new lakebase project and new app, nothing to do with the others… start to build… deploy…
got the permissions, continue."

**Outcome:** app **DEPLOYED & RUNNING** at
https://mke-demand-events-4482605715640778.18.azure.databricksapps.com (all-new assets: Lakebase project
`projects/mke-demand-events`, schema `demand_events` owned by app SP, no coupling to supply). Startup log:
`schema 'demand_events' ready`.

**Deploy blocker (attempt 1 FAILED → fixed):** app SP `2c32a222-5c61-41c7-8a51-9e3578962074` lacked read on
`prod_edw`. The workspace build runs `appkit generate-types` (typegen) **as the SP**; it failed
INSUFFICIENT_PERMISSIONS and failed the whole deploy. Local `databricks apps validate` had PASSED because it
runs as the dev identity — so validate is NOT a deploy predictor when the app reads a catalog the SP can't.
Customer added the SP to the `prod_edw` reader group → attempt 2 succeeded.

**Live smoke test (hero 3697-22, real planner_baseline):** create → multi-customer (HD+CONST_IND+FERGUSON)
→ disaggregate 10k units by real ratios (9888/70/42) → bulk activate (idempotent replay confirmed) → bulk
20% lift (9930→11916, ×1.2, = the call's "3697 lift") → bulk-close customer (the "plumbing" case) → publish
+ acknowledgement (run_id, 1 event/3 rows, SUCCEEDED) → audit trail with actor+timestamp. All ✓.

**2 bugs the smoke test caught that local validate could NOT:**
1. bulk `changed` count used `r.rows.length` (0 for UPDATE) → `r.rowCount`.
2. `APPLY_LIFT` crashed `invalid input syntax for type integer: "0.2"` (Postgres inferred int from
   `ROUND(value*(1+$1))`) → cast `$1::numeric`.
Fixed, redeployed, re-verified live.

**Reinforced lesson:** deploy + drive the real endpoints is the test loop, not `apps validate`. Validate is
build-correctness under the dev identity; it does not exercise the SP's grants or runtime SQL param typing.

**Status:** deployed + self-serve smoke-tested; NOT yet planner-UAT'd. Follow-ups: planner UAT; publication
Delta-MERGE Job into sandbox_operations.po_management; seed existing expansion_* events; reconfirm
item-validation criterion (PurchPlan flags valid ShipSO events).

### 2026-09-02 — Supply Day-3 transcript → requirements → source-data mapping

**Ask:** (1) read every segment of `supply_day3_discussion.md` (Day-3 supply-planning breakout transcript),
list ALL requirements without losing context, in a clearer new doc. (2) Then, for each requirement, find the
right source table in the mke-rsc workspace, list which requirements had NO table, go beyond the known table
list if needed, doing it **one activity at a time via sub-agents**, into a new doc.

**Deliverable 1 — `supply_day3_requirements.md`** (rewritten with heavy formatting on request): full capture of
the Day-3 session in 10 parts (A program framing / B concept demoed / C as-is triage / D domain defs /
E requirements R1–R27+N1–N4 / F Pareto / G data sources / H today's decision / I open questions / J glossary).
Core: planners answer "how did we get here?" ~once/day, checking **5–7 systems, up to ~2h/case**. Day-3 scope =
**explain the past, not predict**. Demand first (~60% of issues). Waterfall North Star = **projected safety
stock at lead time vs current projected gap**. Ambiguities flagged, not guessed ("Unicode"=config tool,
"50 battery", FPL team).

**Deliverable 2 — `supply_day3_data_mapping.md`** (9 activities, one sub-agent each, all READ-ONLY on mke-rsc,
warehouse 7bd33a82f4e92206). **6 ✅ Found · 2 🟡 Partial · 1 ❌ Not found:**
- **A1 top-missing-items** ✅ `20_supply_daily` (miss/low-point DERIVED from `projected_available_balance`; weekly Monday `date_key`, daily `process_date`).
- **A2 demand surprise/consumption/type** ✅ `10_demand_daily` (forecast) + `sales_order_line_transactions`/`inventory_days_on_hand` (actual); DG5 native (`dg5_customer_bigint_key`, 56 mkedg5).
- **A3 priors/late 1–6** ✅ EDW-native from `10_demand_daily` two axes (`date_key`=period × `process_date`=vintage, 371 snaps). **Answered Part I Q3 (priors NOT analytics-only) & Q6 (promo/base ARE columns: planner_promo/promo_total + planner_baseline/baseline_statistical_forecast) — upgraded A2's type-of-demand caveat to ✅.** Table has **254 columns**.
- **A4 safety stock at lead time** ✅ derivable now: `20_supply_daily.safety_stock` + `dim_series_ext_vw.complete_lead_time`; gap = ss − PAB at lead-time week. ⚠️ 22 SS Stat/DOC plans in dimension but **0 rows in fact**; **Sarah's reconstruction (R26) NOT a live table** (verified `sara_grether` holds only a 4-row planning stub, not SS data).
- **A5 PO delay** ✅ `purchase_orders` (requested/promised/original dates) + `purchase_order_change_orders`. **Overturned transcript assumption:** `change_order_originator_type` DOES record BUYER/SUPPLIER/REQUESTER/SYSTEM (planner-vs-supplier IS capturable).
- **A6 holds/adjustments/quality** ✅ `inventory_material_transaction` (adjustments), **new** `sales_fulfillment_hold_transactions`+`hold_codes_vl` (holds), `receiving_receipt_transactions` (quality). Gap: no available-vs-on-hold split on the balance table (reconstruct via join).
- **A7 network/org rollup** ✅ **Overturned transcript assumption** ("no place to roll up across orgs"): native `designated_org_code` pools Olive Branch cluster (1080+2012+2014), already denormalized into `20_supply_daily`; `transfer_orders` (14,772 1080→2014); in-transit/WIP cost columns for stranded. R5 = GROUP BY, not a build.
- **A8 supplier plans + PO-status file** ❌ confirmed external (Excel/SharePoint, not ingested). Closest EDW substitute = A5 tables. R27 = future SharePoint→Delta ingestion.
- **A9 action log + escalation email** 🟡 write targets: Lakebase App schema BUILT (`action_request`/`decision_eval`/`action_audit_event` → R19/R24; R20 fields exist) but **Delta publication Job + `action_outcome_history` + `escalation_email_output` + email template NOT built** (R23/R18).

**Process notes / lessons:**
- Sub-agents caused two false alarms: one agent called `list_available_workspaces` (looked like reaching to
  the wrong workspace); another wrongly reported `sara_grether` as "empty." **Lesson: bake the exact verified
  connection (host + warehouse 7bd33a82f4e92206 + "never enumerate other workspaces") into every sub-agent
  prompt, and spot-verify a sub-agent's negative claims directly** (I re-queried `sara_grether` myself → it
  had a table, just not a useful one). Saved verified connection detail to memory ([[databricks-v2-mcp-connection]]).
- Anchored every search on `data_understanding/00_table_priority_map.md` so agents extended prior discovery
  rather than re-doing it. Went beyond the anchor list where the requirement demanded (found the hold/transfer
  tables, `dim_safety_stock` lead).

**Follow-ups (open actions surfaced):** get Sarah's real safety-stock reconstruction location (R26; candidate
`prod_operations.supply_staging.dim_safety_stock`); confirm 22 SS plan activation for stat-vs-DOC split; build
Lakebase→Delta publication Job + `action_outcome_history` + `escalation_email_output`; wire Forecast Genie to
supply (R25); get demand table/source names from Bill's team (the today-blocker from the session).

### 2026-09-02 (cont.) — Day-3 workbench: design → capability → gaps → ADR → joins → scenarios → foldering

All artifacts collected into a new folder **`supply_day3_rootcause_workbench/`** (11 docs + README index).
This entry captures the full arc *after* the requirements+mapping above — what was built and **why**.

**Framing.** The Day-3 planners described one workflow: *"we're short — how did we get here?"* — 5–7 systems,
~2h/case, tribal triage (demand → supply → holds), ending in a two-bullet escalation email. Everything below
turns that into a validated, buildable product **and** tests whether the data can do more than the room asked.

**3 — Capability map (`supply_day3_capability_map.md`).** *Why:* a visual isn't a feature, it's a capability
grant — so I asked, per screen, "what can the planner now DO?" Placed each on the loop (Detect→Explain→Decide→
Act→Prove→Learn) and a maturity ladder (L0 React → L5 Self-improve). *Finding:* the design lands a clean **L0→L1
(React→Explain)** leap — correct for Day-3 scope — but the business already lives at **L2 Anticipate / L3
Decide**. Named **10 gaps** (forward risk, prescription, simulator, cross-SKU patterns, chronic-vs-acute,
gap-decomposition, demand handoff, supplier signal, alerts, confidence+stakes).

**4 — Gap→tables (`supply_day3_gap_tables.md`).** *Why:* a gap only matters if it's sourceable. Mapped each of
the 10 gaps to workspace tables, live on mke-rsc, one at a time. *Result:* **7 ✅ ready / 3 🟡 / 0 ❌** — every
gap has a source; the 🟡s need build (workflow object / Job / R27 ingestion), not missing data. Proved two live:
forward-risk (~110 fwd weeks w/ PAB+SS per SKU) and gap-decomposition (SS target moved 68→420 same target week).
**Surfaced new tables** beyond the 9-activity set: `demand.fact_sop_commitment` (committed $ = stakes),
`sales.ops_scorecard_fill_rate_vw` (supplier OTIF), work-center/`domain_work_order` (make-capacity), MOQ family
in `dim_series_ext_vw`.

**5–7 — UX design v1/v2/v3.**
- **v1 (`supply_day3_ux_design.md`)** — the shortage workbench: Watchlist → Waterfall(+triage) → driver drills
  (demand/supply/holds) → Escalation → Action log → **Value & Impact page**. *Why the Value page:* Day-1
  success-factor #4 was "quantify the savings"; it measures the tool's own ROI (time saved, $ protected) from
  its own telemetry, honestly staged on the impact ladder (proposed→verified→realized). Design grounded in the
  `databricks-app-design` skill (genre→IBCS notation→AppKit primitives→required states) + the project's
  action-not-state / control-tower domain pattern.
- **v2 (`..._v2.md`)** — once gaps were sourced, upgraded the UI from *explain (L1)* to *anticipate+decide
  (L2/L3)*: Coming-Risk tab, Patterns, Chronic badge, two-tone gap band, Scenario Studio, Recommended-Action
  panel, Alerts. *Why separate doc:* v1 was the honest as-scoped design; v2 is the "now that data is confirmed"
  expansion — keeping them distinct preserves the reasoning.
- **v3 (`..._v3_scenarios.md`)** — six scenario lenses (below) turned into screens; reframes the product from a
  shortage tool to a **control tower / nervous system**.

**8 — Architecture ADR (`supply_day3_data_architecture_adr.md`).** *Why:* before any UI, the user asked "build
on raw tables, or a new datamodel, or UI-first?" *Decision:* **Option C — a thin, slice-scoped Gold serving
layer in `sandbox_operations.po_management`, Lakebase for state, weekly Job on the Monday snapshot, hybrid
live-drill for single-SKU columns.** Reasoning: "faster UI" is an *analytical-serving* problem (not
transactional — Lakebase already owns writes); raw `prod_edw` (13.4B/17.8B rows) dies at the aggregate screens
and drifts semantically; a big upfront model overengineers against still-moving requirements and is the wrong
*shape* (OLTP) for reads. C reuses the proven `p1slice_*`/`sdp_*` pattern. Sequenced **slice-first** (hero SKUs
→ widen after UAT → industrialize v2). Named the throwaway-demo exception.

**9 — Joins + ER (`supply_day3_joins_er_diagram.md`).** *Why:* the user asked exactly how tables join and "on
what basis." Verified **every join key live** via `information_schema`. *Key facts:* one **conformed star** —
item/org/customer/series/date/plan; **two naming gotchas** (plan facts use `product_bigint_key`, txn facts
`item_bigint_key`; sales uses `fulfillment_organization_bigint_key`); **`series_bigint_key` is the hidden hub**
carrying supplier/lead-time/MOQ/cost; **snapshot vintage (`process_date`) pinned for "now", self-joined for
"what changed"**. ~18 source tables → 5 pre-joined serving tables (UI reads 1–2 small queries/screen). Includes
grain-reconciliation rules, 10 join hazards, copy-ready SQL, and §9 mapping industry research (control towers /
FVA / MEIO / OTIF) to specific joins.

**10 — Data-discovered scenarios (`supply_day3_data_scenarios.md`).** *Why:* the user's instinct — "the planners
told a minor story; the data can tell more." Probed the confirmed tables live, one scenario at a time.
**All 6 confirmed with real numbers:**
1. **Excess/overstock — ~$452M, 3.2× more prevalent than shortage** (we were about to build for the smaller
   problem; new finance audience, same tables).
2. **Cross-org rebalance — 1,646** item×network cases short-here/excess-there → transfer beats buy (highest ROI).
3. **Plan nervousness — 2,668** nervous series but ~3% avg swing (concentrated, not systemic → targeted watch).
4. **Supplier slip — top 4 suppliers = ~78%** of self-initiated PO changes (clean Pareto → targeted QBRs).
5. **Forecast bias — customers chronically +60–190%** vs late-3 (structural under-forecast *causes* shortages).
6. **Stranded inventory — $127.5M** on-hand in mfg org 1080, not at a DC.

**Bonus data-mapping correction (from scenario probing):** demand plans are **product-line-split** —
`10_demand_daily.plan_name` ∈ {`10 TOL`,`10 PRT`,`10 ACC`,`10 HND`,`10 QP`}, **not** the supply plans' `20
Global`/`20 Mexico` (filtering a `20 *` name on the demand fact returns 0 rows). **Folded into** the data
mapping (Activity 2 callout), the join model (backbone row + Hazard 10 + corrected consumption SQL), and the
requirements doc.

**Folded scenarios back into scope:** added **Part K — Data-Discovered Requirements (DK-1…DK-6)** to
`supply_day3_requirements.md`, explicitly flagged as *data-sourced candidates* (needs business validation),
distinct from the planner-stated Parts A–J.

**Two transcript assumptions overturned by data (worth repeating to the room):** (a) planners said there's *no
place* to roll an item across orgs → `designated_org_code` does exactly that, denormalized into
`20_supply_daily`; (b) they assumed the EDW can't tell planner-vs-supplier PO changes →
`change_order_originator_type` records BUYER/SUPPLIER/REQUESTER/SYSTEM.

**Recommendation captured across docs:** ship the **shortage hero path (v1) first** (felt pain, earns trust),
then the **cheapest two scenario lenses — S2 Rebalance + S1 Excess** (pure reuse of `20_supply_daily` + org
rollup) which reframe the product to a control tower and open the finance audience. Build via the ADR's thin
serving layer, slice-first, session timers wired from commit #1.

**Status:** design + data-validation complete; **nothing built yet** (no serving table, no app). Definition of
done remains UAT-passed, not designed. **Next:** confirm build intent (planner product vs one-session demo) →
Wave 0 slice (`rc_serving_sku_week` for hero SKUs + hero demand path).

**Method note:** all probing READ-ONLY on `mke-rsc` / warehouse `7bd33a82f4e92206`; figures are live and
illustrative of magnitude, not audited. No `prod_edw`/`prod_operations` writes.

### 2026-09-02 (cont.) — Formulae verification, transcript re-read (DK-7–12), full data validation (V1–V12), convergence & do-nothing

Continuation of the Day-3 workbench arc. All work landed in **`supply_day3_rootcause_workbench/`** (now 14 design
docs + README) and a new **`supply_day3_rootcause_workbench/validation/`** subfolder (README + V1–V12). All
probing READ-ONLY on `mke-rsc` / warehouse `7bd33a82f4e92206`.

**A. Foldering + README.** Moved all `supply_day3_*.md` into `supply_day3_rootcause_workbench/` with a README
index (read-order + provenance tiers). *Why:* keep the growing doc set navigable and self-describing.

**B. Measures & formulae (`supply_day3_measures_and_formulae.md`).** *Ask:* "for each measure, what formula and
why — and can you get it right?" Reverse-engineered formulae from stored data rather than assuming. **Keystone
proven: `PAB[t] = PAB[t−1] + total_supply[t] − total_demand[t]`** reproduced to the decimal (later stress-tested
in V2: **0 breaks / 286,935 transitions**). `total_demand = independent + dependent` exact. Graded every measure
✅ verified / 🟡 inferred / 🔴 blocked. *Statistical section:* MKE's Oracle engine carries MAD/MAPE/bias/model
columns but they are **EMPTY** in the readable EDW → read their stored `safety_stock`, don't recompute; anchored
the canonical `SS = z·σ_LT` to the **ASCM/APICS** standard via one trustworthy web search. **Trap avoided:**
`service_level` is a **category code (TOL/BAT/…), not a %** — would have produced confidently-wrong SS numbers.
*Also:* "show everything with distinctions" provenance system (✅/🟡/🔴 badges, data-driven, upgradeable in place).

**C. Databricks AI functions (`supply_day3_ai_functions_opportunities.md`).** Live-tested on mke-rsc: `ai_gen` ✅
(drafted an escalation), `ai_classify` ✅ (bucketed free-text → "supplier constraint"), `ai_forecast` present.
Framed **with-AI vs without-AI** for each — product fully works WITHOUT AI; AI removes friction (#2 escalation
prose, #3 classify) or unblocks unstructured input (#1 `ai_parse_document` for the supplier Excel/SharePoint —
the one ❌). Rule: **AI wraps the deterministic core, never computes a measure.**

**D. Transcript re-read → DK-7…DK-12** (all live-verified, stored in requirements Part K first, then propagated):
- **DK-7** `prod_operations.demand.fact_forecast_accuracy` — MKE's **governed** forecast-accuracy fact with
  **planner_bias vs system_bias** split. We were about to compute bias empirically; they already have it.
- **DK-8** `dim_forecast_accuracy_reason_codes` — governed **12-reason taxonomy** (reference list, NOT a join —
  no FK); the `ai_classify` target. Make-side: `work_order_root_cause_scd1`.
- **DK-9** forward transfer-to-cover: **7,508** forward crossings coverable by in-network transfer (4.6× the
  near-term 1,646); dense lanes (2012↔2013 65k/34k, 1080→2012/2014).
- **DK-10** lag flexibility: only **lag-1 & lag-3** exist as columns → lag-1..6 needs the `process_date`
  self-join, not pre-built columns.
- **DK-11** count-integrity: on-hand `in_transit/wip/not_put_away` cost cols are **EMPTY**; in-transit derives
  from **`transfer_orders` Open status** (240k open) instead.
- **DK-12** SS-refresh trap: quantified — of 65,186 series, 850 had SS+demand rise together; on those demand
  ~+220% while SS target ~+17.6%. Real but concentrated (~1.3%).
Propagated across join/ER (new facts, join keys verified, hazards #11–14), measures, UX v2/v3, data mapping,
gap-tables. Join keys verified live first — caught that reason-codes is a reference list (no FK), not a dimension.

**E. Full data validation (`validation/`, V1–V12).** *Ask:* "sit at the UI, exercise each feature/measure/
scenario with ≥10 real items, across orgs and time, and record what works vs breaks — with story, root causes,
recommendations & actions, and logged queries." Each file carries all of those. **Tally: 5 ✅ · 5 🟡 · 2 🔴.**
- **V1 Watchlist** 🟡 — ranks sensibly (hero 3697-22 #1, $6.98M) but "gap ≠ stockout" (below-SS-target vs
  negative-PAB must split); org 8000 outlier; correlated-subquery gotcha.
- **V2 Waterfall** ✅ — PAB recursion **0 breaks / 286,935**; gap decomposition (target-move vs position) works.
- **V3 Demand/consumption/priors** 🟡 — all 10 customers chronically under-forecast; **"demand surprise" is
  genuinely ambiguous** (ratio vs signed-error → 153% vs +53%); promo empty on accessories; **priors needs
  month-aggregation, not single `date_key`** (else blank).
- **V4 PO slip** 🟡 — requested→promised works; **two DQ traps: date-key subtraction ≠ days (use DATEDIFF);
  sentinel dates 2000-01-01/2100-12-31 pollute orig-promise** → use requested→promised.
- **V5 Holds/adj/quality** 🟡 — adjustments ✅ rich (reason-coded, ±40M); quality ✅ tiny (154 rejects);
  **holds 🔴: 2.4B-row snapshot, `release IS NULL` gives a false "0 holds"** → latest-snapshot+sentinel logic.
- **V6 Rollup/rebalance** ✅ — per-org misleads (48228902WM: −245k@2013 vs +680k@2012); **coverage mostly
  PARTIAL (9/10)** → show coverable %, "transfer-first-then-buy."
- **V7 Excess** 🟡 — real multi-year-cover SKUs ($4.5M/237wk); **switch trigger ×SS → weeks-of-cover** (×SS
  over-flags fast movers).
- **V8 Forecast bias (governed)** ✅ — planner-vs-system split is a genuine new capability (HDW FLD/ACE: the
  **planner override adds error** — the FVA insight).
- **V9 Forward risk** ✅ — crossings + lead-time flag (top crossings all inside lead time → can't order-fix);
  V9→V6 chain distinguishes transfer-able vs escalate (345020 = no in-network coverage).
- **V10 Nervousness/chronic** ✅ — chronic detection works (SKUs below SS 55/55 snapshots); acute/chronic/nervous
  are 3 distinct temporal classes.
- **V11 Convergence** 🔴 GAP — **52% of shortage SKUs have all 3 causes at once; 1 supplier (Techtronic) behind
  3,035 SKUs; 6,933 crossing one week.** Single-cause triage misses all of it. Added an **action model** (Type 1
  stacked-mitigation + residual-gap tracker; Type 2 constraint-once + capacity allocation, planner→sourcing;
  Type 3 capacity-triage the wave). Codified **DK-13**; UX **S7 convergence lens** (residual-gap tracker,
  constraint-first pivot, risk-wave view, convergence score); join-doc hazard #14 (supplier-name variants
  TTI LIMITED/LTD/LMTD must be normalized).
- **V12 Do-nothing** 🔴 GAP — **only 34% of below-SS flags ever stock out; 66% are the cushion doing its job.**
  Added a **three-way verdict ACT / WATCH / DISMISS** ("do nothing, but be aware" = WATCH: deferred + remembered,
  auto-escalate if it worsens). Codified **DK-14**; UX badge on the watchlist; Value-page "actions suppressed /
  false-alarm-avoided $" metric.

**Cross-cutting lessons from validation:**
- The **math is bulletproof** (PAB 0/287k) but **raw columns lie in repeatable ways** — 6 traps caught that
  would have shipped wrong numbers (date-key subtraction, sentinel dates, holds snapshot, empty in-transit cols,
  ×SS excess, priors single-week). **The validation IS the serving-layer correctness spec.**
- **Severity/temporal/action class matters more than the rank** — "below SS target" ≠ "hard stockout";
  acute≠chronic≠nervous; ACT≠WATCH≠DISMISS. Same shortage number → different (or no) action by class.
- **V11 and V12 are opposite failure modes of the same single-cause design** (under-serves multi-cause;
  over-flags false alarms). Fixing both turns a 10,700-row alarm into a ~3,600-row real worklist grouped by root.
- Recurring **governance concern**: component/bulk orgs (8000, 2092) & huge-UoM SKUs dominate $-rankings —
  segregate from finished-goods DCs before any dollar comparison.

**New open actions surfaced:** pin ONE governed "demand surprise" definition (V3); normalize supplier names
(V11/DK-13b); confirm DISMISS tolerance band (V12/DK-14); confirm $-at-risk cost basis (std vs landed);
segregate component orgs. **Status:** design + validation exhaustive; **still nothing built** — Wave 0 slice
remains the next step, now with the validation as its correctness checklist.

### 2026-09-03 — Recoverability / S&OE (V13, DK-15) + the classifier-layer propagation

**Ask:** "every week there's a 'fire' we recover, and battles we lose no matter what — what's the supply-chain
definition, does it exist in the data, and where does full root-cause analysis belong ('living on the edge')?"
Then: fold the finding into every project file, with **proper data investigation where needed**.

**The vocabulary (answered):** the recoverable weekly fire = an **S&OE (Sales & Operations Execution)** exception
you *expedite*; the lost battle = an **unrecoverable / committed stockout** — the breach is **inside the
lead-time fence** (past the "last responsible moment"); living-on-the-edge = **hand-to-mouth / chronic-critical,
zero-buffer** SKUs. Organizing concept: the **lead-time fence** (S&OP = tactical planning layer; S&OE = the
0–13wk execution layer where this lives).

**Data investigation (live, `20 Global`, next qtr):**
- **Recoverable vs unrecoverable:** of 10,908 flagged crossings, **98% (10,729) are UNRECOVERABLE** (breach
  inside the per-SKU lead-time fence) vs 179 recoverable. With $ + lead attached: **$372.5M unrecoverable (median
  lead 130d) vs $3.7M recoverable (7d)** — recoverability tracks lead time exactly; virtually all dollar exposure
  is in committed losses.
- **Why 98%:** lead time is **BIMODAL — median 2 days but average 122 days** (99,678 series >8wk). The long-lead
  tail *is* the flagged population, because a long lead time is what makes a breach unrecoverable. **⚠️ never use
  an average lead time — always per-SKU `complete_lead_time`** (logged as a hard rule).
- **Damage-control path split:** of 9,310 short item×networks, **1,845 (20%) have in-network excess → TRANSFER**
  (respects no supplier lead time); **7,465 (80%) no excess → ALLOCATE / notify / accept + log**. So
  "unrecoverable" is not monolithic.
- **Living-on-the-edge:** **2,307 SKUs below SS every week** of the horizon (chronic zero-buffer); 3,712 hit
  actual zero.

**Where full RCA belongs (a deliberate inversion):** *not* every fire. Recoverable near-term → fast triage;
**unrecoverable-and-material → FULL RCA** (too late to fix this one → learn *why it became unrecoverable* to
prevent the next); **chronic zero-buffer → systemic RCA** (output = policy change, not expedite); cushion-dip
(DK-14 DISMISS) → no RCA. Deepest analysis goes on the problems you *can't* fix this week — the "lost battles"
and "living on the edge."

**Filed:** `validation/V13_recoverable_vs_lost_edge.md` (with $, damage-control split, lead-time distribution,
all queries logged); codified as **DK-15** in requirements Part K. Validation scoreboard now **5 ✅ · 5 🟡 ·
3 🔴** (V11 convergence, V12 do-nothing, V13 recoverability).

**The realization that shaped the propagation:** V10 (acute/chronic/nervous), V11 (convergence), V12
(ACT/WATCH/DISMISS), V13 (recoverability) are **not four findings — they are one architectural idea: a CLASSIFY
stage between Detect and Explain.** So rather than bolt "recoverability" onto 14 files, I threaded the
**classifier layer** coherently. Per-file changes:
- **ADR** (biggest): `rc_serving_sku_week` gains a **classifier-column block** — `severity_class`,
  `temporal_class`, `recoverability_class`, `action_verdict`, `convergence_score`, `damage_control_path` —
  computed once by the Job, read by every screen. The ADR is the schema *home* for DK-13/14/15 + V10.
- **Capability map:** loop diagram now **Detect → CLASSIFY → Explain → Decide → Act → Prove → Learn**; RCA depth
  gated by class.
- **Measures:** recoverability + damage-control formulae; hazard **B12 bimodal-lead-time (never average)**.
- **UX v1:** watchlist **recoverability + action-verdict + convergence badges**, default sort ACT+RECOVERABLE+$;
  hero screen **RCA-gating + damage-control routing** (TRANSFER vs ALLOCATE).
- **UX v2:** Coming-Risk lead-time flag upgraded to the full recoverability class.
- **UX v3:** an **S-classify** spine section tying all lenses to the shared classifier columns.
- **Joins/ER:** hazard #15 (bimodal lead time) + recoverability/damage-control derivation (no new join —
  `complete_lead_time` already on the series join).
- **Data mapping:** `complete_lead_time` powers recoverability + bimodal caveat.
- **AI functions:** class-aware drafting (recovery escalation vs damage-control notice; RCA narrative only where
  warranted).
- **Gap-tables + both READMEs + requirements synthesis:** classifier-layer note ("DK-13/14/15+V10 = one idea").
- **`discussion.md` untouched** (source transcript).

**Net effect (the through-line):** the classifier layer turns a **10,700-flag alarm into a ~3,634-ACT,
recoverability-aware worklist**, and reserves deep RCA for the committed-material + chronic cases. Verified
consistent across all 12 design docs (grep sweep).

**New open actions:** confirm the recoverability fence definition (does MKE net in-transit/open-transfers before
calling it unrecoverable?); segment SKUs into short-lead vs long-lead bands (bimodal); confirm the "living on the
edge" chronic-critical list is a policy-fix backlog owner exists. **Status unchanged: design + validation
exhaustive, nothing built — Wave 0 slice next, classifier columns now part of its serving-table spec.**

### 2026-09-03 (cont.) — Day-in-the-life, uncovered-scenario sweep (N1–N7 / V15–V21), peer cross-pollination (DK-16–20 / V22–V26)

**A. Day-in-the-life narrative** (`supply_day3_day_in_the_life.md`). Ask: walk through, hour by hour, what a
planner (Leo) sees from opening the laptop, with **real validated examples + full per-screen UI mockups**.
Written: 8:00 pre-triaged worklist (10,700→3,634→128 ACT) → 8:05 hero investigation on 3697-22 ($6.98M, Home
Depot 251-vs-150, PO 212-day slip, +352 target-refresh) → transfer-not-expedite (org 2013 +3,797) → 8:40
do-nothing DISMISS → 9:00 committed-loss damage-control → 9:30 Techtronic 3,035-SKU constraint pivot → forward
risk/wave → forecast-bias handoff → $452M excess → action log → Value page. Real examples reference box + a
"which understanding shows up where" through-line table. It's the "start here" read in the folder README.

**B. Uncovered-scenario sweep → V14 catalogued 7 leads; each then live-validated (V15–V21):**
- **N1 Transition/NPD (V15) ✅** — status is on `items_scd1` (`transition_sku_flag`/`is_npd_item`), NOT the demand
  fact (V14 probed the wrong table). 71,484 transition / 4,038 NPD; **1.5× / ~9× over-represented in shortages**
  — a distinct, sourceable root cause.
- **N2 Over-forecast→excess (V16) 🟡 honest-no** — plausible but **not provable at SKU grain**; excess is
  **62.5% systemic**, SKUs shared. *A membership join is not causation.* Reframed: excess is a planning-policy
  problem, not customer-caused.
- **N3 Returns/warranty (V17) ✅/🟡** — real & material (**3.2M warranty recs** + reason taxonomy) but
  **cross-system (JDE/AX)** → needs an item-key crosswalk; deferred.
- **N4 Found inventory (V18) ✅** — **25,089 found events / +81.9M units**; adjustments must be read **signed**
  (positive = heal signal, downgrades a shortage).
- **N5 Non-standard demand (V19) 🟡 minor** — NO-CHARGE/OTHER only **1.1% of volume** → a weight-by-$ ranking fix.
- **N6 Component/bulk orgs (V20) ✅** — **8000 = Supplier Inv (consignment), 2092 = 3PL Parts** (designated_org
  NULL) — non-DC grains; **segregate before $-ranking** → fixes a distortion that quietly recurred across
  V1/V2/V5/V7/V9.
- **N7 Recovery velocity (V21) ✅** — bimodal: **29% heal fast (≤5 snaps) / 24% stuck (40+)** → sharpens WATCH
  (fast) vs chronic (stuck).

**C. Peer-app cross-pollination** (`supply_day3_cross_pollination_mro_peer.md`). Distilled a peer MRO
inventory-optimization app (a different domain — spare-parts stocking-parameter optimization) into our work,
**data-checked each idea on MKE**, and wrote it up. **Company name withheld throughout** (per request — file
renamed `_mro_peer`, full-workspace grep = 0 occurrences). Key realization: the peer is the **planning/S&OP half**;
ours is the **execution/S&OE half** — together a full control tower. Also validated a **health-status Sankey** is
buildable for MKE (Total on-hand $ → ABC → health), richer than the peer's because our terminal nodes are the
validated classifier states.

**D. Cross-pollination scenarios live-validated (V22–V26):**
- **DK-16 Criticality/ABC (V22) ✅** — A-class shortages **$67.8k/SKU = 2.1× C-class**; buried in a $-only rank →
  add as a classifier axis (blended priority). 37% Unclassified is a completeness gap.
- **DK-17 Dormant/E&O (V23) ✅** — `obsolete_date` too sparse ($0.9M); the real signal is **movement-recency** —
  **$545M never-shipped** + $16M dormant. Must pair with intentional-hold + NPD before calling dead stock.
- **DK-18 Intermittent demand (V24) ✅** — **~24% intermittent** (ADI proxy) → a data-quality **guard on our own
  SS/consumption formulae**; explains part of V3's "chronic under-forecast."
- **DK-19 Parameter recommendation (V25) 🟡 scope-corrected** — MKE is **projection-based, no ROP/MAX** → becomes
  a **safety-stock** review; the recommender is **blocked** (SS methodology B1/B10). But the **proposal-queue
  workflow is reusable now** (Lakebase `action_request` + DK-14 verdict).
- **DK-20 Alignment/Sankey/hold (V26) ✅/🟡** — **54% aligned** KPI ✅; Sankey ✅; intentional-hold *partial*
  (`ss_managed='Yes'` = $450M, no explicit reserve flag); `inventory_planning_method` corrects V25 (MKE has a tiny
  min-max/ROP tail, $15M of $1.6B — 99% projection-based).

**Promoted to requirements + classifier:** Part K now carries **N1–N7** and **DK-16–20** with verdicts + evidence.
ADR `rc_serving_sku_week` classifier block gains `criticality_class`, `demand_class`, `lifecycle_class`,
`dormant_flag`, `intentional_hold` (+ the earlier severity/temporal/recoverability/action_verdict/convergence).
Two of these are **integrity guards** (DK-18 intermittent → low-confidence measures; DK-20 intentional-hold →
suppress false dormant/excess flags).

**Validation set now V1–V26.** Recurring discipline held: **the data disproved two naive claims** (N2 causal link;
DK-19 recommender) and **course-corrected two** (N1 wrong-table, N6 org-type, DK-17 sparse-obsolete-flag, DK-19
model mismatch) — recorded honestly rather than forced. **New open actions:** classify the 37% Unclassified ABC
(DK-16); JDE/AX↔EDW crosswalk for returns (N3); confirm authoritative ABC + a safety-critical flag; a
BOM-dependency signal for true intentional-hold (DK-20). **Status unchanged: design + validation exhaustive across
26 validations + 20 DK requirements; nothing built — Wave 0 slice next, now with the full classifier layer
(9 axes) in its serving-table spec.**

---

## 2026-09-03 — Classifier-axis propagation sweep (N/DK data keys → all workbench docs)

**Ask:** "update all of the other files, with data keys … per the requirements by each file … what gets
modified in the way we are grabbing the data, how are we presenting this on the UI, what capabilities this
whole new information provides to the users … to make the app successful."

**What:** propagated the nine confirmed classifier axes (severity · temporal · recoverability · verdict ·
convergence · **criticality · demand-class · lifecycle · dormant · intentional-hold**) plus adjacent
scenarios (found-inventory, returns, alignment/Sankey, proposal-queue) across every workbench doc along
**three angles** — data-grab, UI presentation, user capability. All edits READ-ONLY-sourced.

**Per-file changes:**
- **`supply_day3_joins_er_diagram.md`** — added a "Classifier-axis data keys (N/DK)" join table + hazards
  #16 (lifecycle lives on item-master, NOT demand-fact — flag is NULL there), #17 (`obsolete_date` too sparse
  → use last-ship recency), #18 (warranty is JDE/AX cross-system, needs crosswalk).
- **`supply_day3_data_architecture_adr.md`** — §7.1a serving columns extended with `criticality_class`,
  `demand_class`, `lifecycle_class`, `dormant_flag`, `intentional_hold`.
- **`supply_day3_data_mapping.md`** — new **Activity 10** table: the exact grab for each signal (dim-join vs
  derived agg vs cross-system), verdicts, and serving-layer impact (most are cheap columns on
  `rc_serving_sku_week`; returns is the only new pipeline).
- **`supply_day3_capability_map.md`** — new **Part 3½** (8 new user capabilities, one line each: escalate by
  $ not by red; trust a measure by its demand pattern; NPD gets its own playbook; see excess not just
  shortage; real fix vs phantom heal; leave reserves alone; one portfolio-health number + drill; propose a
  plan-input change safely) + scoreboard rows 11–18.
- **`supply_day3_ux_design_v3_scenarios.md`** — the presentation home: §S-classify+ (5 axes as serving
  columns that re-rank & calibrate every lens), §S8 Portfolio Health KPI + Sankey (54% aligned), §S9
  Dormant/E&O lens (managed-hold excluded), §S10 found-inventory/phantom-heal badge, §S-badges
  (criticality Ⓐ/Ⓑ/Ⓒ, lifecycle 🌱/🔁, intermittent confidence band). AppKit component notes on each.
- **`supply_day3_ux_design_v2.md`** — watchlist gains criticality badge + lifecycle chip; new default sort
  `criticality × recoverability × convergence`; pointer to v3 §S8–S10.
- **`supply_day3_ux_design.md`** (v1) — data-readiness table extended with the 6 axis rows + returns ❌;
  pointer to v3.
- **`supply_day3_gap_tables.md`** — Gaps 11–19 detail table (source/grab/status per axis) + scoreboard rows;
  grand total now **19 gaps · 12 ✅ · 5 🟡/gated · 1 ❌**.
- **`supply_day3_measures_and_formulae.md`** — already carried the axis formulae (5 refs; verified, no edit).

**Honest downgrades preserved through the sweep:** DK-19 auto-ROP stays **blocked** (MKE is projection-based —
no reorder point to recommend; only the proposal-queue *workflow* is reusable); N3 returns stays **cross-system
❌** (JDE/AX, deferred until an item-key crosswalk exists); DK-20 intentional-hold stays **🟡** (managed-flag
proxy, no explicit reserve flag). Nothing was forced to ✅ to look complete.

**Status:** documentation set is now internally consistent across data → joins → ADR → capability → UX(v1/v2/v3)
→ gap-tables → measures on all nine classifier axes. Still design+validation only; **Wave 0 vertical slice is
the next build**, now with the full classifier layer specified in the serving-table contract.

---

## 2026-09-03 — DK-21: the Value Ledger (incremental savings + suggested-vs-actual)

**Ask:** a page where 08:00 says "this much at risk," each action increments a "this saved this much" counter
through the day, ending in a total built incrementally — **plus** capture the *actual* action taken (which may
differ from the app's suggestion) with the planner's reasoning/thought process.

**The design call that shaped everything:** at the moment of the click, **nothing is saved yet — the action was
only communicated.** A counter that jumps "+$412k" on click is the "claim-before-read-back" trap the room warned
against. So savings move through **three honest states** — 🔵 Projected (on click, the live day-total the ask
wants) → 🟡 Committed (receiver confirms) → ✅ Realized (next snapshot reads the low-point back). You get the
satisfying incremental counter *and* a truthful banked number.

**Four accounting rules that keep it credible** (all validated): (1) unrecoverable exposure (98%, $372.5M, V13)
→ a **separate "loss-avoided" line**, never savings; (2) convergence credits the **action once**, not per-SKU
(V11); (3) realized **subtracts found-inventory** (S10 — cycle-count heals aren't supply wins); (4) DISMISS is a
**"correctly-not-acted" avoided-cost** counter (V12), not savings.

**Suggested-vs-actual = the learning goldmine:** every action logs both `suggested_action`/`suggested_value` and
`actual_action`/`actual_value` + free-text `reasoning` + `override_reason_code` (reuses the **DK-8 12-reason
taxonomy** → `ai_classify`-able) + a `diverged` flag → suggestion-adoption rate, a trust/override map, and an
honest app-vs-planner realized comparison. Turns every override into training data.

**Live verification (READ-ONLY, mke-rsc, warehouse 7bd33a82f4e92206, 2026-09-03):**
- Commitment-weighted unit value source **confirmed**: `prod_operations.demand.fact_sop_commitment.frozen_blended_lag1_forecast_cost / _value` (joins item/dg5/series/date).
- **Realization read-back mechanism confirmed**: comparing forward MIN(PAB) across the two adjacent snapshots
  (20260902→20260903, window to 2026-12-31), of 192,300 SKU-orgs in both, **946 improved their low-point from
  negative, 247 fully healed to ≥0, 34.66M units of low-point recovered** — exactly the ✅ signal, and proof of
  why phantom-heal subtraction is needed (some rose on found-inventory).

**Files touched:**
- `supply_day3_requirements.md` — **DK-21** in Part K (3-state model, 4 accounting rules, suggested-vs-actual, data + verdict).
- `supply_day3_ux_design.md` — **Screen G · Value Ledger** (two headline KPIs, correctly-not-acted + loss-avoided lines, ledger table with suggested→actual + divergence chip + reasoning popover, mandatory action-close capture modal, full states, AppKit component plan).
- `supply_day3_measures_and_formulae.md` — **§5C** three-state savings formulae + 4 accounting rules + day roll-up + adoption-rate.
- `supply_day3_data_architecture_adr.md` — §7.6 new Lakebase action fields; **§7.7 `rc_value_baseline_daily`** + realization publication (only place the ✅ number is minted).
- `supply_day3_capability_map.md` — Part 3½ two new capabilities (prove-it + learn-from-me).
- `supply_day3_gap_tables.md` — Gaps 20–21; grand total now **21 gaps · 14 ✅ · 5 🟡/gated · 1 ❌**.

**Status:** ✅ data-ready, fully specified across requirements → UX → measures → ADR → capability → gaps. Composes
from validated pieces (V1 baseline, V2 delta, V13 recoverability gate, S10 phantom-heal, DK-8 reason codes) + one
new baseline table + forward Lakebase capture. **No new source table.** Still design; builds in Wave 0 alongside
the hero slice (session timers + baseline freeze must start day one — before/after can't be reconstructed later).
**Open:** which lag/cost field is the authoritative unit value (ties to measures B4).

---

## 2026-09-03 — DK-22: root-cause × week heatmap with recursive drill

**Ask:** an interactive heatmap of root causes × weeks at different levels for the observed variances; onclick to
any cell drills into a subset/next-layer heatmap. "It tells a story."

**Verified-before-designed (READ-ONLY, mke-rsc, latest snapshot, 20 Global):**
- **Weeks-by-volume are near-uniform** — 13 forward weeks, mean ~5,961 at-risk flags/wk, **peak/mean 1.33×**, no
  dramatic vertical bands. → a naïve count heatmap would be boring/misleading. **The story is row-concentration
  (V11: 1 supplier = 3,035 SKUs) + $-weighting (A vs C = 300× by consequence), not week volume.** So: rows =
  cause/supplier/org; color = commitment-$-weighted AND signed (short=red/excess=blue); one fixed process_date.
- **Recursive drill works with a measured stop-rule:** designated-pool → **14 member inventory orgs, 33,467→0
  flags (strong band ✅)**. But ABC-within-org → **1 all-NULL row** (`local_planning_abc_code` is 100% NULL on
  the fact) → correctly collapses to a **SKU list**. So the child dimension must come from a *populated* column
  (criticality via the `dim_series_ext_vw` join, not the fact), and recursion continues only while the child has
  ≥ ~4 banding rows — else the leaf is the SKU list (never a ~99%-empty SKU×week grid).

**Design:** recurse the row dimension, keep the week columns; each hop inherits parent filters + appends a
breadcrumb (click to pop up); preserve the fixed snapshot vintage (no shimmer between levels); $-weighted+signed
at every level; convergence cells split fractionally by contribution (S7a) so multi-cause weeks don't inflate.
Reads as three shapes: horizontal band = chronic cause (V10), vertical band = convergence week (DK-13/S7c), lone
cell = acute. Complements S7c risk-wave (forward "when") — this is 2-D backward+forward "what cause, over time."

**Files touched:**
- `supply_day3_requirements.md` — **DK-22** (the two live findings, drill table, two data guardrails, stop-rule, verdict).
- `supply_day3_ux_design_v3_scenarios.md` — **§S12** recursive-drill navigator: ASCII of the drill ladder + breadcrumb + auto-degrade-to-list, AppKit component plan (Heatmap primitive / Badge-cell fallback, useAnalyticsQuery re-fire with appended filters, Breadcrumb, leaf Table → investigate into hero), all states.
- `supply_day3_measures_and_formulae.md` — **§4.5** heatmap aggregation rules (fixed vintage, $-weighted+signed cell, fractional convergence attribution, populated-child rule, measured stop-rule).
- `supply_day3_gap_tables.md` — Gap 22; grand total now **22 gaps · 15 ✅ · 5 🟡/gated · 1 ❌**.

**Status:** ✅ data-ready — one new pre-agg `sandbox_operations.po_management.rc_cause_week_heat`; drill hops
re-query it with tighter filters, leaf drops to live single-org detail. No new source. Ships after the hero path
(reads the same spine). **The negative finding (weeks-uniform-by-volume) is kept front-and-center so the build
doesn't regress into a misleading volume grid.**

---

## 2026-09-03 — Scenario → Real-ID Catalog (≥50 live IDs per scenario)

**Ask:** list ≥50 distinct real IDs for every scenario identified from the beginning (all activities), one by one,
referring to every file so none is skipped; map each ID set to its scenario/requirement; store the successful query.

**Delivered:** `supply_day3_rootcause_workbench/supply_day3_scenario_id_catalog.md` — **25 scenarios, 60 distinct
real Milwaukee SKU IDs each = 1,500 IDs**, segmented one-per-section, each with its scenario→requirement mapping,
predicate, primary source, and the **exact successful READ-ONLY query**.

**Coverage (nothing skipped):** the 7 source Activities (V1–V6 + V4b), the 6 named scenarios (V7 excess, V6
rebalance, V10-ish nervousness→chronic, V4/V4b supplier slip, V8 bias, V20 stranded/component), the classifier
axes (V9 forward, V10 chronic, V11 convergence/DK-13, V12 do-nothing/DK-14, V13 recoverability/DK-15), the N-set
(V15/N1 lifecycle, V16/N2 over-forecast, V18/N4 found-inventory, V19/N5 non-standard demand, V20/N6 component
orgs, V21/N7 recovery velocity), and the DK-16–20 axes (V22 criticality, V23 dormant, V24 intermittent, V25
param/SS, V26 intentional-hold). N3 returns intentionally excluded (cross-system JDE/AX, no crosswalk).

**ID column:** `prod_edw.dimension.items_scd1.item` (real selling SKU, e.g. 48-37-7010, 2941-21Z); V8 uses the
governed `fact_forecast_accuracy.selling_item_number`.

**Data-truth corrections forced during extraction (each was a wrong guess I fixed against live data, not worked around):**
- `dim_series_ext_vw` lives in `prod_operations.edw_extension`, not `prod_edw.dimension`.
- Demand plan names are full strings (`'10 TOL Demand Plan'`, …), and demand buckets are **monthly** — intermittent
  threshold had to be recalibrated to monthly grain.
- `final_demand_forecast_lag3` is **100% NULL** → V8 bias uses the governed `fact_forecast_accuracy` (confirms DK-7),
  and its max date_key is a future bucket → windowed to Jan–Aug 2026 for real actuals.
- `transition_sku_flag` / `is_npd_item` are **BOOLEAN**, not 'Y'/'Yes'.
- PO date-keys are chronological yyyyMMdd → slip = `promised_delivery_date_key > original_promised_delivery_date_key`
  (55,335 distinct items); the earlier zero was an over-tight window, not a data gap.
- Holds (`sales_fulfillment_hold_transactions`) always carry a release date (0 open) → signal is recency of
  `hold_apply_date_key` + `hold_lag_hours` (recovery velocity), not "still open."

**Method:** consolidated runner (`/tmp/scen_all.py`) → `/tmp/scen_results.json` → generated the markdown, so the
document's IDs and queries are exactly what executed. All READ-ONLY on `mke-rsc`; no writes. Every scenario
returned the full 60 (≥50 satisfied).

---

## 2026-09-03 — N3 returns/warranty deep research: verdict OVERTURNED (❌ cross-system → ✅ conformed)

**Trigger:** N3 was the only scenario with no real IDs in the catalog; asked to research it in detail.

**Finding:** the earlier "cross-system, needs a crosswalk, deferred" verdict was **wrong** — it was based on the
raw `staging_jde.fact_warranty_tool` / `staging_ax.*` tables (keyed on `tool_nbr`/`tool_serial_nbr`). A full
returns/warranty table sweep across both catalogs revealed a **governed `prod_edw.domain_service` schema** and,
decisively, a **conformed, item-keyed fact**: `prod_edw.fact.warranty_transaction` (and `fact.service_order_warranty`)
carry **`item_bigint_key`** → clean star join to `items_scd1`. The JDE/AX/Oracle/Connect integration already
happened upstream into the vault (`hub_/lnk_/sat_` service tables). No crosswalk to build.

**Proof (live, READ-ONLY):** 60 real SKU IDs with warranty activity since Jan 2026 —
`2446-20, 0721-20, 6536-21, MXF220-2HD, MXF302-2HD, 6161-33, 49-24-2310, …` (M18/MX FUEL tool bodies, exactly the
finished tools that return under warranty). Fact columns: `item_bigint_key`, `posting_date_key` (through
2026-09-03), `replacement_reason_code`, `problem_description`, `part_quantity`, `material_cost`/`labor_cost`/
`freight_cost`, `warranty_claim_id`, `serial_number`. **Watch-out:** `part_bigint_key` (replaced part) ≠
`item_bigint_key` (returned tool) — grain must be chosen deliberately.

**Why the first pass missed it:** the V17 validation stopped at the staging layer and never checked the conformed
`fact.*` / `domain_service.*` layer one level up. Lesson reinforced: a "cross-system / no crosswalk" claim must be
verified against the conformed EDW facts, not just the raw source-system staging tables.

**Files corrected (❌/🟡 → ✅):** `supply_day3_scenario_id_catalog.md` (V17 added, 26 scenarios · 1,560 IDs; header
correction note), `supply_day3_gap_tables.md` (Gap 19 ✅; grand total **16 ✅ · 0 ❌**), `supply_day3_data_mapping.md`
(Activity 10 returns row + "no new pipeline"), `supply_day3_joins_er_diagram.md` (join row + hazard #18 RESOLVED),
`supply_day3_requirements.md` (N3 row upgraded), `validation/V17_N3_returns_warranty.md` (correction banner atop
the original verdict, kept for provenance).

**Net:** **every scenario identified across the whole engagement now resolves to real EDW SKUs — 0 unreachable.**

---

## 2026-09-03 — Measures doc updated for the N3 (returns/warranty) upgrade

Following the N3 verdict overturn (conformed item-keyed `fact.warranty_transaction` found), the measures doc had
**no returns formulae at all** — returns only appeared as the found-inventory subtraction term inside the Value
Ledger. Now that it's reachable, added the formulae:

- **New §3.8 · Returns / warranty** — six measures: warranty return rate, return cost per item
  (`material+labor+freight`), top failure reasons (by `replacement_reason_code` / `problem_description`,
  `ai_classify`-able), reverse-logistics supply-add, return recency/velocity, end-user geography of failures.
  Confidence-labelled (✅ where columns are populated & item-keyed; 🟡 where a business rule is needed).
- **The governing rule** stated up front: `item_bigint_key` = returned tool vs `part_bigint_key` = replaced part
  are **two grains, never mixed** — and the **two-lens split** (operational returns = supply source that feeds
  PAB/excess math; warranty returns = quality signal ranked by reason/cost).
- **Phantom-heal tie-in:** operational returns re-entering stock are a signed inflow the Value Ledger's
  ✅-realized formula must NOT bank as a supply win (same discipline as found-inventory, §5C.1).
- **Two honest new BLOCKED rows:** B13 (return-rate denominator — claims vs units, which window) and B14 (which
  `replacement_reason_code` values restock as sellable vs scrap). Computable-now measures kept separate from
  these needs-a-rule ones.

All READ-ONLY; columns verified live on `mke-rsc`. Measures doc is now consistent with the ER diagram (§2 node +
§3.1 dual-FK star rows + §7.7 canonical SQL), gap tables (Gap 19 ✅), data-mapping, requirements, and the catalog.

---

## 2026-09-03 — Catalog-run data-truths folded back into the canonical docs

The ID-catalog extraction was a live test that surfaced query-behavior truths. Some were only in scattered
validation files (or nowhere), and one made an existing hazard entry **wrong**. Folded them into the canonical
join-hazard register (the place a builder actually looks) and cross-linked the catalog:

- **Hazard #10 CORRECTED (was inaccurate):** it listed demand plan names as `10 TOL`/`10 PRT`/… — but the stored
  value is the **full string** `'10 TOL Demand Plan'`. Filtering the short form returns **0 rows** (hit live
  during the run). A builder copying the old entry would have gotten empty results. Now shows full strings + the
  0-row warning.
- **Hazard #15 ADDED:** `transition_sku_flag`/`is_npd_item` are **BOOLEAN** — compare `= true`, not
  `IN ('Y','Yes')` (throws DATATYPE_MISMATCH). (Was only in V15.)
- **Hazard #16 ADDED:** `fact_forecast_accuracy` max `date_key` is a **future bucket** with no actuals — window to
  a past range for a real bias read, or you get zero-error rows. (Was nowhere.)
- **Hazard #17 ADDED:** holds are **never open** (0 open across 2.4B rows) — don't filter
  `hold_release_date_key IS NULL`; use `hold_apply_date_key` recency + `hold_lag_hours`. (Was in V5 prose only.)
- **README:** added the catalog as **doc 13** so it's discoverable in the index (26 scenarios · 1,560 IDs).

Net: the join-hazard register (ER §8) is now the single trap list and is consistent with everything the catalog
run actually proved. All READ-ONLY on `mke-rsc`.

---

## 2026-09-03 — BUILT: Wave-0+ serving layer (9 rc_* tables, full 20 Global book)

First real build. User chose "serving layer first" then expanded to **all six tables + full book + the 1,560
catalog IDs pulled in per scenario**. Reused the verified SQL from ER §7, measures §2/§3/§5C, ADR §7.1a, and the
26 catalog predicates — the docs were the build spec. Scripts in `supply_day3_rootcause_workbench/build/` (01–09).

**Tables (all in `sandbox_operations.po_management`, READ-ONLY sources, guardrail-clean — 0 writes to prod):**
- `rc_run_control` — pinned snapshot 20260903.
- `rc_serving_sku_week` — spine, **3.10M rows · 60,810 SKUs · 54 orgs**, full 11-column classifier layer.
- `rc_scenario_membership` — **1,560 seed IDs × 26 scenarios**, tagged + spine-join flagged.
- `rc_forward_risk` (11,590) · `rc_pattern_rollup` (supplier-normalized) · `rc_snapshot_history` (chronic + gap-decomp vs 20260804 vintage).
- `rc_cause_week_heat` (level-stacked, signed $) · `rc_value_baseline_daily` (Value-Ledger anchor).
- `rc_qa_reconciliation`.

**Verification:** reconciliation **drift = 0** (60,810 SKUs & 238,670 SKU×org match a direct prod_edw re-query at
the pinned snapshot). Classifier headlines survive at book scale: **11,590 flagged / 4,438 ACT** (≈ the validated
~10,700 / ~3,634). Hero **2941-21Z** reads exactly as its validation files: chronic + projected-negative +
UNRECOVERABLE + ACT where short, healthy elsewhere, transition lifecycle; appears in V1/V2/V10/V15.

**Two real bugs caught & fixed during the build (not worked around):**
1. **Grain fan-out** — `20_supply_daily` has up to 6 rows per item×org×date_key (finer sub-grain). Collapsed the
   base to a clean item×org×date_key grain (MAX position, SUM flows) FIRST → rows 4.58M→3.10M, dollars sane.
2. **Commitment join fan-out + magnitude** — `fact_sop_commitment` is DG5×org grained; collapsed to one avg unit
   cost per item. Baseline at-risk went from an absurd $2.27T → a defensible **$27.9B** (4,438 ACT items, hero
   2941 ~$669k/wk consistent with validated 3697-22 $6.98M).
3. **Missing 'healthy' state** — added it to severity/verdict so the 227k never-dipping SKU-orgs aren't false-flagged.

**Honest caveats for the next wave:** committed_value uses avg committed unit cost (or std_cost fallback) — the
authoritative cost basis is still open (measures B3/B4); `convergence_score` is a placeholder 1 on the spine
(join rc_scenario/pattern to populate); snapshot-history gap-decomp uses one prior vintage (20260804), widen later.

**Status:** serving layer built, reconciled, guardrail-clean. **Next:** point a Genie space and/or the App at
these `rc_*` tables (they read the serving layer, never raw prod_edw). Not yet DABs-packaged (workspace-first).

---

## 2026-09-03 — BUILT & DEPLOYED: AppKit Supply Root-Cause Workbench (4 pages) into mke-po-actions-st

First front-end build. User asked for an AppKit app of the full UX/UX design, **reusing the deployed
`mke-po-actions-st` app resource** (its SP `d630d5ba` already holds SELECT + USE_SCHEMA on
`sandbox_operations.po_management` — verified live). Constraint: **do NOT touch `mke-po-actions/`** (kept: mtime
unchanged, verified). Scope: full 4-page design, reading only the `rc_*` serving layer.

**App:** `mke-rc-workbench` (fresh scaffold, AppKit 0.57.0, features analytics+genie), new dir
`mke-rc-workbench/`. Deployed into the existing `mke-po-actions-st` resource → **overwrote the Streamlit P3
demand-events app** (user accepted), keeping the SP + grants.

**Built (reusing the design docs + verified SQL as the spec):**
- **10 SQL queries** (`config/queries/*.sql`) over `rc_*` — watchlist, kpi_summary, hero_waterfall, sku_scenarios,
  scenario_catalog/members, cause_week_heat, portfolio_health, pattern_rollup, forward_risk. typegen ✓ (real
  warehouse-inferred types).
- **Cockpit** (hero) — KPI header (flagged/ACT/chronic/unrecoverable) + watchlist table sorted
  verdict×criticality×recoverability with classifier `Badge`s → click SKU → forward PAB-vs-SS `LineChart` +
  classifier tags + scenario memberships.
- **Scenarios** — 26-scenario catalog (member counts + on-spine coverage) w/ drill to member IDs; recursive
  cause×week `HeatmapChart` navigator with breadcrumb + measured stop-rule (DK-22).
- **Portfolio** — inventory-alignment % KPI + book-value-by-ABC×health stacked bar (Sankey fallback) + driver
  pattern rollup (supplier/org/criticality) + forward risk-wave.
- **Ask (Genie)** — `useGenieChat` over the wired space, with **all 5 trust elements**: identity (`/api/whoami`
  route added to server.ts), generated-SQL card, streaming/status, per-answer disclaimer, OBO execution-identity
  note. Design-skill Genie gate satisfied.
- Shared `lib/badges.tsx` — semantic classifier badges via `Badge` variant tokens (no hex), usd/week formatters.

**Verification:** `databricks apps validate` — ALL checks passed (typegen, AST-grep lint, typecheck, build, tests;
no double-assertions). `databricks apps deploy mke-po-actions-st` → **SUCCEEDED, state RUNNING / compute ACTIVE**.
Logs confirm AppKit (`[appkit:server] Mode: production`), not Streamlit. URL:
https://mke-po-actions-st-4482605715640778.18.azure.databricksapps.com

**Guardrails:** app reads only `rc_*` (grep-verified, zero prod_edw/prod_operations); `mke-po-actions/` untouched;
no prod writes. **Out of scope (next wave):** Lakebase action write-back (drafts/approvals/audit), DABs CI/CD
hardening, the action→outcome value-ledger loop. **Open:** committed_value cost basis (measures B3/B4);
convergence_score still placeholder on the spine.

---

## 2026-09-03 — App fixes round 1 (from live screenshots) + a self-inflicted regression, recovered

User exercised the deployed app and surfaced 5 real issues. Fixed all:
1. **`e.toFixed is not a function`** (page crash) — warehouse BIGINT/DECIMAL arrive as **strings** in JSON; hardened `usd()`/`fmtWeek()` in `lib/badges.tsx` to `Number()`-coerce before any numeric method.
2. **Hero chart Y-axis in quintillions** — `LineChart` auto-plotted every numeric col incl. `inventory_organization_bigint_key`. Reshaped `hero_waterfall` to date_key/PAB/SS/shortfall only; split badges into new `hero_meta` query; set explicit `xKey="date_key"` `yKey=[PAB,SS]`.
3. **Portfolio "alignment 0%"** — used `committed_value` (=0 for healthy SKUs). New `alignment_kpi` query on real book value (`on_hand × std_cost`); `portfolio_health` reshaped to health_status×dollars with explicit chart keys.
4. **Pattern/risk-wave charts mixed scales** — explicit `xKey`/`yKey` (+ horizontal orientation on pattern rollup); heatmap given `xKey=week`, `yAxisKey=row_label`, `yKey=cell_value_signed`, diverging palette.
5. **Genie "required scopes: genie"** — app was missing OBO scope. Set `user_api_scopes: [dashboards.genie]`.

**Regression I caused & fixed (honest note):** `databricks apps update --json '{"user_api_scopes":[...]}'` is a
**full-object PUT**, not a patch — it **wiped the app's `resources` array**, so `DATABRICKS_WAREHOUSE_ID` no
longer resolved and the app failed to start (`ConfigurationError: Warehouse ID not found`). Fixed by re-issuing
`apps update` with the **complete** payload (resources sql-warehouse + genie-space AND the scope together), then
redeploying. Lesson: `apps update --json` replaces, so always send the full resource set.

**Status:** deploy SUCCEEDED, **RUNNING / ACTIVE**, resources [sql-warehouse, genie-space] + scope
[dashboards.genie] intact. All 4 chart/data fixes + Genie OBO live. validate passed pre-deploy.

---

## 2026-09-03 — REBUILT the AppKit app to the prototype's case-file IA (editorial workbench)

The user built a richer HTML prototype (`prototype/`) — an editorial "case-file" workbench — and asked the
deployed AppKit app to match it (its own README: "rebuild should match this IA, not the four-page dashboard").
Rebuilt in place, live rc_* where the serving layer supports it + seed the doc-only cells with provenance chips.

**Ported the visual system** (prototype `css/workbench.css` → `client/src/index.css`, scoped `.wb`): Fraunces +
IBM Plex on the industrial paper palette, message-in-title findings, classifier stamps (ACT/WATCH/DISMISS/Lost-
battle, Ⓐ/Ⓑ/Ⓒ, recoverable/unrecoverable, cause colors), provenance chips, two-tone waterfall, rec-bar, evidence
locker, tour bar, dark Genie rail. Fonts added to `client/index.html`.

**New structure:**
- `lib/workbench.tsx` — stamp/chip/formatter/sparkline helpers (ported from prototype app.js).
- `lib/seed.ts` — typed Tier-B/C seed (CASES 3697-22/296720/345020, EXCESS, REBALANCE, BIAS, DORMANT,
  CONSTRAINTS, PORTFOLIO, TOUR) with tiers preserved; live screens read rc_* instead.
- `lib/store.tsx` — session store: evidence locker, value ledger (projected/realized/not-acted/loss-avoided),
  action log, selected SKU, Leo's-day tour index, highlight.
- `pages/WorklistPage` — LIVE kpi_summary + watchlist, case-file table (stamps, sparkline, lost-battle/dismiss
  row styling), row → case file.
- `pages/InvestigatePage` — the hero: finding + stamps (live classifier tags via hero_meta), 3 trial stations
  (insert → locker), two-tone waterfall from SS@LT + DK-12 callout, SVG position chart, recommended playbook
  (Do-this → ledger), evidence locker → escalation. Seed detail chipped DEMO_FALLBACK; live tags for catalog SKUs.
- `pages/LedgerPages` — Ledger (Screen G honest 3-state), Escalation letter, Value (Screen F), and the seed
  lenses Excess/Rebalance/Bias/Constraints/Dormant (chipped, pending live E&O/bias queries).
- `App.tsx` — mast + full IA nav (Worklist·Case·Coming·Constraints·Excess·Rebalance·Bias·Dormant·Scenarios·
  Portfolio·Escalation·Ledger·Value·Ask) + "Play Leo's day" tour bar stepping view+sku+highlight + StoreProvider.
  Scenarios/Analytics/Genie reused. Dead CockpitPage removed.

**Bugs fixed mid-build:** conditional hook in useCase (moved hook unconditional); TS null-narrowing not flowing
into a hoisted `function` closure (→ arrow const); unused imports.

**Verify:** `apps validate` all-pass (typegen ✓, lint, tsc, build, tests). Deploy SUCCEEDED, RUNNING/ACTIVE,
resources + user_api_scopes intact (full-object update — didn't repeat the earlier wipe). `prototype/` and
`mke-po-actions/` untouched (mtime). App reads only rc_*; ledger/evidence are session-state demo; every seed
element carries a provenance chip + the honesty footer.

**Out of scope (next wave):** live rc_* backing for excess/rebalance/bias/dormant lenses; Lakebase action
write-back; per-week PAB path from the serving layer for the position chart (currently seed).

---

## 2026-09-03 — "Make it real" Part A: Lakebase write-back (the app is now stateful)

The workbench's ledger/evidence/actions were session-state demo (gone on refresh). Added real persistence.

**Reuse:** existing Lakebase project `projects/mke-po-actions` (owner=user, active), branch `production`, db
`databricks-postgres`. App SP `d630d5ba` created + owns a dedicated schema **`rc_app`** (verified via psql:
owner=d630d5ba, tables action_request + evidence_item).

**Built:**
- `server/server.ts` — added `lakebase()` plugin; `onPluginsReady` creates `rc_app` schema + tables if-not-exists,
  and registers Express routes: `GET /api/ledger` (server-computed honest 3-state from action_request),
  `GET /api/log`, `GET/POST /api/evidence`, `POST /api/action` (writes request + returns authoritative ledger).
  Parameterized `appkit.lakebase.query`, `::numeric` casts.
- `client/src/lib/store.tsx` — swapped pure useState for fetches to those routes (hydrate ledger/log on load,
  evidence per case; addEvidence→POST, applyAction→POST returns ledger). Same Store interface, pages unchanged.
- `app.yaml` — added `LAKEBASE_ENDPOINT: valueFrom postgres`.
- App resources — merged `postgres` into `[sql-warehouse, genie-space]` via **`apps create-update`** (full-object
  merge, keeping user_api_scopes — the correct verb per the lakebase skill; `apps update` can't change resources).

**Verified end-to-end (via OAuth-token curl on the live app):** POST a transfer on 3697-22 → `{projected:300000,
residual:1800000}`; a *separate* GET returned the same → **persisted to Postgres, not memory**; log showed the row
with savings_state=projected. Then truncated the test rows for a clean demo (ledger back to projected $0 /
residual $2.10M).

**Cache fix (user asked):** AppKit's persistent cache uses a hardcoded `appkit` schema; in this SHARED Postgres
that schema is owned by the *other* P1 app's SP (`06ae418f`), so our SP hit `permission denied for schema appkit`
(non-fatal — server still bound). Fixed by GRANT USAGE/CREATE/ALL on schema `appkit` to our SP. Fresh logs: **0
occurrences** of the error.

**Deploy note:** a `stop/start` lifecycle op stalled in UNAVAILABLE ~5min; a fresh `apps deploy --no-wait`
converged to RUNNING/SUCCEEDED immediately — prefer redeploy over stop/start for this app.

**Status:** RUNNING/ACTIVE, resources [sql-warehouse, genie-space, postgres] + scope intact, write-back live and
persistent, cache clean. **Part B (weekly refresh Job) still pending.** Guardrails: app writes only to rc_app
(Lakebase) + reads rc_*; no prod writes; mke-po-actions/ + prototype/ untouched.

---

## 2026-09-03 — "Make it real" Part B: weekly serving-refresh Job (data no longer frozen)

The rc_* tables were frozen at one snapshot. Scheduled a real refresh.

**Built:** `supply_day3_rootcause_workbench/jobs/rc_refresh.py` — a notebook generated from the 9 `build/*.sql`
files (run_control → spine → membership → forward/pattern/snapshot → heat/baseline → qa_reconciliation), each as
a `spark.sql(...)` cell, ending with a **reconciliation drift-gate** that raises (fails the run) if any
`rc_qa_reconciliation.drift != 0`. Uploaded to `/Workspace/Users/brijendra.raghuwanshi@databricks.com/rc_refresh`.

**Job:** `rc-serving-weekly-refresh` (id 701024912668336) — serverless notebook task, weekly cron
`0 17 7 ? * MON` America/Chicago (Mon ~07:17, matching the plan's own Monday-snapshot cadence), UNPAUSED,
max_concurrent_runs=1, queue enabled. Writes only to `sandbox_operations.po_management`; READ-ONLY sources.

**Verified:** manual run TERMINATED / **SUCCESS** in 92s; `rc_run_control.build_ts` advanced to 23:12:46 (tables
genuinely rebuilt); reconciliation **drift = 0** on both checks (gate passed on real recompute).

**"Make it real" complete:** the workbench now (A) persists actions/ledger/evidence in Lakebase `rc_app` and
(B) refreshes its serving layer weekly with a drift-gated Job. Remaining future work (out of scope): live rc_*
backing for the seed lenses (excess/rebalance/bias/dormant), wiring the app freshness line to build_ts, and
DABs/CI-CD packaging.

---

## 2026-09-03 · Every screen live — 5 new serving tables + all lenses off seed

**Ask:** "I want live data now! Get all of the IDs that are there to be actually loaded! I want every UI thing
to be live too!" — the seed-backed lenses (Excess / Rebalance / Bias / Dormant / Constraints) and the case-file
evidence were still showing ~3–6 hand-seeded rows, not the real book.

**Serving layer — 5 new full-book tables** (`build/10..14`, all added to the weekly Job, drift-gated):
- `rc_excess` — 3,335 SKUs. Excess defined on **projected balance** (`min_pab > 3×SS`), NOT `on_hand`
  (~100% NULL on the plan fact). $ = surplus × std_cost.
- `rc_rebalance` — 3,567 rows. Spine self-join within the designated pool; QUALIFY picks the best excess org
  per short SKU×org.
- `rc_bias` — 54 DG5 channels from the governed `fact_forecast_accuracy`; flags "OVERRIDE adds error" where
  |planner_bias| > |system_bias|.
- `rc_dormant` — 25,387 dormant/never-shipped items from shipment recency; `safety_stock_managed_flag` →
  intentional vs review-E&O (DK-17).
- `rc_case_evidence` — 9,543 flagged SKUs; 6,750 with hold signals. **Honest finding:** every slipped PO in the
  flagged book carries a sentinel `original_promised = 20000101`, so "who-moved-it" PO attribution is *absent* —
  holds (recency + lag) are the real supply signal, and the demand/supply split is chipped DERIVED, not audited.

**Job:** regenerated `jobs/rc_refresh.py` (14 SQL steps), extended the gate to require the 5 new tables non-empty
+ reconciliation drift=0. Re-ran → SUCCESS; reconciliation `sku_org_grain` 238,670=238,670 and `distinct_skus`
60,810=60,810, drift=0.

**App (`mke-rc-workbench` in the `mke-po-actions-st` SP):**
- 6 new `config/queries/*.sql` (excess/rebalance/bias/dormant/constraints + `case_evidence` @item_id). typegen ✓
  all 18 (needed explicit `DATABRICKS_HOST` from the profile — `.env` alone left the new 6 OFFLINE/degraded).
- Rewired `LedgerPages.tsx`: the 5 lenses now use `useAnalyticsQuery` with a shared `LiveTable` shell
  (loading/error/empty), chips flipped to LIVE. `InvestigatePage.tsx`: catalog SKUs get a **live** forward-position
  chart (from `hero_waterfall`) + a live case-evidence panel (holds + DERIVED demand pressure); hero cases keep
  their curated waterfall + trial track.
- Shrank `seed.ts` — deleted EXCESS/REBALANCE/BIAS/DORMANT/CONSTRAINTS arrays (now live); kept CASES hero
  narratives + TOUR + PORTFOLIO headline.
- validate ✓ (tsc/lint/build/test all green). Deployed `--no-wait` → active_dep SUCCEEDED, app ACTIVE, HTTP 302.
  Resources (sql-warehouse + genie-space + postgres) and OBO scope `dashboards.genie` all preserved.

**Verified live (exact app queries):** Excess 3,335 · Rebalance 3,567 · Bias 54 · Dormant 25,387 · Constraints
326 suppliers · case_evidence(48-73-1321) → cause Supply, 12,080u shortfall, 30,733 holds, 690h max lag. Every
lens is the full book, not seed. Only the modeled waterfall unit-split stays DERIVED (no audited per-SKU formula).

---

## 2026-09-03 · Zero hardcoded data — every surface live, snapshot model made explicit

**Ask:** "many things are still with demo fallback! I want everything live!" → "no hard coded data; all
live data and all live analysis!" Plus two sharp questions: *are we on snapshots?* and *where's the date-range
selector?*

**Snapshot answer (verified in the serving layer):** yes — one pinned snapshot `20260903`, forward 13 weeks
(`20260907`→`20261130`), plus one prior plan vintage `20260804` in rc_snapshot_history for nervousness. A free
calendar picker would imply daily history we don't materialize; the honest UI is a live freshness stamp + the
prior-vintage note.

**4 new live queries (typegen ✓ 22/22):**
- `portfolio_headline` — excess$, unrecoverable$, rebalance/nervous/chronic/dismiss counts (kills the PORTFOLIO
  constants). Live: excess **$19.5M** (seed said $452M — wrong), unrecoverable **$198.5B** committed.
- `freshness` — rc_run_control snapshot/forward-window/plan/build_ts + prior_vintage.
- `hero_split` — SS@LT waterfall from rc_snapshot_history at each SKU's worst week (consumption vs
  target-refresh, DK-12).
- `value_baseline` — at-risk committed $ + unrecoverable $ from rc_value_baseline_daily.

**Fully live rewrites:**
- **InvestigatePage** — dropped the seed CASES entirely. Every SKU: live classifier (hero_meta), live forward
  position (hero_waterfall), live waterfall split (hero_split), live evidence (case_evidence). Trial stations
  from the live cause split; playbook gated on the live verdict. Deleted the fabricated demand/PO "who-moved-it"
  rows (sentinel originals — not in the data). Honesty strip states PO who-moved is absent.
- **server.ts / store** — removed hardcoded BASELINE=2100000 and realized=1410000. projected/notActed/lossAvoided
  are live from the Lakebase action log; baseline/residual composed from the live value_baseline query; **realized
  returns null** (no two-snapshot read-back exists yet — shown as "—", never faked).
- **LedgerPage / ValuePage** — live baseline headline, live dismiss count, stakes ladder from real committed$ +
  unrecoverable$; realized deliberately blank with a note. **EscalationPage** — letter built from live
  case_evidence, not CASES.
- **WorklistPage** — headline SKU count + unrecoverable$ live (removed PORTFOLIO import).
- **Mast** — identity from `/api/whoami` (was hardcoded leo@); **FreshBar** live from `freshness` (snapshot +
  forward window + prior vintage + build date), replacing the hardcoded "Mon 2026-08-31" line.
- **seed.ts** — reduced to the TOUR script + honesty footer only. Tour now navigates to **live** SKUs
  (48-73-1200 ACT, 88-93-0100 target-refresh, 3697-22 DISMISS, 48-11-1850 unrecoverable — the old
  296720/345020 aren't in the live book) and its narration states **no figures** so it can't drift.

**Verified:** grep shows 0 DEMO_FALLBACK chips and 0 hardcoded $/counts in any page; validate green; deploy
SUCCEEDED, app ACTIVE, resources + OBO scope intact; live headline queries return real values
(excess $19.5M, baseline $27.9B/4,438 SKUs, freshness 20260903 + prior 20260804). Only remaining non-VALIDATED
chip is the DERIVED demand/supply unit split (no audited per-SKU formula) and the honest null realized figure.

---

## 2026-09-03 · DETAILED — "All live, no hardcoded data" end-to-end (serving layer → App)

> Consolidated, handoff-grade record of the two-wave push that took the Supply Root-Cause
> Workbench from *demo/seed-backed* to *every screen live off the serving layer*. Supersedes the
> two terse entries above in detail (kept append-only). Read this if you're picking the app up cold.

### 0. Where it started / the demand

The deployed app (`mke-rc-workbench`, running inside the **`mke-po-actions-st`** service principal —
NOT `mke-po-actions`, which is off-limits) had a split personality: Worklist / Coming-risk /
Heatmap / Portfolio / Scenarios / Genie read the live `rc_*` serving layer, but the **five scenario
lenses** (Excess, Rebalance, Bias/FVA, Dormant, Constraints), the **case-file investigation
detail**, and every **money headline** (portfolio $, value ledger, baseline) rendered a handful of
hand-seeded rows from `client/src/lib/seed.ts`.

User escalation, in order:
1. "many things are still with demo fallback! I want everything live!"
2. "no hard coded data; all live data and all live analysis!"
3. Two probing questions: *"flagged SKUs in the last week, right? we are working with snapshots?"*
   and *"Where is the date range selector in the whole website?"*
4. *"everything is live? including the dashboards or any kind?"*

Two forks were confirmed via AskUserQuestion before building:
- **Hero cases** → "Fully live, drop what isn't real" (delete fabricated PO/demand rows rather than
  keep polished-but-fake narrative).
- **Snapshot UI** → "Freshness stamp + vintage toggle" (no fake calendar).

### 1. The snapshot / date-range answer (the important conceptual correction)

Verified against the live serving layer, not assumed:
- **`rc_run_control`** pins exactly one snapshot: `supply_process_date = demand_process_date =
  20260903`, `supply_plan_name = '20 Global Supply Plan'`, `forward_window_end = 20261130`.
- **`rc_serving_sku_week`** carries a single `snapshot_date = 20260903` and a **forward 13-week**
  horizon (`date_key` 20260907 → 20261130).
- **`rc_snapshot_history`** holds a second, prior plan vintage `20260804` (one month back) used for
  plan-nervousness deltas — so there ARE two vintages, but only two.

Conclusion delivered to the user: the flags are **one weekly snapshot's forward view**, not a
rolling last-7-days. A free **date-range calendar would be dishonest** — it implies daily history
the serving layer doesn't materialize. The honest UI is a **live freshness stamp** (snapshot +
forward window + prior vintage + build date) which the Job extends as more vintages accrue. A true
re-driving vintage *toggle* is deferred until >1 current snapshot is materialized.

### 2. Wave 1 — five new full-book serving tables (`build/10..14`)

All written to `sandbox_operations.po_management` (WRITE-allowed); all sources `prod_edw` /
`prod_operations` READ-ONLY. All full-book, no LIMIT. Added to the weekly Job and drift-gated.

| Table | Live rows | Definition & key data-truth |
|---|---|---|
| `rc_excess` | **3,335** SKUs / **$19.5M** | excess keyed on **projected balance** (`min_pab > 3×safety_stock`), NOT `on_hand` — on_hand is ~100% NULL on the plan fact. $ = surplus × std_cost. |
| `rc_rebalance` | **3,567** | spine self-join within `designated_organization`; `QUALIFY ROW_NUMBER` picks the single best excess org per short SKU×org. |
| `rc_bias` | **54** DG5 channels | governed `prod_operations.demand.fact_forecast_accuracy`; flags "OVERRIDE adds error" where `|planner_bias| > |system_bias|`; window 20260101–20260831. |
| `rc_dormant` | **25,387** (9,759 managed) | shipment recency over `10_demand_daily`; `safety_stock_managed_flag='Yes'` → intentional reserve vs "review E&O" (DK-17). |
| `rc_case_evidence` | **9,543** flagged / **6,750** with holds | per-SKU likely_cause + shortfall + criticality + **DERIVED** demand-pressure + live hold recency/lag. |

**Hard data-truth found and honored (do not re-litigate):** every slipped PO in the flagged book
carries a **sentinel `original_promised_delivery_date_key = 20000101`** — there is NO genuine
reschedule attribution ("who-moved-it") available. So `rc_case_evidence` deliberately omits PO-slip
columns; **holds (recency + lag) are the real supply-side signal** and the demand/supply unit split
is chipped `DERIVED` (`SYNTHETIC_MEASURE`), never presented as audited.

**Job:** regenerated `jobs/rc_refresh.py` (14 ordered SQL steps, globs `build/*.sql`), extended the
gate to require the 5 new tables non-empty + reconciliation drift = 0. Re-ran job_id
`701024912668336` → SUCCESS. Reconciliation clean: `sku_org_grain` 238,670 = 238,670,
`distinct_skus` 60,810 = 60,810, drift 0. Spine total 3.10M rows.

### 3. Wave 2 — kill every remaining hardcoded value

Inventory grep found the survivors: `PORTFOLIO.*` constants (excess $, dismiss, unrecoverable $),
the 3 curated hero `CASES`, the Investigate waterfall (`DEMO_FALLBACK`), the Value "impact ladder"
($3.1M/$1.6M/$0.9M, "~8 min", "61%"), the Ledger baseline `$2.10M` + `realized 1410000`, the mast's
hardcoded `leo@milwaukeetool.com` and `Mon 2026-08-31` freshness line, and the tour narration's
embedded numbers.

**4 new live queries** (`config/queries/`, typegen ✓ — all 22 queries cache-HIT):
- `portfolio_headline.sql` — excess$/excess_skus/rebalance_rows/unrecoverable$/unrecoverable_skus/
  nervous/chronic/dismiss, one row. Live: excess **$19.48M**, unrecoverable **$198.5B** committed,
  dismiss **6,042**, nervous **0**.
- `freshness.sql` — `rc_run_control` (snapshot/forward/plan/build_ts) + `prior_vintage` sub-select
  from `rc_snapshot_history` (→ 20260804).
- `hero_split.sql` (@item_id) — SS@LT waterfall from `rc_snapshot_history` at the SKU's **worst
  forward week**: `ss_at_lt`, `pab`, `gap`, `consumption`, `target_refresh`, `ss_gap_delta` (DK-12
  target-refresh trap surfaced honestly).
- `value_baseline.sql` — `rc_value_baseline_daily`: `at_risk_dollars` **$27.93B** / 4,438 SKUs /
  `unrecoverable_dollars` **$27.37B**.

**Client rewiring (fully live):**
- `InvestigatePage.tsx` — **dropped seed `CASES` entirely**. Every SKU now renders: live classifier
  (`hero_meta`), live forward-position curve (`hero_waterfall`), live SS@LT waterfall split
  (`hero_split`), live evidence (`case_evidence`). Trial stations built from the live cause split;
  recommended playbook gated on the live verdict/recoverability. **Deleted** the fabricated
  Home-Depot demand rows and PO who-moved-it rows; honesty strip states PO who-moved is absent
  (sentinel originals). Loading/empty states handled.
- `server/server.ts` + `lib/store.tsx` — removed hardcoded `BASELINE=2100000` and
  `realized=1410000`. projected/notActed/lossAvoided remain **live from the Lakebase action log**;
  `baseline`/`residual` are composed **client-side from the live `value_baseline` query** (new
  `setBaseline` in the store); **`realized` returns `null`** (no two-snapshot read-back is published
  yet) → the KPI renders "—", never a fabricated figure. `Ledger` type widened to allow null.
- `LedgerPages.tsx` — `LedgerPage`/`ValuePage` use the live baseline + live dismiss count + a stakes
  ladder from real committed$/unrecoverable$; realized deliberately blank with a note.
  `EscalationPage` builds the letter from live `case_evidence`. `ExcessPage` headline from live
  `portfolio_headline`. (The 5 lenses were already live from Wave 1.)
- `WorklistPage.tsx` — headline flagged-SKU count and unrecoverable$ now live (removed `PORTFOLIO`
  import).
- `App.tsx` — mast identity from `/api/whoami` (real `x-forwarded-email`); new **`FreshBar`**
  component live from `freshness` (snapshot 2026-09-03 · forward through 2026-11-30 · 20 Global ·
  prior plan 2026-08-04 · built …), replacing the hardcoded line.
- `lib/seed.ts` — reduced to the **TOUR script + honesty footer only**. Deleted CASES, PORTFOLIO,
  META, EXCESS/REBALANCE/BIAS/DORMANT/CONSTRAINTS arrays and all Case interfaces. Tour retargeted to
  **live** SKUs — `48-73-1200` (ACT recoverable), `88-93-0100` (target-refresh split), `3697-22`
  (DISMISS live), `48-11-1850` (unrecoverable) — because the old `296720`/`345020` **aren't in the
  live flagged book**. Tour narration now states **no figures** so it can't drift from live pages.

### 4. Gotchas hit this pass (for the next engineer)

- **typegen OFFLINE/degraded** for new queries when only `.env` is sourced — the appkit type
  generator needs `DATABRICKS_HOST` resolved. Fix: `export DATABRICKS_HOST=$(…mke-rsc host…)` +
  `databricks auth token --profile mke-rsc` to warm OAuth, then `npm run typegen` → all cache-HIT.
- **`3697-22` reclassified** — seed called it ACT/RECOVERABLE; live it is **DISMISS /
  projected-negative-PAB**. Reinforces that seed numbers were not just stale but wrong; live is the
  source of truth.
- **Seed excess $452M was ~23× too high** — live is $19.5M. Any doc still quoting $452M is wrong.
- **`realized` has no data source** — resisted the urge to keep 1.41M; it's `null` until a
  second acted snapshot enables read-back. This is a feature (honest), not a gap to paper over.
- Deploy preserved resources — plain `apps deploy` does NOT touch the resources array (only
  `apps create-update` does); sql-warehouse + genie-space + postgres + `dashboards.genie` scope all
  survived both deploys.

### 5. Verification evidence (all green)

- `grep` across `client/src`: **0** `DEMO_FALLBACK` chips in pages, **0** hardcoded $/counts in any
  page, **0** imports of deleted seed symbols. seed.ts exports only `TourStep`/`TOUR`/
  `HONESTY_FOOTER`.
- `databricks apps validate` → typecheck + AST-lint + build + tests all ✅ (fixed one unused-import
  TS6133 on the way).
- Deploy `01f1a7fd…` → active deployment **SUCCEEDED**, app **ACTIVE**, HTTP **302** (OAuth
  redirect = server up). Resources `[sql-warehouse, genie-space, postgres]` + scope
  `[dashboards.genie]` intact.
- Live query smoke: portfolio_headline `[19.48M, 198.5B, 6042 dismiss, 0 nervous]`; freshness
  `[wave0_plus, 20260903, 20260903, 20 Global Supply Plan, 20261130, build…, 20260804]`;
  value_baseline `[27.93B, 4438, 27.37B]`.

### 6. Scope boundary clarified for the user

Two distinct "dashboard" artifacts exist: (a) **this React App's chart/table/heatmap pages** — all
now live off `rc_*`; (b) the separate **managed AI/BI (Lakeview) `sdp_*` dashboard** built earlier —
a different artifact that queries live UC tables by nature, not one of the app's pages.

### 7. Honest residuals (live-but-labeled, deliberately not faked)

- **Realized savings** → "—" until a two-snapshot read-back exists.
- **Demand/supply unit split** → `DERIVED`/`SYNTHETIC_MEASURE` chip (no audited per-SKU formula).
- **PO who-moved-it** → absent (sentinel originals); holds are the live supply signal instead.
- **Vintage toggle** → shown as a freshness note (current + prior), not a re-driving selector, until
  the Job materializes more than one current snapshot.

### 8. What's next (not done this pass)

- Publish a read-back table (compare acted SKUs across two snapshots) to light up **realized**.
- Materialize additional weekly vintages, then promote the freshness note to a true vintage toggle.
- Returns/warranty (N3) lens is a separate cross-system build — not added unless asked.
- App still lives under `mke-rc-workbench-src` in the workspace; DABs/CI-CD packaging remains future.
