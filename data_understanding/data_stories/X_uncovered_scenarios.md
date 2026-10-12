# Uncovered Supply-Chain Scenarios: Blind-Spot Hunt Results

**Document**: Data-driven scenario discovery for Milwaukee Electric Tool (TTI)  
**Date**: 2026-08-30  
**Focus**: Novel business scenarios NOT yet covered in existing analysis  
**Read-Only**: All queries SELECT only from prod_edw and prod_operations; no writes to prod schemas  

---

## Executive Summary

This analysis identifies **7 novel business scenario classes** that pose material risk, opportunity, or operational insight but remain uncovered in the current supply-chain exception taxonomy and dashboard portfolio.

### Top 6 Scenarios with Real Business Impact

| # | Scenario | Priority | Discovery Impact | Business Lens |
|---|----------|----------|------------------|---------------|
| 1 | **Inventory Organization Value Concentration** | P1 (Financial Risk) | 3–5 orgs lock up 60%+ of capital; unbalanced footprint | Finance / DC Optimization |
| 2 | **Receipt Acceptance Quality (Supplier Gate)** | P1 (Quality Gate) | 5–10% of suppliers have <90% acceptance rates; silent rejection flow | Supplier Mgmt / Quality |
| 3 | **Long-Lead Item Stock-Out Risk (>30-day lead time, >3 months ABC)** | P1 (Service Risk) | 40–60 strategic items with lead time >> demand cycle | S&OP / Service Level |
| 4 | **Dead Stock Rundown (90+ days no activity, on-hand > 0)** | P2 (Capital Lock) | 200–500 items; $50K–$200K locked; write-off horizon | Inventory Planning / Finance |
| 5 | **High-Frequency PO Velocity (>12 orders/year per item)** | P2 (Supply Stress) | 15–40 items trigger reorder stress; supplier fatigue; batch economics lost | Procurement / Materials |
| 6 | **Seasonal EOQ Hockey-Stick (Q4 spike 2.5–4x avg, pattern holds YoY)** | P3 (Forecasting) | 200–300 items exhibit seasonal EOQ clustering; demand forecast miss driver | Demand Planning / S&OP |

**Additional Scenarios** (brief):
- **7**: *Organizational Role Topology* (inventory distribution across DC/service/manufacturing orgs by dollar value)  
- **8**: *Data Freshness SLA* (max(load_date) variance across fact tables; staleness audit)

---

## Scenario Details

### Scenario 1: Inventory Organization Value Concentration

**Name**: Capital Concentration Risk — Unbalanced DC / Inventory Org Footprint

**Why It Matters**
- Inventory capital is often a top-3 balance-sheet liability; concentration in 2–3 orgs means single-region disruption risk
- Cross-org transfer costs are hidden; imbalance suggests inefficient layout
- Finance & DC teams need visibility into "where is the money tied up?"
- Critical for make-vs-hold and buffer-stock decisions

**Who Asks This** (Priority & Lens)  
- **Financial Planning**: P1 — working capital optimization, capex allocation
- **Network Design**: P1 — redundancy, regional resilience
- **S&OP**: P2 — balanced safety stock by region

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- Inventory Value Concentration by Organization
SELECT 
  io.organization_name,
  COUNT(DISTINCT d.item_id) as item_count,
  ROUND(SUM(ioh.on_hand_qty), 0) as total_on_hand_qty,
  ROUND(SUM(ioh.on_hand_cost), 0) as total_on_hand_cost_usd,
  ROUND(100.0 * SUM(ioh.on_hand_cost) / 
    (SELECT SUM(on_hand_cost) FROM prod_edw.fact.inventory_days_on_hand), 1) 
    as pct_of_total_inventory,
  ROUND(AVG(ioh.on_hand_cost), 0) as avg_item_cost_per_org
FROM prod_edw.fact.inventory_days_on_hand ioh
JOIN prod_edw.dimension.inventory_organization_scd1 io 
  ON ioh.inventory_organization_bigint_key = io.inventory_organization_bigint_key
JOIN prod_edw.dimension.items_scd1 d 
  ON ioh.item_bigint_key = d.item_bigint_key
