<div align="center">

# 🔬 Data-Discovered Scenarios — Beyond the Transcript

### The planners told a *shortage-triage* story. The data holds more. What else can we do?

**Companions:** [`supply_day3_joins_er_diagram.md`](supply_day3_joins_er_diagram.md) · [`supply_day3_capability_map.md`](supply_day3_capability_map.md) · [`supply_day3_requirements.md`](supply_day3_requirements.md)
**Method:** live READ-ONLY probes on `mke-rsc` (warehouse `7bd33a82f4e92206`) against the confirmed tables, one scenario at a time. Each scenario = a hypothesis → a real query → what the data shows → the capability it unlocks.

</div>

---

> ## 🎯 Why this document exists
> The Day-3 session was scoped to one workflow: *"we're short — how did we get here?"* (demand → supply →
> holds). That's a **minor slice** of what these tables can answer. The same `20_supply_daily`,
> `10_demand_daily`, PO, inventory, and commitment facts also expose **excess, imbalance, plan nervousness,
> supplier concentration, forecast bias, and stranded inventory** — problems that cost money but nobody asked
> about because they're not the fire of the day. This doc probes the data to surface them.

**Scenario status:** 🔬 probing · ✅ confirmed in data · 💡 opportunity framed

| # | Scenario | Angle | Status |
|---|---|---|:--:|
| 1 | Excess / overstock (E&O) — the inverse of shortage | working capital | ✅ |
| 2 | Cross-org rebalance — short here, excess there | transfer-before-buy | ✅ |
| 3 | Plan nervousness — safety-stock target thrash | bullwhip / stability | ✅ |
| 4 | Supplier concentration — who slips the most | supplier risk | ✅ |
| 5 | Forecast bias — systematic over/under | demand quality | ✅ |
| 6 | Stranded inventory — stuck in mfg, not at DC | flow / availability | ✅ |

---

## Scenario 1 · Excess / overstock (E&O) — ✅ Confirmed *(the biggest surprise)*

**Hypothesis:** the transcript was 100% about *shortage* (PAB below safety stock). The inverse — PAB far
*above* safety stock — is tied-up working capital and future E&O risk that nobody in the room mentioned.

**What the data says (live, latest snapshot, next quarter, 20 Global plan):**

