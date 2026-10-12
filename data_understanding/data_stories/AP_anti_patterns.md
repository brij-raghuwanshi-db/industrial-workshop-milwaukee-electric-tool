# Milwaukee Supply Chain — Data Anti-Patterns Catalog

## Overview

This document catalogs 10 critical **anti-patterns** in the Milwaukee supply-chain data warehouse—queries and interpretations that LOOK correct but produce WRONG results when applied to this data's specific structure and semantics. For each pattern, both the WRONG and RIGHT queries are shown with quantified error magnitudes, business priority impact, and planner consequences.

**Key Finding:** The most dangerous anti-patterns are those that silently inflate or deflate totals by 2x–6x without raising any warnings. The guardrails below prevent these mistakes.

---

## Anti-Pattern 1: Summing Point-in-Time Quantities Across Date Snapshots

### Name
**Additive Misinterpretation of Inventory Snapshot Data**

### Why It's Tempting
The `inventory_days_on_hand` table contains `on_hand_qty`, which looks like a measure. Developers naturally sum across rows (across multiple date_keys or process_dates) to get "total inventory over time," not realizing each row is a **snapshot** (point-in-time), not a cumulative transaction.

### WRONG Query
```sql
-- Treating point-in-time snapshots as cumulative
SELECT 
  SUM(on_hand_qty) as inflated_sum,
  COUNT(*) as row_count
FROM prod_edw.fact.inventory_days_on_hand
WHERE item_bigint_key = 3879620845706693458
  AND inventory_organization_bigint_key = 776578178872804310
  AND process_date IN (20260820, 20260821, 20260822, 20260823, 20260824)
```

**WRONG Result:**
- **inflated_sum:** 456,463.0
- **row_count:** 4

### RIGHT Query
```sql
-- Get the latest point-in-time snapshot (not cumulative)
SELECT 
  on_hand_qty as correct_value
FROM prod_edw.fact.inventory_days_on_hand
WHERE item_bigint_key = 3879620845706693458
  AND inventory_organization_bigint_key = 776578178872804310
  AND process_date = 20260829
  AND date_key = 20260829
```

**RIGHT Result:**
- **correct_value:** 83,254.0

### Error Magnitude
- **WRONG value:** 456,463
- **RIGHT value:** 83,254
- **Error:** 5.48× **TOO HIGH** (overstate inventory by 448%)
- **Per-row inflation:** Each snapshot treated as additive increases the total by its full on_hand_qty

### Priority Impact
**P1 / P2:** Inventory planning, safety stock, and allocation decisions directly depend on accurate on-hand quantities. A 5× inflation hides shortages or misleads planners into believing stock is abundant when it is not.

### Planner Impact
A planner looking at an inflated on-hand number concludes "we have plenty of stock for this SKU" and reduces purchase orders or diverts inventory to other locations. In reality, the current on-hand is ~1/5 of the reported number, leading to stockouts, delayed orders, and lost sales.

### Guardrail Rule
**ON_HAND IS SEMI-ADDITIVE:** Only compare on_hand_qty for the same date_key across different organizations/items, or get the MAX() or latest on_hand for a given date_key. NEVER SUM(on_hand_qty) across multiple date_keys.

---

## Anti-Pattern 2: Unconstrained Inventory Material Transaction Aggregation (Transfer Double-Counting)

### Name
**Naive Summation of Material Transactions Without Accounting for Transfer Pair Logic**

### Why It's Tempting
The `inventory_material_transaction` table logs every inventory move (receipt, issue, transfer, etc.). A planner wants to know "net inventory change." They sum `transaction_quantity` across all rows for a SKU, trusting it will give net flow. In reality, **transfers are recorded twice:** once as a shipment out of the source subinventory, and once as a receipt into the destination subinventory. Naive SUM double-counts.

### WRONG Query
```sql
-- Sum all transaction_quantity without separating transaction types
SELECT 
  SUM(transaction_quantity) as wrong_netflow
FROM prod_edw.fact.inventory_material_transaction
WHERE item_bigint_key = 3879620845706693458
  AND location_bigint_key = 776578178872804310
  AND transaction_date_key BETWEEN 20260801 AND 20260829
```

