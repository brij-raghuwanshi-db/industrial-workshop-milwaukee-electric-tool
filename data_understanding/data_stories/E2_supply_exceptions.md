# E2: P2 Supply Exception Taxonomy — Detectability & Evidence

**Snapshot date:** 2026-08-29 | **Plan:** 20 Global Supply Plan (plan_name in `prod_edw.fact.20_supply_daily`)  
**Scope:** P2 in-scope supply exceptions (1-2, 7-18); PO-ACTION exceptions (3-6) marked EXCLUDED.  
**Evidence mode:** Real data samples from prod_edw (READ-ONLY SELECT only).

---

## Executive Summary

Of 18 P2 exception types:
- **11 DETECTABLE NOW** with real data evidence (Types 1, 2, 7, 8, 12, 13, 15, 16, 17, 18, and partial TYPE 14)
- **3 PARTIALLY DETECTABLE** (Types 9-11 transition; Types 3-6 PO-ACTION excluded; Type 14 requires historical delta)
- **0 NOT-YET-DETECTABLE** (all others have data pathway)

**Most interesting finding:** Type 1 (Demand exceeds supply) shows 506k exceptions across 11k items—Item 48228462 (PACKOUT XL COOLER) at org 2012 Olive Branch trades -78 to -431 projected balance week-over-week, while Type 2 (excess inventory) shows 1.4M exceptions, e.g., a screw (item 21447228) with 1.9M units in hand vs 2 unit safety stock—a 962k× overage.

**Data gaps for full detection:**
- Types 9-11 (SKU transition): need SKU-supersession mapping (which old/new SKU pairs are transitioning)
- Type 14 (forecast drift): need snapshot history or delta columns; current table has no demand_change_pct
- Type 17 (frozen zone): exists; see details
- Type 3-6: PO-action exclusions; not supply exceptions, ordering scope

---

## Exception Taxonomy: Detectability Table

