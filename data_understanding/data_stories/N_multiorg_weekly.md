# Multi-Org Network & Weekly Snapshot Cadence: MKE Supply Chain Data Trace

**Date:** 2026-08-30  
**Query Profile:** mke-rsc (READ-ONLY)  
**Scope:** prod_edw (fact.inventory_days_on_hand, fact.20_supply_daily, dim.inventory_organization_scd1, dim.date_scd1)

---

## PART A: MULTI-ORG INVENTORY LANDSCAPE

### A.1: Org Inventory Spread (on date_key 20260829)

The network extends far beyond 2012 Olive Branch and 2120 Mexico. Real multi-org topology revealed:

| Organization Code | Organization Name | Forecasted Org | Distinct Items | Total On-Hand Qty |
|--|--|--|--|--|
| 1019 | Grenada (Plant) | 1-US Distribution | 4,826 | 199,660,044 |
| 1006 | Cookeville, TN | 1-US Distribution | 6,691 | 42,230,462 |
| 2012 | Olive Branch | 1-US Distribution | 126,401 | 40,820,592 |
| 2013 | OB - Home Depot | 1-US Distribution | 84,620 | 32,846,731 |
| 1016 | Greenwood, MS | 1-US Distribution | 11,034 | 29,097,280 |
| 1014 | Mukwonago, WI | 1-US Distribution | 4,353 | 28,054,613 |
| 1015 | Sun Prairie, WI | 1-US Distribution | 1,898 | 14,346,330 |
| 1080 | Byhalia, MS | 1-US Distribution | 16,993 | 14,014,343 |
| 2093 | 3PL DC - Canada Geodis | 1-US Distribution | 5,758 | 5,261,315 |
| 2092 | 3PL Parts & Service | 1-US Distribution | 32,129 | 8,782,904 |
| 9043 | Indy Service Hub | 2-Service | 115,348 | 337,308 |
| 9042 | Greenwood Service Hub | 2-Service | 115,231 | 234,488 |
| 9046 | Canada Georgina Service Hub | 2-Service | 114,877 | 164,425 |
| 3061 | Edmonton Branch | 2-Service | 102,951 | 31,056 |
| 3062 | Vancouver Branch | 2-Service | 103,214 | 20,280 |
| 2120 | Mexico | 3-MEX Distribution | 21,627 | 1,828,475 |

**Finding:** Material non-2012/2120 orgs fall into three tiers:
- **Tier 1 (DCs):** 1019 (Grenada, ~200M units), 1006 (Cookeville, ~42M), 1080 (Byhalia, ~14M), 2013 (OB-HD, ~33M)
- **Tier 2 (3PLs):** 2092 (Parts & Service, 2,125+ breaches/week), 2093 (Canada Geodis, 1,271+ breaches/week)
- **Tier 3 (Service/Branches):** 9043/9042/9046 service hubs; 3061/3062/3067/3070 branches (minimal inventory, highly fragmented)

---

### A.2: Safety-Stock Breaches in NON-2012/2120 Orgs

Process_date 20260829: Real breaches at 3PL and secondary DC locations.

| Organization Code | Organization Name | Org Role | Target Week (date_key) | Breach Count | Distinct Items Breached |
|--|--|--|--|--|--|
| 2092 | 3PL Parts & Service | 1-US Distribution | 20260824 | 2,125 | 2,125 |
| 2092 | 3PL Parts & Service | 1-US Distribution | 20260907 | 2,074 | 2,074 |
| 2092 | 3PL Parts & Service | 1-US Distribution | 20260914 | 2,059 | 2,059 |
| 2093 | 3PL DC - Canada Geodis | 1-US Distribution | 20260831 | 1,271 | 1,271 |
| 2093 | 3PL DC - Canada Geodis | 1-US Distribution | 20260824 | 1,175 | 1,175 |
| 2013 | OB - Home Depot | 1-US Distribution | 20260824 | 1,067 | 1,067 |

**Critical Example: 2092 3PL Parts & Service on 20260824 (4 items, all breached PAB < SS):**