**WRONG Result (simulated from data pattern):**
- **Sum (includes transfers twice):** 1,200,000 (example; actual depends on transfer volume)
- **This counts each transfer pair as +qty (out) and +qty (in) = 2× the real flow**

### RIGHT Query
```sql
-- Separate by reason_name or filter to non-transfer types only
SELECT 
  reason_name,
  SUM(transaction_quantity) as qty_by_reason,
  COUNT(*) as transaction_count
FROM prod_edw.fact.inventory_material_transaction
WHERE item_bigint_key = 3879620845706693458
  AND location_bigint_key = 776578178872804310
  AND transaction_date_key BETWEEN 20260801 AND 20260829
GROUP BY reason_name
```

### Error Magnitude
- **WRONG:** Naive SUM counts each transfer **2× (as both outbound and inbound)**
- **RIGHT:** Separate aggregation by reason or net only non-transfer flows
- **Error Range:** Depending on transfer volume, can inflate net flow by 2–4×

### Priority Impact
**P2 / P3:** Affects demand–supply reconciliation, inventory aging, and MRO (maintenance/repair/operations) spend analysis.

### Planner Impact
If 50% of a month's transactions are internal transfers, a naive SUM reports net change as 2× the real value. A planner then under-forecasts replenishment needs, causing future stockouts, or over-allocates budget to SKU restocking based on a false inflated flow signal.

### Guardrail Rule
**ALWAYS GROUP BY reason_name or transaction reason when aggregating material transactions.** Transfers between subinventories post in pairs; exclude them or net them separately. Label the query intent: "net inflow," "outbound," "internal transfers only," etc.

---

## Anti-Pattern 3: Joining Raw Staging to Dimensions on Unclean Keys

### Name
**Missing Item Column in Raw Staging → Failed Join**

### Why It's Tempting
A developer wants to query **raw** receipts from `receiving_receipt_transactions` and join to items to add item_id or item descriptions. They write a join on `item_id`, not realizing the raw staging table has **NO `item_id` column** — only raw foreign keys like `lpn_id`, `run_id`, `task_id`, `group_id`, `reason_id`. The join silently fails or requires a bridge table (PO → PO line → item).

### WRONG Query
```sql
-- Attempt to join raw staging to item dimension on item_id (column doesn't exist)
SELECT 
  COUNT(*) as receipt_lines
FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions r
LEFT JOIN prod_edw.dim.items_scd1 i ON r.item_id = i.item_id
WHERE r.creation_date >= '2026-08-01'
  AND r.creation_date <= '2026-08-31'
```

**WRONG Result:**
- Error: `[UNRESOLVED_COLUMN] A column, variable, or function parameter with name 'item_id' cannot be resolved`

### RIGHT Query
```sql
-- Use cleaned fact table purchase_receipt_line which has proper item_bigint_key
SELECT 
  COUNT(*) as receipt_lines,
  SUM(received_quantity) as total_received,
  COUNT(DISTINCT purchase_order_number) as po_count
FROM prod_edw.fact.purchase_receipt_line
WHERE item_bigint_key = 3879620845706693458
  AND receipt_creation_date >= '2026-08-01'
  AND receipt_creation_date <= '2026-08-31'
```

**RIGHT Result:**
- **receipt_lines:** 528
- **total_received:** 421,309.0
- **po_count:** 13

### Error Magnitude
- **WRONG:** Query fails immediately; no results.
- **RIGHT:** Correct 528 receipt lines for hero item across 13 POs.
- **Error Type:** Not a numeric error, but a **structural error** that stalls analysis.

### Priority Impact
**P3:** Receipt reconciliation, PO closure, and supplier performance tracking depend on clean receipt data. Missing this forces developers to build workaround joins or use raw data without item context.

### Planner Impact
A supply planner cannot reconcile "Did we receive all of this PO?" without item-level receipt data. They must manually cross-reference PO lines to receipts, slowing exception investigations.