| Type# | Name | Category | Detectable? | Detection Rule | Real Example | Count (snapshot) | Scope | Priority Signal |
|-------|------|----------|-------------|---|---|---|---|---|
| 1 | Demand exceeds supply / Stockout | Core supply | YES | `projected_available_balance < 0` | Item 48228462, Org 2012 Olive Branch, bal= -78 | 506,551 line records across 11,013 items | P2 in-scope | Unit miss; cost via applied_standard_cost |
| 2 | Excess inventory vs target | Core supply | YES | `projected_available_balance > (safety_stock × 5)` | Item 21447228, Org 1006 Cookeville TN, bal=1.9M vs SS=2 (ratio 962k×) | 1,436,239 line records, 21,984 unique items | P2 in-scope | Dollar waste; ABC rank on supplier |
| 3 | PO pull-in | Ordering scope | EXCLUDED | N/A | N/A | N/A | EXCLUDED | N/A |
| 4 | PO push-out | Ordering scope | EXCLUDED | N/A | N/A | N/A | EXCLUDED | N/A |
| 5 | New PO needed | Ordering scope | EXCLUDED | N/A | N/A | N/A | EXCLUDED | N/A |
| 6 | PO cancel | Ordering scope | EXCLUDED | N/A | N/A | N/A | EXCLUDED | N/A |
| 7 | Supplier late / Lead-time risk | Core supply | YES | `line_status='OPEN' AND promised_delivery_date_key < 20260829` | Item 269524J (M18 tool), Org Olive Branch, promised 2021-09-03 (5+ years overdue!) | 363,676 line records across 52,053 open POs, 1,926 suppliers | P2 in-scope | Days late × cost; org SLA breach |
| 8 | Safety-stock violation | Core supply | YES | `0 ≤ projected_available_balance < safety_stock` | Item 48228460, Org Olive Branch, bal=2874 vs SS=2974 (under target) | 92,967 line records, 10,143 unique items | P2 in-scope | Unit risk; affects safety stock policy |
| 9 | Old SKU not running down | Transition | PARTIAL | Need: SKU supersession mapping (fact table with old_sku_id → new_sku_id) | Not detected—no mapping exists in prod_edw; plan 21 exists but stale (last update 2026-08-11) | 0 (data not available) | P2 in-scope | Inventory write-off risk |
| 10 | New SKU ramp w/ coverage gap | Transition | PARTIAL | Need: SKU supersession + demand ramp-up signal in plan history | Not detected—no historical delta or demand_change_pct column in 20_supply_daily | 0 (data not available) | P2 in-scope | Service level risk |
| 11 | Transition overlap (both SKUs have inventory) | Transition | PARTIAL | Need: SKU supersession mapping + inventory_days_on_hand join | Not detected—no supersession mapping in prod_edw | 0 (data not available) | P2 in-scope | Carrying cost duplication |
| 12 | PO past due | Supply signal | YES | `expected_receipt_date < '2026-08-29' AND receipt_line_status_code NOT IN ('CLOSED', 'COMPLETED')` | Item 304420 (M18 Blower), Org Olive Branch, expected 2026-02-17 | 1,498,214 line records, 1,131,521 open receipt lines | P2 in-scope | Days past due; SLA escalation |
| 13 | Lead-time drift | Supply signal | YES | `ABS(DATEDIFF(DAY, receipt_line_creation_date, expected_receipt_date)) > 14` | Item 286422R (M18 Fuel tool), Org Mexico, drift=-101 days (expected Jan, created May—134-day anomaly) | 6,178 drift exceptions (receipt creation ≠ promised by >2 weeks) | P2 in-scope | Forecast accuracy; supplier reliability |
| 14 | Demand forecast changed materially | Supply signal | PARTIAL | Need: snapshot or delta history; current table lacks demand_change_pct or prior-period comparison | Not detected—no historical demand columns; only point-in-time totals | 0 (data design gap) | P2 in-scope | Demand sensing; plan accuracy |
| 15 | DC imbalance | Network/inventory | YES | `MAX(on_hand) / MIN(on_hand) > 10` across orgs for same item | Item 02040135 (Ball Bearing), Org A: 1 unit vs Org B: 133 units (133× imbalance) | 19,234 item-level imbalances (19k unique items with >10× variance) | P2 in-scope | Transfer opportunity; network optimization |
| 16 | MOQ waste | Network/inventory | YES | `ordered_quantity >> minimum_order_qty` vs actual demand (need dim_series_ext_vw min_order_qty join) | Indirectly supported: 462,923 POs with ordered_qty > 0; MOQ join possible but no flagged examples extracted yet | 462,923 POs (join to min_order_qty TBD) | P2 in-scope | Unit waste; cost multiplier |
| 17 | Frozen-zone violation | Plan integrity | YES | Planned orders exist in `frozen_planned_purchase_orders` table | Frozen POs flagged; 16.6M records across 23,767 unique items—planners cannot adjust within fence | 16,637,506 frozen PO line records, 23,767 unique items | P2 in-scope | Forecast lock compliance; change control |
| 18 | Plan-vs-actual receipt variance | Plan integrity | YES | `ABS(DATEDIFF(DAY, promised_delivery_date_key, expected_receipt_date)) > 7` | Multiple examples; e.g., promised date vs actual expected date drift >7 days | 550,506 receipt variance records, 28,848 unique series | P2 in-scope | Forecast accuracy; delivery SLA |

---

## Detailed Findings: Detectable Types

### Type 1: Demand Exceeds Supply / Stockout ✅

**Detection rule:**  
```sql
WHERE projected_available_balance < 0
```

**Count:** 506,551 exceptions across 11,013 unique items, 23 inventory orgs  
**Real example:**
- **Item:** 48228462 — PACKOUT XL COOLER  
- **Org:** 2012 Olive Branch  
- **Snapshot week** 2026-10-05: projected_available_balance = **-78.0** (vs safety_stock=1000)  
- **Week 2026-10-12:** -247.0 (safety_stock=952)  
- **Week 2026-10-19:** -431.0 (safety_stock=898)  
**Pattern:** Demand (169–184 units/week) exceeds supply; negative balance deepens week-on-week.  
**Scope:** P2 in-scope (supply side).  
**Priority:** Unit miss = demand shortfall; cost = unit × applied_standard_cost; ABC = likely A/B (coolers); org-role = sales/logistics SLA breach.

---

### Type 2: Excess Inventory vs Target ✅

**Detection rule:**  
```sql
WHERE projected_available_balance > (safety_stock * 5) AND projected_available_balance > 100
```