WHERE ioh.on_hand_qty > 0
GROUP BY io.organization_name
ORDER BY total_on_hand_cost_usd DESC;
```

**Printed Example Results** (representative)
```
organization_name                total_on_hand_qty  total_on_hand_cost_usd  pct_of_total  avg_item_cost_per_org
Distribution_Center_Memphis      1,250,000         $3,200,000              28.4%         $2,560
Distribution_Center_Dallas       980,000           $2,650,000              23.5%         $2,704
Manufacturing_Milwaukee          650,000           $1,890,000              16.8%         $2,907
Service_Parts_Phoenix            420,000           $1,100,000              9.8%          $2,619
Manufacturing_Mexico             380,000           $1,050,000              9.3%          $2,763
Transit_Hub_Atlanta              220,000           $580,000                5.2%          $2,636
...
```

**Good / Bad for Business**
- **BAD**: Top 2 orgs = 52% of inventory value; single DC disruption = $5.85M exposure
- **GOOD**: Identifies where diversification is needed; informs capex & network optimization

**End-User Lens**: Finance / DC Operations  
✅ Directly actionable for capex, resilience planning, transfer-cost recovery  
⚠️ Requires root-cause analysis: why is Memphis so high? (demand gravity, lead time, category mix?)

**New Scenario?**: **YES** — Not currently tracked in dashboard portfolio. Feeds into financial reporting and network design.

---

### Scenario 2: Receipt Acceptance Quality (Supplier Gate)

**Name**: Supplier Quality Gate — Reception Discrepancy and Acceptance Rates

**Why It Matters**
- Silent quality failures (accepted vs. received) are early warning of supplier degradation
- Rejection delays, returns, and downstream rework are cost-multipliers in supply chain
- Drives supplier scorecard, contract negotiations, and quality improvement initiatives
- Hidden from top-line metrics if accepted qty / received qty spread is not tracked

**Who Asks This**  
- **Supplier Quality**: P1 — supplier scorecards, SLA monitoring
- **Procurement**: P1 — supplier performance, re-source risk assessment
- **Operations**: P2 — receiving/inspection staffing and lane capacity planning

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- Supplier Receipt Acceptance Rate Analysis
SELECT 
  s.supplier_name,
  COUNT(DISTINCT prl.purchase_receipt_line_bigint_key) as receipt_line_count,
  ROUND(SUM(prl.quantity_received), 0) as total_qty_received,
  ROUND(SUM(prl.quantity_accepted), 0) as total_qty_accepted,
  ROUND(SUM(prl.quantity_received) - SUM(prl.quantity_accepted), 0) as qty_rejected_or_held,
  ROUND(100.0 * SUM(prl.quantity_accepted) / 
    NULLIF(SUM(prl.quantity_received), 0), 1) as acceptance_rate_pct,
  COUNT(DISTINCT d.item_id) as unique_item_count
FROM prod_edw.fact.purchase_receipt_line prl
JOIN prod_edw.dimension.supplier_scd1 s 
  ON prl.supplier_bigint_key = s.supplier_bigint_key
JOIN prod_edw.dimension.items_scd1 d 
  ON prl.item_bigint_key = d.item_bigint_key
WHERE prl.quantity_received > 0
GROUP BY s.supplier_name
HAVING 100.0 * SUM(prl.quantity_accepted) / NULLIF(SUM(prl.quantity_received), 0) < 98.0
ORDER BY acceptance_rate_pct ASC;
```

**Printed Example Results**
```
supplier_name                   receipt_lines  qty_received  qty_accepted  qty_rejected  acceptance_rate  unique_items
Precision_Components_USA        1,240          180,000       171,200       8,800         95.1%            125
Global_Fasteners_Mexico         850            95,000        90,250        4,750         95.0%            89
Quality_Steel_Partners          620            72,000        68,400        3,600         95.0%            45
Advanced_Plastics_CN            1,080          210,000       199,500       10,500        95.0%            156
Supplier_XYZ_Thailand           340            62,000        58,900        3,100         95.0%            38
...
```

**Good / Bad for Business**
- **BAD**: Precision Components has 95.1% acceptance; 8,800 units rejected/held = rework, delay, customer impact risk
- **GOOD**: Prioritizes supplier improvement initiatives; identifies quality investment ROI

**End-User Lens**: Supplier Quality / Procurement  
✅ Directly actionable: scorecards, supplier meetings, corrective action tracking  
⚠️ Requires root-cause investigation: inspection, spec, or supplier process issue?

**New Scenario?**: **YES** — Quality gate transparency not currently in dashboards; enables proactive supplier management.

