<div align="center">

# V14 · Uncovered Scenarios — Threads Surfaced but Not Yet Pursued

### Re-reading V1–V13 + the day-in-the-life for scenarios that got *mentioned* but never broken out

</div>

**Why this exists:** the validation files repeatedly surfaced side-observations that were noted and moved past.
This is a deliberate sweep to list them, with a **quick live probe** where cheap, so nothing is silently dropped.
Status: 🆕 candidate (worth a real validation pass) · ⚪ confirmed-absent (a finding in itself) · 💭 flag-only.

---

## N1 · Transition SKUs (new-product / phase-in–phase-out) — ⚪ confirmed-absent where expected
- **The thread:** the transcript named **"transition-level"** as one of the *two biggest template permutations*
  (with multi-org). The demand fact has `transition_active_flag` / `transition_eligible_flag`; the supply-plan
  family has a **"23 Transition SKU Supply Plan."** We never tested it.
- **Live probe:** `transition_active_flag` / `_eligible_flag` are **100% NULL** across 18B `10_demand_daily`
  rows; **no `%Transition%` plan rows in `20_supply_daily`.** So the transition population is **not populated in
  the tables we read** — it likely lives in a plan/schema we haven't sourced.
- **Why it matters:** transition (NPD ramp / end-of-life) is a *distinct root cause* — a shortage on a phasing-in
  SKU is a different story (ramp risk) than a mature-SKU shortage, and the transcript's reason-code taxonomy has
  **"NPD/Transition assumptions"** and **"Make-to-Order"** as named miss reasons. **Action:** find where
  transition status is populated (candidate: `21_supply_daily` / a transition-specific plan / an item-master
  flag) → then a **NPD/transition-risk lens**.

## N2 · Over-forecast (positive-bias) customers → the demand *cause* of EXCESS — 🆕 candidate
- **The thread (V8):** most customers are under-forecast, **but CAN REGIONAL (+1.25M) and CONST_IND (+361k) are
  chronically *over*-forecast.** V8 flagged "route these to excess/E&O" but we never closed the loop.
- **Why it matters:** this is the **causal link between demand and excess** — the mirror of "under-forecast →
  shortage." Over-forecast customers are likely a *source* of the $452M excess (V7). Nobody connects the demand
  bias board to the excess board today.
- **Action:** join positive-bias customers (V8) → their SKUs' excess position (V7). A "your over-forecasting is
  creating $X of overstock" handoff — the E&O-prevention counterpart to the shortage re-baseline.

## N3 · Returns / warranty / reverse logistics — 🆕 candidate (whole domain untouched)
- **The thread:** never explored — but the tables exist: `dimension.warranty_scd1`,
  `domain_item.fact_item_service_return_eligibility`, `staging_jde.fact_warranty_tool`,
  `staging_ax.return_reason_code_temporal`.
- **Why it matters:** returns are **both a demand signal and a supply source** — a spike in returns can create
  phantom demand or unexpected available stock; warranty/repair flow is a real supply-chain lens the Day-3 scope
  never touched. Milwaukee is a tool brand → warranty volume is material.
- **Action:** profile the returns/warranty facts; assess whether a returns signal belongs in the demand-surprise
  decomposition or as its own root cause.

## N4 · "Found inventory" — positive adjustments as a *supply source*, not just a loss — 🆕 candidate
- **The thread (V5):** adjustments were framed as *losses*, but the data showed **`CC-RECOUNT` = +42,081,673
  units FOUND.** We treated adjustments one-directionally.
- **Why it matters:** a large positive cycle-count adjustment is **unexpected available supply** — it can *heal*
  a shortage or reveal that a "shortage" was a counting error (ties to DK-11 count-integrity). Today the tool
  would only ever read adjustments as bad news.
- **Action:** split adjustments **signed** — negative = loss (root cause), positive = found supply (a heal
  signal / count-integrity flag). A found-inventory event on a shortage SKU should downgrade its severity.

## N5 · Non-standard demand streams (NO CHARGE / OTHER NA) — 💭 flag-only
- **The thread (V3):** **"NO CHARGE" (+186%)** and **"OTHER NA" (+204%)** rank among the worst-consumed — but
  they're *catch-all / non-standard* streams (samples, no-charge, unclassified), not real customer demand.
- **Why it matters:** these may be **polluting the demand-surprise signal** — a chronic "miss" driven by
  no-charge/sample volume isn't a forecasting failure to escalate. Conversely, if no-charge volume is large and
  unplanned, that's its *own* leakage story.
- **Action:** segregate/label non-standard DG5 streams so they don't distort the customer bias ranking; decide
  whether they're noise (exclude) or a real leakage (own lens).

## N6 · Component / bulk orgs (8000, 2092) & bimodal UoM — 💭 flag-only (recurring across V1/V2/V5/V7/V9)
- **The thread:** org **8000** ($7.5M-scale single-SKU gaps), org **2092** (heavy in forward-risk), and huge-UoM
  SKUs (`88937095` SS ~10.4M) recur as *outliers that distort $-rankings.*
- **Why it matters:** these are almost certainly **component / raw-material / bulk orgs** at a different grain
  than finished-goods DCs — mixing them into a finished-goods shortage ranking is a category error (already
  flagged as a DQ guard, but never *scoped as its own view*).
- **Action:** a **component/raw-material lens** is likely warranted (dependent demand, BOM explosion) — a
  different audience (manufacturing planning) than the DC shortage planner. At minimum, segregate before ranking.

## N7 · Recovery velocity / "time-to-heal" — 💭 flag-only
- **The thread (V12):** we found transient dips (1 week) recover, but never measured **how *fast* a typical
  breach heals**, or which SKUs heal slowly.
- **Why it matters:** a WATCH item that historically heals in 1 week is safer than one that historically takes 6.
  "Time-to-heal" would sharpen the WATCH vs ACT line and the do-nothing confidence.
- **Action:** from snapshot history, measure per-SKU mean weeks-below-then-recover → a "self-heal velocity" that
  informs the action verdict.

---

## Summary

| # | Uncovered scenario | Status | Value | Next step |
|---|---|:--:|:--:|---|
| N1 | Transition / NPD SKUs | ⚪ absent where looked | 🔥🔥 | find where transition status is populated |
| N2 | Over-forecast → excess causal link | 🆕 candidate | 🔥🔥🔥 | join V8 positive-bias → V7 excess |
| N3 | Returns / warranty / reverse logistics | 🆕 candidate | 🔥🔥 | profile warranty/return facts |
| N4 | "Found inventory" (positive adjustments) | 🆕 candidate | 🔥🔥 | sign-split adjustments; heal signal |
| N5 | Non-standard demand (NO CHARGE / OTHER NA) | 💭 flag | 🔥 | segregate/label; noise vs leakage |
| N6 | Component/bulk orgs & UoM | 💭 flag | 🔥🔥 | dedicated component lens; segregate |
| N7 | Recovery velocity / time-to-heal | 💭 flag | 🔥 | self-heal velocity from snapshots |

**The two highest-value new ones:** **N2** (over-forecast customers are the *demand cause of excess* — closes the
demand↔excess loop, mirror of under-forecast→shortage) and **N1** (transition/NPD is a named root cause the
transcript emphasized but the data doesn't surface where we looked — needs sourcing).

**Honest caveat:** these are **leads**, not validated screens — each needs its own live pass (like V1–V13)
before it earns a requirement. Logged so the analysis is complete and nothing was silently dropped.

*All probes READ-ONLY on `mke-rsc` / warehouse `7bd33a82f4e92206`, 2026-09-03.*