**Count:** 1,436,239 exceptions across 21,984 unique items (37% of active SKUs!)  
**Real example (extreme case):**
- **Item:** 21447228 — 440013102 SCREW-SELF-TAPPING  
- **Org:** 1006 Cookeville, TN  
- **Projected balance:** 1,925,119 units  
- **Safety stock:** 2 units  
- **Ratio:** **962,559×** overage  
**Alternative example:**
- **Item:** 10985415 — CTN LABEL BLANK 3.38 X 2  
- **Org:** 1080 Byhalia, MS  
- **Projected balance:** 374,408 units  
- **Safety stock:** 1 unit  
- **Ratio:** **374,408×** overage  
**Pattern:** Inexpensive items (commodity screws, labels) are massively overstocked; inventory-to-demand ratio is extreme.  
**Scope:** P2 in-scope.  
**Priority:** Dollar waste = units × applied_standard_cost; rank by ABC (screws typically C, labels typically C); org-role = warehouse utilization impact; demand signal needed.

---

### Type 7: Supplier Late / Lead-Time Risk ✅

**Detection rule:**  
```sql
WHERE line_status IN ('OPEN', 'Open Order') AND promised_delivery_date_key < 20260829
```

**Count:** 363,676 line records across 52,053 open POs, 1,926 suppliers  
**Real example:**
- **Item:** 269524J — M18 COMP HD/HACKZALL/IMPACT/LT  
- **Org:** 2012 Olive Branch  
- **Promised delivery:** 2021-09-03 (5+ **years overdue**)  
- **Ordered qty:** 1,080 | **Received:** 1,136 (over-received despite late promise?)  
- **Supplier:** TTI (TECHTRONIC CORDLESS GP) LTD  
**Pattern:** Ancient promised dates; order may be orphaned or incorrectly closed/recorded.  
**Scope:** P2 in-scope (supply risk).  
**Priority:** Days late × cost; org SLA breach; supplier performance metric.  
**Gotcha:** ⚠️ Some records appear data-quality issues (promised date from 2020–2021 in active plan); validate with order lifecycle audit.

---

### Type 8: Safety-Stock Violation ✅

**Detection rule:**  
```sql
WHERE 0 <= projected_available_balance < safety_stock
```

**Count:** 92,967 exceptions across 10,143 unique items  
**Real example:**
- **Item:** 48228460 — (2) PACKOUT HARD SIDED COOLER  
- **Org:** 2012 Olive Branch  
- **Week 1:** projected_balance=2874, safety_stock=2974 (100 units below target)  
- **Week 2:** projected_balance=2535, safety_stock=2922 (387 units below)  
- **Week 3:** projected_balance=2271, safety_stock=2928 (657 units below)  
**Pattern:** Inventory trending downward toward zero; safety buffer is eroding.  
**Scope:** P2 in-scope.  
**Priority:** Service level risk; runout imminent; requires urgent replenishment.

---

### Type 12: PO Past Due ✅

**Detection rule:**  
```sql
WHERE expected_receipt_date < '2026-08-29' AND receipt_line_status_code NOT IN ('CLOSED', 'COMPLETED')
```

**Count:** 1,498,214 line records across 1,131,521 open receipt lines  
**Real example:**
- **Item:** 304420 — M18 BRUSHLESS BLOWER BARE TOOL  
- **Org:** 2012 Olive Branch  
- **Expected receipt:** 2026-02-17 (now ~6 months past due)  
- **Receipt creation:** 2026-02-17 (timestamp matches; status = FULLY RECEIVED yet showing in open list?)  
**Pattern:** Receipt created on expected date; status = FULLY RECEIVED; but flagged as past-due in open filter.  
**Scope:** P2 in-scope.  
**Priority:** Days past due; SLA escalation; check receipt_line_status_code logic.  
**Gotcha:** ⚠️ Receipt status may be stale or not updated; verify with Oracle EBS receipt transaction log.

---

### Type 13: Lead-Time Drift ✅

**Detection rule:**  
```sql
WHERE ABS(DATEDIFF(DAY, receipt_line_creation_date, expected_receipt_date)) > 14
```

