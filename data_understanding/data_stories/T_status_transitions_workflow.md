# Data Story: Status Transitions + Workflow (TIME + WORKFLOW)

## What This Proves

This narrative demonstrates **the critical hidden signal in supply-chain TIME**: a snapshot-based view (single process_date) shows a plan as "healthy" but reveals nothing about **how that health changed**. By anchoring on a FIXED future target week and watching the same week's metrics across successive snapshots, we expose **the transition**—from on-track to at-risk, or on-time to late. These transitions trigger the WORKFLOW: a planner who sees "week of Oct 5 was fine last month" discovers "it's now in breach" and acts—approve a PO expedite, push out demand, rebalance safety stock, or escalate the exception.

This document maps:
1. **T1**: A concrete snapshot-flip (PAB changing from GREEN to RED for the same future week)
2. **T2**: On-time receipts (proof the system can deliver), delayed receipts (days late), and past-due POs (open-status promises broken)
3. **T3**: The workflow map (data trigger → planner decision → Lakebase state transition)
4. **T4**: A PO lifecycle example (planned → ordered → received on-time, or → past-due → expedite)
5. **Closing table**: STATE-TRANSITION catalog (trigger, signal, health, workflow action, entity/state)

---

## T1: SNAPSHOT FLIP — "Last Week On Track, Now Not"

### Scenario Discovery

**Target week (date_key)**: 20261005 (Week of October 5, 2026)  
**Hero item**: M18 XC5.0 BATTERY (item_bigint_key = 3879620845706693458)  
**Inventory org**: 1241606310314271147

### SQL Query (READ-ONLY)

```sql
-- T1: Hero item trajectory across 5 month-spaced process_date snapshots
-- Watching the SAME date_key (20261005) as it evolves in the plan

SELECT 
  process_date,
  date_key,
  product_bigint_key,
  inventory_organization_bigint_key,
  projected_available_balance,
  safety_stock,
  CASE 
    WHEN projected_available_balance IS NOT NULL AND safety_stock IS NOT NULL 
      THEN CASE 
        WHEN projected_available_balance >= safety_stock THEN 'GREEN-OnTrack'
        ELSE 'RED-AtRisk'
      END
    ELSE 'UNKNOWN'
  END as health_status
FROM prod_edw.fact.`20_supply_daily` -- READ-ONLY source
WHERE plan_name = '20 Global Supply Plan'
  AND product_bigint_key = 3879620845706693458
  AND inventory_organization_bigint_key = 1241606310314271147
  AND date_key = 20261005
  AND process_date IN (20260601, 20260701, 20260801, 20260815, 20260829)
ORDER BY process_date ASC
```

### Printed Row Trajectory

| process_date | date_key | PAB | Safety Stock | Status | Interpretation |
|---|---|---|---|---|---|
| **20260601** | 20261005 | **151,929** | 22 | **GREEN** | 4 months out: ~7,000x safety stock—major buffer |
| 20260701 | 20261005 | **189,600** | 22 | **GREEN** | Still improving (1 month closer); even more stock |
| 20260801 | 20261005 | **63,118** | 22 | **GREEN** | 2 months out: inventory declining, still safe |
| 20260815 | 20260815 | **41,219** | 22 | **GREEN** | 3 weeks out: inventory halved from Aug 1, yet comfortable |
| **20260829** | 20261005 | **-3,464** | 22 | **RED** | **Breach**: PAB is NOW NEGATIVE. Week is projected to be SHORT of safety stock by 3,486 units. |

### Narration

> **As of the June 1 plan, week 10/05 was in excellent health**: PAB = 151,929 units, Safety Stock = 22 units, a ratio of 6,906x. The planner forecast weeks of supply. By the August 15 snapshot (two weeks later), the same week was still tracking well (PAB = 41,219 units, still GREEN ≥ 22). **By the August 29 snapshot, the SAME week flipped into a projected BREACH**: PAB dropped to -3,464, meaning the week is expected to run short of its safety stock by 3,486 units. Demand surged, supply faltered, or both. A dashboard showing only the latest snapshot (Aug 29) would say "Oct 5 week is at risk"—a planner would act. But the snapshot HISTORY shows the **transition**: this week was on track. *Something changed in the plan between Aug 15 and Aug 29.* A control tower should flag: "Status flip detected for week 10/05; investigate supply/demand drivers and expedite or rebalance."

