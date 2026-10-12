<div align="center">

# 🔗 Capability Gaps → Source Tables

### Which workspace tables close each gap from the capability map

**Companions:** [`supply_day3_capability_map.md`](supply_day3_capability_map.md) · [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) · [`supply_day3_ux_design.md`](supply_day3_ux_design.md)
**Method:** live on Databricks profile **`mke-rsc`** (host `adb-4482605715640778`, warehouse `7bd33a82f4e92206`), READ-ONLY. Reuses the 9-activity mapping where a gap needs no new source; runs fresh discovery where it does.

</div>

---

## Status legend
✅ **Ready** — tables confirmed; gap is a *build* (query/aggregate), not a data hunt
🟡 **Partial** — core tables exist; a piece is derived, needs a new Delta/Lakebase object, or awaits activation
❌ **Not found** — no workspace source; external or must be created

## Scoreboard

| Gap | Capability | Tables status |
|---|---|:--:|
| 1 | Forward risk ("about to break") | ✅ |
| 2 | Prescription (action menu) | ✅ |
| 3 | Simulator (what-if) | ✅ |
| 4 | Cross-SKU / systemic patterns | ✅ |
| 5 | Chronic vs acute | ✅ |
| 6 | Gap decomposition (real vs target-moved) | ✅ |
| 7 | Demand-team handoff | 🟡 |
| 8 | Supplier live signal | 🟡 |
| 9 | Proactive alerts | 🟡 |
| 10 | Attribution confidence + stakes | ✅ |
| 11 | Criticality / ABC $-triage (DK-16) | ✅ |
| 12 | Lifecycle NPD/transition lens (N1) | ✅ |
| 13 | Intermittent-demand confidence (DK-18) | ✅ |
| 14 | Dormant / E&O scenario (DK-17) | ✅ |
| 15 | Found-inventory / heal (N4) | ✅ |
| 16 | Intentional-hold exclusion (DK-20) | 🟡 |
| 17 | Alignment KPI + Sankey (DK-20) | ✅ |
| 18 | Parameter proposal queue (DK-19) | 🟡 |
| 19 | Returns / warranty driver (N3) | ✅ |
| 20 | Value Ledger — incremental savings (DK-21) | ✅ |
| 21 | Suggested-vs-actual capture (DK-21) | ✅ |
| 22 | Cause × week heatmap + recursive drill (DK-22) | ✅ |

---

## Gap 1 · Forward risk — ✅ Ready
*Capability: rank SKUs projected below safety stock in the next N weeks (not just those already short).*

| Table | Role | Key columns |
|---|---|---|
| `prod_edw.fact.20_supply_daily` | forward projected position per SKU×org×week | `projected_available_balance`, `safety_stock`, `date_key` (forward weekly), `process_date` (latest snapshot), `plan_name` |
| `prod_edw.dimension.dim_series_ext_vw` | lead time → "risk within lead time" filter | `complete_lead_time` |
| `prod_edw.dimension.items_scd1` / `inventory_organization_scd1` / `date_scd1` | dims | keys |

**Verified live:** each SKU/org carries **~109–112 forward weekly buckets** (latest snapshot 20260902 → out to 20281002), each with PAB + safety_stock. Future SS-crossings are directly computable.

**Build (no new data):** from the latest `process_date`, per SKU×org find the **first future `date_key` where `projected_available_balance < safety_stock`**; rank by earliest-crossing / depth within lead time. This is the "Coming Risk" tab.
**Guardrail:** use the plan's own forward PAB — do **not** invent a demand forecast (the room's warning).

---

## Gap 2 · Prescription — stair-step action menu — ✅ Ready *(data) + rules layer to build*
*Capability: recommend the ranked playbook (pull-in → overtime → add capacity → transfer), each option gated by real constraints.*

The transcript's "menu / stair-steps" each need a feasibility gate — all present:

| Action option | Gating data | Table.columns |
|---|---|---|
| Request supplier pull-in / expedite | supplier + lead-time + who to contact | `dim_series_ext_vw`: `origin_supplier_name/number`, `origin_planner_name`, `complete_lead_time`, `preprocessing_/processing_/postprocessing_lead_time` |
| Change PO qty (respect MOQ/multiples) | order constraints | `dim_series_ext_vw`: `purchase_minimum_order_quantity`, `purchase_maximum_order_quantity`, `purchase_multiple`, `inventory_multiple`, `fixed_lot_multiplier`, `minimum_order_quantity` |
| Make vs buy decision | sourcing mode | `dim_series_ext_vw.planning_make_buy_code` |
| **Add shifts / add capacity** (internal make) | work-center capacity | `prod_edw.dimension.work_center_scd1` + `prod_edw.domain_work_order.*work_center*` (work-def/op/transaction work-center facts) |
| Transfer from another org | pooled availability + lanes | Gap 7-adjacent: `inventory_days_on_hand` + `transfer_orders` + `designated_org_code` |
| Cost of each option | economics | `dim_series_ext_vw`: `purchase_burden_cost`, std cost |

**Verdict:** the **constraint data to gate every stair-step exists.** What must be *built* is the deterministic **rules/policy layer** (versioned, not LLM-invented) that reads these and emits the ranked menu — plus the Lakebase `action_request` (already scaffolded, Activity 9) to hold the chosen action.

---

## Gap 3 · Simulator (what-if) — ✅ Ready *(data) + recompute engine + Lakebase scenario store*
*Capability: override a supply/demand line (e.g. supplier cap 750/wk) and see PAB & the SS gap re-project — the Excel simulator, governed.*

| Table | Role | Overrideable component columns |
|---|---|---|
| `prod_edw.fact.20_supply_daily` | the seed row set per SKU×org×week | **demand:** `total_demand`, `manual_demand`, `dependent_demand`, `independent_demand`, `final_demand_forecast`; **supply:** `effective_supply_forecast`, `final_supply_forecast`, `open_orders`, `scheduled_receipts`, `order_quantity`; **state:** `on_hand`, `safety_stock`, `projected_available_balance` |
| `prod_edw.fact.supply_and_demand_planned_purchase_order` | planned PO lines to flex (dates/qty) | `suggested_*_date_key`, `firm_status` (from Activity 5) |
| `prod_edw.dimension.dim_series_ext_vw` | constraints the sim must respect | MOQ / multiples / lead time (Gap 2) |

**Verdict:** every line the planner overrides in Excel today is a **column here.** The recompute (PAB = prior on-hand + supply − demand, walked forward) runs **in the app**, seeded from these columns. Save scenarios to **Lakebase** (`scenario` metadata/inputs per the writeback taxonomy); never write to `prod_edw`. Two templates to support: **transition-level** and **multi-org-combined**.

---

## Gap 4 · Cross-SKU / systemic patterns — ✅ Ready *(no new tables — a re-aggregation)*
*Capability: "what's the single biggest driver across my whole book?" — one supplier slipping 40 SKUs, one customer over-consuming a category.*

No new sources. **Same Gold, grouped by the entity instead of the SKU:**

| Group-by lens | Fact (variance) | Grouping key |
|---|---|---|
| by **supplier** | PO slip (Activity 5): `purchase_orders` + `purchase_order_change_orders` | `dim_series_ext_vw.origin_supplier_number/name` |
| by **customer (DG5)** | demand surprise (Activity 2): `10_demand_daily` + `sales_order_line_transactions` | `dg5_customer_scd1.mkedg5` |
| by **plant / org** | shortfall (Activity 1): `20_supply_daily` | `inventory_organization_scd1` / `designated_org_code` |
| by **planner** | any of the above | `dim_series_ext_vw.planner_name` |

**Build:** roll the per-SKU variance up to the entity and rank by total $-at-risk contributed (std cost from `dim_series_ext_vw`). Turns 40 tickets into one pattern escalation.

---

## Gap 5 · Chronic vs acute — ✅ Ready
*Capability: "this SKU has been below safety stock 6 of the last 8 weeks" / "this supplier slips every month" — separate fire-fighting from fix-the-system.*

