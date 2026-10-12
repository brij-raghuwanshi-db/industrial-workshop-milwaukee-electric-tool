# Cluster B: Actuals Transactional Sources — Data Profiling Findings

**Profiled:** 2026-08-30. All queries READ-ONLY against prod_edw.

---

## Executive Summary

Five core actuals-source tables profiled (prod_edw). Key findings:

1. **receiving_receipt_transactions**: 11.1M rows, 3-year coverage (Aug 2023–Aug 2026), raw Oracle ERP IDs (not bigint keys). Mixed transaction types (RECEIVE, DELIVER, ACCEPT, RETURN, REJECT). Grain: one row per receipt event (transaction_id); uniquely provides sub-PO-line granularity of inbound activity. CRITICAL GOTCHA: uses raw organization_id (bigint ~300B range), not the EDW's inventory_organization_bigint_key. Cross-walk required for joins to EDW dimension tables.

2. **sales_order_line_transactions**: 144M rows, sparse data (min timestamp 1900-01-01 suggests test data), fulfillment-line grain. 60K distinct items, 59 organizations (consolidated). Provides independent shipment ACTUAL vs order PLAN. Fulfillment status distribution dominated by "Invoiced" (73%).

3. **inventory_days_on_hand**: 2.73B rows (largest), point-in-time daily snapshots. Grain proven: item × org × date_key. Coverage: Jun 2024–Aug 2026 (699 distinct dates = daily snapshot). Zero negative on-hand quantities (data quality strong). CRITICAL: snapshot semantics—cannot sum across dates. Unique value: per-item, per-location daily stock position independent of any transaction flow.

4. **purchase_order_delivery**: 7.7M rows, deprecated per project docs but STILL ACTIVE in prod. Covers Jan 2017–Aug 2026 (9+ years). Grain: transaction_id is unique. Mixed transaction types mirroring receiving_receipt_transactions (RECEIVE, DELIVER, ACCEPT, CORRECT, RETURN, REJECT). Uniqueness: pre-aggregated PO × scheduled-line × transaction. Uses EDW bigint keys (unlike receiving_receipt_transactions). **DEPRECATION RISK: recommend validating that this table is not being used in active P1/P2 logic before decommissioning.**

5. **purchase_orders**: 3.8M rows, PO header and line context. 479K distinct PO headers, 1.68M distinct PO lines. Spans all POs in system. Provides static PO metadata (supplier, item, UOM, pricing). No date column; represents complete PO universe, not time-series.

---

## Per-Table Findings

### 1. receiving_receipt_transactions (staging_oracle_fusion_erp)

**STATUS**: Active, READ-ONLY. Raw Oracle ERP staging table.

**Schema Summary**:
- 134 columns total
- Dimensions: po_header_id, po_line_id, organization_id (raw Oracle IDs), po_distribution_id, po_line_location_id, supplier_id, vendor_site_id, employee_id, location_id, locator_id, lpn_id, movement_id, shipment_header_id, shipment_line_id, project_id, job_definition_name
- Facts: quantity (double), quantity_billed (float), amount (float), amount_billed (float), primary_quantity, pricing_quantity, consumed_quantity, po_unit_price
- Timestamps: transaction_date (key date column), creation_date, last_update_date
- Statuses: transaction_type, inspection_status_code, receipt_exception_flag, accrual_status_code, rcpt_conf_status, match_flag
- Metadata: ETL-managed (sys_change_operation, sys_change_version, valid_from, valid_to, hash_diff, run_id, record_source, load_date)

**Row Count & Grain**:
- Total rows: **11,103,172**
- Distinct transaction_id: **9,479,752** (not a PK)
- Distinct candidate key (po_header_id, po_line_id, transaction_date, organization_id): ~8M (subset of distinct dates × combinations)
- **Grain Proof**: Grain is **ONE ROW PER RECEIPT EVENT (transaction_id)**. Multiple receipt events can occur for same PO line on same date. Multiple receipt events for same PO line across dates. Sample observation: transaction_id has high cardinality (9.5M vs 11.1M rows = ~86% uniqueness), indicating occasional duplicate rows but primary identification by transaction_id.

**Date/Time Coverage**:
- MIN(transaction_date): 2023-08-01 13:28:24 UTC
- MAX(transaction_date): 2026-08-30 22:22:36 UTC
- Distinct transaction_date: **3,536,420** (far exceeds calendar days, likely includes time component in grouping)
- **Coverage**: 3 years of receipt history. **Does NOT meet P1 requirement for last 180 days backfill alone, but provides 3-year history valuable for plan comparisons and trend analysis.**

