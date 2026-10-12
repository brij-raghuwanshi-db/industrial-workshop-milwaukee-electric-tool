# Executing the Model the Databricks Way

Do not design a warehouse on paper, generate database-agnostic SQL/PySpark, and merely run it
inside Databricks. Apply the modeling discipline (`dimensional-modeling.md`) as **executable
Databricks architecture** — Unity Catalog, Delta, Lakeflow, Databricks SQL, metric views, AI/BI,
Genie, Apps, Lakebase, Query Profile, DABs.

The working process for Milwaukee data:

> **Inspect in Databricks → declare the business grain → profile keys & cardinality → select the
> correct Delta/Lakeflow dataset type → implement incrementally → reconcile → inspect Query
> Profile → publish governed semantics → connect dashboard/Genie/App → validate the planner
> workflow → promote through DAB & CI/CD when appropriate.**

## Warehousing concept → Databricks-native implementation

| Concept | Databricks-native implementation |
|---|---|
| Atomic facts | Governed Unity Catalog Delta tables |
| Incremental event facts | Lakeflow streaming tables / incremental pipelines |
| Current-state dimensions | Materialized views (when recomputation correctness matters) |
| Historical SCD2 dimensions | Streaming tables with Lakeflow `AUTO CDC` (SCD 1/2) |
| Weekly snapshots | Idempotent Lakeflow pipeline keyed by snapshot date, target week, item, org, plan version |
| Star/snowflake semantics | Unity Catalog metric views over Gold facts & dimensions |
| Reusable metrics | Metric-view measures, filters, joins, window measures |
| Ad hoc investigation | Databricks SQL + Query Profile |
| Dashboard consumption | AI/BI over curated datasets / metric views |
| Genie consumption | Curated metric views + narrowly scoped Gold |
| Application reads | SQL Warehouse, serving tables, or synced Lakebase read models (by latency) |
| Planner writebacks | Lakebase transactional schema |
| Writeback history | Lakebase CDF synchronized into Delta |
| Data-quality controls | Lakeflow expectations, reconciliation tests, monitoring |
| Production delivery | Git, DABs, CI/CD after workspace validation |

## Dataset choice matters (don't default everything to a Delta/streaming table)

- **Streaming table** — append-oriented receipts, shipments, movements, action events.
- **Materialized view** — dimension joins, corrected aggregates, results that must recompute when
  dimension data changes.
- **SCD2 streaming table** — historical item/supplier/org/planner attributes.
- **Standard view** — lightweight abstraction, no persisted results.
- **Metric view** — governed semantic definitions for dashboards/Genie/apps.
- **Lakebase table** — mutable workflow state (cases, assignments, approvals, action status).

Key correctness point: **streaming-table joins do not automatically recompute already-processed
rows when a dimension changes; materialized views can.** Use streaming tables when a changed
dimension must NOT retroactively rewrite history; use MVs when it must.

## Joins in Databricks — validate against real tables

Before implementing a join, inspect the actual UC tables and validate: left/right grains; key
uniqueness; expected cardinality; null & unmatched-key behavior; row counts before/after; measure
totals before/after; the **physical query plan**; shuffle size, skew, spill, runtime; whether to
aggregate before joining; whether changing dimension attributes need historical vs current-state
semantics. Let Databricks choose the physical strategy first; add broadcast/merge/shuffle-hash/
skew hints only with Query-Profile evidence — hints are directives, not a substitute for correct
grain and cardinality.

## Databricks SQL, windows, QUALIFY

Write SQL when the operation is naturally relational: weekly aggregations, plan-vs-actual,
snapshot selection, conditional aggregation, `ROW_NUMBER()` dedup, `LAG()` week-over-week, rolling
demand/lead-time, inventory as-of, exception rankings, supplier performance. Define partition/
order/frame explicitly. Use `QUALIFY` to filter window results clearly, e.g. selecting the latest
valid snapshot:

```sql
SELECT *
FROM inventory_snapshot
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY item_key, organization_key, snapshot_date
  ORDER BY source_updated_at DESC, ingestion_timestamp DESC
) = 1;
```

## Weekly-snapshot pipeline — 12-step operation

Not a "truncate and copy" job unless that's demonstrably correct. Track a `snapshot_run`
(snapshot_date, snapshot_timestamp, target_week_start/end, plan_version, source_extract_timestamp,
source_watermark, pipeline_update_id, source/target_row_count, reconciliation_status,
publication_status). Steps:

1. Resolve the business calendar.
2. Determine the eligible plan vintage.
3. Capture/locate the immutable planning state.
4. Aggregate transactions separately by target week.
5. **Select — not sum —** the approved inventory balance.
6. Conform item and organization keys.
7. Join only after each source reaches the comparison grain.
8. Preserve plan-only and actual-only rows.
9. Validate uniqueness at the declared grain.
10. Reconcile quantities and costs with sources.
11. Publish only after quality gates pass.
12. Support safe reruns and late-arriving corrections.

## Semantic layer — define each measure once

The Gold star is not the end. Place a governed Unity Catalog **metric view** over it (star + multi-
hop snowflake; fact-to-dimension joins are many-to-one, left-outer, preserving fact rows). Metric
views can define windowed, cumulative, and semi-additive measures. Define once — not separately in
dashboard SQL, Genie instructions, and App code: planned receipt qty, actual net receipt qty,
receipt variance, on-time numerator/denominator, end-of-week on-hand, projected available balance,
demand-plan attainment, forecast bias, exception cost exposure, open-action count, average
exception-resolution duration.

## Performance — evidence-first sequence (not premature tuning)

Don't reach for partitions/cache/broadcast/custom Spark tuning first. Sequence:

1. Correct grain and model.
2. Correct filters and projections.
3. Aggregate before dangerous fact-to-fact joins.
4. Inspect Query Profile and execution plan.
5. Identify scans, fanout, skew, shuffle, spill.
6. Verify table statistics and data layout.
7. Consider materialization / aggregate tables.
8. Apply liquid clustering where access patterns justify it.
9. Add explicit hints only with evidence.
10. Recheck both correctness and runtime.

Materialized views physically maintain results as source data changes — use selectively when
repeatedly recomputing a complex aggregation is more expensive than maintaining it.

## Don'ts (the old-school reversions to avoid)

Produce database-agnostic warehouse SQL and call it Databricks development · default everything to
PySpark · rebuild Lakeflow/UC capabilities in a custom framework · treat notebooks as the
production architecture · join large atomic facts then aggregate · sum inventory balances across
time · use streaming tables when changed dimensions require recomputation · put business metrics
separately into dashboard SQL / Genie / App code · add Spark tuning without execution evidence ·
force every prototype immediately into a DAB · design models without checking actual Databricks
schemas, keys, volumes, and query behavior.
