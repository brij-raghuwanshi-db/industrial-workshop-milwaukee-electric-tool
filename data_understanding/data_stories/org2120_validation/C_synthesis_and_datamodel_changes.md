# Org 2120 (Mexico) — Synthesis, Learnings & Data-Model Changes

**Date:** 2026-08-31 · **Author:** consolidation of two logged subagents (A = scenario validation,
B = new-scenario hunt) + my own independent re-verification of every load-bearing number.
**Source:** READ-ONLY `SELECT` on `sandbox_operations.po_management.rung2_plan_vs_actual` (the Rung-2 gold, 2 orgs).
**Companion files:** [A_scenario_validation_2120.md](A_scenario_validation_2120.md) · [B_new_scenarios_2120.md](B_new_scenarios_2120.md)

---

## The headline (answers "we can't blindly say all orgs behave the same")

**Confirmed: they do not.** Org 2120 Mexico is a *structurally different* operating environment from
2012 Olive Branch — not a smaller copy. Every identified P1 scenario still *applies* to 2120 (the model
generalizes), but the **magnitudes, the bias direction, and several structural facts differ enough that
fixed thresholds mis-fire and one-size logic hides real signal.** Three findings are genuinely NEW —
they could not be seen until 2120 was loaded.

## Verification stance (what I trusted vs. re-ran myself)

The user flagged hallucination risk, so I did not enshrine subagent numbers on faith. I re-ran the
load-bearing NEW claims directly against gold:

| Claim | Independent re-check | Status |
|---|---|---|
| Gold grain clean (no fanout from adding 2120) | rows == distinct(item×org×week): 2012=219,938==219,938, 2120=77,273==77,273 | ✅ verified |
| Planner concentration 6 vs 92 | 2120 = **6** distinct planners, 2012 = **92** | ✅ verified |
| Unique-SKU footprint 41% | 2120 items 9,758 → **4,041 only-2120** / 5,717 shared | ✅ verified |
| Net-receiving node | ship/receive ratio **0.094** @ 2120 vs **0.377** @ 2012 | ✅ verified |
| Lean-yet-green | avg safety stock (when >0) **120.0** vs **2,342.6** units; green **62.28%** vs **36.32%** | ✅ verified |

**One correction applied:** Agent A/B reported avg safety stock ≈112.88; that averaged in
near-zero rows. The `>0` figure is **120.0** (2120) vs **2,342.6** (2012). The ~15–20× leanness gap holds
regardless; the artifact uses the verified number, not the subagent's.

---

## Part 1 — Do the ORIGINAL scenarios apply to 2120? (validation)

All apply. How they *behave* differs — this is the important part:

| Scenario | 2012 | 2120 | Applies? | Key difference |
|---|---|---|---|---|
| **Plan-fit bands (G/S5)** | 36% green / 39% red / 18% no-plan | 62% green / 26% red / 2% no-plan | Yes | 2120 far healthier; "no-plan" all but gone |
| **Bias magnitude (accuracy)** | **+101%** mean overage; 41% rows over / 26% under | **+21%** mean overage; 38% rows over / 19% under | Yes | **Same direction (both over-plan), 2012 ~5× larger** — NOT inverted (see correction below) |
| **Extreme $ variance (V)** | p99 $141.5K; max $5.95M | p99 $9.6K; max $380K | Yes | Order of magnitude smaller |
| **Shipment attainment (S3)** | 499% of plan | 1,074% of plan | Yes | Both over-ship; 2120 more extreme |
| **Alert tiers (O8)** | 68 / 6 / 5 / 21% (OK/Mon/Alert/Esc) | 67 / 10 / 9 / 14% | Yes | 2120 escalates less, monitors/alerts MORE |
| **Unplanned (planned_pab NULL)** | 18.17% | 2.03% | Yes | 2120 9× better planned |
| **WoW volatility** | p90 191 units | p90 10 units | Yes | 2120 ~19× steadier |

**Verdict — thresholds MUST be org-specific.** Two independent reasons:
1. **$-thresholds don't scale.** The Escalate trigger (>$200K) essentially never fires in 2120 (its p99
   miss is $9.6K). A 2120 planner would see *zero* escalations and wrongly conclude "all clear."
