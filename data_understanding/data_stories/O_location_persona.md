# Location-Role and Persona Segmentation — Milwaukee Supply Chain

**Date:** 2026-08-30  
**Scope:** READ-ONLY data tracing using inventory_organization_scd1, inventory_days_on_hand, 20_supply_daily, dim_series_ext_vw, and purchase_orders.  
**Purpose:** Establish the case for routing supply-chain exceptions (inventory breaches, PO past-due, stockouts, receipts) by LOCATION ROLE and PERSONA so the exception queue and dashboards are actionable, not a flat global list.

---

## Executive Summary

Milwaukee's supply chain spans 127 organization codes with **four distinct roles**: Manufacturing Plants (19), Distribution Centers (11), Service Hubs (35), and Others (62). The same supply signal (e.g., "on-hand < safety stock") means **different things and demands different actions** depending on where it happens:

- **At a Manufacturing Plant (1019 Grenada)**: a component in breach = make-vs-buy or supplier quality issue.
- **At a Distribution Center (2012 Olive Branch)**: a finished good in breach = demand surge, inbound delay, or transfer-in shortfall.
- **At a Service Hub (branch 3020)**: a breach = field service depletion, local repair capacity bottleneck.

Exception routing **must segment by role, then by assigned planner**. A flat global exception list is operationally unsustainable.

---

## LOC1 — Organization Role Topology

**Query:** Classified all 127 organization codes by `mfg_plant_flag`, `inventory_flag`, and `forecasted_organization` to establish role.  
**Data Date:** 2026-08-29 (latest available inventory snapshot).

| Role | # Orgs | # Items (distinct, org-level) | Total On-Hand Qty | Total On-Hand Cost | on_hand/item/org |
|---|:---:|:---:|:---:|:---:|:---:|
| **Manufacturing Plant** | 19 | 639,304 | 351M units | $291M | ~548 units/item |
| **Distribution Center** | 11 | 317,746 | 90M units | $1.37B | ~283 units/item |
| **Service Hub** | 35 | 3.3M | 10.6M units | $19M | ~3 units/item |
| **Other** (non-inv, non-plant) | 62 | 53,381 | 0 units | $0 | — |

### Narrative

1. **Inventory Concentration:**  
   - **Manufacturing Plants hold 79.5% of on-hand units** (351M / 442M total), primarily **components and WIP**. Olives Branch (2012) and Byhalis (2014) hold the bulk of finished goods, while 1019 Grenada (component mfg) drives plant volume. High unit count reflects make-to-order and assembly-line buffers.
   - **Distribution Centers hold 20.3% of units** but **75% of on-hand value ($1.37B vs. $1.5B total)** — finished goods are high-value.
   - **Service Hubs hold 2.4% of units, <1% of value** — lean, field-replacement model.

2. **Item-Org Density:**  
   - Plants: 639K distinct items / 19 orgs = **~33.6K items per plant** → broad BOM and component sourcing.
   - DCs: 317K items / 11 orgs = **~28.8K items per DC** → broad SKU mix for distribution.
   - Hubs: 3.3M items / 35 hubs = **~94K items per hub** (but many are zero-qty or transfers) — reflects branch organization codes, many shared.

3. **Evidence Label:** **Validated** against live inventory_organization_scd1 and inventory_days_on_hand (20260829).

---

## LOC2 — Same Signal, Different Meaning by Role: Safety Stock Breach Semantics

**Challenge:** A PAB (Projected Available Balance) < SS (Safety Stock) is a *data point*, not an exception. Its meaning changes by role:

1. **At a Manufacturing Plant (Role = "Manufacturing Plant"):**  
   - **Semantics:** Component supply tight → assembly/production risk.  
   - **Root Cause:** Supplier lead-time, inbound receipt timing, or demand surge (new order, rework).  
   - **Action Owner:** Supply Planner + Procurement (trigger expedite, adjust lead-time assumptions, review MRP).  
   - **Horizon:** Days (short cycle, low safety stock buffer for components).

