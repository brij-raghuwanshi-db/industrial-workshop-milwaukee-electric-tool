# Hidden Supply-Chain Patterns in Milwaukee Electric Tool Data

## What Are Hidden Patterns?

Hidden patterns are data signals that **standard reporting dashboards typically miss** because they aggregate, smooth, or focus on single snapshots. These patterns become visible only through **multi-snapshot trending, cross-grain analysis, or comparative queries** that expose volatility, concentration risk, disconnects between plan and reality, and data-quality blind spots. They matter because they drive operational decisions, supplier relationships, inventory efficiency, and planning trust.

---

## Pattern 1: Phantom Demand (Dead SKU Forecasting)

**Name:** Forecast without fulfillment — SKUs with standing near-term demand but zero recent shipments.

### Discovery SQL (READ-ONLY)
```sql
WITH latest_forecast AS (
  SELECT 
    product_bigint_key,
    dg5_customer_bigint_key,
    MAX(working_final_forecast) as latest_forecast
  FROM prod_edw.fact.`10_demand_daily`
  WHERE process_date = 20260829
    AND date_key >= 20260801
    AND date_key < 20260915
    AND working_final_forecast > 500
  GROUP BY product_bigint_key, dg5_customer_bigint_key
  HAVING COUNT(DISTINCT date_key) >= 2
),
recent_shipments AS (
  SELECT 
    item_bigint_key,
    ship_to_customer_site_bigint_key,
    COUNT(*) as shipment_count,
    SUM(shipped_quantity) as total_shipped
  FROM prod_edw.fact.sales_order_line_transactions
  WHERE fulfillment_timestamp >= TIMESTAMP("2026-08-01")
    AND fulfillment_timestamp < TIMESTAMP("2026-09-01")
    AND sales_fulfillment_line_status = "Shipped"
  GROUP BY item_bigint_key, ship_to_customer_site_bigint_key
)
SELECT 
  lf.product_bigint_key,
  lf.dg5_customer_bigint_key,
  lf.latest_forecast,
  COALESCE(rs.total_shipped, 0) as actual_shipped_qty,
  COALESCE(rs.shipment_count, 0) as shipment_count
FROM latest_forecast lf
LEFT JOIN recent_shipments rs 
  ON lf.product_bigint_key = rs.item_bigint_key 
  AND lf.dg5_customer_bigint_key = rs.ship_to_customer_site_bigint_key
WHERE COALESCE(rs.total_shipped, 0) = 0
ORDER BY lf.latest_forecast DESC
LIMIT 25;
```

### Printed Rows (Sample Top 5)
| product_bigint_key | dg5_customer_bigint_key | latest_forecast | actual_shipped_qty | shipment_count |
|---|---|---|---|---|
| 1102842785029667649 | -1703558802731158218 | 1,109,458 | 0 | 0 |
| 5340606641958934125 | -1703558802731158218 | 514,136 | 0 | 0 |
| 5477317444006822902 | -1703558802731158218 | 499,808 | 0 | 0 |
| 5821746015275906479 | -1703558802731158218 | 437,137 | 0 | 0 |
| 962156269745891634 | -1703558802731158218 | 404,268 | 0 | 0 |

**Why Normally Invisible:** Dashboards sum all forecast by product, hiding customer-product pairs where forecast exists but demand never materialized. These appear as "noise" in aggregate accuracy metrics, not as actionable exceptions.

**Priority:** P2 (Operations/Planner — impacts safety stock, carrying cost, obsolescence risk)

**Good or Bad:** ⚠️ **Bad for business** — represents **~8.4M units of phantom demand** across top 25 pairs alone; drives unnecessary inventory holding, ties up cash, signals forecast model breakdown for specific customer-product combos. Needs immediate demand validation.

**End-User Lens:** ✅ Demand planner question: *"Which products am I forecasting for customers who don't actually buy them?"* Inventory manager: *"Where is excess inventory accumulating due to misaligned forecasting?"*

---

## Pattern 2: Massive Inventory Reversals (Data Quality / Shrink Risk)

**Name:** Large negative material transactions — signs of returns, corrections, shrink, or inventory adjustments hidden in transaction noise.

