# Beyond P1–P4 — scenarios that don't belong to any of the four priorities

**As-of 2026-08-30 · READ-ONLY.** During the scenario hunt we surfaced real, query-backed signals that are
NOT P1 (Actuals Supply Plan), P2 (Supply Exceptions), P3 (Demand Events), or P4 (Demand Exceptions). They're
valuable but belong to *other* owners/programs. Grouped here as **"P5 / Beyond"** so they're not lost — and
so they don't get mis-scoped INTO P1–P4. Each is tagged with a proposed owner and whether it's in the
already-known **excluded** scope (Red Keychain ordering) or genuinely new.

## B1 — Strategic sourcing & supply-risk (owner: Sourcing / Supply Risk, not P1–P4)
Cross-node structural risk, not a per-week plan-vs-actual or an exception queue item.
- **Country-of-origin concentration** — 919 A-items single-sourced from China (P_hidden_patterns). Geopolitical/
  tariff/port exposure. Not P2 (no per-item action); it's a sourcing-strategy signal.
- **Single-source suppliers on high-ABC items** — supplier/site concentration (X, O). Resilience/dual-source.
- **Currency / FX exposure** — non-USD `currency_code` sourced items (X_uncovered). Finance/treasury.
- **Import-lane / lead-time concentration** — high freight+import-fee share of standard cost on long ocean
  lanes (LG_logistics_delays L2). Network design, not weekly ops.

## B2 — Procurement optimization / ordering execution (owner: Red Keychain ORDERING — the EXCLUDED scope)
These overlap the explicitly out-of-scope PO/ordering program. Recorded so they route there, not into P2.
- **MOQ waste** — 41,667× overage (12-unit forecast vs 500,000 MOQ) (P_hidden_patterns). Supplier-terms /
  order-sizing. (Red Keychain NEW-5 PO grouping / order economics.)
- **PO velocity / order consolidation** — items with 18–28 POs/year, truckload consolidation opportunity
  (X_uncovered). This is the Truckload-PaaS replacement scope (NEW-5/8/17) — excluded from P2.
- **Requested-vs-confirmed, pull-in/push-out/create/cancel PO** — the whole ordering-action layer. Excluded
  by project scope; scenarios here stay evidence-only.

## B3 — Inventory financial health / working capital (owner: Finance / Inventory Planning)
- **Dead stock / obsolescence** — 200–300 items with on-hand >0 and 90+ days no movement; $50K–$200K locked
  (X_uncovered). Write-off / provision — not a supply-timing exception.
- **Inventory $ concentration** — top 2–3 orgs hold 50%+ of inventory value; single-DC capital exposure
  (X_uncovered, O_location_persona). Capex/resilience.
- **Excess inventory** (the "too much" tail) — 1.44M excess-vs-target rows / 37% of SKUs (E2). *Partly* P2
  (#2 excess), but the systemic working-capital view is a finance rollup beyond the per-item queue.

## B4 — Data governance / quality / pipeline ops (owner: Data Engineering / Analytics Eng)
Not business exceptions — data-trust issues that must be fixed UNDER P1–P4 but aren't themselves scenarios.
- **Inventory reversals / shrink** — 69M units of negative movement on one item; unexplained cycle-count
  adjustments (P_hidden_patterns, EM6). Governance audit.
- **Orphaned/ancient records** — active-2026 open POs with 2020–2021 promised dates; "FULLY RECEIVED" lines
  still flagged open (E2 gotchas). Master-data hygiene.
- **Data freshness / SLA** — fact-table staleness monitoring (X_uncovered); plan 21 stale 18 days (E2).
- **Frozen_* columns 100% NULL** in 10_demand_daily (S9) — pipeline gap blocking the intended P4 mechanism.
- **Grain-split fan-out** (series/order_type) & **semi-additivity / transfer double-count** (AP) — modeling
  guardrails, not scenarios.
- **Raw-Oracle-id vs bigint, dash-normalization** (S1, S7) — conforming rules.

## B5 — Supplier performance management (owner: Supplier Quality / SRM)
- **Receipt acceptance / rejection quality** — suppliers with <90% acceptance; units rejected/held
  (X_uncovered). Supplier scorecard / corrective action — a supplier-relationship program, not the P2 queue
  (though a bad score can *raise* P2 lead-time-risk exceptions).
- **Emergent supplier on-time deterioration** (EM1) — feeds P2 #7/#13 as a *signal*, but the scorecard/SRM
  program that acts on trends is beyond P2.

## B6 — Forecasting method / NPD (owner: Demand Planning method team)
- **Seasonal hockey-stick** — 200–300 items with 1.5–4× Q4 spikes (X_uncovered). A forecasting-model tuning
  concern; it *causes* P4 exceptions but the method fix is upstream.
- **New-product (NPD) launch ramp** — 8 products launched Aug 2026, one +705,033% in 4 weeks (EM2). NPD
  planning discipline; surfaces AS a P4 new-item-signal-gap but the launch process is its own thing.
- **Phantom demand** — forecast on items with zero sales (P, V). Straddles P4 (exception) AND a
  forecasting-hygiene program (why is the model forecasting dead SKUs?).

## How to use this bucket
- **Don't build these into P1–P4.** Route B1→Sourcing, B2→Red Keychain ordering (excluded), B3→Finance,
  B4→Data Eng (but fix as prerequisites), B5→Supplier Quality, B6→Demand-Planning method.
- **B4 is special:** it's not a deliverable, it's a set of **prerequisites/guardrails** that P1–P4 must honor
  (and a few pipeline gaps to escalate). Track it as risk, not scope.
- Several items are **dual-homed** — they *emit a signal* a priority consumes (e.g. supplier deterioration →
  P2) but the *program that owns the fix* is here. Tag = "signal to Pn, owned by B-group."

## One-line proposed P5 definition
> **P5 (Beyond) = structural, financial, data-quality, supplier-management, and forecasting-method concerns
> that the data reveals but that sit outside the four operational planner priorities** — to be routed to
> their owners, with B4 (data governance) treated as prerequisites to P1–P4 rather than separate scope.
