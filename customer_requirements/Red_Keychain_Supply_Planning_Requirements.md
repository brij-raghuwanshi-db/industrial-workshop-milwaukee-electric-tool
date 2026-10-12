%md
# Red Keychain — Supply Planning Detailed Requirements
## Milwaukee Tool

**Related notebook:** Red_Keychain_Planning_Platform_Requirements (framework & architecture decisions)

---

## B: Exception Queue & PO Actions

| # | Question | Answer | Status |
| --- | --- | --- | --- |
| B.1 | Exception types | 18 exception types confirmed across 5 categories | Decided |
| B.2 | Prioritization | Time urgency by largest unit miss. Bookmark financial impact for later | Decided |
| B.3 | PO action execution | Changes must feed back to Oracle (as long as Oracle is in use) | Decided |
| B.4 | Bulk actions | Must have — act on multiple exceptions at once | Decided |

### Exception Types (Full Confirmed List — 18 Types)

**Core Supply Exceptions:**
1. Demand exceeds supply (potential stockout)
2. Excess inventory vs. target
3. PO pull-in recommended (need product earlier)
4. PO push-out recommended (demand dropped)
5. New PO needed (no open order coverage)
6. PO cancel recommended
7. Supplier late / lead time risk
8. Safety stock violation (projected inventory below SS)

**Transition Exceptions:**
9. Old SKU not running down fast enough (obsolescence risk)
10. New SKU ramping but supply coverage gap
11. Transition overlap period mismatch (both SKUs have inventory simultaneously)

**Supply Signal Exceptions:**
12. PO past due — open PO with receipt date in the past, not yet received
13. Lead time drift — actual lead times trending longer than planned assumptions
14. Demand forecast significantly changed since last plan (volatility/instability alert)

**Network / Inventory Exceptions:**
15. Inventory imbalance across DCs — one location overstocked, another short on same SKU (rebalancing trigger)
16. MOQ waste — forced to over-order due to minimum order quantity, creating planned excess

**Plan Integrity Exceptions:**
17. Frozen zone violation — change recommended inside firm/actionable window (requires escalation)
18. Plan vs. actual receipt variance — receipts not matching what was expected this week