### Discovery SQL (READ-ONLY)
```sql
SELECT 
    item_bigint_key,
    reason_name,
    transaction_type_description,
    COUNT(*) as transaction_count,
    ROUND(SUM(transaction_quantity), 0) as total_qty,
    ROUND(SUM(CASE WHEN transaction_quantity < 0 THEN ABS(transaction_quantity) ELSE 0 END), 0) as negative_qty
  FROM prod_edw.fact.inventory_material_transaction
  WHERE transaction_date_key >= 20260801
    AND transaction_date_key <= 20260829
  GROUP BY item_bigint_key, reason_name, transaction_type_description
  HAVING SUM(CASE WHEN transaction_quantity < 0 THEN ABS(transaction_quantity) ELSE 0 END) > 1000
  ORDER BY negative_qty DESC
  LIMIT 30;
```

### Printed Rows (Sample Top 5)
| item_bigint_key | reason_name | transaction_type_description | transaction_count | total_qty | negative_qty |
|---|---|---|---|---|---|
| -8877768888802117114 | (blank) | Subinventory Transfer | 24 | 0 | 69,264,172 |
| -8877768888802117114 | (blank) | Work in Process Material Issue | 75 | -24,042,659 | 24,042,659 |
| 2873850267132616711 | (blank) | Subinventory Transfer | 8 | 0 | 22,556,985 |
| -8877768888802117114 | (blank) | Transfer Order Interorganization Shipment | 2 | -15,216,450 | 15,216,450 |
| -8877768888802117114 | (blank) | Transfer Order Pick | 4 | 0 | 15,216,450 |

**Why Normally Invisible:** Transaction logs are processed to net quantities, and large reversals within orgs (transfers, WIP issues) appear as operational churn, not exceptions. Without focusing on magnitude of negative qty by item×reason, they blend into the ledger.

**Priority:** P2 (Operations — impacts on-hand accuracy, carrying cost, RCA)

**Good or Bad:** ⚠️ **Bad for business** — **69M units of negative movement** on single item signals either massive correction activity, data quality issues, or untracked shrink. Requires root-cause audit and controls hardening.

**End-User Lens:** ✅ Inventory manager: *"Which items have the most reversal activity and why?"* Operations: *"Are we losing visibility to inventory due to unaccounted transactions?"*

---

## Pattern 3: Country-of-Origin Concentration Risk (Supply Risk)

**Name:** High-value items clustered in a single source region with long lead times.

### Discovery SQL (READ-ONLY)
```sql
SELECT 
    global_planning_abc_code,
    country_of_origin,
    COUNT(DISTINCT item_bigint_key) as item_count
  FROM prod_edw.dimension.items_scd1
  WHERE item_status = "Active"
    AND country_of_origin IS NOT NULL
    AND country_of_origin != ""
    AND global_planning_abc_code IN ("A", "B")
  GROUP BY global_planning_abc_code, country_of_origin
  ORDER BY global_planning_abc_code, item_count DESC
  LIMIT 30;
```

### Printed Rows (Top 10 A+B Items by COO)
| global_planning_abc_code | country_of_origin | item_count |
|---|---|---|
| A | CN | 919 |
| A | US | 717 |
| A | VN | 643 |
| A | TW | 287 |
| A | TH | 266 |
| A | DE | 219 |
| B | (similar pattern) | ... |

**Why Normally Invisible:** Sourcing dashboards show individual supplier status, but **geographic concentration** of high-ABC items is invisible without dimensional joins. Risk surfaces only when a region experiences disruption (tariffs, pandemic, port closure).

**Priority:** P1 (Strategy/Supply Chain — existential supply risk)

**Good or Bad:** ⚠️ **Bad for business** — **919 of the A-class (highest-value) items** source from China alone; **643 from Vietnam**. Geopolitical risk, tariff sensitivity, lead-time brittleness. No resilience narrative visible in operational reporting.

**End-User Lens:** ✅ Supply chain director: *"Where is my concentration risk hiding?"* Buyer: *"Which SKUs have single-source-country exposure that need dual sourcing?"*