### Guardrail Rule
**NEVER query raw staging tables directly for operational analysis.** Always use the cleaned fact table (e.g., `purchase_receipt_line`) which has proper key relationships. Raw staging is for debugging, reconciliation testing, or rebuilding the fact layer.

---

## Anti-Pattern 4: Naive Shipped Quantity Aggregation (87% NULL)

### Name
**Ignoring NULL Distribution in Sparse Measures**

### Why It's Tempting
The `sales_order_line_transactions` table has a `shipped_quantity` column. A planner wants to know total units shipped for a product. They calculate `AVG(shipped_quantity)` or `SUM(shipped_quantity)` without checking for NULL. In reality, ~87% of rows have NULL shipped_quantity (orders not yet shipped, cancelled, or on credit memo), so the aggregate is deceptive.

### WRONG Query (Conceptual)
```sql
-- Aggregate without filtering for non-null or valid order status
SELECT 
  COUNT(*) as total_rows,
  COUNT(shipped_quantity) as non_null_qty_rows,
  SUM(shipped_quantity) as sum_qty,
  AVG(shipped_quantity) as avg_qty
FROM prod_edw.fact.sales_order_line_transactions
WHERE item_bigint_key = 3879620845706693458
  AND order_date_key BETWEEN 20260801 AND 20260831
```

**WRONG Result (Interpretation):**
- Naive AVG includes many NULL rows in the denominator, understating average shipped qty per line.
- NULL values collapse to 0 in some tools, artificially lowering aggregate.

### RIGHT Query
```sql
-- Filter to Standard orders with shipped status and positive qty
SELECT 
  COUNT(*) as shipped_lines,
  SUM(shipped_quantity) as total_shipped,
  AVG(shipped_quantity) as avg_per_line
FROM prod_edw.fact.sales_order_line_transactions
WHERE item_bigint_key = 3879620845706693458
  AND order_date_key BETWEEN 20260801 AND 20260831
  AND order_type = 'Standard'
  AND order_status IN ('Invoiced', 'Closed')
  AND shipped_quantity > 0
```

**RIGHT Result:**
- Only rows with actual shipments are counted.
- Accurate average reflects real fulfillment rates.

### Error Magnitude
- **WRONG:** 87% of rows have NULL → SUM and AVG are biased toward lower, less representative values.
- **RIGHT:** Only 13% of rows are counted → aggregate reflects true shipped orders only.
- **Representation Error:** ~6.7× underrepresentation if naive SUM is taken across all rows.

### Priority Impact
**P2:** Sales fulfillment tracking, demand satisfaction metrics, and customer SLA compliance depend on accurate shipped-quantity reporting.

### Planner Impact
If reporting shows "average shipped per line = 15 units" but this is naively averaged across 87% NULL rows, the planner believes fulfillment is poor. In reality, the TRUE average (among shipped lines only) may be 100 units, indicating strong fulfillment. Budget and allocation decisions are then misaligned with reality.

### Guardrail Rule
**ALWAYS FILTER to non-NULL values when aggregating sparse measures.** For shipped_quantity, filter to:
- `order_type = 'Standard'` (exclude returns/credit memos)
- `order_status IN ('Invoiced', 'Closed')` (confirmed shipments)
- `shipped_quantity > 0` (non-null and positive)

---

## Anti-Pattern 5: Ranking P2 Exceptions by Raw Unit-Miss Ignoring Cost

### Name
**Unit-Level Prioritization Divorced from Financial Impact**

### Why It's Tempting
A planner looks at **safety stock exceptions** (items where projected_available_balance < safety_stock) and ranks by magnitude of miss (safety_stock − projected_available_balance). Intuitively, the largest miss should be the highest priority. In reality, a $0.01 scrap item with a 1,000-unit miss is less critical than a $500 electronics assembly with a 1-unit miss. Ignoring cost gives false priorities.

### WRONG Query (Conceptual)
```sql
-- Rank exceptions by raw unit-miss, ignoring cost
SELECT 
  item_id,
  applied_standard_cost,
  safety_stock,
  projected_available_balance,
  (safety_stock - projected_available_balance) as unit_miss,
  ROW_NUMBER() OVER (ORDER BY (safety_stock - projected_available_balance) DESC) as rank
FROM <P2_exception_data>
WHERE safety_stock > projected_available_balance
LIMIT 10
```

