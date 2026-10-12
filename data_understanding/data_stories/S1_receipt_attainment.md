# S1 — RECEIPT ATTAINMENT DATA STORY
## Plan → Ordered → Actually Received (P1 Metric M1)

**Last Traced:** 2026-08-30  
**Hero Item:** item_bigint_key=3879620845706693458, item_id=48111850, "M18 XC5.0 BATTERY", ABC=A  
**Process Date:** 20260829 (snapshot from 2026-08-29)

---

## What This Story Proves

The receipt attainment story traces a single hero item (M18 XC5.0 BATTERY) from **planned supply expectations** through **purchase orders** to **actual receipts**. It answers the planner's core question:

> "What did we plan to receive, what did we actually order, and what arrived?"

By following this one item across three data hops (plan → POs → receipts), we establish:
1. The supply plan's expected receipt timeline (8-week forward buckets)
2. The actual purchase orders issued against this item
3. **The critical bridge mechanism** that connects purchase orders to receipt transactions
4. Receipt attainment: did ordered quantities arrive on-time and in-full?

---

## The Anchor

| Attribute | Value |
|-----------|-------|
| **item_bigint_key** | 3879620845706693458 |
| **item_id** | 48111850 |
| **Description** | M18 XC5.0 BATTERY |
| **ABC Class** | A (high-value) |
| **Plan Snapshot Date** | 20260829 (as-of 2026-08-29) |

---

## Hop-by-Hop Trace

### HOP 1: PLAN — Expected Receipts from Supply Planning

**SQL Query (READ-ONLY):**
```sql
SELECT 
  process_date, 
  date_key, 
  plan_name, 
  product_bigint_key, 
  purchase_orders,
  planned_orders
FROM prod_edw.fact.`20_supply_daily`
WHERE process_date = 20260829
  AND product_bigint_key = 3879620845706693458
  AND plan_name = '20 Global Supply Plan'
ORDER BY date_key;
```

**Observation:** The plan table (`prod_edw.fact.20_supply_daily`) contains columns `purchase_orders` and `planned_orders` but they are **all empty/NULL** for this hero item. This table appears to be structured to hold plan measures but for this item on this snapshot, no planned receipt data is populated.

**Data Found:**
- Plan dimension keys present: product_bigint_key=3879620845706693458 ✓
- Plan-level measures (purchase_orders, planned_orders): **EMPTY**
- Date buckets scanned: 20260824 and forward (all empty)

**End-User Lens:** ⚠️ **Does not answer a user question.** The plan table lacks populated measures for this item's expected supply. We cannot see what the 8-week forward plan expected in terms of purchase orders or planned inventory receipts. This is a **potential data gap**: either the plan was not loaded for this item, or the plan measures for supply are stored elsewhere (e.g., in a separate demand/supply plan table).

**Implication for M1 (Receipt Attainment):** Without the "what we planned," we cannot directly compare plan-vs-actual. We can, however, trace ordered-vs-received from the purchase orders and receipt ledger (hops 2 & 3).

---

### HOP 2: ORDERED — Purchase Orders for the Hero Item

**SQL Query (READ-ONLY):**
```sql
SELECT 
  purchase_order_number, 
  purchase_order_line_number, 
  ordered_quantity, 
  received_quantity, 
  order_status, 
  line_status,
  requested_delivery_date_key, 
  promised_delivery_date_key
FROM prod_edw.fact.purchase_orders
WHERE item_bigint_key = 3879620845706693458
  AND purchase_order_number IN ('480002236', '280023711', '280023712', '280023845')
ORDER BY purchase_order_number, purchase_order_line_number;
```

**Printed Rows** (Recent OPEN and Closed POs):

| PO # | Line | Ordered Qty | Received Qty | Order Status | Line Status | Promised Delivery |
|------|------|-------------|--------------|--------------|-------------|-------------------|
| 280023711 | 1 | 1.0 | 1.0 | CLOSED FOR RECEIVING | CLOSED FOR RECEIVING | 20260831 |
| 280023711 | 1 | 1.0 | 0.0 | OPEN | OPEN | 20260831 |
| 280023712 | 2 | 1.0 | 1.0 | OPEN | CLOSED FOR RECEIVING | 20260831 |
| 280023712 | 2 | 1.0 | 0.0 | OPEN | OPEN | 20260831 |
| 280023845 | 8 | 1.0 | 0.0 | OPEN | OPEN | 20260901 |
| **480002236** | **1** | **2176.0** | **0.0** | **OPEN** | **OPEN** | **20261005** |
| **480002236** | **1** | **2560.0** | **0.0** | **OPEN** | **OPEN** | **20261005** |