| Product ID | PAB | Safety Stock | Miss Qty (SS - PAB) |
|--|--|--|--|
| 5149134010793328314 | -817 | 5,864 | 6,681 |
| 5608740512284151498 | -1,267 | 5,014 | 6,281 |
| 6641546691381387852 | 578 | 6,528 | 5,950 |
| 278065169428500600 | 5,865 | 11,089 | 5,224 |

**End-User Lens (⚠️):** 2092 is not an outlier—it's systematically short on 2,000+ SKUs per week. The plan sees this but doesn't flag it as priority because the logic treats all orgs uniformly. A P1 weekly plan-vs-actual must weight 3PLs differently (they serve multiple distribution regions). Cascading delay through 2093 (Canada, -1,271 items week of 20260831) suggests upstream supply stress.

**P1 Priority Impact:** Multi-week breach visibility across the 3PL network signals supply chain vulnerability. This is NOT a Olive Branch isolated issue.

---

### A.3: DC Imbalance Among Non-2012 Orgs

Same item (hero: 3879620845706693458) high at one non-2012 org, low at another:

**Scenario: Comparing 1080 Byhalia vs 2093 Canada Geodis, target week 20260921 (6 successive weekly snapshots)**

From snapshot date 20260720 through 20260824 (Mondays only):

| Snapshot Date | 1080 Byhalia PAB | 2093 Canada Geodis PAB | Ratio |
|--|--|--|--|
| 20260720 | 9,584 | 2,357 | 4.1x |
| 20260727 | 9,584 | 2,357 | 4.1x |
| 20260803 | 9,584 | 2,562 | 3.7x |
| 20260810 | 9,584 | 2,239 | 4.3x |
| 20260817 | 9,584 | 2,241 | 4.3x |
| 20260824 | 9,584 | 2,241 | 4.3x |

**Finding:** Byhalia (1080) is consistently ~4x better positioned for this hero item than Canada 3PL. Byhalia's view is STABLE (9,584 unchanged for 6 weeks—very predictable), while Canada shows micro-volatility (2,239→2,562→2,241) suggesting tighter, more reactive replenishment. This is not imbalance; it's **role specialization**: Byhalia is a primary DC with buffer stock; 2093 is a just-in-time 3PL fulfillment hub. Weekly plan must account for this.

---

### A.4: Org-Role Contrasts (Service Hub vs Branch vs DC)

Same target week (20260824), plan snapshot from process_date 20260829:

#### Service Hubs (9xxx) Behavior:

| Hub | Items Planned | % with SS | % with Demand | Avg PAB | Avg SS | Role Note |
|--|--|--|--|--|--|--|
| 9043 Indy | 17,219 | 73.9% | 33.3% | 24.14 | 16.80 | Higher SS coverage, light demand |
| 9042 Greenwood | 15,151 | 66.7% | 28.4% | 19.75 | 14.15 | Moderate SS + demand breadth |
| 9046 Canada Georgina | 15,383 | 0.0% | 0.4% | 17.90 | (empty) | Demand-only, NO safety stock |

#### Branches (3xxx) Behavior:

| Branch | Items Planned | % with SS | % with Demand | Avg PAB | Avg SS | Role Note |
|--|--|--|--|--|--|--|
| 3020 Chicago | 1,746 | 0.0% | 0.06% | 3.61 | (empty) | Minimal planning, order-reactive |
| 3021 Baltimore-DC | 1,436 | 0.0% | 0.14% | 2.61 | (empty) | Minimal planning |
| 3022 New York | 2,151 | 0.0% | 0.05% | 3.18 | (empty) | Minimal planning |
| 3024 Seattle | 1,650 | 0.0% | 0.24% | 2.53 | (empty) | Minimal planning |

#### DC (2012, 1080, 2014) Behavior:

| DC | Items Planned | % with SS | % with Demand | Avg PAB | Avg SS | Role Note |
|--|--|--|--|--|--|--|
| 2012 Olive Branch | 27,327 | 38.2% | 50.4% | 1,731 | 1,325 | PRIMARY: heavy SS + demand |
| 1080 Byhalia | 9,041 | 6.9% | 8.2% | 2,171 | 1,292 | Secondary DC: selective SS |
| 2014 Byhalia DC | 4,281 | 6.8% | 10.2% | 960 | 453 | Tertiary DC: minimal SS |

**Finding (✅):** Org role MUST shape scenario logic:

1. **DCs (2012, 1080, 2014)** have deep safety-stock planning (38% of items at 2012; 7% at 1080/2014). Demand is incorporated (50% at 2012, 8% at 1080). This is ACTIVE inventory management.

2. **Service Hubs (9043, 9042)** do carry safety stock (~67–74% of items) but it's THIN (avg 14–17 units vs 1,292 at DCs). Demand is light (28–33% of items). **Hybrid role:** some buffering, mostly reactive.

3. **9046 Canada Georgina** has ZERO safety stock planning—pure demand-driven. This hub is a pass-through for Canadian service calls.

4. **Branches (3020–3025)** have NO safety stock planning, minimal demand signals, and minimal PAB (2–4 units). They are **order-only** fulfillment endpoints; they don't participate in proactive planning.

**P1 Impact:** A weekly plan-vs-actual algorithm that treats all orgs with the same variance tolerance will fail catastrophically at branches (expected near-zero inventory, but flagged as shortfall). Service hubs will be falsely flagged as overstocked. DCs need tighter governance. Weekly logic must tag org role at query time.

---

## PART B: WEEKLY SNAPSHOT CADENCE

### B.5: Process-Date Calendar – 6 Weeks (2026-07-14 to 2026-08-29)

The plan stores DAILY snapshots. For P1 weekly grain, we must pick ONE process_date per calendar week. Availability check:

| Week | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Mon (Next) | Gaps |
|--|--|--|--|--|--|--|--|--|--|
| Jul 14–20 | (missing) | ✓ 14 | ✓ 15 | ✓ 16 | ✓ 17 | ✓ 18 | (no Sun) | ✓ 20 (Mon) | Sun 19 missing |
| Jul 21–27 | ✓ 20 | ✓ 21 | ✓ 22 | ✓ 23 | ✓ 24 | ✓ 25 | (no Sun) | ✓ 27 (Mon) | Sun 26 missing |
| Jul 28–Aug 3 | ✓ 27 | ✓ 28 | ✓ 29 | ✓ 30 | ✓ 31 | ✓ 1 | (no Sun) | ✓ 3 (Mon) | Sun 2 missing |
| Aug 4–10 | ✓ 3 | ✓ 4 | ✓ 5 | ✓ 6 | ✓ 7 | ✓ 8 | (no Sun) | ✓ 10 (Mon) | Sun 9 missing |
| Aug 11–17 | ✓ 10 | ✓ 11 | ✓ 12 | ✓ 13 | ✓ 14 | ✓ 15 | (no Sun) | ✓ 17 (Mon) | Sun 16 missing |
| Aug 18–24 | ✓ 17 | ✓ 18 | ✓ 19 | ✓ 20 | ✓ 21 | ✓ 22 | (no Sun) | ✓ 24 (Mon) | Sun 23 missing |
| Aug 25–29 | ✓ 24 | ✓ 25 | ✓ 26 | ✓ 27 | ✓ 28 | ✓ 29 | (no Sun) | — | Every Sunday missing |

**Row Counts per Snapshot (all ~60,000 rows, stable):**
- 20260714: 59,460 rows | 20260720: 59,676 rows | 20260727: 59,863 rows | 20260803: 60,159 rows | 20260810: 60,329 rows | 20260817: 60,460 rows | 20260824: 60,513 rows | 20260829: 60,600 rows

**Finding (✅):** **NO Sunday snapshots exist; every Sunday (19th, 26th, etc.) is missing.** Monday snapshots are ALWAYS present and consistently available. **Weekly snapshot selection rule:** use the MONDAY process_date as the canonical week. (Fallback: if Monday missing—rare—use Saturday of preceding week.)

---