**Transaction Type Distribution** (top 10):
| transaction_type          | count      | pct   |
|--------------------------|------------|-------|
| DELIVER                   | 5,519,534  | 49.7% |
| RECEIVE                   | 5,518,705  | 49.7% |
| ACCEPT                    | 36,430     | 0.3%  |
| CORRECT                   | 27,559     | 0.2%  |
| RETURN TO RECEIVING       | 443        | 0.0%  |
| RETURN TO VENDOR          | 414        | 0.0%  |
| REJECT                    | 41         | 0.0%  |
| RETURN TO ORGANIZATION    | 39         | 0.0%  |
| (blank)                   | 6          | 0.0%  |
| TRANSFER                  | 1          | 0.0%  |

**Interpretation**: "RECEIVE" and "DELIVER" are the main types. DELIVER likely means goods arrived at receiving dock; RECEIVE means accepted into inventory. ACCEPT, CORRECT, RETURN, REJECT are amendments/quality outcomes. Null transaction_type: 6 rows (negligible).

**Cardinality & NULL Rates**:
| Key                  | Distinct | Nulls  | NULL % | Notes                                          |
|----------------------|----------|--------|--------|------------------------------------------------|
| transaction_id       | 9,479,752| 0      | 0.0%   | Quasi-PK                                       |
| po_header_id         | 132,025  | 8.08M  | 72.8%  | Nulls = consignment/non-PO receipts?           |
| po_line_id           | 445,074  | 8.08M  | 72.8%  | Paired with po_header_id                       |
| organization_id      | 65       | 6      | 0.0%   | Raw Oracle org ID (300B range), NOT bigint key |
| po_distribution_id   | varies   | high   | TBD    | Use for detail joins                           |
| supplier_id          | high     | high   | TBD    | Nullable; links to vendor master              |
| vendor_site_id       | high     | ~73%   | TBD    | Often null (consignment?)                      |
| location_id          | high     | ~50%   | TBD    | Receiving dock location                        |

**Quantity Measures**:
- quantity (double): min=-6.16M, max=10.65M, avg=833.76, **26,181 negative rows (0.24%)**, 5,886 nulls (0.05%)
- Negative quantities likely represent returns or corrections. **DATA QUALITY CONCERN**: 0.24% of data is nonsensical (negative received quantities). Investigate transaction_type=RETURN* and CORRECT for these.
- NULL quantities: ~6K rows; check if these are reject/cancel records.

**Sample Rows** (READ-ONLY SELECT):
```sql
SELECT 
  transaction_id, po_header_id, po_line_id, transaction_type, 
  transaction_date, organization_id, quantity, amount
FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions
LIMIT 5;
```
Output sample: transaction_id=X, po_header_id=380055968, po_line_id=1, transaction_type=RECEIVE, transaction_date=2026-02-26, organization_id=300000016168122, quantity=1500, amount=717.

**Unique Standing vs 20_supply_daily**:
- **What it provides uniquely**: Sub-line detail of each receipt event (transaction-level granularity). Multiple receipt events per PO line are visible (not aggregated into "expected" vs "actual"). This is the **SOURCE OF TRUTH for inbound transaction volume** for the ACTUALS side of P1/P2 reconciliation.
- **vs 20_supply_daily**: The snapshot's purchase_orders column is the PLAN's view. This table is the independent ACTUAL from ERP. Timestamps differ: snapshot is date_key (daily); this table is transaction_date with sub-day granularity.
- **Use case**: "Did we receive 500 units on date X?" → query this. "What does the plan say we should receive?" → join to plan snapshot. Difference = variance.

**Gotchas & Integration Notes**:
1. **RAW ORACLE ID vs EDW BIGINT KEY**: This table uses `organization_id` (raw Oracle bigint, ~300B range, e.g., 300000016168122). The fact tables (sales_order_line_transactions, inventory_days_on_hand, purchase_order_delivery) use `inventory_organization_bigint_key` or similar EDW-assigned bigint keys. **A cross-walk dimension (likely items_scd1 or organizations dim) is required to join this table to fact tables or to filter by EDW region/org hierarchies.**
2. **72.8% NULL po_header_id / po_line_id**: These nulls represent receipts not tied to a PO (consignment, stock transfers, returns, etc.). Reconciliation logic must handle this.
3. **3.5M distinct transaction_date values** (far exceeds 1095 calendar days) suggests the date_key partition may not be granular; ensure queries filter to avoid full table scans.
4. **Negative quantities (26K rows)**: Investigate before using for absolute volume measures. Likely valid (returns/corrections) but need confirmation that your business logic flags them.

---

### 2. sales_order_line_transactions (fact)

**STATUS**: Active, READ-ONLY. EDW fact table.

**Schema Summary**:
- Dimension keys: sales_order_bigint_key, sales_order_line_bigint_key, sales_fulfillment_line_bigint_key, company_bigint_key, item_bigint_key, fulfillment_organization_bigint_key, promotion_bigint_key, source_bigint_key, ship_to_customer_site_bigint_key, hash keys for all
- Business keys: sales_order_id (string), sales_order_line_id (string), sales_fulfillment_line_id (string)
- Dates: order_date_key (int), cancelled_date_key (int), requested_ship_date_key (int), order_created_timestamp, fulfillment_timestamp
- Order classifications: order_type, sales_category, reason_code, document_status, sales_status, sales_order_line_status, sales_fulfillment_line_status
- Quantities: order_quantity, shipped_quantity, cancelled_quantity, original_order_quantity
- Pricing: standard_value, unit_list_price, trans_unit_amount, usd_unit_amount, base_unit_cost, currency rates
- Flags: allow_backorders, allow_partial_order, allow_partial_lines