**Narrative:** The M18 battery is on several active orders. The **flagship open PO 480002236 for 2176 units** promises delivery on 10/05/2026 (37 days out). There are also older test/sample POs (280023711, 280023712) for 1 unit each that arrived on 20260831 and 20260828 respectively. PO 280023845 for 1 unit has 20260901 promised.

**End-User Lens:** ✅ **Answers a planner question: "What are we ordered for the M18 battery?"** The planner sees:
- Large production order: 2176 units promised 2026-10-05 (OPEN, not yet received)
- Smaller orders already received (1 unit each on 8/28 and 8/29)
- Total on-order: ~2560 units spread across multiple POs
- Key risk: 2176-unit order is still OPEN with no receipts yet, ~37 days to promised delivery

---

### HOP 3: THE BRIDGE — Joining Purchase Orders to Receipts

**THE CRITICAL FINDING:** The receipt data lives in `prod_edw.fact.purchase_receipt_line`, not in a raw transaction table. This table **bridges** the purchase order to its received items.

**Bridge Mechanism:**

```
purchase_orders.purchase_order_number (STRING)
         ↓ (FK match)
purchase_receipt_line.purchase_order_number (STRING)
         ↓
purchase_receipt_line.purchase_order_line_number (INT)
         ↓ (FK match)
purchase_orders.purchase_order_line_number (INT)
```

**Key Columns in Bridge:**
- `purchase_receipt_line.purchase_order_number` — matches `purchase_orders.purchase_order_number`
- `purchase_receipt_line.purchase_order_line_number` — matches `purchase_orders.purchase_order_line_number`
- `purchase_receipt_line.item_bigint_key` — tells us which item was received

**Bridge Validation:**  
✅ **The bridge WORKS.** Both tables carry the full purchase order number and line number as textual/numeric keys. No ambiguous numeric IDs or Oracle-raw header lookups needed. The join is direct.

**Example Join Logic (Pseudo-SQL):**
```sql
SELECT 
  po.purchase_order_number,
  po.purchase_order_line_number,
  po.ordered_quantity,
  pr.received_quantity,
  pr.receipt_creation_date
FROM prod_edw.fact.purchase_orders po
JOIN prod_edw.fact.purchase_receipt_line pr
  ON po.purchase_order_number = pr.purchase_order_number
  AND po.purchase_order_line_number = pr.purchase_order_line_number
WHERE po.item_bigint_key = 3879620845706693458;
```

---

### HOP 4: ATTAINMENT — Receipt Ledger for Hero Item's POs

**SQL Query (READ-ONLY):**
```sql
SELECT 
  purchase_order_number, 
  purchase_order_line_number, 
  shipped_quantity, 
  received_quantity, 
  accepted_quantity, 
  rejected_quantity,
  receipt_line_status_code, 
  receipt_creation_date, 
  expected_receipt_date
FROM prod_edw.fact.purchase_receipt_line
WHERE item_bigint_key = 3879620845706693458
  AND purchase_order_number IN ('280023711', '280023712', '280023845', '480002236')
ORDER BY purchase_order_number, receipt_creation_date;
```

**Printed Rows** (Actual Receipts):

| PO # | Line | Shipped | Received | Accepted | Rejected | Status | Receipt Date | Expected Date |
|------|------|---------|----------|----------|----------|--------|--------------|---------------|
| 280023711 | 1 | 1.0 | 1.0 | 0.0 | 0.0 | FULLY RECEIVED | 2026-08-29 03:53:00 | 2026-08-29 03:52:55 |
| 280023712 | 2 | 1.0 | 1.0 | 0.0 | 0.0 | FULLY RECEIVED | 2026-08-28 20:54:46 | 2026-08-28 20:54:45 |

**Narrative:** For the hero item (M18 XC5.0 BATTERY), **two small orders have been fully received and closed**:

- **PO 280023711, Line 1:** 1 unit ordered, 1 unit received on 2026-08-29 03:53 (on-time, 5 seconds after expected)
- **PO 280023712, Line 2:** 1 unit ordered, 1 unit received on 2026-08-28 20:54 (on-time, 1 second after expected)

**The large PO 480002236 (2176 units promised 2026-10-05) has NO receipts yet.** It is still OPEN as of the 2026-08-29 snapshot. The expected delivery is 37 days in the future.

