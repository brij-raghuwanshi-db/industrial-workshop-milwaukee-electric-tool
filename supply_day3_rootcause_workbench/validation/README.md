<div align="center">

# 🧪 Data Validation — Testing Every Feature Against Real Records

### "Sit at the UI and exercise each screen, each measure, each scenario — with 10 real items — and record what works vs what breaks."

**Parent:** [`../`](../) the design doc set · **Method:** live READ-ONLY on `mke-rsc` (warehouse `7bd33a82f4e92206`).
For each UI feature: pull **≥10 real items** (SKUs / POs / customers / suppliers / item×networks), compute the
**documented measures/formulae** on them, test **data quality + within/across-org coverage** across time ranges,
and record a **verdict** — so we learn from the data itself what holds up before we build.

</div>

---

## How this is organized
One file per **UI feature / screen** (the unit "what works / doesn't" attaches to). Each file:
1. What it claims to show (from the design docs) + the measure/formula being tested.
2. The **10 real items** pulled live.
3. The computed result on each (the actual numbers).
4. **Data-quality findings** (nulls, sparsity, grain traps, empty columns).
5. **Within-org and across-org** behavior.
6. **Verdict**: ✅ works as designed · 🟡 works with caveat · 🔴 breaks / needs rework.

## Scoreboard (filled as each completes)