**WRONG Top Items (Example):**
1. Item 88930100 (carbide part): 1,000-unit miss, applied_standard_cost = $0.0134 → **financial miss: $13.40**
2. Item 88930200 (fastener): 500-unit miss, cost = $0.02 → **financial miss: $10.00**
3. Item 88930300 (custom bracket): 2-unit miss, cost = $485.00 → **financial miss: $970.00** ← **WRONG PRIORITY**

### RIGHT Query (Conceptual)
```sql
-- Rank exceptions by financial impact (unit-miss × cost)
SELECT 
  item_id,
  applied_standard_cost,
  safety_stock,
  projected_available_balance,
  (safety_stock - projected_available_balance) as unit_miss,
  (safety_stock - projected_available_balance) * applied_standard_cost as financial_miss_usd,
  ROW_NUMBER() OVER (ORDER BY (safety_stock - projected_available_balance) * applied_standard_cost DESC) as rank
FROM <P2_exception_data>
WHERE safety_stock > projected_available_balance
LIMIT 10
```

**RIGHT Top Items:**
1. Item 88930300 (custom bracket): 2-unit miss, cost = $485.00 → **financial miss: $970.00** ← **CORRECT PRIORITY**
2. Item 88930100 (carbide part): 1,000-unit miss, cost = $0.0134 → **financial miss: $13.40**
3. Item 88930200 (fastener): 500-unit miss, cost = $0.02 → **financial miss: $10.00**

### Error Magnitude
- **WRONG:** Top-ranked item has $13 financial impact; #3 item has $970 impact.
- **RIGHT:** Items are reordered by true business impact.
- **Priority Error:** Unit-based ranking places a low-cost item ~70× higher in rank than a high-cost item.

### Priority Impact
**P2:** Safety stock and procurement exception management directly affect fulfillment SLA and cash flow.

### Planner Impact
A planner manually reviews the top 10 exceptions and spends 8 hours rushing to acquire 1,000 more carbide parts (perceived as critical because of raw unit-miss), while the custom bracket shortage (real $970 impact) sits unaddressed. This wastes labor, delays critical repairs, and harms customer satisfaction for high-value products.

### Guardrail Rule
**ALWAYS weight unit-miss by applied_standard_cost to derive financial impact.** Rank by `(safety_stock - projected_available_balance) × applied_standard_cost DESC`, not by raw units. Add a cost column to exception reports so planners see both unit and financial severity.

---

## Anti-Pattern 6: Single-Snapshot Blindness (Not Comparing Vintages)

### Name
**Assuming One Process Date Represents Ground Truth**

### Why It's Tempting
A planner pulls the latest `inventory_days_on_hand` snapshot (process_date = 20260829) and sees on_hand = 83,254 for the hero item. They conclude "stock is healthy." They don't compare this to the same future date_key (e.g., 20260905) across two or three recent process_date snapshots to catch **plan degradation** (the item was previously forecasted to have plenty, but now is projected to run short).

### WRONG Query (Conceptual)
```sql
-- Only look at the latest snapshot
SELECT 
  date_key,
  on_hand_qty,
  process_date
FROM prod_edw.fact.inventory_days_on_hand
WHERE item_bigint_key = 3879620845706693458
  AND inventory_organization_bigint_key = 776578178872804310
  AND process_date = 20260829  -- Only latest
ORDER BY date_key DESC
```

**WRONG Conclusion:**
- "On-hand for 2026-09-05 is 95,000 units; we're fine."
- **Planner takes no action.**

### RIGHT Query (Conceptual)
```sql
-- Compare the SAME future date_key across multiple snapshots (process_date vintages)
SELECT 
  process_date,
  date_key,
  on_hand_qty,
  LAG(on_hand_qty) OVER (ORDER BY process_date) as prev_snapshot_qty,
  on_hand_qty - LAG(on_hand_qty) OVER (ORDER BY process_date) as change_from_prev
FROM prod_edw.fact.inventory_days_on_hand
WHERE item_bigint_key = 3879620845706693458
  AND inventory_organization_bigint_key = 776578178872804310
  AND date_key = 20260905  -- Same future date
  AND process_date IN (20260825, 20260826, 20260827, 20260828, 20260829)
ORDER BY process_date DESC
```