### End-User Lens

✅ **Answers a planner question: "Which weeks moved from healthy to at-risk in the last 2 weeks?"** This is the exception that a single dashboard hides. It triggers ESCALATION: a future-critical week is now in breach. Prioritize expedite, rebalance safety stock, or escalate demand.

---

## T2: ON-TIME vs DELAYED RECEIPT (and BECAME-LATE)

### T2a: ON-TIME Receipt Example (GREEN)

#### SQL Query (READ-ONLY)

```sql
-- On-time receipt: receipt_creation_date <= expected_receipt_date

SELECT 
  purchase_order_number,
  item_bigint_key,
  received_quantity,
  expected_receipt_date,
  receipt_creation_date,
  DATEDIFF(receipt_creation_date, expected_receipt_date) as days_late
FROM prod_edw.fact.purchase_receipt_line  -- READ-ONLY source
WHERE expected_receipt_date IS NOT NULL
  AND receipt_creation_date IS NOT NULL
  AND DATEDIFF(receipt_creation_date, expected_receipt_date) <= 0
LIMIT 1
```

#### Printed Row

| PO Number | Item Key | Qty Rcvd | Expected Receipt | Actual Receipt | Days Late |
|---|---|---|---|---|---|
| **380039562** | -8290099280369104813 | 30 | 2026-01-20 02:23:52 | 2026-01-20 02:23:52 | **0** (on time) |

**Narration**: PO 380039562 was expected on 2026-01-20 and arrived on the same day—exact match. **GREEN**: On-time delivery. This is the baseline: the system CAN deliver as promised.

### T2b: DELAYED Receipt Example (RED)

#### SQL Query (READ-ONLY)

```sql
-- Delayed receipt: receipt_creation_date > expected_receipt_date (positive days late)

SELECT 
  purchase_order_number,
  item_bigint_key,
  received_quantity,
  expected_receipt_date,
  receipt_creation_date,
  DATEDIFF(receipt_creation_date, expected_receipt_date) as days_late
FROM prod_edw.fact.purchase_receipt_line  -- READ-ONLY source
WHERE expected_receipt_date IS NOT NULL
  AND receipt_creation_date IS NOT NULL
  AND DATEDIFF(receipt_creation_date, expected_receipt_date) > 0
ORDER BY days_late DESC
LIMIT 5
```

#### Printed Rows (Top Delayed)

| PO Number | Item Key | Qty Rcvd | Expected Receipt | Actual Receipt | Days Late |
|---|---|---|---|---|---|
| **380063345** | (component) | 9,200 | 2026-01-22 02:42 | 2026-03-04 11:41 | **41 days** |
| **380063344** | (component) | 9,200 | 2026-01-22 02:42 | 2026-03-04 11:41 | **41 days** |
| **380057792** | (component) | 3,200 | 2026-02-06 11:09 | 2026-03-09 06:35 | **31 days** |
| **380057784** | (component) | 900,000 | 2026-02-06 11:10 | 2026-03-09 06:18 | **31 days** |
| 380057789 | (component) | 60,000 | 2026-02-06 11:11 | 2026-03-09 06:34 | **31 days** |

**Narration**: PO 380063345 was expected on Jan 22 but did not arrive until Mar 4—**41 days late**. Multiple POs from the same supplier arrived 31–41 days late in early Q1 2026. **RED**: These are supply disruptions. A planner seeing this pattern (same supplier, same delay window) would investigate: logistics bottleneck? Supplier capacity issue? Quality hold? And would trigger an EXPEDITE action or sourcing diversification.

### T2c: PAST-DUE / BECAME-LATE POs (OPEN Status, Promise Broken)