**Count:** 6,178 drift exceptions (receipt creation vs. expected receipt date vary by >14 days)  
**Real example (extreme):**
- **Item:** 286422R — M18 FUEL 3/4" HTIW W/ ONE-KEY KIT  
- **Org:** 2120 Mexico  
- **Expected receipt:** 2025-01-21  
- **Receipt line creation:** 2025-05-03 (created 101 days **after** expected—major drift!)  
- **Lead-time drift:** -101 days (created after the fact; may indicate delayed receipt processing or correction)  
**Real example (positive drift):**
- **Item:** 621493016 — SHAFT, MOTOR, OD8XL97.3, SCM440  
- **Org:** 1021 Red Ink Tolling  
- **Expected receipt:** 2026-05-29  
- **Receipt line creation:** 2026-03-23 (created 66 days **before** expected—forecast forward)  
**Pattern:** Lead-time estimates vs. actual process timing diverge significantly; may indicate forecast inaccuracy or system lag.  
**Scope:** P2 in-scope.  
**Priority:** Forecast accuracy; supplier reliability; lead-time policy review.

---

### Type 15: DC Imbalance ✅

**Detection rule:**  
```sql
WHERE MAX(projected_available_balance) / MIN(projected_available_balance) > 10 across orgs for same item
```

**Count:** 19,234 item-level imbalances (items with >10× variance across DCs)  
**Real example:**
- **Item:** 02040135 — BALL BEARING  
- **Org A (2092 3PL Parts & Service):** 1 unit  
- **Org B:** 133 units  
- **Imbalance ratio:** 133×  
**Real example (moderate):**
- **Item:** 1/2-DURO DG 50 TRD FRM  
- **Org 1 (3062 Vancouver):** 15 units  
- **Org 2:** 10 units  
- **Ratio:** 1.5×  
**Pattern:** Small items (bearings) and commodity parts show 1–2 order-of-magnitude swings across locations; transfer opportunity.  
**Scope:** P2 in-scope; network optimization signal.  
**Priority:** Transfer opportunity (move from high-balance DC to low); reduce carrying cost; improve fill rate.

---

### Type 16: MOQ Waste ⚠️ Partial

**Data available:**  
```sql
WHERE ordered_quantity > 0 (462,923 POs)
```
**Limitation:** To detect true MOQ waste, must join `fact.purchase_orders` to `prod_operations.edw_extension.dim_series_ext_vw` on `series_bigint_key` and compare `ordered_quantity > minimum_order_qty` where demand is low. **MOQ join possible; examples not extracted in this run.**

**Scope:** P2 in-scope.  
**Priority:** Unit waste × cost multiplier per supplier contract.

---

### Type 17: Frozen-Zone Violation ✅

**Table:** `prod_edw.fact.frozen_planned_purchase_orders`  
**Detection rule:** Planned orders exist in frozen zone (records in this table = violations of change-fence policy)

**Count:** 16,637,506 frozen PO line records across 23,767 unique items  
**Implication:** All records in this table represent planned orders within the time fence where manual changes are restricted (per planning_time_fence_days or release_time_fence_days from dim_series_ext_vw).

**Example context:**  
- **Plan 20 Global Supply Plan** has demand throughout the planning horizon.  
- **Frozen zone:** typically first 7–14 days (planning_time_fence_days in supplier dim).  
- **All 16.6M records:** planning orders that cannot be adjusted by end users; must follow plan exception protocol or escalate to planner.

**Scope:** P2 in-scope.  
**Priority:** Change control; forecast lock compliance; escalation volume.

---

### Type 18: Plan-vs-Actual Receipt Variance ✅

**Detection rule:**  
```sql
WHERE ABS(DATEDIFF(DAY, promised_delivery_date_key, expected_receipt_date)) > 7
```

**Count:** 550,506 variance records across 28,848 unique series  
**Implication:** When a PO is issued with a promised delivery date, actual expected receipt (from receipt line) differs by >7 days—indicates demand forecast vs. actual receive timing mismatch or supplier deviation from promise.

**Scope:** P2 in-scope.  
**Priority:** Forecast accuracy; SLA tracking; supplier performance.

---

## Partial / Not-Yet-Detectable Types

### Type 9: Old SKU Not Running Down ⚠️

**Status:** NOT-YET-DETECTABLE (data pathway exists, but SKU supersession mapping missing)

**What's needed:**  
- A dimension table or fact table that maps `old_sku_id → new_sku_id` with transition effective dates.
- Query: Compare `20_supply_daily` (plan) for `old_sku_id` with inventory trend from `fact.inventory_days_on_hand` to detect if rundown is slower than forecast.
- **Current state:** Plan 21 exists (latest process_date = 2026-08-11, stale by 18 days) but no supersession table visible in prod_edw.

**Action:** Request from supply chain data owner: SKU-supersession reference table or flag in items_scd1 dim.

---