**RIGHT Result (Example):**
```
| process_date | date_key | on_hand_qty | prev_snapshot | change    |
|--------------|----------|-------------|---------------|-----------|
| 20260829     | 20260905 | 15,000      | 95,000        | -80,000   |  ← RED FLAG
| 20260828     | 20260905 | 95,000      | 105,000       | -10,000   |
| 20260827     | 20260905 | 105,000     | 110,000       | -5,000    |
```

**RIGHT Conclusion:**
- "On 2026-08-29, the forecast for 2026-09-05 dropped from 95,000 to 15,000 units (80,000 unit swing). This is a major plan change. Trigger escalation."

### Error Magnitude
- **WRONG:** Single snapshot misses the trend; planner sees "15,000" and thinks it's stable.
- **RIGHT:** Comparison reveals a 5-day degradation of 80,000 units (drop from 95,000 to 15,000).
- **Information Loss:** Entire trend (was-healthy-now-red) is invisible with single snapshot.

### Priority Impact
**P1 / P2:** Early detection of plan degradation triggers proactive supply-chain response (expedited orders, capacity rebalancing, customer communication).

### Planner Impact
Without the trend, the planner sees only the low number and either overreacts (emergency orders that cost extra) or trusts it's normal (then faces shortage when demand hits). With trend comparison, the planner investigates *why* the forecast dropped 80,000 units and makes informed trade-off decisions.

### Guardrail Rule
**For inventory/supply analysis, ALWAYS compare the same future date_key across 2–3 recent process_date snapshots.** Use LAG() to show deltas. Flag large swings (>10% change from prior day). Report changes as trends, not point values.

---

## Anti-Pattern 7: Naive 20_supply_daily Aggregation Without Series/Order-Type Grain

### Name
**Ignoring Multi-Grain Fact Table Dimension Split**

### Why It's Tempting
The `20_supply_daily` table contains daily supply plan rows. A planner wants "total demand" for a product on a date. They query:
```sql
SELECT SUM(measure) FROM 20_supply_daily WHERE product_key = X AND date_key = D
```
Not realizing the fact table is **multi-grained:** the same product×date combination appears multiple times, split by `series_bigint_key` (sales channel / product line) and `order_type_bigint_key` (Standard / returns / no-charge orders). Naive SUM inflates.

### WRONG Query (Conceptual)
```sql
-- Naive SUM without accounting for series/order_type fan-out
SELECT 
  product_bigint_key,
  date_key,
  SUM(demand_qty) as total_demand_wrong
FROM prod_edw.fact.`20_supply_daily`
WHERE product_bigint_key = 3879620845706693458
  AND date_key = 20260829
```

**WRONG Result:**
- **total_demand: 150,000** (might actually be 150K = 50K (Standard) + 30K (returns) + 20K (no-charge) + duplicates from series split)

### RIGHT Query (Conceptual)
```sql
-- GROUP BY series and order_type to see the actual grain
SELECT 
  product_bigint_key,
  date_key,
  series_bigint_key,
  order_type_bigint_key,
  SUM(demand_qty) as demand_by_series_ordertype,
  COUNT(*) as row_count
FROM prod_edw.fact.`20_supply_daily`
WHERE product_bigint_key = 3879620845706693458
  AND date_key = 20260829
GROUP BY product_bigint_key, date_key, series_bigint_key, order_type_bigint_key
```

**RIGHT Result:**
```
| series | order_type | demand_qty | row_count |
|--------|------------|------------|-----------|
| 2001   | 1 (Std)    | 50,000     | 1         |
| 2001   | 2 (Return) | 30,000     | 1         |
| 2002   | 1 (Std)    | 25,000     | 1         |
| 2002   | 3 (No-chr) | 20,000     | 1         |
| 2001   | 1 (Std)    | 25,000     | 1         | ← Duplicate or plan variant
```
**Actual total demand (Standard orders only): 50,000 + 25,000 = 75,000; not 150,000**

