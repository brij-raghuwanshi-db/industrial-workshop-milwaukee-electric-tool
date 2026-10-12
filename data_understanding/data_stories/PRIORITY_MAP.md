# Scenario → Priority tag matrix

Every data-story / scenario file tagged to P1 / P2 / P3 / P4 (and cross-cutting). ● = primary home,
○ = also serves. As-of 2026-08-30. Priorities: **P1** Actuals Supply Plan · **P2** Supply Exceptions ·
**P3** Demand Events App · **P4** Demand Exceptions.

| File / scenario | P1 | P2 | P3 | P4 | Primary priority — why |
|---|:--:|:--:|:--:|:--:|---|
| S0 hero item discovery | ○ | ○ | ○ | ○ | cross-cutting — the conformed join spine all four use |
| S1 receipt attainment | ● | ○ | | | P1 M1: planned vs actual PO receipts |
| S2 on-hand & why it moved | ● | ○ | | | P1 M3 + variance root-cause 2.3.7 |
| S3 shipment attainment | ● | | | ○ | P1 M2: planned vs actual shipped |
| S5 stockout / SS-breach priority | ○ | ● | | | P2 exc #1/#8, largest-unit-miss prioritization |
| S6 DC imbalance / rebalance | | ● | | | P2 exc #15 (order-vs-rebalance) |
| S7 demand event journey | | | ● | ○ | P3 event Excel→fact, validation, mkedg5 map |
| S9 forecast drift | | | ○ | ● | P4 "changed since last plan"; deep-links to P3 |
| E2 supply exceptions (18 types) | ○ | ● | | | P2 — the full supply taxonomy walk |
| E34 demand exceptions | | | ● | ● | P3 event-validation types + P4 forecast-exception types |
| G positive/green scenarios | ● | ○ | | ○ | P1 mostly (healthy receipt/stock/forecast/fulfillment); green twins of S-stories |
| R received / not-received matrix | ● | ● | | | P1 receipt actuals + P2 #12 past-due queue |
| V extreme variance + forecast-vs-actual | ● | ○ | | ● | P1 plan-vs-actual on-hand tail + P4 forecast≫actual |
| T status transitions & workflow | ○ | ● | ○ | ○ | P2 exception lifecycle; P3 event lifecycle; "was green now red" spans all |
| C recoverable counterfactuals | ○ | ● | | ○ | P2 — the ROI case for the exception queue |
| RW rolling windows (Mon–Sun) | ● | ○ | | ○ | P1 weekly grain; rolling KPIs stabilize P2 alerts |
| LG logistics delays | ● | ● | | | P1 Supply-Timing variance; P2 #7/#12/#13 |
| P hidden patterns | ○ | ● | ○ | ● | cross-cutting: phantom demand (P4), MOQ/COO/reversals (P2), grain (all) |
| AP anti-patterns | ● | ● | ● | ● | cross-cutting guardrails — protect every priority's numbers |
| X uncovered / blind-spot sweep | ○ | ● | | ○ | mostly P2/ops (dead stock, PO velocity, acceptance quality, freshness) |
| EM emergent patterns | ○ | ● | | ● | early-onset supplier/demand/plan signals — P2 + P4 |
| O location-role & persona | ○ | ● | ○ | ○ | routing/filtering — how every priority's queue is segmented |
| L lineage | ● | ○ | ○ | ○ | the source→target map underpinning P1 first, reused by all |
| HOP product journey | ● | ○ | ○ | | P1/control-tower flow view; node-to-node quantity hops (traceability capability) |
| STATE point-in-time stage | ● | ○ | ○ | ○ | temporal lineage — where/what-stage as-of a date; powers "was green now red" (all) |
| QTY status breakdown | ● | ● | ○ | | ordered→received→open + multi-supplier; P1 receipt detail, P2 supply status |
| GEO geography data | ○ | ○ | ○ | ○ | cross-cutting enabler — region/COO geography for maps & sourcing risk |
| CAUSES common root causes | ● | ● | ● | ● | cross-cutting synthesis — root-cause rollup across all four |
| IMPACT agentic app | ● | ● | ● | ● | cross-cutting — record blast-radius if the app is built; governs all writes |
| FIN finance data | ● | ● | ● | ● | cross-cutting — the $ columns that dollarize every priority's units |
| LOSS supply-chain losses | ● | ● | ○ | ● | cross-cutting — losses per issue in $ (P1 variance $, P2 overdue/exception $, P4 forecast-error $) |
| THE_SEARCH_PAIN_JOURNEY | — | — | — | — | meta — the pain narrative; not a priority scenario |

## Rollup — how many scenarios touch each priority
- **P1 (Actuals Supply Plan):** primary in S1, S2, S3, G, R, V, RW, LG, AP, L; supporting in most others. The
  best-covered priority (it's the foundation).
- **P2 (Supply Exceptions):** primary in S5, S6, E2, T, C, LG, EM, X, O, AP, P; the richest exception surface.
- **P3 (Demand Events):** primary in S7, E34; supporting in P, O, L. Distinct data world (demand fact +
  events + customer hierarchy).
- **P4 (Demand Exceptions):** primary in S9, E34, V; supporting in P, EM, AP. Leans on 10_demand_daily +
  frozen-column gap → process_date deltas.

## Notes on multi-priority scenarios
- **AP anti-patterns and L lineage are deliberately all-four** — they're guardrails/plumbing every priority depends on.
- **T (transitions/workflow)** spans P2 (case lifecycle) and P3 (event In Progress→Active→Deactivated) because
  the *workflow* mechanic differs by priority even when the *transition* idea is shared.
- **V and P** each straddle P1 (supply variance) and P4 (demand/forecast) because forecast-vs-actual is both a
  P1 demand-variance input and a P4 exception.
- The **excluded PO-ordering scope** (pull-in/push-out/create/cancel PO, truckload grouping) is NOT a priority
  here — flagged in E2 and the catalog; scenarios stay evidence-only, no PO writes.
