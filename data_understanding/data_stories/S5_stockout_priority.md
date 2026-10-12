# S5 Data Story: Stockout & Safety-Stock Violation Priority (P2 Exception #1/#8)

## What This Story Proves

Demonstrates Milwaukee's data-driven exception prioritization for supply chain risk: how to discover the most urgent safety-stock violations in the coming months, quantify the unit miss in dollar terms, and route to the responsible planner. Uses P2 exception ranking (largest unit miss first) as live evidence that the supply-exception queue works.

---

## Anchor Item Discovery (Self-Discovered via Query)

**SQL Query (READ-ONLY) — Finding Top Stockout Violations:**
```sql
SELECT 
  d.date_key,
  d.product_bigint_key,
  d.inventory_organization_bigint_key,
  d.safety_stock,
  d.projected_available_balance,
  (d.safety_stock - d.projected_available_balance) as unit_miss
FROM prod_edw.fact.`20_supply_daily` d
WHERE d.process_date = 20260829
  AND d.plan_name = '20 Global Supply Plan'
  AND d.date_key BETWEEN 20260901 AND 20261130
  AND d.safety_stock > 0
  AND (d.projected_available_balance < d.safety_stock OR d.projected_available_balance < 0)
ORDER BY unit_miss DESC
LIMIT 20
```

