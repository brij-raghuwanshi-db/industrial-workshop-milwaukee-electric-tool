# Most common causes of issues — synthesized across all findings

**As-of 2026-08-30.** This aggregates the root causes seen repeatedly across the 24 story files. Two kinds:
**(A) Business/operational causes** (why the supply chain misses) and **(B) Data/analytical causes** (why the
numbers mislead). Ranked by how often they recurred across the traces. Every cause cites the files it came from.

## A. Business / operational root causes (why plans miss reality)

### A1. Supply timing — goods late or stuck in transit (MOST COMMON supply miss)
- **Evidence:** 356K PO lines past-due-not-received (R); receipts up to 41 days late (LG, T); interorg
  transfers arriving a day+ after demand (S2: transfer +87K landed the day AFTER the −32K spike); items
  **99.99% dependent on in-transit stock** (LG: 75K transit / 6 on-hand).
- **Why:** supplier delay, port/ocean lane time, receiving-dock booking lag, transfer not pre-positioned.
- **Maps to:** P1 variance category *Supply Timing*; P2 #7 supplier-late, #12 past-due, #13 lead-time-drift.

### A2. Demand ≠ forecast — over-forecasting / phantom demand (MOST COMMON demand miss)
- **Evidence:** forecast 269K vs shipped 4K on one A-item; several A-items forecast 100K+, **shipped 0** (V);
  **8.4M units** of standing forecast on pairs with zero shipments (P); +184K (+23,016%) baseline revision (S9).
- **Why:** forecasts on dead/slow SKUs, seasonality/timing mismatch (winter gloves forecast in July),
  manual baseline overrides without recorded reason, events double-counted or mis-timed.
- **Maps to:** P4 forecast exceptions; P1 demand-variance; P3 event accuracy.

### A3. Inventory in the wrong place — network imbalance
- **Evidence:** same item 869K at Olive Branch vs 393K at Byhalia (S6); 19,234 items with >10× cross-org
  variance (E2); a 3PL systematically short on 2,000+ SKUs/week (N).
- **Why:** allocation not rebalanced to demand; new orders placed into already-long DCs instead of transferring.
- **Maps to:** P2 #15 DC imbalance; the order-vs-rebalance decision.

### A4. Too much inventory — excess / working capital tied up (the other tail)
- **Evidence:** 1.44M excess-vs-target rows / **37% of active SKUs** (E2); a screw at 1,925,119 units vs SS=2;
  MOQ waste 41,667× (P); dead stock 200–300 items, $50K–$200K locked (X).
- **Why:** MOQ over-ordering, obsolescence not run down, safety-stock parameters mis-set (1–2 unit SS on
  commodities), demand that never came.
- **Maps to:** P2 #2 excess; B3 finance/working-capital.

### A5. Supplier & sourcing concentration risk
- **Evidence:** 919 A-items single-sourced from China; long import lanes with high freight/import-fee share
  (P, LG, B1); 90% of the emergent past-due cluster is TTI-family (EM).
- **Why:** single-source, single-COO, consolidated manufacturing bottleneck.
- **Maps to:** B1 sourcing risk; feeds P2 lead-time exceptions.

### A6. Plan instability / stale plan
- **Evidence:** week Oct-5 flipped PAB 151,929 → −3,464 across snapshots (T); plan projected 60K while actual
  path hit 70K after a spike the plan never saw (S2); plan 21 stale 18 days (E2).
- **Why:** static snapshot can't absorb mid-cycle shocks; plan nervousness swings week-to-week.
- **Maps to:** P1 plan accuracy/bias; P2 #14 forecast-change, #17 frozen-zone.

## B. Data / analytical root causes (why the numbers mislead) — these are as common as the business ones

### B1. Wrong grain / semi-additivity (MOST COMMON data trap)
- **Evidence:** summing on-hand across dates inflates 5.48× (AP, S2); 20_supply_daily splits into up to 3,989
  rows per product×org×week via series/order_type (P, AP); transfer movements double-count as ship+receive
  across subinventories so the ledger won't tie to on-hand (S2, AP).
- **Fix:** on-hand = point-in-time (never sum over time); GROUP BY the true grain; net inter-org flows.

### B2. Ranking by raw magnitude instead of business impact
- **Evidence:** the #1 "safety-stock breach" by unit-miss was a **$0.0134 carbide component at a plant**
  (~$235K, un-expeditable), not a crisis (S5, V); priority flips 70× when you weight by cost (AP).
- **Fix:** rank by unit-miss × applied_standard_cost, stratified by ABC and org-role (plant vs DC).

### B3. Single-snapshot blindness
- **Evidence:** "was green last week, now red" and emergent onset are invisible on one snapshot (T, EM, AP);
  the daily-snapshot history is what makes them visible.
- **Fix:** always compare the same target week across snapshots (multi-vintage).

### B4. Wrong source table / key mismatch
- **Evidence:** doc pointed at raw-id `receiving_receipt_transactions` (no item column) instead of the clean
  `purchase_receipt_line` (S1, KEY_FINDING); expansion item match 4.8%→98.7% after dash-normalization (S7);
  87%-null shipped_quantity must be status-filtered or fulfillment understates 6.7× (S3, AP).
- **Fix:** use the modeled EDW facts + conformed bigint keys; normalize item codes; filter to
  shipped/invoiced non-null.

### B5. Missing / unpopulated data
- **Evidence:** `frozen_*` columns 100% NULL → P4 "since last freeze" needs process_date deltas (S9);
  no SKU-supersession map → P2 transition exceptions #9–11 undetectable (E2); no lat/long (GEO);
  demand↔supply is an inferred link, not a hard key (L).
- **Fix:** escalate pipeline gaps; build the missing bridges in sandbox; treat as prerequisites.

### B6. Master-data hygiene
- **Evidence:** orphaned 2020–2021 promised dates on active POs; "FULLY RECEIVED" lines still flagged open
  (E2); COO codes not normalized (US/USA, CN/CHN) (GEO); mkedg0 case inconsistency (D).
- **Fix:** canonicalization + status-logic audit before trusting counts.

## The one-paragraph answer
Across everything, the **most common OPERATIONAL cause is supply-timing/logistics delay** (late or in-transit-
stuck receipts, transfers arriving after the need) closely followed by **demand not matching forecast**
(over-forecasting / phantom demand) and **inventory in the wrong place or in excess**. The **most common
ANALYTICAL cause is grain/semi-additivity mistakes** (summing point-in-time on-hand, double-counting transfers,
ignoring the series/order_type split), then **ranking by raw magnitude instead of $×ABC×org-role**, and
**single-snapshot blindness**. A large share of apparent "issues" are actually **data-trust problems**
(wrong source table, unnormalized keys, null columns, stale/orphaned records) that must be fixed as
prerequisites — otherwise the real business exceptions get buried under artifacts.
