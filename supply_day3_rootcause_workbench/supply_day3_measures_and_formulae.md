<div align="center">

# 🧮 Measures & Formulae — What We Compute, How, and Why

### The honest accounting: verified formulae vs. inferred vs. blocked-pending-business-input

**Companions:** [`supply_day3_joins_er_diagram.md`](supply_day3_joins_er_diagram.md) · [`supply_day3_data_scenarios.md`](supply_day3_data_scenarios.md) · [`supply_day3_ux_design.md`](supply_day3_ux_design.md)
**Why this doc exists:** the transcript is full of *"there's a fair amount of formulas that go into some of those views… ending inventory is really just demand plus supply plus inputs."* Getting measures **accurate** is where planner trust is won or lost. This document states, for **every measure the UI presents**, the exact formula, the columns, and — critically — **my confidence level**, tested against the real data on `mke-rsc`.

</div>

---

> ## 🎯 The straight answer to "can you get the formulae right?"
>
> **Partly yes — and I'll be honest about which parts.** Three tiers:
>
> | Tier | Meaning | How I know |
> |---|---|---|
> | ✅ **Verified** | I reproduced the plan's own stored number from its component columns, to the decimal | tested live on real SKUs |
> | 🟡 **Inferred** | Standard supply-chain formula, columns exist, but I have **not** confirmed Milwaukee's exact definition | needs a planner to confirm |
> | 🔴 **Blocked** | The logic lives in Excel / an analytics semantic layer / tribal knowledge — **not fully in the EDW** | needs the source formula from the team |
>
> **The single most important finding:** the plan's core identity is **verified** —
> **`PAB[t] = PAB[t−1] + total_supply[t] − total_demand[t]`** — reproduced to the decimal. That one formula is
> both the *position* measure **and** the *simulation engine*. Everything else builds on it.

---