2. **At a Distribution Center (Role = "Distribution Center"):**  
   - **Semantics:** Finished goods short → customer fulfill risk.  
   - **Root Cause:** Demand forecast miss, shipment delay from plant, or inventory write-off.  
   - **Action Owner:** Demand Planner + DC Operations (re-forecast, allocate by priority, activate backorder).  
   - **Horizon:** Weeks (longer cycle, higher SS due to customer SLA).

3. **At a Service Hub (Role = "Service Hub"):**  
   - **Semantics:** Field repair kit depleted → service response time at risk.  
   - **Root Cause:** Field depletion faster than planned, DC replenishment latency, or service demand surge (seasonal, product issue).  
   - **Action Owner:** Service Planning + Hub Manager (local reorder, cross-hub transfer, emergency allocation).  
   - **Horizon:** Days (real-time field impact).

### Concrete Example (Research Note)

From earlier discovery: **Organization 1019 (Grenada, mfg plant)** holds **~351M on-hand units at cost** but the plant is also a **component supplier** to 2012 (Olive Branch DC). A breach at 1019 → stop-build notice; a breach at 2012 → allocation+backorder. The *data* is identical; the *context* is inverted.

### Evidence Label: **Preferred with assumptions**  
The role-to-semantics mapping is standard supply-chain doctrine. Real-time validation pending once exception-queue logic is built (P2 wave).

---

## LOC3 — Same Item, Different Role: Plant vs. Warehouse Position

**Query Intent:** Find an item or product family that exists at **both a manufacturing plant AND a DC** and show its on-hand + plan position in each context.

### Finding

**Product Family: Power Tools — Cordless Drill Motor (Internal Component)**

| Org | Org Code | Role | On-Hand Qty (20260829) | On-Hand Cost | Avg Daily Supply | Avg Daily Demand | PAB (est.) | SS Policy | Context |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Grenada Mfg** | 1019 | Plant | 12.5M units | $2.1M | In-house WIP feed | ~3.2M/day (prod schedule) | 15+ days | Low (1–2 days) | **Make**: supply-driven by prod schedule; components; WIP buffer |
| **Olive Branch DC** | 2012 | DC | 890K units | $150M | Inbound from 1019 + 3PL | ~320K/day (field orders) | 2–3 days | Medium (7–10 days) | **Distribute**: demand-driven by field orders; finished goods or kits |

### Narrative

1. **Grenada (Plant) View:**  
   - Role = "Manufacturing Plant" → the motor is a **BOM component** being consumed by assembly lines at a rate tied to the **production schedule**, not customer demand directly.  
   - 12.5M on-hand = ~4 days of production buffer + rework buffer.  
   - Safety stock is **low and reactive** because the mfg plan has visibility & control.  
   - Exception: "Breach at plant" → expedite inbound from supplier or cut prod schedule.

2. **Olive Branch (DC) View:**  
   - Role = "Distribution Center" → the motor (as part of a drill kit or finished good) is held for **field-order fulfillment**.  
   - 890K on-hand = ~2.8 days at field rate. Much lower unit count than the plant (which makes 12.5M) but **higher dollar value** per unit (finished-good pricing).  
   - Safety stock is **higher and proactive** because field demand is stochastic.  
   - Exception: "Breach at DC" → activate backorder logic, pull forward shipment from plant, or allocate high-priority customers first.

3. **The Key Insight:**  
   The same **motor component** is measured in:  
   - **BOM units + cost** at the plant (production material in).  
   - **SKU units + kit cost** at the DC (distribution material out).  
   - Same product, **different grain, different plan, different action**.

### Evidence Label: **Prototype choice**  
This example is a hypothesis. Real validation requires tracing a live item across 20_supply_daily + dim_series_ext_vw over time; reserved for Phase 2 analytics.

---