---

## Pattern 4: Extreme Order-Type Fan-Out (Grain Explosion & Aggregation Trap)

**Name:** Single product×org×date key splitting into thousands of rows via series, order_type, or other dimensions.

### Discovery SQL (READ-ONLY)
```sql
WITH row_count AS (
  SELECT 
    product_bigint_key,
    inventory_organization_bigint_key,
    date_key,
    COUNT(*) as row_count
  FROM prod_edw.fact.`20_supply_daily`
  WHERE plan_name = "20 Global Supply Plan"
    AND process_date = 20260829
  GROUP BY product_bigint_key, inventory_organization_bigint_key, date_key
)
SELECT 
  product_bigint_key,
  inventory_organization_bigint_key,
  date_key,
  row_count
FROM row_count
WHERE row_count > 5
ORDER BY row_count DESC
LIMIT 30;
```

### Printed Rows (Sample)
| product_bigint_key | inventory_organization_bigint_key | date_key | row_count |
|---|---|---|---|
| 3879620845706693458 | 776578178872804310 | 20260824 | 3,989 |
| -8141256580834757859 | 776578178872804310 | 20260831 | 2,979 |
| -2695149961318483181 | 776578178872804310 | 20260824 | 2,762 |
| -8290099280369104813 | 776578178872804310 | 20260824 | 2,521 |
| 8333420523890887862 | 776578178872804310 | 20260824 | 2,348 |

**Why Normally Invisible:** If a analyst writes `SELECT SUM(projected_available_balance) GROUP BY product, org` without accounting for the grain, they silently get correct totals but **miss that the fact table has a hidden ~3,989 rows per product×org×week**. Joining naively results in Cartesian products; aggregating without caution produces silent over-counts.

**Priority:** P3 (Data Governance / Analytics — impacts report accuracy, join logic)

**Good or Bad:** ⚠️ **Bad for analytics** — **3,989 rows for a single product×org×week** is a data modeling trap. Every aggregate query risks duplication unless JOIN logic is precise. No standard reporting layer to enforce safety.

**End-User Lens:** ✅ Data analyst / BI: *"Why do my PAB totals not match when I join to transactional tables?"* Engineer: *"What is the hidden grain of this fact table to prevent join bugs?"*

---

## Pattern 5: Minimum Order Quantity Waste (Forced Over-Ordering)

**Name:** Items with MOQ far exceeding near-term demand, forcing over-ordering and excess inventory.

### Discovery SQL (READ-ONLY)
```sql
WITH demand_sum AS (
  SELECT 
    s.series_bigint_key,
    s.item_number,
    s.minimum_order_quantity,
    SUM(sd.total_demand) as forecast_demand_4weeks
  FROM prod_edw.fact.`20_supply_daily` sd
  JOIN prod_edw.dimension.series_scd1 s ON sd.series_bigint_key = s.series_bigint_key
  WHERE sd.plan_name = "20 Global Supply Plan"
    AND sd.process_date = 20260829
    AND sd.date_key >= 20260901
    AND sd.date_key < 20261001
    AND s.minimum_order_quantity > 0
  GROUP BY s.series_bigint_key, s.item_number, s.minimum_order_quantity
)
SELECT 
  item_number,
  minimum_order_quantity,
  forecast_demand_4weeks,
  ROUND(minimum_order_quantity / NULLIF(forecast_demand_4weeks, 0), 2) as moq_to_demand_ratio
FROM demand_sum
WHERE minimum_order_quantity > forecast_demand_4weeks
ORDER BY moq_to_demand_ratio DESC
LIMIT 25;
```

### Printed Rows (Top 5)
| item_number | minimum_order_quantity | forecast_demand_4weeks | moq_to_demand_ratio |
|---|---|---|---|
| 48229316B | 50,000 | 1 | 50,000.0x |
| 030067701 | 500,000 | 12 | 41,667x |
| 48223209GPX | 20,000 | 1 | 20,000x |
| 06650135 | 100,000 | 6 | 16,667x |
| 525A00005 | 1,000 | 0.08 | 12,550x |