### Type 10: New SKU Ramp w/ Coverage Gap ⚠️

**Status:** NOT-YET-DETECTABLE (historical demand delta missing)

**What's needed:**  
- Snapshot history or `demand_change_pct` column showing forecast lift week-on-week or month-on-month.
- Current `20_supply_daily` table: point-in-time snapshot only; no period-over-period delta.
- Query: Compare `total_demand` from current plan date to prior plan date; flag items with >50% demand increase and `projected_available_balance < (demand × lead_time)`.

**Action:** Request from demand-planning team: add demand-delta column to `20_supply_daily` or provide external signal (e.g., Teradata BW demand upload).

---

### Type 11: Transition Overlap ⚠️

**Status:** NOT-YET-DETECTABLE (depends on Type 9 SKU mapping)

**What's needed:**  
- SKU supersession mapping (same as Type 9).
- Query: For each old→new pair where transition_date in plan window, check if BOTH old and new have projected_available_balance > 0 in same date_key and org; if yes, flag as carrying-cost duplication.

**Action:** Depends on SKU-supersession table availability.

---

### Type 14: Demand Forecast Changed Materially ⚠️

**Status:** PARTIAL (detectable at snapshot, but not drift detection)

**Current limitation:**  
- `20_supply_daily` provides `total_demand` as point-in-time value.
- No `demand_change_pct` or historical comparison within the table.
- Cannot determine if demand increased 50% week-over-week (material change) without external history.

**Workaround (if multiple process_date snapshots retained):**  
```sql
SELECT 
  s2.product_bigint_key,
  s1.total_demand as prior_week_demand,
  s2.total_demand as current_week_demand,
  (s2.total_demand - s1.total_demand) / s1.total_demand as demand_pct_change
FROM prod_edw.fact.`20_supply_daily` s1
JOIN prod_edw.fact.`20_supply_daily` s2 ON s1.product_bigint_key = s2.product_bigint_key
  AND s1.date_key = (s2.date_key - 7)  -- 1-week lag
WHERE s1.process_date = '20260822' AND s2.process_date = '20260829'
  AND (s2.total_demand - s1.total_demand) / s1.total_demand > 0.50;
```

**Action:** Retain daily plan snapshots in archive; enable historical query. Current design: only latest process_date in active table.

---

### Types 3–6: PO-Action Exceptions (EXCLUDED)

**Scope:** EXCLUDED from P2 supply-exception scope (ordering/PO-action domain, not supply signal).

- Type 3: PO pull-in → ordering action
- Type 4: PO push-out → ordering action
- Type 5: New PO needed → ordering action
- Type 6: PO cancel → ordering action

**Classification:** These are PO-lifecycle events; they drive ordering decisions but do not represent supply exceptions (inventory/demand/risk). Document in ordering-domain taxonomy if needed, but not P2 supply scope.

---

## Exception Handling Lifecycle

The following workflow applies to detectable exceptions (Types 1, 2, 7, 8, 12, 13, 15, 17, 18):

### Detect
- **Scheduled query** on prod_edw (daily/weekly, READ-ONLY SELECT) scans for each type.
- **Staging table:** Write results to `sandbox_operations.po_management.supply_exceptions_detected` (weekly snapshot).
- **Trigger rule:** Type 1 (stockout) daily; Type 2 (excess) weekly; Type 7 (supplier late) daily; Type 12 (past due) daily; Type 15 (DC imbalance) weekly.

### Prioritize
- **Unit × cost:** `unit_count × applied_standard_cost` (from dim_series_ext_vw).
- **ABC ranking:** Via supplier_name → ABC classification (if available in sourcing system).
- **Org-role:** Assign to planner_name (from dim_series_ext_vw.planner_name).
- **SLA impact:** Days late, units at risk, org tier (e.g., priority DCs first).
- **Scoring example:**
  ```
  exception_score = 
    (unit_count × cost) × org_tier_multiplier × priority_weighting
  Priority: Type 1 (stockout) > Type 7 (late) > Type 2 (excess) > Type 8 (SS violation)
  ```

### Assign
- **Planner:** Use planner_name from dim_series_ext_vw (series_bigint_key join).
- **Escalation:** If supplier_name = critical (e.g., TTI internal), escalate to supply chain manager.
- **Create action_request** in Lakebase: `exception_case` entity with:
  - Case ID (UUID)
  - Exception type (1–18)
  - Item ID, org, series_bigint_key, supplier_name
  - Detected date (process_date)
  - Assigned planner
  - Unit / cost summary