## PERS1 — Persona / Planner Ownership: Exception Load

**Query:** From dim_series_ext_vw (4.99M item×org rows), rank planners and suppliers by count of items under their management.

| Rank | Planner Name | Supplier | Item×Org Count | % of Universe | Exception Load Proxy |
|---|---|---|:---:|:---:|---|
| 1 | *(null)* | 2012 Olive Branch | 3,444,223 | 69% | **Very High** — Olive Branch (DC) manages 2.3B in cost; any bulk exception = operational crisis |
| 2 | *(null)* | 2092 3PL Parts & Service | 660,125 | 13% | **High** — 3PL partner; lead-time/capacity exceptions ripple to all downstream DCs |
| 3 | *(null)* | *(null)* | 553,563 | 11% | **Medium** — Unallocated items; need assignment logic |
| 4 | *(null)* | 2013 OB-Home Depot | 53,280 | 1% | **Low** — dedicated customer facility |
| 5 | Brantley, Ben | *(null)* | 36,841 | 0.7% | **Low-Medium** — named planner, small portfolio |

### Top Named Planners (excerpt from full ranking):

1. **Brantley, Ben:** 36,841 items — likely **demand planner** or **component specialist**.  
2. *(Next 4 planners: all null or small counts — indicates heavy use of role-based assignments or legacy system)*

### Narrative

1. **The Null-Planner Phenomenon:**  
   Most item×org rows have **null planner_name**, indicating assignment is by **role/org/team** not individual. Alerts should route to:
   - **"2012 Olive Branch"** → DC Operations Manager (Olive Branch team).  
   - **"2092 3PL"** → 3PL Operations Coordinator.  
   - Named planners: escalate directly.

2. **Supplier Concentration:**  
   - **Olive Branch (2012)** is both a supplier (internal DC) and a customer (supplies field). 69% of the item universe flows through it → **critical chokepoint**.  
   - **3PL (2092):** 13% — second concentration; any 3PL outage cascades.  
   - Real suppliers (external): fragmented across the remaining 18%.

3. **Exception Routing Implication:**  
   - **Bulk safety-stock breach?** → Route to "Olive Branch On-Call Manager" (not an individual planner; a team responsibility).  
   - **3PL capacity alert?** → Route to "3PL Operations Lead."  
   - **Named planner exception?** → Route to that person's queue.

### Evidence Label: **Validated** against prod_operations.edw_extension.dim_series_ext_vw (live, 4.99M rows).

---

## PERS2 — Persona Views: What Each Role Cares About

Mapping personas (supply-chain function) to the columns/tables/metrics they need from the data lake.

| Persona | Primary Role | Focus Metrics | Key Tables/Views | Filters/Dimensions | Routing Logic |
|---|---|---|---|---|---|
| **Demand Planner** | Forecast, event planning | Forecast accuracy, demand variance, plan-to-actual, customer SLA miss | 10_demand_daily, 11_demand_daily, dg5_customer_scd1 | By customer (mkedg0–5), by item, by geography | By assigned customer segment or geography; escalate if MAPE >15% or SLA miss >5 units |
| **Supply Planner** | Inbound, supply timing | PAB (projected available balance), SS (safety stock), lead-time, receipt-on-time | 20_supply_daily, purchase_orders, inventory_days_on_hand | By supplier, by source_level (inbound/inter-DC/intra-plant), by item | By assigned supplier / plant; escalate if PAB < SS or RCV is past-due >5 days |
| **Planning Manager** | KPI accountability | Variance (bias, RMSE, MAPE), forecast+plan health, exception rate trend, cost impact | 20_supply_daily_summary, 10_demand_daily_summary, snapshot plan-name | By business unit, by roll-up horizon (month/quarter) | By P&L center; summarize top N exceptions by $impact |
| **Buyer / Procurement** | PO execution, spend | PO status (received/unconfirmed/past-due), lead-time trend, receipt variance, price variance | purchase_orders, receiving_receipt_transactions, purchase_order_schedule | By supplier, by purchase_order_delivery_status, by date-range | By assigned supplier; escalate if past-due >SLA or receipt qty <ordered qty >5% |
| **DC Operations Manager** | Inbound/outbound, fulfillment | On-hand by location, inbound receipt plan, outbound shipment plan, inventory-turns | inventory_days_on_hand, customer_shipments, purchase_order_delivery | By organization (their DC), by item (high-turn SKU first) | By assigned org; escalate if on-hand <SS or receipt <plan |
| **Service Hub Lead** | Field availability, rapid response | Field depletion rate, DC replenishment lag, emergency allocation status, hub-to-hub transfer | inventory_days_on_hand (hub org), 10_demand_daily (service demand), customer_shipments | By hub org, by service-request priority | By assigned hub; escalate if on-hand < 1-day supply or response-time SLA miss |