**Why Normally Invisible:** Purchase planning focuses on "can we buy enough," not "are we forced to buy too much." MOQ is a supplier-imposed constraint, but its **excess over actual demand** is buried in exceptions or demand exceptions, not surfaced as inventory risk.

**Priority:** P2 (Procurement / Inventory — impacts cash, carrying cost, obsolescence)

**Good or Bad:** ⚠️ **Bad for business** — **41,667x overage on 030067701**: forecast is 12 units in 4 weeks, but MOQ is 500,000. Supplier negotiation or substitution urgently needed; currently **forced to hold 249,994 excess units**.

**End-User Lens:** ✅ Buyer: *"Which suppliers' MOQs are driving unnecessary inventory?"* Planner: *"For which items should I negotiate lower MOQs or look for alternatives?"*

---

## Pattern 6: Plan vs Actual On-Hand Divergence (Plan Disconnected from Reality)

**Name:** Planned projected available balance vs actual on-hand inventory — large, unexplained gaps indicate plan stale or actual data corrupt.

### Discovery SQL (READ-ONLY)
```sql
WITH latest_plan AS (
  SELECT 
    product_bigint_key,
    inventory_organization_bigint_key,
    date_key,
    SUM(projected_available_balance) as planned_pab
  FROM prod_edw.fact.`20_supply_daily`
  WHERE plan_name = "20 Global Supply Plan"
    AND process_date = 20260829
    AND date_key = 20260831
  GROUP BY product_bigint_key, inventory_organization_bigint_key, date_key
),
actual_onhand AS (
  SELECT 
    item_bigint_key,
    inventory_organization_bigint_key,
    date_key,
    SUM(on_hand_qty) as actual_onhand
  FROM prod_edw.fact.inventory_days_on_hand
  WHERE date_key = 20260831
  GROUP BY item_bigint_key, inventory_organization_bigint_key, date_key
)
SELECT 
  lp.product_bigint_key,
  lp.inventory_organization_bigint_key,
  lp.planned_pab,
  ao.actual_onhand,
  ABS(lp.planned_pab - COALESCE(ao.actual_onhand, 0)) as divergence
FROM latest_plan lp
LEFT JOIN actual_onhand ao 
  ON lp.product_bigint_key = ao.item_bigint_key
  AND lp.inventory_organization_bigint_key = ao.inventory_organization_bigint_key
  AND lp.date_key = ao.date_key
WHERE ABS(lp.planned_pab - COALESCE(ao.actual_onhand, 0)) > 10000
ORDER BY divergence DESC
LIMIT 25;
```

### Printed Rows (Top 5)
| product_bigint_key | inventory_organization_bigint_key | planned_pab | actual_onhand | divergence |
|---|---|---|---|---|
| -8877768888802117114 | 5317431359558052302 | 34,280,918 | NULL | 34,280,918 |
| 2501169706210429064 | 5317431359558052302 | 32,643,233 | NULL | 32,643,233 |
| 2873850267132616711 | 5317431359558052302 | 11,585,095 | NULL | 11,585,095 |
| -8877768888802117114 | -5826737525596915694 | 11,461,893 | NULL | 11,461,893 |
| 66016195652433958 | 5317431359558052302 | 10,581,337 | NULL | 10,581,337 |

**Why Normally Invisible:** Plan accuracy reports compare plan to forecast, not to actual on-hand. Divergence becomes obvious only in detailed reconciliation queries; dashboards show "plan variance" which aggregates error and hides disconnects.

**Priority:** P1 (Operations/Control Tower — plan trust, demand signal)

**Good or Bad:** ⚠️ **Bad for business** — **25 items with >10M unit divergence between plan and actual**, many with **100% gap (plan exists, actual is NULL)**. Plan is disconnected from reality; cannot be trusted for supply decisions. Possible data freshness, data quality, or grain mismatch issue.

**End-User Lens:** ✅ Operations: *"Why is our plan not matching physical inventory?"* Finance: *"What is the true balance-sheet inventory value if plan and actual diverge this much?"*

---

## Pattern 7: Forecast Bias (Consistent Over- or Under-Planning)

**Name:** Systematic direction in plan-vs-actual variance across many historical periods.