### B.6: Weekly Plan Vintages – How PAB Forecasts Evolve Week-by-Week

**Scenario:** Hero item 3879620845706693458 at target week 20260921 (Sept 21), viewed across 6 successive Monday snapshots (20260720 through 20260824):

#### 2012 Olive Branch – Weekly Vintage Series:

| Snapshot Date (Mon) | PAB for Week 20260921 | Safety Stock | Trend |
|--|--|--|--|
| 20260720 | 18,049 | 55,918 | **Base forecast** |
| 20260727 | 47,179 | 56,384 | ⬆️ Upward revision (+29,130 units; new receipt or demand deferrals?) |
| 20260803 | 42,585 | 56,378 | ⬇️ Slight correction (-4,594 units; consumption or demand acceleration?) |
| 20260810 | 40,177 | 56,382 | ⬇️ Continue lower (-2,408 units) |
| 20260817 | 56,199 | 56,475 | ⬆️ Sharp upward spike (+16,022 units; likely purchase order receipt booked) |
| 20260824 | 55,204 | 56,585 | ⬇️ Small drop (-995 units; demand consumed some of the receipt) |

**Narrative:** 2012's view of the week of 21st Sept is **volatile**. The jump from 18K→47K→42K→40K→56K→55K shows **weekly re-planning** in action. By week 5 (20260817), a large inbound receipt stabilizes the view near safety stock. This is a **"how did our expectation for week W shift, week by week?"** series—perfect for answering "when did we first see the supply gap?" or "how confident is this forecast?"

#### 1080 Byhalia – Weekly Vintage Series (Same target week):

| Snapshot Date (Mon) | PAB for Week 20260921 | Safety Stock | Trend |
|--|--|--|--|
| 20260720 | 9,584 | (empty) | **Stable** |
| 20260727 | 9,584 | (empty) | — (unchanged) |
| 20260803 | 9,584 | (empty) | — (unchanged) |
| 20260810 | 9,584 | (empty) | — (unchanged) |
| 20260817 | 9,584 | (empty) | — (unchanged) |
| 20260824 | 9,584 | (empty) | — (unchanged) |

**Narrative:** Byhalia's forecast is **FROZEN** at 9,584 units for 6 weeks straight. No safety stock is planned (empty column). This suggests Byhalia's plan is **stateless / deterministic** (not re-optimized weekly like 2012). Or it has very low throughput and demand is light, so the forecast doesn't move. This is acceptable for a secondary DC but raises a question: **is 1080 planned reactively (order-to-stock) rather than demand-driven?**

#### 2093 Canada Geodis – Weekly Vintage Series (Same target week):

| Snapshot Date (Mon) | PAB for Week 20260921 | Safety Stock | Trend |
|--|--|--|--|
| 20260720 | 2,357 | 1,589 | **Baseline** |
| 20260727 | 2,357 | 1,589 | — (unchanged) |
| 20260803 | 2,562 | 1,588 | ⬆️ Micro-revision (+205 units) |
| 20260810 | 2,239 | 1,588 | ⬇️ Correction (-323 units) |
| 20260817 | 2,241 | 1,551 | ⬇️ Hold (-2 units; SS also dropped to 1,551) |
| 20260824 | 2,241 | 1,551 | — (unchanged) |

**Narrative:** 2093's forecast is **tightly boundaried** (2,239–2,562, a 14% range) with **thin safety stock** (~1,551 units). It's re-planned weekly but only **micro-corrected**. This is consistent with a just-in-time 3PL that runs lean and is less sensitive to long-term demand changes.

**Finding (✅):** Weekly vintages reveal **org planning personality**:
- **2012 (primary DC):** High volatility, large swings, responsive re-planning → **demand-driven, active**
- **1080 (secondary DC):** Frozen PAB, minimal SS → **order-driven, passive** (or very stable demand)
- **2093 (3PL):** Micro-adjustments, tight bounds → **lean, just-in-time**