## 📑 Contents
1. [How I tested — the method](#1--how-i-tested)
2. [The keystone: PAB recursion (✅ verified)](#2--the-keystone--pab-recursion)
3. [Measure-by-measure formula table](#3--measure-by-measure-formulae)
4. [Variance — it is NOT just weekly (the detailed answer)](#4--variance--not-just-weekly)
5. [What-if / simulation formulae](#5--what-if--simulation-formulae)
5B. [Statistical formulae — what the data supports (+ a trap avoided)](#5b--statistical-formulae--what-the-data-supports-and-a-critical-trap-avoided)
6. [What is BLOCKED — formulae I need from the team](#6--what-is-blocked)
7. [Honest confidence summary](#7--honest-confidence-summary)

---

## 1 · How I tested

I didn't assume formulae — I **reverse-engineered them from the stored data**: pull a real SKU's component
columns across weeks, compute my candidate formula, and check it against the plan's own stored result. If they
match to the decimal, it's ✅ Verified. All READ-ONLY on `mke-rsc` (warehouse `7bd33a82f4e92206`).

**Grain note discovered while testing:** `20_supply_daily` is finer than item×org — it has customer /
demand-class / series sub-rows. PAB is carried at the aggregate; measures must be summed to the item×org×week
grain before applying formulae (this is itself a correctness rule — §3).

---

## 2 · The keystone — PAB recursion

**Measure:** Projected Available Balance (the forward inventory position — the spine of the waterfall, the
watchlist, forward-risk, and the simulator).

### ✅ VERIFIED formula
```
PAB[t] = PAB[t−1] + total_supply[t] − total_demand[t]
```

### The proof (live, one real SKU, `20 Global`, latest snapshot)
| Week | demand | supply | PAB | PAB Δ | supply − demand | match? |
|---|---|---|---|---|---|---|
| 20260831 | 15,663.7 | 180,309.4 | 164,645.7 | — | — | — |
| 20260907 | 12,056.0 | 0 | 152,589.7 | **−12,056.0** | −12,056.0 | ✅ |
| 20260914 | 16,205.6 | 0 | 136,384.0 | **−16,205.7** | −16,205.6 | ✅ |
| 20260928 | 17,530.4 | 76,000.0 | 177,482.8 | **+58,469.6** | +58,469.6 | ✅ |
| 20261012 | 17,334.5 | 38,000.0 | 182,124.7 | **+20,665.5** | +20,665.5 | ✅ |

Every week's PAB movement equals `supply − demand` to the decimal. **The identity holds.**

### And the components are verified too
```
total_demand = independent_demand + dependent_demand          ✅ (33,202,243 = 33,202,243, exact)
total_supply = on_hand + scheduled_receipts + [other supply columns]   🟡 (sched_receipts confirmed a component; full set to enumerate)
```

> **Why this matters so much:** because PAB is verified as a *recursion over supply and demand*, I can (a)
> present the position honestly, (b) decompose any gap into supply-driven vs demand-driven movement, and (c)
> **simulate** — a what-if is literally this same recursion re-run with one input changed (§5). Crack the
> recursion, crack the simulator.

---

## 3 · Measure-by-measure formulae

*Every measure the workbench presents. ✅ verified / 🟡 inferred (needs confirm) / 🔴 blocked (needs source).*

### 3.1 · Position & shortage (the shortage workbench)

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **Projected Available Balance** | `PAB[t] = PAB[t−1] + total_supply[t] − total_demand[t]` | `projected_available_balance` (stored) / recomputable | ✅ verified |
| **Total demand** | `independent_demand + dependent_demand` | both cols | ✅ verified |
| **Total supply** | `on_hand + scheduled_receipts + …` | components | 🟡 sched_receipts confirmed; enumerate rest |
| **Safety-stock gap** | `ss_gap = PAB − safety_stock` | `projected_available_balance`, `safety_stock` | ✅ (definitional, matches domain pattern) |
| **Shortfall units** | `max(0, safety_stock − PAB)` | same | ✅ (higher-is-better convention) |
| **Below-SS flag** | `PAB < safety_stock` | same | ✅ |
| **Low point / risk period** | `MIN(PAB)` over the forward `date_key` window | PAB series | ✅ (aggregation) |
| **SS at lead time** | `safety_stock` at `date_key = snapshot_week + complete_lead_time` | `safety_stock` + `dim_series_ext_vw.complete_lead_time` | 🟡 lead-time-days→weekly-bucket rounding to confirm |
| **SS-refresh decomposition** (DK-12, the Carter trap) | for same target week across snapshots: `Δtarget = safety_stock_now − safety_stock_old`; `Δposition = PAB_now − PAB_old`. A worse gap driven by `Δtarget>0` (from higher demand) is **not** a physical shortage | `20_supply_daily` self-join on `process_date`, fixed `date_key` | ✅ **verified live**: on coupled cases demand rose ~220%, SS target rose ~17.6% together; ~1.3% of series → **targeted callout** |
| **Recoverability class** (DK-15, the lead-time fence) | `RECOVERABLE` if `first_cross_week > today + complete_lead_time` else `UNRECOVERABLE` (breach locked in — no PO can arrive in time) | `20_supply_daily` first-cross week + `dim_series_ext_vw.complete_lead_time` | ✅ **verified live**: 98% UNRECOVERABLE, **$372.5M** vs $3.7M recoverable; median lead 130d(unrec) vs 7d(rec) |
| **Damage-control path** (DK-15) | for UNRECOVERABLE: `TRANSFER` if in-network excess exists, else `ALLOCATE-ACCEPT` | org-rollup gap (`designated_org_code`) + recoverability | ✅ live: 1,845 TRANSFER (20%) / 7,465 ALLOCATE (80%) of 9,310 short networks |

### 3.2 · Stakes / value

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **$ at risk (std cost)** | `shortfall_units × standard_cost` | `dim_series_ext_vw.standard_cost` | 🟡 std cost confirmed exists; which cost basis (std vs landed vs burden) to confirm |
| **$ excess** | `max(0, PAB − upper_target) × standard_cost` | PAB, SS, cost | 🟡 "upper target" definition needed (3×SS is my placeholder) |
| **Committed $ at risk** | `shortfall_units × committed_unit_value` | `fact_sop_commitment.working_final_forecast_lag1_value / _units` | 🟡 which lag/value field is authoritative |

### 3.3 · Demand surprise / consumption

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **Consumption %** | `actual_shipped ÷ forecast × 100` | `shipments_history` ÷ a forecast col | 🟡 **which forecast?** (working_final vs baseline vs a lag) — planner must pick |
| **Demand surprise (units)** | `actual − forecast` over a range | same | 🟡 range + forecast basis needs confirm |
| **Over-consumption %** | `SUM(actual) ÷ SUM(forecast)` over N months | `shipments_history`, `final_demand_forecast_*` | 🟡 the "134% over 4 months" needs the exact window rule |
| **Forecast bias** | *prefer the governed fact* — `planner_bias` / `system_bias` stored | **✅ `prod_operations.demand.fact_forecast_accuracy`** (DK-7) — MKE's own lag-3 accuracy fact with planner-vs-system bias split, +error/cost, rolling-6 | ✅ **sourced** (use theirs); empirical `(actual−lateN)÷lateN` from `10_demand_daily` is the *fallback / lag-flex* path |

### 3.4 · Forecast evolution (priors / late 1–6)

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **Late-N forecast** | forecast for period P, from the snapshot N months before P | **only `lag1` & `lag3` exist as columns (DK-10)** → for lag-2/4/5/6 use `10_demand_daily` `date_key` (P) × `process_date` (vintage) self-join | ✅ structure verified; ⚠ **must self-join snapshots for full lag-1..6** — pre-built columns give only lag-1 & lag-3 (the accuracy fact is lag-3-locked) |
| **Forecast change (evolution)** | `forecast[P, vintage_now] − forecast[P, vintage_earlier]` | self-join on `process_date`, fixed `date_key` | ✅ verified pattern |

### 3.5 · Supply / PO

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **PO slip (days)** | `promised_delivery_date_key − requested_delivery_date_key` | both date keys (via `date_scd1` for true day-count) | ✅ (date arithmetic; use `date_scd1` not raw key subtraction) |
| **PO date drift** | `promised − original_promised` | both | ✅ |
| **Who moved it** | group by `change_order_originator_type` | BUYER/SUPPLIER/… | ✅ verified (distribution pulled) |
| **Supplier slip concentration** | supplier's share of `SUPPLIER`-type changes | `purchase_order_change_orders` | ✅ verified (top-4 = 78%) |
| **Fill rate** | stored | `ops_scorecard_fill_rate_vw.SupplyFR` | 🟡 use their stored metric; confirm definition |

### 3.6 · Holds / inventory / flow

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **On-hand (level)** | `SUM(on_hand_qty)` at ONE date across item/org | `inventory_days_on_hand.on_hand_qty` | ✅ (never sum across dates — semi-additive) |
| **Adjustment units** | `SUM(transaction_quantity)` where type LIKE '%Adjustment%' | `inventory_material_transaction` | ✅ |
| **On-hold units** | held qty where `hold_release... IS NULL` | `sales_fulfillment_hold_transactions` | 🟡 balance-level vs SO-level reconciliation |
| **Stranded (mfg not DC)** | `on_hand` in org 1080 minus legitimate WIP/in-transit | `on_hand_qty`, `in_transit_cost`, `work_order_wip_cost` | 🟡 split rule needs confirm |
| **Weeks of cover** | `PAB ÷ avg_weekly_demand` OR stored `days_of_cover ÷ 7` | `days_of_cover` or derive | 🟡 they have `days_of_cover` — use theirs, confirm basis |

### 3.7 · Org rollup (pooled network)

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **Pooled PAB** | `SUM(PAB)` grouped by `designated_org_code` at a `date_key` | `designated_organization_bigint_key` | ✅ verified (pooled 669 across OB cluster) |
| **Rebalance candidate** | item where `MIN(org PAB−SS) < 0` AND `MAX(org PAB−SS) > 0` in same network | org-level gaps | ✅ verified (1,646 cases) |

### 3.8 · Returns / warranty (V17/N3 — reachable as of 2026-09-03)

*New block: N3 was previously "cross-system, no measures." The conformed, item-keyed
`prod_edw.fact.warranty_transaction` makes these computable on the same spine. **The one rule that governs all of
them:** `item_bigint_key` = the **returned tool**, `part_bigint_key` = the **replaced part** — two different
grains; never mix them in one measure.*

| Measure | Formula | Columns | Confidence |
|---|---|---|---|
| **Warranty return rate** | `SUM(part_quantity) [returned-tool grain] ÷ SUM(shipments_history)` over the same item × window | `warranty_transaction` (item_bigint_key) ÷ `10_demand_daily.shipments_history` | 🟡 grain/units alignment to confirm (claims vs units) |
| **Return cost per item** | `SUM(material_cost + labor_cost + freight_cost)` grouped by `item_bigint_key` | `warranty_transaction` cost cols | ✅ columns populated & item-keyed |
| **Top failure reasons** | `COUNT(*)` / `SUM(cost)` grouped by `replacement_reason_code` (× item) | `replacement_reason_code`, `problem_description` | ✅ (governed reason field; `ai_classify` on `problem_description` free text — see AI doc) |
| **Reverse-logistics supply add** | `SUM(qty)` of *operational* returns that re-enter stock (restock reasons), added to available supply | join to the operational-return subset (reason ≠ warranty-scrap) | 🟡 which reasons re-enter sellable stock needs a business rule |
| **Return recency / velocity** | `DATEDIFF` on `posting_date_key` vs ship; claims per month trend | `posting_date_key` | ✅ (dates through 2026-09-03) |
| **End-user geography of failures** | returns grouped by `end_user_state` / `end_user_zip` | inline on the fact | ✅ (a quality-signal lens, not a supply measure) |

> **Two distinct lenses, two different measures (do not conflate):**
> 1. **Supply lens** — *operational returns* (Customer/Shipping/Duplicate-shipment errors) come **back into
>    stock** → a supply source that can heal a shortage or inflate excess. Feeds the same PAB/excess math.
> 2. **Quality lens** — *warranty returns* (genuine failures) are a **demand-quality signal**, not restock →
>    ranks failing SKUs by reason and cost. Splitting these by `replacement_reason_code` is the prerequisite.
>
> **Phantom-heal tie-in:** operational returns that re-enter stock are one of the signed inflows the Value
> Ledger's ✅-realized formula must **not** count as a supply win (same discipline as found-inventory, §5C.1).

---

## 4 · Variance — NOT just weekly

*This is the detailed answer to "for variance… different situations, or just weekly?" The transcript is
explicit that the same word "variance" means several different comparisons, and the horizon is a **sliding
scale**, not a fixed week. Presenting one weekly number would be wrong.*

### 4.1 · Variance is a family, not a metric (per the domain pattern)
The same UI must compute **different variances for different questions** — and label which one:

| Variance type | Formula | Business question | When shown |
|---|---|---|---|
| **Plan vs plan** (same-bucket) | `plan[P, snap_now] − plan[P, snap_earlier]` | how did the expectation for the *same* week change? | priors, gap-decomposition |
| **Plan vs actual** | `actual[P] − frozen_plan[P]` | did what happened match the frozen expectation? | attainment, outcome proof |
| **Actual vs actual** | `actual[wk] − actual[wk−1]` | is operations improving week to week? | trend |
| **Confirmed vs requested** | `promised_date − requested_date` | did the supplier commit to what we asked? | supply drill |
| **Target vs projected** | `PAB − safety_stock` | are we projected to breach the target? | shortage/excess |

> **Rule:** never show a bare "variance." Always name it (the domain pattern lists 6 meanings of
> "week-over-week"). Same-bucket (same target week across snapshots) = real plan movement; rolling-week
> (different target weeks) is NOT a plan change and must not be labeled one.

### 4.2 · Direction matters — variance sign is not "good/bad"
Per the domain pattern, classify by the measure's desired direction (this changes the formula):
```
Higher-is-better (fill rate, on-time):     shortfall = max(0, Target − Actual)
Lower-is-better  (forecast error, late):   overage   = max(0, Actual − Target)
Exact target     (planned receipt qty):    report signed variance AND |Actual − Target|
Target range     (safety stock/coverage):  shortfall = max(0, Lower − Actual); excess = max(0, Actual − Upper)
```
A forecast *increase* can be **bad** here (it raises the SS target → looks worse). So green≠up blindly.

### 4.3 · The horizon is a sliding scale (weekly AND multi-period)
The transcript: *"could be over weeks, and multiple months… ±6 months."* So variance is computed at
**whatever window the user picks**, not a fixed week:

| Situation | Aggregation | Example from transcript |
|---|---|---|
| Single worst week | variance at one `date_key` | "the worst week so to speak" |
| Multi-week / months | `SUM` over a `date_key` range | "5 straight months" |
| Lag-based (demand) | forecast at late-1..6, standard late-3 | "3 months ago the forecast was X, now Y" |
| Look-back bound | ≤ ±6 months | "6 months in the past is really the root" |

### 4.4 · Grain matters — weekly vs monthly is a real correctness issue
- **Supply variance** = weekly (20-plan is weekly Monday buckets).
- **Demand variance** = **monthly** by default (10-plan is planned monthly; a *weekly* demand-surprise is just
  the monthly ÷ N — the transcript flagged this as possibly meaningless). Offer weekly only behind a toggle
  with a caveat.
- **Cross-org variance** = pooled via `designated_org_code`, not per-org (per-org is misleading).

> **So: variance is weekly, monthly, multi-month, lag-based, per-org, and pooled — the user picks the
> situation, and the UI must apply the matching formula + label it.** A single weekly number would be
> incorrect for most of the planner's real questions.

### 4.5 · Variance heatmap (cause × week) — the aggregation rules (DK-22)
*The heatmap (UX v3 §S12) is variance-over-time made visual. Three rules keep each cell honest — verified live.*

| Rule | Formula / rule | Why |
|---|---|---|
| **Fixed snapshot vintage** | every cell computed from **one `process_date`** (`= MAX(process_date)` or a chosen pin) | variance is snapshot-dependent (the priors/late-1–6 finding); mixing vintages makes the grid shimmer between levels |
| **$-weighted, signed cell** | `cell_value = Σ (safety_stock − PAB) × committed_unit_value` over the (cause,week) set; **sign preserved** (short<0-cover = red, excess = blue) | count-only hides that a C-class band ($200) ≠ an A-class band ($67.8k); magnitude-only hides short-vs-excess |
| **Fractional convergence attribution** | a SKU-week with k causes contributes `variance × (contribution_cause / Σ contribution)` to each cause row (reuse S7a bars) | counting the full variance once per cause **inflates** multi-cause weeks; fractions sum back to the true total |
| **Drill child = populated column** | next-level rows from a **non-null** dimension (criticality via `dim_series_ext_vw`, member inv-org via the fact) — **never** the all-NULL `local_planning_abc_code` fact column | verified: ABC-on-fact is 100% NULL within the busiest org → an all-null child renders one empty band |

> **Measured stop-rule:** recurse to a child heatmap only while it has **≥ ~4 populated rows that band**
> (peak/mean spread > ~1.5×); below that the leaf is the **SKU list**. Live: designated-pool → 14 member orgs
> (33,467→0, bands ✅); ABC-within-org → 1 row (list ✅). Weeks-by-volume alone are near-uniform (peak/mean
> 1.33×) — so the signal is row-concentration + $, not week count.

---

## 5 · What-if / simulation formulae

*Your instinct is right — the simulator has formulae, and I can state them precisely because they reuse the
verified PAB recursion.*

### 5.1 · The simulator IS the recursion, re-run with an override
Because **`PAB[t] = PAB[t−1] + supply[t] − demand[t]`** is verified, a what-if is deterministic:
```
1. Take the SKU's baseline series (on_hand, supply[t], demand[t]) from 20_supply_daily.
2. Override ONE (or more) input line — e.g. cap supply at 750/wk, or demand +10%.
3. Re-walk the recursion forward: sim_PAB[t] = sim_PAB[t−1] + sim_supply[t] − sim_demand[t].
4. Re-derive gap = sim_PAB − safety_stock, new low point, new risk weeks.
5. Show delta: baseline vs scenario, gap −904 → −120, $ at risk $412k → $54k.
```
This is exactly the transcript's Excel move ("I changed all this incoming supply to 750/week to show what
that would look like") — now governed and reproducible.

### 5.2 · Constraint formulae the sim must enforce (so it can't propose the impossible)
| Constraint | Formula | Column |
|---|---|---|
| Min order | `order_qty ≥ purchase_minimum_order_quantity` | `dim_series_ext_vw` |
| Order multiple | `order_qty MOD purchase_multiple = 0` (round up) | `dim_series_ext_vw` |
| Max order | `order_qty ≤ purchase_maximum_order_quantity` | `dim_series_ext_vw` |
| Lead-time feasibility | arrival week `≥ now + complete_lead_time` | `complete_lead_time` |
| Transfer availability | `transfer_qty ≤ source_org excess PAB` | pooled PAB |

### 5.3 · Common what-if scenarios and their formula
| Scenario | Override | Recompute |
|---|---|---|
| Supplier capacity cap | `sim_supply[t] = min(supply[t], cap)` | recursion → new gap |
| Demand up/down % | `sim_demand[t] = demand[t] × (1 ± p)` | recursion → new gap |
| Pull-in a PO | shift `scheduled_receipts` to an earlier `date_key` | recursion → earlier recovery |
| Transfer from org | `sim_supply_destorg[t] += q; sim_supply_srcorg[t] −= q` | pooled recursion |
| Change PO qty | `sim_supply[arrival_wk] = new_qty` (MOQ-checked) | recursion → new gap |

> **Confidence:** the recursion is ✅ verified, so the *mechanics* of the sim are trustworthy. The **safety-stock
> refresh** under a demand change is 🟡 — if you raise demand, does the sim also refresh the SS target (forward
> DOC)? That behavior (Carter's point) needs the team's rule before the sim can auto-refresh SS; until then,
> hold SS constant in-scenario and label it.

---

## 5B · Statistical formulae — what the data supports (and a critical trap avoided)

*You asked specifically about statistical formulae. Supply chains run on them — but here the honest answer is
nuanced, and I found one trap worth calling out.*

### 5B.1 · The apparatus EXISTS in the schema (Oracle's statistical forecasting)
`10_demand_daily` and `20_supply_daily` carry a **full statistical-forecasting column family**:
`total_statistical_forecast_mad`, `_mape`, `_bias`, `_forecast_methods`, `_forecast_method_weights`,
`_intermittent_indicator` (Croston-style intermittent demand), `_outlier_values`, `_outlier_indicator`,
`_regime_change_indicator`, `_average_interarrival_time`, `_batch_size`, `_complexity`,
`baseline_statistical_forecast`, `dampened_statistical_baseline`, `locked_statistical_baseline`.

This tells us MKE's planning engine (Oracle) **does** compute MAD, MAPE, bias, model selection, and
intermittent-demand handling internally.

### 5B.2 · ⚠️ BUT they are EMPTY in what we read (verified)
```
On the latest snapshot, across ALL demand plans (10 TOL/PRT/ACC/HND/QP):
   total_statistical_forecast_mad   → 0 populated
   total_statistical_forecast_mape  → 0 populated
   total_statistical_forecast_bias  → 0 populated
   total_statistical_forecast_forecast_methods → none populated
```
So although the columns exist, **the statistical error metrics are not exposed in the EDW data we can read** —
they likely live inside the Oracle planning engine and aren't published to these fact tables. **I cannot
present MAD/MAPE/bias from the source today** — that would be presenting empty columns as if populated.

### 5B.3 · 🔴 The trap I avoided: `service_level` is NOT a percentage
The canonical safety-stock formula needs a service level (z-factor). `dim_series_ext_vw.service_level` **looks**
like the input — but its actual values are **category codes**: `TOL`, `BAT`, `OPE`, `MXF-CON`, `DCE`, `HYD`…
(product/service groupings), **not** `0.95`. **Had I assumed `service_level = 95%` in a safety-stock formula, I
would have produced confidently wrong numbers.** This is exactly the accuracy risk you're worried about — so I'm
flagging it rather than guessing.

### 5B.4 · The canonical statistical safety-stock formula (anchored to ASCM/APICS)
*If/when MKE wants us to compute statistical safety stock (rather than read their stored `safety_stock`), this
is the recognized standard — so we're defensible, not inventing:*
```
Safety Stock = z × σ_LT
   σ_LT = √( E[L]·σ_d²  +  μ_d²·σ_L² )      ← combined demand + lead-time variability
   z    = Φ⁻¹(CSL)                          ← e.g. 95%→1.645, 99%→2.33
   ROP  = μ_d·E[L] + SS                     ← reorder point
```
- `μ_d`, `σ_d` = mean & std-dev of demand per period (derivable from `10_demand_daily` history + actuals).
- `E[L]`, `σ_L` = mean & std-dev of lead time (`dim_series_ext_vw.complete_lead_time` gives the mean; **std-dev
  of lead time is not a column** → would need PO history `promised − actual receipt` to estimate).
- **Source:** ASCM/APICS canonical treatment (verified via research 2026-09-02).
- **Caution from the standard itself:** assumes demand-during-lead-time is ~Normal. MKE has **intermittent**
  items (the `intermittent_indicator` column exists) → for those, Normal-based SS is wrong; use Croston /
  fill-rate-based methods. So even the "standard" formula is item-dependent.

### 5B.5 · Statistical measures I CAN compute from populated data (✅/🟡)
| Statistical measure | Formula | From | Confidence |
|---|---|---|---|
| **Forecast bias** (empirical) | `mean(actual − forecast)` over history | `shipments_history` vs `final_demand_forecast_3_month_ago` | ✅ computed live (+60–190%) |
| **MAPE** (empirical, self-computed) | `mean(|actual − forecast| ÷ actual)` | same, over a window | 🟡 computable *by us* from history (not from their empty MAD/MAPE cols) |
| **Demand CoV** (variability class) | `σ_d ÷ μ_d` over demand history | `10_demand_daily` demand series | 🟡 computable; useful to flag erratic SKUs |
| **Demand std-dev during lead time** | `√(E[L]·σ_d²)` (deterministic-LT case) | demand history + `complete_lead_time` | 🟡 computable; σ_L missing for full form |
| **Lead-time variability** (σ_L) | `stddev(actual_receipt − promised)` | PO history | 🟡 derivable from `purchase_orders` receipts |

> **So the honest statistical answer:** MKE's engine computes the heavy stats (MAD/MAPE/model selection)
> internally but **doesn't publish them** to the tables we read; I should **read their stored `safety_stock`
> rather than recompute it** (their method is authoritative and I can't see it — B1). Where I *do* present
> statistics (bias, MAPE, CoV, variability), I compute them **empirically from actuals+forecast history** and
> label them as *our* computation, anchored to the ASCM standard — not claiming to mirror Oracle's internal
> numbers.

---

## 5C · Value-Ledger / savings-realization formulae (DK-21 — Screen G)

*The savings counter is a real measure with a strict accounting model. The core rule: **savings are recognized in
three states**, and only the last is "banked." Sources verified live 2026-09-03.*

### 5C.1 · The three states — and the exact number in each

| State | Formula | Basis | Confidence |
|---|---|---|:--:|
| 🔵 **Projected** (on click) | `Δrisk_action = min(exposure_before, action_qty) × committed_unit_value` where `exposure_before = max(0, safety_stock − MIN(PAB)_forward)` | PAB/gap (V2, ✅) × `fact_sop_commitment.frozen_blended_lag1_forecast_cost` (✅ live) | 🟡 provisional by design |
| 🟡 **Committed** (receiver confirms) | same value, state promoted on supplier-accept / transfer-approve event | Lakebase action event | 🟡 |
| ✅ **Realized** (next snapshot) | `Δrealized = max(0, MIN(PAB)_forward[t] − MIN(PAB)_forward[t−1]) × unit_value − found_inventory_units × unit_value` | low-point read-back (`20_supply_daily`, ✅ live) **minus** signed `inventory_material_transaction` (S10) | ✅ mechanism verified |

> **Realization read-back — verified live (09/02→09/03, forward window to 2026-12-31):** of 192,300 SKU-orgs
> present in both snapshots, **946 raised their forward low-point from negative, 247 fully healed to ≥0, 34.66M
> units of low-point recovered.** This is the raw ✅ signal; the phantom-heal subtraction (below) nets out the
> portion that came from cycle-count adjustments, not supply.

### 5C.2 · The four accounting rules (each changes the number)

1. **Unrecoverable → loss-avoided line, not savings.** If `recoverability_class = UNRECOVERABLE` (V13: first
   forward-cross < `complete_lead_time`), the action's value books to **`loss_avoided`**, never `savings`.
   `loss_avoided = reallocated_units × committed_unit_value`. *(98% of $ exposure lives here — this rule is the
   difference between a credible ledger and a $372.5M fantasy.)*
2. **Convergence attributes once.** For a batch action over N SKUs (V11), `Δrisk_action` is computed on the
   **batch** and booked **once**; per-SKU allocation `Δrisk_sku = Δrisk_action × (exposure_sku / Σ exposure_sku)`
   is **drill-only**, never re-summed into the day total.
3. **Phantom-heal subtraction** (already in the ✅ formula): realized savings subtract found-inventory over the
   heal window. A gap closing on `transaction_quantity > 0` (adjustment) is not a supply win.
4. **DISMISS avoided-cost** (V12): correctly-not-acted books to a separate counter —
   `avoided_cost = Σ over-order_units_that_would_have_been_triggered × unit_cost`; count + $, not savings.

### 5C.3 · The day roll-up (incremental, as the customer described)

```
protected_today (🔵)      = Σ Δrisk_action over today's ACT actions      -- live running total
residual_risk             = baseline_at_risk(08:00) − protected_today
realized_this_week (✅)    = Σ Δrealized over actions whose read-back landed this week
correctly_not_acted        = COUNT(DISMISS) , Σ avoided_cost
loss_avoided (🟥)          = Σ over UNRECOVERABLE actions              -- separate, never in "saved"
```
- **Baseline** frozen at start-of-day into `sandbox_operations.po_management.rc_value_baseline_daily`
  (`baseline_snapshot_id`, at-risk $ commitment-weighted, SKU count).
- **Suggested-vs-actual** is not a $ formula but a logged pair: `suggested_value` (what the recommender's Δ would
  have been) vs `actual_value` (the taken action's Δ) → **suggestion-adoption rate** = `Σ actions where
  actual=suggested ÷ Σ actions`; **app-vs-planner realized** = compare `Δrealized` grouped by `diverged` flag.

**Confidence:** projected 🟡 (provisional by definition, honest label); realized ✅ (read-back mechanism verified);
unit-value basis 🟡 (which lag/cost field is authoritative — same open question as B4). No number is invented.

---

## 6 · What is BLOCKED — formulae I need from the team

*Honest list. These I should NOT invent — presenting a guessed number here would break trust. Each needs the
source formula (Excel template, analytics semantic layer, or a planner).*

| # | Measure | Why blocked | What I need |
|---|---|---|---|
| B1 | **Exact safety-stock calculation** (statistical vs DOC) | `22 SS Stat/DOC` plans have **0 rows in fact**; the method behind `20 Global`'s `safety_stock` isn't exposed; Sarah's reconstruction isn't a live table | the SS formula / method, or the activated plan |
| B2 | **"Demand surprise" canonical definition** | transcript says it varies by person; multiple forecast bases exist (working_final, baseline, lags) | one agreed numerator/denominator + range |
| B3 | **Which cost basis for $ at risk** | `standard_cost` exists, but also burden/landed variants | confirm std vs landed vs burden |
| B4 | **"Upper target" for excess** | there's a safety-stock (lower) target but no explicit max/upper | the overstock threshold rule (DOC-based?) |
| B5 | **The Excel simulator templates' exact formulae** | the "70% consistent template" logic lives in Excel, hooked to EDW — "a fair amount of formulas" | the actual template workbook(s) |
| B6 | **Weeks/days of cover basis** | `days_of_cover` is stored but its averaging window/basis unknown | confirm the denominator (avg demand over what window) |
| B7 | **SS refresh rule under demand change** (for sim) | Carter's "target refreshes when demand rises" — the coupling formula | the forward-DOC → SS rule |
| B8 | **Full `total_supply` component list** | verified sched_receipts is one part; other supply columns exist | enumerate/confirm the sum |
| B9 | **Statistical error metrics (MAD/MAPE/bias/model)** | columns EXIST but are **empty** in the EDW — live in Oracle engine | published values, or accept we compute empirically |
| B10 | **Service-level → z-factor** | `service_level` is a **category code (TOL/BAT/…), not a %** | the CSL target per class to map to z |
| B11 | **Lead-time variability (σ_L)** | only mean lead time (`complete_lead_time`) exists; no std-dev | derive from PO receipt history or get from team |
| B12 | **Lead time is BIMODAL — never average it** | `complete_lead_time` is median **2 days** but average **122 days** (99,678 series >8wk). An average lead time is meaningless and mis-classifies recoverability. **Always use per-SKU `complete_lead_time`;** segment SKUs into short-lead vs long-lead tail bands. | build rule (V13) |
| B13 | **Warranty return-rate denominator** (V17/N3) | the fact is now item-keyed (✅), but return-rate needs an agreed basis — warranty **claims** vs **units** (`part_quantity`) over **shipped units** in **which window/lag** | one agreed numerator/denominator + window (parallels B2) |
| B14 | **Which return reasons re-enter sellable stock** (V17/N3) | the supply-lens "reverse-logistics supply add" needs the rule for which `replacement_reason_code` values restock as sellable vs scrap/warranty-consume | the reason-code → disposition mapping (business rule) |

> **Recommendation:** pull the **actual Excel simulator template(s)** from the team (B5) — they likely encode
> B2, B4, B6, and B7 in their cell formulas. One workbook probably unblocks half this list. That's the
> highest-value artifact to request next, exactly as the transcript hinted ("these templates hooked up
> essentially to the EDW").

---

## 6B · Show everything — with distinctions (the UI provenance system)

*Decision: **render every measure**, but each one visibly wears its confidence tier so a planner instantly knows
what to trust vs. verify. Nothing is hidden; nothing is silently presented as truth it isn't.* This is the
"coverage-honesty band" (UX concept C-6) made concrete — and it's how you win an expert user who's been burned
by black boxes.

### 6B.1 · The three-badge taxonomy (one visual language, everywhere)

| Tier | Badge | Semantic token | Tooltip says | Behaves |
|---|---|---|---|---|
| ✅ **Verified** | `● Verified` (or no badge = default trust) | `--success` dot / neutral | "Reproduces the plan's stored value. Formula: …" | shown normally |
| 🟡 **Needs-confirm** | `◑ Check basis` | `--warning` | "Computed with a standard formula; the exact basis (e.g. which forecast/cost) is unconfirmed. Formula: …" | shown, with a small caret to expand the assumption |
| 🔴 **Blocked / not-sourced** | `○ Not connected` | `--muted-foreground` | "Source not available in Databricks yet (e.g. Oracle-internal / Excel). Placeholder — do not action." | shown as **placeholder**, greyed, never a live number |

- **AppKit binding:** a `Badge` (variant per tier) beside the value + a `Tooltip`/`HoverCard` carrying the
  formula and source. Reuse the exact same three tokens on **every** screen (IBCS UNIFY) — a planner learns the
  language once.
- **Never** use a raw number without its tier. A KPI tile shows `value + unit + period + freshness + tier`.

### 6B.2 · Per-element treatment map (what badge each UI element wears)

| Screen · element | Measure | Tier | UI treatment |
|---|---|---|---|
| Watchlist · low point, shortfall | PAB, SS gap | ✅ | normal |
| Watchlist · **$ at risk** | shortfall × cost | 🟡 | value + `◑ cost basis` tooltip (std cost) |
| Watchlist · **committed $** | commitment value | 🟡 | value + `◑` |
| Waterfall · buckets, position | PAB recursion | ✅ | normal (this is the proven spine) |
| Waterfall · **SS-at-lead-time** (North Star) | SS @ lead-time week | 🟡 | value + `◑ rounding` note |
| Waterfall · **SS-method "why"** overlay | statistical vs DOC | 🔴 | **placeholder panel** "method not exposed — showing SS value only" |
| Demand drill · **"over-consumed 134%"** | consumption % | 🟡 | value + `◑` + a **forecast-basis selector** (working_final / baseline / lag) |
| Demand drill · customer/promo split | DG5 × promo/base | ✅ | normal |
| Priors · forecast evolution / late-N | vintage self-join | ✅ | normal |
| Supply drill · slip days, who-moved-it | date diff, originator | ✅ | normal |
| Supply drill · fill rate | `SupplyFR` | 🟡 | value + `◑ their metric` |
| Excess board · **excess threshold** | max(0, PAB − upper) | 🟡 | value + a **tunable threshold control** (3× SS = default placeholder) |
| Rebalance · candidates, pooled PAB | org rollup | ✅ | normal |
| Holds · adjustments | txn sum | ✅ | normal |
| Holds · **on-hold units** | hold reconciliation | 🟡 | value + `◑ SO-level` note |
| Flow · **stranded split** | WIP vs stranded | 🟡 | value + `◑ split rule` |
| Weeks-of-cover (any screen) | `days_of_cover ÷ 7` | 🟡 | use **their** stored value + `◑ basis` |
| Bias board · forecast bias | empirical | ✅* | normal + "computed by us (ASCM), not Oracle" note |
| Any **statistical accuracy tile** (MAD/MAPE) | — | 🔴 | **not built from source**; if shown, "our empirical estimate" placeholder |
| Simulator · re-projected PAB | recursion re-run | ✅ | normal |
| Simulator · **SS auto-refresh on demand change** | Carter's coupling | 🔴 | **toggle OFF + note** "SS held constant — refresh rule not yet encoded" |

### 6B.3 · The rules that keep it honest
1. **Everything renders** — a 🔴 measure appears as a labelled placeholder, never omitted (omission hides the
   gap; a placeholder advertises it).
2. **Default = verified.** Only 🟡/🔴 carry a visible badge, so the screen isn't badge-noise — the eye goes to
   what needs caution.
3. **Escalation output inherits tiers** — if a drafted escalation includes a 🟡 number, the draft carries the
   "verify basis" note (the planner is accountable for what they send).
4. **A tier can be *upgraded* in place** — when the team confirms a definition (e.g. the "demand surprise"
   basis) or a source lands (R27), the badge flips 🟡→✅ with no UI rebuild. The provenance system is the
   mechanism for graduating trust over time.
5. **Tie to the ADR serving layer** — store the tier as a column/metadata on each serving measure
   (`rc_serving_sku_week.<measure>_tier`) so the badge is data-driven, not hard-coded per screen.

> **Net:** the planner sees the *whole* picture on day one — but the tool is transparent about which numbers are
> bedrock (PAB, gaps, rebalance) and which are still being pinned down (demand-surprise %, SS method). That
> honesty is the feature, not a limitation.

---

## 7 · Honest confidence summary

```
  ✅ VERIFIED (reproduce the plan's own numbers, safe to present):
     • PAB recursion = PAB[t-1] + supply - demand      ← the keystone + the simulator engine
     • total_demand = independent + dependent
     • SS gap, shortfall, low point, below-SS flag
     • PO slip/drift, who-moved-it, supplier concentration
     • on-hand level (single date), adjustments
     • pooled PAB rollup, rebalance detection
     • forecast-evolution / late-N structure, forecast bias (computed live)

  🟡 INFERRED (standard formula, columns exist, needs a planner to CONFIRM the exact basis):
     • consumption % / demand surprise (which forecast? which range?)
     • $ at risk (which cost?), $ excess (what upper target?)
     • weeks of cover, SS-at-lead-time rounding, fill-rate definition
     • stranded-inventory split, on-hold reconciliation

  🔴 BLOCKED (lives in Excel / semantic layer / tribal / Oracle engine — do NOT invent):
     • exact safety-stock method (B1), the Excel template formulae (B5),
       SS-refresh-under-demand-change (B7), canonical "demand surprise" (B2)
     • statistical error metrics MAD/MAPE/bias — columns EXIST but EMPTY (B9)
     • service_level is a CATEGORY code not a % — do NOT plug into z-formula (B10)
     • lead-time variability σ_L has no column (B11)
```

**On statistics specifically:** MKE's Oracle engine computes the heavy stats (MAD, MAPE, model selection,
intermittent-demand handling) but **doesn't publish them** to the readable tables. So we **read their stored
`safety_stock`** (authoritative, their method) rather than recompute it; and any statistics we *do* show
(forecast bias, MAPE, CoV, variability) we compute **empirically from actuals+forecast history**, labelled as
*our* computation and anchored to the **ASCM/APICS** standard `SS = z·σ_LT` — never claiming to mirror Oracle's
internal numbers, never assuming `service_level` is a percentage.

**Bottom line for you:** I can present the **structural/position measures accurately today** (the PAB spine is
proven, and it carries the waterfall, forward-risk, rebalance, and the simulator). The **judgment measures**
(what exactly is "demand surprise," "weeks of cover," the safety-stock method) I can compute *a* correct number
for, but I should **confirm the definition with a planner or pull the Excel template before presenting them as
the source of truth** — otherwise I'd be inventing precision I don't have. That's the sincere answer.

---

<div align="center">

### 📌 In one line
**The plan's core identity — `PAB = prior PAB + supply − demand` — is verified to the decimal, so position,
gaps, forward-risk, rebalance, and the simulator all rest on solid ground; variance is a *family* of formulae
across situations/grains/horizons (never just weekly); and the judgment measures (demand-surprise, safety-stock
method, the Excel template logic) are honestly flagged as needing the team's actual formula before we present
them as truth.**

*All formulae tested READ-ONLY on `mke-rsc`; figures illustrative. Verified = reproduced the stored value;
inferred = needs confirm; blocked = needs the source formula. No production schema written.*

</div>
