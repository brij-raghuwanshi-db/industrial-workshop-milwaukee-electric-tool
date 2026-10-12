<div align="center">

# 🎨 UX Design **v3** — Scenario Screens (the Nervous System)

### From a shortage workbench to a supply-chain nervous system — screens for what the *data* revealed

**Companions:** [`supply_day3_ux_design_v2.md`](supply_day3_ux_design_v2.md) · [`supply_day3_data_scenarios.md`](supply_day3_data_scenarios.md) · [`supply_day3_joins_er_diagram.md`](supply_day3_joins_er_diagram.md)
**What changed since v2:** v1/v2 designed the *shortage* workbench (the planners' told story). Six live data probes ([scenarios doc](supply_day3_data_scenarios.md)) proved the same tables hold **excess ($452M), rebalance (1,646 cases), plan nervousness, supplier-slip concentration, forecast bias, and stranded inventory ($127M).** v3 designs a screen for each — every one on data confirmed present today.

</div>

---

> ## 🎯 The reframe
> The workbench is no longer "the shortage tool." It's a **control tower with six lenses on one shared data
> spine** — each lens a different question, audience, and action, all reading the same conformed star
> ([join model](supply_day3_joins_er_diagram.md)). The shortage lens (v1/v2) ships first to earn trust; these
> five are the highest-value *next* lenses.
>
> ```
>   ONE DATA SPINE (20_supply_daily · 10_demand_daily · PO · inventory · commitment)
>        │
>        ├─ Lens 1: SHORTAGE   (v1/v2 — planners, "we're short")
>        ├─ Lens 2: EXCESS     (finance, "$452M tied up")
>        ├─ Lens 3: REBALANCE  (planners, "transfer, don't buy" — 1,646)
>        ├─ Lens 4: STABILITY  (planners, "stop reacting to thrash")
>        ├─ Lens 5: SUPPLIER   (sourcing, "4 suppliers = 78% of slips")
>        └─ Lens 6: DEMAND-BIAS (demand team, "customers +60–190%")
> ```

**Screen status:** each backed by a live-confirmed figure. Component bindings at the end (§C).

| # | Screen | Scenario | Audience | Live signal |
|---|---|---|---|---|
| S1 | Excess & Overstock board | Sc.1 | Finance / planner | $452M, 3.2× shortage |
| S2 | Rebalance recommender | Sc.2 | Planner | 1,646 transfer cases |
| S3 | Plan Stability monitor | Sc.3 | Planner | 2,668 nervous series |
| S4 | Supplier Reliability scorecard | Sc.4 | Sourcing | top 4 = 78% slips |
| S5 | Forecast Bias / FVA board | Sc.5 | Demand team | +60–190% bias |
| S6 | Inventory Flow / Stranded view | Sc.6 | Ops / planner | $127.5M in mfg |

---

## 📑 Contents
- [S1 · Excess & Overstock board](#s1--excess--overstock-board)
- [S2 · Rebalance recommender](#s2--rebalance-recommender)
- [S3 · Plan Stability monitor](#s3--plan-stability-monitor)
- [S4 · Supplier Reliability scorecard](#s4--supplier-reliability-scorecard)
- [S5 · Forecast Bias / FVA board](#s5--forecast-bias--fva-board)
- [S6 · Inventory Flow / Stranded view](#s6--inventory-flow--stranded-view)
- [S7 · Convergence lens (DK-13)](#s7--convergence-lens-dk-13--the-case-single-cause-triage-misses)
- [C · Component + table bindings](#c--component--table-bindings)
- [D · How they connect — the unified navigation](#d--how-they-connect)
- [E · Build priority](#e--build-priority)

---

## S1 · Excess & Overstock board
*The mirror of the shortage watchlist. Genre: control-tower + analytic. Audience: finance + planner.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  💰 EXCESS & OVERSTOCK        [Network ▾]  [Plan ▾]              $452M tied up ▲  📤 PDF   │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ◆ $ excess (peak/qtr)  ◆ SKUs > 3× SS   ◆ Excess : Shortage    ◆ Aging > 26wk cover     │
│    $452M                  20,543            3.2 : 1  ⚠            (E&O risk) ▸             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  MOST OVERSTOCKED — ranked by $ tied up          [ by $ | by weeks-of-cover | aging ]     │
│  SKU      Desc        On-hand  SS target  Excess$   Wks cover   Driver          Action    │
│  7xxx ▸   PACKOUT…    12,400   1,800      $1.2M     34 wk       fcst dropped     [de-stock▾]│
│  8xxx ▸   M12 …       9,900    900        $0.8M     41 wk       over-received    [slow PO ▾]│
│   Excess = max(0, PAB − upper target).  Freshness: snapshot Mon 08-31 · READ-ONLY source  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Same waterfall pattern, inverted** — instead of "how did we fall below SS," it's "how did we pile up above it": driver = forecast dropped / over-received / demand shifted (same buckets, opposite sign).
- **Actions are the opposite of expedite:** de-stock, slow/cancel inbound PO, reallocate, promote. Ties to the Rebalance recommender (S2).
- **Aging → E&O:** weeks-of-cover > threshold flags obsolescence risk — the finance conversation.
- **Data (live):** `20_supply_daily` PAB vs `safety_stock`; $ via `dim_series_ext_vw.standard_cost`. Confirmed $452M / 20,543 SKUs.

---

## S2 · Rebalance recommender
*The highest-ROI screen. Genre: analytic + action. Audience: planner. "Transfer, don't buy."*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  🔄 REBALANCE — short here, excess there (same network)         1,646 opportunities        │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  SKU 2941 · M18 FUEL · Olive Branch network                                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │  ORG      Position vs SS      Units                                                 │   │
│  │  2014 DC  ▓▓▓░░░ SHORT -300   ◄── need                                              │   │
│  │  1080 Mfg ▓▓▓▓▓▓▓▓ EXCESS +900 ──► transfer 300  ✅ covers the short                │   │
│  │  2012 OB  ▓▓▓▓▓ on target                                                           │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│   💡 Recommended: TRANSFER 300 units 1080 → 2014  (vs. buying — saves $ + lead time)      │
│      [ Draft transfer order ▸ ]   [ compare to PO expedite ]                              │
│   ⚠ transfer feasibility: lane exists (14,772 hist. 1080→2014), lead ~1wk                 │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **The insight made actionable:** before the shortage workbench proposes an expedite, this checks *is there excess of this SKU elsewhere in my network?* → transfer beats buy.
- **Wires:** `20_supply_daily` org-level gap + `designated_org_code` rollup + `transfer_orders` (lane feasibility). Confirmed **1,646 near-term** cases.
- 🎯 **DK-9 — extends to FORWARD rebalance:** over the next quarter, **7,508** projected crossings are coverable by in-network transfer (4.6× the near-term count). So S2 pairs with Coming-Risk (v2 B.1): not just "you're short now, transfer" but "you'll cross at wk39, transfer now to prevent it." Lanes verified dense (2012↔2013 65k/34k, 1080→2012 30k, 1080→2014 15k).
- **Action:** drafts a transfer to Lakebase `action_request` (type = transfer); the writeback taxonomy's "convert to a rebalance/transfer" path.

---

## S3 · Plan Stability monitor
*Genre: analytic. Audience: planner. "Stop reacting to a target that'll move back."*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  📉 PLAN STABILITY — nervous SKUs (target thrash)              2,668 nervous / 66k tracked │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  SKU 3xxx · target for wk44, last 5 snapshots                                             │
│   SS target:  120 → 340 → 130 → 360 → 140     🔁 changed 5×, swing 200%   NERVOUS         │
│   ▁▇▁▇▁  ← thrash pattern                                                                  │
│   💡 Don't trigger a buy off this week's spike — it reversed 4× already.                   │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │ Nervous-SKU list   [ revisions ▾ | reversals | frozen-zone breaches ]              │   │
│  │ SKU     revisions(8wk)  directional reversals  in-frozen-zone?  avg swing%          │   │
│  │ 3xxx    5               4                       ⚠ yes           200%                │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│   Most SKUs are stable (~3% avg swing) — this is a CONCENTRATED watch, not systemic.      │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Prevents wasteful action** — the room's own worry ("don't trigger a buy off a signal already covered"). Flags the 2,668 thrashers so planners ignore noise.
- **Honest framing:** the header states most SKUs are stable — this is a targeted watch (matches the ~3% avg finding).
- **Wires:** `20_supply_daily` self-join across `process_date` for a fixed `date_key` (revisions, range, reversals). Confirmed 2,668.

---

## S4 · Supplier Reliability scorecard
*Genre: analytic + repository. Audience: sourcing. "4 suppliers = 78% of slips."*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  🏭 SUPPLIER RELIABILITY                                    top 4 = 78% of supplier slips  │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  Supplier          Self-slips(YTD)  Share   Fill rate  SupplyMiss   Chronic  QBR          │
│  Acme Cordless  ▸   408             32% 🔴   88% ▼      3            🔁       [schedule ▸] │
│  Bolt Ind.      ▸   231             18%      94%        1                     [schedule ▸] │
│  Cordex         ▸   226             18%      91% ▼      2            🔁                     │
│  … (long tail)                                                                            │
│   OTIF to requested vs promise ▾   ·   who-warned-us? (SUPPLIER-initiated = accountable)   │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Turns tribal "this supplier is unreliable" into a ranked, evidenced scorecard** — targeted QBRs, not blanket pressure.
- **Wires:** `purchase_order_change_orders` (`change_order_originator_type='SUPPLIER'`, concentration) + `ops_scorecard_fill_rate_vw` (`SupplyFR`, `SupplyMiss`). Confirmed top-4 = 78%.
- **Research-aligned** (§9 of join doc): OTIF to *both* requested and promise date; capture originator — the industry OTIF pattern.

---

## S5 · Forecast Bias / FVA board
*Genre: analytic. Audience: demand team. "Customers chronically +60–190%."*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  🎯 FORECAST BIAS — actual vs late-3 forecast, by customer   [Demand plan ▾ 10 ACC]       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  Customer (DG5)   Actual    Late-3 fcst   Bias      Direction                             │
│  TTI NZ           67,442    23,261        +190% 🔴  chronic UNDER-forecast                 │
│  PCS              541,265   257,964       +110% 🔴  chronic UNDER-forecast                 │
│  OTHER NA         760,129   371,871       +104% 🔴                                         │
│  …                                                                                        │
│   💡 These aren't noise — they're structural bias. Root of the shortages planners fight.  │
│   [ Flag to demand: re-baseline ▸ ]   FVA: does planner override help or hurt? ▾          │
│  ⚠ Filter the RIGHT demand plan: 10 TOL / PRT / ACC / HND / QP (product-line split)        │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Attacks the root cause upstream** — systematic under-forecast *causes* the shortages. Fix here, the fire shrinks.
- **FVA angle** (from research): does each process step (planner override, promo input) improve or worsen accuracy? Rank by bias, feed demand handoff (Gap 7) with evidence.
- **Wires:** ✅ **prefer the governed `prod_operations.demand.fact_forecast_accuracy`** (DK-7) — has
  `planner_bias` **and** `system_bias` (a bias-split we couldn't derive empirically), error + cost, rolling-6,
  by DG5×item×date. Fall back to empirical `10_demand_daily` (`shipments_history` vs late-3) only for lag-flex.
- **Reason-code drill (DK-8):** clicking a biased customer shows the **governed reason codes**
  (`dim_forecast_accuracy_reason_codes` — Promo strategy change, Constrained Ordering, Timing, E&O…) — not
  invented buckets; `ai_classify` maps any free-text into these.
- **Planner-vs-system bias is a new lens:** the governed fact separates *planner* bias from *system* bias —
  answer "is it the model or the human override?" (the FVA question) directly.
- **⚠ Carries the demand-plan correction** — empirical path must target `10 TOL/PRT/ACC/HND/QP`, not "20 Global."
- **⚠ Fixes a known limitation (DK-10):** the existing accuracy dashboard is locked to lag-3; this screen adds
  lag-1..6 flexibility.

---

## S6 · Inventory Flow / Stranded view
*Genre: schematic (layout follows the physical network). Audience: ops / planner. "$127M in mfg, not DC."*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  📦 INVENTORY FLOW — Olive Branch network                     $127.5M stranded in mfg      │
├───────────────────────────────────────────────────────────────────────────────────────┤
│    1080 MFG            ──transfer──►     2014 / 2012 DC          ──ship──►  CUSTOMER       │
│    $127.5M  ⚠                            $705M                                             │
│    13.7M units                           43.4M units                                      │
│    ├ finished, not moved ⚠ (stranded)                                                     │
│    ├ WIP (legitimate)                                                                     │
│    └ in-transit (coming)                                                                  │
│   💡 Finished goods sitting in 1080 inflate network health but can't ship from the DC.    │
│      [ show stranded SKUs ▸ ]  [ rebalance → S2 ]                                          │
│   split: on_hand_cost (populated) + OPEN transfer_orders (in-transit; cost cols are empty) │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Schematic layout** — mirrors the real mfg→DC→customer flow, so "where is it stuck" is spatial.
- ⚠️ **DK-11 CORRECTION — the in-transit/WIP cost columns are EMPTY.** Verified live: `inventory_days_on_hand.in_transit_cost` / `work_order_wip_cost` / `received_not_put_away_cost` are **$0 network-wide** — only `on_hand_cost` ($1.65B) is populated. So do **not** source the flow-split from those columns.
- 🎯 **Count-integrity signal comes from `transfer_orders` instead:** **240,197 Open** transfers (vs 445,638 Closed) carry `status` + `scheduled_ship_date` + `requested_quantity`. **An Open transfer past its scheduled ship = "projected healthy but not actually here"** — the planner's exact "it said 1080 but it had transferred" mis-count case. Flag these, don't just show an on-hand number.
- **Wires:** `inventory_days_on_hand.on_hand_cost` by org (1080/2012/2014) for the level ($127.5M in 1080 confirmed) **+ `transfer_orders` (status='Open')** for the in-transit/count-integrity overlay. Feeds S2 (stranded = transfer candidate).

---

## C · Component + table bindings
*Only components exported from `@databricks/appkit` / `@databricks/appkit-ui`; confirm via `npx @databricks/appkit docs`.*

| Screen | Key components | queryKey → confirmed source |
|---|---|---|
| S1 Excess | `Table` + `Card*` KPIs + inverted-`BarChart` waterfall | `excess_board` → `20_supply_daily` (PAB>SS) + `dim_series_ext_vw.standard_cost` |
| S2 Rebalance | `Table` + horizontal `BarChart` (org position) + `Button`→Lakebase | `rebalance` → `20_supply_daily` org gap + `designated_org_code` + `transfer_orders` |
| S3 Stability | `LineChart` (target over snapshots) + `Table` + `Badge` | `plan_stability` → `20_supply_daily` self-join on `process_date` |
| S4 Supplier | `Table` + `Badge` (chronic) + `BarChart` (concentration) | `supplier_reliability` → `purchase_order_change_orders` + `ops_scorecard_fill_rate_vw` |
| S5 Bias | `Table` + `BarChart` (bias by customer) + `Select` (plan) | `forecast_bias` → `10_demand_daily` (ship vs late-3) + `dg5_customer_scd1` |
| S6 Flow | schematic layout (`Card*` nodes) + `BarChart` (org split) | `inv_flow` → `inventory_days_on_hand` by org |

> **Notation (IBCS) carries over:** shortage=`--destructive`, excess=`--warning` (working-capital caution, not
> "bad"); same Demand/Supply/Holds tokens; actual solid, target dashed reference, projected muted. S6 uses a
> schematic (process-map) layout — the one place a spatial arrangement beats a chart.

---

## D · How they connect

The six lenses aren't separate apps — they **cross-link around the shared SKU/network context:**

```
        ┌─────────────── SHORTAGE (v1/v2 hero) ───────────────┐
        │  investigating 2941 …                                │
        │    ├─ excess of 2941 elsewhere? ───────────► S2 Rebalance
        │    ├─ is 2941's target nervous? ───────────► S3 Stability
        │    ├─ which supplier drove it? ────────────► S4 Supplier
        │    └─ is the customer chronically off? ────► S5 Bias
        └──────────────────────────────────────────────────────┘
   S1 Excess ←──── portfolio entry (finance) ────► S6 Flow (where is it?)
```
- From any shortage investigation, one click pivots to the *relevant* lens for that SKU (rebalance option, nervous-target warning, supplier record, customer bias).
- S1 and S6 are **portfolio-level entry points** for non-planner audiences (finance, ops).
- All share the network toggle, time slider, and the conformed keys — no context re-entry.

---

## E · Build priority

*The shortage workbench (v1/v2) still ships first — felt pain, trust. Then, by value-to-effort:*

| Wave | Screen | Why | Effort |
|---|---|---|:--:|
| **v3.1** | **S2 Rebalance** | highest ROI — transfer-before-buy saves cash immediately; reuses org rollup | Low-Med |
| **v3.1** | **S1 Excess** | $452M story; new finance audience; pure inversion of existing waterfall | Low |
| **v3.2** | **S5 Forecast Bias** | attacks the *root cause* of shortages; strongest demand-handoff evidence | Med |
| **v3.2** | **S4 Supplier Reliability** | targeted QBRs; pairs with existing supply drill | Med |
| **v3.3** | **S3 Plan Stability** | prevents wasteful action; concentrated so lower urgency | Med |
| **v3.3** | **S6 Inventory Flow** | flow visibility; needs WIP/in-transit split to be precise | Med |

> **Recommendation:** ship **S2 + S1 right after the v1/v2 hero path.** They're the cheapest (both reuse the
> `20_supply_daily` + rollup you've already built), they open a new audience (finance) and a new *action*
> (transfer), and together they reframe the product from "shortage tool" to "control tower" — which is the
> story that wins the room.

### AI-optional layer on the scenario screens (show both)
Each scenario screen is fully deterministic; AI (live-tested — see
[`supply_day3_ai_functions_opportunities.md`](supply_day3_ai_functions_opportunities.md)) is an optional add:
- **S4 Supplier** — without AI: ranked slip/fill-rate scorecard. With AI: `ai_classify` structures free-text
  PO-change reasons into cause categories.
- **S5 Forecast Bias** — without AI: empirical bias (actual vs late-3, computed live). With AI: `ai_forecast`
  second-opinion projection, labelled experimental.
- **S1 Excess / S6 Flow** — without AI: full deterministic $ + flow. With AI: `ai_gen` narrative summary of the
  overstock/stranded story for the finance/ops reader.
All AI outputs carry the 🟡 provenance badge; baseline ships first, AI as a toggle.

---

## S-classify · The classifier layer (V10–V13) — the spine under every lens
*Before any lens recommends anything, each flagged SKU carries pre-computed tags (ADR §7.1a serving columns)
that decide **whether and how** to act — and gate RCA depth:*
- **recoverability_class** (V13): `RECOVERABLE` (winnable) vs `UNRECOVERABLE` (committed loss — 98%, $372.5M) →
  UNRECOVERABLE ⇒ damage-control (TRANSFER 20% / ALLOCATE 80%), not a PO.
- **action_verdict** (V12): ACT / WATCH / DISMISS — only ~34% ACT; 66% cushion-dip DISMISS.
- **temporal_class** (V10): acute / chronic / nervous.
- **convergence_score** (V11): # co-firing causes.
> **RCA-gating:** full root-cause runs **only** where `recoverability_class=UNRECOVERABLE & material` or
> `temporal_class=chronic` — fast-triage the recoverable, DISMISS the cushion dips. This is what turns a
> 10,700-flag alarm into a ~3,600-row worklist. Every scenario lens below reads these columns; it doesn't
> re-derive them.

## S7 · Convergence lens (DK-13) — the case single-cause triage misses
*Genre: analytic + control-tower. Validated live (V11): 52% of shortages are multi-cause, 1 supplier behind
3,035 SKUs, 6,933 crossing one week. The single-cause "likely cause chip" under-serves the majority of the book.*

### S7a · Multi-cause SKU — residual-gap tracker (on the hero waterfall)
```
┌─ 2941 · gap −900 · ⚠ 3 causes converging ───────────────────────────────┐
│  Cause          contribution   actionable-by   lever            residual │
│  🟦 Demand +540  ▓▓▓▓▓▓ 60%     demand team     re-baseline  ─┐           │
│  🟧 Supply +270  ▓▓▓ 30%        me (planner)    pull-in       │           │
│  🟪 Holds  +90   ▓ 10%          quality         release       │           │
│  ─────────────────────────────────────────────────────────────           │
│  apply pull-in ▸ covers 300 → RESIDUAL 600 (demand-owned) → [Flag demand] │◄ residual tracker
│  [ One combined escalation covering all 3 ▸ ]                             │
└───────────────────────────────────────────────────────────────────────────┘
```
- Replaces the single "likely cause" winner with **combined contribution bars**; each action closes part of the
  bar and shows **who owns the residual**. One escalation, not three tickets. *(Wires: the three variance buckets
  from V2/V3/V4, ranked by contribution × ownership.)*

### S7b · Constraint-first pivot — "1 root, not 3,035 fires"
```
┌─ 🎯 CONSTRAINTS behind my shortages    [ by Supplier | Component | DC ]   │
│  Techtronic Cordless   ▓▓▓▓▓▓▓▓▓▓  3,035 SKUs · $XXM · N committed   [▸]  │◄ one action, not 3,035
│    └ allocate capacity: run these top-value SKUs first ▸                  │
│  Milwaukee Mfg Corp    ▓▓  218 SKUs                                  [▸]  │
│   ⚠ supplier names normalized (TTI LIMITED/LTD/LMTD merged)              │
└───────────────────────────────────────────────────────────────────────────┘
```
- **Changes who acts (planner → sourcing).** One constraint action + a **capacity-allocation** sub-view ranking
  SKUs *within* the supplier. This is the biggest time-saver. *(Wires: shortage SKUs → `dim_series_ext_vw.origin_supplier_name`, normalized.)*

### S7c · Risk-wave view (on Coming-Risk)
```
┌─ 📅 RISK WAVE — SKUs first-crossing per week                              │
│  wk37 ████████████████████ 6,933  ⚠ CAPACITY CRUNCH — impact-rank+defer   │
│  wk38 ██ 612    wk40 █ 441   …                                            │
│  [ work top-N by $/committed ]  [ log deferred tail ]  [ smooth ▸ ]       │
└───────────────────────────────────────────────────────────────────────────┘
```
- Aggregates the **week-level load** (not a flat SKU list); flags spike weeks; supports work-top-N + **logged
  deferral** of the tail + pull-forward smoothing. *(Wires: forward first-cross week from V9, grouped.)*

### Cross-cutting: **convergence score** on the watchlist
Add `# active causes` to each watchlist row — a 3-cause SKU at $2M outranks a 1-cause SKU at $2M. Persist as a
serving column (`convergence_score`).

**Guardrails (per DK-13):** convergence actions move *batches* → **propose, never auto-execute** (rules rank &
allocate, human disposes); **supplier-name normalization is a prerequisite** for S7b.

**Build priority:** **S7b (constraint pivot) is the highest-ROI convergence element** — one click collapses
3,035 fires into one sourcing action; ships right after the hero path alongside S2/S1. S7a and S7c follow.

---

## S-classify+ · Classifier axes added (N/DK, validated V15–V26)
*The spine above (recoverability · verdict · temporal · convergence) gains five priority/confidence axes.
All are ADR §7.1a serving columns — read, never re-derived, by every lens below.*
- **criticality_class** (DK-16): A/B/C from `inventory_abc_class`. **The $-weight** on every verdict — A-class $67.8k/SKU (2.1× C). A-class committed acute ⇒ top of ACT; C-class recoverable ⇒ auto-DISMISS.
- **lifecycle_class** (N1): `NPD` / `TRANSITION` / `MATURE` from item master. **Suppresses false-chronic** on 71.5k transition / 4.0k NPD SKUs → launch playbook, not a chronic flag.
- **demand_class** (DK-18): `INTERMITTENT` / `SMOOTH` (ADI proxy). **The confidence gate** — ~24% intermittent → measures shown with a low-confidence band, no over-reaction to one spike.
- **dormant_flag** (DK-17): last-ship recency. Opens the **excess/E&O** half of the book ($545M never-shipped, $16M dormant).
- **intentional_hold** (DK-20): `safety_stock_managed_flag='Yes'`. **Excludes $450M managed stock** from "excess" — don't fight the plan.

> These don't add screens so much as **re-rank and calibrate** everything. The watchlist sort key becomes
> *criticality × recoverability × convergence*, not raw gap. Confidence bands follow `demand_class`. The
> excess board (S1) and the new S8 read `dormant_flag` + `intentional_hold`.

## S8 · Portfolio Health headline + Sankey (DK-20 / V26)
*Genre: infographic + repository. The exec/S&OP view above the SKU grind. Live: 54% aligned.*
```
┌─ 📊 INVENTORY ALIGNMENT — 54% healthy  ▲ +2pt WoW ────────────────────────┐
│  Total on-hand $X.XB                                                       │
│   ├─ ✅ Aligned      54%  ▓▓▓▓▓▓▓▓▓▓▓                                       │
│   ├─ 🟡 At-risk      NN%  ▓▓▓▓                                              │
│   ├─ 🔴 Short        NN%  ▓▓                                                │
│   └─ 🟣 Excess/E&O   NN%  ▓▓▓  ($545M never-shipped · $16M dormant)         │
│  [ Sankey ▸  Total $ → ABC class → health status ]                         │◄ drill visual
└───────────────────────────────────────────────────────────────────────────┘
```
- One **portfolio-health KPI** (unit=$/%, period=current snapshot, comparison=WoW, freshness=latest `process_date`)
  that trends week-over-week; the **Sankey** flows Total $ → A/B/C → {aligned, at-risk, short, excess} so an exec
  sees where the dollars sit *and* how healthy each band is. *(Wires: `20_supply_daily` gap × `inventory_days_on_hand.on_hand_cost` × `inventory_abc_class`. Sankey = AppKit chart primitive; if unavailable, a stacked-bar fallback per ABC class.)*
- **States:** loading → `Skeleton` on the bar + Sankey; empty (no snapshot) → `Empty` "no supply snapshot for this week"; partial (Unclassified ABC 37%) → show an explicit "Unclassified" band, never silently drop it.

## S9 · Dormant & E&O lens (DK-17 / V23) — the other half of the balance sheet
```
┌─ 🟣 DORMANT / EXCESS — $16M dormant · $545M never-shipped ────────────────┐
│  SKU     org    on-hand$   last-ship   ABC   hold?      verdict            │
│  4931-.. 2120   $1.2M      412d ago    A     —          🔴 review E&O      │
│  2804-.. 2012   $0.4M      never       C     managed    ⚪ intentional     │◄ hold excluded from E&O
│  [ group by: org | ABC | age-band ]   [ propose disposition ▸ ]           │
└───────────────────────────────────────────────────────────────────────────┘
```
- The shortage app was **blind to value not moving**; this makes it first-class. **`intentional_hold` rows render
  as ⚪ and are excluded from the E&O total** — a managed reserve is not obsolescence. Disposition proposals route
  through the same governed proposal queue (never auto-execute). *(Wires: last-ship recency + `on_hand_cost` + `inventory_abc_class` + `safety_stock_managed_flag`.)*

## S10 · Found-inventory / heal badge (N4 / V18) — did we really fix it?
```
┌─ Investigation · SKU 2941 — RESOLVED ─────────────────────────────────────┐
│  gap closed wk36.  ✅ real fix: PO 4471 pulled in (+540)                    │
│  ⚠ heal check: +90 from a signed inventory adjustment (cycle count)        │◄ phantom-heal warning
│     → 15% of the recovery was a correction, not new supply.                │
└───────────────────────────────────────────────────────────────────────────┘
```
- On any resolved/healing SKU, decompose the recovery into **real supply vs signed adjustment** (found inventory).
  A heal that's mostly a cycle-count correction gets a ⚠ so a planner doesn't bank a phantom win. *(Wires: signed
  `inventory_material_transaction.transaction_quantity` over the heal window; +81.9M found / 25k events confirmed.)*

## S-badges · Lifecycle & criticality on the hero + watchlist (N1 · DK-16 · DK-18)
- **Criticality badge** `Ⓐ/Ⓑ/Ⓒ` next to every SKU id — colored by ABC, tooltip = $/SKU. Drives the default sort.
- **Lifecycle chip** `🌱 NPD` / `🔁 TRANSITION` — when present, the chronic-slipper flag is **replaced** by "launch — thin history expected," and the RCA gate does **not** escalate it as chronic.
- **Confidence band** on any measure for an `INTERMITTENT` SKU — mean/CV shown greyed with "lumpy demand — low confidence" so nobody over-reacts to a single-period spike.

> **Component note (AppKit):** all badges = `Badge` with `colorPalette` semantic tokens (no hex); the alignment
> KPI = composed KPI (Text + delta arrow + freshness caption), *not* a prebuilt card; Sankey = chart primitive
> with stacked-bar fallback. Proposal actions reuse the S7 "propose, never auto-execute" pattern + Lakebase queue.

## S12 · Root-cause × week heatmap — recursive drill navigator (DK-22)
*Genre: analytic + control-tower. The visual instantiation of the classifier layer: horizontal band = chronic
cause, vertical band = convergence week, lone hot cell = acute. Onclick recurses into the next level — until the
child stops banding, then it becomes a list.*

```
┌─ 🔥 CAUSE × WEEK — 20 Global · snapshot 2026-09-03 · $-weighted, signed ───┐
│  breadcrumb:  All ▸ (click a crumb to pop up)                              │
│                 wk37  wk38  wk39  wk40  wk41  wk42  wk43                    │
│  Supplier TTI   ▓▓▓▓  ▓▓▓▓  ▓▓▓▓  ▓▓▓   ▓▓▓   ▓▓    ▓     ◄ horizontal=CHRONIC│
│  Demand 10 TOL  ░░    ▓▓▓▓▓ ▓▓    ░░    ░     ░     ░     ◄ lone cell=ACUTE  │
│  Holds/quality  ░     ░     ▓▓▓▓  ▓▓▓▓  ▓▓▓   ▓▓    ▓                        │
│  Org pool 2120  ▓▓▓   ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓  ▓▓▓   ▓▓▓   ▓▓                       │
│                       ↑ vertical band = bad WEEK = convergence wave (S7c)  │
│  🔴 short  🔵 excess   intensity = commitment-$    [click any cell ▸]       │
└────────────────────────────────────────────────────────────────────────────┘
   click TTI × wk39  ▼
┌─ All ▸ TTI ▸ wk39 ────────────────────────────────────────────────────────┐
│  (rows swap to next level; weeks stay)   Pool 2120 ▓▓▓▓  Pool 1080 ▓▓  …    │
└────────────────────────────────────────────────────────────────────────────┘
   click Pool 2120  ▼   (14 member orgs — verified bands, 33,467→0)
┌─ All ▸ TTI ▸ wk39 ▸ Pool 2120 ─────────────────────────────────────────────┐
│  inv-org 8841 ▓▓▓▓   inv-org 8843 ▓▓▓   …                                   │
└────────────────────────────────────────────────────────────────────────────┘
   click an org with < ~4 banding child rows  ▼   AUTO-DEGRADE
┌─ … ▸ inv-org 8841 —  SKU LIST (leaf: drill target, not a heatmap) ─────────┐
│  SKU     gap$    ABC   cause    recover   verdict   [investigate ▸]         │
│  2941   $412k    Ⓐ    supply   commit    🔴 ACT                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**The interaction (onclick → next-layer subset), with the measured rules:**
- **Recurse the row dimension, keep the weeks.** Portfolio → product-line/supplier → designated-pool →
  member inv-org. Each click **inherits the parent's filters** (cause + week + org) and appends a **breadcrumb**
  crumb (click a crumb to pop back up).
- **Stop-rule (measured, not fixed-depth):** recurse only while the child has **≥ ~4 populated rows that band**;
  below that → the leaf is the **SKU list** (verified: designated-pool → 14 member orgs bands; ABC-within-org
  collapsed to 1 all-NULL row → list). **Never a SKU × week heatmap** (~99% empty).
- **⚠ Data guardrails (from live probing):** child dimension comes from a **populated** column — criticality via
  the `dim_series_ext_vw` join, **not** the all-NULL `local_planning_abc_code` fact column; **fixed snapshot
  vintage** across all levels so numbers don't shimmer; **$-weighted + signed** color at every level; convergence
  cells **split fractionally** (S7a) so multi-cause weeks don't inflate.
- **Weeks-by-volume are near-uniform** (live: peak/mean 1.33×) — so the story is deliberately in **row
  concentration + $**, not week count. This is why the heatmap is cause/supplier/org-rowed, not a volume grid.

**Component plan (AppKit):**
- Grid → chart **Heatmap** primitive (or a composed `Table` of `Badge`-colored cells if the heatmap primitive
  lacks onclick); diverging `colorPalette` (red↔blue), intensity bound to commitment-$; **no hex**.
- Onclick → `useAnalyticsQuery` re-fires with the appended filter (`sql.*` params carry cause/week/org + the
  frozen `process_date`); breadcrumb = `Breadcrumb`; each hop is a new `queryKey` so back/forward is cache-cheap.
- Leaf SKU list → server-paginated `Table` reusing the watchlist row (criticality Ⓐ/Ⓑ/Ⓒ, recoverability,
  verdict) with **[investigate ▸]** into the hero waterfall (Screen B).
- **States:** loading → `Skeleton` grid; **empty** (no variance in this subset) → `Empty` "no misses for this
  filter — pop up a level ▸"; **all-null child** → skip that dimension, fall to the next populated one or the
  list (never render an empty band); **error** → inline `Alert`.

**Data readiness:** ✅ — pre-agg `sandbox_operations.po_management.rc_cause_week_heat` = `20_supply_daily`
(weeks × cause-bucket × pool/org) × commitment-$ (`fact_sop_commitment`), one frozen `process_date`. Drill hops
re-query the same pre-agg with tighter filters; the leaf list drops to the live single-org detail. No new source.
**Complements S7c** (forward "when") — this is the 2-D backward+forward "what cause, over time."

---

<div align="center">

### 📌 v3 in one line
**Six lenses on one data spine turn the shortage workbench into a supply-chain nervous system — excess,
rebalance, stability, supplier, bias, and flow — each a real screen on data confirmed present today, each
cross-linked to the shortage investigation, and the cheapest two (Rebalance + Excess) are the ones that
reframe the whole product.**

*All figures live READ-ONLY on `mke-rsc`; wireframes are ASCII sketches; every element binds to a real AppKit
primitive (§C) and a confirmed source. Serving tables in `sandbox_operations.po_management`; state in Lakebase.*

</div>