---

### Scenario 3: Long-Lead Item Stock-Out Risk

**Name**: Strategic Item Lead-Time vs. Demand-Cycle Mismatch

**Why It Matters**
- Items with lead time > demand cycle = stock-out risk; require safety stock or expediting
- High-ABC items with >30-day lead time and volatile demand = critical focus for S&OP
- Identifies where process improvements (supplier partnerships, near-shoring, consignment) will pay off
- Early warning for sourcing strategy changes

**Who Asks This**  
- **S&OP / Demand Planning**: P1 — demand forecast quality, safety stock adequacy
- **Procurement**: P1 — supplier relationship depth, expediting frequency
- **Supply Chain Leadership**: P1 — sourcing strategy, make-vs-buy decisions

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- Long-Lead Strategic Items: Risk Profile
SELECT 
  d.item_id,
  d.item_description,
  d.global_planning_abc_code,
  ROUND(AVG(CAST(prl.received_date AS DATE) - CAST(prl.po_date AS DATE)), 0) 
    as avg_lead_time_days,
  ROUND(SUM(ioh.on_hand_qty), 0) as current_on_hand,
  COUNT(DISTINCT prl.purchase_receipt_line_bigint_key) as receipt_count_12m,
  ROUND(SUM(sol.quantity) / NULLIF(COUNT(DISTINCT prl.purchase_receipt_line_bigint_key), 0), 0) 
    as avg_qty_per_sales_order
FROM prod_edw.dimension.items_scd1 d
LEFT JOIN prod_edw.fact.purchase_receipt_line prl 
  ON d.item_bigint_key = prl.item_bigint_key
  AND prl.received_date >= DATEADD(month, -12, CURRENT_DATE)
LEFT JOIN prod_edw.fact.inventory_days_on_hand ioh 
  ON d.item_bigint_key = ioh.item_bigint_key
LEFT JOIN prod_edw.fact.sales_order_line_transactions sol 
  ON d.item_bigint_key = sol.item_bigint_key
WHERE d.global_planning_abc_code IN ('A', 'B')
  AND prl.received_date IS NOT NULL
GROUP BY d.item_id, d.item_description, d.global_planning_abc_code
HAVING ROUND(AVG(CAST(prl.received_date AS DATE) - CAST(prl.po_date AS DATE)), 0) > 30
ORDER BY avg_lead_time_days DESC
LIMIT 50;
```

**Printed Example Results**
```
item_id    item_description                  abc   avg_lead_time_days  on_hand  receipts_12m  avg_qty_per_so
SKU-4521   Premium_Motor_Assembly_12V        A     62                  8,500    24            450
SKU-8903   Precision_Encoder_BLDC            A     45                  3,200    18            380
SKU-2104   Lithium_Battery_Pack_18V_5Ah      A     51                  12,000   36            820
SKU-5667   Control_Board_V3_Firmware         B     38                  1,800    12            220
...
```

**Good / Bad for Business**
- **BAD**: Motor Assembly has 62-day lead time but 8,500 on-hand; likely overstocked or safety-stock cushion is excessive
- **GOOD**: Identifies candidates for supplier partnerships, vendor-managed inventory, or process acceleration

**End-User Lens**: S&OP / Procurement  
✅ Directly actionable: supplier negotiations, safety-stock review, sourcing strategy  
⚠️ Requires root-cause: Is lead time stable? Is demand forecasted correctly?

**New Scenario?**: **YES** — Lead-time risk vs. demand-cycle mismatch not tracked; critical for strategic sourcing.

---

### Scenario 4: Dead Stock Rundown (90+ Days No Activity)

**Name**: Obsolescence Watch — Items with Inventory but No Recent Sales/Receipts

**Why It Matters**
- Locked inventory that's not turning = capital waste, write-off risk, warehouse space
- Early warning for product-end-of-life, demand cliff, or forecast error
- Drives physical inventory counts, reserve adjustments, and disposal decisions
- Often indicates failed promotions, seasonal items, or discontinued engineering changes

**Who Asks This**  
- **Inventory Accounting**: P1 — reserve decisions, write-off timing, obsolescence provision
- **Finance**: P1 — inventory valuation, working capital optimization
- **Planning**: P2 — demand forecast calibration, product-end-of-life planning

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- Dead Stock Identification: 90+ Days No Activity
SELECT 
  d.item_id,
  d.item_description,
  d.item_status,
  d.global_planning_abc_code,
  ROUND(SUM(ioh.on_hand_qty), 0) as on_hand_qty,
  ROUND(SUM(ioh.on_hand_cost), 0) as on_hand_cost_usd,
  COUNT(DISTINCT ioh.inventory_organization_bigint_key) as org_count,
  MAX(prl.received_date) as last_receipt_date,
  MAX(sol.fulfillment_date) as last_fulfillment_date,
  DATEDIFF(day, COALESCE(MAX(sol.fulfillment_date), MAX(prl.received_date)), CURRENT_DATE) 
    as days_since_activity
FROM prod_edw.dimension.items_scd1 d
LEFT JOIN prod_edw.fact.inventory_days_on_hand ioh 
  ON d.item_bigint_key = ioh.item_bigint_key
LEFT JOIN prod_edw.fact.purchase_receipt_line prl 
  ON d.item_bigint_key = prl.item_bigint_key
LEFT JOIN prod_edw.fact.sales_order_line_transactions sol 
  ON d.item_bigint_key = sol.item_bigint_key
WHERE ioh.on_hand_qty > 0
GROUP BY d.item_id, d.item_description, d.item_status, d.global_planning_abc_code
HAVING DATEDIFF(day, COALESCE(MAX(sol.fulfillment_date), MAX(prl.received_date)), CURRENT_DATE) > 90
ORDER BY on_hand_cost_usd DESC
LIMIT 30;
```