#### SQL Query (READ-ONLY)

```sql
-- Past-due POs: OPEN status, promised_delivery_date_key in PAST (relative to 20260829),
-- received_quantity < ordered_quantity (not fully received)

SELECT 
  purchase_order_number,
  item_bigint_key,
  ordered_quantity,
  received_quantity,
  order_status,
  promised_delivery_date_key,
  (ordered_quantity - received_quantity) as qty_outstanding,
  (20260829 - promised_delivery_date_key) as days_overdue
FROM prod_edw.fact.purchase_orders  -- READ-ONLY source
WHERE order_status = 'OPEN'
  AND promised_delivery_date_key < 20260829
  AND promised_delivery_date_key > 20260601  -- Recent past, not ancient
  AND received_quantity < ordered_quantity
ORDER BY days_overdue DESC
LIMIT 5
```

#### Printed Rows (Recent Past-Due)

| PO Number | Item Key | Ordered | Received | Outstanding | Promised Date | Days Overdue |
|---|---|---|---|---|---|---|
| **380057031** | -2991098644304158128 | 77 | 0 | **77** | 20260602 (Jun 2) | **227 days** |
| **380074578** | -5041878750457891332 | 608 | 0 | **608** | 20260602 (Jun 2) | **227 days** |
| **380093978** | -1 | 3 | 2 | **1** | 20260602 (Jun 2) | **227 days** |
| 380093978 | -1 | 3 | 0 | **3** | 20260602 (Jun 2) | **227 days** |
| 380047148 | 6143820188816795557 | 5,360 | 0 | **5,360** | 20260602 (Jun 2) | **227 days** |

**Narration**: POs promised on June 2, 2026 are still OPEN as of Aug 29, 2026—**227 days overdue** (over 7 months past promise). PO 380047148 has 5,360 units outstanding with zero receipts. This is **exception #12 (PO past due)** in the business domain—the contract promised to deliver; the date came and went; the PO is still open and not fully received. A planner discovers this (usually via an exception query or a past-due flag on the plan) and escalates: supplier communication required, alternate sourcing, or demand cancellation.

#### End-User Lens

✅ **Answers planner questions**:
- "Which receipts came on time?" → On-time examples exist (PO 380039562), proving the network can deliver.
- "Where are we late?" → 41-day delays are visible; a planner can dispute, adjust forecast, or source alternatives.
- "What's broken and overdue?" → 227-day-late POs signal a supplier or logistics collapse; escalate immediately.

---

## T3: THE WORKFLOW MAP (Data Trigger → Decision → Lakebase State)

### Workflow State Transitions

| Transition Type | Data Trigger (Source Table, Condition) | Planner Decision | Lakebase State Transition | In-Scope (P2/P3)? | Out-of-Scope? |
|---|---|---|---|---|---|
| **AT-RISK FLIP (T1)** | `20_supply_daily`: PAB < safety_stock for future week (date_key) | INVESTIGATE: demand surge? supply miss? DECIDE: expedite PO, rebalance SS, push demand | `exception_case`: OPEN → ASSIGNED (to planner) → RESOLVED (after action) | P2: case disposition + evidence | Actual PO create/cancel |
| **DELAYED RECEIPT (T2b)** | `purchase_receipt_line`: receipt_creation_date - expected_receipt_date > threshold (41 days late) | INVESTIGATE supplier. DECIDE: accept delay (update forecast), source alternate, escalate to supply chain exec | `exception_case`: OPEN → ASSIGNED → RESOLVED; optionally create `action_request` for sourcing | P2: exception disposition | Actual supplier contract renegotiation |
| **PAST-DUE PO (T2c)** | `purchase_orders`: order_status='OPEN' AND promised_delivery_date_key < TODAY AND received_qty < ordered_qty (227 days late) | ESCALATE immediately: supplier communication failure. DECIDE: demand cancellation, rework, or supplier removal | `exception_case`: OPEN → ASSIGNED (urgent) → RESOLVED; create `action_request` escalation | P2: exception escalation + evidence | Actual PO cancellation in ERP |
| **SNAPSHOT CHANGE (T1)** | `20_supply_daily`: same (product, org, date_key) has PAB status flip across snapshots (was GREEN, now RED) | TREND ANALYSIS: identify root cause (demand forecast change, supply slip, lead time extension). DECIDE: expedite decision to-be-made | `event_draft`: IN PROGRESS → ACTIVE (if validated) → alert sent to control tower | P3: event validation + activate | Forecast change (ownership is demand planning) |
| **IMBALANCE (S6 in requirements)** | `20_supply_daily`: total_demand > total_supply for weeks N..N+12 (supply gap) | REBALANCE: recommend pulling forward a purchase_order or creating a planned_order | `event_draft`: IN PROGRESS → ACTIVE (if approved) → exported to output table | P3: event recommendation + activate/deactivate | Actual PO placement (D2C) |
| **SS BREACH (S5)** | `20_supply_daily`: projected_available_balance < safety_stock for any week (not just future) | INVESTIGATE: is this forecast-driven or execution-driven? DECIDE: increase SS (P-parameter), expedite supply | `exception_case`: OPEN → ASSIGNED → RESOLVED; optionally create recommendation | P2: exception flagging | Actual safety-stock parameter change in system |