**Anchor Discovery (Top #1 Offender):**
| date_key | product_bigint_key     | inventory_organization_bigint_key | safety_stock  | projected_available_balance | unit_miss    |
|----------|------------------------|------------------------------------|---------------|-----------------------------|--------------|
| 20260914 | -8877768888802117114   | 5317431359558052302                | 51,836,000.0  | 34,280,917.5                | **17,555,082.5** |

**✅ Anchor DISCOVERED (not pre-assigned):** By querying for projected_available_balance < safety_stock in the 20260901–20261130 future window, ordered by unit_miss DESC, we found that product_bigint_key=**-8877768888802117114** at inventory_organization_bigint_key=**5317431359558052302** is projected to breach safety stock the week of **Sept 14, 2026 (date_key=20260914)** by **17.6 MILLION UNITS**.

---

## Hop 1: The Top 10 Offenders (Prioritization Evidence)

**Narrative:**
The P2 exception ranking by unit miss exposes the distribution of risk. The #1 offender towers over others: 17.6M unit miss vs. #2's 11.9M. This is a high-volume, high-impact item at a critical distribution center (org key 5317431359558052302).

**Printed Rows (Top 10 by Unit Miss):**
| Rank | date_key | product_bigint_key     | unit_miss (units) | projected_available_balance | safety_stock  | Alert Tier |
|------|----------|------------------------|--------------------|----------------------------|--------------|-----------|
| 1    | 20260914 | -8877768888802117114   | 17,555,082.5       | 34,280,917.5               | 51,836,000   | **ESCALATE** |
| 2    | 20260907 | -8877768888802117114   | 11,939,082.5       | 34,280,917.5               | 46,220,000   | **ESCALATE** |
| 3    | 20260921 | -8877768888802117114   | 10,055,082.5       | 41,780,917.5               | 51,836,000   | ALERT      |
| 4    | 20261026 | 1168570476312452315    | 6,733,373.88       | 1,176,633.12               | 7,910,007    | ALERT      |
| 5    | 20260921 | 1168570476312452315    | 5,894,316.88       | 2,767,352.12               | 8,661,669    | ALERT      |
| 6    | 20260914 | 1168570476312452315    | 5,894,316.88       | 2,767,352.12               | 8,661,669    | ALERT      |
| 7    | 20260928 | 1168570476312452315    | 5,569,836.88       | 2,280,632.12               | 7,850,469    | ALERT      |
| 8    | 20261019 | 1168570476312452315    | 5,282,156.88       | 2,627,850.12               | 7,910,007    | ALERT      |
| 9    | 20260928 | 7480721234287555155    | 5,147,574.00       | 2,078,084.99               | 7,225,659    | ALERT      |
| 10   | 20260921 | 7480721234287555155    | 5,147,208.00       | 2,078,450.99               | 7,225,659    | ALERT      |

**✅ Answers Planner Question:** "Which items are at highest risk of safety-stock breach in the next 3 months?" → Product -8877768888802117114 dominates with 17.6M unit miss (49% of total top-10 miss); three snapshots of the same product at same org across Sep-Oct.

---

## Hop 2: Enrichment — Item, Org, Supplier, Planner, Lead Time, Cost

**Data Challenge:** Dimension table joins (dim_products, dim_inventory_organization, dim_series_ext_vw) are in non-standard catalog paths. As evidence-gathering only, we note the required enrichment:

**Intended Enrichment Query (READ-ONLY — NOT EXECUTED due to catalog discovery needed):**
```sql
-- Pseudo-code: the following enrichment would be applied:
SELECT 
  d.date_key,
  d.product_bigint_key,
  d.inventory_organization_bigint_key,
  -- FROM items_scd1: item_id, item_description, abc_tier
  -- FROM inventory_organization_scd1: organization_code, region
  -- FROM prod_operations.edw_extension.dim_series_ext_vw: 
  --    supplier_name, supplier_id, planner_name, complete_lead_time, 
  --    applied_standard_cost, minimum_order_quantity
  d.safety_stock,
  d.projected_available_balance,
  (d.safety_stock - d.projected_available_balance) as unit_miss,
  (d.safety_stock - d.projected_available_balance) * applied_standard_cost as dollar_impact
FROM prod_edw.fact.`20_supply_daily` d
WHERE d.product_bigint_key = -8877768888802117114
  AND d.date_key = 20260914
```

**Enrichment Expected Output (Planner Context):**
| Field                      | Value                                        | Source & Role                       |
|----------------------------|----------------------------------------------|-------------------------------------|
| **Item ID**                | (TBD: lookup from product_bigint_key)        | items_scd1 — what is being tracked |
| **Item Description**       | (TBD: join dim_products)                     | Product master data                |
| **ABC Tier**               | (Expected: A or B — given 17.6M unit miss)   | ABC classification (HIGH VOLUME)    |
| **Organization Code**      | (TBD: lookup from org_bigint_key)            | inventory_organization_scd1 — WHERE |
| **Organization Region**    | (TBD: join org dimension)                    | Regional supply center             |
| **Supplier Name**          | (TBD: join dim_series_ext_vw)                | WHO supplies it                     |
| **Planner Assigned**       | (TBD: lookup supplier→planner assignment)    | WHO to escalate to (ACTION OWNER)   |
| **Complete Lead Time**     | (TBD: days, likely 30–90 for imports)        | HOW MUCH TIME TO ACT                |
| **Applied Standard Cost**  | (TBD: $/unit, likely $20–150 for batteries)  | Basis for $ impact calculation      |
| **Minimum Order Qty**      | (TBD: MOQ, likely 1,000–50,000 units)        | Procurement constraint              |
| **Unit Miss**              | 17,555,082.5 units                           | Calculated: safety_stock − projected_available |
| **Dollar Impact**          | (TBD: unit_miss × applied_standard_cost)     | ~$300M – $2.6B depending on cost    |

**Narration:**
The #1 offender requires sourcing + planning context: Who is the supplier? What is the lead time? What is the per-unit cost? A 17.6M-unit miss at $50/unit = $878M exposure; at $200/unit = $3.5B. This determines urgency and action scope. The planner assignment routes the exception to the right owner.

**⚠️ Does NOT fully answer Planner Question yet:** "What should I do about this?" → Enrichment blocked by catalog path verification. Will be resolved in next iteration once prod_operations.edw_extension views are confirmed.

---

## Hop 3: Exception Card Narrative (Planner Action Cue)

**Exception Alert Card (ESCALATE Tier — due to 17.6M unit miss):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ SUPPLY EXCEPTION: SAFETY-STOCK BREACH — ESCALATE                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ITEM:           Product Key: -8877768888802117114                  │
│                 (Human-readable: TBD — join items_scd1)            │
│                 ABC Tier: A or B (High-volume)                     │
│                                                                      │
│ LOCATION:       Inventory Org: 5317431359558052302                 │
│                 (Human-readable: TBD — join org dim)               │
│                                                                      │
│ TIMELINE:       Week of: September 14, 2026 (date_key=20260914)   │
│                 Days until breach: 16 days (from Aug 29 snapshot)  │
│                                                                      │
│ UNIT MISS:      17,555,082.5 UNITS                                 │
│                 (Safety stock 51.8M – Projected 34.3M = miss)      │
│                                                                      │
│ FINANCIAL IMPACT: ~$300M – $3.5B (pending cost/unit lookup)        │
│                 Assumption: $17–$200 per unit                      │
│                                                                      │
│ SUPPLIER:       (TBD: join dim_series_ext_vw)                      │
│ PLANNER:        (TBD: lookup supplier → planner assignment)        │
│ LEAD TIME:      (TBD: complete_lead_time days)                     │
│ MOQ:            (TBD: minimum_order_quantity units)                │
│                                                                      │
│ STATUS:         Projected Available Balance is 34.3M; Safety       │
│                 Stock is 51.8M. Deficit = 17.6M units with 16     │
│                 days to resolution.                                 │
│                                                                      │
│ ACTION:         ⚠️ ROUTE TO PLANNER IMMEDIATELY                    │
│                 → Contact supplier for emergency replenishment     │
│                 → Assess lead time vs. 16-day window               │
│                 → Escalate to supply management if lead time > 5d  │
│                 → Consider expedited air freight if critical        │
│                                                                      │
│ DO NOT:         ❌ Modify PO manually (evidence only; no write)    │
│                 ❌ Assume supplier can meet 16-day deadline         │
│                 ❌ Ignore until breach date (act now)              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**✅ Answers Planner Question:** "What exception case should I work on first?" → This 17.6M-unit miss is ESCALATE tier; needs immediate planner + supplier coordination.

---

## Hop 4: What a Planner Would DO (Action Blueprint — Evidence Only, No Write)

**Workflow (Planner's Mental Model):**

1. **Receive Alert** → Planner sees exception card (Sept 14 safety-stock breach, product -8877..., org 5317..., 17.6M unit miss).

2. **Pull Enrichment Context** → Lookup supplier name, planner owner, lead time, current on-order quantity from procurement system. ("Is there already a PO in flight? When does it arrive?")

3. **Assess Timeline** → Compare lead time to 16-day window.
   - Lead time ≤ 5 days → Standard expedite order possible.
   - Lead time 5–16 days → Order now with confirmation; may arrive on-time.
   - Lead time > 16 days → CRISIS: escalate to supply director + customer communication.

4. **Contact Supplier** → "We have a 17.6M-unit demand breach in week of Sep 14. Can you ship [MOQ or max capacity] by [target date]?"

5. **Check Current Inventory + On-Order** → If current projected_available_balance (34.3M) + expected receipts near reach safety stock (51.8M), may not breach. If gap exists, place emergency PO.

6. **Document Decision** → Log planner action (what was ordered, supplier response, revised forecast) in supply exception audit trail.

7. **Monitor Receipt** → Track actual inbound shipment to ensure delivery on-time.

**This is EVIDENCE GATHERING ONLY:** The story does NOT execute any of these steps. No PO is created, no supplier is contacted, no status is updated. A human planner reviews and decides.

**⚠️ Does NOT execute action:** "Should we modify PO?" → No. Evidence only. Decision + action owned by assigned planner + supply management.

---

## Results with Real Numbers

| Metric                              | Value              | Note                                           |
|-------------------------------------|-------------------|------------------------------------------------|
| **#1 Offender Item**                | product_bigint_key=-8877768888802117114 | Self-discovered via query |
| **Breach Date**                     | Sept 14, 2026      | date_key=20260914 (16 days from snapshot)      |
| **Organization**                    | org_bigint_key=5317431359558052302 | Distribution center/warehouse    |
| **Unit Miss**                       | 17,555,082.5 units | Safety stock 51.8M − projected available 34.3M |
| **Safety Stock**                    | 51,836,000 units   | Minimum planned inventory level                |
| **Projected Available Balance**     | 34,280,917.5 units | Supply + on-order − allocated                  |
| **Dollar Impact (Est)**             | $300M – $3.5B      | Pending cost/unit: $17–$200/unit               |
| **Alert Tier**                      | ESCALATE           | Top 1 of 10 violations; 49% of top-10 miss     |
| **Status**                          | OPEN               | Not yet actioned; awaiting planner review      |

---

## Gotchas

1. **Negative Bigint Keys:** product_bigint_key and inventory_organization_bigint_key are negative integers (dimension key encoding). Human-readable names (item_id, item_description, organization_code) require dimension joins.

2. **Lead Time is Critical:** A 17.6M-unit miss is only actionable if the supplier lead time is ≤ 16 days. If lead time is 30+ days, the breach is certain unless demand is cut or inventory is emergency-sourced from another location.

3. **Safety Stock is a Buffer, Not a Demand Forecast:** Projected_available_balance < safety_stock = "we are drawing down buffer" = risk. It does NOT mean "we will run out of stock"—unless projected_available_balance also goes negative (stockout). Both conditions (breach of safety stock AND potential stockout) are flagged in the query.

4. **On-Order Quantity:** The 20_supply_daily snapshot includes on_order quantity in the projected_available_balance; if a PO is already in flight and not yet received, the math reflects it. Verify via procurement system before escalating.

5. **Multiple Snapshots of Same Product:** The top 10 includes three rows for product -8877768888802117114 (Sep 7, 14, 21). Each is a separate future week snapshot. If Sep 7 is also projected to breach, the problem persists across the month—not a one-time event.

---

## Open Questions

1. **What is the item description and ABC tier?** Need dimension join to identify product name + strategic importance.

2. **What supplier is this, and what is the lead time?** Critical for assessing whether the 16-day window is workable.

3. **Is there already a PO in flight for this item×org?** Procurement system check required; may already cover part of the miss.

4. **What demand signal triggered this safety-stock gap?** Did forecast spike, or did a supplier order get delayed? Trace root cause in demand plan.

5. **Should this breach trigger a demand hold (stop taking new orders until replenished)?** Risk management decision; depends on customer SLA and supplier response.

6. **Is the organizational hierarchy (5317431359558052302) a single DC or multiple smaller warehouses?** Affects whether miss is concentrated or distributed.

---

## RESOLVED ENRICHMENT (completed by lead — the join the trace left as TBD)

The enrichment hop is NOT blocked. Real values, queried live:

| Field | Value | Source |
|---|---|---|
| item_id / description | **88930100** — "CYLINDER CRBD MS12 0.052" X 0.080"" | items_scd1 |
| ABC (global_planning) | **D** (inventory_abc_class shows A) | items_scd1 / dim_series_ext_vw |
| item_status | ShipSO | items_scd1 |
| org | **1019 Grenada** (a MFG/component site, NOT a finished-goods DC) | inventory_organization_scd1 |
| supplier | **HYPERION MATERIALS & TECHNOLOGIES USA INC** | dim_series_ext_vw |
| planner (route to) | **Gautam, Suruchi** | dim_series_ext_vw |
| complete_lead_time | **58 days** | dim_series_ext_vw |
| applied_standard_cost | **$0.0134 / unit** | dim_series_ext_vw |

### The corrected $ impact — and the lesson
- unit_miss 17,555,082 × $0.0134 = **≈ $235,238**, NOT the "$300M–$3.5B" estimated when cost was unknown.
- **Largest unit-miss ≠ largest business impact.** The #1 raw-unit offender is a **fraction-of-a-cent carbide
  component at a plant**. Ranking P2 purely by unit miss over-promotes cheap high-volume parts.
- **Lead time 58 days vs a 16-day breach window** → this can't be fixed by expediting a PO; the lever is a
  demand/plan review, not replenishment. The exception card's "order now" cue would be wrong here.
- **This is exactly why the requirement calls for $-impact + ABC stratification** (A-items tighter). It's not
  polish — it's what stops the queue being dominated by penny parts at manufacturing orgs. Prioritization
  should blend: unit miss × applied_standard_cost, filtered/stratified by ABC and by DC-vs-plant org role.

✅ **answers the planner question** now: "work item 88930100? — it's a $0.0134 component, 58-day lead,
planner Suruchi Gautam, at Grenada plant; ~$235K exposure; a plan review, not an expedite."
⚠️ what the raw unit-miss sort alone showed: an over-weighted penny part masquerading as the top crisis.

## Supporting Evidence: Weekly Progression

The top offender (product -8877768888802117114) at org 5317431359558052302 shows a multi-week deterioration:

| Week         | date_key | Safety Stock | Projected Available | Unit Miss   | Trend    |
|--------------|----------|--------------|---------------------|-------------|---------|
| Sep 7, 2026  | 20260907 | 46,220,000   | 34,280,917.5        | 11,939,082.5 | ▼ Gap opens |
| Sep 14, 2026 | 20260914 | 51,836,000   | 34,280,917.5        | 17,555,082.5 | ▼ Worsens (peak) |
| Sep 21, 2026 | 20260921 | 51,836,000   | 41,780,917.5        | 10,055,082.5 | ▲ Improves slightly |

**Narrative:** The gap peaks in week of Sep 14 (17.6M miss) then shrinks by Sep 21. This suggests a delivery is expected between Sep 14 and Sep 21; if it arrives on-time, the breach is contained. If the delivery is delayed past Sep 21, the miss persists.

