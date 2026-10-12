# Supply-Chain Dimensional Modeling (Kimball) & Medallion

> **Kimball supplies the modeling discipline; Databricks supplies the execution architecture.**
> (Execution "how" is in `databricks-execution-craft.md`; this file is the modeling craft.)

The binding rule: **declare exactly what one row represents before designing joins, dimensions,
measures, SQL, pipelines, dashboards, Genie, or ML features.**

## Grain first — as a business sentence, not a key list

Never state grain as `item_key + org_key + week_key`. State it as a sentence:

> One row represents the supply plan for one item, at one inventory organization, for one target
> week, as seen in one planning snapshot and plan version.

Distinct grains already present in this project:

| Business process | Atomic grain |
|---|---|
| Supply-plan snapshot | item × org × plan date × snapshot date × plan/version |
| PO receipt | one receipt transaction event (by PO line, item, org) |
| Sales shipment | one shipment/fulfillment event per order line |
| Inventory snapshot | item × org × snapshot date (± subinventory/lot/status) |
| Demand-planning event | event × item × customer leaf × forecast month |
| Weekly plan vs actual | item × org × week × selected plan vintage |
| Supply exception | one detected exception instance × item/location × eval timestamp |
| Planner action | one action/recommendation decision against an exception |

**Preserve atomic facts.** A weekly comparison table is derived, not a replacement for atomic
receipts/shipments/movements/snapshots. Atomic grain answers unanticipated questions; aggregates
exist for common patterns and performance.

## Three Kimball fact types — use all three deliberately

| Fact type | Supply-chain use | Row behavior |
|---|---|---|
| Transaction | receipt, shipment, movement, order change, planner action | insert one row per event |
| Periodic snapshot | daily inventory, weekly supply plan, monthly forecast, supplier scorecard | insert one row per period × entity |
| Accumulating snapshot | PO / sales-order fulfillment, exception-resolution, req-to-receipt lifecycle | update one row as milestones occur |

Movements explain *why* inventory changed; periodic snapshots show *how much* existed;
accumulating snapshots measure *how long* a lifecycle took.

## Weekly snapshot date taxonomy

"Weekly snapshot" is incomplete until these dates are separated: `snapshot_date` (captured),
`target_week_start` (period the plan applies to), `transaction_date`, `expected_receipt_date`,
`actual_receipt_date`, `week_end_date` (ending inventory), `source_extract_timestamp`,
`pipeline_processed_timestamp`. Project convention: Monday–Sunday week; Monday-morning snapshot =
prior Sunday end-of-day. Keep `snapshot_date` and `target_week` separate or a query will compare a
plan made *this* week for a future period against an actual from the *same calendar* week.

**Immutable vintages.** A plan snapshot is an immutable planning vintage — a new plan supersedes
it operationally but must not erase what planners believed earlier. For late data distinguish:
original snapshot, restated/corrected snapshot, latest operational view, official
performance-measurement version, data-arrival timestamp. Never silently rewrite history.

## Measure additivity (classify every measure)

| Measure | Across items/orgs | Across time | Handling |
|---|---|---|---|
| Receipt / shipped / movement qty | Sum | Sum | fully additive (movement is signed) |
| On-hand balance | Sum at same instant | **Do NOT sum** | end-of-period / point-in-time |
| Projected available balance | Sum w/ constraints | Do NOT sum | snapshot / as-of |
| Safety stock | Sum at same grain | Do NOT sum blindly | approved snapshot |
| Forecast qty | Sum within one vintage | **Not across vintages** | filter to one snapshot/version |
| On-time % / accuracy % | Do NOT sum | Do NOT sum | sum numerator & denominator, then divide |
| Unit cost | Not additive | Not additive | weighted average / defined valuation |
| Extended inventory value | Sum at same snapshot | Do NOT sum over time | qty × valid cost |

Inventory balances are **semi-additive**: totaling across products/locations at one instant is
fine; adding Mon+Tue+Wed inventory is meaningless — use an as-of filter or `LAST_VALUE`, never
`SUM` across dates. For ratios preserve numerator/denominator
(`sum(on_time)/sum(expected)`, **not** `avg(location_pct)`).

## Join discipline (joins are business relationships)

Before any join document: left/right grains; expected cardinality (1:1 / 1:M / M:1 / M:M);
natural & surrogate keys; effective-date needs; null/unknown-member handling; expected unmatched
%; whether it can multiply measures; whether a side must be pre-aggregated/deduplicated;
reconciliation totals before and after.

**SCD2 fact-to-dimension** — business key alone is insufficient; join to the row valid at event
time:
```sql
fact.item_id = dim.item_id
AND fact.event_ts >= dim.effective_from
AND fact.event_ts <  dim.effective_to
```
Reuse an EDW-provided surrogate key on the fact rather than reconstructing history.