2. **Bias magnitude differs ~5× (corrected — NOT inverted).** A row-sign test refuted the earlier
   "inverted" claim: BOTH orgs skew to overage (actual on-hand > planned PAB) — 2012 41% over / 26% under,
   2120 38% over / 19% under, medians 0% for both. The +101% vs +21% means measure the *size of the overage
   tail*, not direction. So a global over-plan correction has the right SIGN for both, but the wrong
   MAGNITUDE for 2120 (would over-correct it ~5×). Store per-org bias magnitude; don't apply 2012's.

---

## Part 2 — NEW scenarios, only visible once 2120 was loaded

These are not rescalings of 2012 patterns — they are structural facts about Mexico.

### N1 · Ultra-concentrated planner model (key-person risk) — VERIFIED
6 planners run all of Mexico (12,879 rows each) vs 92 at 2012 (2,391 each). **Miller + Ystesund own ~85%
of Mexico planning.** This is an *operational-continuity* signal the plan-vs-actual model never surfaced
before: turnover of 1–2 people = Mexico planning paralysis. → belongs in a **planner-load / concentration**
view, and argues for a `planner` dimension being first-class (not just a label).

### N2 · Distinct sourcing footprint — 41% Mexico-exclusive SKUs — VERIFIED
4,041 of 9,758 items exist ONLY at 2120 (83% are D-class, names like "DRIVER RIM", "GEAR, RING" = regional
mechanical components). **Mexico's plan is not a filtered slice of Global** — it's an independent portfolio.
→ Cross-org SKU comparisons must be **inner-joined on shared items**; a naive union over-counts and blends
two portfolios. The S6 DC-imbalance tile on the dashboard is only valid for the **5,717 shared** items.

### N3 · Mexico is a directly-sourced node, NOT a transfer hub — VERIFIED & CORRECTED (2026-08-31)
Ship/receive ratio **0.094 at 2120 vs 0.377 at 2012** — 2120 receives ~11× what it ships. My earlier
reading ("regional distribution hub fed by intercompany transfer from 2012") was **WRONG** — I chased it
into the network tables (`manufacturing_sc.fact_transfer_order_receipt/shipment`,
`features.inventory_rebalance_*`, `features.safety_stock_network_sourcing_rules`) and the data refutes it:
- **2120 has ZERO transfer-order lines** (0 as source, 0 as dest, across 790,382 receipt lines scanned).
- **2120's sourcing rules contain NO "Transfer from" type** — only **"Buy from" (85,544 rules / 21,386
  items)** + **"Make at" (964)**. Mexico procures directly / makes locally; it does **not** participate in
  inter-org transfer.
- **2012 is the opposite** — a massive transfer hub: **395,940 "Transfer from" rules across 19 source orgs**
  (2013, 2093, 1080, 1019, 2014…), with **billions** in transfer receipts (e.g. 2012←2013 ≈ $1.4B).
Correct reframing: 2120's high receive/low ship is **inbound purchasing + local manufacturing**, not
transfer. So "hub vs producer" is real but **the roles are reversed from my first guess**: **2012 = network
hub (transfer-fed), 2120 = directly-sourced leaf.** The `org_role` attribute (Change 5) should encode
`transfer_hub` vs `direct_source` from the sourcing-rule mix, not assume the small org is the hub.

### N4 · Lean-yet-green inventory posture — VERIFIED
2120 holds **120 units** avg safety stock (vs 2,342 at 2012 — ~19× leaner) yet runs **62% green vs 36%**.
Mexico proves lower buffers + better health simultaneously — a just-in-time posture. **Risk:** that leanness
is only safe while demand stays stable; a demand shock tests it hard. This is a *positive* pattern worth
benchmarking, not an exception to alert on.

### N5 · Planned-PAB completeness 9× better — VERIFIED (via unplanned rate)
2.03% null planned_pab vs 18.17%. Either Mexico enforces plan-entry discipline, or 2012's global feed has
an ingestion gap. Actionable both ways: if it's a 2012 data gap, ~40K rows are silently unplanned.

---

## Part 3 — What must change in the data model / logic

The core lesson: **org is not just a filter — it's a context that changes how numbers should be judged.**
Minimum-sufficient changes (no overengineering):