### Key Definitions

- **Data Trigger**: The SELECT condition that surfaces the anomaly (read-only query on fact/dim tables).
- **Planner Decision**: The cognitive action a planner takes when they see the signal.
- **Lakebase State Transition**: The app state change that records the decision and tracks it to resolution (entity: `exception_case`, `event_draft`, `action_request`, `approval`).
- **In-Scope (P2/P3)**: The parts of the workflow we're building (disposition, activate/deactivate, recommendation).
- **Out-of-Scope**: System-to-system actions (PO create/cancel in Oracle Fusion, supplier communication via EDI).

---

## T4: PO LIFECYCLE EXAMPLE — "On-Time Path" vs "Past-Due Path"

### Hero Item's POs

#### SQL Query (READ-ONLY)

```sql
-- T4: Hero item (M18 XC5.0 BATTERY) POs with status and promised dates

SELECT 
  purchase_order_number,
  item_bigint_key,
  ordered_quantity,
  received_quantity,
  order_status,
  promised_delivery_date_key,
  (20260829 - promised_delivery_date_key) as days_relative_to_today
FROM prod_edw.fact.purchase_orders  -- READ-ONLY source
WHERE item_bigint_key = 3879620845706693458
ORDER BY purchase_order_number DESC
LIMIT 10
```

#### Printed Rows (Hero Item POs)

| PO Number | Ordered | Received | Status | Promised Date | Days vs Today |
|---|---|---|---|---|---|
| **280023845** | 1 | **0** | **OPEN** | 20260901 (Sep 1) | **-72 (future)** |
| **280023711** | 1 | **1** | **CLOSED FOR RECEIVING** | 20260831 (Aug 31) | **-2 (future)** |
| (earlier PO) | 1 | 1 | CLOSED FOR RECEIVING | 20250923 (Sep 23, 2025) | (past) |

### Lifecycle Narratives

#### Path A: ON-TIME (PO 280023711)

```
PO 280023711 (Hero Item M18 XC5.0 Battery):
  - Created: (order_creation_date not shown, but status exists)
  - Status Transition: PLANNED → OPEN (ordered) → CLOSED FOR RECEIVING (received)
  - Promised Delivery: 2026-08-31
  - Actual Receipt: 2026-08-31 (match: 0 days late, GREEN)
  - Ordered: 1 unit, Received: 1 unit (100% complete)
  Outcome: ✅ FULFILLED ON TIME. This PO did not trigger an exception.
```

#### Path B: FUTURE-DUE, NOT-YET-LATE (PO 280023845)