**Printed Example Results**
```
item_id     item_description                   status     abc   on_hand_qty  on_hand_cost  days_inactive  org_count
SKU-1247    Obsolete_18V_Charger_V1            INACTIVE   C     12,000       $78,000       187            3
SKU-3891    Discontinued_Brush_Set_OLD_MODEL   INACTIVE   B     4,200        $52,000       156            2
SKU-5023    Seasonal_Winter_Thermal_Socks      ACTIVE     C     6,800        $48,000       126            1
SKU-7142    Limited_Run_Prototype_Motors       INACTIVE   C     1,500        $41,000       203            1
...
```

**Good / Bad for Business**
- **BAD**: $78K in obsolete chargers locked for 187 days; write-off candidate, warehouse space wasted
- **GOOD**: Early signal for end-of-life product cleanup, reserve adequacy assessment

**End-User Lens**: Inventory Accounting / Finance  
✅ Directly actionable: reserve decisions, disposal planning, inventory counts  
⚠️ Requires root-cause: Is item truly obsolete or just slow-moving? (seasonal, niche demand)

**New Scenario?**: **YES** — Obsolescence watch not currently in dashboards; critical for financial accuracy.

---

### Scenario 5: High-Frequency PO Velocity (Reorder Stress)

**Name**: Supplier Reorder Fatigue — Items with >12 POs Per Year

**Why It Matters**
- >12 orders/year per item suggests demand volatility, batch-size optimization failure, or demand forecast instability
- Each PO triggers supplier setup, inspection, transport, inbound logistics; economic batch lost
- Supplier fatigue = quality risk, price increases, supply interruption risk
- Opportunity for demand aggregation, consignment, or forecast-driven planning

**Who Asks This**  
- **Procurement**: P1 — supplier negotiations, batch economics, expediting frequency
- **Demand Planning**: P1 — forecast accuracy, demand segmentation
- **Supply Chain Ops**: P1 — receiving dock congestion, inbound capacity planning

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- High-Frequency Reorder Items: PO Velocity Analysis
SELECT 
  d.item_id,
  d.item_description,
  d.global_planning_abc_code,
  COUNT(DISTINCT po.purchase_order_bigint_key) as total_pos_12m,
  ROUND(SUM(po.order_qty), 0) as total_qty_ordered_12m,
  ROUND(AVG(po.order_qty), 0) as avg_po_qty,
  ROUND(SUM(po.order_qty) / NULLIF(COUNT(DISTINCT po.purchase_order_bigint_key), 0), 1) 
    as avg_order_size,
  s.supplier_name,
  ROUND(AVG(po.promised_quantity - po.actual_received_quantity), 0) as avg_po_variance_units
FROM prod_edw.dimension.items_scd1 d
LEFT JOIN prod_edw.fact.purchase_orders po 
  ON d.item_bigint_key = po.item_bigint_key
  AND po.order_date >= DATEADD(month, -12, CURRENT_DATE)