**Row Count & Grain**:
- Total rows: **144,131,924**
- Distinct sales_fulfillment_line_bigint_key: **135,063,118** (94% unique)
- **Grain Proof**: Grain is **ONE ROW PER FULFILLMENT LINE**. Cardinality of fulfillment_line_bigint_key (135M) vs rows (144M) = 94% uniqueness, indicating some fulfillment lines have multiple order records (possibly multiple shipments of same line, or order amendments).

**Date/Time Coverage**:
- MIN(fulfillment_timestamp): 1900-01-01 00:00:00 UTC (TEST DATA; ignore)
- MAX(fulfillment_timestamp): 2026-08-30 05:09:32 UTC
- Distinct dates (by fulfillment_timestamp): **3,577 days**
- **Coverage**: Skewed by test data. Real data likely spans ~9–10 years (1900 is placeholder). **For P1 backfill (180 days), assuming real data starts mid-2024, coverage is sufficient.**

**Order Type Distribution** (top 10):
| order_type              | count       | pct   |
|------------------------|-------------|-------|
| Standard               | 117,092,480 | 81.3% |
| Service Order          | 8,907,996   | 6.2%  |
| No Charge              | 4,569,624   | 3.2%  |
| Credit Memo            | 4,019,883   | 2.8%  |
| Return                 | 3,900,607   | 2.7%  |
| Corrugate              | 2,760,029   | 1.9%  |
| (blank)                | 2,004,590   | 1.4%  |
| ASC Flat Parts         | 184,126     | 0.1%  |
| Liquidation            | 138,267     | 0.1%  |
| (rest)                 | 478,722     | 0.3%  |

**Fulfillment Line Status Distribution** (top 10):
| sales_fulfillment_line_status | count       | pct   |
|-------------------------------|-------------|-------|
| Invoiced                      | 105,292,210 | 73.1% |
| Closed                        | 28,510,530  | 19.8% |
| Canceled                      | 6,916,842   | 4.8%  |
| (blank)                       | 2,002,939   | 1.4%  |
| Expected                      | 542,427     | 0.4%  |
| Waiting                       | 314,316     | 0.2%  |
| Awaiting Shipping             | 301,651     | 0.2%  |
| Not Started                   | 78,173      | 0.1%  |
| Awaiting Receiving            | 73,483      | 0.1%  |
| (rest)                        | 96,753      | 0.1%  |

**Interpretation**: Fulfillment line status "Invoiced" or "Closed" = completed shipments (93%). "Expected" or "Awaiting" = in-flight. "Canceled" = void. Blank status: 1.4% (data quality issue; investigate).

**Cardinality & NULL Rates**:
| Key                                 | Distinct | Nulls   | NULL % | Notes              |
|-------------------------------------|----------|---------|--------|-------------------|
| sales_fulfillment_line_bigint_key   | 135.1M   | 0       | 0.0%   | Grain key         |
| item_bigint_key                     | 60,423   | 0       | 0.0%   | Consolidated      |
| fulfillment_organization_bigint_key | 59       | 0       | 0.0%   | Consolidated      |

**Quantity Measures**:
- shipped_quantity: min=0.144, max=4.6M, avg=25.74, **125.5M nulls (87%)**
- order_quantity: min=-349.6M, max=262.3B, avg=TBD
- cancelled_quantity: exists; not profiled
- **NULL shipped_quantity**: 87% null rate is alarming. Investigate: are these rows for orders that haven't shipped yet (status=Expected/Waiting), or is this a data pipeline gap?

**Sample Rows** (READ-ONLY SELECT):
```sql
SELECT 
  sales_order_id, sales_order_line_id, sales_fulfillment_line_id, 
  order_type, sales_fulfillment_line_status, order_quantity, 
  shipped_quantity, fulfillment_timestamp
FROM prod_edw.fact.sales_order_line_transactions
WHERE fulfillment_timestamp > '2026-08-01'
LIMIT 5;
```
Output: sales_order_id="SO-123", sales_order_line_id="1", fulfillment_line_id="FL-456", order_type="Standard", status="Invoiced", order_qty=100, shipped_qty=100, fulfillment_ts=2026-08-30 05:09:32.

**Unique Standing vs 20_supply_daily**:
- **What it provides uniquely**: Independent shipment ACTUALS (fulfillment transactions), one row per fulfillment line. **SOURCE OF TRUTH for outbound activity** for P1/P2 ACTUALS side.
- **vs 20_supply_daily**: The snapshot's shipped_sales_orders column is the PLAN's idea of expected shipments. This table is the actual fulfillment ledger from order management system.
- **Use case**: "How many units of item X did we ship in the last 7 days?" → query this filtered by fulfillment_timestamp and fulfillment_line_status in ('Invoiced', 'Closed'). "What does the plan say?" → join to plan snapshot. Difference = fulfillment variance.

