<div align="center">

# 🔀 Cross-Pollination — Peer MRO App → MKE Workbench

### Distilling a peer Databricks app (different domain, adjacent problem) for what we can reuse — and what we hadn't considered

**Source:** screenshots of the peer app's **"MRO Inventory — Inventory Optimization Dashboard"** (an MRO spare-parts
optimization app on Databricks Apps). **Stance:** *don't deviate from our MKE work* — distill transferable ideas,
confirm against MKE data, and flag genuine gaps. Every "we have this" / "this is new" is checked live on `mke-rsc`.

</div>

---

> ## The one-paragraph read
> The peer app solves a **different problem** (MRO/spare-parts stocking-parameter optimization: is SAP's
> Safety-Stock / Reorder-Point / Max right?) than ours (finished-goods shortage root-cause). But the **skeleton
> is strikingly parallel** — health-status segmentation, a per-SKU review screen, a **current-vs-recommended
> parameter delta with a working-capital $**, and a **propose → accept/override/no-change → queue → implement →
> audit** workflow. Several of its concepts we already have; a few we **hadn't considered** and MKE has the data
> for them. The single most valuable steal is the **parameter-recommendation + proposal-queue workflow**.

---

## 1 · What the peer app shows (from the screenshots)

| Screen | What it does |
|---|---|
| **Dashboard** | "Inventory alignment 29%; 2,518 materials need review = $1.43M optimization opportunity." Plant Health Snapshot ($ total / active / non-moving / non-moving % / MoM change). **Sankey: Inventory Value by Health Status** → Healthy / Overstock / Critical-Stockout / At-Risk-Below-ROP / BOM-Standby / Dormant / Strategic-Reserve. "Where is the money held?" overstock Pareto (152 materials = 80%). |
| **SKU Review** | per-material: Plant, **Criticality, Critical-Part, MRP-Type/Lot-Sizing, Demand-Class (Intermittent), Health (Excess-Overstock)**; 36-mo inventory trend (receipts/consumption/**returns**/on-hand); lifecycle dates (first movement / last receipt / last consumption); Key Metrics (current stock, avg consumption/mo, **months coverage**, rounding value, **stock value, overstock value**). |
| **Parameter Comparison** | **Current SAP vs Recommended vs Delta** for SS / ROP / MAX / Lead-Time, with **"Working Capital Opportunity: $72,085 if MAX adopted"** (or "Additional investment needed: $8,090"). |
| **Initiate Proposal** | radio: **Accept Model Recommendations / Override with Custom Values / Reviewed–No Change**, + justification, + Submit. |
| **Proposal Queue** | table of proposals: material, plant, submitter, type (accept/override/no-change), curr vs proposed ROP/MAX/LT/Crit, status (PROPOSED), comments. |
| **Implementation Tracker / Audit Log** | (nav) — closed loop from proposal → implementation → audit. |

---

## 2 · Cross-map: what we ALREADY have vs what's NEW

*(checked live on MKE `mke-rsc`)*

| Peer-app concept | MKE status | Evidence |
|---|:--:|---|
| Health-status segmentation (Healthy/Overstock/Critical/At-Risk/Dormant…) | ✅ **have, richer** | our **classifier layer** (V10–V13): severity, ACT/WATCH/DISMISS, recoverable/unrecoverable, acute/chronic/nervous |
| Overstock / excess $ + "where's the money held" Pareto | ✅ **have** | V7/S1 Excess board ($452M, weeks-of-cover) |
| Returns as a trend series | ✅ **have (validated)** | V17/N3 (3.2M warranty recs) + V18/N4 found-inventory |
| Months-of-coverage / weeks-of-cover | ✅ **have** | V7 (`days_of_cover`); measures doc |
| Consumption / avg usage | ✅ **have** | V3 consumption |
| **Criticality / Critical-Part** | 🆕 **NEW — data present** | `dim_series_ext_vw.inventory_abc_class` (A 55,781 / B 11,299 / C 3.05M), `global/local_planning_abc_code`, `items_scd1.item_class` |
| **MRP-Type / planning method / lot-sizing** | 🆕 **NEW — data present** | `inventory_planning_method`, `safety_stock_planning_method`, `fixed_lot_multiplier`, MOQ family |
| **Demand class = Intermittent** (Croston-style) | 🆕 **NEW — partially seen** | the stat-forecast `intermittent_indicator` (empty in fact, V-measures B9) — needs a computed CoV/ADI classifier |
| **Dormant / obsolete / E&O aging** | 🆕 **NEW — data present** | `dim_series_ext_vw.obsolete_date` populated on **1.14M series**; + lifecycle dates (first movement / last receipt / last consumption) |
| **Parameter recommendation: current-SAP vs recommended SS/ROP/MAX/LT + delta** | 🆕 **NEW — the big one** | we have `safety_stock` (current) but **no "recommended" engine**; MAX/ROP as explicit params not yet modeled |
| **Proposal queue + accept/override/no-change + working-capital $** | 🆕 **NEW workflow** | our Lakebase `action_request` is the *plumbing*; the **parameter-proposal pattern** is a new action *type* |
| **Inventory alignment %** (a single health KPI) | 🆕 **NEW framing** | a nice single north-star metric we don't surface |
| **Strategic Reserve / BOM-Standby** health states | 🆕 **NEW** | intentional-hold categories we don't model (we'd mis-flag these as excess) |