### Change 1 — Org-aware thresholds (the big one)
Introduce a small **config table** `sandbox_operations.po_management.threshold_config`
keyed by `organization_code` (or plan_name), carrying the band cut-points:
`red_pct, yellow_pct, escalate_dollar, alert_dollar, unplanned_tolerance_pct, wow_alert_units`.
The gold's `onhand_status` / `alert_tier` derivation **joins this config on org** instead of hard-coding
15/30/50% + $50K/$200K. Recommended 2120 starting values (from its own quantiles): red band anchored at
2120 p95–p99 (~$1.3K–$9.6K), escalate ≈ $10–12K, unplanned tolerance <3%, WoW alert ~$100–200.
- **Better still (my recommendation):** make the bands **percentile-based within org** (e.g. red = top
  ~25–30% of that org's variance) so they auto-calibrate as new orgs load — no manual $ tuning per org.
  Keep an absolute-$ floor so a tiny org doesn't escalate on trivial dollars.

### Change 2 — Bias correction is per-org in MAGNITUDE (same sign, corrected)
Both orgs over-plan (on-hand > plan); the correction sign is the same, but the magnitude differs ~5×
(2012 +101% vs 2120 +21% mean overage). A forecast/plan-correction feature must read the **org's own**
bias magnitude and never apply 2012's to 2120 (it would over-correct ~5×). Store per-org rolling bias.

### Change 3 — Cross-org comparisons join on shared SKUs
Because 41% of 2120 SKUs are Mexico-only, cross-org tiles (imbalance, "same item at both DCs") must
**INNER JOIN on item across orgs**. Union-all breakdowns are fine *within* an org but must be labeled as
portfolio-blended, never presented as like-for-like.

### Change 4 — First-class planner attribute + a load/concentration view
Planner is already joined (1:1, no fanout — re-verified). Add a lightweight **planner-load** rollup
(rows & items per planner per org) so N1's key-person concentration is visible, and so per-planner bias
(2.4.3) generalizes cleanly to any org.

### Change 5 — Org role/type tag (hub vs producer)
N3 shows 2120 behaves as an inbound hub. A tiny `org_role` attribute (producer / hub / mixed) lets the
model interpret ship/receive ratios correctly rather than flagging a hub's low ship rate as a miss.
Start as a static lookup; revisit if more orgs load.

### What does NOT need to change
- The **grain, joins, semi-additive on-hand handling, receipt/shipment filters** all generalized to 2120
  with zero rewrite (grain re-verified clean). The org→plan predicate correctly prevents double-count.
- No new heavy engineering. Changes 1–5 are a config table + a couple of derived columns/attributes +
  join discipline — all inside the existing Rung-2/3 gold build.

---

## Part 4 — Honest limits (what gold alone can't prove)

- **Intercompany transfer (N3) — RESOLVED, not deferred:** now confirmed against the network tables
  (`prod_operations.manufacturing_sc.fact_transfer_order_receipt/shipment`, `features.inventory_rebalance_*`,
  `features.safety_stock_network_sourcing_rules`): **2120 does NOT transfer** (0 lines; sourcing = Buy/Make
  only). **2012 is the transfer hub** (19 source orgs, billions $). Earlier "implies 2012→2120 transfer" was
  refuted. These network tables are a newly-explored, richly-populated source for the physical-flow /
  hop / freight-cost stories (see the new discovery note in `D_network_flow_tables.md`).
- **Country-of-origin / import exposure:** COO mix and currency/tariff exposure could not be tested — the
  gold doesn't carry COO. If the business wants FX/import scenarios, add COO from `items_scd1` (read-only)
  in a follow-up. Flagged, not fabricated.
- **Demand-shock adequacy of the lean model (N4):** an analytical scenario, not a fact in the data.

---

## One-line takeaway for the build
> Loading 2120 proved the *logic* generalizes but the *judgement* does not: bands, bias, and comparison
> rules must be org-aware. The concrete asks are a per-org `threshold_config`, percentile-based bands,
> directional bias correction, shared-SKU cross-org joins, and small planner-load / org-role attributes —
> all fits inside the existing gold build, carried into the Rung-3 pipeline.