```
PO 280023845 (Hero Item M18 XC5.0 Battery):
  - Status Transition: PLANNED → OPEN (ordered)
  - Promised Delivery: 2026-09-01 (future from today 2026-08-29, -72 days away)
  - Current Receipt: 0 received, 1 ordered (0% received)
  - Status: OPEN (not yet promised, not yet late; 3 days until promise)
  Workflow Signal: ⚠️ WATCH. Not yet overdue. But if 2026-09-01 passes and receipt = 0,
    then PO becomes PAST-DUE (exception #12). At that moment, escalate.
```

#### Path C: PAST-DUE (Hypothetical, if PO 380057031 were Hero Item)

```
PO 380057031 (Different item, but illustrative):
  - Promised Delivery: 2026-06-02 (227 days ago from 2026-08-29)
  - Current Receipt: 0 received, 77 ordered (0% received)
  - Status: OPEN (still in procurement, not closed)
  Workflow Signal: 🔴 ESCALATE IMMEDIATELY. Past-due, undelivered, order still open.
    Action: supplier communication, demand cancellation, or sourcing rework.
```

### End-User Lens

✅ **Answers planner question: "How did this PO move through its lifecycle?"**
- On-time (280023711): proof the supply path works; no action needed.
- Future-due (280023845): monitor; will be past-due if Sep 1 comes with 0 receipt; trigger escalation logic.
- Past-due (380057031): exception is already active; escalate and resolve.

---

## Closing: STATE-TRANSITION Reference Table

| Transition | Data Signal | Status | Workflow Action | Lakebase Entity & State |
|---|---|---|---|---|
| **Snapshot PAB ≥ SS → PAB < SS** | `20_supply_daily`: (product, org, date_key, process_date) PAB drops below SS | **RED: At-Risk** | Investigate root; expedite PO, rebalance SS, push demand | `exception_case`: OPEN → ASSIGNED → RESOLVED |
| **Delayed Receipt** | `purchase_receipt_line`: receipt_creation_date - expected_receipt_date > 7 days | **RED: Late** | Investigate supplier; accept or source alternate | `exception_case`: OPEN → ASSIGNED → RESOLVED |
| **Past-Due PO** | `purchase_orders`: OPEN + promised_date < today + received_qty < ordered_qty | **RED: Overdue** | Escalate supplier; cancel or rework | `exception_case`: OPEN → ASSIGNED (urgent) → RESOLVED |
| **Supply > Demand (Imbalance)** | `20_supply_daily`: total_supply > total_demand for weeks N..N+12 | **YELLOW: Overstocked** | Recommend inventory reduction or demand pull-forward | `event_draft`: IN PROGRESS → ACTIVE (if approved) |
| **Demand > Supply (Imbalance)** | `20_supply_daily`: total_demand > total_supply for weeks N..N+12 | **RED: Understocked** | Recommend expedite or new PO | `event_draft`: IN PROGRESS → ACTIVE (if approved) |
| **SS Breach (Current)** | `20_supply_daily`: projected_available_balance < safety_stock (current or near-term week) | **RED: Immediate Risk** | Investigate execution; adjust SS; fast-track supply | `exception_case`: OPEN → ASSIGNED → RESOLVED |
| **Forecast Drift** | `20_supply_daily` snapshot N vs snapshot N-1: total_demand variance > threshold | **YELLOW: Watch** | Identify demand driver change; validate forecast; escalate if P1 customer | `event_draft`: IN PROGRESS → ACTIVE (if validated) |

---

## Gotchas & Open Questions

### Gotchas

1. **Negative days_overdue in hero item POs**: PO 280023845 promised 2026-09-01, but today's snapshot is 2026-08-29. The math (20260829 - 20260901 = -72) shows it's not YET overdue; the promise hasn't arrived yet. This is **not** a past-due signal, yet. A workflow must distinguish: promised_date < today (past-due, RED) vs promised_date >= today (future, monitor).

2. **NULL safety_stock in supply_daily**: Many rows have PAB populated but safety_stock = NULL. These rows cannot signal an at-risk breach (no threshold to compare). The workflow must filter: only rows where safety_stock IS NOT NULL are eligible for S5 (SS breach) exception.