---

## 3 · What we hadn't considered — the genuinely new lenses (data-backed)

### 🆕 A · Criticality / ABC as a first-class classifier axis — **highest transfer value**
The peer app leads every SKU with **Criticality + Critical-Part**. We rank by $ and recoverability but **not by
criticality** — yet MKE has `inventory_abc_class` (A/B/C/D, live) and `items_scd1.item_class`. **This belongs in
our classifier layer:** an A-class critical part below safety stock is a different priority than a C-class one at
the same $. *Action: add `criticality_class` to `rc_serving_sku_week`; weight the ACT ranking by it.*

### 🆕 B · Dormant / obsolescence / E&O aging — **a whole health state we're missing**
the peer app's Sankey has **Dormant** and their SKU shows **last-consumption date**. MKE has **`obsolete_date` on
1.14M series** + lifecycle dates. Our Excess board (V7) finds *overstock*, but **dormant/obsolete is different** —
stock that isn't moving *at all* (no consumption for N months) heading to write-off. *Action: a
dormant/E&O lens using `obsolete_date` + last-consumption; distinct from active overstock.* (Complements N4/N3.)

### 🆕 C · Demand-class: intermittent vs smooth (Croston territory) — **changes the math**
The peer app explicitly tags **Demand-Class: Intermittent**. This matters because our verified formulae (safety
stock, consumption, forecast) **assume smooth-ish demand** — but MKE has intermittent SKUs (the empty
`intermittent_indicator`, V-measures B9). *Action: compute an ADI/CoV demand classifier; for intermittent SKUs,
flag that Normal-based SS and % consumption are unreliable (use Croston/fill-rate) — a data-quality guard on our
own measures.*

### 🆕 D · The parameter-recommendation workflow — **the biggest structural idea**
the peer app's core loop is: **model recommends SS/ROP/MAX/LT → planner sees current-SAP-vs-recommended-vs-delta +
the working-capital $ → accept / override / no-change → proposal queue → implement → audit.** Ours is
*root-cause → escalate*; theirs is *parameter-optimize → propose-writeback*. **These are complementary halves of
the same control tower:** we explain *why we're short today* (execution/S&OE); they fix *whether the stocking
parameters are right* (planning/S&OP). MKE has the pieces — `safety_stock` (current), `dim_series_ext_vw` (MOQ,
lead time, planning method) — but **no recommendation engine and no parameter-proposal action type.** *Action:
a "parameter review" mode + a `parameter_proposal` Lakebase action type (accept/override/no-change), reusing our
`action_request` plumbing and DK-14's verdict pattern.*

### 🆕 E · Two smaller framings worth stealing
- **"Inventory alignment %"** — a single north-star health KPI ("29% aligned, $1.43M opportunity"). We have all
  the parts; we don't roll them into one number. Cheap, exec-friendly.
- **Strategic-Reserve / BOM-Standby** as *intentional-hold* health states — inventory held on purpose (safety-
  critical spares, BOM dependencies). **We'd currently mis-flag these as excess/dormant.** Need an
  intentional-hold flag so the do-nothing/DISMISS logic (V12) doesn't cry wolf on deliberate reserves.

---

## 3b · 🌊 The Sankey — "Inventory Value by Health Status" (we can do this, richer)

the peer app's standout visual is a **Sankey**: Total Inventory $ → Active/Non-Moving → health states
(Healthy / Overstock / Critical-Stockout / At-Risk / BOM-Standby / Dormant / Strategic-Reserve). **We can build
this for MKE — and better, because our classifier layer has more honest states.** Tested live:

**MKE on-hand $ flow (real, latest snapshot, DC orgs only):**
```
                                   ┌─ A-class      $232.2M  (7,945 SKUs)
  TOTAL ON-HAND $ ~$1.64B ──┬──────┼─ B-class      $4.2M    (402)
   (finished-goods DCs)     │      ├─ C-class      $1,034.6M (105,218)
                            │      └─ Unclassified $370.0M  (42,865)
                            │
                            └─ lifecycle split ──┬─ Active           ~$1.64B
                                                 └─ Obsolete/Dormant  $0.9M (66)  ← from obsolete_date
```
→ Confirmed: `on_hand_cost` by **ABC class × lifecycle** flows cleanly. This is a genuine multi-level Sankey.