**End-User Lens:** ✅ **Answers a planner question: "What M18 batteries actually arrived?"** The planner sees:
- Small orders **arrived on-time and in-full** (2 units total)
- Large production order **has not started receiving** yet (still 37 days out)
- Attainment rate to date: 2 out of ~2560 ordered units (0.08%) — but only because the large PO is not yet due
- Risk: No data anomalies for received receipts (all were full, on-time). System is clean for what has been received.

---

## The Bridge Finding (Critical)

### Bridge Status: ✅ WORKING

**How Purchase Orders Link to Receipt Transactions:**

The join is **via business keys** (purchase order number and line number), not via obscure numeric IDs:

| From Table | From Columns | To Table | To Columns | Match |
|------------|--------------|----------|------------|-------|
| `prod_edw.fact.purchase_orders` | `purchase_order_number` (STRING), `purchase_order_line_number` (INT) | `prod_edw.fact.purchase_receipt_line` | `purchase_order_number` (STRING), `purchase_order_line_number` (INT) | ✅ Direct, no ambiguity |

**Why This Matters:**
- **No need to hunt for raw Oracle numeric IDs** (po_header_id, po_line_id) — they aren't exposed in the EDW dim/fact tables.
- **No lookup table required** — the business key itself is the bridge.
- **The bridge is 1:M** — one PO line can have multiple receipt lines (partial receipts, multiple deliveries). In our case, each PO line has one receipt line (full receipt).
- **Item tracking:** Both tables carry `item_bigint_key`, so the received item can be confirmed.

**Verified with Real Data:**
- ✅ PO 280023711 line 1 → Receipt line 1 (shipped 1, received 1)
- ✅ PO 280023712 line 2 → Receipt line 2 (shipped 1, received 1)

---

## Attainment Result with Real Numbers

### For PO 280023711 (Small test order, completed)
| Measure | Value | Status |
|---------|-------|--------|
| **Ordered** | 1 unit | Baseline |
| **Received** | 1 unit | 100% attainment |
| **On-Time?** | Yes (5 sec early) | ✅ On-time |
| **Full?** | Yes (no shortage) | ✅ Full |
| **Attainment Grade** | **A** (full & on-time) | ✅ Perfect |

### For PO 280023712 (Small test order, completed)
| Measure | Value | Status |
|---------|-------|--------|
| **Ordered** | 1 unit | Baseline |
| **Received** | 1 unit | 100% attainment |
| **On-Time?** | Yes (1 sec early) | ✅ On-time |
| **Full?** | Yes (no shortage) | ✅ Full |
| **Attainment Grade** | **A** (full & on-time) | ✅ Perfect |

### For PO 480002236 (Large production order, in-flight)
| Measure | Value | Status |
|---------|-------|--------|
| **Ordered** | 2176 units (Line 1) + 2560 units (Line 1 duplicate?) | Baseline |
| **Received to Date** | 0 units | Not yet due |
| **On-Time?** | Pending (promised 2026-10-05, 37 days out) | ⏳ In-flight |
| **Full?** | Pending | ⏳ In-flight |
| **Attainment Grade** | **PENDING** | ⏳ Awaiting delivery |

### Summary Attainment Metrics
| Metric | Value |
|--------|-------|
| **Total Units Ordered** | ~4736 units (2 x 1 unit + 2176/2560 on flagship PO) |
| **Total Units Received** | 2 units |
| **Received Attainment %** | 0.04% (early receipts only) |
| **On-Time %** | 100% (what has arrived) |
| **In-Full %** | 100% (no partial receipts yet) |
| **Grade for Completed Orders** | ✅ **A** (perfect on-time, full delivery for small orders) |
| **Grade for In-Flight Orders** | ⏳ **PENDING** (large 2176-unit order awaiting 2026-10-05 delivery) |

---

## Gotchas & Data Quality Notes

### Gotcha 1: Duplicate Rows in Purchase_Orders
The PO table query returned **duplicate rows** for the same PO line (e.g., PO 480002236 line 1 appears twice with ordered_quantity of 2176 and 2560 respectively). This suggests:
- Either the table has a **slowly-changing dimension (SCD) history** and both versions are valid-to = 99991231 (future)
- Or there is **data duplication** in the fact table

**Impact:** When joining to receipt_line, ensure you filter by `valid_to` or use the **latest** row (compare `load_date` or `valid_from`).