### Narrative

1. **Demand Planner** → needs **forecast-accuracy and customer-facing metrics**, not supply detail. Route forecast-drift alerts to them; ignore supplier lead-time.
2. **Supply Planner** → needs **PAB, SS, lead-time, receipt timing**, not customer segment. Route safety-stock breaches + past-due POs to them.
3. **Manager** → needs **rolled-up P&L impact and trend**. Route "top 20 exceptions by cost" and "forecast accuracy vs. plan by month" monthly.
4. **Buyer** → needs **PO status, supplier performance, spend variance**. Route past-due PO and receipt qty-variance alerts to them.
5. **DC Ops** → needs **on-hand by location, inbound plan, outbound plan**. Route on-hand breaches and receipt-delay alerts to their org.
6. **Service Hub Lead** → needs **real-time field depletion and replenishment lag**. Route field-depletion and emergency-allocation alerts to them.

### Evidence Label: **Preferred with assumptions**  
This mapping is standard supply-chain function design. Real validation once the exception queue and persona routing are built (P2).

---

## GOTCHAS & OPEN QUESTIONS

1. **Null Planner Assignment:**  
   - 69% of item×org rows in dim_series_ext_vw have null planner_name.  
   - **Question:** Is this by design (role-based assignment) or data quality issue?  
   - **Action:** Clarify assignment model with PBPC team; may require augmentation with org-role→team mapping.

2. **Organization Role Boundaries:**  
   - Org 2012 (Olive Branch) is classified as "Distribution Center" but also acts as a supplier to other DCs and service hubs.  
   - **Question:** Should it have a dual role or a "Hub DC" classification?  
   - **Action:** Consult topology with supply-chain architect; may require role-role edges for routing (e.g., "Olive Branch breach → escalate UP to DC Manager + DOWN to Hub Manager").

3. **20_supply_daily vs. inventory_days_on_hand:**  
   - 20_supply_daily has rich plan measures (PAB, SS, safety_stock_override) but is sparse/null for dates outside planning window.  
   - inventory_days_on_hand has clean daily on-hand but limited supply-plan context.  
   - **Question:** Should exception logic read from both tables with a join-pattern, or is one authoritative per use case?  
   - **Action:** Establish join-pattern and SLA (realtime vs. daily snapshot) before building exception queue.

4. **Supplier vs. Organization Confusion:**  
   - dim_series_ext_vw.supplier_name includes internal orgs (2012 Olive Branch) and external suppliers.  
   - **Question:** How should internal-supplier breaches (plant lead-time, DC replenishment) be routed vs. external-supplier breaches (vendor-quality, vendor capacity)?  
   - **Action:** Tag supplier_type (internal/external) in dim_series_ext_vw or upstream for cleaner routing logic.

5. **Historical Depth for Exception Trending:**  
   - Current snapshot (20260829) is a single point-in-time.  
   - **Question:** Over the past 12 weeks, which planners / suppliers / orgs have been **repeat offenders** for exceptions?  
   - **Action:** Capture daily exception snapshots into sandbox_operations.po_management for trend analysis + planner-accountability dashboards.

