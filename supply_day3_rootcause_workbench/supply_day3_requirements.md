<div align="center">

# 🔧 Supply Planning Root-Cause Tool
### Day 3 Working Session — Requirements, Findings & Decisions

**Source:** `supply_day3_discussion.md` · Day-3 supply-planning breakout transcript
**Type:** Business-requirements capture (read-only — no data written, no production schema touched)

</div>

---

> ## 🎯 The whole session in one box
>
> Build a tool that lets a supply planner answer — in **minutes instead of hours** — the question
> a product/channel partner throws at them:
>
> > ### *"We're in a bad position right now. How did we get here?"*
>
> …by collapsing the **5–7 systems** they check today into **one trusted root-cause view.**
>
> | | |
> |---|---|
> | **Day-3 scope** | Explain the **past** ("how did we get here") — *not* predict the future |
> | **First slice** | **Demand** (~60% of all issues) |
> | **North Star** | Waterfall starting at **projected safety stock at lead time** |
> | **Golden rule** | If it doesn't save time, it doesn't ship — no forced adoption |

---

## 📑 Contents

| # | Part | What's inside |
|---|------|---------------|
| A | [Program framing](#part-a--program-framing) | The 2-week sprint, 3 threads, 5 success factors |
| B | [The concept demoed](#part-b--the-concept-demoed) | Root-cause coverage chart + heat-map output |
| C | [How planners work **today**](#part-c--how-planners-root-cause-today-as-is) | The real AS-IS triage process (the core requirements source) |
| D | [Domain definitions](#part-d--domain-definitions) | Terms that must be pinned to one meaning |
| E | [Requirements](#part-e--requirements) | R1–R27 + non-functionals, tagged by priority |
| F | [Prioritization (Pareto)](#part-f--prioritization-the-pareto) | Demand vs supply vs long tail |
| G | [Data sources](#part-g--data-sources-referenced) | Every system named + Databricks status |
| H | [Decision for today](#part-h--the-decision-for-today) | The MVP-for-the-day + action items |
| I | [Open questions](#part-i--open-questions--gaps) | 11 items to resolve |
| J | [Glossary](#part-j--glossary) | Quick reference |

**Legend used throughout:**
🔴 `P1-today` · 🟡 `MVP` · ⚪ `Future/backlog` · ⚠️ data-feasibility flag · `[interpretation]` / `[unclear]` = transcript ambiguity

---

# Part A — Program framing
*Leadership context set at the top of the day. Applies to **both** supply and demand tracks.*

### A.1 · Where we are in the arc

| Day | What it was | Output |
|-----|-------------|--------|
| **Day 1** | "Art of the possible" demo (by *Bridge*) — how fast you can move once data is in a good place | Got the juices flowing |
| **Day 2** | Training & enablement — hands-on, **data-lens-first** (understand data → then solution) | Demand: **v0.1 app**. Supply: clearer view + started historical root-cause |
| **Day 3** ⭐ | **Pivot to a 2-week sprint** toward production-ready solutions | *(this session)* |

### A.2 · The three overarching threads

```
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│  1. SUPPLY PLANNING │   │    2. DEMAND        │   │  3. ORACLE INTEG.   │
│  Narrow the MVP     │   │  Drive v0.1 → prod  │   │  Databricks+Lakebase│
│  deployable in      │   │  validated over     │   │  → Oracle via APIs  │
│  2 weeks            │   │  2 weeks             │   │  (high-level test)  │
└────────────────────┘   └────────────────────┘   └────────────────────┘
```

### A.3 · The five success factors (next 2 weeks)

1. **Business-validated workflows** (supply + demand) — *the hard part.* Once requirements are solid, dev is straightforward + iterative.
2. **Documented requirements** — started, continuously tuned (demand team updated theirs live from feedback).
3. **Configure the application** from those requirements using the low-code config tool `[transcribed "Unicode" — exact product name unconfirmed]`.
4. **Quantify the savings / business value** — document time & value saved as real users test it. *This must drive business value.*
5. **Oracle API integration** — at least high-level tested in the window.

### A.4 · Operating expectations

> 💡 **Own it like a product, don't hand it off.** Product teams with roles — solution owners,
> hands-on builders, business users representing real needs. *"We own it and constantly iterate,"*
> not *"you own this part."*

- ⏱️ **Short runway → rapid decisions, rapid iteration.**
- 📋 **Document access/environment blockers** the moment you hit *"I need this dataset / it may not be available."* Ideally the data is already in Databricks.
- 📉 **Close the technical→business gap** — MKE develops faster than it ships to business.
- 🤝 **Ownership for future apps** (Jeremy & Chris): who owns requirements vs. development? When does planning hand off to a developer? Proposed: a **70/30/20 methodology** — bring a standard method, adjust the customer's process around it. → afternoon enablement / best-practices session.
- 🗓️ Logistics: two rooms (supply / demand), whiteboarding encouraged, reconvene ~11:00.

---

# Part B — The concept demoed
*Shown to the supply team for feedback.*

### B.1 · The mind-frame

> A product/channel partner says **"We're in a bad position — how did we get here?"** Today the
> planner must dig: demand change? supply/PO change? lost inventory? on hold? The concept's job:
> **answer that fast, in a standardized, trusted format.**

### B.2 · What was on screen — two panels

**◀ LEFT — "Root-Cause Coverage" chart.** Categories that can put you in a bad position, each with a **build-feasibility status:**

| Status | Meaning | Example |
|--------|---------|---------|
| 🟢 **Working** | All data connections exist → variance is calculable | PO receipts |
| 🟡 **Partial** | Missing some data, or need to find the right source | — |
| 🔵 **By design** *("if it's the design")* | Don't have the right data — a **known gap** | — |

**RIGHT ▶ — the output table.** A **heat-map of known issues that cause variances**, computed as a variance table, going **back 8 weeks.**

### B.3 · The deliberately tiny parameters ⚠️ *proof-of-concept — "take with a grain of salt"*

| Parameter | Demo value |
|-----------|-----------|
| SKU | one — the "50 battery" `[interpretation: a specific battery SKU]` |
| Org | one — **2012** |
| Look-back | **8 weeks** |
| Compute/data | kept minimal on purpose |

> **Next step is explicit:** scale to *everything* — all SKUs, all planners (e.g. PL035, Dale, …).

### B.4 · The validation question put to planners

*"How does this help you — can it help you? What more can we do to make it more digestible?"*
**Guardrail:** *if it doesn't save time, it's not worth it — we won't force adoption.*

---

# Part C — How planners root-cause today (AS-IS)
*The richest part of the session and the true requirements source. The tool must compress **all** of this.*

### C.1 · Frequency & cost — *why this matters*

<div align="center">

| 📅 Asked | 🔍 Systems per case | ⏱️ Time per case | 🧠 How the answer is found |
|:---:|:---:|:---:|:---:|
| **~once a day** | **5–7** dashboards/files | **up to ~2 hours** | **inferred**, not handed over |

</div>

### C.2 · The mental model — triage by process of elimination

Planners use **tribal knowledge**: know what's *most likely*, check it, move to next most likely.

```
   START
     │
     ▼
┌─────────────┐   most likely (~60%)
│  1. DEMAND  │──▶ base-forecast change? specific customer? promo added?
└─────────────┘
     │ if not demand
     ▼
┌─────────────┐   (~20-25%)
│  2. SUPPLY  │──▶ POs delayed? supplier moved dates?
└─────────────┘
     │ if not supply
     ▼
┌──────────────────────────────┐   long tail
│ 3. HOLDS / INV ADJ / QUALITY  │──▶ lost/adjusted inventory, or on hold
│    / CYCLE COUNT              │     (there but not shippable) — usually quality
└──────────────────────────────┘
```

> 💡 **Root-causing *is* the action.** The tool needn't *take* an action to be valuable —
> **reducing time-to-triage is the value.**

### C.3 · The tell-tale habit — personal saved snapshots

- Planners **save their own data every week** (own Excel copies) — easier to manipulate, they like the export format.
- A Databricks historical dashboard existed once; they still keep their own copies.
- **All their working systems are in Excel.**
- 🎯 **The ask:** historical data at the **network level (rolled up)** — not per individual inventory org.

### C.4 · The org / network-rollup problem ⭐ *(important)*

- **3–4 inventory orgs within a couple miles** (the Olive Branch cluster), inventory **constantly transferring** between them.
- Oracle **20 supply-plan is per-org** → a single org record is **misleading**; planners reason about **pooled/network inventory.**
- 🚫 **Today there is *no place*** (Databricks, Power BI, anywhere) to say *"show me this item rolled up across orgs."* The data exists; it's never been shaped that way.

| Org code | Meaning |
|----------|---------|
| **1080** | Manufacturing org |
| **2014** | DC org |
| **2012** | Demo org |
| **2120** | Mexico / THD MEX `[from project memory]` |

- Escalation happens at **total-network level** — essentially never per-org today (may change as the DC network regionalizes).
- **Nuance:** stranded inventory in Olive Branch ("OB") and 1080 inventory not yet at the DC (2014) matters — a historical miss can be explained by in-transit inventory that hadn't actualized.

### C.5 · The live walkthrough (Leo, on the real screens)

Concrete step-by-step for one SKU — example **2941…** (a Mexico org, ~2000 orders):

| # | System / artifact | What the planner does | Example numbers from the demo |
|---|-------------------|-----------------------|-------------------------------|
| **1** | **Oracle** SQL dashboard | Weekly plan review of **top missing items**; look out through lead time / what's purchased | ~mid-Feb: **4,600** units demand, projecting to **miss ~900**, low point **837 short**, risk **through Oct** |
| **2** | **Supply simulator** | Visualize position across the risk window | — |
| **3** | **Consumption** Power BI | Did the customer **over-consume** vs forecast? Break down by **customer (DG5)** *(check first if risk is near-term)* | **overconsumed 134%** over 4 months |
| **4** | **Priors** dashboard | How the **forecast changed over time** *(start here if risk is farther out)* | — |
| **5** | **Supplier production plans** (Excel, weekly, **not in Oracle**) | Compare **requested date** vs **current ETA / promise date**; big gap = risk driver | ~**70%** fit a consistent template; long tail doesn't |
| **6** | **Email** (primary) + supplier files | Email the supplier / dig into "why" files | — |
| **7** | **Oracle** | **Holds / inventory adjustments** — there but not shippable — **usually quality** | long-tail causes |
| **8** | **Oracle** | Late transfer orders, stranded inventory (1080 vs 2014) — may not have actualized | — |

> **The consumption + priors "hand-in-hand" story:** if a customer over-consumes, their go-forward
> forecast usually also rose → the full story is *"over-consumed by **X** **and** raised forecast
> by **Y**, within the purchased lead time."*

### C.6 · The Priors dashboard, decoded

```
              SNAPSHOT  (this month → 1mo ago → 2mo ago → … → a year ago)
              ───────────────────────────────────────────────────────▶
  F  Jan26 │  ▓▓▓  ▓▓▓  ▓▓▓  ░░░  ░░░              ▓ RED  = actualized (won't change)
  O  Feb26 │  ▓▓▓  ▓▓▓  ░░░  ░░░  ░░░              ░ WHITE = still open / not yet actualized
  R  Mar26 │  ▓▓▓  ░░░  ░░░  ░░░  ░░░
  E  Apr26 │  ░░░  ░░░  ░░░  ░░░  ░░░              ▸ Drill down to CUSTOMER level per month
  C  …     │
  A
  S  (rows = the forecast PERIOD being forecast)
  T
```

### C.7 · Logging today = informal / tribal

- Escalations, mitigation steps, supplier answers → **not formally logged.** Kept as "really good notes" + the email trail.
- A weekly **"watch list"** exists (change mitigation tactic, add comments) but **no consistent structure** (no standard date/reason). **The team wants a proper log.**
- **Actions taken today:** request pull-ins · work with supplier to prioritize production · validate go-forward forecast with demand team.
- ⚠️ **Hard constraint:** you **can't retroactively infer** some facts — e.g. whether a PO date change was made by a **planner** or a **supplier** isn't reliably in the EDW. A log must **capture going forward**, not fake unlogged history.

### C.8 · Supplier data exchange today

- ❌ **No live data shares with suppliers.** They **publish production plans weekly in Excel** (when they'll actually take product), separate from Oracle ETAs.
- 📄 The **PO status report** = a **spreadsheet dumped onto SharePoint.** Databricks has **SharePoint connectors** but is **not** pulling this file in.
- A recent call explored live-exchange tech → **follow-up conversation exists.**

---

# Part D — Domain definitions
*Recurring theme: business and data must speak **one language** — one definition per term, surfaced **in the UI.***

| Term | Working definition (from the room) | Nuance / status |
|------|-----------------------------------|-----------------|
| **Demand surprise** | Actual demand vs forecast over a range ("this ÷ that over this range") | Backward- **and** forward-looking. **Varies by person → needs one unified definition.** |
| **Safety stock** | A **theoretical target**, not physical ("an imaginary number") | You can be **below** it (usually are). "Zero right now, and we're below it." |
| **Safety stock at lead time** ⭐ | The **North Star** waterfall start point | Key driver = *safety stock at lead time* vs *current projected gap*. Question: **did the variation (ins/outs) consume the safety stock?** SS already covers *some* variation (explicit in newer methods, implicit via DOC) → "surprise" = surprise **over** what's baked in. |
| **Variance to explain** | The gap you must explain — "100 / 500 / 30 units" | The starting point above everything. |
| **10-plan (demand plan)** | **Daily** at guidance level; **monthly** buckets; **keeps customer grain + sub-buckets** (base/promo/run-rate) | ✅ **Strongly preferred** — the 20-plan loses customer grain & sub-buckets. |
| **20-plan (supply plan)** | **Weekly (Monday) snapshot**; weekly buckets; **per-org**; loses customer grain | Feeds off the 10-plan. |
| **Lags / "lates" (late 1–6)** | Months prior to forecast actualizing. **Standard metric = late 3** | Sometimes late 1/2/5/6 by **item lead time**. A **sliding scale**: "3mo ago the next-3mo forecast was X; now it's Y." |
| **DG5** | Customer hierarchy **level 5 = individual customer** (output grain) | Demand must break down to DG5. |
| **Consumption** | Whether a customer bought more/less than forecast | **"4 different ways of doing consumption"** — all DB-driven. |
| **Grain mismatch** ⚠️ | **Demand = monthly; supply = weekly** | A weekly demand-surprise is just a weekly average of the monthly forecast → **planners doubt weekly demand-surprise is meaningful.** Let the user choose; default monthly. |

---

# Part E — Requirements
*Business-stated requirements from the session. Data feasibility noted where raised.*
🔴 `P1-today` · 🟡 `MVP` · ⚪ `Future`

### E.1 · Consolidation — the "magic wand"
- 🟡 **R1** — Consolidate the 5–7 systems into **one place.** *(Direct answer to "what would make life easier?" → "just being all consolidated.")*
- 🟡 **R2** — Be a **trusted, standardized format the business understands** — same structure every time, so planners stop re-deriving.

### E.2 · Root-cause triage *(the heart)*
- 🟡 **R3** — **Identify the likely cause first** — demand / supply / inventory adjustment / holds / quality / cycle-count, or a *combination* → then isolate → then detail.
- 🟡 **R4** — Cover the **root-cause categories** with a **build-status** (🟢 Working / 🟡 Partial / 🔵 By-design) so gaps are explicit.
- 🟡 **R5** — **Network / org rollup** — roll up across orgs for a selling item, at the level fitting the specific problem *(impossible today)*.

### E.3 · The waterfall view — *"how did we get here"*
- 🟡 **R6** — **Start point = projected safety stock at lead time** (the risk period / low point). Agreed **North Star.**
- 🟡 **R7** — **Buckets = the variances** to that reference (demand surprise, supply/PO changes, inventory adjustments, holds, quality…).
- 🟡 **R8** — **Drill-down per bucket** → break down (customer/DG5, promo vs base, month, lag) → **roll back up** into the story.
- ⚪ **R9** — Full "entire root cause" incl. **future** impact, not just what actualized. *(Day-3 heat map is only the what-actualized piece.)*

### E.4 · Time flexibility
- 🟡 **R10** — **User picks the time frame each visit** — every visit = a different journey / problem. Must be flexible, not fixed.
- 🟡 **R11** — **Look-back ≈ ±6 months** (agreed reasonable rule, rare exceptions). *"6 months in the past is really the root — that's how we got here today."*
- 🟡 **R12** — **Not always weekly** — a **slider** for "1 week back," "3 weeks back," spanning **weeks → multiple months.** Handle single-worst-week *and* "5 straight months" (different conversations).
- 🟡 **R13** — Default demand granularity **monthly**; treat **weekly demand-surprise as suspect** *(see grain mismatch)*.

### E.5 · Demand detail *(the P1 slice)*
- 🔴 **R14** — **Demand is the first slice** (~60% of issues). Get demand data in first.
- 🔴 **R15** — Demand detail breaks down by **at least**:

  | Dimension | Detail |
  |-----------|--------|
  | **Customer (DG5)** | *who* drove it |
  | **Type of demand** | promo vs run-rate vs base |
  | **Monthly bucket** | — |
  | **Lag / late 1–6** | — |

  Mirror the consumption + priors Power BI content as a **popup / drill view** on the waterfall.
- 🟡 **R16** — Support the **consumption ↔ priors "hand-in-hand" story** (over-consumed X *and* raised go-forward Y within purchased lead time).

### E.6 · Unified definitions in the product
- 🟡 **R17** — Encode **one agreed definition per term** and **show it in the UI** — no business↔data miscommunication.

### E.7 · Output — the escalation artifact
- 🟡 **R18** — Produce a **structured, standardized formatted email/output** — a **two-bullet statement**, e.g.:

  > *"At this DG5, [customers] over-consumed by [amount] over [horizon/lag], driving [X units] of risk in [period]."*

  Same structure every time; details vary by case.
- ⚪ **R19** — **App drafts the email** in that structure; planner reviews → confirms → **submits/sends.**
- ⚪ **R20** — **Edit-in-app writeback** (final state): edit a value → updates underlying data **and** email content in one place. *(⚠️ much of the needed info is offline/tribal, not in the EDW.)*

### E.8 · Simulator *(future, but named explicitly)*
- ⚪ **R21** — A **simulator** to manipulate inputs & see the effect (the Excel "little radial green simulator"). E.g. supplier capacity is really **750/week** but hasn't actualized in Oracle → **override the supply line to 750/week** and see the projection. Also plus/minus demand.
- ⚪ **R22** — **Templates** feeding off the EDW: punch in a SKU → pulls all data → planner overrides known constraints. Two biggest permutations: **transition-level** and **multi-org-combined.** *(~70% of business fits a consistent template.)*

### E.9 · Action / outcome log
- ⚪ **R23** — A **tracking mechanism** for **root cause + actions taken**, evolving the watch-list. Constraint: **capture going forward** (can't infer planner-vs-supplier PO changes). Ideal flow: app **recommends** → planner **clicks** → **logged.**
- ⚪ **R24** — **Record how the answer was assembled** so it can be reported on later.

### E.10 · Reuse existing assets *(do not rebuild)*
- 🔴 **R25** — **Reuse Chris's Forecast Genie** (already built for demand). It already does:

  ✅ weekly forecast snapshots · ✅ decomposition of misses · ✅ which customers drove the miss · ✅ promo vs base · ✅ forecast evolution over time

  - **Action:** check whether the Genie was pushed to supply *(appears demand-only; supply has never seen it)*. Wiring expected feasible **"in ~1.5 hours"** if data is there.
  - Combine the **natural-language agent with UX visuals** — not either/or.
- ⚪ **R26** — **Reuse the new safety-stock process** (Sarah's "complete reconstruction, on Databricks") for the waterfall start point — "complete future state," viable/tangible.
- ⚪ **R27** — **Ingest the PO status report** (SharePoint spreadsheet) via connectors and **flag** it (requested-date vs promise-date deltas).

### E.11 · Non-functional principles
| # | Principle | Detail |
|---|-----------|--------|
| 🟡 **N1** | **Must save time or it's dead** | 5–7 systems, ~once/day, up to ~2h per case. No help → don't ship. No forced adoption. |
| 🟡 **N2** | **Building block / ground zero** | Step 1 toward future prediction. **Don't go too fast** — cautionary tale: customers who release "I can predict every SKU" and send their supply chain the wrong way. Shared understanding of variance/on-hand/demand/supply **first.** |
| 🟡 **N3** | **Conceptual for now** | Not for real decisions yet — validate the data points are directionally helpful, then refine. |
| 🟡 **N4** | **Feedback-driven** | Every definition and lever is subject to planner feedback ("are these the right insights, or missing a lever?"). |

---

# Part F — Prioritization (the Pareto)
*Planner-estimated shares — explicitly "rough numbers," directionally agreed.*

<div align="center">

| Bucket | Share of issues | Day-3 priority |
|--------|:---:|:---:|
| 🔴 **Demand** — base-forecast change, customer, promo, over-consumption | **~60–75%** | **P1 — build first** |
| 🟡 **Supply** — PO delays, supplier date moves | ~20–25% | MVP next |
| ⚪ **Holds / inventory adj / quality / cycle / other** | long tail | backlog |

</div>

> 🔁 **Compounding effect (Carter):** a forward-looking forecast increase doesn't just raise
> demand — it **raises the safety-stock target** too (forward days-of-coverage → hold more), so
> health looks *worse* on both sides. This is why demand changes dominate.

---

# Part G — Data sources referenced

| Source / artifact | System | Role | In Databricks/EDW? |
|-------------------|--------|------|:---:|
| Oracle SQL dashboard / weekly plan review | Oracle | Find top missing items; entry point | source of truth *(read-only)* |
| Supply simulator | Oracle/Excel | Position over risk window | Excel today |
| Consumption dashboard | Power BI | Over-consumption vs forecast, by DG5 | ✅ **DB-driven** (4 methods) |
| Priors dashboard | Power BI / analytics | Forecast period × snapshot; late 1–6 | ⚠️ priors 1–6 **may be analytics-only, not EDW** (semantic model/formula) |
| **Forecast Genie** (Chris) | Databricks Genie | Snapshots, decomposition, customer drivers, promo/base, forecast evolution | ✅ **exists — reuse** |
| Supplier production plans | Excel (weekly) | Requested vs promise/ETA dates | ❌ not in Oracle; Excel only |
| PO status report | SharePoint spreadsheet | PO status; date-change flags | ❌ **not ingested** (connectors exist) |
| Safety-stock process (Sarah) | Databricks | New safety-stock reconstruction | ✅ **exists — reuse** for waterfall start |
| Watch list / risk register | Excel/notes | Informal action log | informal, inconsistent |
| Item / customer / plan tables | `prod_edw` (Bill's team) | 10-plan, 20-plan, items, DG5 | 🔒 **read-only** |

> ## 🔒 Guardrail reminder *(project rule — non-negotiable)*
> `prod_edw` and `prod_operations` are **READ-ONLY.** All derived tables, snapshots, and outputs
> for this tool land in **`sandbox_operations.po_management`**; all transactional app state
> (drafts, logs, action requests, comments) goes to **Lakebase.** Any Oracle writeback is a
> separately approved, typed, auditable action path — **never** a direct write to a production
> Databricks schema.

---

# Part H — The decision for today
*MVP-for-the-day.*

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  DO TODAY                                                          │
  │  1. Build the DEMAND slice (P1) — ~60% of issues, data is         │
  │     objective (customer, DG5, type-of-demand, month, priors 1-6). │
  │     ✔ No demand-team person needed — just the data.               │
  │  2. Wire the FORECAST GENIE to supply (if accessible); split its  │
  │     ~5 demand views into individual, drillable pieces             │
  │     (e.g. "break down this material by individual customer").     │
  │     ✔ ~1.5h if data is available; run in parallel with access.    │
  ├──────────────────────────────────────────────────────────────────┤
  │  BACKLOG (build on top later)                                     │
  │  · Waterfall  · Safety-stock reconstruction (Sarah's)             │
  │  · PO status report ingestion  · Action log  · Simulator          │
  │  "A bit much for today."                                          │
  └──────────────────────────────────────────────────────────────────┘
```

### H.1 · Immediate action items

| # | Action | Owner (as stated) | Notes |
|---|--------|-------------------|-------|
| 1 | Capture this session as **structured direct feedback** | Databricks (Eric/Sarah) | *this document* |
| 2 | **Locate the Forecast Genie**; confirm supply has access | Chris Eyler / analytics | likely demand-only; may need Chris to push |
| 3 | **Wire the Genie**; split ~5 views into customer-level drilldowns | Databricks team | parallel with #2 |
| 4 | 🚧 **Get the demand table / source names** | **Bill's team** + Chris | **blocker** — "otherwise we're searching in the dark" |
| 5 | Confirm **priors 1–6** location — EDW vs analytics semantic layer | Chris / analytics | affects direct sourcing |

---

# Part I — Open questions & gaps

| # | Question | Type |
|---|----------|------|
| 1 | **Weekly vs monthly demand-surprise** — is weekly even meaningful? *(planners lean monthly)* | 🟨 decision |
| 2 | **Default lag (late 1–6)** + how to expose the sliding scale | 🟨 decision |
| 3 | **Priors 1–6 location** — EDW vs analytics-only semantic model | ⚠️ data |
| 4 | **Coverage build-status** — Working/Partial/By-design once scaled past 1 SKU | 🔧 build |
| 5 | **Network/org rollup logic** — pool 1080/2014/DC; Canada/Mexico handling | 🧱 modeling |
| 6 | **Unified "demand surprise"** definition (and others) | 🤝 business+data |
| 7 | **Action-log design** — capturable-forward vs never-inferable | 🎨 design |
| 8 | **Supplier live data exchange** — tech to replace weekly Excel | 📞 follow-up |
| 9 | **PO status report ingestion** — connect SharePoint file, define flags | 🔧 build (backlog) |
| 10 | **Ownership model** for next 5 apps — 70/30/20 handoff | 🔄 process |
| 11 | **Product-name confirmation** — config tool transcribed "Unicode" | ❓ clarify |

---

# Part J — Glossary

| Term | Meaning |
|------|---------|
| **10-plan / demand plan** | Demand forecast; daily at guidance level, monthly buckets, keeps customer grain + sub-buckets. **Preferred** demand root-cause source. |
| **20-plan / supply plan** | Supply plan; weekly Monday snapshot, weekly buckets, per-org, loses customer grain. |
| **DG5** | Customer hierarchy level 5 = individual customer (output grain). |
| **Demand surprise** | Actual demand vs forecast over a range; the surprise *over* what safety stock covers. Backward + forward-looking. |
| **Safety stock** | Theoretical target inventory (not physical). Can be below it. |
| **Safety stock at lead time** | The waterfall's start point / North Star; compare to current projected gap. |
| **Lag / late 1–6** | Months prior to forecast actualizing; standard = late 3; varies with item lead time. |
| **Consumption** | Whether a customer bought more/less than forecast (4 DB-driven methods). |
| **Priors dashboard** | Forecast snapshots: forecast period (rows) × snapshot month (cols); red=actualized, white=open. |
| **Forecast Genie** | Chris's Databricks Genie: snapshots, decomposition, customer drivers, promo/base, forecast evolution. |
| **Watch list / risk register** | Informal weekly log of mitigation tactics + comments; no standard structure today. |
| **Org 1080 / 2014 / 2012 / 2120** | 1080 = manufacturing; 2014 = DC; 2012 = demo; 2120 = Mexico/THD MEX. |
| **OB** | Olive Branch (DC location / cluster of orgs). |
| **Simulator** | Excel tool to override inputs (e.g. supplier capacity 750/week) and see the projected position. |
| **Requested date vs promise/ETA date** | PO placement date vs supplier's current committed date; the gap flags supply risk. |
| **PO status report** | Spreadsheet dumped to SharePoint; not yet ingested into Databricks. |
| **Unicode** `[unconfirmed]` | Transcribed name of the low-code app-config/requirements tool. |
| **FPL team** `[interpretation]` | The forecast/planning business team that owns requirements. |

---

# Part K — Data-Discovered Requirements *(beyond the transcript)*

> ⚠️ **Provenance differs from Parts A–J.** Everything above is *planner-stated* (from the transcript).
> Part K is **data-sourced** — candidate requirements surfaced by probing the actual tables
> ([`supply_day3_data_scenarios.md`](supply_day3_data_scenarios.md)), *not* things the room asked for. They
> are strong candidates because the data proves the magnitude, but they need **business validation** before
> being treated as committed scope. Figures are live (`mke-rsc`, 2026-09-02), illustrative of magnitude.

The planners scoped one workflow (shortage triage). Six live probes show the same confirmed tables answer far
more. Each becomes a candidate requirement + a UX lens ([`supply_day3_ux_design_v3_scenarios.md`](supply_day3_ux_design_v3_scenarios.md)).

| # | Data-discovered requirement | Live signal | Audience | Status |
|---|---|---|---|:--:|
| **DK-1** | **Excess / overstock visibility** — mirror of the shortage view for PAB *above* target; rank by $ tied up + aging→E&O | **~$452M**, excess **3.2× more prevalent** than shortage | Finance + planner | candidate |
| **DK-2** | **Rebalance-before-buy** — detect same-SKU short-in-one-org / excess-in-another; recommend transfer over PO | **1,646** item×network cases | Planner | candidate *(highest ROI)* |
| **DK-3** | **Plan-stability / nervous-SKU flag** — flag targets that thrash across snapshots so planners don't react to noise | 2,668 nervous series (concentrated; ~3% avg) | Planner | candidate |
| **DK-4** | **Supplier reliability scorecard** — rank chronic self-slippers; targeted QBRs | top 4 = **~78%** of supplier-initiated slips | Sourcing | candidate |
| **DK-5** | **Forecast-bias / FVA board** — systematic over/under vs late-3 by customer; fix the root cause of shortages | customers **+60–190%** chronic bias | Demand team | candidate |
| **DK-6** | **Inventory-flow / stranded view** — finished goods in mfg not at DC; split WIP vs stranded vs in-transit | **$127.5M** on-hand in mfg org 1080 | Ops + planner | candidate |

**The reframe these imply:** the product is not "the shortage tool" — it's a **control tower / supply-chain
nervous system** with the shortage workflow as its first lens. DK-1 and DK-2 are the cheapest to build (pure
reuse of `20_supply_daily` + the org rollup) and reframe the product most — recommended right after the v1/v2
hero path.

### DK-7…DK-12 — transcript re-read findings *(said in the room, not previously captured)*

> A second close read of the transcript surfaced items **explicitly discussed by the planners** that our
> earlier requirements (Parts A–J) under-weighted or missed. Two are backed by **newly-found governed tables**
> (verified live 2026-09-02) — meaning MKE already has the data/logic we assumed we'd have to build.

| # | Requirement (transcript quote / basis) | Status in data | Why it matters |
|---|---|---|---|
| **DK-7** | **Reuse the existing `fact_forecast_accuracy` table** — the transcript names a "forecast accuracy dashboard… fixed to lake three." | ✅ **found live**: `prod_operations.demand.fact_forecast_accuracy` — carries `planner_bias`, `system_bias`, `positive/negative_error(_cost)`, `working_final_forecast_lag3_units/_cost`, `rolling_6_*` by DG5×item×date | We planned to *compute* bias empirically (DK-5); **MKE already has a governed bias/accuracy fact** (planner vs system bias split!). Use theirs — don't reinvent. Upgrades DK-5 from 🟡 to ✅-sourced. |
| **DK-8** | **Adopt the existing governed root-cause taxonomy** — the room wanted structured reasons ("why did the forecast miss / why the escalation"). | ✅ **found live**: `prod_operations.demand.dim_forecast_accuracy_reason_codes` — 12 governed reasons w/ definitions (Incorrect POS assumptions, NPD/Transition, Promo strategy change, Business Decision, Constrained Ordering, Make-to-Order, Timing, Seasonality, Expansion, E&O, Customer Opportunity…); plus `prod_edw.dimension.work_order_root_cause_scd1` for the make side | This is **the categorical taxonomy** we said `ai_classify` needed — it *already exists and is governed*. `ai_classify` should classify into THESE codes, not invented ones. Makes the feedback loop real on day one. |
| **DK-9** | **"How do I transfer from here to meet expectations" — the forward SOP** (Eric: *"what's my stock-out risk next week, two, three weeks… how can I transfer"*) | ✅ **quantified live**: **7,508** forward SKU×network cases (next quarter) where a *projected* shortage is coverable by transferring same-SKU excess from another org in-network; **dense established lanes** (2012↔2013 65k/34k, 1080→2012 30k, 1080→2014 15k) | The planners explicitly framed the *future* action as **transfer-to-cover**. 7,508 is 4.6× the near-term-only rebalance count (1,646) — forward-risk (DK-1) + rebalance (DK-2) are **one workflow**: "you'll cross below SS at wk39 → transfer 300 from 1080 now (lane exists) → covered." Sequence them together. |
| **DK-10** | **Forecast-accuracy dashboard's lag mismatch is a known pain** (*"a lot of times it's a lake-one or lake-four story, versus forecast accuracy is fixed to lake-three"*) | ✅ **verified precisely**: pre-built lag columns exist for **only lag-1 and lag-3** (`final_distribution_forecast_lag1`/`_lag3`, `final_demand_forecast_3_month_ago`/`_lag3`) — **no lag-2/4/5/6 columns**. Full lag-1..6 must come from the **`process_date` snapshot self-join** (verified Activity 3). | Confirms the pain is real: reading columns gives you **only lag-1 & lag-3** (accuracy fact is lag-3-locked). The "lake-one/lake-four story" needs the **vintage self-join** — so the priors view *must* compute lag-N from snapshots, not lean on the pre-built lag columns. This is a concrete design instruction, not just a nice-to-have. |
| **DK-11** | **Building/sub-org counting error is a real data-quality issue** (*"it transferred and somehow it still said it was in 1080, so I thought we had more… off-counted"*) | ⚠️ **verified nuance**: on `inventory_days_on_hand` the `in_transit_cost` / `work_order_wip_cost` / `received_not_put_away_cost` columns **EXIST but are $0/empty** network-wide (only `on_hand_cost`=$1.65B populated) — so the count-integrity signal is **NOT** in the on-hand fact. **BUT** it IS derivable from **`transfer_orders`: 240,197 Open transfers** (vs 445,638 Closed) + `status` + `scheduled_ship_date` + `requested_quantity` | An **Open transfer past its scheduled-ship date = "in-transit, projected healthy but not actually here"** — exactly the planner's mis-count case. So the stranded/flow view (DK-6) sources the count-integrity flag from **open transfer orders**, not the (empty) in-transit cost column. Concrete correction to how DK-6 must be built. |
| **DK-12** | **Forecast increase → safety-stock target auto-refresh (the compounding trap)** (Carter: *"your health will look worse if they increase the forecast… safety stock will refresh… forward days of coverage, hold more"*) | ✅ **quantified live** (same target week, over 8 snapshots): of 65,186 series, SS target rose for 4,717; in **850 cases SS AND demand rose together** — and on those, **demand rose ~220% while the SS target rose ~17.6% alongside it.** Carter's mechanism proven with magnitudes. | Real but **concentrated (~1.3% of series)** → a **targeted callout**, not universal. When both moved, surface it explicitly: *"position looks −X worse, but ~18% of that is the SS target refreshing on higher demand, not a physical shortage — don't over-buy."* This is the "don't trigger a buy off a signal already covered" guardrail the room stressed. Elevate from Gap-6 chart detail to a decision-trap flag. |

### DK-13 — Convergence: the common case the single-cause design misses *(data-validation finding)*

> Surfaced by the validation pass (`validation/V11_convergence_scenarios.md`), not the transcript. The Day-3
> mental model is **single-dominant-cause triage** ("is it demand OR supply OR holds?"). **Live data shows that
> framing is wrong for the majority of cases** — causes and constraints *converge*. Three types, all verified:

| Type | Live finding | Action model (the "what to do") |
|---|---|---|
| **DK-13a · Multi-cause on one SKU** | **52%** of 8,853 shortage SKUs have **all three** causes at once (below SS + PO slip + demand over-consumption) | **Stacked mitigation + residual-gap tracker**: rank co-firing causes by *contribution × who-can-act*; apply top movable lever; show remaining gap + owner; emit **one combined escalation**, not three tickets |
| **DK-13b · Shared constraint** | **1 supplier (Techtronic Cordless) behind 3,035 shortage SKUs** (understated — 4+ name variants) | **Act on the constraint ONCE + allocate capacity**: aggregate to the constraint, one sourcing action (QBR/capacity/expedite-batch), allocate scarce capacity to highest-value SKUs. **Changes who acts: planner → sourcing.** Biggest time-saver in the product |
| **DK-13c · Temporal risk wave** | **6,933 SKUs first-cross in one week**, then long tail | **Capacity-triage, not a flat queue**: impact-rank the wave, work top-N, **log the deferred/accept-risk tail**, smooth by pulling forward where lead time allows; treat as a workload forecast |

**Core principle:** convergence changes the **unit of action** — from a SKU, to a *cause-stack* (13a), a
*constraint* (13b), or a *week* (13c). Detection is easy; the value is the action. **Guardrails:** convergence
actions move *batches* → **propose, don't auto-execute** (human-in-the-loop, deterministic rules rank/allocate);
and **supplier-name normalization is a prerequisite** for 13b or the constraint fragments.

**Status:** 🔴 **capability gap** in the current design (single-cause triage, per-SKU screens surface none of the
three). Not a broken measure — a missing lens. New UX: **residual-gap tracker, constraint-first pivot, risk-wave
view, convergence score** (# active causes) on the watchlist rank.

### DK-14 — The do-nothing / watch verdict: showing root cause but recommending NO action *(data-validation finding)*

> Surfaced by the validation pass (`validation/V12_do_nothing_scenarios.md`). A tool that *only* ever says "act"
> cries wolf and trains planners to ignore it — the transcript's own worry (*"if we have in our safety stock some
> of that variation already covered, then I don't want to trigger"*). **Live data: of 10,700 "below safety stock"
> flags, only ~3,634 (34%) ever actually stock out.** The right answer for the majority is do-nothing or watch.

**A three-way action verdict** (not act/ignore): `ACT` (real, near-term, physical) · `WATCH` (real but
not-yet / may self-correct → monitor, don't spend) · `DISMISS` (false-alarm-by-design → close the flag with
evidence).

| Situation | Live count | Verdict |
|---|---|---|
| Below SS but **PAB never goes negative** (cushion dip — SS doing its job) | **7,066 = 66%** of flags | 🟢 DISMISS |
| Below SS for **only 1 week** of the horizon (transient blip) | 1,603 | 🟢 DISMISS / WATCH |
| Flagged "worse" but **position unchanged — SS target rose** under it (DK-12 artifact) | 420 | 🟡 WATCH — don't buy |
| **Excess** flagged but only 5–6 wks cover (×SS false-positive, V7) | ~20% of excess | 🟢 DISMISS |
| Crosses **beyond the ~8-week window** (far-out, may self-correct) | 884 | 🟡 WATCH — re-check next snapshot |
| Near-term + physically negative PAB | ~3,634 | 🔴 ACT |

**Core principle:** *"do nothing" is a recommendation, not an absence of one* — the tool shows the root cause AND
the recovery evidence ("dips to −200 wk38, recovers wk39, never negative → no action"), so the planner spends
nothing but the tool proved the non-action was right. **WATCH = deferred + remembered** (auto-escalate if it
worsens; don't lose it). Gate `ACT` to near-term + physical breach (or tolerance breach), **not "below target"
alone**.

**Status:** 🔴 **capability + trust gap** — the current design has only "problem → act"; no do-nothing/watch
state, yet the data says that's correct ~66% of the time. New: an `action_verdict` (ACT/WATCH/DISMISS) serving
column; DISMISS-with-evidence; a **"suppressed / do-nothing" count on the Value page** (proving the tool *saved*
wasted actions is as valuable as proving it drove them). Pairs with DK-13 (convergence) and V10 (acute/chronic/
nervous): temporal-class + action-verdict together turn a 10,700-row alarm into a ~3,600-row real worklist. The
DISMISS threshold (how far below SS, how long, is genuinely OK) is a **business rule to confirm with a planner**.

### DK-15 — Recoverability class: winnable fire vs committed loss vs living-on-the-edge *(data-validation finding)*

> Surfaced by `validation/V13_recoverable_vs_lost_edge.md`. Planners live a weekly rhythm of **fires we recover**
> and **battles we lose no matter what** — distinct, named supply-chain states the tool must separate.
> **Professional terms:** the winnable weekly fire = an **S&OE (Sales & Operations Execution) exception** you
> *expedite*; the lost battle = an **unrecoverable / committed stockout** (breach **inside the lead-time fence** —
> no supply can arrive in time, past the "last responsible moment"); living-on-the-edge = **hand-to-mouth /
> chronic-critical, zero-buffer** SKUs. Organizing concept: the **lead-time fence**.

**Live data:**
- **98% of flagged crossings are INSIDE the lead-time fence (unrecoverable by ordering)** — because lead time is
  **bimodal: median 2 days but average 122 days**, and the long-lead tail *is* the flagged population. So for
  flagged SKUs, "place a PO" is almost never the lever — **transfer** (respects no supplier lead time) or it's a
  committed loss.
- **2,307 SKUs are below SS every week** of the horizon (chronic zero-buffer / living-on-the-edge); 3,712 hit
  actual zero.

**Where full RCA belongs (a deliberate inversion):** *not* every fire.
- Recoverable near-term fire → **fast triage** (you have a lever; speed > depth).
- **Unrecoverable + high-$/committed → FULL RCA** — too late to fix *this* one, so the value is *learning why it
  became unrecoverable* (late detection? unknown fence?) to prevent the next. (The transcript's "capture how it
  happened so we can report/prevent.")
- **Chronic zero-buffer → systemic RCA** → output is a **policy change** (SS realism, dual-source), not an expedite.
- Cushion dip (DK-14 DISMISS) → **no RCA** (waste).
→ **Full RCA is reserved for the committed-and-material and the chronic** — the "living on the edge" and "lost
battle" cases — because that's where the learning and prevention live.

**Status:** 🔴 **capability + trust + time gap.** New: a **recoverability class** (`RECOVERABLE` /
`UNRECOVERABLE`) on every flag, computed with **per-SKU `complete_lead_time` (never an average — it's bimodal)**;
UNRECOVERABLE flags switch the recommended action to **damage-control** (transfer→allocate→notify→log lost);
a **chronic-critical / living-on-the-edge watch** routed to a policy-fix backlog; RCA depth gated by class.
Ties to DK-13 (convergence), DK-14 (ACT/WATCH/DISMISS), V10 (acute/chronic/nervous) — the four classifiers
together are what make the alarm a worklist.

**Net from the re-read:** the two biggest are **DK-7 + DK-8** — MKE already has a **governed forecast-accuracy fact (with planner-vs-system bias)** and a **governed root-cause reason-code taxonomy**. We were about to build both. This is the "reuse what Chris/analytics already has" theme the transcript kept returning to ("leverage what Chris has… not something net new").

### N1…N7 — uncovered-scenario sweep (validated V15–V21)

> Leads that surfaced *inside* the validation (V14 sweep) and were then each live-validated. Status:
> ✅ confirmed / 🟡 minor-or-gated / 🟡 honest-no.

| # | Scenario | Verdict | The number / finding | Action |
|---|---|:--:|---|---|
| **N1** | Transition / NPD SKUs | ✅ V15 | status on `items_scd1` (V14 probed wrong table); **71,484 transition, 4,038 NPD**; **1.5× / ~9× over-represented** in shortages | add **lifecycle class** (mature/transition/NPD); route NPD shortages to launch-execution owners; map to reason codes |
| **N2** | Over-forecast → excess | 🟡 honest-no V16 | plausible but **not provable at SKU grain** — excess is **62.5% systemic**, SKUs shared | **don't ship as causal**; pivot to the bigger truth — excess is a **planning-policy** problem (SS/MOQ/forward-DOC), not customer-caused |
| **N3** | Returns / warranty | ✅ V17 (**upgraded 2026-09-03**) | real & material warranty history + reason taxonomy, and — corrected — **conformed & item-keyed**: `prod_edw.fact.warranty_transaction.item_bigint_key` → `items_scd1` (governed `domain_service` schema already integrated JDE/AX/Oracle/Connect upstream). 60 real IDs pulled. | build the returns/quality lens on the conformed fact; split operational-restock (supply source) vs warranty (quality lens); mind `part_bigint_key` vs `item_bigint_key` grain |
| **N4** | Found inventory (positive adj) | ✅ V18 | **25,089 found events / +81.9M units** — adjustments must be read **signed** | positive adj = **heal signal** → downgrades a shortage's severity (ties DK-11 count-integrity, V13) |
| **N5** | Non-standard demand | 🟡 minor V19 | only **1.1% of volume** — over-ranks on unweighted % | rank demand-bias by **weighted $/units**; tag/exclude NO-CHARGE/OTHER streams |
| **N6** | Component / bulk orgs | ✅ V20 | **8000 = Supplier Inv (consignment), 2092 = 3PL Parts** — non-DC grains | **segregate non-DC orgs before any $-ranking** — fixes the distortion recurring across V1/V2/V5/V7/V9; add governed `org_type` |
| **N7** | Recovery velocity | ✅ V21 | bimodal: **29% heal fast (≤5 snaps) / 24% stuck (40+)** | add **self-heal velocity** to sharpen WATCH (fast-heal) vs chronic (stuck, V10) |

**The discipline note:** N2 *disproved* a clean causal claim and was recorded as such — "a membership join is not
causation." N6 both *explains and fixes* a DQ distortion that quietly recurred through six earlier validations.
Highest-value confirmed: **N1 (transition/NPD lifecycle)** and **N4 (signed adjustments / found-inventory heal)**.

### DK-16…DK-20 — validated adjacent scenarios (from data-lead sweep V14 + peer-app cross-pollination)

> Each **live-validated** (V15–V26). Status: ✅ confirmed / 🟡 gated or partial. Sources: the uncovered-scenario
> sweep (N1–N7) and a peer MRO inventory-optimization app (cross-pollination, name withheld).

| # | Requirement | Verdict | Live evidence | Action |
|---|---|:--:|---|---|
| **DK-16** | **Criticality / ABC as a classifier axis** — weight the ACT rank by A/B/C | ✅ V22 | A-class shortages **$67.8k/SKU = 2.1× C-class**; buried in a $-only rank | add `criticality_class` to serving layer; blended priority (criticality × $ × recoverability); fallback for 37% Unclassified |
| **DK-17** | **Dormant / E&O lens** — no-movement + write-off risk, distinct from active overstock | ✅ V23 | `obsolete_date` too sparse; **movement-recency** is the signal — **$545M never-shipped**, $16M dormant | build on last-ship recency, NOT obsolete_date; pair with intentional-hold (DK-20) + NPD (V15) before calling dead stock |
| **DK-18** | **Demand-class (intermittent/smooth)** — a guard on our own SS/consumption formulae | ✅ V24 | **~24% intermittent** (ADI proxy); Normal-SS & %-consumption unreliable there; explains some V3 "misses" | add `demand_class`; flag standard measures low-confidence on intermittent SKUs |
| **DK-19** | **Parameter recommendation + proposal queue** | 🟡 V25 scope-corrected | MKE is **projection-based, no ROP/MAX** → becomes a **safety-stock** review; recommender **blocked** (SS methodology, B1/B10) | ship the **proposal-queue workflow now** (reuse `action_request`); gate the recommender behind SS-method unblock |
| **DK-20** | **Alignment-% KPI + health Sankey + intentional-hold** | ✅/🟡 V26 | **54% aligned** (healthy/excess/short); Sankey ready; intentional-hold *partial* (`ss_managed`=$450M, no explicit reserve flag); `inventory_planning_method` = new dim | ship $-weighted alignment KPI + Sankey; use `ss_managed='Yes'` to suppress false dormant/excess flags |

**Cross-cutting — the classifier layer now has more axes.** Beyond severity/temporal/recoverability/convergence/
action-verdict, add **criticality (DK-16), demand-class (DK-18), lifecycle (transition/NPD DK/V15, dormant
DK-17)**. Two are also **integrity guards** on existing measures: DK-18 (intermittent → SS/consumption
unreliable) and DK-20 intentional-hold (suppress false dormant/excess flags). DK-19 is the **planning/S&OP
counterpart** to our execution/S&OE root-cause tool — the two halves of a full control tower, but the recommender
is a later, evidence-gated build.

### The classifier layer — DK-13/14/15 + V10 are ONE idea, not four
The validation findings converge on a single architectural insight: **a Classify stage between Detect and
Explain.** Before any recommendation, each flag is tagged — **severity** (below-target vs hard-stockout),
**temporal class** (acute/chronic/nervous, V10), **convergence** (# co-firing causes, DK-13), **recoverability**
(winnable vs committed loss, DK-15), **action-verdict** (ACT/WATCH/DISMISS, DK-14). These tags decide *whether
and how* to act and **gate RCA depth** (full RCA only for unrecoverable-material or chronic). They are
pre-computed **serving columns** (ADR §7.1a). *Net effect (live): a 10,700-flag alarm → a ~3,634-ACT,
recoverability-aware worklist.* This is the biggest quality lever the validation surfaced — bigger than any
single measure.

### DK-21 — The Value Ledger: incremental savings + suggested-vs-actual capture *(customer request, 2026-09-03)*

**The ask (verbatim intent):** a page that proves the day's savings. 08:00 says *"this much at risk";* each
action fires a counter that says *"this action saved this much,"* incrementing through the day; end-of-day shows
the **total, built incrementally.** Plus: the app's suggested action and the **actual** action a planner takes
may differ — so capture the **actual action + the planner's reasoning / thought process** per item or batch.

**The honest-accounting principle (non-negotiable, or the ledger loses trust):** *at the moment of the click,
nothing is saved yet — the action has only been communicated.* Savings therefore move through **three states**,
mirroring the app's existing ✅🟡🔴 provenance discipline:

| State | Trigger | Meaning | Counter |
|---|---|---|:--:|
| 🔵 **Projected** | on click (after receiver informed) | modeled exposure the action *should* remove | live, provisional — **this is the day-long running total the customer described** |
| 🟡 **Committed** | receiver confirms (supplier accepts / transfer approved) | the other party agreed | firmer |
| ✅ **Realized** | next weekly snapshot read-back | the SKU's forward low-point actually rose | banked |

**Four accounting rules that keep the number credible** *(all validated):*
1. **Unrecoverable ≠ saved.** 98% of exposure ($372.5M, V13) is inside the lead-time fence — cannot be "saved."
   Those actions credit a **separate line — "loss avoided / demand reallocated,"** never the savings counter.
2. **Convergence attributes once.** One constraint action covering 3,035 SKUs (V11) credits the **action once**,
   fanned to SKUs for drill — never re-summed per SKU or per lens.
3. **Phantom-heal subtracted.** Realized savings **subtract found-inventory** (S10 / N4 — signed adjustments); a
   gap that closed on a cycle count is not a supply win. *(Live read-back 09/02→09/03: 946 SKU-orgs improved
   their forward low-point, 247 fully healed — some on found-inventory, which is exactly why we net it out.)*
4. **DISMISS is value in a different unit.** Correctly doing nothing (V12) avoids wasted expedite/over-order
   spend → a **"correctly not-acted"** counter (count + avoided-$), not lumped into savings.

**Suggested-vs-actual capture (the learning goldmine):** every action records **both** what the app proposed
and what the planner did, structured — `suggested_action` / `suggested_value`, `actual_action` (typed) /
`actual_value`, `reasoning` (free text), `override_reason_code` (reuses the **DK-8 12-reason taxonomy** →
`ai_classify`-able), and a divergence flag. This yields a **suggestion-adoption rate**, a map of *where the
recommender is trusted vs overridden and why*, and an honest app-vs-planner realized-value comparison — turning
every override into training data instead of a black box nobody follows.

**Data (all within guardrails, sources verified live 2026-09-03):**
- **Baseline** = start-of-day frozen watchlist exposure → snapshot `sandbox_operations.po_management.rc_value_baseline_daily`.
- **Per-action projected Δ** = the verified PAB/gap math (V2) × **commitment-weighted unit value**
  (`prod_operations.demand.fact_sop_commitment.frozen_blended_lag1_forecast_cost/_value`, joins item/dg5/series/date;
  `dim_series_ext_vw.standard_cost` fallback).
- **Realized** = next-snapshot forward low-point read-back (`20_supply_daily`, MIN(PAB) over window) **minus**
  found-inventory. **Mechanism confirmed live** (192,300 SKU-orgs comparable across two adjacent snapshots).
- **New Lakebase fields** on `action_request` / `action_outcome_history`: `suggested_action`, `suggested_value`,
  `actual_action`, `actual_value`, `reasoning`, `override_reason_code`, `savings_state`, `baseline_snapshot_id`.
  Realization published Lakebase→Delta into `…action_outcome_history`.

**Verdict:** ✅ data-ready — composes from validated pieces (V1 baseline, V2 delta, V13 recoverability gate, S10
phantom-heal, DK-8 reason codes) + forward Lakebase capture. New **Screen G · Value Ledger** (UX v1) + the
savings formula (measures) + action-record fields (ADR/Lakebase). No new source table required.

### DK-22 — Root-cause × week heatmap: recursive drill-down navigator *(customer request, 2026-09-03)*

**The ask:** an interactive heatmap of **root causes × weeks** at **different levels**, for the variances
observed — and **onclick to any cell, drill into a subset/next-layer heatmap.** It should tell the story of
where and when misses cluster.

**The heatmap IS the visual instantiation of the classifier layer** (temporal + convergence axes):
- **Horizontal band** (one cause, hot across many weeks) = **chronic** cause (V10 `temporal_class`).
- **Vertical band** (one week, hot across many causes) = a **convergence wave** (DK-13 / S7c).
- **Lone hot cell** = **acute** one-off.

**Two findings from live probing that reshape it from a generic heatmap (READ-ONLY, latest snapshot, 20 Global):**
1. **⚠ Weeks-by-volume are near-uniform** — 13 forward weeks, mean ~5,961 at-risk flags/week, **peak/mean only
   1.33×**, gentle near-term decay, no dramatic vertical bands. **A naïve count heatmap would be boring and
   slightly misleading.** The story is NOT on the week axis by volume — it's in **row concentration**
   (V11: 1 supplier = 3,035 SKUs = a blazing horizontal band) and in **$-weighting** (A-class $67.8k/SKU vs
   C-class look identical by count, 300× different by consequence). → **Rule: rows = cause/supplier/org;
   color = commitment-$-weighted AND signed (short=red, excess=blue); one fixed `process_date`.**
2. **✅ The recursive drill works — with a measured stop-rule.** Clicking a cell narrows the filter set and swaps
   the **row dimension** to the next level, keeping the week columns:

| Click on… | Child rows | Verified live |
|---|---|---|
| Portfolio | product-line / supplier | bands |
| Product-line / supplier | org (designated pool) | bands |
| **Designated pool** | **member inventory orgs** | ✅ **14 rows, 33,467→0 flags — strong band** |
| Org, or any cell with **< ~4 populated banding child rows** | **auto-degrades to the SKU list** | ✅ ABC-within-org collapsed to 1 row → list is correct |

**Two guardrails the probes forced (or the drill would lie):**
- **Child dimension must come from a *populated* column.** `local_planning_abc_code` on the supply fact is
  **100% NULL within the busiest org** — criticality must come from the `dim_series_ext_vw` join (the 37%
  Unclassified reality, V22), never that fact column. A drill onto an all-null child renders one empty band.
- **Stop-rule is measured, not fixed-depth.** Recurse only while the child has **≥ ~4 populated rows that band**;
  below that the leaf is the **SKU list** (the drill *target*), never a ~99%-empty SKU heatmap.

**Every hop:** carries a **breadcrumb + inherited filters** (cause=TTI · org=2120 · wk39; click a crumb to pop
up), **preserves the fixed snapshot vintage** (variance is snapshot-dependent — the priors finding, so levels
don't shimmer), keeps **$-weighted + signed** color (child speaks the parent's language), and **splits
convergence cells fractionally** by contribution (S7a) so multi-cause weeks don't inflate totals.

**Complements, not duplicates, S7c risk-wave:** the risk-wave is forward "*when* will it break" (1-D bars); the
heatmap is backward+forward "*what cause* has been driving misses, over time" (2-D, drillable).

**Verdict:** ✅ data-ready — aggregations over `20_supply_daily` (weeks) × {cause bucket / `origin_supplier_name`
/ designated-pool / member inv-org} × commitment-$ (`fact_sop_commitment`), served from a small pre-agg
(`rc_cause_week_heat`). New **UX v3 §S12**. No new source. Ships after the hero path (it reads the same spine).

### Data-mapping correction surfaced by this probing
- **Demand plans are product-line-split** — `10_demand_daily.plan_name` ∈ {`10 TOL`, `10 PRT`, `10 ACC`,
  `10 HND`, `10 QP`} (tools / parts / accessories / hand-tools / quoted-products), **not** the supply plans'
  `20 Global`/`20 Mexico`. Every demand query must filter the correct `10 *` plan(s). *(Folded into the data
  mapping + join model.)*

---

<div align="center">

### 📌 Provenance & confidence

Parts A–J trace to `supply_day3_discussion.md`; **Part K is data-sourced** (candidate scope, needs business validation).
Numbers (*~60%, 5–7 systems, 134%, 837 units, 6 months*) are **planner estimates / example
values** — not validated system facts. Domain definitions reflect what was *said in the room*;
several explicitly need a single agreed definition *(Part I)*.

**This is a read-only business-requirements capture. No data was written; no production schema was touched.**

</div>