### Gotcha 2: Plan Measures Missing for Hero Item
The `prod_edw.fact.20_supply_daily` table has no populated `purchase_orders` or `planned_orders` measures for this item on snapshot date 20260829. 
- This may be **expected** if the plan is computed at a coarser grain (e.g., site-level, not item-level) and must be **joined to item via hierarchies**.
- Or the **supply plan extraction** is from a different table (e.g., a separate plan-fact table not queried here).

**Impact:** M1 "Receipt Attainment" requires both planned and actual; without plan data, we can only compute **"Ordered vs. Received"** (a subset of M1).

### Gotcha 3: Receipt_Creation_Date vs. Expected_Receipt_Date
- **expected_receipt_date:** When the receipt was expected to arrive (from PO promised_delivery_date_key)
- **receipt_creation_date:** When the receipt transaction was created in the system (timestamp of actual receipt event)

For the two completed POs, the receipt was created **seconds after** expected (1–5 seconds). This is likely a **real-time sync** between Oracle and the EDW load. In a real supply chain, look for larger deltas here as a sign of late delivery.

### Gotcha 4: Accepted_Quantity is Zero
All receipt rows show `accepted_quantity = 0.0` even though `received_quantity = 1.0`. This suggests:
- The **inspection/acceptance step** is not yet complete, or
- The table captures **receipt but not acceptance**, which may be in a separate inspection/QC table

**Impact:** For a **received vs. accepted** comparison, we would need to join to an inspection ledger. For "receipt attainment," we use received_quantity as the ground truth.

### Gotcha 5: Order_Status vs. Line_Status Mismatch
In purchase_orders, some rows show:
- order_status = "OPEN" but line_status = "CLOSED FOR RECEIVING"

This indicates the **order header is still open** (other lines may be pending) but **this specific line is closed** (all expected receipts received). Use **line_status** for per-item attainment tracking.

---

## Open Questions

1. **Plan data gap:** Where are the supply-plan expected receipts for the M18 battery? Are they in `prod_edw.fact.20_supply_daily` under different dimensions, or in a separate plan-fact table?

2. **Duplicate PO rows:** Why does PO 480002236 line 1 appear twice in purchase_orders with different ordered_quantity values (2176 vs. 2560)? Is this SCD versioning or a data anomaly?

3. **Large PO split:** Are the 2176 and 2560 units on PO 480002236 line 1 **two shipment schedules** (split delivery) or **duplicate entries**? Expected behavior depends on whether the PO has `purchase_order_schedule_number` differentiators.

4. **Inspection table:** Is there a separate QC/inspection fact table that populates `accepted_quantity`? If so, the **true attainment** may hinge on acceptance, not just receipt.

5. **Plan-vs.-Actual comparison:** For M1 (Receipt Attainment), should we compare:
   - Ordered → Received (what we traced today), or
   - Planned → Received (requires joining plan fact to supply)?
   
   Recommendation: Define the "plan" grain (site? warehouse? item?) before computing the metric.

---

## Summary: The Story

> **On 2026-08-29, the supply plan snapshot showed no populated expectations for the M18 XC5.0 battery's planned receipts.** However, the purchase order ledger revealed a clear intent: we have issued 4 POs for this item, with a flagship 2176-unit order (PO 480002236) promised for 2026-10-05.
>
> **As of 2026-08-28/29, only 2 units have been received** (from test orders PO 280023711 and PO 280023712), both arriving **on-time and in-full**. The large production order is still in-flight, 37 days from promised delivery, with **zero receipts to date**.
>
> **The bridge from purchase orders to receipts is clean and direct:** matching on `purchase_order_number` and `purchase_order_line_number` in the receipt line table. No complex Oracle numeric ID lookups required.
>
> **M1 Attainment Grade (for completed orders):** ✅ **A** (100% on-time, 100% in-full). **M1 for in-flight orders:** ⏳ **PENDING** (awaiting 2026-10-05).

---

## File Metadata

- **Story Type:** Dimensional trace (anchor ID → plan → orders → receipts)
- **Scope:** One hero item (3879620845706693458, M18 XC5.0 BATTERY)
- **Tables Queried:** 
  - `prod_edw.fact.20_supply_daily` (plan snapshot, READ-ONLY)
  - `prod_edw.fact.purchase_orders` (orders, READ-ONLY)
  - `prod_edw.fact.purchase_receipt_line` (receipts, READ-ONLY)
- **No writes performed.** All queries are SELECT only.
- **Bridge verified:** ✅ `purchase_orders` ↔ `purchase_receipt_line` via (purchase_order_number, purchase_order_line_number)