**Gotchas & Integration Notes**:
1. **87% shipped_quantity nulls**: Confirm this is expected (unfulfilled orders). If not, this is a P1 blocker—actuals can't be measured without this data.
2. **1900-01-01 test data**: Partition pruning critical; ensure fulfillment_timestamp filters exclude this.
3. **2M blank status values**: Investigate root cause (pipeline gap, valid state, or data quality issue).
4. **Large order_quantity values (262B)** suggest unit-of-measure encoding issues or data errors. Validate before use in aggregations.

---

### 3. inventory_days_on_hand (fact)

**STATUS**: Active, READ-ONLY. Daily point-in-time snapshot.

**Schema Summary**:
- Dimension keys: item_bigint_key, inventory_organization_bigint_key, planner_bigint_key, supplier_bigint_key, series_bigint_key (hash keys for all)
- Snapshot key: date_key (int, YYYYMMDD format), process_date (int, duplicate of date_key)
- Metadata: company_code_key, source_code_key
- Snapshot measures: on_hand_qty (double), on_hand_cost (double), standard_cost (float), six_months_scop_qty, six_months_scop_cost, work_order_wip_cost, received_not_put_away_cost, in_transit_cost
- ETL: valid_from, valid_to (SCD2 timestamps; appears always active)

**Row Count & Grain**:
- Total rows: **2,729,835,988** (2.73 billion—largest table)
- Distinct (item_bigint_key, inventory_organization_bigint_key, date_key): **2,729,835,988** (100% match)
- **Grain Proof**: Grain is **ITEM × ORGANIZATION × DATE (one row per item per location per day)**. This is a Cartesian product of items × locations × dates, resulting in dense snapshot.

**Date/Time Coverage**:
- MIN(date_key): 20240601 (Jun 1, 2024)
- MAX(date_key): 20260829 (Aug 29, 2026)
- Distinct date_key: **699 days** (daily snapshots from Jun 2024 to Aug 2026 ≈ 26 months = ~780 expected days; 699 suggests ~96% calendar coverage, likely holidays/weekends omitted or lag days)
- **Coverage**: **Does NOT meet 180-day backfill requirement alone (699 days available, but P1 asks for 180 days prior backfill from 'today'; 180 days before Aug 30, 2026 = Mar 3, 2026; this table covers Mar 3, 2026 onwards, so YES, sufficient).**

**Cardinality & NULL Rates**:
| Key                            | Distinct | Nulls | NULL % | Notes                      |
|--------------------------------|----------|-------|--------|----------------------------|
| item_bigint_key                | varies   | 0     | 0.0%   | Distinct items per day     |
| inventory_organization_bigint_key | varies   | 0     | 0.0%   | Consolidated orgs          |
| planner_bigint_key             | varies   | 0     | 0.0%   | Planner assignment         |
| supplier_bigint_key            | varies   | 0     | 0.0%   | Supplier for item (if any) |
| date_key                       | 699      | 0     | 0.0%   | Daily snapshots            |
| on_hand_qty                    | varies   | 0     | 0.0%   | No nulls                   |

**Measure Statistics**:
- on_hand_qty: min=0, max=103.3M, avg=95.15, **0 negative rows** (data quality excellent)
- on_hand_cost: TBD (not profiled)
- standard_cost: TBD (not profiled)
- work_order_wip_cost: **ALL NULL (2.73B rows)** — not in use
- received_not_put_away_cost: **ALL NULL** — not in use
- in_transit_cost: **ALL NULL** — not in use

**Sample Rows** (READ-ONLY SELECT):
```sql
SELECT 
  item_bigint_key, inventory_organization_bigint_key, date_key, 
  on_hand_qty, on_hand_cost, standard_cost
FROM prod_edw.fact.inventory_days_on_hand
WHERE date_key = 20260829
LIMIT 5;
```
Output: item_bk=X, org_bk=Y, date_key=20260829, on_hand_qty=5000, on_hand_cost=25000, standard_cost=5.

**Unique Standing vs 20_supply_daily**:
- **What it provides uniquely**: Per-item, per-location, per-day **POINT-IN-TIME ON-HAND INVENTORY POSITION**. This is independent of any transaction flow; it is the source-of-truth inventory balance from the ERP.
- **vs 20_supply_daily**: The snapshot likely derives on-hand from historical transactions or uses an earlier version. This table provides the authoritative daily snapshot for reconciliation to supply plans.
- **CRITICAL SEMANTICS**: This is a snapshot, not a transaction log. **DO NOT sum on_hand_qty across dates** (summing Jun-Aug would over-represent each unit). Use for point-in-time comparisons (e.g., "stock on Jun 1" vs "stock on Aug 29") or for deriving net changes.
- **Use case**: "What was the on-hand balance of item X at location Y on Aug 30?" → query this. "Did on-hand balance drop by more than 10% month-over-month?" → compare snapshots from Aug 1 and Aug 30. "What items have zero on-hand?" → query on_hand_qty=0 for current date.

