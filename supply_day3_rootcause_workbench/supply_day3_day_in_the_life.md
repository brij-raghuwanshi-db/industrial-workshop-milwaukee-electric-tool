<div align="center">

# ☀️ A Day in the Life — The Supply Root-Cause Workbench in Use

### From "open the laptop" to "close the loop" — how every piece of this exercise solves a real problem

**Companions:** the whole `supply_day3_rootcause_workbench/` set + `validation/`. **Persona:** *Leo*, a Milwaukee
supply planner (the planner who walked the team through his process in the Day-3 transcript). Every screen,
number, and behavior below traces to a **live-validated** finding (Vn / DKn cited inline).

</div>

---

> ## The one sentence this whole day proves
> Today, Leo answers *"we're in a bad position — how did we get here?"* in **minutes instead of ~2 hours**, and —
> more importantly — the tool tells him **which fires are worth fighting, which are already lost, and which he
> should ignore**, so he spends his day on the ~3,634 problems that are real and winnable instead of drowning in
> a 10,700-row alarm.

---

## 📊 The real examples behind this day (all live-validated)

Every number in the mockups below is from an actual query against `mke-rsc` (not invented):

| Example | Real finding | From |
|---|---|---|
| **3697-22** (M18 FUEL 2PC combo) | ranks #1 on the watchlist, **$6.98M** at risk; short at org 2012 but **+3,797 headroom at org 2013** (same network) | V1, V6 |
| **10,700 → ~3,634 → 128** | 10,700 below-SS flags; only 34% ever stock out; only near-term+physical+recoverable are ACT | V12, V13 |
| **$372.5M unrecoverable** vs $3.7M recoverable | 98% of crossings inside the lead-time fence | V13 |
| **Techtronic Cordless → 3,035 SKUs** | one supplier behind 3,035 shortage SKUs (after name-normalization) | V11 |
| **Home Depot 251 vs 150** (+101u, 134%) | real over-consumption, base demand, DG5 level | V3, transcript |
| **PO slip 212 days, SUPPLIER-initiated** | requested→promised slip; originator captured | V4 |
| **+352 of the −904 gap = SS-target refresh** | demand +220% / SS target +17.6% coupled | V2, DK-12 |
| **Chronic: 2,307 SKUs below SS every week** | living-on-the-edge population | V13 |
| **Excess: 273421 = $4.52M, 237 weeks cover** | the E&O other-side-of-the-coin | V7 |
| **Forecast bias: HDW FLD planner −380,873 vs system −246,844** | planner override *adds* error | V8 |
| **6,933 SKUs crest wk37** | the temporal risk wave | V11 |

---

## ⏰ 8:00 AM — Leo opens the laptop and the app

He does **not** see a wall of red. He does **not** open 5–7 systems. He sees **one screen: the Control Tower
worklist** — the raw 10,700 flags already triaged into what's worth his time, with a **pushed overnight banner**
and the **worklist itself sorted ACT + RECOVERABLE + $**:

```
┌════════════════════════════════════════════════════════════════════════════════════════════════┐
║ 🔧 Supply Root-Cause Workbench      [Network ▾ Olive Branch]  [Plan ▾ 20 Global]  [Mine ▾]  👤 leo ║
╠════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 📣 OVERNIGHT (Mon snapshot): 9 newly at-risk · 3 recovered · ⚠ 1 supplier pattern (Techtronic)    ║
╟────────────────────────────────────────────────────────────────────────────────────────────────╢
║  ◆ ACT today        ◆ $ at risk        ◆ WATCH        ◆ DISMISS (verified)   ◆ LOST BATTLE         ║
║    128  🔴            $14.2M winnable     884  🟡         412  🟢 cushion       47  ⚫ committed      ║
║    of 10,700 raw flags → 3,634 real → 128 near-term+physical+recoverable                           ║
╟────────────────────────────────────────────────────────────────────────────────────────────────╢
║  YOUR WORKLIST — sorted by ACT · recoverable · $           [🔴ACT] [🟡WATCH] [🟢DISMISS] [⚫LOST]   ║
║  ┌──────────┬────────────────┬────────┬───────┬──────────┬────────┬──────┬──────┬───────────────┐ ║
║  │ SKU      │ Desc           │ gap    │ crosses│ cause    │ verdict│ recov│ conv │ $ at risk      │ ║
║  ├──────────┼────────────────┼────────┼───────┼──────────┼────────┼──────┼──────┼───────────────┤ ║
║  │ 3697-22 ▸│ M18 FUEL 2PC   │ -904   │ wk36  │🟦Demand+ │ 🔴ACT  │ 🟢   │ ⚠2   │ $6.98M ⭐      │ ║
║  │ 4811xxx ▸│ PACKOUT        │ -1,240 │ wk38  │🟧Supply  │ 🔴ACT  │ 🟢   │ 1    │ $2.66M         │ ║
║  │ 301621  ▸│ …              │ -22.5k │ wk39  │🟧Supply  │ 🔴ACT  │ 🟢   │ ⚠3   │ $4.78M         │ ║
║  │ 296720  ▸│ …              │ -31k   │ wk38  │🟦Demand  │ 🟢DISM │ —    │ 1    │ (cushion — no $)│ ║
║  │ 345020  ▸│ …              │ -1,765 │ wk37  │🟧Supply  │ ⚫LOST │ 🔴   │ 1    │ committed      │ ║
║  └──────────┴────────────────┴────────┴───────┴──────────┴────────┴──────┴──────┴───────────────┘ ║
║  Freshness: plan snapshot Mon 2026-08-31 · on-hand 06:00 · READ-ONLY · verdicts computed overnight ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
```
*(Legend: verdict = ACT/WATCH/DISMISS/LOST · recov = 🟢recoverable/🔴unrecoverable · conv = # converging causes)*

**Why this is the first thing he sees — and why it's the whole point:**
The raw data has **10,700 "below safety stock" flags** this morning. A naïve tool would show all of them and Leo
would be back to triaging by gut. Instead the **classifier layer** (V10–V13, computed overnight by the Job into
`rc_serving_sku_week`) has already sorted them:
- **~3,634 are real** (ever actually stock out) — and of those only **128 are ACT** (near-term, physical, *and*
  recoverable) → **that's his worklist.** *(V12: only 34% of flags are real; V13: recoverability gate.)*
- **412 are auto-DISMISSED** — the cushion doing exactly its job; shown with recovery evidence, not hidden.
  *(V12: 66% never go negative.)*
- **47 are already-lost battles** — committed stockouts inside the lead-time fence; they go straight to
  *notify + log*, not the fight. *(V13: 98% of crossings unrecoverable, $372.5M — but only the material ones
  surface here.)*

> **The problem this solves:** the transcript's planner checked **5–7 systems ~once a day, up to 2 hours** and
> triaged from tribal memory. Leo now walks in to a **pre-triaged, ranked, de-noised worklist** — the "magic
> wand: all consolidated" he asked for, plus the judgement of *what's even worth doing.*

---

## ⏰ 8:05 AM — The product partner's Slack: *"We're short on 3697-22, how did we get here?"*

This is the exact Day-3 scenario. Leo clicks **3697-22** on the watchlist. One screen — the **Root-Cause
Investigation** — loads with the answer already written at the top:

```
┌════════════════════════════════════════════════════════════════════════════════════════════════┐
║ ‹ Worklist   3697-22 · M18 FUEL 2PC COMBO KIT      Network: Olive Branch (1080+2012+2013+2014)     ║
║ 🔴 ACT   🟢 RECOVERABLE (crosses wk36, before the lead-time fence)   ⚠ 2 CAUSES CONVERGING         ║
╠════════════════════════════════════════════════════════════════════════════════════════════════╣
║ ▸ THE ANSWER (auto-drafted):  "3697-22 fell 904u below safety stock at wk36. PRIMARY driver:      ║
║   Home Depot over-consumed +101u (251 vs 150 forecast = 134%, last 4 months). CONTRIBUTING:       ║
║   PO 380… slipped 212 days, supplier-initiated. Note: +352u of the gap is the safety-stock        ║
║   TARGET refreshing on higher demand — not a physical drop."          [ Draft escalation ▸ ]      ║
╟──────────────────────────────────────────────┬───────────────────────────────────────────────────╢
║  WATERFALL — how we got to the gap             │  CAUSE STRIP (ranked contribution × who-can-act)   ║
║   SS@lead-time ─┐                              │  ┌─────────────────────────────────────────────┐ ║
║      904        │▒▒▒▒ target refresh +352 ⚠   │  │🟦 DEMAND  +540u ▓▓▓▓▓▓▓ 71%  🎯High → demand │▸║
║   (North Star)  │▓▓▓▓ real consumption −101    │  │🟧 SUPPLY  +270u ▓▓▓ 30%       → me (pull-in) │▸║
║                 │▓▓ supply slip −40            │  │🟪 HOLDS   +90u  ▓ 10%         → quality      │▸║
║                 │▓ holds −18                   │  └─────────────────────────────────────────────┘ ║
║                 └────► GAP −904 (wk36) 🔴      │  residual after top lever (pull-in): 600u →demand ║
╟──────────────────────────────────────────────┴───────────────────────────────────────────────────╢
║  POSITION OVER TIME     ▓ on-hand actual   ─ ─ safety stock target   ░ projected PAB               ║
║   ─ ─ ─ ─ ─ ─ ─ ─ ─SS─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                          ║
║   ▓▓▓▓▓▓▓▓▓▓▓▒▒▒░░░░░░░░  ◄ dips below SS at wk36 (low point +15,906 — never negative)             ║
║   wk28    wk32    wk36🔴   wk40    wk44          [ ◀ time-machine scrubber ▶ ]  [ Week|Month ]      ║
╟────────────────────────────────────────────────────────────────────────────────────────────────╢
║ 🧭 RECOMMENDED (feasibility-gated):  1.TRANSFER 300u from org 2013 (+3,797 headroom, lane ✅) ▸    ║
║   2.Supplier pull-in (~300u) ▸   3.Flag 600u to demand (Home Depot re-baseline) ▸                  ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
```
*(Drill panels open on the right — Demand: Home Depot 251 vs 150, base, DG5 level; Supply: PO 380…, req Jun-3 →
promised Jan-1, 212d, SUPPLIER-initiated. Both from the validated queries.)*

**What just happened, step by step, and which understanding solved it:**

1. **He didn't assemble anything** — the two-bullet answer is *pre-drafted* from the deterministic buckets.
   *(V2: PAB recursion verified 0 breaks/287k — the waterfall math is trustworthy to the unit.)*
2. **The waterfall starts at safety-stock-at-lead-time** — the North Star the room agreed on. *(DK/Activity 4.)*
3. **The two-tone gap band** shows the −904 isn't all real: **+352 of it is the safety-stock *target*
   refreshing** because demand rose, not a physical drop. Leo instantly knows not to over-buy for the full 904.
   *(DK-12, verified: SS target moves with demand ~+18% on coupled cases.)*
4. **"⚠ 2 causes converging"** — the tool didn't force a single "likely cause." It shows demand **and** supply
   co-firing, ranked by *contribution × who-can-act*. *(V11: 52% of shortages are multi-cause — the single-cause
   chip would have hidden the supplier slip.)*
5. **🟢 RECOVERABLE** — the crossing is *outside* the lead-time fence, so a pull-in can still land in time. This
   is a fight worth having. *(V13.)*

He clicks the **Demand drill** — sees Home Depot at 251 vs 150 forecast, broken to the DG5 customer, base (not
promo) demand *(V3: consumption works; promo empty on this line)*. He clicks **Supply** — PO 380… requested Jun-3,
promised Jan-1, **212-day slip, "SUPPLIER-initiated"** *(V4: requested→promised is the trustworthy slip; the
originator answers "did they warn us or did we catch it?" — the thing the room thought wasn't in the data)*.

**Answer to the partner: ~4 minutes.** He hits **"Draft escalation"** → the note writes itself in the standard
two-bullet format, carries the committed-$ and the provenance/verify badge, and he sends it. *(R18/R19; the
escalation is a living object, V-value.)*

> **Problem solved:** the ~2-hour, 5–7-system hunt collapses to one guided screen — *and* Leo doesn't over-react,
> because the tool separated the real shortage (−101 consumption) from the target artifact (+352).

---

## ⏰ 8:20 AM — But the recommended action isn't "expedite" — it's "transfer"

Before Leo fires a PO expedite on 3697-22, the **Recommended-Action panel** checks the network:

```
🧭 RECOMMENDED (ranked, feasibility-gated)
  1. TRANSFER 300u from org 2013 (same network, +3,797 headroom, lane exists ~1wk) ✅  ← do this first
  2. Request supplier pull-in (covers ~300 more)                                   ✅
  3. Flag remaining 600u to demand (re-baseline Home Depot)                        ▸
```

The tool saw that 3697-22 is short at org 2012 but org **2013 — same Olive Branch network — has +3,797 headroom**
*(V1 + V6, verified live)*. So the cheapest, fastest fix is **move what we already own**, not buy more. Leo drafts
the transfer; the residual 600u (demand-driven) routes to the demand team with the evidence attached.

> **Problem solved:** the transcript's exact pain — "the 20-plan is per-org and misleading; we look at pooled
> inventory." The tool makes pooled the default and turns a shortage into a transfer, saving cash and lead time.
> *(V6: this is the highest-ROI action; but the tool honestly shows coverage is partial — transfer 300, buy/flag
> the rest.)*

---

## ⏰ 8:40 AM — A "how did we get here" that ends in *do nothing*

Next flagged item: **296720**, org 2012. Partner-style question again. Leo opens it — but the header says:

```
┌ 296720 ·  🟢 DISMISS — no action warranted ─────────────────────────────────────────────┐
│ ▸ "Flagged below safety-stock TARGET at wk38 (−31,297 vs target), but on-hand never goes  │
│    negative (low point +20,457). Dips into the cushion, recovers wk40. Safety stock is     │
│    doing its job. Recommended: no action."                                                 │
│   [ evidence: PAB stays positive all 14 weeks ▾ ]        [ dismiss + close flag ]          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

Leo reads it, agrees, closes it in **15 seconds.** He did *nothing* — and that was the correct, evidenced answer.
*(V12: 66% of flags are this; V1: "below-SS-target ≠ hard stockout" — the severity split.)*

> **Problem solved — the trust one:** a tool that shouted "ACT" on 296720 would be crying wolf (it's wrong
> two-thirds of the time). By saying *"do nothing, here's why,"* it earns the credibility that makes Leo trust
> the 128 it *does* say to act on. **The do-nothing recommendation is a feature, not an absence of one.**

---

## ⏰ 9:00 AM — A lost battle: damage control, not firefighting

Item **345020**, org 2012. Header:

```
┌ 345020 ·  ⚫ UNRECOVERABLE — committed loss ─────────────────────────────────────────────┐
│ ▸ "Crosses below SS wk37, INSIDE the 130-day lead-time fence — no PO can arrive in time.    │
│    No in-network excess to transfer. This shortage is locked in."                           │
│   DAMAGE CONTROL:  [ allocate scarce supply to committed customers ▸ ]                      │
│                    [ notify affected customers early ▸ ]  [ log as committed loss ]          │
│   ▸ FULL RCA (why did this become unrecoverable?) — worth it, $-material ▸                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

Leo does **not** waste an hour root-causing how to fix wk37 — it *can't* be fixed. Instead he: allocates the
limited supply to the committed customers, sends early notifications, logs it. **Then** — because it's material —
he clicks **Full RCA**, because the value now is *learning why it became unrecoverable* (was it detected late? was
the lead-time fence known?) so **next quarter's version of this fire never starts.**

> **Problem solved:** the "battle we lose no matter what." The tool names it honestly, switches the action from
> expedite to damage-control, and — the inversion — reserves the *deepest* analysis for the loss you couldn't
> prevent, to prevent the next one. *(V13/DK-15: 98% unrecoverable, $372.5M; RCA gated by class.)*

---

## ⏰ 9:30 AM — The pattern: one root behind 3,035 fires

The overnight alert said *"1 supplier pattern detected."* Leo opens the **Constraint pivot**:

```
┌════════════════════════════════════════════════════════════════════════════════════════════════┐
║ 🎯 CONSTRAINTS behind today's shortages            [ by Supplier | Component | DC | Planner ]      ║
╟────────────────────────────────────────────────────────────────────────────────────────────────╢
║  Constraint                          shortage SKUs   share      fill rate   action                ║
║  ┌────────────────────────────────┬─────────────┬──────────┬──────────┬─────────────────────────┐║
║  │ Techtronic Cordless (merged*)   │ ▓▓▓▓▓▓▓▓▓▓  │ 3,035    │  88% ▼   │ [ QBR + allocate ▸ ]    │║
║  │ Milwaukee Mfg Corp              │ ▓          │   218    │  94%     │ [ review ▸ ]            │║
║  │ Pinehurst Mfg GmbH              │ ▏          │   123    │  91%     │ [ review ▸ ]            │║
║  └────────────────────────────────┴─────────────┴──────────┴──────────┴─────────────────────────┘║
║  *name-normalized: TTI LIMITED/LTD/LMTD + OUTSRCD/OUTSRC SVPT merged into one entity              ║
║  ▸ ONE supplier (Techtronic) is behind 3,035 of today's shortages — don't triage 3,035 tickets.    ║
║  ▸ ALLOCATE its constrained capacity: run these top-$ / committed SKUs first  [ open allocation ▸ ]║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
```

Instead of investigating 3,035 SKUs one at a time, Leo sees they trace to **one supplier** *(V11, verified —
after name-normalization merged the TTI LIMITED/LTD/LMTD variants)*. He escalates **once** — a capacity
conversation with Techtronic and a procurement hand-off — and uses the tool to tell the supplier *which* SKUs to
run first with the scarce capacity.

> **Problem solved:** the single biggest time-sink — thousands of per-SKU fires that are really *one problem
> wearing 3,035 costumes.* The unit of action becomes the **constraint**, and it moves to the right team
> (sourcing). *(V11/DK-13b.)*

---

## ⏰ 10:00 AM — Getting ahead of it: the risk that hasn't happened yet

Leo switches to the **⚡ Coming-Risk** tab — the proactive counterpart:

```
⚡ COMING RISK — projected to cross (next 8 weeks)         [ ≤2wk | ≤4wk | ≤8wk ]
  SKU     healthy now  crosses  weeks-to  recoverable?  suggested pre-emptive move
  5820 ▸  ✅ today     wk41     +5 wks    🟢 RECOVERABLE  transfer 200 from 1080 now (lane exists)
  6104 ▸  ✅ today     wk43     +7 wks    🟢 RECOVERABLE  small pull-in now avoids the crossing
  ⚠ wk37 RISK WAVE: 6,933 SKUs crest this week — capacity crunch, work top-$ first
```

He acts on the *recoverable* forward crossings **while there's still time** (transfer/pull-in before the breach),
and sees the **wk37 risk wave** coming — 6,933 SKUs cresting at once — so he plans his week's capacity around it
rather than being ambushed. *(DK-1 forward risk; DK-9 transfer-to-cover, 7,508 forward-coverable; V11 Type-3
temporal wave.)*

> **Problem solved:** the transcript's future wish — *"what's my stock-out risk next week, two, three weeks… how
> can I transfer."* Reactive firefighting becomes proactive prevention, guarded so it never tips into
> over-prediction (uses the plan's own forward PAB, not an invented forecast).

---

## ⏰ 10:30 AM — Fixing the root, not the symptom: forecast bias → demand team

Leo notices Home Depot keeps driving shortages. He opens the **Forecast Bias board** (governed
`fact_forecast_accuracy`, DK-7/V8):

```
┌════════════════════════════════════════════════════════════════════════════════════════════════┐
║ 🎯 FORECAST BIAS — actual vs forecast, planner vs system   [Demand plan ▾ 10 ACC]  (governed fact) ║
╟────────────────────────────────────────────────────────────────────────────────────────────────╢
║  Customer (DG5)   actual    late-3 fcst   consumption   planner_bias   system_bias   flag         ║
║  ┌──────────────┬─────────┬───────────┬────────────┬─────────────┬─────────────┬───────────────┐ ║
║  │ TTI NZ        │ 67,442  │ 23,261    │ 290%       │ chronic under-forecast          │           │ ║
║  │ HOME DEPOT    │ (see 3697-22)        │            │ −587,166    │ −581,035    │ model+planner │ ║
║  │ HDW FLD       │         │           │            │ −380,873    │ −246,844    │ ⚠ OVERRIDE    │ ║
║  │ ACE           │         │           │            │ −338,302    │ −181,870    │ ⚠ OVERRIDE    │ ║
║  └──────────────┴─────────┴───────────┴────────────┴─────────────┴─────────────┴───────────────┘ ║
║  ⚠ where |planner_bias| > |system_bias| the planner OVERRIDE is ADDING error (the FVA insight)     ║
║  ▸ [ Flag to demand: re-baseline HDW FLD, ACE (evidence attached) ]   reason: governed codes ▾    ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
```

The governed fact shows **who** is chronically under-forecast **and** whether it's the model or the human
override causing it — the FVA insight. Leo sends a **structured re-baseline request** to the demand team with the
evidence, so the *cause* of the recurring shortages gets fixed, not just this week's symptom. *(V8; DK-8 governed
reason codes; Gap-7 demand handoff.)*

> **Problem solved:** the transcript's "60% of issues are demand" — but now it's actionable at the source, with
> planner-vs-system bias naming exactly where the forecast process is failing.

---

## ⏰ 11:00 AM — The other side of the coin: $452M sleeping on the shelf

A finance partner pings about working capital. Leo opens the **Excess board** (S1/V7):

```
💰 EXCESS — ranked by $ tied up + weeks of cover
  273421   $4.52M   237 weeks cover ⚠ E&O risk     [ slow inbound PO ▸ ] [ rebalance ▸ ]
  290920   $5.59M   123 weeks cover                 [ de-stock ▸ ]
```

The same data that finds shortages finds **excess** — SKUs with 2–4.5 *years* of cover. Leo (or a finance user)
now has a de-stock / slow-PO / rebalance action, and the excess here often *covers a shortage elsewhere*
(links back to the rebalance engine). *(V7: use weeks-of-cover not ×SS; S1: $452M, 3.2× more prevalent than
shortage — a whole new audience the shortage tool never served.)*

> **Problem solved:** the product is no longer "the shortage tool" — it's a control tower that serves service
> (planners) *and* cash (finance) from one spine.

---

## ⏰ 4:30 PM — Close the loop: the action log writes itself

Everything Leo did today — the 3697-22 transfer, the Techtronic escalation, the 345020 committed-loss log, the
demand re-baseline — is captured in the **Action & Outcome log** (Lakebase), with root cause + action + status +
owner, append-only. No more "he knows because he's the guy who did it." *(Activity 9; the transcript's wished-for
"watch list with consistency.")* Two weeks from now, the tool will auto-read the next snapshots and tell him
whether each action **recovered / improving / no-change** — turning his tribal notes into institutional memory.

---

## ⏰ 4:45 PM — Proof it was worth it: the Value & Impact page

```
⏱ TIME TO ANSWER    📉 SYSTEMS     ✅ ACTIONS SUPPRESSED    💵 $ PROTECTED (verified)   🎯 CAUSE MIX
  ~8 min ▼ from 2h    1 (was 5–7)    412 false-alarms today   $1.6M (read-back)          61% demand ✓
```

The tool measures its own worth from its own telemetry — including the **"actions suppressed" count** (proving it
saved Leo from 412 wasted investigations today is as valuable as the actions it drove). This is the Day-1
mandate — *quantify the savings* — as a live screen, and Leo's ammunition to evangelize it. *(Screen F / V-value;
DK-14 suppressed-count.)*

---

## 🗓️ The rhythm beyond one day

| Cadence | What the tool does |
|---|---|
| **Every morning** | pre-triaged worklist (Classify overnight): ACT / WATCH / DISMISS / lost-battle — Leo starts on the ~128 that matter |
| **Weekly (Monday snapshot)** | the plan refreshes; chronic SKUs (2,307 always-below) surface for **policy fixes**, not weekly firefighting; the risk-wave for the week is visible |
| **When a partner asks** | the ~2-hour hunt is a ~4-minute guided answer — with the honest split of real-vs-artifact and winnable-vs-lost |
| **Over the quarter** | committed-loss RCAs feed prevention; forecast-bias handoffs fix the demand root; the outcome log proves what worked; MLflow-style feedback makes next quarter's triage smarter |

---

## 🧭 The through-line: how each understanding shows up in Leo's day

| The understanding we built | Where it appears in the day | The problem it solves |
|---|---|---|
| **Classifier layer** (V10–V13) | 8:00 AM — the first screen is triaged, not raw | 10,700 alarm → 128 worth doing |
| PAB recursion (V2) | 8:05 — the waterfall's trustworthy math | the answer is *right*, to the unit |
| SS-refresh / two-tone gap (DK-12) | 8:05 — "+352 is target, not real" | stops over-buying on an artifact |
| Convergence (V11/DK-13) | 8:05 & 9:30 — multi-cause + constraint pivot | stops single-cause blindness; 3,035→1 |
| Who-moved-the-PO (V4) | 8:05 — supplier-initiated slip | accountability the room thought was lost |
| Recoverability / S&OE (V13/DK-15) | 8:00 & 9:00 — ACT vs lost-battle | fight winnable fires, damage-control the rest |
| Do-nothing verdict (V12) | 8:40 — DISMISS with evidence | earns trust; kills false alarms |
| Org rollup / rebalance (V6) | 8:20 — transfer before buy | pooled truth; cash + lead-time saved |
| Forward risk / transfer-to-cover (DK-1/9) | 10:00 — coming-risk + wave | reactive → proactive |
| Forecast bias governed (V8/DK-7) | 10:30 — planner-vs-system, re-baseline | fixes the *cause* (60% demand) at source |
| Excess (V7/S1) | 11:00 — $452M, weeks-of-cover | new finance audience; working capital |
| Action log + Value page (Act.9, F) | 4:30 & 4:45 — closed loop + ROI | institutional memory + provable savings |

---

<div align="center">

### 📌 A day in one line
**Leo opens one screen that has already done his triage — separating the real from the noise, the winnable from
the lost, the demand from the supply — so he spends his day *acting on what matters and provably ignoring what
doesn't*, answers the partner in minutes, fixes roots not symptoms, and closes every loop into memory the whole
team inherits.**

*Every screen, number, and behavior above is backed by a live-validated finding in `validation/` (Vn) and
`requirements` Part K (DKn). Nothing is built yet — this is the day the validated design delivers once Wave 0
ships.*

</div>