P1 **"plan confidence decay"** metric: if 2012's forecast swings ±50% week-to-week, but 2093 swings ±5%, then week W's plan for 2093 is far more predictable/confident. Weekly variance patterns should inform demand-shaping and supply contracts.

---

### B.7: Weekly Actuals Rollup – Point-in-Time vs Summed Flows

**Semi-Additive Grain Rule at Weekly:** On-hand inventory is a **SNAPSHOT** at week-end (one value per week); flows (shipments, receipts) are **SUMMED** within the Mon–Sun interval.

**Example: Hero item 3879620845706693458 at 2012 Olive Branch (process_date 20260829, Monday snapshots only)**

| Week Start | Week Ending (Mon) | Week-Ending On-Hand (Snapshot) | Weekly Shipments (Sum) |
|--|--|--|--|
| 2026-08-03 | 20260810 | 110,391 units | 20,099 units |
| 2026-08-10 | 20260817 | 125,221 units | 18,856 units |
| 2026-08-24 | 20260824 | 108,309 units | 16,177 units |

**Narrative:**
- **Week 1 (Aug 3–9, reported on 10th):** Started the week with ~110K on-hand; shipped out 20K. (Implies receipts or prior opening balance reconciliation.)
- **Week 2 (Aug 10–16, reported on 17th):** Started with ~125K (up from 110K); shipped 18.9K. (Likely major receipt landed on or after the 10th snapshot.)
- **Week 3 (Aug 24–29, reported on 24th):** Back down to 108K; shipped 16.2K. (Steady consumption, no large receipt captured in this week.)

**Gotcha:** If you SUM the on-hand column (110K + 125K + 108K = 343K), it is **WRONG**. That's triple-counting inventory that existed at different times. The **correct weekly on-hand** is one per week: a point-in-time measurement on Monday.

**Correct semi-additive formula:**
```
Weekly_Ending_Inventory[W] = Snapshot at Monday of week W (point-in-time)
Weekly_Shipments[W] = SUM(daily shipments Mon–Sun of week W) (flows, additive)
Weekly_Receipts[W] = SUM(daily receipts Mon–Sun of week W) (flows, additive)

Weekly_Opening_Inventory[W] = Weekly_Ending_Inventory[W-1]
```

**P1 Impact:** Plan-vs-actual must use this rule. If you mistakenly SUM weekly on-hand values, your starting/ending inventory balances will be nonsense, and your supply-demand reconciliation will fail. The fact that Monday snapshots exist consistently (no Sundays) makes this easy to enforce: always use Monday, always treat it as a snapshot, always sum the flows separately.

---

### B.8: Monday Availability and Data Continuity

Over the 6 weeks (2026-07-14 to 2026-08-29):
- **Mondays available:** 20260720, 20260727, 20260803, 20260810, 20260817, 20260824 (6 out of 6; **100%**)
- **Sundays available:** 0 (none; systematic pattern)
- **Saturday available:** Yes, all 6 Saturdays (20260718, 20260725, 20260801, 20260808, 20260815, 20260822)
- **Weekday (Tue–Fri) available:** Yes, all (daily load is consistent)

**Stability:** Row counts stable at ~59,500–60,600 across the entire period; no drops or anomalies.

**Finding (✅):** **Clean Monday snapshots exist every week. This is the canonical weekly reporting unit. The schedule is reliable.**

---

## CROSS-CUTTING GOTCHAS & OPEN QUESTIONS

### Gotcha 1: Empty Safety Stock at Branches & Some Service Hubs
Many org types (branches 3020–3025, service hub 9046 Canada Georgina) have **zero or missing safety-stock values** in the plan. This is correct by design—they don't hold safety stock—but scenario logic must handle it gracefully (don't flag as "missing data"; it means "not applicable for this org role").

### Gotcha 2: Org-Role Visibility in Dimensions
The `forecasted_organization` field is the only explicit role marker (1=US Distribution, 2=Service, 3=MEX, 4=MEX Floorcare). Branch/service-hub classification must be inferred from org_code ranges (3000–3999 branches, 9000–9999 service hubs). Encode this rule in the plan-vs-actual queries to avoid hard-coding org lists.