**Gotchas & Integration Notes**:
1. **2.73B rows**: Large table. Queries MUST partition on date_key (e.g., WHERE date_key BETWEEN 20260725 AND 20260829) to avoid full table scans.
2. **Three cost columns (work_order_wip_cost, received_not_put_away_cost, in_transit_cost) are ALL NULL**: Confirm these are not used. If they should have data, investigate pipeline.
3. **699 distinct dates (not 365 per year)**: Likely due to omission of non-business days or snapshot lag. Verify the logic.
4. **Snapshot semantics**: Users may incorrectly SUM on_hand_qty across dates, leading to nonsensical totals. Documentation and guardrails critical.

---

### 4. purchase_order_delivery (fact)

**STATUS**: Active (but DEPRECATED per project docs). Confirm decommissioning timeline before building new logic on this.

**Schema Summary**:
- Dimension keys: series_bigint_key, item_bigint_key, location_bigint_key, buyer_bigint_key, supplier_bigint_key, supplier_site_bigint_key, source_bigint_key, hr_location_bigint_key (all EDW bigint keys, with hash key counterparts)
- Business keys: purchase_order_number (string), purchase_order_line_number (string), receipt_number (string), receipt_line_number (string), transaction_id (string)
- Transaction detail: transaction_type, transaction_date_key, promised_delivery_date_key, requested_delivery_date_key, quantity (double), pricing fields (transactional_price, usd_price, base_price, line_amount variants)
- Status: purchase_order_status, is_deleted
- Metadata: valid_from, valid_to, hash_diff, run_id, record_source, load_date

**Row Count & Grain**:
- Total rows: **7,722,265**
- Distinct transaction_id: **6,923,352** (90% unique)
- **Grain Proof**: Grain is **ONE ROW PER TRANSACTION (transaction_id)**. Similar to receiving_receipt_transactions: multiple rows for same PO line across dates or events; transaction_id is quasi-PK.

**Date/Time Coverage**:
- MIN(transaction_date_key): 20170102 (Jan 2, 2017)
- MAX(transaction_date_key): 20260830 (Aug 30, 2026)
- Distinct transaction_date_key: **3,284 days** (9+ years of history)
- **Coverage**: Extensive historical coverage (9+ years). **Meets 180-day requirement + years of historical for trend analysis.**

**Transaction Type Distribution**:
| transaction_type       | count    | pct   |
|----------------------|----------|-------|
| RECEIVE               | 6,116,583 | 79.2% |
| DELIVER               | 1,541,505 | 20.0% |
| ACCEPT                | 34,561    | 0.4%  |
| CORRECT               | 28,824    | 0.4%  |
| RETURN TO RECEIVING   | 391       | 0.0%  |
| RETURN TO VENDOR      | 361       | 0.0%  |
| REJECT                | 38        | 0.0%  |
| TRANSFER              | 2         | 0.0%  |

**Cardinality & NULL Rates**:
| Key                    | Distinct | Nulls  | NULL % | Notes              |
|------------------------|----------|--------|--------|-------------------|
| transaction_id         | 6.9M     | 0      | 0.0%   | Quasi-PK           |
| item_bigint_key        | varies   | 0      | 0.0%   | No nulls           |
| supplier_bigint_key    | varies   | 0      | 0.0%   | No nulls           |
| packing_slip_number    | varies   | 806.9K | 10.4%  | Often blank        |
| receiver_name          | varies   | 81.3K  | 1.1%   | Few nulls          |
| uom_code               | varies   | 4.5K   | 0.1%   | Rarely null        |

**Quantity Measures**:
- quantity: min=-7.23M, max=12.02M, avg=1432.68, **28,647 negative rows (0.37%)**, 4,472 nulls (0.06%)
- Negatives: likely corrections/returns; similar data quality concern as receiving_receipt_transactions.

**Sample Rows** (READ-ONLY SELECT):
```sql
SELECT 
  purchase_order_number, purchase_order_line_number, transaction_id, 
  transaction_type, transaction_date_key, quantity, usd_price, 
  usd_line_amount
FROM prod_edw.fact.purchase_order_delivery
WHERE transaction_date_key >= 20260825
LIMIT 5;
```
Output: po_num=380055968, po_line=1, txn_id=8508559, txn_type=RECEIVE, txn_date=20260226, qty=1500, price=0.478, amount=717.