### Key Implications
- Oracle integration required — API or file-based mechanism to push PO changes back to Fusion
- Prioritization by largest unit miss = projected inventory vs. demand gap driving sort order
- Bulk actions = "select multiple + apply action" UX pattern
- Transition exceptions (#9-11) tie to bookmarked transitions deep-dive
- Rebalancing trigger (#15) = natural integration point for absorbing existing rebalancing app

---

## BRAINSTORM REQUIREMENTS INCORPORATION
*Source: Team brainstorm doc "Red Key Chain: Ordering — Key Requirements"*

### NEW Items Added (not previously captured)

#### 1. Core Planning Calculation Changes (NEW)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-1 | **Requested vs. Confirmed plans** | Distinguish between what was requested from supplier and what supplier confirmed. Carry both through the plan. Confirmed data comes from Oracle Procurement module | Decided |
| NEW-2 | **"Rec not before PO" constraint** | Don't recommend receipts earlier than a placed PO can realistically deliver. Keeps recommendations executable | Decided |
| NEW-3 | **Order vs. Rebalance decision** | Explicitly determine when to place a new order vs. rebalance/transfer existing inventory to hit SS targets. Make this a first-class decision in the engine | Decided |
| NEW-4 | **Stranded inventory / pooling** | Pool inventory visibility across nodes to identify and redeploy stranded stock rather than ordering new units when existing inventory could cover | Decided |
| NEW-5 | **PO grouping & sequencing** | Group and sequence POs by business rules (truckload consolidation, requested delivery date, timing). Rules defined by supply leaders. Make POs smaller and grouped by specific criteria | Decided |

#### 2. Supply Optimization Engine (NEW Details)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-6 | **Supplier forecast → Oracle SCC** | Flow resulting supplier forecast to Oracle SCC via API. Weekly EDI cadence (Friday 4PM freeze) + ad hoc publish. Auto-identify off-cycle POs for mass publish | Decided |
| NEW-7 | **Phased supplier rollout** | Start with TTi (largest supplier), then expand to distribution, MFG signal, and service supplier types | Decided |
| NEW-8 | **Replace Truckload PaaS** | Current Oracle PaaS handles requisition → PO conversion with truckload grouping logic. Red Keychain replaces this. Can reference its logic | Decided |

#### 3. Scenario Simulation (NEW Details)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-9 | **Probability-based scenarios** | Not just +/- %, but probabilistic modeling. Ability to change dials with different probabilities (e.g., 70% chance supplier is 1 week late, 30% chance 3 weeks late) | Decided |
| NEW-10 | **Fill Rate Test = Supply Plan + dials** | Simulation IS the supply plan with ability to change probability dials. Not a separate tool | Decided |

#### 4. Recommendation Engine / AI (NEW Details)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-11 | **Codify planner tribal knowledge** | Capture planner logic, business rules, supplier-specific rules, MOQs, transitions, ordering exceptions into repeatable logic | Decided |
| NEW-12 | **Explainable release recommendations** | Prioritized with specific rules: no demand spikes present, order falls within X months of demand, consistent planned orders already exist | Decided |
| NEW-13 | **Seed rules from planner knowledge** | Rules haven't been created yet. Need to build from planner tribal knowledge (Matt Michael, Dana Balog, Alyssa Bubik). Interview-based requirement | To Build |

#### 5. Ordering App / UX (NEW Details)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-14 | **Restore Redwood lost functionality** | Oracle Redwood upgrade removed edit-in-spreadsheet capability. Must restore this in Red Keychain | Decided |
| NEW-15 | **PO grouping at point of release** | Support exception management AND PO grouping/sequencing at the moment of release (not just planning) | Decided |

#### 6. System Integrations (NEW Details)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-16 | **Forecast → Oracle SCC** | Drop file into SCC on weekly EDI cadence (Friday 4PM freeze) or ad hoc via publish | Decided |
| NEW-17 | **POs → Truckload PaaS (replacement)** | Red Keychain replaces the Oracle PaaS that converts requisitions to POs with truckload grouping. Reference existing logic | Decided |
| NEW-18 | **Feedback loop** | Capture planned-order release outcomes + exception catches. Flow back into optimizer and app for continuous improvement/learning | Decided |

#### 7. Virtual DC & Postponement (Future - Expands Bookmark)

| # | Requirement | Description | Status |
| --- | --- | --- | --- |
| NEW-19 | **Decision fences** | Prevent allocation churn — don't reallocate daily. Create fences so allocations are stable | Future |
| NEW-20 | **SKU segmentation** | Segment by volatility, volume, criticality, forecast-signal decay to determine planning treatment | Future |
| NEW-21 | **Post-freeze change tracking** | Track allocation changes after freeze as a process-health metric | Future |
| NEW-22 | **Plan globally → allocate regionally → sort locally** | Hierarchical commitment: country → region → DC. Commit to geography only as uncertainty resolves | Future |

### Key Implications from Brainstorm Doc
- **Requested vs. Confirmed is critical** — the plan today assumes requested = actual, which causes bad recommendations. Carrying both creates a more realistic supply picture
- **Order vs. Rebalance decision** maps directly to the existing optimizer (which already has both transfer AND purchase variables). Need to make this trade-off explicit and visible to planners
- **PO grouping & sequencing** is a new capability beyond what we discussed — planners don't just approve individual POs; they group them into efficient shipments (truckloads)
- **TTi first** — gives clear pilot scope. One supplier type, prove the model, then expand
- **Planner knowledge capture (NEW-13)** is a project unto itself — need structured interviews with Matt Michael, Dana Balog, Alyssa Bubik to codify their exception rules
- **Replace Truckload PaaS** — Red Keychain isn't just a planning tool; it's also the ORDER EXECUTION layer (requisition → grouped PO → release)
- **Feedback loop** enables AI to learn from planner overrides and improve recommendations over time
- **Probabilistic simulation** is more advanced than simple what-if — may require Monte Carlo or similar approach (aligns with existing safety stock simulation model)