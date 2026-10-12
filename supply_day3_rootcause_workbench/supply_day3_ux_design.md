<div align="center">

# 🎨 Supply Root-Cause Workbench — UX Story & Wireframes

### The front-end that answers *"How did we get here?"* in minutes, not hours

**Companions:** [`supply_day3_requirements.md`](supply_day3_requirements.md) · [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) · source [`supply_day3_discussion.md`](supply_day3_discussion.md)
**Grounded in:** the `databricks-app-design` skill (genre → composition → IBCS notation → AppKit components → required states) + the project's control-tower / "action-not-state" domain pattern.
**Platform:** Databricks App (AppKit / React), reading `sandbox_operations.po_management` Gold + Genie; writing action state to Lakebase.

</div>

---

> ## 🎯 The story in one screen
>
> A product/channel partner drops the question: **"We're in a bad position on 2941 — how did we get here?"**
>
> Today the planner opens **5–7 systems** (Oracle SQL dashboard, supply simulator, consumption Power BI, priors Power BI, supplier Excel, SharePoint PO status, their own saved snapshots), spends **up to ~2 hours**, and hand-assembles a **two-bullet escalation email** from tribal knowledge.
>
> **The workbench replaces that hunt with one guided funnel:**
>
> ```
>   PICK the SKU/network  →  SEE the risk  →  TRIAGE the cause  →  DRILL the driver  →  SEND the story
>   (Watchlist)             (Waterfall)      (Demand/Supply/     (by customer/PO/     (escalation
>                                             Holds strip)         hold)                draft + log)
> ```
>
> **North Star (agreed in the room):** the waterfall **starts at projected safety stock at lead time**, and every bucket is a **variance to that reference**. The tool doesn't predict the future yet — it **explains the past**.

---