**The MKE version — 3 levels, richer than the peer app's (proposed):**
```
  Total On-Hand $ ──► ABC class (A/B/C) ──► Health state (from OUR classifier)
                                            ├─ Healthy
                                            ├─ At-risk (below SS, recoverable)      ← V13
                                            ├─ Committed loss (unrecoverable)        ← V13
                                            ├─ Excess / Overstock                    ← V7
                                            ├─ Dormant / Obsolete (obsolete_date)    ← DK-17
                                            └─ Intentional hold (Strategic/BOM)      ← DK-20 (once flagged)
```
- **Why it beats theirs:** the peer app's states are static categories; ours are the **validated classifier states**
  (recoverable vs committed, acute/chronic, do-nothing-DISMISS) — so the Sankey shows not just *where the money
  is* but *how much is winnable vs lost vs deliberately held.*
- **AppKit binding:** AppKit-ui ships a Sankey/flow chart (confirm exact name via `npx @databricks/appkit docs`);
  bind `queryKey → rc_serving_sku_week` aggregated `SUM(on_hand_cost)` grouped by `abc_class` → `health_state`.
  Semantic tokens per state (green healthy / warning excess / destructive committed-loss / muted dormant).
- **⚠ Data guards (from our validation):** filter **non-DC orgs** (8000 Supplier-Inv, 2092 3PL — V20/N6) or the
  flow is polluted; use **on-hand $** at a single date (never sum across dates — V5); segregate component/bulk UoM.
- **Home:** the **Dashboard / Control-Tower landing** (the "where is the money held?" exec view) — pairs with the
  worklist. This is a strong candidate for the day-in-the-life 8:00 AM screen's companion.

*Added to the backlog as part of DK-20 (health-status Sankey + inventory-alignment KPI + intentional-hold states).*

## 4 · What does NOT transfer (stay disciplined)

- The peer app is **MRO spare parts** (intermittent, criticality-driven, stocking-parameter optimization). MKE P1
  is **finished-goods shortage root-cause** (higher-volume, demand-driven, S&OE execution). Don't import their
  *primary workflow* wholesale — import the *concepts*.
- Their "recommended parameters" imply an **optimization model** (MEIO/statistical). Per our own measures doc
  (B1, statistical SS is blocked) and the room's "don't over-predict" warning, **a recommendation engine is a
  later, evidence-gated build** — not the Wave-0 shortage slice.
- Their MAX/ROP min-max policy is an MRO stocking model; MKE's plan is projection-based (PAB recursion). Both
  valid; don't conflate the two inventory philosophies.

---

## 5 · Net adds to our backlog (proposed DK-16…DK-20 — candidates, need their own validation)

| # | New requirement (from a peer app) | Data ready? | Priority |
|---|---|:--:|---|
| **DK-16** | **Criticality / ABC as a classifier axis** — weight ACT ranking by A/B/C | ✅ `inventory_abc_class` live | 🔴 high transfer value |
| **DK-17** | **Dormant / obsolescence / E&O lens** — no-movement + `obsolete_date`, distinct from active overstock | ✅ `obsolete_date` on 1.14M | 🟡 |
| **DK-18** | **Demand-class (intermittent vs smooth)** — ADI/CoV; guards our SS/consumption formulae | 🟡 compute (indicator empty) | 🟡 (integrity) |
| **DK-19** | **Parameter-recommendation + proposal-queue** (current-vs-recommended SS/ROP/MAX/LT + working-capital $, accept/override/no-change) | 🟡 current params yes; recommender = new | 🟡 (big, later — the S&OP half) |
| **DK-20** | **"Inventory alignment %" north-star KPI** + **intentional-hold states** (Strategic-Reserve/BOM-Standby) so do-nothing doesn't mis-flag | ✅ / 🟡 | 🟢 cheap + prevents false flags |

**The single highest-value steal:** **DK-16 (criticality axis)** — cheap, data-ready, and it fixes a real hole
(we rank by $ but not by how *critical* the part is). **The most strategic:** **DK-19** — the parameter-proposal
loop is the **planning/S&OP counterpart** to our execution/S&OE root-cause tool; together they're a full control
tower. But it needs a recommendation engine, so it's a deliberate later phase.

> **Discipline note:** these are **candidates distilled from a peer app + a live data check** — each needs its own
> validation pass (like V1–V21) before it becomes committed scope. Logged so we capture the learning without
> deviating from the MKE Wave-0 path.

*All MKE data checks READ-ONLY on `mke-rsc` / warehouse `7bd33a82f4e92206`, 2026-09-03.*