| # | Feature / page | Source doc | Verdict | Headline finding |
|---|---|---|:--:|---|
| V1 | Watchlist / top-missing-items | mapping A1, measures §3.1 | 🟡 | ranks sensibly (hero #1 $6.98M); must split "below-SS-target" vs "hard stockout"; org 8000 outlier; cross-org rebalance visible live |
| V2 | Waterfall / PAB + gap decomposition | measures §2, §3.1 | ✅ | PAB recursion **0 breaks / 286,935** transitions; gap decomposition splits target-move vs position on real SKUs (Carter trap visible) |
| V3 | Demand surprise / consumption + priors | mapping A2/A3, measures §3.3 | 🟡 | consumption works (all 10 chronically under-forecast); "demand surprise" definition ambiguous (ratio vs error); promo empty on accessories; priors needs month-aggregation not single week |
| V4 | Supply / PO slip + who-moved-it | mapping A5, measures §3.5 | 🟡 | requested→promised slip works (200+ day slips real); **date-key subtraction trap** + **sentinel dates** pollute orig→current drift; supplier slips concentrated in 19 suppliers |
| V5 | Holds / adjustments / quality | mapping A6, measures §3.6 | 🟡 | adjustments ✅ rich (reason-coded, ±40M swings); quality ✅ tiny (154 rejects); **holds 🔴 2.4B-row snapshot — "IS NULL" gives false 0**, needs latest-snapshot+sentinel logic |
| V6 | Org rollup + rebalance | scenarios S2, gap G-rollup | ✅ | pooled rollup works; per-org genuinely misleads (48228902WM: −245k at 2013 vs +680k at 2012); **coverage is mostly PARTIAL (9/10) → show coverable %, "transfer-first-then-buy"** |
| V7 | Excess / overstock | scenarios S1 | 🟡 | real multi-year-cover SKUs ($4.5M/237wk); confirms S1; **switch trigger from ×SS to weeks-of-cover** (×SS over-flags fast movers) |
| V8 | Forecast bias / accuracy (governed) | DK-7, measures §3.3 | ✅ | governed fact works; **planner-vs-system bias split is a genuine new capability** (HDW FLD/ACE: planner override *adds* error — FVA insight); present as % |
| V9 | Forward risk + transfer-to-cover | DK-1/DK-9 | ✅ | forward crossings + lead-time flag work (top crossings all inside lead time → can't order-fix); V9→V6 chain distinguishes transfer-able vs escalate (345020 = no coverage) |
| V10 | Plan nervousness + SS-refresh + chronic | S3/DK-12/G5 | ✅ | chronic detection works (SKUs below SS 55/55 snapshots); acute/chronic/nervous are 3 distinct temporal classes — biggest time-saver |
| **V11** | **Convergence scenarios** (multi-cause / shared-constraint / risk-wave) | **NEW — the gap** | 🔴 | **52% of shortage SKUs have all 3 causes at once; 1 supplier behind 3,035 SKUs; 6,933 crossing one week — the single-cause design misses all of it** |
| **V12** | **Do-nothing / false-alarm** (cushion dip / transient / target-artifact / far-out) | **NEW — the gap** | 🔴 | **only 34% of below-SS flags ever stock out; 66% are cushion doing its job → need ACT / WATCH / DISMISS verdict or the tool cries wolf** |
| **V13** | **Recoverable vs Lost Battle vs Living-on-Edge** (time-fence / S&OE) | **NEW — the gap** | 🔴 | **98% of flags are INSIDE the lead-time fence (unrecoverable by PO); 2,307 SKUs always-below (chronic edge); lead time bimodal 2d/122d — full RCA belongs on the committed+chronic, not every fire** |
| **V14** | **Uncovered scenarios** (leads surfaced but not pursued) | **sweep** | 💭 | 7 new threads catalogued (N1–N7); each validated below (V15–V21) |
| **V15 (N1)** | Transition / NPD SKUs | new | ✅ | transition status is on `items_scd1` (71,484 transition, 4,038 NPD); **1.5× / ~9× over-represented in shortages** — distinct root cause, wrong table probed in V14 |
| **V16 (N2)** | Over-forecast → excess link | new | 🟡 | plausible but **not provable at SKU grain** (excess is 62.5% systemic; SKUs shared) — reframed: excess is a **planning-policy** problem, not customer-specific |
| **V17 (N3)** | Returns / warranty | new | ✅/🟡 | real & material (3.2M warranty recs + reason taxonomy) but **cross-system** (JDE/AX) — needs item-key crosswalk; deferred |
| **V18 (N4)** | Found inventory (positive adj) | new | ✅ | **25,089 found events / +81.9M units** — adjustments must be read **signed**; positive = heal signal |
| **V19 (N5)** | Non-standard demand | new | 🟡 | only **1.1% of volume** — a ranking-hygiene fix (weight by $), not material pollution |
| **V20 (N6)** | Component/bulk orgs | new | ✅ | 8000 = **Supplier Inv (consignment)**, 2092 = **3PL Parts** — non-DC grains; **segregate before $-ranking** (fixes V1/2/5/7/9 distortion) |
| **V21 (N7)** | Recovery velocity | new | ✅ | bimodal: **29% heal fast / 24% stuck** — sharpens WATCH-vs-chronic |
| **V22 (DK-16)** | Criticality / ABC axis | cross-poll | ✅ | A-class shortages **$67.8k/SKU = 2.1× C-class** — criticality re-ranks; add as classifier axis (37% Unclassified) |
| **V23 (DK-17)** | Dormant / obsolescence / E&O | cross-poll | ✅ | `obsolete_date` too sparse; **movement-recency** is the signal — **$545M never-shipped** + $16M dormant |
| **V24 (DK-18)** | Intermittent demand | cross-poll | ✅ | **~24% intermittent** → guards our SS/consumption formulae; explains some V3 "misses" |
| **V25 (DK-19)** | Parameter recommendation | cross-poll | 🟡 | MKE is **projection-based, no ROP/MAX**; = a **safety-stock** review (recommender blocked); **proposal-queue workflow reusable now** |
| **V26 (DK-20)** | Alignment KPI + Sankey + hold | cross-poll | ✅/🟡 | **54% aligned** KPI ✅; Sankey ✅; intentional-hold partial (`ss_managed`=$450M); planning-method corrects V25 |

Legend: ✅ works · 🟡 caveat · 🔴 breaks · ⏳ pending

**Tally: 5 ✅ works · 5 🟡 caveat · 3 🔴 gaps (convergence V11, do-nothing V12, recoverability V13).** The measures all work; the 🔴s
are *missing capabilities* (no convergence lens; no do-nothing/watch verdict), not broken measures. Both are
**trust** gaps: V11 = under-serving multi-cause; V12 = over-flagging false alarms. Together they turn a
10,700-row alarm into a ~3,600-row real worklist grouped by shared root.

---

## 🧭 Synthesis — what the data taught us across all 10

**The load-bearing math is bulletproof.** The PAB recursion held **0 breaks across 286,935 transitions** (V2) —
so the waterfall, forward-risk, rebalance, excess, and the simulator all rest on verified arithmetic. That's the
single most reassuring result.

**But raw columns lie in specific, repeatable ways — the validation caught 6 traps that would have shipped wrong
numbers:**
1. **Date-key subtraction ≠ days** (V4) — must `DATEDIFF` via `date_scd1`.
2. **Sentinel dates** `2000-01-01`/`2100-12-31` pollute PO "original promise" (V4) — use requested→promised.
3. **Holds table is a 2.4B-row snapshot** — `release IS NULL` gives a false "0 holds" (V5).
4. **In-transit cost columns are empty** — use open `transfer_orders` instead (V5/DK-11).
5. **"3× safety stock" over-flags fast movers** as excess (V7) — use weeks-of-cover.
6. **Priors self-join needs month-aggregation**, not a single weekly `date_key` (V3).

**Three cross-cutting design truths the data forced:**
- **Severity/temporal class matters more than the rank.** "Below SS target" ≠ "hard stockout" (V1); acute ≠
  chronic ≠ nervous (V10). The same shortage number means act / escalate / ignore depending on class.
- **Per-org is genuinely misleading; pooled is truth** — proven repeatedly (V1, V6, V9). But rebalance coverage
  is **mostly partial** (V6) — "transfer-first, buy-the-rest," never over-promise.
- **One definition must be pinned** for "demand surprise" (V3) — same data gives 153% or +53% depending on
  formula; and a governed source exists for bias (V8) with a planner-vs-system split that's a genuine new capability.

**The one governance concern:** component/bulk orgs (8000, 2092) and huge-magnitude UoM SKUs recur across V1,
V2, V5, V7 — segregate them from finished-goods DCs before any $-ranking, or they dominate with non-comparable
numbers.

**Bottom line:** the product is real and the data supports it — but **~half the measures need a definition
pinned or a DQ guard before they face a planner.** The validation *is* the spec for the serving layer's
correctness rules.

---
*All figures live READ-ONLY 2026-09-02+; illustrative of behavior, not audited. No production schema written.
Each Vn file carries: the 10 items, computed results, DQ findings, the story, root causes, recommendations &
actions, and logged successful queries.*