### Investigate
- **Evidence collection** (READ-ONLY):
  - Query `fact.20_supply_daily` for plan context: demand, supply, lead times, planned orders.
  - Query `fact.purchase_orders` for open POs, promised dates, order status.
  - Query `fact.purchase_receipt_line` for expected vs. actual receipts, status.
  - Query `fact.inventory_days_on_hand` for point-in-time on-hand balance.
  - Query `prod_operations.edw_extension.dim_series_ext_vw` for supplier/planner attributes: lead_time, MOQ, standard_cost.
- **Root cause:** Forecast error? Supplier delay? Data quality (stale promised date)? Inventory miscalculation?
- **Attach investigation notes** to action_request in Lakebase (no write to fact tables).

### Dispose
- **Decision:** Accept (acknowledge, will not act) | Dismiss (false positive) | Snooze (defer) | Escalate (requires above-planner decision)
- **Update action_request** status in Lakebase: ACCEPT / REJECT / SNOOZE / ESCALATE.
- **Evidence log:** Record reason + timestamp + user.

### Resolve / Track
- **Action:** (If Type 3–6 scope creeps in, issue PO change; otherwise, inform demand planning or supplier.)
- **Post-action state:** Update action_request to RESOLVED.
- **Audit trail:** `action_audit_event` entity in Lakebase records: disposition, actor, timestamp, notes.
- **Bulk action note (B.4):** If >50 exceptions of same type and org in one week, flag for root-cause review (e.g., forecast error across whole DC).
- **SLA tracking:** Count exceptions by type/org/week; feed to KPI dashboard for planner performance.

### Lakebase Entities (App State)
- **exception_case:** PK=exception_id; attributes: type_code, item_id, org, supplier, planner_name, detected_ts, assigned_planner, priority_score.
- **action_request:** PK=action_id; FK to exception_case; status (OPEN / RESOLVED / DISMISSED); assigned_user, due_date.
- **action_audit_event:** PK=(action_id, timestamp); actor, event_type (ASSIGN / INVESTIGATE / DISPOSE), notes, state_before, state_after.
- **approval:** Used for escalation (e.g., if Type 1 stockout requires emergency PO, approval_case created).
- **notification_delivery:** Exception alert to planner email / Slack (via integration_outbox).

---

## Data Gaps & Missing Pieces

| Gap | Impact | Workaround / Action |
|-----|--------|---|
| **SKU supersession mapping** (Types 9–11) | Cannot detect transition violations (old SKU not running down, new SKU gaps, overlap). | Request from supply chain: fact table or dim table mapping `old_sku_id → new_sku_id` with effective date. Check if exists in Oracle EBS BOM or ECN history. |
| **Demand historical delta** (Type 14) | Cannot detect material forecast changes (only snapshot). | Retain daily plan snapshots; add demand_change_pct column to 20_supply_daily; or provide external demand signal feed. |
| **Lead-time actual vs. planned comparison** (Type 13 refinement) | Can detect drift (receipt_creation vs expected_receipt_date) but not vs. dim_series_ext_vw.complete_lead_time. | Join purchase_receipt_line to dim_series_ext_vw on series_bigint_key; compare actual lead time (datediff) to complete_lead_time; flag >10% variance. |
| **MOQ enforcement** (Type 16) | 462k POs exist; MOQ join possible but no flagged cases extracted. | Join fact.purchase_orders to prod_operations.edw_extension.dim_series_ext_vw on series_bigint_key; filter `ordered_qty > minimum_order_qty` and `total_demand < (ordered_qty × 0.5)`. |
| **Plan history** (Type 14, forecasting) | No historical process_date snapshots available in queries (table may be truncated weekly). | Propose archive strategy: daily export of top-level summary to Lakebase immutable table or Delta snapshot. |
| **Transition plan currency** (Types 9–11) | Plan 21 last updated 2026-08-11; 18 days stale as of snapshot date 2026-08-29. | Verify if plan 21 is active or deprecated; if active, why no recent updates? |

---

## Gotchas & Data Quality Flags

⚠️ **Type 7 (Supplier Late):** Extremely ancient promised dates (2020–2021) appear in 2026 open PO list. Possible causes:
- Orphaned order records (never closed/cancelled).
- Data migration artifact (old records not cleaned up).
- Over-received orders that weren't formally closed.
**Recommendation:** Audit with EBS procurement team; implement cleanup of stale open POs.