| Signal | Source | Method |
|---|---|---|
| SKU chronic-shortfall | `prod_edw.fact.20_supply_daily` (snapshot history) | count snapshots (same target week) where `PAB < safety_stock`; **55 snapshots since 2026-07-01** verified — ample depth |
| Supplier chronic-slip | `purchase_order_change_orders` (Activity 5) | count `SUPPLIER`-initiated slips per supplier over trailing window |
| Chronic escalations | Lakebase `action_request` → `action_outcome_history` (Activity 9) | repeat cases per SKU/supplier once the log is populated |

**Verdict:** history depth is confirmed; recurrence is a windowed count over existing snapshots. Emit a **chronic badge** + filter; route chronic items to a systemic-fix backlog rather than a one-off escalation. (Prior project work already noted a "chronic-slipper" signal — consistent.)

---

## Gap 6 · Gap decomposition (real consumption vs target moved) — ✅ Ready *(elegant, one table)*
*Capability: split the SS gap into "I actually consumed more" vs "my safety-stock target refreshed higher" (Carter's point) — so planners don't buy against a harmless target shift.*

| Table | Role | Columns |
|---|---|---|
| `prod_edw.fact.20_supply_daily` | same target week across snapshot vintages | `safety_stock` (the target) + `projected_available_balance` + `total_demand`, compared across `process_date` for a fixed `date_key` |

**Verified live (this is the whole proof):** for one SKU, **target week 20261005**, the `safety_stock` target moved **68 → 68 → 420** across snapshots 07-20 → 08-10 → 09-02 while PAB moved 853 → 911 → 8888. So:
- **Δ target** = `safety_stock@latest − safety_stock@earlier` = the "your demand's higher, hold more" component.
- **Δ position** = `PAB` movement = real consumption/supply effect.

**Verdict:** decomposition is a **self-join of `20_supply_daily` across `process_date`** — no new source. Render as a two-tone band on the waterfall (gap-from-consumption vs gap-from-target-refresh). Near-free.

---

## Gap 7 · Demand-team handoff — 🟡 Partial *(evidence ready; handoff channel to build)*
*Capability: one-click "flag to demand with evidence" — package the DG5/promo/priors story into a tracked request to demand planning.*

| Piece | Source | Status |
|---|---|---|
| The evidence to send | `10_demand_daily` (consumption, promo/base) + priors matrix (Activity 2/3) | ✅ ready |
| Shared bridge to demand | **Forecast Genie** (Chris's) + the demand app's Lakebase | ✅ exists (R25) |
| The tracked handoff record | **Lakebase** `integration_outbox` / `notification_delivery` / a cross-app request entity | 🟡 must build |

**Verdict:** all *data* to justify a demand handoff exists; what's missing is the **workflow object** — a Lakebase request that packages the evidence, routes to demand, and closes when they respond (not a lost email). No new `prod_edw` source needed.

---

## Gap 8 · Supplier live signal — 🟡 Partial *(upgraded from ❌ — supplier PERFORMANCE exists in-warehouse)*
*Capability: see supplier reliability/commit at source, not just Oracle's derived promise date.*

Activity 8 confirmed **forward supplier plans / SharePoint PO-status = external ❌.** But this pass found **supplier-performance sources that ARE in the warehouse** and weren't in the original mapping:

| New source found | What it gives | Columns |
|---|---|---|
| `prod_operations.sales.ops_scorecard_fill_rate_vw` | **fill rate + SupplyMiss by item × customer × supplier** — a ready OTIF-style signal | `SupplyFR`, `CustSupplyFR`, `SupplyMiss`, `CustSupplyMiss`, `supplier_number/name`, `itemid`, `CustomerAccountNumber` |
| `prod_operations.edw_extension.fact_approved_supplier_list_vw` | approved-supplier list (alternate sourcing options) | supplier keys |
| `prod_edw.fact.purchase_order_change_orders` | supplier-initiated slip history (Activity 5) | `change_order_originator_type` |
| `prod_operations.korber.cleansed_korber_full_network_storage_capacity` | **DC storage capacity** (network constraint) | capacity fields |

| Still external ❌ | supplier forward **production capacity / weekly commit** (the Excel plans), SharePoint PO-status file → R27 ingest |

**Verdict:** supplier **reliability/fill-rate/slip** is now sourceable in-warehouse (build a supplier scorecard); supplier **forward capacity/commit** remains external until R27 ingestion + a collaboration surface.

---

## Gap 9 · Proactive alerts (push, not pull) — 🟡 Partial *(detection ready; delivery to build)*
*Capability: "3697 just crossed into risk — root cause pre-built, click to review" — pushed, not waited-for.*

| Piece | Source | Status |
|---|---|---|
| Newly-at-risk detection | `prod_edw.fact.20_supply_daily` — diff two consecutive `process_date` snapshots for a SKU that flipped `PAB ≥ SS` → `PAB < SS` | ✅ ready (snapshot history confirmed, Gap 5) |
| Pre-computed likely cause | Gap 1/Activity 1 forward-risk logic | ✅ ready |
| Delivery channel | **Lakebase** `integration_outbox` / `notification_delivery` + a scheduled **Lakeflow Job** on snapshot arrival | 🟡 build |

**Verdict:** the *detection* is a snapshot-over-snapshot diff on existing data; only the **Job + notification wiring** (Teams/email/in-app) needs building. Depends on Gap 1.

---

## Gap 10 · Attribution confidence + stakes — ✅ Ready *(stakes source newly found)*
*Capability: (a) how confident are we it's "primarily demand"? (b) is this a strategic customer commitment or long-tail?*

| Sub-need | Source | Method |
|---|---|---|
| **Confidence** (dominance of the top cause) | derived from the waterfall bucket contributions (no table) | e.g. top-bucket share vs next; a simple ratio |
| **Stakes — $ value** | `prod_operations.demand.fact_sop_commitment` (**newly found**) | `working_final_forecast_lag1_value` / `_cost` by **DG5 customer × item × org** — weight the gap by committed value |
| **Stakes — customer importance** | `prod_edw.dimension.dg5_customer_scd1` + commitment above | rank customers by committed volume/value (strategic vs long-tail) |
| **Stakes — fill-rate exposure** | `prod_operations.sales.ops_scorecard_fill_rate_vw` | which customers already suffering `SupplyMiss` |

**Verdict:** confidence is a computed indicator (free); **stakes weighting is now sourceable** via the S&OP commitment fact (value/cost per DG5) — so "$ at risk" can graduate from bare std-cost to **commitment-weighted** exposure. `fact_sop_commitment` was not in the original mapping.

---

## Gaps 11–19 · Classifier axes & adjacent scenarios (N/DK, validated V15–V26)

*These came out of the validation pass and the peer-MRO distillation, not the original capability map. All but
returns ride the existing conformed spine — dim-joins or cheap derived aggregations, no new pipeline.*

| Gap | Capability | Source table / column | Grab | Status |
|---|---|---|---|:--:|
| **11** Criticality / ABC | ABC $-triage on every verdict | `dim_series_ext_vw.inventory_abc_class` (join `series_bigint_key`) | dim-join | ✅ Ready |
| **12** Lifecycle | NPD/transition suppress false-chronic | `items_scd1.transition_sku_flag`, `is_npd_item`, `npd_launch_date` (join `item_bigint_key`) | dim-join | ✅ Ready |
| **13** Demand-class | intermittent → confidence band | ADI proxy over `10_demand_daily.shipments_history` | derived agg | ✅ Ready |
| **14** Dormant / E&O | value not moving (excess) | last-ship recency = `MAX(date_key WHERE shipments_history>0)` per item | derived agg | ✅ Ready |
| **15** Found-inventory | real fix vs phantom heal | `inventory_material_transaction.transaction_quantity` **signed** | signed agg | ✅ Ready |
| **16** Intentional-hold | exclude managed reserve from excess | `dim_series_ext_vw.safety_stock_managed_flag='Yes'` + `inventory_planning_method` | dim-join | 🟡 Partial (no explicit reserve flag) |
| **17** Alignment KPI + Sankey | portfolio-health headline | `20_supply_daily` gap × `inventory_days_on_hand.on_hand_cost` × `inventory_abc_class` | 3-way agg | ✅ Ready |
| **18** Parameter proposal queue | governed plan-input change | current `safety_stock`, order min/max, `complete_lead_time` — **no ROP/MAX** | workflow | 🟡 Gated (SS method = projection, not min-max) |
| **19** Returns / warranty | reverse-logistics driver | ✅ **conformed, item-keyed:** `prod_edw.fact.warranty_transaction.item_bigint_key` → `items_scd1` (+ `replacement_reason_code`, `problem_description`, material/labor/freight cost, `warranty_claim_id`). Governed `domain_service` schema. Raw JDE/AX staging (`tool_nbr`) is upstream only. | conformed fact | ✅ **Ready** (crosswalk found 2026-09-03; 60 real IDs pulled — corrects earlier ❌) |
| **20** Value Ledger (DK-21) | prove incremental daily savings | PAB Δ (V2) × `fact_sop_commitment.frozen_blended_lag1_forecast_cost/_value`; realized = low-point read-back `20_supply_daily` **−** found-inventory; new `rc_value_baseline_daily` | derived + new baseline table + Lakebase publication | ✅ Ready (read-back verified live) |
| **21** Suggested-vs-actual (DK-21) | capture override + reasoning | new Lakebase fields on `action_request`/`action_outcome_history` + DK-8 reason taxonomy | Lakebase capture | ✅ Ready (fields to add) |
| **22** Cause × week heatmap + drill (DK-22) | variance story + recursive drill | pre-agg `rc_cause_week_heat` = `20_supply_daily` (week × cause/pool/org) × commitment-$; drill re-queries with tighter filters; leaf = live SKU list | new pre-agg table | ✅ Ready (banding + stop-rule verified live) |

**Verified live figures:** A-class $67.8k/SKU (2.1× C); 71,484 transition / 4,038 NPD; ~24% intermittent;
$545M never-shipped / $16M dormant; +81.9M found over 25,089 events; $450M managed stock; 54% aligned.
**One honest downgrade:** DK-19 auto-ROP is **blocked** (MKE is projection-based, no reorder point to recommend
— only the *proposal-queue workflow* is reusable). **Corrected 2026-09-03:** N3 returns was previously called
cross-system ❌ — that was based on the raw JDE/AX staging tables. A **governed, item-keyed conformed fact**
(`prod_edw.fact.warranty_transaction`) exists and joins straight to `items_scd1`; N3 is now ✅ Ready (60 real IDs
pulled). See [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) Activity 10 for the full grab spec.

---

## 📊 Final scoreboard & new tables surfaced

**All 10 original gaps mapped: 7 ✅ Ready · 3 🟡 Partial · 0 ❌.** Every capability-map gap has a workable source; the 🟡s need a build (workflow object / Job / ingestion), not a missing table.

**Plus 9 classifier-axis gaps (11–19, N/DK): 6 ✅ Ready · 2 🟡 Partial · 1 gated (DK-19 auto-ROP) · 0 ❌.** (N3 returns upgraded ❌→✅ 2026-09-03 — conformed warranty fact found.) Detail in the section above.

**Plus 2 Value-Ledger gaps (20–21, DK-21): both ✅ Ready** — compose from validated pieces (V2 delta, read-back verified live, DK-8 taxonomy) + one new baseline table + Lakebase capture fields; no new source.

**Plus 1 heatmap gap (22, DK-22): ✅ Ready** — one new pre-agg (`rc_cause_week_heat`); recursive-drill banding + measured stop-rule verified live (designated-pool → 14 member orgs; ABC-on-fact all-NULL → list). **Grand total: 22 gaps · 16 ✅ · 5 🟡/gated · 0 ❌** (N3 returns upgraded ❌→✅ after the conformed warranty fact was found — see the N3 research entry in WORKLOG).

| Gap | Status | Net-new work (beyond existing Gold) |
|---|:--:|---|
| 1 Forward risk | ✅ | query only |
| 2 Prescription | ✅ | rules layer (data ready) |
| 3 Simulator | ✅ | recompute engine + Lakebase scenario |
| 4 Cross-SKU patterns | ✅ | re-aggregation only |
| 5 Chronic vs acute | ✅ | windowed count |
| 6 Gap decomposition | ✅ | self-join across snapshots |
| 7 Demand handoff | 🟡 | Lakebase request object |
| 8 Supplier signal | 🟡 | scorecard build now possible; forward capacity still external (R27) |
| 9 Proactive alerts | 🟡 | detection ready; Job + notification |
| 10 Confidence + stakes | ✅ | commitment-weighting (source found) |

**Tables discovered this pass that were NOT in the 9-activity mapping (candidates to raise):**
- `prod_operations.sales.ops_scorecard_fill_rate_vw` — fill rate + SupplyMiss by item×customer×supplier (Gap 8/10).
- `prod_operations.demand.fact_sop_commitment` — S&OP commitment, lag-1 forecast **cost/value** by DG5 (Gap 10 stakes).
- `prod_operations.edw_extension.fact_approved_supplier_list_vw` — approved/alternate suppliers (Gap 2 sourcing options).
- `prod_operations.korber.cleansed_korber_full_network_storage_capacity` — DC storage capacity (Gap 2 capacity gate).
- `prod_edw.dimension.work_center_scd1` + `prod_edw.domain_work_order.*work_center*` — make-capacity / add-shifts (Gap 2).
- `dim_series_ext_vw` MOQ family: `purchase_minimum/maximum_order_quantity`, `purchase_multiple`, `inventory_multiple`, `fixed_lot_multiplier`, `planning_make_buy_code` (Gap 2).

**Transcript re-read additions (DK-7…DK-12, verified 2026-09-02):**
- `prod_operations.demand.fact_forecast_accuracy` (DK-7) — **governed** forecast bias w/ **planner_bias vs system_bias** split, error/cost, lag-3, rolling-6 → **strengthens Gap 10 (confidence/stakes) + Gap 5** (bias is now sourced, not empirical). Joins the conformed spine (item/dg5/series/date).
- `prod_operations.demand.dim_forecast_accuracy_reason_codes` (DK-8) — **governed 12-reason taxonomy** (reference list, NOT a join) → the `ai_classify` target for Gap 7 feedback loop. Make-side: `work_order_root_cause_scd1`.
- `prod_edw.fact.transfer_orders` **status='Open'** (DK-9/DK-11) — **240k open transfers** = the forward-rebalance pool (**7,508** forward-coverable crossings) AND the in-transit/count-integrity signal (since `inventory_days_on_hand` in-transit/WIP cost cols are **empty**).
- **DK-10 precision:** only `lag1`/`lag3` columns exist → lag-1..6 must use the `process_date` self-join.
- **DK-12 quantified:** SS-refresh trap real but concentrated (~1.3%; demand ~+220% / SS target ~+17.6% together).
- **DK-15 recoverability (V13) — data-ready, no new table:** `recoverability_class` = forward first-cross (`20_supply_daily`) vs **per-SKU `complete_lead_time`** (`dim_series_ext_vw`). Live: 98% UNRECOVERABLE ($372.5M), lead time bimodal (2d median / 122d avg — never average). Damage-control path (TRANSFER 20% / ALLOCATE 80%) = recoverability × `designated_org_code` rollup. All existing sources.

**One-line takeaway:** the gaps that make planners *more capable* (forward risk, patterns, chronicity, gap-decomposition, stakes) are **all data-ready today** — the missing pieces are build effort (rules, Jobs, Lakebase workflow objects, and the R27 supplier ingestion), not missing sources.

**Method note:** all queries READ-ONLY on `mke-rsc` / warehouse `7bd33a82f4e92206`. Discovery via `information_schema` + small `SELECT`s; no writes.

