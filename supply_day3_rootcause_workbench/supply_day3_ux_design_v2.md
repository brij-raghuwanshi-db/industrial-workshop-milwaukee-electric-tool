<div align="center">

# 🎨 Supply Root-Cause Workbench — UX Design **v2**

### What the front end becomes now that every gap has a confirmed source

**Companions:** [`supply_day3_ux_design.md`](supply_day3_ux_design.md) (v1) · [`supply_day3_gap_tables.md`](supply_day3_gap_tables.md) · [`supply_day3_capability_map.md`](supply_day3_capability_map.md)
**What changed since v1:** v1 was scoped to *explain the past (L1)* because that's all we'd confirmed. The gap→table pass proved **7 of 10 gaps are data-ready today** and surfaced new tables (`fact_sop_commitment`, `ops_scorecard_fill_rate_vw`, work-center capacity, MOQ family). So the UI can now climb to **Anticipate (L2)** and **Decide (L3)** — this doc is that evolved design.

</div>

---

> ## 🎯 The shift in one line
> **v1 answered "how did we get here?" v2 also answers "what's about to break, what's the pattern, and what should I do about it?"** — because the data to do so is confirmed present, not aspirational.
>
> ```
>   v1 (shipped scope):   DETECT → EXPLAIN → (escalate) → PROVE
>   v2 (now unlocked):    ANTICIPATE → DETECT → EXPLAIN → DECIDE → ACT → PROVE → LEARN
>                         └ new ┘                          └ new ┘              └ new ┘
> ```

**How to read this doc:** §A = what gets *added to existing v1 screens*. §B = *net-new screens/panels*. §C = the new *component + table bindings*. §D = revised information architecture. §E = build sequence. Every addition cites the gap (G1–G10) and the confirmed table.

---