## 📑 Contents
1. [Who / what decision / design frame](#1--frame)
2. [Genre & the narrative spine](#2--genre--narrative-spine)
3. [The screens (wireframes)](#3--the-screens)
   - 3.1 [Watchlist / Control Tower](#31--screen-a--watchlist--control-tower)
   - 3.2 [Root-Cause Investigation (the hero)](#32--screen-b--root-cause-investigation-the-hero-screen)
   - 3.3 [Driver drill-downs](#33--screen-c--driver-drill-downs-demand--supply--holds)
   - 3.4 [Escalation output](#34--screen-d--escalation-output)
   - 3.5 [Action & outcome log](#35--screen-e--action--outcome-log)
   - 3.6 [**Value & Impact (the "why it's worth it" page)**](#36--screen-f--value--impact)
4. [Creative concepts — the ideas that make it more than a dashboard](#3b--creative-concepts)
5. [Cross-cutting controls](#4--cross-cutting-controls-time-network-genie)
6. [Component plan (AppKit binding)](#5--component-plan--appkit-binding)
7. [Notation rules applied](#6--notation-rules-applied-ibcs)
8. [Required states](#7--required-states-non-negotiable)
9. [What maps to real data vs what's blocked](#8--data-readiness-per-screen)
10. [How value is achieved & measured (the model)](#8b--how-value-is-achieved--measured)
11. [Build sequence & tradeoffs](#9--build-sequence--tradeoffs)

---

## 1 · Frame

| | |
|---|---|
| **Audience** | Supply planners (expert, do this ~once/day), + the product/channel partner who asks the question |
| **The decision** | *Why* is this SKU in a bad position, and what do I tell people / do about it? |
| **Primary task** | Root-cause triage → standardized escalation. **Investigate, not admire.** |
| **Refresh cadence** | Weekly Monday plan snapshot (matches `20_supply_daily`); on-hand daily |
| **Device** | Desktop, dual-monitor (planners keep many windows) — dense is OK if notation is disciplined |
| **Genre** | **Analytic** (investigation/drill-down), with an **embedded control-tower** entry page |

> 💡 **The one lesson that shapes everything (from project memory):** an operational page must show
> **change + verb + $**, not just levels. "On-hand = 30" is a chart. **"Fell 904 units below safety
> stock beginning wk36; primary driver: Home Depot over-consumed +101 units"** is a decision. Every
> tile below leads with the *movement and its driver*, never a bare number.

---

## 2 · Genre & narrative spine

The transcript **is** the information architecture. The planner's own triage order becomes the screen order:

```
 TRANSCRIPT BEHAVIOR                          →  SCREEN
 ─────────────────────────────────────────────────────────────────────────
 "weekly plan review, top missing items"      →  A. Watchlist (what needs attention)
 "how did we get here? / risk period"         →  B. Waterfall + likely-cause triage (HERO)
 "check demand first: consumption + priors"   →  C1. Demand drill (by DG5, promo/base, late 1-6)
 "then supply: requested vs promise, who?"    →  C2. Supply drill (PO slip + originator)
 "then holds / adjustments / quality"         →  C3. Holds drill
 "the two-bullet email I send"                →  D. Escalation output (draft + send)
 "no log today; we want one"                  →  E. Action & outcome log
```

**Structure = hierarchical** (overview → drilldown), **layout = stratified** (headline story on top,
drivers below). One highlight style for the *main* driver; everything else neutral.

---

## 3 · The screens

Legend for wireframes: `[ ]` control · `▓` filled/actual · `░` open/forecast · `◆` KPI tile · `▸` drill affordance

---

### 3.1 · Screen A — Watchlist / Control Tower
*Genre: embedded control-tower. Answers "what should I look at first?" Replaces the Oracle "top missing items" weekly review.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  Supply Root-Cause Workbench            [Network ▾ Olive Branch]  [Plan ▾ 20 Global]  👤 │
│                                                                        signed in: leo@…  │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ◆ Items at risk      ◆ Units short (net)   ◆ $ at risk        ◆ New this week           │
│    47  ▲6 vs last wk     128,400  ▲12%         $2.1M  ▲$310k       9  ▸                   │
│    (below safety stock)  (network, wk36–wk48)  (std cost × short)  (crossed into risk)    │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  TOP MISSING ITEMS — ranked by $ at risk        [search SKU…]  [ Mine ▾ ]  [ ⚙ columns ] │
│  ┌─────────┬──────────────────┬────────┬─────────┬──────────┬───────────┬─────────────┐ │
│  │ SKU     │ Description       │ Low pt │ Wks     │ Likely   │ $ at risk │ Trend (8wk) │ │
│  │         │                   │ (units)│ at risk │ cause    │           │             │ │
│  ├─────────┼──────────────────┼────────┼─────────┼──────────┼───────────┼─────────────┤ │
│  │ 2941▸   │ M18 FUEL …        │ -837   │ thru Oct│ 🟦 Demand│ $412k     │ ▁▂▃▅▇ ▼     │ │
│  │ 4811▸   │ PACKOUT …         │ -1,240 │ 6 wks   │ 🟧 Supply│ $388k     │ ▂▂▃▄▆ ▼     │ │
│  │ 3697-22▸│ M18 2PC COMBO KIT │ -560   │ 3 wks   │ 🟪 Holds │ $190k     │ ▃▃▂▄▅       │ │
│  │ …       │                   │        │         │          │           │             │ │
│  └─────────┴──────────────────┴────────┴─────────┴──────────┴───────────┴─────────────┘ │
│   Freshness: plan snapshot Mon 2026-08-31 · on-hand 2026-09-02 06:00 · READ-ONLY source  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**What each element does & why:**
- **4 KPI tiles** — each shows *value + Δ vs last week + unit + period + provenance*. `$ at risk` = `short units × std cost` (from `dim_series_ext_vw`). Not levels — **movement**.
- **Likely-cause chip** — a *pre-computed first guess* (Demand / Supply / Holds) so the planner starts triage already oriented. This is the transcript's "triage by most-likely" encoded. Chip color = the semantic family reused on every screen (UNIFY).
- ⭐ **Classifier badges (validation V10–V13) — the column that makes the list a *worklist*.** Each row carries:
  a **recoverability badge** `🟢 RECOVERABLE` (winnable — lever exists) vs `🔴 UNRECOVERABLE` (breach inside the
  lead-time fence — a committed loss; **98% of flags, $372.5M** — verified live); an **action-verdict** `ACT /
  WATCH / DISMISS` (only ~34% are ACT — 66% are the cushion doing its job); and a **convergence score** (# active
  causes). **Default sort = ACT + RECOVERABLE + $, so the planner sees the winnable fires first, not the
  10,700-row noise.** All are pre-computed serving columns (per the ADR classifier layer). *Without these, the
  watchlist is an alarm; with them, it's a triaged queue.*
- **Trend sparkline + ▼** — 8-week direction of the low point; the ▼ = worsening.
- **"Mine" filter** — planners own SKU portfolios; default to theirs.
- **Row click ▸** → Screen B for that SKU.

> **Why a table, not cards:** this is a ranked lookup/triage list — IBCS says table with integrated bar/sparkline + clear sort. Server-side sort/paginate (47 today, thousands at scale).

---

### 3.2 · Screen B — Root-Cause Investigation *(the hero screen)*
*Genre: analytic. This is the whole value proposition — the waterfall + the likely-cause triage in one view. Replaces the supply simulator + the planner's mental model.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ ‹ Watchlist   2941 · M18 FUEL …    [Network ▾ Olive Branch (1080+2012+2014)]            │
│                                     Time: [◀ wk28 ●────────── wk44 ▶]  [Week|Month]      │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  MESSAGE-IN-TITLE (the answer, stated):                                                  │
│  ▸ "2941 fell 904 units below safety stock at wk36; primary driver: DEMAND —             │
│     Home Depot over-consumed +101 units (134% of forecast) over the last 4 months."      │
├────────────────────────────────────────────┬──────────────────────────────────────────┤
│  WATERFALL — how we got to the gap           │  LIKELY CAUSE (triage strip)             │
│  start = projected safety stock @ lead time  │  ┌──────────────────────────────────┐   │
│                                              │  │ 🟦 DEMAND        +101u   ▓▓▓▓▓▓▓�7│▸ │   │
│   SS@LT ─┐                                   │  │    over-consumption + fcst raise  │   │
│    904   │▓▓                                 │  ├──────────────────────────────────┤   │
│          └──┐demand ▼101                     │  │ 🟧 SUPPLY        -40u    ▓▓ 20%   │▸ │   │
│             └──┐supply ▼40                   │  │    PO 380… slipped 21 days        │   │
│                └──┐holds ▼18                 │  ├──────────────────────────────────┤   │
│                   └───► GAP -904 (wk36) 🔴   │  │ 🟪 HOLDS/ADJ    -18u    ▓ 10%    │▸ │   │
│   ░░░ projected ending PAB ░░░               │  │    quality hold, 2014 DC          │   │
│  [ underlying rows ▾ ]                       │  └──────────────────────────────────┘   │
│                                              │  contribution = share of total variance  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  POSITION OVER TIME (actual vs plan vs safety stock)          scenario marks →           │
│   units                                                                                  │
│    ▓ = on-hand actual   ─ ─ safety stock (target)   ░ = projected PAB                     │
│   ┌────────────────────────────────────────────────────────────────────────────┐        │
│   │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─SS─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│        │
│   │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒░░░░░░░░░░░░░░░░  ◄ crosses below SS at wk36           │        │
│   └────────────────────────────────────────────────────────────────────────────┘        │
│     wk28      wk32      wk36 🔴      wk40      wk44         [ + add PO receipt ▾ ]         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**What each element does & why:**
- **Message-in-title** — the *stated finding*, not a label. This is the two-bullet email, pre-drafted, at the top. (IBCS SAY.)
- **Waterfall** — the North Star. Bridge from **safety stock at lead time** → subtract each variance bucket → land on the **gap**. Each step is a bucket the planner can click. This is exactly what Carter/Eric asked for.
- **Likely-cause triage strip** — the three buckets ranked by contribution, each a **▸ drill**. Reuses the watchlist chip colors (UNIFY). The planner's "check demand, then supply, then holds" made visible and clickable.
- **Position-over-time** — actual on-hand (▓ solid = AC), safety stock (─ ─ dashed reference = target), projected PAB (░ = the open/forecast portion). The **wk36 crossing** is annotated — the risk period. Time flows left→right (IBCS).
- **"+ add PO receipt / simulate"** — a *seed* for the future simulator (R21): override an incoming supply line (e.g. supplier really 750/wk) and see the line re-project. Present but clearly a later phase.
- ⭐ **Recoverability banner + RCA-gating (V13/DK-15).** The screen header states the **recoverability class** and
  routes the effort accordingly:
  - `🟢 RECOVERABLE` (breach after the lead-time fence) → **fast triage** — pick the lever, act, move on.
  - `🔴 UNRECOVERABLE` (breach inside the fence — 98% of flags) → **do NOT expedite a PO** (it can't arrive).
    Switch to the **damage-control path**: `TRANSFER` if in-network excess exists (20% of cases — the winnable
    subset), else `ALLOCATE / notify / accept + log as lost battle` (80%). And this is where **full RCA is
    warranted** *if material* — because the value is learning *why it became unrecoverable* to prevent the next
    one, not fixing this one.
  - **Chronic** (V10) → the waterfall opens a **systemic-fix** framing (SS realism / re-source), not an expedite.
  So the hero screen doesn't just explain — it tells the planner **whether this is even winnable, and therefore
  how much analysis it deserves.** RCA depth is *gated by class*, never run blindly on all 10,700 flags.

> **Why waterfall + triage side-by-side:** the transcript wants *both* "explain the number" (waterfall)
> and "which lever" (triage) at a glance, without a page switch. CONDENSE only what's compared together.

---

### 3.3 · Screen C — Driver drill-downs (Demand · Supply · Holds)
*Opened as a right-side **drawer** (detail-on-demand) over Screen B, so the planner keeps the waterfall in context. Three variants, one per bucket.*

#### C1 · Demand drill *(the P1 slice — ~60% of issues)*
```
┌─ DEMAND — why demand drove the gap ────────────────────────────  ✕ ┐
│  [ Consumption | Priors (forecast evolution) ]     ← two tabs      │
│                                                                    │
│  ▸ CONSUMPTION tab:  "Over-consumed 134% over last 4 months"       │
│  ┌────────────────────────────┬──────────┬──────────┬──────────┐  │
│  │ Customer (DG5)  │ Type       │ Forecast │ Actual   │ Δ (surprise)│
│  ├────────────────────────────┼──────────┼──────────┼──────────┤  │
│  │ HOME DEPOT      │ 🔵 Base    │ 150      │ 251  ▓▓▓ │ +101 🔴  │  │
│  │ FERGUSON        │ 🟡 Promo   │ 40       │ 44       │ +4       │  │
│  │ ACE             │ 🔵 Base    │ 30       │ 28       │ -2       │  │
│  └────────────────────────────┴──────────┴──────────┴──────────┘  │
│   grain: monthly · consumption method: shipped ÷ forecast          │
│                                                                    │
│  ▸ PRIORS tab: forecast period × snapshot vintage (late 1–6)       │
│        late6 late5 late4 late3* late2 late1  now                   │
│   Sep │ 150   150   160   180    210   240   251 ▓  (*standard=L3)  │
│   Oct │ 140   140   150   150    175   190   ░                      │
│   Nov │ 130   130   135   140    150   ░     ░    ▓=actualized      │
│         └── forecast crept up months before it actualized ──┘      │
│  [ ◀ slide vintage ]                    [ Insert into escalation ▸]│
└────────────────────────────────────────────────────────────────────┘
```
- **Consumption table** — actual vs forecast by **DG5 customer** and **demand type** (promo/base/run-rate) — *exactly* the granularity the room insisted on. Δ = "demand surprise," red when unfavorable. **"who did this?"** answered on sight.
- **Priors tab** — the forecast-evolution matrix: rows = forecast month, cols = snapshot vintage (late 1–6, standard = late 3 highlighted). Red = actualized, white = open. The **slider** (R12) walks vintages. This is the priors Power BI dashboard, rebuilt native.
- **"Insert into escalation"** — pushes this driver into Screen D.

#### C2 · Supply drill
```
┌─ SUPPLY — PO timing ───────────────────────────────────────────  ✕ ┐
│  "PO 380020278 slipped 21 days: requested 02-17 → promised 03-10"  │
│  ┌────────┬──────────┬──────────┬──────────┬────────┬───────────┐ │
│  │ PO #   │ Requested│ Original │ Current  │ Slip   │ Moved by  │ │
│  │        │ date     │ promise  │ promise  │ (days) │           │ │
│  ├────────┼──────────┼──────────┼──────────┼────────┼───────────┤ │
│  │ 380..▸ │ 02-17    │ 02-17    │ 03-10    │ +21 🔴 │ SUPPLIER  │ │◄ who moved it
│  │ 380..▸ │ 02-24    │ 02-24    │ 02-26    │ +2     │ BUYER     │ │
│  └────────┴──────────┴──────────┴──────────┴────────┴───────────┘ │
│   supplier: Acme Cordless · qty 750/wk cap  [ Insert into escalation ▸]│
└────────────────────────────────────────────────────────────────────┘
```
- **Requested vs original vs current promise + slip days** — the exact comparison from the transcript. **"Moved by"** = `change_order_originator_type` (BUYER/SUPPLIER/REQUESTER) — the thing the room *assumed wasn't in the data but is.* This is a headline capability: it answers "did they tell us, or did we catch it?"

#### C3 · Holds / adjustments drill
```
┌─ HOLDS / INVENTORY ADJ ────────────────────────────────────────  ✕ ┐
│  "18 units on quality hold at 2014 DC; 12 units lost to cycle-count"│
│  ┌──────────────┬────────┬──────────┬───────────────┬───────────┐  │
│  │ Type         │ Org    │ Units    │ Reason        │ As of     │  │
│  ├──────────────┼────────┼──────────┼───────────────┼───────────┤  │
│  │ 🟪 Quality hold│ 2014   │ 18       │ REJECTED insp │ 09-01     │  │
│  │ 🟪 Cycle adj  │ 2012   │ -12      │ CC ADJ ERROR  │ 08-28     │  │
│  └──────────────┴────────┴──────────┴───────────────┴───────────┘  │
│   ⚠ on-hold vs available is reconstructed (no native split)        │
└────────────────────────────────────────────────────────────────────┘
```
- Holds from `sales_fulfillment_hold_transactions`, adjustments from `inventory_material_transaction`, quality from `receiving_receipt_transactions`. The **⚠ note** is honest about the reconstructed available-vs-on-hold (a real data caveat from the mapping).

---

### 3.4 · Screen D — Escalation output
*The deliverable. The standardized two-bullet email, pre-drafted from the drivers the planner inserted. Replaces the ~2h hand-assembly.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  ESCALATION DRAFT — 2941 · M18 FUEL …                        [ Edit ] [ Copy ] [ Send ▸]│
├───────────────────────────────────────────────────────────────────────────────────────┤
│  Subject: 2941 supply risk — 904u below safety stock wk36, demand-driven                │
│                                                                                          │
│  • ROOT CAUSE: Home Depot (DG5) over-consumed base demand by +101 units (251 vs 150     │
│    forecast, 134%) over the last 4 months; go-forward forecast also raised within the    │
│    purchased lead time. Contributing: PO 380020278 slipped 21 days (supplier-initiated); │
│    18u on quality hold at 2014 DC.                                                       │
│  • RISK: 904 units below safety stock beginning wk36, projected to persist ~3 weeks;     │
│    $412k at risk (network, Olive Branch pooled).                                         │
│                                                                                          │
│  Actions taken / proposed:  [ Requested pull-in ▾ ]  [ + add action ]                    │
│  ────────────────────────────────────────────────────────────────────────────────────  │
│  ⚠ AI-assisted draft from governed data — verify before sending.  Sources: waterfall,   │
│     consumption (10_demand_daily), PO change orders. Generated SQL ▾                     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Two bullets, fixed structure** (R18): *root cause* (DG5 + customer + units + horizon/lag) and *risk* (units below SS + duration + $). Exactly the transcript's format.
- **Editable** before send (R19/R20). Fields trace back to the drivers.
- **Provenance footer** — sources + "verify" disclaimer; if any text is Genie-generated, the generated SQL is inspectable (AI-trust rules).
- **Send** → writes to Lakebase `integration_outbox`; does **not** claim Oracle changed until verified.

---

### 3.5 · Screen E — Action & outcome log
*The thing the team explicitly wants and doesn't have. Append-only history of what was found and done.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  ACTION & OUTCOME LOG                                    [ SKU ▾ ] [ Me ▾ ] [ Open ▾ ]  │
│  ┌──────────┬────────┬───────────────┬────────────────┬──────────┬─────────┬─────────┐ │
│  │ When     │ SKU    │ Root cause    │ Action         │ By       │ Status  │ Outcome │ │
│  ├──────────┼────────┼───────────────┼────────────────┼──────────┼─────────┼─────────┤ │
│  │ 09-02    │ 2941   │ Demand (HD)   │ Requested pull-│ leo      │ Sent    │ pending │ │
│  │          │        │ over-consume  │ in + escalated │          │         │         │ │
│  │ 08-28    │ 4811   │ Supply slip   │ Confirmed 750/ │ leo      │ Verified│ recovered│ │
│  └──────────┴────────┴───────────────┴────────────────┴──────────┴─────────┴─────────┘ │
│   captured going forward only (can't reconstruct pre-log history) · Lakebase-backed      │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Root cause + action + status + outcome**, append-only (R23/R24). **Impact states** honored: Sent ≠ Verified ≠ Recovered (don't claim improvement early).
- The **honest caveat** — captured going forward only (the transcript's hard constraint on inferring history).

---

### 3.6 · Screen F — Value & Impact
*The page the customer explicitly asked for, and success-factor #4 from the Day-1 kickoff: **quantify the savings.** It answers "is this worth it?" for the planner, their manager, and the exec who funded it — with numbers the tool measures on itself, not a slide.*

> 💡 **Design principle for this page: the tool measures its own ROI as a first-class dataset.** Every
> investigation, every escalation, every logged action emits a timing + outcome record to Lakebase →
> `action_outcome_history`. This page is the read-out. It is **honest about impact states** — it separates
> *time saved* (measured the day one) from *units/$ protected* (only claimable after read-back), so we never
> over-claim (the transcript's own warning about tools that promise too much).

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  VALUE & IMPACT — Supply Root-Cause Workbench        [ This month ▾ ]  [ Team ▾ ]  📤 PDF │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ⏱ TIME TO ANSWER            📉 SYSTEMS TOUCHED        ✅ ADOPTION           💵 $ PROTECTED│
│   ~8 min   ▼ from ~2 hrs       1   ▼ from 5–7            34 investigations    $1.6M        │
│   median, this month          (one workbench)           12 escalations        verified    │
│   ▸ 93% faster                                          7 planners active     (read-back)  │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  WHERE THE TIME GOES — before vs after (per investigation)                                │
│   BEFORE ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ~120 min                                              │
│    hunt across 5–7 systems ▓▓▓▓▓▓▓▓▓▓▓▓▓ 70   assemble email ▓▓▓▓▓▓ 35   re-derive ▓▓ 15   │
│   AFTER  ▓▓  ~8 min                                                                        │
│    triage ▓ 3   drill ▓ 3   send ▓ 2                                                       │
│   ═══════════════════════════════════════════════════════════════════════════            │
│   Saved ≈ 112 min × 34 investigations = 63.5 planner-hours this month ≈ 1.6 FTE-weeks      │
├────────────────────────────────────────────┬──────────────────────────────────────────┤
│  IMPACT LADDER (don't claim early)           │  ROOT-CAUSE MIX (is the Pareto real?)    │
│   proposed → approved → executed → verified  │   🟦 Demand  ▓▓▓▓▓▓▓▓▓▓▓▓ 61%             │
│              → realized                      │   🟧 Supply  ▓▓▓▓▓ 24%                    │
│   $ protected by stage:                      │   🟪 Holds   ▓▓ 12%    other ▏ 3%         │
│    proposed  ░░░░░░░░  $3.1M                  │   ← matches the room's ~60/25/15 guess    │
│    verified  ▓▓▓▓      $1.6M  ◄ claimable    │   (validates where to invest next)        │
│    realized  ▓▓        $0.9M  (downstream)   │                                           │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  OUTCOME PROOF — did the escalation change anything? (self-measured)                      │
│  ┌──────────┬────────┬─────────────┬───────────────┬────────────┬──────────────────┐   │
│  │ SKU      │ Cause  │ Action      │ SS gap @ send │ SS gap +2wk│ Outcome          │   │
│  ├──────────┼────────┼─────────────┼───────────────┼────────────┼──────────────────┤   │
│  │ 4811     │ Supply │ pull-in     │ -1,240 🔴     │ +80 🟢     │ recovered        │   │
│  │ 2941     │ Demand │ escalate    │ -904 🔴       │ -820 🟡    │ improving        │   │
│  │ 7xxx     │ Holds  │ release req │ -300 🔴       │ -300 🔴    │ no change ▸ why? │   │
│  └──────────┴────────┴─────────────┴───────────────┴────────────┴──────────────────┘   │
│   outcome = compare safety-stock gap at escalation vs 2 weeks later (auto, from snapshots)│
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ⚠ Method: time saved is measured per session (start→send). $ protected at "verified" =   │
│  short-units × std cost for SKUs whose SS gap closed after a logged action. Realized $ is  │
│  downstream-confirmed only. Baseline (~120 min, 5–7 systems) = planner-stated, Day-3.      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**What makes this page trustworthy (and not vanity metrics):**
- **Time saved is *measured*, not assumed** — the app timestamps each investigation (open → escalation sent). The ~120-min / 5–7-system baseline is the planners' own Day-3 number, labelled as stated-baseline. So "93% faster" is `measured_now` vs `stated_before`, disclosed as such.
- **$ protected uses the impact ladder** — proposed / approved / executed / **verified** / realized are separate bars. Only **verified** (SS gap closed after a logged action, read from the next snapshots) is headlined; realized is downstream. This directly honors the project's "don't claim improvement early" rule and the transcript's caution against over-promising.
- **Root-cause mix validates the Pareto** — if the live mix drifts from the room's ~60/25/15, that's a *signal about where to invest next*, not decoration. It also quietly proves the triage guesses are calibrated.
- **Outcome proof table is the killer artifact** — for each escalation, it auto-compares the safety-stock gap at send-time vs two snapshots later. "recovered / improving / no change." The **"no change ▸ why?"** link routes to the rejected-recommendation feedback (turning a miss into a candidate rule). This is the closed analytical loop, visible.
- **Export to PDF** — because the exec who asks "what did we get for this?" wants a one-pager, and the planner wants ammunition to *evangelize* it (the transcript's word).
- **"Actions suppressed / do-nothing" count (DK-14)** — a first-class ROI metric: how many flags the tool
  correctly told the planner to **DISMISS/WATCH** (66% of below-SS flags never stock out). *Proving the tool
  saved wasted expedites/buys is as valuable as proving it drove actions* — and it's the direct evidence the tool
  isn't crying wolf. Pair with a "false-alarm-avoided $" (buys not triggered on cushion dips).

> **Why this page matters strategically:** the Day-1 framing said the whole engagement must "drive business
> value" and that we should "quantify the savings." Most tools bolt ROI on as a slide at the end. Here it's
> a **live screen fed by the same action log that runs the workbench** — the tool proves its own worth from
> its own telemetry, continuously. That's the difference between "we think this helps" and "here are 63
> planner-hours and $1.6M we can point to this month."

---

### 3.7 · Screen G — Value Ledger *(the daily incremental savings run + suggested-vs-actual)* — DK-21
*Screen F is the **monthly ROI board**; Screen G is the **live daily ledger** the customer described: 08:00 freezes
"this much at risk," each action increments a running "saved" counter through the day, and end-of-day shows the
total built incrementally. It is the operational heartbeat under Screen F's monthly read-out.*

> 💡 **The one principle that makes this page honest:** *at the click, nothing is saved yet — the action was
> communicated.* So the running counter is **🔵 Projected** (provisional, satisfying, live), and a separate
> **✅ Realized** total trails behind it as weekly snapshots read back. You get the day-long incrementing number
> the ask wants — labeled truthfully, so the first supplier that misses doesn't torch the ledger's credibility.

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  💰 VALUE LEDGER — Tue 2026-09-03          baseline 08:00:  $2.10M at risk (47 SKUs)  📤 │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  🔵 PROTECTED TODAY (projected)   ✅ REALIZED THIS WK      ⚪ CORRECTLY NOT-ACTED         │
│   $1.79M  ▲ incrementing           $1.41M                    12  ·  $88k over-order avoided│
│   residual risk $0.31M             (prior actions confirmed) (DISMISS/WATCH, V12)         │
│  ── 🟥 LOSS AVOIDED (unrecoverable, separate line): $260k demand reallocated ──────────── │◄ never in "saved"
├───────────────────────────────────────────────────────────────────────────────────────┤
│  time  SKU / batch      suggested → actual              state    Δ$        why            │
│  09:14  2941            pull-in PO4471 → pull-in ✓       🟡 com   $412k     —              │
│  10:02  TTI ▸(3,035)    allocate → allocate              🔵 proj  $640k     [note ▸]       │◄ 1 credit, not 3,035
│  11:30  4811            transfer → ✗ air-freight  ⑂div   🔵 proj  $230k     SUPPLIER_CAP   │◄ divergence chip
│  14:00  7781, 8420      (app: expedite) → DISMISS ⑂div   ⚪ n/a    $0        cushion-dip    │
│  ─────────────────────────────────────────────────────────────────────────────────────  │
│  EOD roll-up:  at-risk $2.10M → residual $0.31M   ·   protected $1.79M proj / $1.41M real │
│  ⚠ realized nets OUT found-inventory (cycle-count heals aren't supply wins)               │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Action-close capture (the suggested-vs-actual step) — required before an action logs:**
```
┌─ Close action · SKU 4811 ─────────────────────────────────────────────┐
│  App suggested:  ▸ transfer 300 from Olive Branch → 2120   (~$230k)    │
│  Actual action:  [ air-freight expedite ▾ ]   qty [ 300 ]  value $230k │◄ typed, structured
│  Diverged from suggestion?  ⑂ YES                                      │
│  Reason code:    [ SUPPLIER_CAPACITY ▾ ]   (DK-8 taxonomy)            │◄ ai_classify-able
│  Reasoning:      "supplier tapped out on the pull-in; air-freight was  │
│                   cheaper than the customer's line-down penalty."      │◄ free text, the thought process
│                                             [ Cancel ]  [ Log action ] │
└───────────────────────────────────────────────────────────────────────┘
```

**What each element does — and why it's honest:**
- **Two headline KPIs, not one.** 🔵 Projected is the live day-total the ask wants; ✅ Realized is the banked,
  read-back-confirmed number. Never one merged figure — that's the "claim before read-back" trap.
- **⚪ Correctly-not-acted** makes *good restraint* visible (V12): 12 dismissals, $88k of over-orders avoided.
  Doing nothing well is value; it just isn't "savings."
- **🟥 Loss-avoided** is a **separate line** — unrecoverable exposure (98%, $372.5M, V13) can't be "saved," only
  reallocated. Keeping it out of the counter is what stops a $372M fantasy.
- **Convergence credits once** — the TTI row covers 3,035 SKUs but books one Δ$; the batch expands for drill.
- **Divergence chip ⑂** flags every suggested≠actual; the reason code + reasoning feed the recommender's
  suggestion-adoption learning loop (and a later app-vs-planner realized-value comparison).

**Component plan (AppKit):**
- Headline KPIs → **composed** KPI (`Text` value + delta arrow + freshness caption), *not* a prebuilt card; the
  🔵/🟡/✅/⚪/🟥 tiers → `Badge` + `colorPalette` semantic tokens (no hex).
- Ledger → server-paginated `Table`; the running total is a sticky footer row; divergence rows carry an
  `override_reason_code` `Badge` and a `reasoning` `Popover`.
- Action-close capture → `Dialog`/`Drawer` with a typed action `Select`, qty/value inputs, a divergence `Switch`,
  reason-code `Select`, and a `Textarea` for reasoning — **required** on close (no silent logging).
- Baseline freeze → a start-of-day Job writes `rc_value_baseline_daily`; the page reads it for the 08:00 anchor.
- **States:** loading → `Skeleton` on KPIs + table; **empty** (no actions yet) → `Empty` "no actions logged —
  baseline $2.10M at risk, start triaging ▸"; **realized-pending** → 🔵 row with "awaiting next snapshot"
  caption, never a fake ✅; **error** (baseline missing) → inline `Alert` "08:00 baseline not frozen — showing
  live exposure only."

**Data readiness:** ✅ — projected Δ = verified PAB/gap (V2) × commitment-weighted unit value
(`fact_sop_commitment.frozen_blended_lag1_forecast_cost/_value`, confirmed live); realized = next-snapshot
low-point read-back (confirmed live: 946 SKU-orgs improved, 247 healed across 09/02→09/03) **minus**
found-inventory (S10). Capture fields are new Lakebase columns (ADR). No new source table.

---

## 3B · Creative concepts
*The ideas that make this a planner's investigative instrument, not "one more dashboard." Each is optional polish over the core funnel — flagged by phase — but each attacks a specific pain the transcript voiced.*

### 💡 C-1 · The "Why?" ribbon — one-click causal narrative
The transcript's deepest wish: *"a product partner asks why, and I want to answer in a matter of minutes."*
So put a persistent **`▸ Why?` ribbon** at the top of the hero screen that, on click, **auto-narrates the
waterfall in plain English, top driver first**, assembled from the deterministic buckets (never LLM-invented
numbers; the LLM only phrases the sentence around governed values). It *is* the escalation's first bullet,
generated live. One click = the answer the planner used to spend 2 hours building.

### 💡 C-2 · Time-machine scrubber — "show me the week it broke"
Instead of a static week picker, a **scrubber across the 8-week snapshot history** that **animates the
position line and re-ranks the drivers as you drag**. Planners today "go back in time to see where we were a
week ago" by opening old saved Excel copies. Here, dragging the scrubber replays the plan's own snapshots
(`process_date` vintages already exist) — you literally *watch* the SS gap open and see *which bucket moved
first*. Answers "was it one bad week or five straight months?" — a question the room explicitly raised — by
making the shape of the deterioration visible.

### 💡 C-3 · Pooled vs per-org "ghost" overlay
The org-rollup pain: a single-org record is "misleading" because inventory pools across the Olive Branch
cluster. So on the position chart, show the **pooled network line solid** and the **per-org lines as faint
"ghosts"** behind it. The planner instantly sees *"we look short at 2014, but pooled across 1080+2012+2014
we're fine — it's stranded in manufacturing."* This turns the `designated_org_code` rollup (which the room
thought didn't exist anywhere) into a one-glance insight, and surfaces the stranded-inventory story
(`in_transit_cost` / `work_order_wip_cost`) without a separate report.

### 💡 C-4 · "Who moved my PO?" trust badge
Because the data *does* record `change_order_originator_type` (BUYER/SUPPLIER/REQUESTER) — which the room
assumed was lost tribal knowledge — surface it as a small **accountability badge** on every PO slip:
*"supplier-initiated, no heads-up"* vs *"planner pull-in."* The transcript is explicit that "did they reach
out or did we catch it?" is a recurring, unanswerable frustration. This makes it answerable and creates the
supplier-accountability record the team wants — a genuinely novel capability, nearly free from existing data.

### 💡 C-5 · Escalation as a living object, not a dead email
The email today is a screenshot of a filled template — static, unversioned, un-tracked. Reframe the
escalation as a **living record** with a stable ID: it carries its drivers as structured data, it links back
to the exact snapshot it was built from, and **two weeks later it self-updates with the outcome** (fed into
Screen F). So "the email I sent" becomes "the case I can reopen, re-run against fresh data, and prove the
result of." This is the bridge from tribal notes to institutional memory.

### 💡 C-6 · Confidence & coverage honesty band
Borrowing the demo's own "Working / Partial / By-design" coverage idea: every driver bucket carries a small
**coverage indicator** — green (fully sourced), amber (reconstructed, e.g. available-vs-on-hold), grey (not
connected, e.g. supplier ship-date). The planner *trusts* the tool precisely because it tells them where it's
guessing. This is a creative inversion: most tools hide their gaps; this one advertises them, which is exactly
how you win an expert user who's been burned by black boxes.

### 💡 C-7 · "Similar past cases" rail (Lakebase search)
When investigating 2941, a rail suggests **"3 past escalations that looked like this"** (same cause family +
customer), pulled by Lakebase BM25 search over the action log. Root-causing is pattern-matching from
experience — the transcript calls it "tribal knowledge." This *externalizes* that: a new planner inherits the
team's accumulated triage memory instead of re-learning it. Grows in value with every logged case.

---

## 4 · Cross-cutting controls (Time, Network, Genie)

| Control | Behavior | Requirement | Placement |
|---|---|---|---|
| **Time slider** | Pick the risk week / range; **±6 months** back; **Week ↔ Month** toggle (default month for demand) | R10, R11, R12, R13 | Screen B header (persists to drills) |
| **Network toggle** | Roll up across orgs via `designated_org_code` (Olive Branch = 1080+2012+2014); or single-org; Canada/Mexico separate | R5, C.4 | Every screen header |
| **Genie assistant** | "Ask this SKU": NL over the same Gold + Forecast Genie; answers show **generated SQL + source + who-it-ran-as** | R25 | Collapsible right rail |
| **Plan selector** | 20 Global / 20 Mexico (+ future 22 SS Stat/DOC) | Part D | Header |

> **Genie is additive, not the product.** The transcript agreed: visuals + a natural-language agent
> work *together*. Genie sits beside the waterfall for "break this down by customer" style follow-ups —
> never the only surface, and every answer carries provenance (AI-trust: identity, generated SQL,
> streaming status, disclaimer, governance).

---

## 5 · Component plan — AppKit binding
*Every element → a primitive actually exported from `@databricks/appkit` / `@databricks/appkit-ui`. Confirm exact props via `npx @databricks/appkit docs`.*

| UI element | AppKit component | Data (queryKey → source) | Color token |
|---|---|---|---|
| KPI tiles (A, B) | `Card*` composed (no prebuilt KPI card) + delta text | `watchlist_kpis` → `sdp_*` / `20_supply_daily` | `--success`/`--warning`/`--destructive` by direction |
| Watchlist table | `Table` (server sort/paginate) + inline sparkline | `top_missing_items` → `20_supply_daily` + `dim_series_ext_vw` cost | likely-cause chip = `Badge` per family |
| Likely-cause chip | `Badge` | derived contribution | Demand/Supply/Holds = 3 categorical tokens (fixed across app) |
| **Waterfall** | `BarChart` (floating/stacked bridge) | `variance_bridge` → `20_supply_daily` diffs | diverging palette; gap = `--destructive` |
| Position-over-time | `LineChart` + `AreaChart` (PAB) + reference line (SS) | `position_timeline` → `20_supply_daily` + `inventory_days_on_hand` | AC `--foreground`, SS dashed reference, PAB muted |
| Demand consumption | `Table` | `demand_consumption` → `10_demand_daily` + `sales_order_line_transactions` + `dg5_customer_scd1` | promo/base = 2 categorical tokens |
| Priors matrix | `Table` (heatmap cells) or `BarChart` small-multiples | `priors_matrix` → `10_demand_daily` (date_key × process_date) | sequential palette; actualized = `--foreground` |
| Supply PO drill | `Table` | `po_timing` → `purchase_orders` + `purchase_order_change_orders` | slip = `--destructive`; originator = `Badge` |
| Holds drill | `Table` | `holds_adj` → hold/adj/quality tables | holds family token |
| Escalation draft | `Card` + `Textarea` + `Button` | composed from inserted drivers; write → Lakebase `action_request`/`integration_outbox` | neutral; disclaimer `Alert` |
| Action log | `Table` | Lakebase `action_request` + `action_audit_event` → published to `action_outcome_history` | status `Badge` (5-state) |
| **Value KPIs (F)** | `Card*` composed + delta | `roi_kpis` → `action_outcome_history` (session timings) | `--success` for saved/faster |
| **Before/after time bars (F)** | `BarChart` (horizontal, stacked) | `time_breakdown` → session logs vs stated baseline | neutral; saved = `--success` |
| **Impact ladder (F)** | `BarChart` (stacked by stage) | `impact_by_stage` → `action_outcome_history` | sequential; verified = `--foreground` |
| **Root-cause mix (F)** | `BarChart` (horizontal 100%) | `cause_mix` → `action_outcome_history` | 3 cause tokens (UNIFY) |
| **Outcome-proof table (F)** | `Table` | `outcome_proof` → SS gap at send vs +2wk snapshots | gap delta `--success`/`--destructive` |
| **"Why?" ribbon (C-1)** | `Button` + `Card` + Genie phrasing | deterministic buckets → LLM phrasing only | neutral |
| **Time-machine scrubber (C-2)** | `Slider` animating `LineChart` | `position_timeline` across `process_date` vintages | AC `--foreground` |
| **Pooled-vs-org ghosts (C-3)** | `LineChart` multi-series (muted ghosts) | `position_by_org` → `designated_org_code` | pooled `--foreground`, org `--muted-foreground` |
| **Similar-cases rail (C-7)** | `Table`/list | Lakebase BM25 search over `action_request` | neutral |
| Time slider | `Slider` + `Tabs` (Week/Month) | param `sql.*` into all queries | — |
| Network/Plan | `Select` | param into all queries | — |
| Genie rail | `GenieChat` + `useGenieChat` | Forecast Genie space | provenance `Card` |
| Loading / empty / error | `Skeleton` / `Empty` / `Alert` | every view | — |

---

## 6 · Notation rules applied (IBCS)

- **SAY** — every screen leads with the *stated finding* in the title, not a bare metric.
- **UNIFY** — Demand=🟦 / Supply=🟧 / Holds=🟪 are the **same three tokens everywhere** (watchlist chip → triage strip → drill headers → escalation). Actual = solid `--foreground`; safety stock = dashed reference line; projected PAB = muted/open (░); forecast (when shown) = hatched, never just "lighter."
- **Good/bad is per-metric** — below safety stock = `--destructive`; on-time = `--success`. Never "positive = green" blindly (a forecast *increase* can be bad here).
- **Honest scales** — position-over-time and waterfall share the unit axis; no truncated bars; the wk36 crossing is annotated, not implied.
- **CONDENSE** — waterfall + triage + timeline on one hero screen because the planner compares them together; drivers paginate into drawers.
- **Direct labels** over legends (slip "+21 days", surprise "+101").
- **On Screen F specifically** — before/after bars share one time axis (no truncation); the impact ladder is a stacked bar where *only the verified segment is emphasized* (`--foreground`), proposed/realized stay muted so the eye doesn't over-read unconfirmed value; "93% faster" always carries its "vs stated ~2 hrs" reference inline. The ROI page must hold itself to the same integrity bar it measures the planners against.

---

## 7 · Required states (non-negotiable)

| State | Treatment |
|---|---|
| **Loading** | `Skeleton` for each tile/chart/table — never a spinner over the whole page |
| **Empty** | `Empty` with a next action ("No items at risk in this network — widen the horizon or switch plan") |
| **Error** | inline `Alert` per panel; a failed drill never blanks the hero |
| **Partial / stale** | show what we have + a freshness note ("plan snapshot Mon 08-31; on-hand 06:00"); flag when a source (e.g. supplier PO status) is **not connected** |
| **Not-yet-sourced** | for buckets whose data is external (supplier plans), show a labelled placeholder — *"supplier ship-date not in Databricks yet"* — never a fake number |

---

## 8 · Data readiness per screen
*Straight from [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) — so the build knows what's real today.*

| Screen / element | Data verdict | Source |
|---|:--:|---|
| Watchlist ranking, low-point, $ at risk | ✅ | `20_supply_daily` + `dim_series_ext_vw` |
| Waterfall start = safety stock @ lead time | ✅ | `20_supply_daily.safety_stock` + `complete_lead_time` |
| Position-over-time (AC vs SS vs PAB) | ✅ | `20_supply_daily` + `inventory_days_on_hand` |
| Demand consumption by DG5 + promo/base | ✅ | `10_demand_daily` + `sales_order_line_transactions` + `dg5_customer_scd1` |
| Priors / late 1–6 matrix | ✅ | `10_demand_daily` (date_key × process_date) |
| Supply PO slip + **who moved it** | ✅ | `purchase_orders` + `purchase_order_change_orders` |
| Holds / adjustments / quality | ✅ | hold + adjustment + receipt tables |
| Network rollup (Olive Branch pooled) | ✅ | `designated_org_code` |
| Escalation draft + action log | 🟡 | Lakebase schema exists; **needs** `action_outcome_history` + `escalation_email_output` + publication Job |
| **Value & Impact page (F)** | 🟡 | time metrics = **new** session telemetry (must instrument); $ protected + outcome-proof read `action_outcome_history` + existing snapshots; cause-mix ✅ derivable |
| Supplier ship-date bucket in the drill | ❌ | **external** (Excel/SharePoint) — show as "not connected," future R27 ingest |
| Statistical-vs-DOC safety stock overlay | 🟡 | 22 SS plans not yet populated in fact; needs activation |
| Time-machine scrubber (C-2) | ✅ | `process_date` snapshot vintages already exist in `20_supply_daily` |
| Pooled-vs-org ghosts (C-3), who-moved-PO badge (C-4) | ✅ | `designated_org_code`; `change_order_originator_type` |
| Similar-cases rail (C-7) | 🟡 | needs action log populated + Lakebase BM25 index (grows with use) |
| Criticality Ⓐ/Ⓑ/Ⓒ badge + $-triage sort | ✅ | `dim_series_ext_vw.inventory_abc_class` (DK-16 / V22) |
| Lifecycle 🌱NPD/🔁transition chip | ✅ | `items_scd1.transition_sku_flag`, `is_npd_item` (N1 / V15) |
| Intermittent-demand confidence band | ✅ | ADI proxy over `10_demand_daily` (DK-18 / V24) |
| Dormant/E&O + portfolio-alignment KPI + Sankey | ✅ | last-ship recency + `on_hand_cost` × `inventory_abc_class` (DK-17/DK-20 / V23,V26) |
| Found-inventory / phantom-heal badge | ✅ | signed `inventory_material_transaction.transaction_quantity` (N4 / V18) |
| Returns / warranty driver | ❌ | **cross-system** JDE/AX — needs item-key crosswalk (N3 / V17); deferred |

> **v3 carries these:** the classifier axes (criticality/lifecycle/demand-class/dormant/hold) and the screens
> they open (portfolio health + Sankey S8, dormant/E&O S9, found-inventory heal S10) are specified in
> [`supply_day3_ux_design_v3_scenarios.md`](supply_day3_ux_design_v3_scenarios.md) §S-classify+ / §S8–S10.

> **Design consequence:** the entire **demand-first hero path (A → B → C1 → D)** is buildable on
> confirmed data **today**. The supply "who moved it" drill (C2) is a *bonus* the data already supports.
> Only the supplier-ship-date bucket and the action-log write-targets need work — and the UI shows those
> honestly rather than faking them.

---

## 8B · How value is achieved & measured
*The instrumentation model behind Screen F. This is how the tool proves its own ROI from telemetry — the "define/show how you're achieving the outcome & impact" the customer asked for.*

### The value chain — from click to dollars

```
  planner opens SKU            supply gap explained          escalation sent            outcome verified
  ───────────────►             ───────────────►              ───────────────►           ───────────────►
  ⏱ session_start              buckets computed              action_request +           SS gap re-read
  logged (Lakebase)            (deterministic)               integration_outbox         from next snapshots
        │                            │                             │                          │
        ▼                            ▼                             ▼                          ▼
  ── TIME SAVED ──          ── FASTER, TRUSTED ──         ── STANDARDIZED ──         ── $ PROTECTED ──
  measured now vs           1 system vs 5–7,              same 2-bullet every        short-units × std cost
  stated ~120 min           trusted format               time; auditable            for gaps that closed
        │                                                       │                          │
        └───────────────────────────────────────────────────────┴──────────────────────────┘
                                             │
                                             ▼
                        action_outcome_history (Delta)  ──►  Screen F reads it back
```

### The three value levers, and exactly how each is computed

| Lever | Mechanism | Measurement (what feeds Screen F) | Honesty guard |
|---|---|---|---|
| **1. Time-to-answer** ⏱ | One funnel replaces 5–7 systems | `session_end − session_start` per investigation (Lakebase timestamps); median rolled up | Baseline (~120 min) is **planner-stated**, labelled as such — not a fabricated "before" |
| **2. Decision quality** ✅ | Deterministic root cause + standardized escalation + captured feedback | count of investigations → escalations → verified outcomes; root-cause mix vs the Pareto | "Likely cause" is a hypothesis; overrides are logged as feedback, not hidden |
| **3. $ protected** 💵 | Faster triage → earlier action → gap closed before it hurts service | for each logged action: `short_units × std_cost` (`dim_series_ext_vw`) on SKUs whose **SS gap improved** in the next snapshots | Impact ladder: only **verified** (read-back) is headlined; realized is downstream-confirmed |

### The measurement is a by-product, not extra work

Every screen the planner already uses **emits the telemetry for free**:
- Screen B open → `session_start`; Screen D send → `session_end` + `action_request`.
- Screen E is the action log; Screen F is just an **aggregation query over `action_outcome_history`** + a scheduled Job that re-reads the SS gap 2 weeks after each action (using snapshots that already exist).
- No separate "please log your time saved" survey — the workflow *is* the instrument.

### Value equation (the one-liner for the exec)

```
  Monthly value ≈  (stated_minutes_before − measured_minutes_now) × investigations × planner_cost_rate      [hard, immediate]
                +  Σ verified_$_protected  (short-units × std cost on gaps closed after a logged action)     [claimable at read-back]
                +  Σ realized_$            (downstream service/working-capital improvement)                   [confirmed later, conservative]
```

**Illustrative (self-measured, this month):** 112 min saved × 34 investigations ≈ **63 planner-hours ≈ 1.6 FTE-weeks**,
plus **$1.6M verified** protected. Numbers shown are placeholders until live; the *method* is what's fixed.

### What this unlocks beyond the number
- **Evangelism ammunition** — the transcript wants planners to "evangelize this." A live, exportable ROI page is the artifact that spreads it to the next planner and the next team.
- **Investment steering** — the root-cause mix tells leadership whether to build the demand deep-dive or the supply integration next, from *evidence* not opinion.
- **Feedback → rules** — every "no change / rejected" outcome is a candidate rule or data-quality fix (the domain pattern's feedback-quality loop), so the tool gets *smarter* as it's used.

---

## 9 · Build sequence & tradeoffs

**Recommended slice order (vertical, per project pattern — one thin path end-to-end before widening):**

1. **Hero demand path** — Watchlist → Waterfall → Demand drill (C1) → Escalation draft (D), on `3697-22`/`2941`. Everything ✅ data. *This is the demo that proves the "2 hours → 8 minutes" claim.* Instrument `session_start`/`session_end` from day one so Screen F has data to grow.
2. **Supply drill (C2)** + **who-moved-PO badge (C-4)** — adds the accountability headline (cheap; data ready).
3. **Holds drill (C3)** + **network rollup + pooled-vs-org ghosts (C-3)**.
4. **Action log (E)** + Lakebase publication Job → **Value & Impact page (F)** — closes both loops and turns on the ROI read-out. *Ship F early even if sparse; it fills as the tool is used and is the evangelism artifact.*
5. **"Why?" ribbon (C-1)**, **time-machine scrubber (C-2)**, **similar-cases rail (C-7)** — investigative polish.
6. **Simulator seed (R21)** + supplier-ship-date ingest (R27) — future phases, clearly labelled.

> **Sequencing insight:** Screen F depends on the action log (Screen E), which depends on the escalation
> (D). So the ROI page is *last to light up* — but the **session timers must be wired in step 1**, or you
> lose the "before → after" evidence you can never reconstruct later (same lesson as the action log:
> capture going forward). Turn on the stopwatch with the very first slice.

**Tradeoffs & risks:**
- **Density vs overload** — the hero screen is intentionally dense (waterfall + triage + timeline). Mitigation: strict UNIFY notation + drivers hidden in drawers until asked. If planners find it heavy, split timeline to a tab.
- **"Likely cause" pre-guess can mislead** — it's a *starting hypothesis*, not a verdict. Label it "likely," always let the planner override, and capture the override as feedback (rejected-recommendation reasons).
- **Weekly demand-surprise is suspect** — default demand to **monthly**; weekly only behind the toggle with a caveat (transcript + mapping both flag this).
- **Don't over-build the simulator early** — the room warned against tools that "predict every SKU and send the chain the wrong way." Ship *explain-the-past* first; simulate later.
- **Escalation autodraft trust** — it drafts, the planner *always* reviews before send; provenance + "verify" is mandatory. It is decision *support*, not automation.

---

<div align="center">

### 📌 Design intent in one line
**Collapse the 5–7-system, 2-hour hunt into one guided funnel that starts at safety-stock-at-lead-time,
triages demand→supply→holds, ends in a trusted two-bullet escalation — and measures its own worth
(time saved + $ protected) from the very telemetry it generates, explaining the past honestly before
ever predicting the future.**

*Wireframes are ASCII sketches for alignment, not pixel specs. Every element binds to a real AppKit
primitive (§5) and a confirmed data source (§8). No production schema is written; action state lives in
Lakebase, analytical history in `sandbox_operations.po_management`.*

</div>