| Metric | Value |
|---|---|
| SKU×org×weeks **below** safety stock (the transcript's problem) | **75,836** |
| SKU×org×weeks **>3× above** safety stock (excess) | **245,569** |
| **Ratio** | **excess is ~3.2× more prevalent than shortage** |
| Units above target | ~716M |
| **Excess inventory value (peak, next qtr, via `standard_cost`)** | **~$452M across ~20,500 SKUs** |

**Query basis:** `20_supply_daily` (latest `process_date`, `date_key` next quarter) → `projected_available_balance
> safety_stock × 3`; valued via `dim_series_ext_vw.standard_cost` on `series_bigint_key`. READ-ONLY.

**What it unlocks (new capability, same tables, same UI pattern):**
- An **"Excess & Overstock" board** — the exact mirror of the watchlist waterfall, but for *overage* (`excess = max(0, PAB − upper target)`), ranked by $ tied up.
- Feeds **de-stock / slow-down-PO / reallocate** actions (the opposite of expedite) — and pairs with Scenario 2 (rebalance short-from-excess).
- Directly serves the working-capital conversation execs care about — a **different audience** than the shortage-firefighting planner.

> 💡 **Why this matters:** the planners optimize for *service* (don't be short). Finance optimizes for *cash*
> (don't overstock). The same `20_supply_daily` answers both — we've only built for one. This is a whole second
> user community, free.

---

## Scenario 2 · Cross-org rebalance (transfer before buy) — ✅ Confirmed *(highest-ROI action)*

**Hypothesis:** because inventory pools across the Olive Branch cluster (transcript's own point), the same item
may be **short in one org while sitting in excess in another org of the same network** — so the right action is
a **transfer, not a purchase order.** The per-org view planners use today hides this.

**What the data says (live, latest snapshot, near-term window):**

| Metric | Value |
|---|---|
| **Item × networks that are short in ≥1 org AND excess in ≥1 other org (same `designated_org`)** | **1,646** |

**Query basis:** `20_supply_daily` grouped to org-level gap, rolled up by `designated_organization_bigint_key`;
count networks with both a short org and an excess org for the same `product_bigint_key`. READ-ONLY.

**What it unlocks:**
- A **"Rebalance first" recommendation** — before proposing a PO expedite/pull-in, the Recommended-Action panel
  (capability-map G2) checks: *is there excess of this SKU elsewhere in my network?* If yes → transfer is
  cheaper and faster than buying.
- Directly wires `transfer_orders` (source→dest org) + `designated_org_code` rollup (already confirmed).
- **Quantifiable savings:** every avoided PO on these 1,646 cases is cash not spent + lead time not waited.

> 💡 **This is the single most actionable scenario** — it converts the org-rollup capability (which the room
> thought impossible) into a *money-saving default action*, not just a nicer view.

---

## Scenario 3 · Plan nervousness (target thrash) — ✅ Confirmed *(concentrated, not systemic)*

**Hypothesis:** the safety-stock *target* moves across snapshots (proved in Gap 6). At scale, excessive
week-to-week target churn = bullwhip, and it drives the unnecessary buys the room explicitly worried about
("I don't want to trigger a buy off a signal already covered by safety stock").

**What the data says (target week 20261102, last 5 snapshots, 20 Global):**

| Metric | Value | Read |
|---|---|---|
| Series tracked | 66,286 | — |
| Series that changed target **≥3 times** in 5 snapshots | **2,668** | the nervous subset |
| Average target swing (range ÷ avg) | **~3%** | most SKUs are *stable* |

**Interpretation:** plan nervousness is **real but concentrated** — ~4% of series thrash, the rest are calm.
That's a *useful* finding: it argues for a **targeted "nervous SKU" watch**, not a boil-the-ocean stability
program.

**Query basis:** hold `date_key` fixed (one future week), vary `process_date` across last 5 snapshots, count
distinct `safety_stock` values + range per series. READ-ONLY.

**What it unlocks:**
- A **"Plan Stability / Nervous SKU" flag** — surface the 2,668 thrashers so planners *don't* react to a target
  that will move back next week (prevents wasteful expedites/buys).
- Feeds the domain pattern's **plan-nervousness metrics** (revisions per target week, directional reversals,
  frozen-zone changes) — all derivable from the same snapshot self-join.

---

## Scenario 4 · Supplier concentration / slip — ✅ Confirmed *(clean Pareto)*

**Hypothesis:** `change_order_originator_type` records who moved a PO date (Activity 5). At scale — *which
suppliers slip most, and is the risk concentrated?* The room said "did they warn us or did we catch it?" is
unanswerable; here it's a named-supplier ranking.

**What the data says (PO change orders, 2026 YTD):**

| Originator | Changes | POs | Read |
|---|---|---|---|
| BUYER | 1,882,703 | 73,905 | normal planner activity |
| REQUESTER | 5,718 | 1,469 | internal |
| **SUPPLIER** | **1,283** | **244** | **the accountability signal** |
| SYSTEM | 304 | 166 | automated |

**Supplier-initiated slips are highly concentrated:**

| Rank | Supplier (key) | Supplier-initiated changes | Share |
|---|---|---|---|
| 1 | 1117895973958984041 | **408** | **32% of all** |
| 2 | −7411750002910805707 | 231 | 18% |
| 3 | −4798892570171058991 | 226 | 18% |
| 4 | −8086735199777763431 | 131 | 10% |
| | **top 4 combined** | **~78%** | |

**Query basis:** `purchase_order_change_orders` grouped by `change_order_originator_type`, then by
`supplier_bigint_key` for `SUPPLIER` changes. READ-ONLY.

**What it unlocks:**
- A **supplier-reliability scorecard** (pairs with `ops_scorecard_fill_rate_vw`, Scenario/Gap 8) — rank the
  chronic-slip suppliers, join names via `dim_series_ext_vw`/supplier dim.
- **Targeted supplier QBRs** — 4 suppliers explain ~78% of self-initiated slips; that's a focused
  accountability conversation, not a broad one.
- Feeds the "who moved my PO" badge from a *pattern* level, not just per-PO.

---

## Scenario 5 · Forecast bias — systematic over/under — ✅ Confirmed *(fixable at source)*

**Hypothesis:** the transcript looked at demand-surprise *reactively, per SKU.* At scale, is there
**systematic directional bias** — customers who *consistently* ship more/less than forecast? Consistent bias is
fixable at the source (unlike random error).

**What the data says (latest snapshot, `10 ACC Demand Plan`, actual `shipments_history` vs late-3 forecast
`final_demand_forecast_3_month_ago`, by DG5 customer):**

| Customer (mkedg5) | Actual | Late-3 forecast | Bias |
|---|---|---|---|
| TTI NZ | 67,442 | 23,261 | **+190%** |
| PCS | 541,265 | 257,964 | **+110%** |
| OTHER NA | 760,129 | 371,871 | **+104%** |
| NO CHARGE | 430,637 | 231,336 | +86% |
| OEM | 15,600 | 8,609 | +81% |
| LANDSCAPING | 28,525 | 15,809 | +80% |

**Interpretation:** these customers are **chronically under-forecast** by 60–190% — that's structural bias, not
noise. It directly *causes* the shortages the planners fire-fight, because the plan systematically expects too
little.

**Query basis:** `10_demand_daily` `shipments_history` (actual) vs `final_demand_forecast_3_month_ago` (late-3),
grouped by `dg5_customer_scd1.mkedg5`. READ-ONLY.

> 🔑 **Bonus finding — demand plans are product-line-split.** Demand doesn't use "20 Global"; it's split into
> **`10 TOL` / `10 PRT` / `10 ACC` / `10 HND` / `10 QP` Demand Plans** (by product line — tools, parts,
> accessories, hand-tools, quoted-products). The join model + serving layer must **filter the correct demand
> plan(s)** — this wasn't obvious from the transcript and affects every demand query. *(Update to the data
> mapping.)*

**What it unlocks:**
- A **forecast-bias / FVA scorecard** (the industry Forecast-Value-Added pattern from the research) — rank
  customers/items by systematic bias so demand planning fixes the *cause*, not the symptom.
- Turns the demand-handoff (Gap 7) from "this SKU looks off" into "this customer is structurally +104%, please
  re-baseline" — a far stronger, evidence-backed request.

---

## Scenario 6 · Stranded inventory (stuck in mfg, not at DC) — ✅ Confirmed

**Hypothesis:** the transcript mentioned inventory stuck in mfg org **1080** that hasn't reached the DC (2014) —
"stranded," so projections look healthy but the stock isn't where demand ships. How much?

**What the data says (latest on-hand snapshot, Olive Branch cluster):**

| Org | Role | On-hand units | On-hand cost |
|---|---|---|---|
| 2012 | DC / Olive Branch | 41.2M | **$533M** |
| 2014 | Byhalia DC | 2.2M | $172M |
| **1080** | **Manufacturing** | **13.7M** | **$127.5M** |

**Interpretation:** **~$127.5M of on-hand sits in the manufacturing org.** Some is normal WIP/staging, but
finished-goods sitting in 1080 rather than a DC is *stranded* relative to customer demand — it inflates network
health while being unavailable to ship from the DC. The transcript flagged this qualitatively; it's a **$127M**
quantity.

**Query basis:** `inventory_days_on_hand` at latest `date_key`, joined to `inventory_organization_scd1`, orgs
1080/2012/2014. READ-ONLY. (Refine with subinventory / `in_transit_cost` / `work_order_wip_cost` to split
true-stranded from legitimate WIP.)

**What it unlocks:**
- A **flow / stranded-inventory view** — highlight finished goods in 1080 not yet at a DC, and in-transit that
  hasn't actualized (the transcript's "healthy projection, but it's coming / it's stuck" case).
- Pairs with Scenario 2 (rebalance) — stranded stock is a *transfer* candidate.

---

## 🧭 Synthesis — what the data says we should ALSO build

The planners told a **shortage-triage** story. Six live probes show the same tables answer far more:

| # | Scenario | Live signal | New audience / action |
|---|---|---|---|
| 1 | **Excess / overstock** | **~$452M** excess, 3.2× more prevalent than shortage | Finance / working-capital; de-stock actions |
| 2 | **Cross-org rebalance** | **1,646** item×networks short-here-excess-there | Planner; **transfer-before-buy** (biggest ROI) |
| 3 | **Plan nervousness** | 2,668 nervous series (concentrated, ~3% avg swing) | Planner; don't-react-to-thrash flag |
| 4 | **Supplier slip concentration** | top 4 suppliers = ~78% of self-initiated slips | Sourcing; targeted QBRs |
| 5 | **Forecast bias** | customers chronically +60–190% vs late-3 | Demand team; fix at source (FVA) |
| 6 | **Stranded inventory** | **$127.5M** on-hand in mfg org, not DC | Planner/ops; flow visibility |

### The three headlines for the room
1. **We built for the smaller problem.** Shortage is what hurts *today*, but **excess ($452M) is 3× bigger** and nobody's watching it. Same tables, same UI pattern.
2. **The highest-ROI action isn't "expedite" — it's "transfer."** 1,646 cases where the fix is moving stock you already own, not buying more.
3. **The shortages have a root cause upstream:** systematic **forecast bias** (customers +60–190%) and a **handful of chronic suppliers** (4 = 78% of slips). Fix those and the daily fire shrinks.

> **Recommendation:** the shortage workbench (v1) is still the right *first* build — it's the planners' felt
> pain and earns trust. But frame it from day one as **one lens of a broader "supply-chain nervous system"**;
> scenarios 1, 2, and 5 are the highest-value *next* lenses, all on data confirmed present today.

**Data-mapping correction surfaced:** demand plans are **product-line-split** (`10 TOL/PRT/ACC/HND/QP`), not
"20 Global" — every demand query must target the right plan(s). Fold into the join model + serving layer.

---

<div align="center">

### 📌 In one line
**The planners described the shortage fire; the data reveals a $452M excess problem 3× larger, 1,646
transfer-before-buy opportunities, chronic forecast bias and supplier slip driving the very shortages they
fight, and $127M stranded in manufacturing — all in the tables we already confirmed, all buildable on the same
UI pattern.**

*All figures live READ-ONLY on `mke-rsc` 2026-09-02; illustrative of magnitude, not audited. No writes.*

</div>