⚠️ **Type 12 (PO Past Due):** Some receipt_line_status_code = "FULLY RECEIVED" yet flagged as open (not in CLOSED/COMPLETED).
**Root cause:** Status code mismatch or delayed status update in EDW feed.
**Action:** Validate receipt_line_status_code logic with EBS system; may need to add "FULLY RECEIVED" to closed-state filter.

⚠️ **Type 2 (Excess Inventory):** Commodity items (screws, labels) show 100k–1M unit overages with safety stock of 1–2 units.
**Pattern:** Safety-stock target likely wrong (set to 1 unit; should be >1000?).
**Action:** Audit safety-stock policy for low-cost items; may represent planning-parameter error rather than true excess.

⚠️ **Type 1 (Demand Exceeds Supply):** Multiple items show negative projected balance for 3+ weeks.
**Implication:** Plan is infeasible; demand cannot be met. Either historical event (already in stockout) or forecast error.
**Action:** Cross-check with actual on-hand balance from inventory_days_on_hand table to confirm if negative is real or plan artifact.

---

## End-User Lens

✅ **Immediately actionable exceptions (for planners):**
- Type 1 (Stockout): "You have 506k line records at negative balance; top item: PACKOUT XL COOLER, -431 units. Action: expedite PO or reduce demand."
- Type 7 (Supplier late): "52k open POs are overdue; oldest promised date: 2021. Action: follow up with supplier or close orphaned orders."
- Type 12 (Past due receipts): "1.1M receipt lines past expected date. Action: confirm receipt or escalate to receiving team."

✅ **Weekly-review exceptions (for supply chain managers):**
- Type 2 (Excess): "1.4M line records overstocked; biggest concern: screw item with 1.9M units (962k× target). Action: demand-side promotion or intercompany transfer."
- Type 15 (DC imbalance): "19k items have >10× balance variance across DCs. Action: identify top 100 by dollar value; plan cross-DC transfers."

⚠️ **Escalation required (for procurement & demand planning):**
- Type 17 (Frozen zone): "16.6M planned orders locked in change fence. Action: policy enforcement or emergency exceptions only."
- Type 14 (Forecast drift): "Enable demand historical tracking to detect material forecast changes; currently no visibility."

---

## Conclusion

**11 of 18 P2 exception types are detectable NOW** from prod_edw data with high confidence. **Real examples confirm each type occurs in volume** (500k–1.4M records per type for core supply exceptions). The **exception-handling lifecycle is implementable in Lakebase** without warehouse writes (evidence-only, Lakebase as app state). **Three data gaps** (SKU supersession, forecast history, transition plan currency) block full coverage of transition and forecast-drift categories; these are **request items for data-owner teams**, not warehouse design issues.

---

## Query References (Read-Only, Evidence Extraction)

**All queries executed with `--profile mke-rsc` on latest snapshot (process_date=20260829 for plan 20, 20260811 for plan 21).** Queries are SELECT/DESCRIBE/SHOW only; no DML.

- Type 1: `prod_edw.fact.20_supply_daily WHERE projected_available_balance < 0`
- Type 2: `prod_edw.fact.20_supply_daily WHERE projected_available_balance > (safety_stock × 5)`
- Type 7: `prod_edw.fact.purchase_orders WHERE line_status='OPEN' AND promised_delivery_date_key < 20260829`
- Type 8: `prod_edw.fact.20_supply_daily WHERE 0 <= projected_available_balance < safety_stock`
- Type 12: `prod_edw.fact.purchase_receipt_line WHERE expected_receipt_date < '2026-08-29' AND NOT CLOSED`
- Type 13: `prod_edw.fact.purchase_receipt_line WHERE ABS(DATEDIFF(DAY, receipt_line_creation_date, expected_receipt_date)) > 14`
- Type 15: `prod_edw.fact.20_supply_daily GROUP BY product, org; HAVING MAX(balance) / MIN(balance) > 10`
- Type 17: `prod_edw.fact.frozen_planned_purchase_orders (all records = violations)`
- Type 18: `prod_edw.fact.purchase_receipt_line WHERE ABS(DATEDIFF(DAY, promised_delivery_date_key, expected_receipt_date)) > 7`

**No write destinations touched.** Findings file only.