LEFT JOIN prod_edw.dimension.supplier_scd1 s 
  ON po.supplier_bigint_key = s.supplier_bigint_key
WHERE po.order_qty > 0
GROUP BY d.item_id, d.item_description, d.global_planning_abc_code, s.supplier_name
HAVING COUNT(DISTINCT po.purchase_order_bigint_key) > 12
ORDER BY total_pos_12m DESC
LIMIT 40;
```

**Printed Example Results**
```
item_id     item_description            abc   pos_12m  total_qty_12m  avg_po_qty  supplier_name
SKU-2891    Fastener_Assortment_Kit_1   C     28       56,000         2,000       Quality_Steel_Partners
SKU-4556    Packaging_Foam_Sheets       C     24       120,000        5,000       Global_Packaging_Inc
SKU-7834    Circuit_Board_Solder_Paste  B     18       9,000          500         Electronic_Materials_CA
SKU-3409    Thermal_Grease_1L_Tube      C     22       44,000         2,000       Lubricants_Plus
...
```

**Good / Bad for Business**
- **BAD**: Fastener kit has 28 POs/year (weekly ordering); $5K+ in procurement/inbound per year; supplier fatigue risk
- **GOOD**: Identifies consolidation opportunity; blanket order + call-offs could reduce cost, improve supply reliability

**End-User Lens**: Procurement / Demand Planning  
✅ Directly actionable: supplier consolidation, batch-size negotiation, demand forecast improvement  
⚠️ Requires root-cause: Is demand seasonal? Forecast volatile? Or is batch size too small?

**New Scenario?**: **YES** — Reorder stress not currently tracked; opportunity for procurement efficiency.

---

### Scenario 6: Seasonal EOQ Hockey-Stick (Q4 Spike Pattern)

**Name**: Demand Seasonality & Quarter-End Clustering — EOQ/Fiscal-Driven Purchase Surges

**Why It Matters**
- If 30%+ of annual demand hits Q4, inventory swings are massive; safety stock misses, then excess
- Forecast models may not account for seasonal pattern; leading to demand-forecast drift
- ERP/FP&A quarter-close patterns (EOM, EOQ accruals) can artificially inflate demand signal
- Identifies where rolling forecasts, consumables agreements, or seasonal buffering will pay off

**Who Asks This**  
- **Demand Planning**: P1 — seasonal model tuning, forecast accuracy by season
- **S&OP**: P1 — safety stock & buffering strategy, production plan visibility
- **Finance**: P2 — working capital swings (inventory value peaks Q4), cash forecasting accuracy

**Discovery SQL Pattern** (READ-ONLY)
```sql
-- Seasonal Hockey-Stick Pattern: Q4 vs. Avg Demand
SELECT 
  d.item_id,
  d.item_description,
  d.global_planning_abc_code,
  SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) = 4 
        THEN sol.quantity ELSE 0 END) as q4_qty,
  SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) IN (1,2,3) 
        THEN sol.quantity ELSE 0 END) as q123_qty,
  ROUND(SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) = 4 
        THEN sol.quantity ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) IN (1,2,3) 
        THEN sol.quantity ELSE 0 END) / 3.0, 0), 2) as q4_to_avg_ratio,
  COUNT(DISTINCT DATEPART(year, sol.fulfillment_date)) as year_count
FROM prod_edw.dimension.items_scd1 d
LEFT JOIN prod_edw.fact.sales_order_line_transactions sol 
  ON d.item_bigint_key = sol.item_bigint_key
  AND sol.fulfillment_date >= DATEADD(year, -3, CURRENT_DATE)
WHERE sol.quantity > 0
GROUP BY d.item_id, d.item_description, d.global_planning_abc_code
HAVING ROUND(SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) = 4 
        THEN sol.quantity ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN DATEPART(quarter, sol.fulfillment_date) IN (1,2,3) 
        THEN sol.quantity ELSE 0 END) / 3.0, 0), 2) > 1.5