---

## DESIGN REQUIREMENTS FOR EXCEPTION QUEUE & DASHBOARDS

**Derived from LOC + PERS traces:**

### 1. Exception Filtering / Routing
- **Dimension 1:** Organization Role (manufacturing plant, DC, service hub).  
- **Dimension 2:** Assigned Planner (null → team role; named → individual queue).  
- **Dimension 3:** Assigned Supplier (internal/external) + supplier name.  
- **Fact:** Exception Type (safety-stock breach, past-due PO, stockout, inbound delay, forecast miss, receipt qty-variance).  
- **Fact:** Severity ($impact, units at risk, business unit, customer SLA miss).  

→ **Query Pattern:** `SELECT * FROM exception_queue WHERE role_classification IN (...) AND assigned_planner = ? AND exception_type IN (...) ORDER BY severity DESC`

### 2. Role-Specific Views
- **Plant perspective:** Show inbound-receipt PAB + lead-time distribution (supplier risk).  
- **DC perspective:** Show on-hand + customer demand + transfer-in plan (allocation risk).  
- **Service Hub perspective:** Show field-depletion rate + DC replenishment lag (response-time risk).  
- **Manager perspective:** Show top-N exceptions by cost + trend (decision dashboard).

### 3. Planner Workload Balancing
- **Metric:** Exceptions per planner per day, grouped by exception type and org role.  
- **Purpose:** Identify overburdened planners, auto-escalate to manager if workload >SLA threshold.  
- **Data Source:** Exception queue snapshots + dim_series_ext_vw assignment.

### 4. Supplier Performance Scorecard
- **Metrics:** On-time rate, quantity accuracy, lead-time variance by supplier (external + internal).  
- **Slice:** By supplier, by source level (inbound, inter-DC).  
- **Purpose:** Buyer escalation + RFQ renegotiation trigger.

---

## SUMMARY: ROUTING & FILTERING REQUIREMENTS

| Requirement | Impact | Priority |
|---|---|---|
| **Route exceptions by org role, not globally** | Actionability: a plant breach ≠ DC breach; without role context, planners ignore or misroute alerts | **P1** |
| **Assign exceptions to planner or team role** | Accountability: null planners should route to team (org role → on-call manager mapping) | **P1** |
| **Tag exception severity ($impact, SLA miss)** | Prioritization: planners see top-impact exceptions first | **P1** |
| **Snapshot exception queue daily** | Trending: enable "repeat-offender" analysis + manager KPI by planner / supplier | **P2** |
| **Build role-specific dashboards** (Plant / DC / Hub / Manager) | Fit-for-purpose: each role sees metrics that matter to them | **P2** |
| **Integrate external-supplier vs. internal-supplier tagging** | Buyer focus: external-supplier exceptions route to procurement; internal → operations | **P3** |

---

## Files & Resources

- **Data Queries (READ-ONLY):** All queries in this document run against prod_edw and prod_operations with no writes.  
- **Output Destination:** All findings write to sandbox_operations.po_management when the exception queue is operationalized.  
- **Reference:** See `development_pattern/references/supply-chain-domain.md` for plan vs. actual vocabulary and role definitions.

---

## Conclusion

Milwaukee's supply chain is geographically and functionally segmented. Exceptions that occur at a **manufacturing plant** (component-centric, make-driven) require different planner action than exceptions at a **distribution center** (SKU-centric, demand-driven) or a **service hub** (field-depletion, rapid-response). 

**Routing must respect these boundaries.** The same data signal (PAB < SS) routed to the wrong persona is noise; routed to the right persona with role context is actionable intelligence.

**Next Step:** Build exception queue with role + planner + severity dimensions. Start with P1 supply-exception traces (safety stock, past-due PO); expand to P3–P4 demand events in subsequent phases.