**Fact-to-fact — never join detailed facts then aggregate** (fanout multiplies quantities).
Aggregate each independently to the conformed grain, then join:
```
aggregate plan │ aggregate receipts │ aggregate shipments │ select end-of-week inventory
      └──────────────── join conformed results at SKU × Org × Week ────────────────┘
```

## Sparse comparisons — scaffold pattern

Plan-vs-actual is sparse; an inner join hides the exceptions planners need. Build the complete
item–org–week key set × comparison periods, aggregate each source, LEFT JOIN each to the scaffold,
**preserve plan-only and actual-only rows** (actual with no plan, plan with no actual, new SKU in
latest-only, discontinued SKU in history-only, inventory at a location with no demand).

## Window functions (define frames explicitly)

`ROW_NUMBER()` (latest/dedupe) · `LAG()`/`LEAD()` (prior/next period) · `FIRST_VALUE()`/
`LAST_VALUE()` (opening/ending) · running `SUM()` · rolling `AVG()` · `RANK()`/`PERCENT_RANK()`
(exception severity) · conditional window aggregates (pivot vintages to current/prior) ·
gap-and-island (consecutive shortage weeks). `LAST_VALUE()` returns the current row unless the
frame is `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`; still reduce to one intended
weekly row so repeated end-of-week balances don't enter downstream sums.

## Star default, snowflake selective

Star schema is the default for curated Gold + semantic layer (AI/BI, Genie, metric views, planner
exploration, reusable KPIs, feature prep, App read models). Snowflake **only** where normalizing a
hierarchy gives a real governance/maintenance benefit (item→product line→category→BU; org→region→
country; customer→channel→geography; supplier site→supplier→parent; component→subassembly→FG).

> **Normalize where governance demands it; present a star where analytics benefits from it.**
Expose frequently-used hierarchy attributes in a flattened conformed dimension while the mastered
hierarchy stays normalized underneath.

## Many-to-many — bridge tables, not multiplying joins

Never flatten M:M into comma-separated fields or join directly (multiplies facts). Candidate
bridges: `bridge_item_supplier`, `bridge_product_component`, `bridge_kit_item`,
`bridge_event_customer`, `bridge_exception_root_cause`, `bridge_recommendation_exception`,
`bridge_inventory_demand_eligibility`. Include allocation weights only where the business has a
valid rule; a bridge without one must not be used to sum a measure across members.

## Conformed dimensions & bus matrix

Governed shared dimensions used consistently across demand/planning/procurement/manufacturing/
inventory/shipping/exceptions/actions: Date & planning calendar · Item/SKU · Product hierarchy ·
Inventory org & DC · Supplier & site · Customer & hierarchy · Planner/buyer/ownership ·
Plan/scenario/forecast vintage · PO/SO (degenerate) · UoM · Currency · Exception type & root cause
· Action & approval status · Source system.

Preliminary Milwaukee bus matrix (architectural starting point — verify against the real EDW):

| Business process | Date | Item | Org | Supplier | Customer | Planner | Plan/vintage |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Demand plan | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Supply-plan snapshot | ✓ | ✓ | ✓ | ✓ |  | ✓ | ✓ |
| PO receipt | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |
| Sales shipment | ✓ | ✓ | ✓ |  | ✓ |  |  |
| Inventory snapshot | ✓ | ✓ | ✓ |  |  | ✓ |  |
| Forecast event | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Exception | ✓ | ✓ | ✓ | opt | opt | ✓ | ✓ |
| Planner action | ✓ | ✓ | ✓ | opt | opt | ✓ | opt |

## Medallion architecture — pragmatic

| Layer | Supply-chain purpose | Example |
|---|---|---|
| Bronze | source fidelity + ingestion evidence | raw Oracle CDC, API responses, uploaded planning files |
| Silver | clean, dedupe, type, conform, retain atomic detail | receipt txn, shipment event, inventory & supply-plan snapshots |
| Gold | supply-chain semantics + dimensional modeling + aggregation | weekly actual-vs-plan, exceptions, event forecast |
| Semantic | trusted measures & relationships | attainment, variance, bias, severity (Metric Views) |
| Operational | mutable workflow state | Lakebase cases, assignments, approvals, actions |

Semantic and operational are useful **labels, not extra mandatory medals**. Medallion is NOT:
dev/test/prod; the same as Kimball; Lakebase; Databricks Apps; a mandate to copy every EDW table
three times or build three pipelines per use case. **If an existing `prod_edw` table is already
governed, cleaned, and historized, reuse it as an authoritative source** rather than manufacturing
Bronze/Silver copies to satisfy a diagram. Kimball stars live in Gold; Lakebase sits alongside as
the transactional workflow store.
