# Data Stories — INDEX (start here)

**What this is:** query-driven data journeys and scenario coverage for the MKE supply-chain project (P1–P4),
built by tracing real anchor IDs through the actual tables on workspace `mke-rsc`. Every file is READ-ONLY
evidence: real printed rows, hop-by-hop narration, and an end-user lens (✅ answers a planner question /
⚠️ plumbing-or-gap). As-of 2026-08-30.

## Read order
1. `STORIES_CATALOG.md` — the map of scenarios + method + end-user-question lens.
2. `S0_hero_item_discovery.md` — how the hero anchor was chosen (not random) + presence map.
3. `KEY_FINDING_receipt_source.md` — the pivotal findings that change the build.
4. `STORIES_SYNTHESIS.md` — consolidated view, both polarities, decisions.
5. Individual stories (below) for depth.

## The hero anchor
item_bigint_key **3879620845706693458** = item_id **48111850**, "M18 XC5.0 BATTERY", ABC A. Chosen for
richest cross-table presence (plan + on-hand 47 orgs + 7,707 ship lines + 56K movements + real POs).

## Files by theme

### Core P1 journeys (plan vs actual, on the hero item)
- `S1_receipt_attainment.md` — plan→ordered→received; **found the clean receipt fact `purchase_receipt_line`**.
- `S2_onhand_and_why.md` — ending on-hand + the movement ledger explaining it; semi-additivity demo.
- `S3_shipment_attainment.md` — plan vs actual shipped; the 87%-null shipped_quantity gotcha.

### P2 supply exceptions
- `S5_stockout_priority.md` — SS-breach prioritized by unit miss; **raw unit-miss over-ranks cheap parts** (→ weight by cost×ABC).
- `S6_dc_imbalance.md` — same item long at one DC, short at another; rebalance-vs-order.
- `E2_supply_exceptions.md` — **all 18 types walked**; 11/18 detectable now; #9–11 need SKU supersession map; #3–6 excluded.

### P3 / P4 demand
- `S7_demand_event_journey.md` — a real expansion event Excel→fact; **item match is dash-normalization (98.7% vs 4.8%)**.
- `S9_forecast_drift.md` — +184K (+23,016%) baseline revision; **frozen_* cols 100% NULL → use process_date deltas**.
- `E34_demand_exceptions.md` — P3 (6 types) + P4 (6 types) walked; 5/6 each detectable.

### Polarity, workflow, time
- `G_positive_scenarios.md` — the GREEN twins (perfect receipt, healthy stock, stable forecast, strong fulfillment).
- `R_received_notreceived.md` — PO fulfillment-state matrix (fully/partial/past-due/over/not-yet) + unhappy plan-vs-actual.
- `V_extreme_variance.md` — biggest plan-vs-actual on-hand gaps + forecast-vs-actual misses (real numbers).
- `T_status_transitions_workflow.md` — "on-track last week, now not" (week Oct5: PAB 151,929→−3,464); trigger→decision→Lakebase state.
- `C_recoverable_counterfactuals.md` — exceptions that acting-in-time could have flipped (recoverable vs unavoidable; ~37% recoverable). [some anchors illustrative — prefer the real PO examples]
- `RW_rolling_windows.md` — Monday–Sunday rolling 4/13-week, WoW, weeks-of-cover. [pending/landing]

### Cross-cutting patterns
- `P_hidden_patterns.md` — phantom demand 8.4M units, 69M-unit reversals, MOQ 41,667×, China COO concentration, grain explosion.
- `AP_anti_patterns.md` — WRONG-vs-RIGHT with error magnitudes (priority flip 70×, on-hand inflate 5.48×, fulfillment understate 6.7×).
- `X_uncovered_scenarios.md` — blind-spot sweep: receipt acceptance quality, dead stock, PO velocity, seasonal hockey-stick, freshness SLA.
- `EM_emergent_patterns.md` — recently-onset: demand +705,033% (NPD), past-due cluster 46.5K lines (90% TTI), new shrink behavior.
- `LG_logistics_delays.md` — in-transit lag; items 99.99% dependent on in-transit stock (75K transit / 6 on-hand); 41-day-late receipts.
- `N_multiorg_weekly.md` — full org network (1019 Grenada 199M, 3PLs, branches); clean weekly Mondays (6/6); org-role plan rules.
- `O_location_persona.md` — segmentation by location-role (plant/DC/3PL/branch/service) and persona (planner/supplier routing).
- `L_lineage.md` — supply-chain physical lineage + data lineage (source→target); system.access lineage NOT available.

### Traceability / "where & what stage" (temporal lineage)
- `HOP_product_journey.md` — physical hop-chain (supplier→plant→transit→DC→customer); from→to works within an org, not across; no serial/lot.
- `STATE_pointintime_stage.md` — where the product is + what stage, as-of a date; time-lapse across daily snapshots.
- `QTY_status_breakdown.md` — ordered→received→open split, split-delivery schedules, multi-supplier per item (allocation_percent).
- `GEO_geography_data.md` — geography available (address/city/region/country, COO) vs missing (no lat/long); mapping needs geocode.

### Finance / dollars
- `FIN_finance_data.md` — where the money data lives (unit cost + buildup in dim_series_ext_vw, on_hand_cost, PO usd_*, sales revenue/COGS); standard-cost not GL.
- `LOSS_supply_chain_losses.md` — losses per issue in $ ($1.68B on-hand value, ~$4–5B overdue PO deduped); with the dedup/key/cost-base caveats.

### Question-driven syntheses (asked during review)
- `CAUSES_common_root_causes.md` — the most common operational + analytical root causes across all findings.
- `IMPACT_agentic_app.md` — if we build the agentic app: which records impacted good vs adverse; blast-radius ranking + rails.
- `THE_SEARCH_PAIN_JOURNEY.md` — **the first-person story of the pain**: why "data is in the mature EDW" ≠ "usable"; the 7 chapters of traps every user re-pays.

### Navigation & rollups
- `PRIORITY_MAP.md` — **every scenario tagged P1/P2/P3/P4** (primary ● / also ○) + per-priority rollup.
- `BEYOND_P1P4_scenarios.md` — **"P5 / Beyond"**: scenarios that fall under NO priority, grouped by owner
  (sourcing, ordering/excluded, finance, data-governance, supplier-quality, forecasting-method).

## Cross-file recurring lessons (the through-lines)
1. **Weight variance/priority by cost × ABC × org-role** — raw unit/qty magnitude points at penny components at plants (S5, V1, P).
2. **`purchase_receipt_line` is the clean receipt fact** — the raw-Oracle-id crosswalk isn't needed (S1, KEY_FINDING).
3. **Semi-additive on-hand & transfer double-counting** — never sum on_hand across dates; net inter-org flows (S2, AP).
4. **Multi-snapshot is mandatory** — single-snapshot dashboards hide "was green now red" and emergent onset (T, EM, AP).
5. **Signal ≠ workflow state** — prod data gives trigger+evidence; approve/reject/dispose live in Lakebase (T, E2, E34).
6. **Demand forecast >> actual (phantom demand)** is a real, large P4/P1 signal, seasonality-guarded (V, P, S9).