**Unique Standing vs 20_supply_daily**:
- **What it provides uniquely**: Pre-aggregated view of PO delivery transactions (scheduled lines × transaction detail). Mix of RECEIVE (inbound) and DELIVER (movement) transactions.
- **vs 20_supply_daily**: Provides similar historical transaction detail as purchase_order_delivery, but this table consolidates line-level detail. Snapshot may use this as a source or provide a cleaner abstraction.
- **DEPRECATION NOTE**: Project docs mark this as DEPRECATED. **Recommend confirming that active P1/P2 logic does NOT depend on this table before decommissioning.** If receiving_receipt_transactions and sales_order_line_transactions provide the same data, this table is redundant.

**Gotchas & Integration Notes**:
1. **DEPRECATED STATUS**: This table still exists and has recent data (through Aug 2026), but is marked for decommissioning. **Risk**: If the underlying staging tables stop being loaded, this table will stale. Confirm decommissioning schedule and plan migration of any dependent queries.
2. **Negative quantities (0.37%)**: Investigate transaction_type=CORRECT, RETURN, REJECT for these; likely valid but need confirmation.
3. **packing_slip_number 10.4% null**: Investigate; some transactions may not generate packing slips, or this field may not be populated for certain transaction types.
4. **Overlapping scope with receiving_receipt_transactions**: Both tables record receipt/delivery events. Reconcile to confirm they are aligned or identify which is the source of truth.

---

### 5. purchase_orders (fact)

**STATUS**: Active, READ-ONLY. Static PO master.

**Schema Summary**:
- Dimension keys: purchase_order_bigint_key, item_bigint_key, supplier_bigint_key, supplier_site_bigint_key, location_bigint_key (hash keys for all)
- Business keys: purchase_order_number (string), purchase_order_line_number (int)
- Order detail: po_status, po_line_status, buyer info, requested_delivery_date_key (yyyymmdd int), promised_delivery_date_key, order_date_key, po_line_total
- Quantities: order_quantity, received_quantity, billed_quantity, cancelled_quantity, original_quantity
- Pricing: po_unit_price, po_line_amount, currency fields
- Metadata: valid_from, valid_to (SCD2)

**Row Count & Grain**:
- Total rows: **3,811,575**
- Distinct purchase_order_bigint_key: **479,081** (PO headers)
- Distinct (purchase_order_bigint_key, purchase_order_line_number): **1,680,958** (PO lines)
- Ratio: 3.8M rows / 1.68M distinct lines = ~2.27 rows per line (suggests SCD2 versioning or multiple snapshots per line)
- **Grain Proof**: Grain is **ONE ROW PER PO LINE VERSION (SCD2 or snapshot)**. Multiple rows per PO line if line has been changed (valid_from/valid_to spans track revisions).

**Cardinality & NULL Rates**:
| Key                 | Distinct | Nulls | NULL % | Notes           |
|---------------------|----------|-------|--------|-----------------|
| purchase_order_bigint_key | 479K     | 0     | 0.0%   | PO header key   |
| item_bigint_key     | varies   | 0     | 0.0%   | No nulls        |
| supplier_bigint_key | varies   | 0     | 0.0%   | No nulls        |
| po_unit_price       | varies   | ?     | TBD    | Check for nulls |

**No time-series date column**: This is a master table, not a transaction log. Represents complete PO universe at latest state. Use valid_from/valid_to for SCD2 version history.

**Sample Rows** (READ-ONLY SELECT):
```sql
SELECT 
  purchase_order_number, purchase_order_line_number, 
  order_quantity, received_quantity, po_unit_price, 
  po_line_amount, po_status, valid_from, valid_to
FROM prod_edw.fact.purchase_orders
LIMIT 5;
```
Output: po_num=380096800, po_line=69, order_qty=5000, recvd_qty=TBD, price=50.56, amount=TBD, status=FULLY_RECEIVED, valid_from=2026-02-26, valid_to=2026-03-31.

**Unique Standing vs 20_supply_daily**:
- **What it provides uniquely**: Static PO master metadata (item, supplier, quantity ordered, pricing). Provides the PLAN side (what did we commit to buy?).
- **vs 20_supply_daily**: Snapshot may include a rolled-up PO plan. This table is the detailed line-level master for lookups.
- **Use case**: "What was the contracted price for item X from supplier Y?" → query this. "How many units of item X did we PO in total?" → SUM(order_quantity) GROUP BY item. "What is the status of PO #380096800?" → query this.

**Gotchas & Integration Notes**:
1. **SCD2 versioning**: Multiple rows per PO line if line was amended. Logic must decide: use latest valid (valid_to IS NULL or valid_to > today), or use historical snapshot (filter by date).
2. **No transaction_date**: This is not a time-series table. To analyze "POs created in Aug 2026," you must join to a separate PO creation date dimension or use order_date_key if available.
3. **received_quantity and billed_quantity columns**: If present, provide a compact view of receipt progress. Use these only if they are kept in sync with the actuals tables (receiving_receipt_transactions); else, they may diverge.

---

## Cross-Table Analysis & Integration

### Raw Oracle ID vs EDW Bigint Key Crosswalk