### Gotcha 3: Multiple Records per Product×Org×Date in 20_supply_daily
Some items appear multiple times in the same snapshot (e.g., 2012 Olive Branch item 3879620845706693458 on date_key 20260921 has 3–4 rows with different plan_name or planning scenario). Current queries aggregate across all plan variants. Clarify whether to:
- Combine across all scenarios (current approach)
- Isolate primary/approved plan only
- Compare scenario divergence (which plans see different PAB?)

### Gotcha 4: 3PL Breaches are Persistent, Not Acute
2092 3PL Parts & Service has 2,000+ items breached every week. This is NOT a single-week crisis; it's a **structural under-supply** at this fulfillment hub. Escalation rules for P1 must distinguish "breach count > 1000" (routine for 3PLs) vs "breach count > X AND breach_duration > 2 weeks AND trend worsening" (true exception). Without this, 2092's chronic shortage will drown out true anomalies.

### Gotcha 5: Process_date vs date_key Grain Confusion
- `process_date` = the snapshot capture date (when the plan was run; e.g., 20260829)
- `date_key` = the target week/period the plan forecasts (e.g., 20260921)
- A single process_date contains many date_keys (the plan looks weeks/months ahead).

Weekly aggregation must be on **process_date** (one per calendar week), while plan targets are on **date_key**. Don't mix the two.

### Open Question 1: Is 1080 Byhalia Plan Static or Demand-Driven?
1080's forecast for item 3879620845706693458 is frozen at 9,584 units for 6 weeks. Is this:
- (A) A genuinely stable item with constant demand?
- (B) A planning bug (plan not updating)?
- (C) A configuration (1080 uses different planning logic, e.g., order-to-stock with fixed reorder quantity)?

Recommend: sample 10–20 different items at 1080 across the same 6-week period; if all are frozen, it's a policy issue.

