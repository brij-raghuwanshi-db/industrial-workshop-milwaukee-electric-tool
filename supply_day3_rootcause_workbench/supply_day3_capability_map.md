<div align="center">

# 🧭 Capability Map & Gap Analysis

### What each visual makes the user *able to do* — and what they still can't, even after all this

**Companions:** [`supply_day3_ux_design.md`](supply_day3_ux_design.md) · [`supply_day3_requirements.md`](supply_day3_requirements.md) · [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md)
**Purpose:** (1) for every visual capability in the UX design, name the **user capability** it introduces; (2) find what the business needs that we are **not** showing; (3) say concretely how to make planners **more capable.**

</div>

---

> ## 🎯 The core idea
>
> A visual is not a feature — it's a **capability grant.** A chart the user can't *act differently* because
> of is decoration. So below, every element is judged by one test: **"what can the planner now DO that they
> couldn't before?"** Then we ask the harder question — **what can they still NOT do**, and is that a
> deliberate scope line or a real gap the business will hit?

Two lenses used throughout:

**The closed loop** (from the control-tower domain pattern) — every capability sits at a stage:
```
   DETECT → CLASSIFY → EXPLAIN → DECIDE → ACT → PROVE → LEARN
   (what?)  (what      (why?)    (what    (do    (did it (get
             KIND?)               to do?)  it)    work?)  smarter)
```
> ⭐ **The validation (V10–V13) inserted the CLASSIFY stage** — between flag and explanation. Before recommending
> anything, tag the flag by **severity** (below-target vs hard-stockout, V1), **temporal class** (acute/chronic/
> nervous, V10), **convergence** (# co-firing causes, V11), **recoverability** (winnable vs committed loss, V13),
> and **action-verdict** (ACT/WATCH/DISMISS, V12). These tags decide *whether and how* to act — and they gate RCA
> depth: **full root-cause only for UNRECOVERABLE-and-material or chronic; fast-triage the recoverable; DISMISS
> the cushion dips.** Classify is what turns a 10,700-flag alarm into a ~3,600-row worklist.

**The capability ladder** — the planner's maturity journey:
```
   L0 React    L1 Explain    L2 Anticipate   L3 Decide     L4 Orchestrate   L5 Self-improve
   (hunt,      (one funnel,  (see it break   (recommend +  (cross-team +    (system proposes
    2 hrs,     fast, past-    before asked)   simulate the  supplier +       rule/forecast
    tribal)    focused)                       fix)          closed loop)     improvements)
```

---

## 📑 Contents
1. [Part 1 — Capability per visual (what each grants)](#part-1--what-each-visual-makes-the-user-able-to-do)
2. [Part 2 — Where the design lands on the ladder](#part-2--where-this-design-lands-on-the-ladder)
3. [Part 3 — What we are NOT showing that the business needs](#part-3--what-were-not-showing-that-the-business-needs)
4. [Part 4 — How to make users more capable (prioritized)](#part-4--how-to-make-users-more-capable-prioritized)
5. [Part 5 — Summary](#part-5--summary)

---

# Part 1 — What each visual makes the user able to do

*Each row: the visual → the user capability it introduces → the loop stage → whether it's genuinely new vs today.*

### Screen A · Watchlist / Control Tower

| Visual | User capability introduced | Loop | New vs today? |
|---|---|---|---|
| 4 KPI tiles (Δ vs last week) | **Sense the book's movement at a glance** — "are we getting better or worse this week?" without opening anything | Detect | New (today: no single pane) |
| Top-missing-items table, ranked by **$ at risk** | **Prioritize by money, not gut** — attack the biggest exposure first | Detect | New (today: ranked by units in Oracle, no $) |
| **Likely-cause chip** (Demand/Supply/Holds) | **Start already oriented** — skip the "is it demand or supply?" opening guess | Detect→Explain | New (today: pure tribal guess) |
| Trend sparkline + ▼ | **Distinguish worsening from stable** at the list level | Detect | New |
| "Mine" filter | **Work my portfolio** without wading through everyone's | Detect | Parity (Oracle filters exist) |

> **Net capability:** the planner can now **walk in and know where to look first, ranked by business
> impact, pre-classified by likely cause** — replacing the weekly manual Oracle "top missing items" review.

### Screen B · Root-Cause Investigation (hero)

| Visual | User capability introduced | Loop | New vs today? |
|---|---|---|---|
| Message-in-title (stated finding) | **Read the answer instead of deriving it** — the two-bullet is pre-written at the top | Explain | New (today: 2 hrs to assemble) |
| **Waterfall from safety-stock-at-lead-time** | **Decompose the gap into named, sized drivers** — see *how much* each cause contributed | Explain | New (today: mental math across tools) |
| Likely-cause triage strip (ranked, clickable) | **Pick the lever with confidence** — process-of-elimination made visible | Explain→Decide | New |
| Position-over-time (AC vs SS vs PAB) | **See *when* it broke and *how long* the risk lasts** — the risk period, not a point | Explain | Parity-ish (simulator shows this, but siloed) |
| "+ add PO receipt / simulate" (seed) | **Test a known constraint** (future) — override supply and re-project | Decide | New (future) |

> **Net capability:** the planner can **explain a bad position in one screen — quantified, time-shaped, and
> attributed** — instead of inferring it across 5–7 systems.

### Screen C · Driver drill-downs

| Visual | User capability introduced | Loop |
|---|---|---|
| **C1 Consumption** by DG5 + promo/base | **Name *who* drove it and *what kind* of demand** (Home Depot, base, +101u) | Explain |
| **C1 Priors matrix + slider** (late 1–6) | **Separate over-consumption from forecast-creep**, and see it at the vintage the item's lead time demands | Explain |
| **C2 Requested vs promise + slip days** | **Quantify the supplier slip** in days, precisely | Explain |
| **C2 "who moved it" (originator)** | **Assign accountability** — supplier-initiated vs planner pull-in | Explain→Learn |
| **C3 Holds / adjustments / quality** | **Rule out or confirm the long tail** — is it stuck, lost, or quality? | Explain |
| "Insert into escalation" | **Assemble the story from evidence**, not memory | Decide→Act |

> **Net capability:** the planner can **drill any driver to the grain they'd defend to a partner** — customer,
> PO, hold — and pull it straight into the escalation.

### Screen D · Escalation output

| Visual | User capability introduced | Loop |
|---|---|---|
| Two-bullet standardized draft | **Produce the deliverable in seconds, in the format the business trusts** | Act |
| Editable + actions-taken field | **Adjust with tribal knowledge the data lacks**, add the action | Act |
| Provenance footer + "verify" | **Send something trustworthy** — sources shown, nothing faked | Act |
| Send → outbox (not "done") | **Act without claiming false completion** — honest state | Act |

### Screen E · Action & outcome log

| Visual | User capability introduced | Loop |
|---|---|---|
| Root cause + action + status + outcome | **Remember what was found and done** — institutional memory replaces "he knows because he did it" | Learn |
| 5-state status (Sent≠Verified≠Recovered) | **Track honestly** without over-claiming | Prove→Learn |

### Screen F · Value & Impact

| Visual | User capability introduced | Loop |
|---|---|---|
| Time-to-answer / systems / adoption | **Prove the tool's worth from its own telemetry** — and evangelize it | Prove |
| Before/after time bars | **Quantify the savings** (the Day-1 success factor) | Prove |
| Impact ladder (proposed→verified→realized) | **Claim value honestly**, staged | Prove |
| Root-cause mix vs Pareto | **Steer where to invest next** from evidence | Learn |
| Outcome-proof table (gap at send vs +2wk) | **Prove an escalation actually changed the position** | Prove |

### Creative concepts

| Concept | User capability introduced | Loop |
|---|---|---|
| **C-1 "Why?" ribbon** | **Answer the partner in one click** — live causal narrative | Explain |
| **C-2 Time-machine scrubber** | **Watch the deterioration** and answer "one bad week or five straight months?" | Explain |
| **C-3 Pooled-vs-org ghosts** | **See past the misleading single-org record** to the true network + stranded stock | Explain |
| **C-4 "Who moved my PO?" badge** | **Hold suppliers accountable** — did they warn us or did we catch it? | Learn |
| **C-5 Living escalation** | **Reopen, re-run, and prove a case** over time | Prove |
| **C-6 Coverage-honesty band** | **Know where to trust the tool** and where it's reconstructing | Explain |
| **C-7 Similar-cases rail** | **Inherit the team's triage memory** instead of re-learning it | Learn |

### Cross-cutting

| Control | User capability introduced |
|---|---|
| Time slider (±6mo, week/month) | **Choose the window the problem lives in** — flexible per visit |
| Network toggle (`designated_org_code`) | **Roll up across orgs** — the thing they thought impossible |
| Genie rail | **Ask in natural language** for follow-ups the UI didn't pre-build |

---

# Part 2 — Where this design lands on the ladder

```
  L0 React ──► L1 Explain ──►│ L2 Anticipate    L3 Decide      L4 Orchestrate   L5 Self-improve
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│░░░░░░░░░░░░░░░   ░░░░░░░░░░░░░   ▓▒░░░░░░░░░░░░░   ░░░░░░░░░░░░░
   (was here)   ◄ THE DESIGN │  mostly gap      mostly gap      partial (log+    barely touched
                LANDS HERE   │                                  value loop = ▒)
```

**The design moves the planner decisively from L0 (React) to L1 (Explain).** That is the correct, honest
target — it's the transcript's Day-3 scope ("explain what happened in the past… something you can maybe
solve in two days") and the room's own warning against sprinting to prediction.

It also **touches L4** (the action log + value loop are early orchestration/learning) — but **L2 Anticipate
and L3 Decide are largely empty.** That's the gap the business will feel next, and Part 3 is about it.

---

# Part 3 — What we're NOT showing that the business needs

*Each gap: the missing capability · the business evidence it's real (mostly the transcript's own words) · what it would unlock · data feasibility (from the mapping doc) · what to do. Ordered by value-to-effort.*

---

### 🔴 GAP 1 — Forward risk: "what's about to break," not just "what broke"
- **Missing capability:** *Anticipate.* The whole design explains the **past**. The planner still can't open a view that says **"these 5 SKUs are healthy today but project below safety stock in 2–3 weeks."**
- **Business evidence:** *"what is my stock-out risk next week, two weeks, three weeks… how can I transfer to meet expectations"* — stated explicitly as the desired future state. It's also the difference between reacting to a partner's question and getting ahead of it.
- **Unlocks:** L2. Moves the planner from **reactive** (answer when asked) to **proactive** (act before the partner asks).
- **Feasibility:** 🟢 **The data is already there.** `20_supply_daily` projects PAB forward per week; my position chart already *draws* the projected (░) portion. We simply aren't **ranking the future crossings** into a "coming risk" list or alerting on them. Cheap.
- **What to do:** add a **"Coming Risk" tab** on the Watchlist — same table, ranked by *projected* SS-crossing date within the horizon, not just current gap. Near-zero new data.

> ⚠️ **Guardrail (the room's own):** don't cross into *predicting demand* ("I can tell you every SKU for the
> next month") — that's the trap they warned about. Forward **risk from the existing plan projection** is
> safe; a new demand forecast is not. Show the plan's own forward view, not an invented one.

---

### 🔴 GAP 2 — Prescription: recommend the fix, not just explain the cause
- **Missing capability:** *Decide.* We explain *why* and produce an escalation, but we never **propose the action**. The planner still chooses the fix from tribal knowledge.
- **Business evidence:** *"there's kind of a menu of options… first we work with the supplier, that gives you an overtime menu, we add shifts, add capacity — the stair steps."* The team has a **known, ordered playbook** the tool doesn't encode.
- **Unlocks:** L3. Turns the workbench from an explainer into a **decision assistant** — "given demand-driven, supplier-firm, here's the recommended stair-step: request pull-in → then overtime → then transfer 200 from 1080."
- **Feasibility:** 🟡 needs a **deterministic action-menu / policy layer** (versioned rules, not LLM-invented). The action fields already exist in Lakebase. Medium effort, high value.
- **What to do:** encode the "stair-step menu" as governed rules; surface a **Recommended Action** card on Screen B/D with the ranked options and the reason each is/ isn't available (MOQ, lead time). The LLM phrases it; the rules decide it.

---

### 🟠 GAP 3 — The simulator (real, not seeded)
- **Missing capability:** *Decide / what-if.* Planners **simulate daily in Excel** ("we all use these all day, every day") — override supplier capacity to 750/wk, plus/minus demand — and can't anymore in a governed tool.
- **Business evidence:** verbatim above; plus the specific 750/wk capacity-override example.
- **Unlocks:** L3. Test a constraint **before** committing to an escalation or action.
- **Feasibility:** 🟡 data ready (`20_supply_daily` components + templates); needs interactive recompute. I seeded it (R21) but deferred. Medium effort.
- **What to do:** promote the "+ simulate" seed to a real **Scenario panel** — editable supply/demand lines, live re-projection of PAB and the SS gap, "save scenario" to Lakebase. Two biggest templates: transition-level and multi-org-combined.

---

### 🟠 GAP 4 — Cross-SKU / systemic patterns (the portfolio view)
- **Missing capability:** *Detect at scale.* The design is **one SKU at a time.** A single **supplier slipping across 40 SKUs**, or **one customer over-consuming a whole category**, is invisible — you'd only see it by investigating 40 SKUs individually.
- **Business evidence:** planners **escalate at total-network level**, manage portfolios, and the Pareto itself (60% demand) is a *systemic* observation. Chronic issues are "recurring."
- **Unlocks:** L2/L4. Ask **"what is the single biggest driver across my whole book this week?"** — and escalate the *pattern*, not 40 tickets.
- **Feasibility:** 🟢 data ready — it's the same Gold, aggregated by supplier/customer/plant instead of by SKU.
- **What to do:** add a **"Patterns" view** — rank drivers (suppliers, DG5 customers, plants) by total $ at risk contributed across all at-risk SKUs. One query, high insight.

---

### 🟠 GAP 5 — Chronic vs acute (is this a one-off or a repeat offender?)
- **Missing capability:** *Learn / triage smarter.* The tool treats every investigation as fresh. It can't say **"this SKU has been below safety stock 6 of the last 8 weeks"** or "this supplier slips every month."
- **Business evidence:** *"we talk about the recurring issues"*; the distinction between "one week" and "five straight months" is one they raised explicitly; prior project work already flagged a **"chronic-slipper signal."**
- **Unlocks:** L2/L4. Separates **fire-fighting** (acute) from **fix-the-system** (chronic) — a different conversation and a different action.
- **Feasibility:** 🟢 snapshot history exists (371 vintages) + action log being built. Just needs a recurrence count.
- **What to do:** a **chronic badge** on the watchlist ("6/8 weeks at risk") and a chronic filter; feed chronic items to a systemic-fix backlog rather than a one-off escalation.

---

### 🟡 GAP 6 — Decompose the gap: "real demand" vs "the target just moved"
- **Missing capability:** *Explain, deeper.* When forecast rises, the **safety-stock target rises too** (forward days-of-coverage), so health looks worse **even if nothing physically changed.** The planner can't currently separate *"I actually consumed more"* from *"my target refreshed higher."*
- **Business evidence:** Carter's exact point — *"your health will look worse if they increase the forecast… because our safety stock will refresh and go 'your demand's higher, therefore hold more.'"* A genuinely subtle, high-value distinction.
- **Unlocks:** L1+. Stops planners from **reacting to a harmless target shift** as if it were a real shortage — prevents unnecessary buys (which the room worried about).
- **Feasibility:** 🟢 `safety_stock` is stored **per snapshot per week** — compare the SS target across vintages and split the gap into "demand actualized" vs "target moved." Cheap and clever.
- **What to do:** add a **two-tone band** to the waterfall/timeline: gap-from-real-consumption vs gap-from-target-refresh. Near-free from existing columns.

---

### 🟡 GAP 7 — Demand-team handoff (the fix lives on another team)
- **Missing capability:** *Orchestrate across teams.* 60% of issues are demand-driven — but the **fix** (validate/adjust the go-forward forecast) belongs to the **demand team**, on **different tools**. The tool root-causes it, then… the planner emails a human.
- **Business evidence:** *"working with the demand team to validate the go-forward forecast."* Two teams, two toolsets, a manual seam.
- **Unlocks:** L4. **Flag-to-demand-with-evidence** — one click sends the DG5/promo/priors evidence to demand planning as a structured request, tracked.
- **Feasibility:** 🟡 Lakebase outbox/notification pattern exists; needs a demand-side inbox or the shared Forecast Genie as the bridge.
- **What to do:** a **"Flag to Demand"** action that packages the demand-drill evidence into a tracked request (not a lost email); close the loop when demand responds.

---

### 🟡 GAP 8 — Supplier live signal
- **Missing capability:** *Orchestrate with suppliers.* Supplier production plans live in **weekly Excel, not connected** (mapping verdict ❌). The planner still can't see supplier commits in the tool — only Oracle's derived promise date.
- **Business evidence:** *"no live data shares with suppliers… back-and-forth Excel."* R27 wants the SharePoint PO-status file ingested.
- **Unlocks:** L4. Supplier slip visible *at source*, and eventually two-way.
- **Feasibility:** 🔴 external — needs the SharePoint→Delta ingestion (R27) then a supplier collaboration surface. Bigger lift.
- **What to do:** phase 1 — ingest the PO status file, flag requested-vs-supplier-date deltas; phase 2 — supplier portal / live share (separate initiative already flagged).

---

### 🟢 GAP 9 — Proactive push (from pull to alert)
- **Missing capability:** the tool is **pull** — the planner opens it. There's no **push** when a SKU crosses into risk.
- **Business evidence:** the question is asked ~once/day *reactively*; getting ahead means the tool tells you before the partner does.
- **Unlocks:** L2. "3697 just crossed into risk — root cause pre-built, click to review."
- **Feasibility:** 🟡 needs a scheduled Job + notification (Lakebase outbox / Teams/email). Depends on Gap 1 (forward risk).
- **What to do:** a weekly (or on-snapshot) alert that pushes newly-at-risk items with their pre-computed likely cause.

---

### 🟢 GAP 10 — Attribution confidence + business stakes
- **Missing capabilities (two smaller ones):**
  - **Attribution confidence** — when demand + supply + holds all contribute, how sure are we it's "*primarily* demand"? We show contribution size but not confidence.
  - **Business stakes context** — "$ at risk" is std cost; it doesn't know if this is a **strategic customer commitment** or long-tail. Not all 837-unit gaps are equal.
- **Business evidence:** planners weigh "which customer, is it a commitment" implicitly; the room stressed customer grain matters.
- **Unlocks:** sharper prioritization and trust.
- **Feasibility:** 🟡 confidence = a simple dominance ratio on contributions; stakes = join customer/commitment context (partly available).
- **What to do:** a small **confidence indicator** on the likely-cause chip; enrich `$ at risk` with customer-commitment weighting when that data lands.

---

## Gap scoreboard

| # | Missing capability | Ladder | Value | Effort | Data |
|---|---|:--:|:--:|:--:|:--:|
| 1 | Forward risk ("about to break") | L2 | 🔥🔥🔥 | Low | 🟢 ready |
| 2 | Prescription (action menu / stair-steps) | L3 | 🔥🔥🔥 | Med | 🟡 rules |
| 3 | Real simulator | L3 | 🔥🔥 | Med | 🟡 |
| 4 | Cross-SKU / systemic patterns | L2/L4 | 🔥🔥🔥 | Low | 🟢 ready |
| 5 | Chronic vs acute | L2/L4 | 🔥🔥 | Low | 🟢 ready |
| 6 | Gap decomposition (real vs target-moved) | L1+ | 🔥🔥 | Low | 🟢 ready |
| 7 | Demand-team handoff | L4 | 🔥🔥 | Med | 🟡 |
| 8 | Supplier live signal | L4 | 🔥🔥 | High | 🔴 external |
| 9 | Proactive push / alerts | L2 | 🔥🔥 | Med | 🟡 |
| 10 | Attribution confidence + stakes | L1+ | 🔥 | Low | 🟡 |
| 11 | Criticality / ABC $-triage (DK-16) | L1+ | 🔥🔥🔥 | Low | 🟢 ready |
| 12 | Lifecycle NPD/transition lens (N1) | L1+ | 🔥🔥 | Low | 🟢 ready |
| 13 | Intermittent-demand confidence (DK-18) | L1+ | 🔥🔥 | Low | 🟢 ready |
| 14 | Dormant / E&O scenario (DK-17) | L2 | 🔥🔥🔥 | Low | 🟢 ready |
| 15 | Found-inventory / heal detection (N4) | L1+ | 🔥🔥 | Low | 🟢 ready |
| 16 | Intentional-hold exclusion (DK-20) | L1+ | 🔥 | Low | 🟡 partial |
| 17 | Alignment % KPI + Sankey (DK-20) | L2 | 🔥🔥 | Low | 🟢 ready |
| 18 | Parameter proposal queue (DK-19) | L3 | 🔥🔥 | Med | 🟡 gated |

> Rows 11–18 are the **classifier-axis** capabilities detailed in **Part 3½**. Most are 🟢 data-ready and Low
> effort because they ride the existing conformed spine as dim-joins or cheap derived aggregations — they raise
> **priority quality (L1+)** and open the **excess/E&O scenario (L2)** without new pipelines.

---

# Part 3½ — New capabilities from the classifier axes (N/DK, validated V15–V26)

*Part 1 asked "what does each visual let the user DO." The classifier layer (severity · temporal ·
recoverability · verdict · convergence · **criticality · demand-class · lifecycle · dormant · hold**)
adds a set of new user capabilities that don't fit the original screen inventory. Each is data-validated;
each answers a question the planner cannot answer in any current system.*

| New signal (req / validation) | Today the planner… | With the axis they can… | New capability granted | Data |
|---|---|---|:--:|:--:|
| **Criticality — ABC** (DK-16 / V22) | treats a $68k A-item and a $200 C-item as one "red" | **rank the same shortage by dollars-at-risk**, escalate A-class first, auto-**dismiss** C-class noise | *Triage by consequence, not just by symptom* — the ACT/WATCH/DISMISS verdict gets a dollar spine | 🟢 `inventory_abc_class` |
| **Lifecycle — NPD / transition** (N1 / V15) | reads a launch-item's thin history as "chronic under-plan" | **suppress the false-chronic flag** for NPD/transition SKUs, apply a launch playbook instead | *Stop mis-diagnosing new items as broken* — 71.5k transition / 4.0k NPD SKUs get the right lens | 🟢 `transition_sku_flag`, `is_npd_item` |
| **Demand-class — intermittent** (DK-18 / V24) | shows a mean/CV on lumpy demand that means nothing | **flag ~24% of SKUs as intermittent**, show a low-confidence band, avoid over-reacting to a single spike | *Know when the statistics are trustworthy* — confidence follows demand pattern | 🟢 ADI proxy (derived) |
| **Dormant / E&O** (DK-17 / V23) | has no view of value **not moving** (only shortages) | **see the other half of the balance sheet**: $545M never-shipped, $16M dormant, by org/class | *Surface excess & obsolescence as first-class* — a whole scenario the shortage app was blind to | 🟢 last-ship recency (derived) |
| **Found-inventory / heal** (N4 / V18) | sees a shortage clear and doesn't know **why** | **distinguish a real fix from a phantom heal** — +81.9M signed adjustments over 25k events | *Trust that a resolved flag was actually solved*, not an inventory correction masking the problem | 🟢 signed `transaction_quantity` |
| **Intentional-hold** (DK-20 / V26) | can't tell a planned reserve from an unplanned pile | **exclude managed/reserved stock** ($450M) from "excess," avoid recommending action on deliberate inventory | *Don't fight the plan* — WATCH/DISMISS respects intent | 🟡 `safety_stock_managed_flag` |
| **Inventory alignment %** (DK-20 / V26) | has no single number for "how healthy is the whole book" | **watch one portfolio KPI** (54% aligned) trend week-over-week, drill via a **Sankey** (Total $ → ABC → health) | *A portfolio health headline* — the exec/S&OP view above the SKU grind | 🟢 gap × on-hand × ABC |
| **Parameter proposal queue** (DK-19 / V25, scope-corrected) | edits SS in the source system, untracked | **propose a governed parameter change** in-app, route for approval, log outcome | *A safe, auditable "change the plan input" path* — even though auto-ROP is blocked (projection-based) | 🟡 workflow (SS method gates recommender) |

### How these reshape the four-verb loop
- **Detect** gains a second dimension: not just "PAB went negative" but **"…on an A-class, committed, chronic item"** vs **"…on a C-class, recoverable, NPD-launch item."** Same detector, radically different priority.
- **Classify** is where all of these live — they are the axes of the Classify stage. Criticality gives the **$ weight**, lifecycle/demand-class give the **confidence & applicability**, dormant/found/hold give the **is-this-even-a-problem** gate.
- **Explain** inherits them as guardrails: don't explain an NPD item as chronic; don't explain a healed-by-adjustment shortage as a supply win.
- **Act** inherits the **verdict spine**: A-class committed acute → ACT; C-class recoverable nervous → DISMISS; managed-hold excess → leave alone.

### What the planner is *newly able to do* (one line each)
1. **Escalate by dollars, not by red.** (criticality)
2. **Trust — or distrust — a measure based on the demand pattern behind it.** (demand-class)
3. **Give new-product launches their own playbook instead of a false chronic label.** (lifecycle)
4. **See excess and dormancy, not only shortage** — the balance sheet's other half. (dormant/E&O)
5. **Tell a real fix from a phantom heal.** (found-inventory)
6. **Leave deliberate reserves alone.** (intentional-hold)
7. **Report one portfolio-health number and drill it visually.** (alignment % + Sankey)
8. **Propose a plan-input change safely and track the outcome.** (proposal queue)

> **Net:** the original design made the planner able to *explain the past fast*. The classifier axes make them
> able to *prioritize by consequence, calibrate their own confidence, and see the problems the shortage-only
> app couldn't* — without adding a single un-validated signal or violating the read-only guardrail.

### DK-21/DK-22 · Value Ledger + heatmap navigator — three more capabilities (prove-it + learn-from-me + see-the-pattern)
| New signal (req / validation) | Today the planner… | With it they can… | New capability | Data |
|---|---|---|:--:|:--:|
| **Incremental savings ledger** (DK-21) | can't show what a day of triage was *worth*; ROI is a slide | **watch a live running "protected today" counter** (🔵 projected) and a trailing **✅ realized** total, built action-by-action | *Prove the tool's worth from its own telemetry, honestly* — projected on click, realized only on read-back | 🟢 PAB Δ × committed value; read-back verified |
| **Suggested-vs-actual capture** (DK-21) | takes a different action than suggested; the reason is lost | **log the actual action + reasoning + reason code** whenever they diverge | *Turn every override into training data* — adoption rate, trust map, app-vs-planner realized comparison | 🟢 Lakebase fields + DK-8 taxonomy |
| **Cause × week heatmap navigator** (DK-22) | scans SKU lists one at a time; can't *see* where/when misses cluster | **read the pattern in one grid** — horizontal band = chronic cause, vertical band = convergence week, lone cell = acute — then **click to drill the subset** into the next level, down to the SKU list | *See the temporal + convergence classifier axes visually, and navigate cause→org→SKU by clicking* — the classifier layer made spatial | 🟢 `rc_cause_week_heat` pre-agg (banding + stop-rule verified live) |

**Why this is a capability, not a report:** it closes the loop the room asked for — *"quantify the savings"* —
without the over-claim trap. The planner gains the ability to **stand behind a number** (realized, read-back-proven)
and the recommender gains the ability to **get better** (every divergence is labeled feedback). The honest
3-state model is what makes both trustworthy: a counter that jumped "+$412k" on click would be the fastest way
to lose the room.

---

# Part 4 — How to make users more capable (prioritized)

**The pattern in the gaps:** the design nails **Explain (L1)** but the business already operates at **Anticipate
(L2)** and **Decide (L3)** in their heads and in Excel. The highest-leverage moves close *that* distance —
and most are cheap because **the data already exists** (we're re-framing, not re-sourcing).

### 🥇 Do-now (cheap, data-ready, high value) — the "L1→L2 leap"
1. **Coming-Risk tab** (Gap 1) — rank forward SS-crossings from the projection we already draw.
2. **Patterns view** (Gap 4) — aggregate drivers by supplier/customer/plant across the whole book.
3. **Chronic badge** (Gap 5) — recurrence count from snapshot history.
4. **Gap decomposition** (Gap 6) — split real-consumption vs target-refresh from stored SS vintages.

> These four turn the planner from *"I explain what happened"* to *"I see what's coming and what's systemic"*
> — with almost no new data plumbing. **This is the single most capability-per-effort move available.**

### 🥈 Next (medium effort, decision-grade) — the "L2→L3 leap"
5. **Recommended-action menu** (Gap 2) — encode the stair-step playbook as governed rules.
6. **Real simulator** (Gap 3) — promote the seed to a scenario panel.
7. **Proactive alerts** (Gap 9) — push newly-at-risk items (needs #1).

### 🥉 Then (orchestration) — the "L3→L4 leap"
8. **Flag-to-Demand handoff** (Gap 7) — structured, tracked cross-team request.
9. **Supplier ingestion → collaboration** (Gap 8) — R27, then two-way.
10. **Confidence + stakes** (Gap 10) — sharpen trust and prioritization.

### The through-line
Everything above still obeys the room's discipline: **explain honestly before predicting, propose from
governed rules (never LLM-invented), and never claim improvement before read-back.** We make planners more
capable not by adding a crystal ball, but by **surfacing what the plan already knows** (forward risk,
patterns, chronicity, target movement) and **encoding what the team already does** (the stair-step playbook)
— so their expertise is amplified, not replaced.

---

# Part 5 — Summary

- **What each visual grants** (Part 1): the design walks the planner cleanly through **Detect → Explain →
  Act → Prove**, replacing a 2-hour, 5–7-system, tribal hunt with a guided funnel.
- **Where it lands** (Part 2): a decisive, *correct* **L0→L1 (React→Explain)** leap, lightly touching L4 via
  the action + value loop. Deliberately past-focused, per the room's scope.
- **What's still missing** (Part 3): the business already lives at **L2 Anticipate** and **L3 Decide** — so
  the felt gaps are **forward risk, prescription, simulation, systemic patterns, chronicity, gap
  decomposition, cross-team handoff, and supplier signal.**
- **How to make them more capable** (Part 4): **four cheap, data-ready moves** (coming-risk, patterns,
  chronic, gap-decomposition) close most of the L1→L2 distance immediately; the stair-step **action menu** and
  **simulator** open L3 — all without violating the "explain-first, rules-not-guesses, verify-before-claiming"
  discipline.

<div align="center">

### 📌 One line
**The design makes planners able to *explain the past fast and honestly*; to make them truly more capable, we
next surface what the plan already knows about the *future and the patterns*, and encode the *playbook they
already run* — turning an explainer into an anticipator and a decision partner, without ever pretending to
predict what it can't.**

</div>