## 📑 Contents
- [A · Upgrades to existing v1 screens](#a--upgrades-to-existing-screens)
- [B · Net-new screens & panels](#b--net-new-screens--panels)
- [C · New component + table bindings](#c--new-component--table-bindings)
- [D · Revised information architecture](#d--revised-information-architecture)
- [E · Build sequence (v1 → v2)](#e--build-sequence)
- [F · What still can't be built, and why](#f--what-still-cant-be-built)

---

# A · Upgrades to existing screens

*Each v1 screen gains capability from a now-confirmed table — no rebuild, just additions.*

### A.1 · Watchlist (Screen A) gains three things

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  Supply Root-Cause Workbench   [Network ▾]  [Plan ▾]     [ Now | ⚡Coming Risk | Patterns ]│◄ NEW tabs
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ◆ At risk NOW   ◆ ⚡Crossing in ≤3wk   ◆ $ at risk (committed)   ◆ Chronic (6/8wk+)     │◄ NEW tiles
│    47              18  ▸ act early          $2.1M ▲                  9  🔁               │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  SKU     Desc        Low pt  Wks   Likely    $ at risk   Chronic  Trend                  │
│  2941 ▸  M18 FUEL    -837    Oct   🟦 Demand  $412k ⭐    🔁 6/8   ▁▂▃▅▇▼                  │◄ NEW: chronic + ⭐committed
│  4811 ▸  PACKOUT     -1,240  6wk   🟧 Supply  $388k       —        ▂▂▃▄▆▼                  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

| Addition | Capability | Gap | Confirmed table |
|---|---|---|---|
| **⚡ "Coming Risk" tab** | rank SKUs *projected* to cross below SS in ≤N weeks — act before asked | G1 | `20_supply_daily` (verified ~110 fwd weeks w/ PAB+SS) |
| **"Patterns" tab** | biggest driver across the whole book (supplier/customer/plant), not per-SKU | G4 | same Gold grouped by `origin_supplier_number` / `mkedg5` / `designated_org_code` |
| **🔁 Chronic badge** | "6 of last 8 weeks at risk" — separate fire-fighting from fix-the-system | G5 | `20_supply_daily` snapshot history (55 snaps/2mo verified) |
| **⭐ Committed-$** | rank by *commitment-weighted* exposure, not bare std cost | G10 | `demand.fact_sop_commitment` (lag-1 value/cost by DG5) |
| **Ⓐ Criticality badge** | ABC $-triage — A-class shortage outranks a C-class one at equal gap | DK-16 | `dim_series_ext_vw.inventory_abc_class` (A=$67.8k/SKU, 2.1×C) |
| **🌱 Lifecycle chip** | NPD/transition suppress false-chronic → launch playbook not a fire | N1 | `items_scd1.transition_sku_flag`, `is_npd_item` (71.5k/4.0k) |

> **New default sort (v3 spine):** `criticality × recoverability × convergence`, not raw gap. See v3 §S-classify+
> for the five axes and §S8–S10 for the excess/E&O, portfolio-health, and found-inventory screens they open.

### A.2 · Hero investigation (Screen B) gains the two-tone gap + confidence

```
┌─ WATERFALL ──────────────────────────────┬─ LIKELY CAUSE ──────────────────────┐
│  SS@LT ─┐                                 │ 🟦 DEMAND  +101u ▓▓▓▓▓▓ 71%  🎯 High │◄ NEW confidence
│    904  │▓▓  ← gap splits into:           │ 🟧 SUPPLY  -40u  ▓▓ 20%              │
│         │▒▒ target refreshed (+352) NEW   │ 🟪 HOLDS   -18u  ▓ 10%               │
│         │▓▓ real consumption (-101)       │                                     │
│         └──► GAP -904 🔴                   │ 🎯 = how dominant the top cause is   │
└──────────────────────────────────────────┴─────────────────────────────────────┘
```

| Addition | Capability | Gap | Confirmed table |
|---|---|---|---|
| **Two-tone gap band** | split "I consumed more" vs "my SS target refreshed higher" (Carter's point) | G6 | `20_supply_daily` self-join across `process_date` (proved live: SS 68→420 same target week) |
| **🎯 Confidence indicator** on the top cause | "how sure are we it's *primarily* demand?" | G10 | derived ratio of bucket contributions (no table) |
| **⚠ SS-refresh decision-trap callout** (DK-12) | when position looks worse *and* both demand+SS-target rose together, say so: *"~18% of this gap is the safety-stock target refreshing on higher demand — not a physical shortage; don't over-buy"* | DK-12 | `20_supply_daily` self-join; verified: demand ~+220%, SS target ~+17.6% together; ~1.3% of series → targeted callout, not universal |
| **🚦 ACT / WATCH / DISMISS verdict** (DK-14) | a three-way badge on every flagged row — `ACT` (near-term + physical), `WATCH` (real but not-yet / target-artifact / far-out → monitor), `DISMISS` (cushion dip / transient → false-alarm-by-design, closed with recovery evidence) | DK-14 | verified: only 34% of below-SS flags ever stock out; **66% DISMISS**. Turns a 10,700-row alarm into ~3,634 ACT. DISMISS shows root cause **and** the recovery ("dips −200 wk38, recovers wk39") |

### A.3 · Supply drill (Screen C2) gains a supplier scorecard

```
┌─ SUPPLY — PO timing + supplier reliability ────────────────────────┐
│  "PO 380… slipped 21d (SUPPLIER). Acme fill rate 88%, 3 misses/qtr" │◄ NEW reliability line
│  … PO table (v1) …                                                  │
│  ── Supplier scorecard: Acme Cordless ──────────────────────────    │◄ NEW mini-panel
│   Fill rate 88% ▼   SupplyMiss 3   chronic-slip 🔁   [ view all POs ]│
└─────────────────────────────────────────────────────────────────────┘
```

| Addition | Capability | Gap | Confirmed table |
|---|---|---|---|
| **Supplier scorecard mini-panel** | is this supplier a repeat offender, or a one-off? | G8 | `sales.ops_scorecard_fill_rate_vw` (`SupplyFR`, `SupplyMiss` by supplier) + `purchase_order_change_orders` |

### A.4 · Escalation (Screen D) gains commitment context + recommended action
- Escalation now states **committed $ at risk** (not just std cost) — `fact_sop_commitment`. (G10)
- Escalation carries the **recommended action** from the new Action panel (below). (G2)

---

# B · Net-new screens & panels

*The capabilities v1 couldn't offer at all — now buildable.*

### B.1 · ⚡ Coming-Risk board *(new — the L1→L2 leap)*
*Genre: control-tower. The proactive counterpart to the reactive watchlist.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ COMING RISK — projected to cross below safety stock (next 8 weeks)   [ ≤2wk|≤4wk|≤8wk ]│
├───────────────────────────────────────────────────────────────────────────────────────┤
│  SKU     Healthy now?  Crosses    Weeks to   Depth at    Likely cause   Committed $  Act  │
│                        (week)     crossing   low point   (pre-computed)               │
│  ┌────────────────────────────────────────────────────────────────────────────────┐    │
│  │ 5820 ▸  ✅ today     wk39       +3 wks     -420 units  🟧 PO gap      $210k ⭐    [▸]│    │
│  │ 6104 ▸  ✅ today     wk41       +5 wks     -180 units  🟦 Demand      $95k       [▸]│    │
│  └────────────────────────────────────────────────────────────────────────────────┘    │
│   Within lead time? ⚠ 5820 crosses INSIDE its lead time — can't fully recover by ordering │◄ lead-time-aware
│   Freshness: snapshot Mon 08-31 · projection from plan's own forward PAB (not a new forecast)│
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Why it matters:** the transcript's explicit wish — "what's my stock-out risk next week, two, three weeks." Turns the planner from reactive to proactive.
- **Lead-time-aware flag** (G1 + `complete_lead_time`): if the crossing is *inside* the lead time, ordering now won't fix it — that's a transfer/expedite case, flagged distinctly.
- ⭐ **Upgrade to the full recoverability class (V13/DK-15):** this flag becomes the `RECOVERABLE` / `UNRECOVERABLE`
  serving column. Live: **98% of crossings are UNRECOVERABLE** (breach inside the fence, $372.5M) — so Coming-Risk
  must lead with *"can this still be won?"* not just *"when does it cross?"*. UNRECOVERABLE rows route to
  **damage-control** (TRANSFER if in-network excess — 20%, else ALLOCATE — 80%), never a PO. Uses **per-SKU**
  `complete_lead_time` (bimodal — never an average).
- **Guardrail honored:** uses the plan's own forward PAB (`20_supply_daily`), *not* an invented demand forecast.
- 🎯 **DK-9 — transfer-to-cover is built in, not a separate screen.** Verified live: **7,508** forward crossings (next qtr) are coverable by transferring same-SKU excess from another in-network org (4.6× the near-term 1,646), over dense proven lanes (2012↔2013, 1080→2012/2014). So each Coming-Risk row's **[▸] action first checks "is there in-network excess to transfer?"** → "crosses wk39 → transfer 300 from 1080 (lane exists, ~1wk) → covered" *before* proposing a buy. This fuses Coming-Risk (G1) + Rebalance (S2) into one forward workflow — exactly the planners' "how can I transfer to meet expectations."

### B.2 · 🔎 Patterns view *(new — systemic, not per-SKU)*
*Genre: analytic. "What's the single biggest driver across my whole book?"*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  🔎 PATTERNS — drivers ranked across all at-risk SKUs      [ by Supplier | Customer | Plant ]│
├───────────────────────────────────────────────────────────────────────────────────────┤
│  ▸ BY SUPPLIER                                                                            │
│   Acme Cordless    ▓▓▓▓▓▓▓▓▓▓  $612k   across 14 SKUs   fill 88% 🔁   [ escalate pattern ▸]│◄ one escalation,
│   Bolt Industrial  ▓▓▓▓▓       $310k   across  6 SKUs   fill 94%      [ escalate pattern ▸]│  not 14 tickets
│   …                                                                                       │
│  ▸ BY CUSTOMER (DG5)                                                                      │
│   Home Depot       ▓▓▓▓▓▓▓▓    $488k   over-consuming across 9 SKUs   [ flag to demand ▸ ] │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
- **Why it matters:** planners escalate at network level and chase recurring issues. One supplier slipping 14 SKUs is *one* conversation, not 14 investigations.
- **"Escalate pattern"** / **"Flag to demand"** act on the whole cluster at once. (G4 + G7)

### B.3 · 🎛️ Scenario Studio *(new — the simulator, governed)*
*Genre: analytic/interactive. The Excel simulator, in-tool.*

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  🎛️ SCENARIO — 2941 · what-if            [ Reset ] [ Save scenario ] [ Apply to escalation ]│
├──────────────────────────────────────────┬──────────────────────────────────────────────┤
│  OVERRIDE LINES (editable)                │  RE-PROJECTED POSITION (live)                 │
│   Incoming supply:  [ 750 ]/wk  (was 900) │   ─ ─ SS ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │
│   Demand:           [ +0% ▾ ]             │   ▓▓▓▓▓▓▒▒▒░░░░  baseline (dashed)             │
│   Add transfer:     [ 200 from 1080 ▾ ]   │   ▓▓▓▓▓▓▓▓▓▒▒░░  scenario (solid) ← recovers wk40│
│  ⚠ MOQ 250 · multiple 50 · lead 3wk       │   Gap: -904 → -120  ($412k → $54k at risk)     │◄ instant delta
│    (constraints enforced)                 │                                                │
└──────────────────────────────────────────┴──────────────────────────────────────────────┘
```
- **Why it matters:** "we all use these all day, every day." Overriding a supplier cap to 750/wk and seeing the re-projection is the daily Excel move — now governed, constraint-aware, and saveable.
- **Constraints enforced** (G2): MOQ/multiple/lead-time from `dim_series_ext_vw` — the sim can't propose an impossible order.
- **Recompute in-app**, seeded from `20_supply_daily` component columns (G3); scenarios saved to **Lakebase**, never `prod_edw`.

### B.4 · 🧭 Recommended-Action panel *(new — the L3 leap)*
*Appears on Screen B/D. The stair-step playbook, ranked, each option gated by real feasibility.*

```
┌─ 🧭 RECOMMENDED ACTIONS (stair-step, ranked) ─────────────────────────┐
│  Given: demand-driven, supplier firm, -904u gap at wk36               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ 1. Request supplier pull-in   feasible ✅   ~covers 300u   [▸] │    │◄ ranked menu
│  │ 2. Transfer 200u from 1080    feasible ✅   pooled avail   [▸] │    │
│  │ 3. Add shift (make org)       capacity ⚠ 60%  +overtime$  [▸] │    │
│  │ 4. Change PO qty → 1000       MOQ ok, mult ok            [▸] │    │
│  │ 5. Escalate to demand (fcst)  60% root cause             [▸] │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  each option: rule-decided (not AI-invented), reason shown, 1-click log│
└────────────────────────────────────────────────────────────────────────┘
```
- **Why it matters:** the room described a **known ordered playbook** the tool never encoded. This makes the planner a *decider*, not just an explainer.
- **Every option gated by confirmed data** (G2): pull-in (supplier/lead-time in `dim_series_ext_vw`), transfer (pooled availability G7), add-shift (`work_center_scd1`/`domain_work_order`), PO qty (MOQ family). **Rules decide; the LLM only phrases.**

### B.5 · 🔔 Alerts inbox *(new — push, not pull)*
```
┌─ 🔔 NEW THIS SNAPSHOT ───────────────────────────────┐
│  ⚡ 3697 crossed into risk (wk38) — cause pre-built ▸ │
│  🔁 Acme slipped a 5th SKU this month ▸               │
│  ✅ 4811 recovered after your pull-in ▸               │
└───────────────────────────────────────────────────────┘
```
- **Detection ready** (G9): snapshot-over-snapshot diff on `20_supply_daily`. Delivery = Lakebase outbox + a Lakeflow Job on snapshot arrival. Turns the ~once-a-day question into a *pushed* queue.

---

# C · New component + table bindings

*Only components exported from `@databricks/appkit` / `@databricks/appkit-ui`; confirm props via `npx @databricks/appkit docs`.*

| New UI element | AppKit component | queryKey → confirmed source | Gap |
|---|---|---|---|
| Coming-Risk board | `Table` (server sort) + `Badge` (within-lead-time) | `coming_risk` → `20_supply_daily` fwd + `dim_series_ext_vw.complete_lead_time` | G1 |
| Patterns view | `BarChart` (horizontal, ranked) + `Table` | `pattern_by_supplier/customer/plant` → Gold grouped | G4 |
| Chronic badge | `Badge` | `chronic_count` → `20_supply_daily` snapshot window | G5 |
| Two-tone gap band | `BarChart` (stacked bridge) | `gap_decomp` → `20_supply_daily` self-join over `process_date` | G6 |
| Confidence indicator | `Badge` / small meter | derived (bucket dominance) | G10 |
| Committed-$ column/tile | `Table` col + `Card` | `committed_value` → `demand.fact_sop_commitment` | G10 |
| Supplier scorecard panel | `Card*` + `Table` | `supplier_scorecard` → `sales.ops_scorecard_fill_rate_vw` + `purchase_order_change_orders` | G8 |
| Scenario Studio | `Input`/`Select` + `LineChart` (live) | seed `scenario_seed` → `20_supply_daily` components; recompute in-app; save → Lakebase | G3 |
| Recommended-Action panel | `Card` + `Table` + `Button` | `action_options` → rules over `dim_series_ext_vw` MOQ + `work_center_scd1` + pooled avail | G2 |
| Alerts inbox | `Table`/list + `Badge` | `new_risk` → `20_supply_daily` snapshot diff; deliver via Lakebase outbox | G9 |
| Flag-to-Demand / Escalate-Pattern | `Button` → Lakebase | write `action_request` / `integration_outbox` | G4/G7 |

> **Notation carries over (IBCS):** new charts reuse the v1 scenario marks — actual solid `--foreground`, SS dashed reference, scenario/projection muted or hatched; Demand/Supply/Holds keep their three tokens everywhere (UNIFY). The two-tone gap band uses a diverging split (consumption vs target-move), not two arbitrary colors.

---

# D · Revised information architecture

```
                          ┌─────────────────────────────────────────────┐
        ⚡ Coming Risk ───►│                                             │
        🔔 Alerts ────────►│   1. WATCHLIST  (Now / Coming / Patterns)   │  ← ANTICIPATE + DETECT
                          │        │                                     │
                          └────────┼─────────────────────────────────────┘
                                   ▼ pick SKU (or pattern)
                          ┌─────────────────────────────────────────────┐
                          │   2. INVESTIGATION (waterfall + triage       │  ← EXPLAIN
                          │      + two-tone gap + confidence)            │
                          │        │            │            │           │
                          │   ┌────▼───┐  ┌─────▼────┐  ┌────▼─────┐      │
                          │   │ Demand │  │  Supply  │  │  Holds   │      │  ← EXPLAIN (drill)
                          │   │ drill  │  │ + scorecd│  │  drill   │      │
                          │   └────────┘  └──────────┘  └──────────┘      │
                          │        │                                      │
                          │   ┌────▼──────────┐   ┌──────────────────┐    │
                          │   │ 🎛️ Scenario    │──►│ 🧭 Recommended   │    │  ← DECIDE
                          │   │    Studio      │   │    Actions       │    │
                          │   └────────────────┘   └────────┬─────────┘    │
                          └───────────────────────────────── │ ───────────┘
                                                              ▼
                          ┌─────────────────────────────────────────────┐
                          │   3. ESCALATION (committed-$ + rec. action)  │  ← ACT
                          └────────┬─────────────────────────────────────┘
                                   ▼
                          ┌─────────────────────────────────────────────┐
                          │   4. ACTION LOG → 5. VALUE & IMPACT          │  ← PROVE + LEARN
                          │      (+ chronic feed, pattern feed)          │
                          └─────────────────────────────────────────────┘
```

**What's new structurally:** two *entry points above the watchlist* (Coming Risk, Alerts) push the planner into the loop proactively; a *decide layer* (Scenario + Actions) sits between Explain and Act; the Learn loop now feeds chronic/pattern detection back to the top.

---

# E · Build sequence (v1 → v2)

*v1 hero path ships first (all ✅ data). v2 additions layer on, cheapest-highest-value first.*

| Wave | Additions | Gap | Effort | Why this order |
|---|---|---|:--:|---|
| **v1** | Watchlist → Waterfall → Demand drill → Escalation (+ session timers) | — | — | proves 2hr→8min; already scoped |
| **v2.1** (cheap, data-only) | Coming-Risk tab · Patterns tab · Chronic badge · Two-tone gap · Committed-$ | G1,4,5,6,10 | Low | pure query/aggregation over confirmed Gold — biggest capability-per-effort |
| **v2.2** (decision layer) | Supplier scorecard · Recommended-Action panel | G8,2 | Med | scorecard = new view; actions = rules layer (data ready) |
| **v2.3** (interactive) | Scenario Studio | G3 | Med | recompute engine + Lakebase scenario store |
| **v2.4** (orchestration) | Alerts inbox · Flag-to-Demand/Escalate-Pattern | G9,7,4 | Med | needs Jobs + Lakebase workflow objects |
| **v3** (external) | Supplier forward-capacity ingestion + collaboration | G8 (R27) | High | SharePoint→Delta first, then two-way |

> **Sequencing insight:** **v2.1 is almost free** — five genuinely new user capabilities (anticipate, patterns, chronicity, honest-gap, stakes) that are *pure queries* over data we already confirmed. That wave alone moves the planner from L1→L2. Do it right after the v1 hero path.

---

# F · What still can't be built

Honest scope line — even after all this, two things remain out of reach and the UI must say so:

| Not buildable yet | Why | UI treatment |
|---|---|---|
| Supplier **forward production capacity / weekly commit** | external (weekly Excel), not ingested — Activity 8 ❌ | Scenario Studio's "supplier cap" is a *manual override*, labelled "not from a live feed"; Coming-Risk can't see a supplier's future commit |
| Statistical-vs-DOC safety-stock **overlay** | 22 SS Stat/DOC plans exist in dimension but **0 rows in fact** | show current method only; add the overlay when those plans activate |
| **Realized** downstream $ (vs verified) | needs downstream actuals confirmation | Value page keeps realized separate/muted (impact-ladder honesty) |

Everything else in this v2 is backed by a table confirmed live on `mke-rsc`.

---

# G · AI-optional elements (show both — with & without AI)

*Databricks AI functions were live-tested on this workspace (`ai_gen`, `ai_classify` ✅; `ai_forecast` present;
`ai_parse_document` standard — see [`supply_day3_ai_functions_opportunities.md`](supply_day3_ai_functions_opportunities.md)).
The rule: **every screen fully works WITHOUT AI**; AI is an optional layer that removes friction or unblocks
unstructured input — never load-bearing for a verified number. So each AI-touched element ships in two modes:*

| Element | Without AI (baseline — always works) | With AI (optional enhancement) |
|---|---|---|
| **Escalation draft** (Recommended-Action → Escalation) | templated string fills verified numbers into a fixed sentence | `ai_gen` writes fluent, multi-driver prose (tested ✅) — a "wow", not a new capability |
| **Alerts inbox** | rule-detected newly-at-risk rows, plain text | `ai_gen` one-line human summary per alert |
| **Rejection / hold reasons** (feedback loop) | planner picks category from a dropdown | `ai_classify` auto-buckets free-text (tested ✅), planner corrects |
| **Coming-Risk / forward view** | plan's own PAB projection (verified, deterministic — the primary view) | `ai_forecast` optional "second-opinion" lens, labelled experimental |
| **Supplier capacity feed** (the §F ❌) | stays "not connected" placeholder | `ai_parse_document` parses the Excel/SharePoint files → live 🟡 feed (the biggest unlock) |

**Every AI output wears the 🟡 provenance badge** (per the measures doc's show-everything-with-distinctions
system) and carries an "AI-generated — verify" note. **Build order:** baseline first (deterministic), AI as a
fast-follow toggle — so the product is trustworthy on day one and gets the AI polish without a rebuild.

---

<div align="center">

### 📌 v2 in one line
**With every gap now sourced, the workbench grows from an *explainer* into an *anticipator and decision
partner* — Coming-Risk and Patterns push the planner ahead of the question, the two-tone gap and confidence
make the explanation honest, and Scenario Studio + Recommended Actions let them decide and act — all on data
confirmed present today, still refusing to predict what it can't.**

*Wireframes are ASCII sketches; every element binds to a real AppKit primitive (§C) and a confirmed source
(cited per addition). No `prod_edw` writes; scenarios/actions live in Lakebase, history in
`sandbox_operations.po_management`.*

</div>
