# Genie Question Bank — every question our scenarios imply a planner will ask

**Written:** 2026-08-31 · companion to [GENIE_ENABLEMENT_NOTE.md](GENIE_ENABLEMENT_NOTE.md).
**Why this exists:** the user asked that Genie *know what kinds of questions might be asked, based on all the
scenarios we have observed*. This bank is derived directly from our query-backed scenario library
(`data_stories/` — S1–S9, G, R, V, T, C, RW, LG, EM, N, O, P, AP, HOP, STATE, QTY, GEO, the 2120 validation,
and the order-lifecycle flow work). Each question is tagged with: **priority**, the **table/measure that
answers it**, and the **expected answer / gotcha** we already proved — so a Genie space can be seeded with
benchmark Q&A and evaluated against known-good answers.

**How to use in the Genie space:** seed the ★ questions as example/benchmark queries; encode the
**Guardrail** section (Part 7) as instructions so naive phrasings don't produce the wrong-but-plausible
answer; run the whole bank through MLflow eval / LLM-judge before trusting the space (project rule:
done = reconciled/UAT-passed, not deployed).

Legend: ★ = seed as a benchmark example · ⚠️ = a question whose *naive* SQL is wrong (guardrail applies) ·
tables are in `sandbox_operations.po_management` unless noted.

---

## Part 1 — P1 Plan-vs-Actual (on-hand, receipts, shipments)  → `rung2_plan_vs_actual`

| # | Question (natural language) | Answered by | Expected answer / gotcha |
|---|---|---|---|
|★|Which items are off-plan this week, ranked by dollar impact?|onhand_variance_dollar, onhand_status|rank by $ not units (S5); red/yellow/green bands|
||What's my on-hand vs plan for item X at org Y over the last 8 weeks?|planned_pab vs actual_end_on_hand|the hero-item trajectory (S2)|
|⚠️|What's total on-hand value for org 2012?|actual_end_on_hand × cost, latest week only|**NEVER SUM on-hand across weeks** — point-in-time (AP-1; 5.48× trap)|
||Which items breached safety stock (PAB < SS)?|planned_pab vs planned_safety_stock|stockout risk (S5); both tails matter — PAB≫3×SS = excess (G/RW)|
||How much did we receive vs plan for item X this week?|actual_po_received|receipt bridge via purchase_receipt_line (S1)|
|⚠️|What did we ship for item X last week?|actual_shipped|87%-null shipped_quantity trap — needs Standard+Invoiced/Closed filter (AP-4/S3)|
|★|Which items are unplanned (activity but no plan baseline)?|planned_pab IS NULL|18% at 2012 vs 2% at 2120 — "Unplanned (no plan)", not "no actual"|
||Show week-over-week on-hand swing for the volatile items.|wow_onhand_delta|WoW ±138% (RW); 2012 p90 191u vs 2120 10u|

## Part 2 — Plan accuracy & bias (P4-adjacent, P1 quality)  → `rung2_plan_vs_actual`

| # | Question | Answered by | Expected / gotcha |
|---|---|---|---|
|★|Are we over- or under-planning, and by how much?|AVG(onhand_variance_pct) by org|both orgs OVER-plan; 2012 ~5× harder (+101% vs +21%) — NOT "inverted" (corrected)|
||Which planner's items drift most from plan?|planner_name + variance|bias by planner (2.4.3); 69% item×orgs unassigned → route by role (O)|
||Which ABC class carries the most variance dollars?|abc + onhand_variance_dollar|A-items dominate $ at 2012; 2120 A-item variance 22× smaller|
|⚠️|Compare average variance % between 2012 and 2120.|onhand_variance_pct by org|means are outlier-inflated; report median + row-sign too, not just mean|

## Part 3 — Alerting & exception queue (P2)  → `rung2_plan_vs_actual`

| # | Question | Answered by | Expected / gotcha |
|---|---|---|---|
|★|What should I escalate right now?|alert_tier = '3 · Escalate'|org-aware: $200K trigger never fires at 2120 → use org-relative bands|
||Show the exception queue ranked by cost.|onhand_variance_dollar desc|cost-ranked NOT unit-ranked (S5, AP-5: $0.0134 part over-ranks)|
||How many items are in each alert tier by org?|alert_tier by org|2012 21% escalate vs 2120 14%; tiers partition exactly (no double-count)|

## Part 4 — Cross-org / multi-org behavior (the 2120 findings)  → `rung2_plan_vs_actual`, `ds_*`

| # | Question | Answered by | Expected / gotcha |
|---|---|---|---|
|★|How do 2012 and 2120 compare on plan health?|scorecard (ds_scorecard)|2120 healthier: 62% vs 36% green; compare in RELATIVE terms (24× scale gap)|
||Which items exist at both orgs, and how do their stocks compare?|shared-SKU INNER JOIN|only 5,717 shared; **must inner-join** — 41% of 2120 is Mexico-exclusive (S6/N3)|
|⚠️|Show the biggest DC imbalances across orgs.|imbalance (ds_imbalance)|valid ONLY on shared items; e.g. M18 battery 310,834@2012 vs 0@2120 (S6)|
||Is 2120 a transfer hub or directly sourced?|org role (sourcing rules)|2120 = direct Buy/Make leaf, ZERO transfers; 2012 = hub (19 source orgs)|
||Why does 2120's low ship-rate look bad but isn't?|ship/receive ratio + org_role|0.094 vs 0.377 — it's a receiving node; not a "miss"|
||Which org concentrates planning risk?|planners per org, top-planner share|2120: 6 planners, top owns 53% = key-person risk; 2012: 92, top 12%|

## Part 5 — Order-lifecycle / preemptive timing (the flow work)  → `p1flow_order_stage_gold`