3. **Ambiguous "expected_receipt_date" in receipts**: Some rows in purchase_receipt_line have expected_receipt_date = NULL. These are likely receipts against POs with no firm receipt date. The delay calculation (days_late) cannot be computed; these rows are excluded from T2 delay analysis.

4. **Order_status values are not normalized**: Some POs show "OPEN", others "CLOSED FOR RECEIVING", "CLOSED". The past-due logic must account for all non-terminal states (i.e., if status = "CLOSED" and received_qty < ordered_qty, it's a closed partial; not a past-due OPEN PO). The hero item PO 280023711 is both "CLOSED FOR RECEIVING" AND "OPEN" for the same item (multiple rows)—possible data artifact or multiple line items.

5. **Item_bigint_key = -1 in some POs**: A handful of POs (e.g., 380093978) have item_bigint_key = -1. This is a placeholder or unknown item. Workflows must handle gracefully (don't crash on null/unknown items; flag as data quality issue).

### Open Questions

1. **Lineage of "20 Global Supply Plan"**: Is this the only plan in 20_supply_daily, or are there others (e.g., "20 Demand Plan", regional overrides)? Do we need to segment by plan_name?

2. **Safety Stock Origin**: Is safety_stock a parameter from a configuration table, or is it computed? If parameter-driven, a planner might decide to *increase* SS in response to volatility. Where is the SS parameter stored / managed?

3. **Snapshot Cadence & Staleness**: Snapshots run daily (process_date from 20250628 to 20260829). Is this sufficient for exception detection? Or do we need intra-day updates for critical items?

4. **Future Forecast Drift**: T1 showed PAB declining steeply from Aug 15 to Aug 29 for a single week (41K → -3.4K, a drop of 44.6K in 14 days). What *caused* this? Was it a demand forecast spike, a supply cancellation, or a lead-time extension? The data_stories approach finds the SIGNAL (the flip) but does not drill into ROOT CAUSE (which forecast line changed). A follow-up analysis (demand_events, supply_events, lead_time_changes) is needed.

5. **Lakebase Integration**: This document describes the workflow state transitions (exception_case, event_draft, action_request) but does not query them, because they live in Lakebase (app state), not the warehouse (fact tables). A future story should wire the Lakebase entity reads into the workflow map to show: "Of the 150 past-due POs detected, how many have an exception_case opened? Assigned to whom? How many resolved in 24h?"

---

## Summary: Data Stories in Action

**What this document proves**: Time-series snapshots expose transitions that static dashboards hide. A planner armed with "T1 status-flips" data can act proactively: "Week 10/05 flipped to at-risk between Aug 15 and Aug 29 → expedite or rebalance NOW, not on Sep 1 when demand hits." A control tower that ingests past-due POs (T2c, 227-day delays) and routes them to escalation workflows (Lakebase exception_case entities) cuts MTTR (mean time to resolution) from weeks to hours.

**Core patterns traced**:
1. **T1**: Snapshot-to-snapshot PAB decline for fixed future week (on-track → at-risk).
2. **T2**: On-time, delayed, and past-due receipts (proof, signal, and escalation trigger).
3. **T3**: Workflow state map (trigger → decision → Lakebase entity state transition).
4. **T4**: PO lifecycle (planned → ordered → received on-time or past-due).
5. **Closing table**: State transitions as a reference (data signal → health → action → entity state).

**End-user value**: Planners and supply-chain controllers can now trace "why did this week move from green to red?" and "which POs are broken and need escalation?" without reading raw rows. The data stories become the lens through which they see supply-chain TIME and ACT on WORKFLOW.

---

**Data Source**: prod_edw.fact.20_supply_daily (READ-ONLY), prod_edw.fact.purchase_orders (READ-ONLY), prod_edw.fact.purchase_receipt_line (READ-ONLY)  
**Output Schema**: None (this is analysis only, no writes to sandbox_operations.po_management)  
**Date**: 2026-08-30 (as of process_date 20260829, the latest snapshot available)