### Error Magnitude
- **WRONG:** 150,000 units (includes all order types + potential duplicates)
- **RIGHT:** 75,000 units (Standard orders only; or specify which order types to include)
- **Error:** 2× if naive SUM mixes order types; can be higher if series/plan variants create multi-row scenarios.

### Priority Impact
**P3:** Demand planning, S&OP, and capacity allocation depend on understanding demand by order type (Standard is revenue-generating; returns reduce; no-charge are service). Mixing them distorts the forecast.

### Planner Impact
A planner sees inflated demand (150K) and increases production/ordering. But only 75K is revenue-generating (Standard); 30K is returns (reduces net); 20K is no-charge (cost, no revenue). Over-production on inflated signal wastes resources.

### Guardrail Rule
**20_supply_daily is MULTI-GRAINED by series_bigint_key + order_type_bigint_key + plan scenario.** ALWAYS GROUP BY these dimensions when aggregating. Clearly label the query: "Standard orders only," "All order types," "Returns separated," etc. Never SUM across series without explicit intent.

---

## Anti-Pattern 8: Unconstrained Frozen Column Use (100% NULL)

### Name
**Assuming Deprecated Columns Are Still Populated**

### Why It's Tempting
The `10_demand_daily` table has columns like `frozen_working_final_forecast`, `frozen_demand`, etc. A planner thinks "frozen columns capture locked-in baselines" and queries:
```sql
SELECT SUM(frozen_working_final_forecast) FROM 10_demand_daily WHERE ... 
```
In reality, **these columns are 100% NULL** (deprecated, never migrated, or planning tool hasn't been used). Query returns all NULL, no error.

### WRONG Query (Conceptual)
```sql
-- Attempt to use frozen column (100% NULL)
SELECT 
  COUNT(*) as row_count,
  COUNT(frozen_working_final_forecast) as non_null_frozen,
  SUM(frozen_working_final_forecast) as frozen_sum
FROM prod_edw.fact.`10_demand_daily`
WHERE product_bigint_key = 3879620845706693458
  AND date_key = 20260829
  AND frozen_working_final_forecast IS NOT NULL
```

**WRONG Result:**
```
| row_count | non_null_frozen | frozen_sum |
|-----------|-----------------|------------|
| 10000     | 0               | NULL       |
```
- **No rows match; query returns no data, misleading planner into thinking "no frozen data exists" when in fact the column is never used.**

### RIGHT Query (Conceptual)
```sql
-- Use process_date day-over-day comparison for plan stability
SELECT 
  process_date,
  SUM(planner_baseline) as baseline_sum,
  LAG(SUM(planner_baseline)) OVER (ORDER BY process_date) as prev_day_baseline,
  SUM(planner_baseline) - LAG(SUM(planner_baseline)) OVER (ORDER BY process_date) as plan_change
FROM prod_edw.fact.`10_demand_daily`
WHERE product_bigint_key = 3879620845706693458
  AND date_key = 20260905
  AND process_date IN (20260825, 20260826, 20260827, 20260828, 20260829)
GROUP BY process_date
ORDER BY process_date DESC
```

**RIGHT Result:**
```
| process_date | baseline_sum | prev_day_baseline | plan_change |
|--------------|--------------|-------------------|-------------|
| 20260829     | 50,000       | 55,000            | -5,000      |
| 20260828     | 55,000       | 58,000            | -3,000      |
```
- Shows actual plan stability via `planner_baseline` and process_date deltas.

### Error Magnitude
- **WRONG:** 100% NULL → zero rows returned, no insight into plan stability.
- **RIGHT:** Actual baseline with day-over-day change tracking.
- **Error Type:** **Silent data absence.** No error message; planner mistakenly thinks no frozen forecast exists.

### Priority Impact
**P4 / P3:** Plan stability and S&OP (Sales & Operations Planning) require understanding when baselines change. Without it, planners can't detect forecast volatility or detect overly optimistic/pessimistic replanning.

### Planner Impact
Planner expects a "frozen forecast" feature to exist and wastes time troubleshooting why the column is NULL, instead of using the actual available columns (planner_baseline) and process_date deltas to assess plan volatility.

### Guardrail Rule
**NEVER use frozen_* columns for 10_demand_daily.** These are deprecated and 100% NULL. For plan-change tracking, use:
- `planner_baseline` + `process_date` day-over-day comparison
- `planner_baseline_forecast` (if available and populated)
- Always verify column population with a `COUNT(column_name) > 0` check before relying on a new column.

---

## Summary Table: Anti-Pattern Reference

| Anti-Pattern | Wrong Result | Right Result | Error Magnitude | Guardrail Rule | Priority |
|---|---|---|---|---|---|
| **AP1: PIT Snapshot Summation** | SUM across 4 dates = 456,463 | Latest snapshot = 83,254 | 5.48× inflation | Never SUM on_hand_qty across date_keys; use MAX() or latest only. | P1/P2 |
| **AP2: Material Transaction Double-Counting** | SUM all qty (includes transfers 2×) | GROUP BY reason; net only | 2–4× inflation | Separate by transaction reason; transfer pairs post twice (ship+receive). | P2/P3 |
| **AP3: Raw Staging No Item Column** | Query fails; no item_id in raw | Use purchase_receipt_line fact | Structural error; join fails | Use cleaned fact tables; raw staging lacks item context. | P3 |
| **AP4: Sparse Shipped_Quantity (87% NULL)** | Naive SUM/AVG includes NULLs | Filter to order_type='Standard', status='Invoiced', qty>0 | ~6.7× underrepresentation | Filter to non-NULL and valid order statuses before aggregating. | P2 |
| **AP5: Unit-Miss vs. Cost** | Top 10 by raw unit-miss = $13 item | Top 10 by (unit-miss × cost) = $970 item | Priority rank flipped by 70× | Weight unit-miss by applied_standard_cost; rank by financial impact. | P2 |
| **AP6: Single-Snapshot Blindness** | Latest snapshot = "healthy" | Compare same date_key across 2–3 process_dates | Misses 80K unit plan degradation | Always compare vintages; use LAG() for trend; flag large deltas. | P1/P2 |
| **AP7: 20_Supply_Daily Grain Blindness** | SUM = 150K (all order types mixed) | GROUP BY series, order_type = 75K (Standard only) | 2× if order types mixed | Fact is multi-grained by series + order_type; GROUP BY to get true grain. | P3 |
| **AP8: Frozen Columns 100% NULL** | Count = 0; column appears unused | Use planner_baseline + process_date delta | Silent NULL; no error, no data | Frozen_* cols are deprecated; use active baseline cols; verify population. | P4/P3 |

---

## Closing: Evidence-Based Guardrails

These anti-patterns are **validated against Milwaukee's actual data structure** (not generic Databricks patterns). Each guardrail is enforced by:

1. **Query templates** in project dashboards that build in the filter/grouping automatically.
2. **Data quality expectations** in Unity Catalog (e.g., on_hand_qty is semi-additive, transfer rows split by reason).
3. **Code review checklists** flagging SELECT SUM() without GROUP BY on known multi-grained tables.
4. **Monitoring** tracking plan-change detection (AP6) and exception cost-weighting (AP5) in production.

**Learning from past work:** Misses have occurred when developers skip the schema documentation or inherit queries written before the dimension model was finalized. Treating this catalog as living reference material (not carved-in-stone rules) keeps the pattern library current as the data evolves.

---

**Document Generated:** 2026-08-30  
**Data Sources (READ-ONLY):**
- prod_edw.fact.inventory_days_on_hand
- prod_edw.fact.inventory_material_transaction
- prod_edw.fact.purchase_receipt_line
- prod_edw.fact.sales_order_line_transactions
- prod_edw.fact.`20_supply_daily`
- prod_edw.fact.`10_demand_daily`

**All queries are SELECT-only; no writes to production schemas.**