| # | Question | Answered by | Expected / gotcha |
|---|---|---|---|
|★|Which orders should I expedite before they're late?|timing_band='4 Very late', recommended_maneuver|preemptive, org-aware bands (percentile per lane×org)|
|★|Which "expedite" orders are actually chronic-supplier problems (fix the source, don't just expedite)?|recommended_maneuver + chronic_pct_late≥60|2120: 345/453 (76%) are systemic; 2012 only 76 — the decision upgrade|
||Which orders are arriving too early — can we defer or downsize?|timing_band='0 Very early'|frees working capital; 2012 1,647 / 2120 325 candidates|
||What's the typical transit time for transfers into 2012, and the tail?|transit_days (p50/p90)|p50 4d, p90 26d — the tail is the risk|
||Which suppliers are chronically late for 2120?|supplier_name, chronic_pct_late|2120 = 3 suppliers, 80.6% late — concentrated & unreliable|
|⚠️|Are POs arriving on time vs the promised date?|p1flow_po_stages slip_days|use the historical lead-time table, NOT purchase_receipt_line.expected (same-day mirage)|
||How many orders need a maneuver today, by org?|recommended_maneuver <> 'None'|2012 6,828 / 2120 1,098|

## Part 6 — Deeper scenario questions (from the wider story library)

| # | Question | Scenario | Answered by / gotcha |
|---|---|---|---|
||Which SKUs are we forecasting demand for that are effectively dead?|P (phantom demand)|forecast≫actual (Inkzall 269K fcst / 4K ship) — P4/V; weight by cost|
||Which POs are past due and not received?|R|356K past-due-not-received lines; 227-day overdue example (T)|
||Which items flipped from on-track to off-plan since last week?|T (status transitions)|PAB 151,929→−3,464 across snapshots; needs vintage compare (AP-6)|
||What's my weeks-of-cover and is it trending to a stockout?|RW (rolling windows)|weeks-of-cover flip 1.07→0.32→1.07; rolling-4wk smoothing|
||Which items are almost entirely dependent on in-transit stock?|LG (logistics)|75K transit / 6 on-hand — 99.99% in-transit dependent; 41-day-late receipts|
||Which new-product launches are spiking demand?|EM (emergent)|demand +705,033% NPD; past-due cluster forming (46.5K lines, 90% TTI)|
||Where is this item right now and at what stage?|STATE / HOP / QTY|169.5K on-hand / 721 in transit / 2,297 scheduled; single-leg hops only, no serial/lot; NOT live track-and-trace|
||Which items have country-of-origin concentration risk?|P (COO risk) / GEO|COO present, no lat/long (needs geocode to map)|
||Which items are forced into over-ordering by MOQ?|P (MOQ waste)|min-order-qty waste pattern|
||Is this a recoverable exception (worth acting on)?|C (counterfactuals)|~37% clearly recoverable — the ROI case for the action queue|

## Part 7 — GUARDRAIL questions (naive phrasing → wrong answer; encode as Genie instructions)

These are the anti-patterns (AP catalog). For each, Genie must apply the RIGHT interpretation, not the
tempting one. Encode as space instructions + prefer certified measures.

| Naive question / phrasing | Wrong result | Right rule |
|---|---|---|
|"Total inventory over these dates" (SUM on_hand)|5.48× too high|point-in-time; take latest snapshot, never SUM across dates (AP-1)|
|"Total transferred units" (SUM material txns unfiltered)|double-counts both legs|constrain transfer direction; dedup (AP-2)|
|"Join staging to dim on raw key"|match rate collapses|dash-normalize keys (AP-3; S7 98.7% vs 4.8%)|
|"Total shipped" (SUM shipped_quantity)|87% NULL deflates|filter Standard + Invoiced/Closed + qty>0 (AP-4)|
|"Rank exceptions by unit-miss"|$0.0134 part tops list|rank by unit-miss × cost × ABC (AP-5)|
|"Status now" (single snapshot)|misses the flip|compare vintages / process_date deltas (AP-6)|
|"Sum 20_supply_daily measures"|grain explosion|respect series/order-type grain, one snapshot/week (AP-7)|
|"Use frozen_* columns"|100% NULL|use process_date deltas; frozen not populated (AP-8)|
|"PO on-time vs expected_receipt_date"|0% late (same-day mirage)|use historical lead-time-error table (flow work)|
|"Compare orgs on raw $ totals"|small org vanishes|compare in relative %/ratio/percentile terms; org-aware (2120 synthesis)|

---

## Coverage map (so we know the bank is complete, not cherry-picked)
Every scenario file → at least one question: S1(P1 receipt)·S2(on-hand)·S3(shipment)·S5(stockout/rank)·
S6(imbalance)·S7(demand event)·S9(forecast drift)·G(positive/both-tails)·R(received/not)·V(extreme var)·
T(transitions)·C(recoverable)·RW(rolling/cover)·LG(logistics/in-transit)·EM(emergent/NPD)·N(multi-org)·
O(location/persona/planner-routing)·P(hidden: phantom/COO/MOQ)·AP(all 10 guardrails)·HOP/STATE/QTY(stage/where)·
GEO(geography)·2120(cross-org, org-role, planner concentration)·flow(preemptive timing, chronic slipper).

## What Genie should SAY when it can't answer well (honesty rule)
Some questions need data not yet in the gold: live "where is it now" (no live feed — completed events only),
lat/long mapping (needs geocode), root-cause categorization (needs the material-transaction ledger),
re-promise history (a Rung-3 accrual). Genie should say "not available yet / here's the closest proxy"
rather than fabricate — mirroring how we flagged limits instead of guessing.