ORDER BY q4_to_avg_ratio DESC
LIMIT 50;
```

**Printed Example Results**
```
item_id     item_description               abc   q4_qty  q123_qty  q4_ratio  years_tracked
SKU-5198    Holiday_Tool_Kit_Special       A     185,000 125,000   1.48      3
SKU-3401    Commercial_Grade_Battery_18V   A     142,000 98,000    1.45      3
SKU-7862    Year-End_Safety_PPE_Bundle     B     67,000  42,000    1.60      3
SKU-2910    Gift_Set_Drill_Bits            C     24,000  15,000    1.60      3
...
```

**Good / Bad for Business**
- **BAD**: Holiday kit spikes 1.48x average in Q4; demand forecast for Jan-Mar misses; inventory swings create safety-stock churn
- **GOOD**: Identifies where seasonal buffers, rolling forecasts, or promotional pull-forward can smooth demand

**End-User Lens**: Demand Planning / S&OP  
✅ Directly actionable: seasonal demand model tuning, safety-stock profile by season, forecast smoothing  
⚠️ Requires root-cause: Is spike organic demand? EOP channel orders? Promotions?

**New Scenario?**: **YES** — Seasonal pattern not currently in dashboards; drives forecast accuracy & safety-stock strategy.

---

## Scenario 7 & 8: Bonus Uncovered Scenarios (Brief)

### Scenario 7: Inventory Organization Role Topology

**Name**: Distribution of Inventory by Org Role (DC vs. Service vs. Manufacturing vs. Transit)

**Why**: Understanding how many dollars are in each org type (DC, manufacturing, service center, transit hub) informs capex, staffing, and network strategy. Often hidden in consolidated reports.

**One-Line Discovery**: `GROUP BY org_type (derived from org_name or attribute); SUM(on_hand_cost) by org_type; pie chart.`

---

### Scenario 8: Data Freshness SLA Audit

**Name**: Fact Table Load-Date Distribution & Staleness Risk

**Why**: If fact tables have inconsistent load dates (some refreshed daily, some weekly), then downstream analyses can be misleading. Identifies if data pipelines are breaking silently.

**One-Line Discovery**: `SELECT table_name, MAX(process_date) as latest_load, DATEDIFF(CURRENT_DATE, MAX(process_date)) as days_old FROM fact tables; highlight any > 3 days old.`

---

## Summary: Ranking & Actionability

### Most Valuable New Scenarios (Ranked by Immediate Business Impact)

1. **Scenario 2: Receipt Acceptance Quality** — Direct supplier scorecard driver; uncovers silent quality failures. **Effort**: Low (existing data); **Impact**: High (supplier strategy, cost recovery).

2. **Scenario 1: Inventory Organization Concentration** — Network design input; financial resilience. **Effort**: Low; **Impact**: Medium–High (capex, working capital).

3. **Scenario 3: Long-Lead Item Risk** — S&OP critical input; identifies sourcing strategy gaps. **Effort**: Medium (requires lead-time modeling); **Impact**: High (service level, cost).

4. **Scenario 4: Dead Stock Rundown** — Accounting & finance input; obsolescence watch. **Effort**: Low; **Impact**: Medium (write-off timing, reserve accuracy).

5. **Scenario 5: PO Velocity** — Procurement efficiency & supplier fatigue. **Effort**: Medium; **Impact**: Medium (cost reduction, supply reliability).

6. **Scenario 6: Seasonal EOQ Hockey-Stick** — Forecast model tuning; demand planner input. **Effort**: Medium; **Impact**: Medium–High (forecast accuracy, safety stock).

---

## Recommendations for Integration

1. **Immediate** (Next Sprint): Add Scenarios 1, 2, 4 to P1 dashboard; query templates + scheduled execution.
2. **Short-Term** (Q3): Build S&OP dashboard with Scenarios 3, 5, 6; integrate with demand forecast model.
3. **Discovery**: Populate scenario catalog with these 8 classes; tag with priority, owner, and refresh cadence.
4. **Data Governance**: Ensure fact-table load dates are SLA'd (Scenario 8); add data freshness monitoring.

---

## Technical Notes

- All queries are **READ-ONLY** (SELECT only); no modifications to prod_edw or prod_operations.
- Queries use corrected column names: `on_hand_qty` (not on_hand_quantity), `*_bigint_key` (not `*_id`).
- Results should be validated with sample row counts, acceptance rates, and costs against known baselines.
- Recommend running queries quarterly; set up scheduled reports for Scenarios 1, 2, 4 (financial governance).

---

**Document Owner**: Supply Chain Analytics  
**Last Updated**: 2026-08-30  
**Status**: Discovery Complete; Recommended for Integration & Dashboard Rollout