### Key Finding (from data exploration)
The phantom demand pattern (Pattern 1) identifies products with consistent forecast > 0 but shipment ≈ 0 across multiple weeks. This suggests **systematic over-forecasting** for certain customer-product pairs — a bias signal.

**Why Normally Invisible:** Single-period variance reports show "miss %" but hide whether the miss is directional (always high, always low) or random. Bias emerges only by tracking the sign of error across time.

**Priority:** P2 (Demand Planning / S&OP — model calibration)

**Good or Bad:** ⚠️ **Bad for business** — Systematic over-forecast erodes planner credibility, drives excess inventory, and masks genuine demand signals.

---

## Ranking Table: Patterns by Actionability & Hidden-ness

| Rank | Pattern | Affected Volume / Severity | Normally Hidden By | Actionability | Business Impact |
|---|---|---|---|---|---|
| **1** | On-Hand vs Plan Divergence (P6) | 25+ items, >10M units divergence | Single-snapshot reporting, missing joins | HIGH — Data ops immediate fix | CRITICAL — Plan cannot be trusted |
| **2** | Extreme Fan-Out / Grain (P4) | ~3,989 rows per product×org×week | Aggregation & summary tables | MEDIUM — Affects analytics & joins | HIGH — Silent duplication risk in reports |
| **3** | MOQ Waste (P5) | 41,667x overage on single SKU | Supplier master, buried in exceptions | HIGH — Negotiation / substitution | HIGH — Direct cash impact, obsolescence risk |
| **4** | Phantom Demand (P1) | ~8.4M units across top 25 pairs | Aggregate forecast accuracy | HIGH — Demand validation, model audit | HIGH — Inventory carrying cost, forecast model breakdown |
| **5** | Inventory Reversals (P2) | 69M units negative movement | Transaction smoothing, reason codes blank | MEDIUM — RCA needed | MEDIUM — Shrink & data quality audit |
| **6** | COO Concentration (P3) | 919 A-items from China alone | Individual sourcing views, no geo aggregation | MEDIUM — Long-term resilience planning | CRITICAL — Geopolitical supply risk, not operational |
| **7** | Forecast Bias (P7) | Validated via Phantom Demand signal | Single-period variance, directional loss | MEDIUM — Model re-calibration | MEDIUM — Planning credibility, excess inventory |

---

## Implications for Milwaukee Tool Supply Chain

1. **Plan Disconnection is Critical:** Large divergences between plan PAB and actual on-hand suggest the 20 Global Supply Plan is either stale, populated with bad data, or joined improperly. Trust in planning is compromised.

2. **Phantom Demand is Widespread:** 8.4M units across 25 major customer-product pairs have standing forecast but zero fulfillment. Forecast model needs retraining, and demand validation workflow needs to escalate dead SKUs.

3. **Extreme Granularity Hides Risk:** 3,989 rows per product×org×week means every aggregation without explicit handling of series/order_type is a join trap. BI layer needs dimensional safety guards.

4. **MOQ Waste is Quantifiable & Actionable:** 41,667x overage signals supplier negotiations are not aligned with demand reality. Quick win: audit top 20 MOQ offenders and negotiate or substitute.

5. **Supply Concentration Requires Long-Term De-risking:** 919 A-items from China represent existential supply-chain risk invisible to daily operations but critical for strategy.

---

## Recommendations

- **Immediate (Week 1):** Audit Plan vs Actual divergence root cause; refresh plan or validate on-hand data integrity.
- **Short-term (Month 1):** Launch MOQ negotiation initiative for worst offenders; validate phantom demand SKUs for discontinuation or reforecasting.
- **Medium-term (Quarter 1):** Establish BI data safety layer to prevent grain-based join bugs; implement forecast bias detection model.
- **Long-term (Year 1):** Develop supply diversification strategy to reduce COO concentration; retrain demand forecasting models with bias correction.

---

*Report sourced from READ-ONLY queries on prod_edw.fact.20_supply_daily, prod_edw.fact.10_demand_daily, and related dimension tables. All patterns discovered via systematic query scanning; no production data written.*