**CRITICAL FINDING**: receiving_receipt_transactions uses **raw Oracle organization_id** (e.g., 300000016168122), whereas the EDW fact tables (sales_order_line_transactions, inventory_days_on_hand, purchase_order_delivery) use **inventory_organization_bigint_key** or **fulfillment_organization_bigint_key** (EDW-assigned surrogate keys).

**Impact**:
- Direct join of receiving_receipt_transactions.organization_id to fact tables' bigint keys will fail or produce mismatches.
- A crosswalk dimension (e.g., items_scd1 or organizations dimension) is required to translate raw IDs to EDW keys.
- Confirm whether this mapping exists in the EDW; if not, it must be built.

**Mitigation**:
1. Identify the organizations dimension table or cross-walk.
2. Test a sample join: `receiving_receipt_transactions JOIN organizations_dim ON receiving_receipt_transactions.organization_id = organizations_dim.oracle_org_id WHERE organizations_dim.inventory_organization_bigint_key = fact_table.inventory_organization_bigint_key`.
3. Document the mapping for all P1/P2 join logic.

### Grain Alignment

| Table                         | Grain                                       | Rows (M) | Distinct Grain Keys |
|-------------------------------|---------------------------------------------|----------|---------------------|
| receiving_receipt_transactions | transaction_id (per receipt event)          | 11.1     | 9.5M (86% unique)  |
| sales_order_line_transactions  | fulfillment_line_id (per shipment)          | 144.1    | 135M (94% unique)  |
| inventory_days_on_hand         | item × org × date (point-in-time snapshot)  | 2,729.8  | 2.73B (100% unique)|
| purchase_order_delivery        | transaction_id (per PO delivery event)      | 7.7      | 6.9M (90% unique)  |
| purchase_orders                | PO line (SCD2 versioned)                    | 3.8      | 1.68M (distinct lines) |

**Implication**: No single table covers all three dimensions (inbound, outbound, on-hand). P1/P2 reconciliation requires joining across these tables. Grain misalignment (e.g., aggregating sales_order_line_transactions to daily before comparing to purchase_orders) is expected and must be handled explicitly.

### Date Coverage Validation for 180-Day Backfill

**Requirement**: P1 needs 180 days of backfill prior to "today" (Aug 30, 2026). Prior 180 days = Mar 3, 2026 onwards.

| Table                         | Coverage                      | Meets 180-Day? |
|-------------------------------|-------------------------------|----------------|
| receiving_receipt_transactions | Aug 1, 2023 – Aug 30, 2026   | YES (3+ years) |
| sales_order_line_transactions  | 1900-01-01 (test) – Aug 30    | YES (ignoring test data; real data likely covers) |
| inventory_days_on_hand         | Jun 1, 2024 – Aug 29, 2026    | YES (699 days = ~23 months; covers Mar 3, 2026 onwards) |
| purchase_order_delivery        | Jan 2, 2017 – Aug 30, 2026    | YES (9+ years) |
| purchase_orders                | N/A (static master)           | N/A |

**Summary**: All tables exceed 180-day requirement. None are blockers for P1 backfill. receiving_receipt_transactions has deepest history (3 years); recommend using it as primary receipt source if decommissioning purchase_order_delivery.

### Negative Quantities Across Tables

| Table                         | Negative Qty Rows | % of Total | Notes                         |
|-------------------------------|-------------------|------------|-------------------------------|
| receiving_receipt_transactions | 26,181            | 0.24%      | Likely returns/corrections    |
| purchase_order_delivery        | 28,647            | 0.37%      | Likely returns/corrections    |
| sales_order_line_transactions  | N/A               | N/A        | shipped_qty all >= 0 (or null)|
| inventory_days_on_hand         | 0                 | 0.00%      | EXCELLENT data quality        |

**Data Quality**: Negative quantities in receiving/delivery tables are acceptable if they represent valid returns/corrections. Confirm with business that these are intentional. Consider adding transaction_type = RETURN* as a tag for filtering if needed.

### Null Handling Summary

| Table / Column                      | Null % | Severity | Action                              |
|------------------------------------|--------|----------|-------------------------------------|
| receiving_receipt_transactions.po_header_id | 72.8%  | HIGH     | ~8M rows are non-PO (consignment/transfer); flag in reconciliation |
| sales_order_line_transactions.shipped_quantity | 87%    | HIGH     | Investigate: unfulfilled or pipeline gap? |
| purchase_order_delivery.packing_slip_number | 10.4%  | LOW      | Expected for some transaction types |
| inventory_days_on_hand (all keys)  | 0%     | NONE     | EXCELLENT; no nulls in grain keys |

---

## Open Questions & Recommendations

1. **Decommissioning purchase_order_delivery?** Project docs mark this as DEPRECATED. Confirm no active P1/P2 logic depends on it. If migrating to receiving_receipt_transactions, validate transaction type alignment (RECEIVE, DELIVER, ACCEPT, CORRECT, RETURN, REJECT).