### Open Question 2: Should Service Hubs (9xxx) and Branches (3xxx) Be in the Weekly Plan?
Branches (3020–3025) are minimally planned (0.05–0.2% of items have demand signals). They look more like read-only fulfillment endpoints than active inventory nodes. Recommend:
- **Exclude branches from P1 weekly variance analysis** (they're noise).
- Keep them in exception-case tracking (e.g., "order placed but no inventory, escalate to branch manager").
- **Include service hubs 9043–9046 in weekly P1**, but with org-role-specific thresholds (accept higher % variance due to service-call volatility).

### Open Question 3: Weekly Vintage Volatility Trend Line
2012's PAB swings widely week-to-week (18K→47K→40K→56K). Is this:
- (A) Expected re-planning as demand/supply updates arrive?
- (B) Sign of poor demand forecast (high churn)?
- (C) Symptom of bullwhip effect upstream (supplier lead times, safety stock dynamics)?

Recommend: build a **volatility index per item per org per target week**: track the coefficient of variation (std dev / mean) of PAB across the 6-week vintage series. Flag items where volatility > threshold (e.g., >30%). This feeds a "forecast confidence" layer for supply-shaping conversations.

---

## SUMMARY & PRIORITY ALIGNMENT

### Which Non-2012/2120 Orgs Are Material?

**Tier-1 (Supply Volume):**
- **1019 Grenada (Plant):** 199M units; primary input node.
- **1006 Cookeville, TN:** 42M units; secondary DC.
- **1080 Byhalia, MS:** 14M units; inventory hub.
- **2013 OB - Home Depot:** 33M units; customer-dedicated warehouse.

**Tier-2 (Exception Volume):**
- **2092 3PL Parts & Service:** 2,100+ safety-stock breaches/week; critical supply risk node.
- **2093 3PL Canada Geodis:** 1,200+ breaches/week; international supply vulnerability.

**Tier-3 (Operational):**
- **Service hubs (9043, 9042):** 115K+ items planned; light on-hand but high distribution importance.
- **Branches (3020–3025):** Minimal planning; treat as read-only fulfillment endpoints.

### A Real Non-2012 Breach Example (✅)

**2092 3PL Parts & Service, week of 24th Aug (date_key 20260824), snapshot 20260829:**
- Product ID 5149134010793328314: PAB = -817 units, SS = 5,864 units → **Miss = 6,681 units**
- **End-user impact:** This 3PL cannot fulfill 6,681 units of demand for this SKU. Upstream supply (from 2012, 1080, etc.) is blocked or delayed.

### Do Clean Weekly Monday Snapshots Exist? (✅)

**Yes.** 6 weeks = 6 Mondays, all present. Sundays are systematically absent (no data load on Sundays). Saturday snapshots exist as a fallback. **Weekly reporting grain is robust; use Monday process_date as the canonical snapshot.**

---

## RECOMMENDATIONS FOR P1 WEEKLY PLAN-VS-ACTUAL BUILD

1. **Org-Role Tagging:** Encode org classification (DC, 3PL, service hub, branch) directly in the plan query; use it to apply org-specific variance thresholds and exception rules.

2. **Weekly Snapshot Selection:** Use Monday process_date; if missing (rare), fall back to Saturday. Never use average or sum of multiple days.

3. **Semi-Additive Enforcement:** On-hand is point-in-time (Monday only); flows (shipments, receipts, adjustments) are summed within the Mon–Sun week.

4. **3PL Exception Handling:** Distinguish "routine 3PL breach" (expected at 2092, 2093) from "new breach" or "breach worsening." Threshold: flag if breach count > 1.5x recent baseline AND breach_duration > 2 consecutive weeks.

5. **Vintage Volatility Index:** For each item×org×target_week, compute std dev of PAB across the prior 6 Monday snapshots. High volatility (>30%) signals forecast instability; feeds confidence scoring for supply actions.

6. **Branch Exclusion:** Branches (3xxx) are noise in P1 weekly; use exception-case logic instead (e.g., "urgent order placed but branch has zero inventory → escalate").

7. **Data Continuity Monitoring:** Sunday gaps are normal. Monitor for new weekday gaps; if they appear, investigate data load process.

---

## FILES & EVIDENCE

**Data Sources (READ-ONLY; no writes):**
- `prod_edw.fact.inventory_days_on_hand` – on-hand position by org, item, date
- `prod_edw.fact.20_supply_daily` – plan snapshots by org, item, target week
- `prod_edw.dimension.inventory_organization_scd1` – org hierarchy, roles
- `prod_edw.dimension.date_scd1` – date grain (week_start_date, day_of_week, etc.)
- `prod_edw.fact.sales_order_line_transactions` – shipment flows by order date

**Queries (all SELECT; read-only):**
1. Org inventory landscape (20260829)
2. Multi-org safety-stock breaches (non-2012/2120)
3. Specific breach example (2092, 20260824)
4. Process-date calendar (6-week range)
5. Weekly plan vintages (hero item across 6 Mondays)
6. Weekly ending on-hand + summed flows
7. Org-role contrasts (DC vs service hub vs branch)

**Output File:** `/Users/brijendra.raghuwanshi/Downloads/mke_rsc_isaac/data_understanding/data_stories/N_multiorg_weekly.md`

---

## CLOSING NOTES

The MKE supply network is **not a two-DC system**. It's a multi-tier, multi-geography, multi-role ecosystem:
- **Primary DCs (2012)** are re-planned weekly and respond to demand shifts.
- **Secondary/Tertiary DCs (1080, 2014)** run leaner, with slower re-planning cadence.
- **3PLs (2092, 2093)** are chronically short but performing as designed (thin safety stock, high throughput).
- **Service hubs & branches** are fulfillment endpoints, not inventory managers.

A P1 weekly plan-vs-actual **must respect these roles**. Uniform exception thresholds will produce false positives at branches and false negatives at 3PLs. The stable Monday snapshot schedule is an asset; use it. Weekly vintage analysis (how forecast confidence decays) is a hidden lever for supply-shaping decisions.

---

**End of Report**  
Query executed: 2026-08-30  
Profile: mke-rsc (read-only)  
Status: All data verified; no writes performed.