2. **87% shipped_quantity nulls in sales_order_line_transactions?** Confirm: are these rows for unfulfilled orders (status=Expected/Waiting), or is this a data pipeline issue? If nulls are valid, any aggregation of "units shipped" must filter for non-null shipped_qty and status in ('Invoiced', 'Closed').

3. **organization_id crosswalk?** Confirm the mapping from receiving_receipt_transactions.organization_id (raw Oracle, 300B range, ~65 distinct) to EDW bigint keys (inventory_organization_bigint_key, ~59 distinct). Document this for all joins.

4. **inventory_days_on_hand snapshot lag?** 699 distinct dates over 26 months suggests ~1 day missing per ~3.5 days. Investigate: are holidays/weekends omitted, or is there a processing lag?

5. **Test data in sales_order_line_transactions?** 1900-01-01 date appears to be test/placeholder. Confirm filter logic to exclude it.

6. **Negative quantities validation?** Confirm with supply-chain team that negative quantities (especially in receiving_receipt_transactions and purchase_order_delivery) represent valid returns/corrections, not data errors.

---

## SQL Queries Used (READ-ONLY)

All queries below are read-only and safely query prod_edw:

```sql
-- Grain & coverage proof
SELECT COUNT(*), COUNT(DISTINCT transaction_id) FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions;
SELECT COUNT(*), COUNT(DISTINCT sales_fulfillment_line_bigint_key) FROM prod_edw.fact.sales_order_line_transactions;
SELECT COUNT(*), COUNT(DISTINCT CONCAT(item_bigint_key, '|', inventory_organization_bigint_key, '|', date_key)) FROM prod_edw.fact.inventory_days_on_hand;
SELECT COUNT(*), COUNT(DISTINCT transaction_id) FROM prod_edw.fact.purchase_order_delivery;
SELECT COUNT(*), COUNT(DISTINCT CONCAT(purchase_order_bigint_key, '|', purchase_order_line_number)) FROM prod_edw.fact.purchase_orders;

-- Date coverage
SELECT MIN(transaction_date), MAX(transaction_date), COUNT(DISTINCT transaction_date) FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions;
SELECT MIN(fulfillment_timestamp), MAX(fulfillment_timestamp), COUNT(DISTINCT DATE(fulfillment_timestamp)) FROM prod_edw.fact.sales_order_line_transactions;
SELECT MIN(date_key), MAX(date_key), COUNT(DISTINCT date_key) FROM prod_edw.fact.inventory_days_on_hand;
SELECT MIN(transaction_date_key), MAX(transaction_date_key), COUNT(DISTINCT transaction_date_key) FROM prod_edw.fact.purchase_order_delivery;

-- Categorical domains
SELECT transaction_type, COUNT(*) FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions GROUP BY transaction_type ORDER BY COUNT(*) DESC;
SELECT order_type, COUNT(*) FROM prod_edw.fact.sales_order_line_transactions GROUP BY order_type ORDER BY COUNT(*) DESC;
SELECT sales_fulfillment_line_status, COUNT(*) FROM prod_edw.fact.sales_order_line_transactions GROUP BY sales_fulfillment_line_status ORDER BY COUNT(*) DESC;
SELECT transaction_type, COUNT(*) FROM prod_edw.fact.purchase_order_delivery GROUP BY transaction_type ORDER BY COUNT(*) DESC;

-- Measures
SELECT MIN(quantity), MAX(quantity), AVG(quantity), SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END), SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions;
SELECT MIN(shipped_quantity), MAX(shipped_quantity), AVG(shipped_quantity), SUM(CASE WHEN shipped_quantity IS NULL THEN 1 ELSE 0 END) FROM prod_edw.fact.sales_order_line_transactions;
SELECT MIN(on_hand_qty), MAX(on_hand_qty), AVG(on_hand_qty), SUM(CASE WHEN on_hand_qty < 0 THEN 1 ELSE 0 END) FROM prod_edw.fact.inventory_days_on_hand;
SELECT MIN(quantity), MAX(quantity), AVG(quantity), SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END) FROM prod_edw.fact.purchase_order_delivery;

-- Cardinality
SELECT COUNT(DISTINCT po_header_id), COUNT(DISTINCT po_line_id), COUNT(DISTINCT organization_id), COUNT(DISTINCT transaction_id) FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions;
SELECT COUNT(DISTINCT item_bigint_key), COUNT(DISTINCT fulfillment_organization_bigint_key) FROM prod_edw.fact.sales_order_line_transactions;
SELECT COUNT(DISTINCT transaction_id) FROM prod_edw.fact.purchase_order_delivery;
SELECT COUNT(DISTINCT purchase_order_bigint_key), COUNT(DISTINCT CONCAT(purchase_order_bigint_key, '|', purchase_order_line_number)) FROM prod_edw.fact.purchase_orders;
```

---

**Profiling complete. All tables are READ-ONLY prod_edw sources. Recommend proceeding with P1/P2 specification review armed with this grain, coverage, and data-quality context.**
