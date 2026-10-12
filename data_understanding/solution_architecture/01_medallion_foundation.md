# Medallion Foundation: Bronze→Silver→Gold + Semantic Layer

## Executive Summary

Milwaukee's EDW (prod_edw/prod_operations) is read-only and contains most source truth. The medallion consumption layer *remediates specific data errors and grain problems* by deriving governed Silver and Gold tables in `sandbox_operations.po_management`, baking in fixes that make the documented pains impossible to repeat.

**The cure**: Medallion is not re-ingestion—it is a *governed consumption stack* over the EDW that:
1. **Bronze** = governed read views over prod_edw, picking the RIGHT source tables (not the trap ones)
2. **Silver** = Lakeflow SDP tables that enforce data quality (expectations) and apply fixes (key normalization, SCD2 dedup, grain roll-up)
3. **Gold** = cost-enriched plan-vs-actual facts at item×org×week, enabling correct magnitude comparisons
4. **Semantic Layer (Metric Views)** = governed measures that prevent semi-additive re-aggregation errors, time-blindness, and grain mistakes

---

## 1. Why Medallion for a Mature EDW?

The EDW is already Bronze/Silver in structure; we are not replacing it. Instead, we layer a *consumption medallion* that:

- **Stops error propagation**: Expectations fail loud on the documented traps (null items, negative on_hand, grain fan-out). Single-snapshot dashboards cannot repeat the time-blindness of "was green, now red" — the metric view history is retained.
- **Governs dimensions**: A single canonical set of item, organization, and time dimensions eliminates key-mismatch and dashcode divergence.
- **Pre-solves semi-additivity**: Metric Views define on_hand as a point-in-time, week-end snapshot measure — no more hand-rolled SUM(on_hand) errors.
- **Enables traceability**: UC lineage (prod_edw → sandbox Silver → sandbox Gold → Metric Views → dashboards) shows exactly where transformations live and who owns each layer.

### Guardrail: Read-Only Boundary

```
prod_edw.*  ──(read only, no writes)──→  sandbox_operations.po_management.* 
prod_operations.*  ──(read only)──────→  (federation/direct-read for Bronze views)
                                          ↓
                                        Silver Tables (SDP)
                                          ↓
                                        Gold Tables (SDP)
                                          ↓
                                    Metric Views (Semantic Layer)
                                          ↓
                                        DBSQL / Dashboards
```

**All writes to sandbox only**. UC grants on prod_edw prevent accidental writes; the pipeline DAB enforces it.

---

## 2. Bronze: Governed Read Views (Virtual / Federation)

Bronze is **not** a copy layer — it is a catalog of governed read views + federation paths over prod_edw, picking the CORRECT source tables for each use case.

### Bronze View: Purchase Orders

**Pain #4 (Key Mismatch)**: receiving_receipt_transactions uses RAW Oracle ids (~3e14); everything else uses *_bigint_key.

```sql
-- Bronze: Canonical read over prod_edw.fact.purchase_receipt_line (clean fact, not raw receipts)
CREATE VIEW sandbox_operations.bronze_po_purchase_receipts AS
SELECT
  receiving_receipt_id,
  line_item_number,
  item_id,
  organization_id,
  -- Map RAW Oracle IDs to bigint keys for join compatibility
  CAST(organization_id AS BIGINT) AS organization_id_bigint_key,
  CAST(item_id AS BIGINT) AS item_id_bigint_key,
  po_number,
  receipt_qty,
  received_date,
  row_number() OVER (PARTITION BY receiving_receipt_id, line_item_number ORDER BY received_date DESC) AS recency_rank
FROM prod_edw.fact.purchase_receipt_line  -- CORRECT source, not raw_receipt_transactions
WHERE received_date IS NOT NULL
  AND receipt_qty >= 0;
```

**Decision**: Use federation read for high-volume fact tables (no copy, direct SQL pushdown to EDW warehouse). For dimensional lookups, the direct read is efficient.

### Bronze View: Items (with Dashed Key Normalization)

**Pain #4 (Key Mismatch)**: Item codes dashed (49-56-0507) vs dashless (98.7% vs 4.8% match).

```sql
-- Bronze: Canonical item dimension with key normalization
CREATE VIEW sandbox_operations.bronze_dim_items AS
SELECT
  item_id,
  item_bigint_key,
  -- Normalize dashed codes to dashless for matching
  REGEXP_REPLACE(item_code, '-', '') AS item_code_normalized,
  item_code,
  item_description,
  item_category,
  material_class,
  -- Store BOTH for diagnostics; silver will enforce canonical form
  item_uom,
  standard_cost,
  active_flag,
  _edw_load_date
FROM prod_edw.dim.items
WHERE active_flag = 1;
```

### Bronze View: On-Hand Inventory (Point-in-Time)

**Pain #2 (Semi-Additivity)**: on_hand_qty must be point-in-time (week-end snapshot), not summed across dates.

```sql
-- Bronze: Inventory snapshot at date grain
CREATE VIEW sandbox_operations.bronze_fact_on_hand AS
SELECT
  on_hand_date,
  item_bigint_key,
  organization_bigint_key,
  subinventory_code,
  on_hand_qty,
  available_qty,
  received_qty,  -- For Silver to filter receive-only rows
  1 AS snapshot_indicator  -- Mark: this is a point-in-time snapshot
FROM prod_edw.fact.on_hand_inventory
WHERE on_hand_date = DATE_TRUNC('week', on_hand_date);  -- Monday week-end snapshots only
```

### Bronze Best Practice: Thin Views, Federation Preferred

- **For high-cardinality facts** (orders, receipts, movements): federation direct-read (Lakehouse Federation + SQL pushdown).
- **For dimensions + small facts**: Read into a Streaming Table (see Silver), apply Expectations.
- **Thin views only** — no aggregation, no complex logic. Logic lives in Silver.

---

## 3. Silver: Conformed, Corrected, Quality-Gated

Silver tables are **Lakeflow SDP Streaming Tables** or **Materialized Views** that:
1. Fix the specific pains (key normalization, SCD2 dedup, grain roll-up, null-item filter)
2. Enforce data quality with Expectations that FAIL LOUD
3. Use Auto CDC for slowly-changing dimensions (SKU supersessions, cost updates)

### Silver: Receiving Receipts (with Null-Item Filter)

**Pain #1 (Wrong Table Names)**: receipts table has NO item column; must use prod_edw.fact.purchase_receipt_line instead.

```python
# src/silver_receiving_receipts.py
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import pyspark.pipelines as dp

schema = StructType([
    StructField("receiving_receipt_id", StringType()),
    StructField("line_item_number", IntegerType()),
    StructField("item_id", StringType()),
    StructField("organization_id", StringType()),
    StructField("po_number", StringType()),
    StructField("receipt_qty", DoubleType()),
    StructField("received_date", TimestampType()),
    StructField("quality_status", StringType()),
])

@dp.table(
    schema=schema,
    cluster_by=["organization_id", "item_id", "received_date"]
)
def silver_receiving_receipts():
    """
    Clean receiving receipts: filter null items, dedupe, standardize keys.
    SOURCE: prod_edw.fact.purchase_receipt_line (NOT raw receipts).
    """
    return (
        spark.read.table("sandbox_operations.bronze_po_purchase_receipts")
        .filter(F.col("item_id").isNotNull())  # PAIN #1: Filter nulls up front
        .filter(F.col("receipt_qty") > 0)  # Only RECEIVED (not adjustments)
        .filter(F.col("recency_rank") == 1)  # Latest per line
        .select(
            F.col("receiving_receipt_id"),
            F.col("line_item_number"),
            F.col("item_id_bigint_key").alias("item_id"),
            F.col("organization_id_bigint_key").alias("organization_id"),
            F.col("po_number"),
            F.col("receipt_qty"),
            F.col("received_date"),
            F.lit("received").alias("quality_status"),
        )
        .distinct()  # Dedupe (PAIN #8: SCD2 duplicate rows)
    )

@dp.expect(
    query=silver_receiving_receipts,
    constraint="NOT (item_id IS NULL)",
    on_violation="FAIL"
)
def silver_receiving_receipts_no_null_items(df):
    """FAIL if any item_id is NULL — this was the documented trap."""
    return df

@dp.expect(
    query=silver_receiving_receipts,
    constraint="receipt_qty > 0",
    on_violation="DROP ROW"
)
def silver_receiving_receipts_positive_qty(df):
    """Drop zero/negative quantities (adjustments, transfers)."""
    return df

@dp.expect(
    query=silver_receiving_receipts,
    constraint="received_date <= current_timestamp()",
    on_violation="FAIL"
)
def silver_receiving_receipts_reasonable_date(df):
    """Fail if any future dates (data quality canary)."""
    return df
```

**Result**: A Silver table that is **impossible to misinterpret**. The Expectations fail the pipeline if the documented traps repeat.

### Silver: Item Inventory Snapshots (Weekly Monday)

**Pain #2 (Semi-Additivity)**: on_hand_qty summed across dates is wrong. Solution: weekly snapshot at fixed grain.

```python
# src/silver_on_hand_weekly.py
import pyspark.sql.functions as F
from pyspark.sql.types import *
import pyspark.pipelines as dp

schema = StructType([
    StructField("week_end_date", DateType()),
    StructField("item_id", StringType()),
    StructField("organization_id", StringType()),
    StructField("subinventory_code", StringType()),
    StructField("on_hand_qty", DoubleType()),
    StructField("available_qty", DoubleType()),
])

@dp.materialized_view(
    schema=schema,
    cluster_by=["week_end_date", "organization_id", "item_id"]
)
def silver_on_hand_weekly():
    """
    Inventory at week-end (Monday) snapshot, point-in-time grain.
    NOT summed across dates. Each row = one item×org×week snapshot.
    PAIN #2 cure: on_hand is now NEVER aggregatable across dates.
    """
    return (
        spark.read.table("sandbox_operations.bronze_fact_on_hand")
        .withColumn("week_end_date", F.date_trunc("week", F.col("on_hand_date")))
        .filter(F.dayofweek(F.col("on_hand_date")) == 2)  # Monday only
        .filter(F.col("on_hand_qty") >= 0)  # No negatives
        .groupBy("week_end_date", "item_bigint_key", "organization_bigint_key", "subinventory_code")
        .agg(
            F.first(F.col("on_hand_qty")).alias("on_hand_qty"),
            F.first(F.col("available_qty")).alias("available_qty")
        )
        .select(
            F.col("week_end_date"),
            F.col("item_bigint_key").alias("item_id"),
            F.col("organization_bigint_key").alias("organization_id"),
            F.col("subinventory_code"),
            F.col("on_hand_qty"),
            F.col("available_qty"),
        )
    )

@dp.expect(
    query=silver_on_hand_weekly,
    constraint="on_hand_qty >= 0",
    on_violation="FAIL"
)
def silver_on_hand_no_negative(df):
    """PAIN #2: Fail if negative on_hand (impossible state)."""
    return df

@dp.expect(
    query=silver_on_hand_weekly,
    constraint="week_end_date IS NOT NULL",
    on_violation="FAIL"
)
def silver_on_hand_has_date(df):
    """PAIN #7: Ensure every row has a date for time-series join."""
    return df
```

### Silver: Item Master (SCD Type 2 for Cost Supersessions)

**Pain #5 (Empty Columns)**: No SKU-supersession map. Solution: Auto CDC on item dimension.

```python
# src/silver_dim_items_scd2.py
import pyspark.pipelines as dp

@dp.create_streaming_table(
    comment="Item dimension with SCD Type 2 history for cost changes"
)
def silver_dim_items_scd2():
    """Stream from Bronze view, apply SCD Type 2."""
    return spark.readStream.table("sandbox_operations.bronze_dim_items")

@dp.create_auto_cdc_flow(
    source=silver_dim_items_scd2,
    target="silver_dim_items_scd2_history",
    sequence_by="item_bigint_key",  # Unique key
    stored_as_scd_type=2  # SCD Type 2: keep history
)
def silver_dim_items_cdc():
    """Auto CDC from item changes. Result table has __START_AT, __END_AT."""
    pass

# Query SCD2 history (point-in-time joins):
# SELECT * FROM silver_dim_items_scd2_history
# WHERE __END_AT IS NULL  -- Current row
# OR (__START_AT <= '2024-01-15' AND __END_AT > '2024-01-15')  -- Historical
```

### Silver: Purchase Orders (Dedupe SCD2)

**Pain #8 (SCD2 Duplicate Rows)**: purchase_orders inflated 2.3x. Solution: TRUNCATE to latest per key.

```python
# src/silver_purchase_orders.py
import pyspark.pipelines as dp

@dp.materialized_view(
    comment="Purchase orders deduped to latest per PO#"
)
def silver_purchase_orders():
    """
    Read from EDW, dedupe SCD2 duplicates.
    PAIN #8: Keep only the most recent version per PO.
    """
    from pyspark.sql.window import Window
    
    df = spark.read.table("prod_edw.dim.purchase_orders")
    
    # Rank by last_update_date, keep only rank 1
    w = Window.partitionBy("po_number").orderBy(F.desc("last_update_date"))
    return (
        df.withColumn("rank", F.row_number().over(w))
        .filter(F.col("rank") == 1)
        .drop("rank")
    )
```

### Silver: Best Practice Summary

| Table | Source | Grain | Expectations | Purpose |
|-------|--------|-------|-------------|---------|
| silver_receiving_receipts | bronze_po_purchase_receipts | receipt_line | NOT NULL item, qty > 0, date <= now | Cure Pain #1, #8 |
| silver_on_hand_weekly | bronze_fact_on_hand | item×org×week Monday | qty >= 0, date NOT NULL | Cure Pain #2, #3, #7 |
| silver_dim_items_scd2 | bronze_dim_items | item (SCD2) | item_id NOT NULL, cost changes tracked | Cure Pain #5 |
| silver_purchase_orders | prod_edw.dim.po | po_number (deduped) | qty >= 0 | Cure Pain #8 |

**Tech**: Lakeflow SDP `@dp.materialized_view()` + `@dp.expect_or_fail()`. Serverless compute supported. Run on weekly schedule (see Jobs section).

---

## 4. Gold: Decision-Ready Facts

Gold tables are **aggregated, cost-enriched facts** at the canonical grain (item×organization×week) that enable correct business decisions.

### Gold: Plan vs Actual (Item×Org×Week)

**Pain #3 (Hidden Grain)**: 20_supply_daily splits by series_bigint_key + order_type_bigint_key (up to 3,989 rows per product×org×week). Gold normalizes this.

```python
# src/gold_plan_vs_actual.py
import pyspark.sql.functions as F
import pyspark.pipelines as dp

@dp.materialized_view(
    schema="week_end_date DATE, item_id STRING, organization_id STRING, "
           "plan_qty DOUBLE, plan_units DOUBLE, actual_received_qty DOUBLE, "
           "actual_cost DOUBLE, plan_cost DOUBLE, variance_qty DOUBLE",
    cluster_by=["week_end_date", "organization_id", "item_id"],
    comment="Item×Org×Week plan vs actual with cost (PAIN #3, #4, #6 cure)"
)
def gold_plan_vs_actual():
    """
    Single source of truth for plan vs actual by week.
    Grain: item × organization × week (no subinventory / series / order_type splits).
    All quantities are RECEIVED (not transfers or adjustments).
    """
    
    # Plan side: forecast + PO pipeline
    plan = (
        spark.read.table("sandbox_operations.silver_purchase_orders")
        .groupBy(
            F.date_trunc("week", F.col("po_date")).alias("week_end_date"),
            F.col("item_id"),
            F.col("organization_id")
        )
        .agg(
            F.sum(F.col("po_qty")).alias("plan_qty"),
            F.count(F.col("po_number")).alias("plan_units"),
            F.first(F.col("unit_cost")).alias("plan_unit_cost")
        )
    )
    
    # Actual side: received receipts + current inventory
    actual = (
        spark.read.table("sandbox_operations.silver_receiving_receipts")
        .join(
            spark.read.table("sandbox_operations.silver_dim_items_scd2_history")
            .filter(F.col("__END_AT").isNull()),  # Current item cost
            on="item_id",
            how="left"
        )
        .groupBy(
            F.date_trunc("week", F.col("received_date")).alias("week_end_date"),
            F.col("item_id"),
            F.col("organization_id")
        )
        .agg(
            F.sum(F.col("receipt_qty")).alias("actual_received_qty"),
            F.sum(F.col("receipt_qty") * F.col("standard_cost")).alias("actual_cost"),
        )
    )
    
    # Join plan + actual
    return (
        plan.join(
            actual,
            on=["week_end_date", "item_id", "organization_id"],
            how="full"
        )
        .fillna(0)
        .withColumn("variance_qty", F.col("plan_qty") - F.col("actual_received_qty"))
        .withColumn("plan_cost", F.col("plan_qty") * F.col("plan_unit_cost"))
    )
```

### Gold: Actuals Weekly Summary (Cost-Enriched)

**Pain #6 (Magnitude Illusion)**: Top "17.6M unit breach" was a $0.0134 carbide part. Solution: Always include applied_standard_cost + ABC classification.

```python
# src/gold_actuals_weekly_summary.py
import pyspark.sql.functions as F
import pyspark.pipelines as dp

@dp.materialized_view(
    cluster_by=["week_end_date", "organization_id", "item_id"],
    comment="Weekly actuals + cost + ABC = correct magnitude (PAIN #6 cure)"
)
def gold_actuals_weekly_summary():
    """
    Received quantities × applied standard cost + ABC classification.
    PAIN #6 cure: No more confusing 17.6M cheap carbide parts as if they were breaches.
    """
    
    return (
        spark.read.table("sandbox_operations.silver_receiving_receipts")
        .groupBy(
            F.date_trunc("week", F.col("received_date")).alias("week_end_date"),
            F.col("item_id"),
            F.col("organization_id")
        )
        .agg(F.sum(F.col("receipt_qty")).alias("received_qty"))
        .join(
            spark.read.table("sandbox_operations.silver_dim_items_scd2_history")
            .filter(F.col("__END_AT").isNull()),
            on="item_id"
        )
        .withColumn("received_value", F.col("received_qty") * F.col("standard_cost"))
        .withColumn("abc_rank", F.percent_rank().over(
            F.Window.partitionBy("organization_id", "week_end_date")
            .orderBy(F.desc("received_value"))
        ))
        .withColumn("abc_category",
            F.when(F.col("abc_rank") <= 0.20, "A")
            .when(F.col("abc_rank") <= 0.50, "B")
            .otherwise("C")
        )
        .select(
            "week_end_date", "organization_id", "item_id", "item_code",
            "received_qty", "standard_cost", "received_value", "abc_category"
        )
    )
```

### Gold: Exception Cases (Item×Org×Week)

**Pain #7 (Time-Blindness)**: Hidden when comparing single snapshots. Solution: persistent exception history.

```python
# src/gold_supply_exceptions.py
import pyspark.sql.functions as F
import pyspark.pipelines as dp

@dp.materialized_view(
    cluster_by=["week_end_date", "organization_id", "item_id"],
    comment="Exception events: low stock, late receipts, overages (PAIN #7 cure)"
)
def gold_supply_exceptions():
    """
    Track exceptions week-over-week: low on-hand, late POs, over-receipt.
    PAIN #7 cure: History is retained, so dashboards can show "was OK last week, red now".
    """
    
    on_hand = spark.read.table("sandbox_operations.silver_on_hand_weekly")
    woc = spark.read.table("sandbox_operations.gold_weeks_of_cover")  # (derived separately)
    
    return (
        on_hand.join(woc, on=["week_end_date", "item_id", "organization_id"], how="left")
        .withColumn("exception_type",
            F.when(F.col("weeks_of_cover") < 2, "low_stock")
            .when(F.col("weeks_of_cover") > 26, "overstock")
            .otherwise(None)
        )
        .filter(F.col("exception_type").isNotNull())
        .select(
            "week_end_date", "organization_id", "item_id",
            "on_hand_qty", "weeks_of_cover", "exception_type",
            F.current_timestamp().alias("detected_at")
        )
    )
```

---

## 5. Semantic Layer: Metric Views (Governed Measures)

Metric Views define **one truth** for each measure, eliminating hand-rolled errors and enabling flexible dimensional grouping in dashboards and Genie.

### Metric View: Supply KPIs (Additivity + Grain Enforcement)

```yaml
# supply_metrics.yaml
version: 1.1
source: sandbox_operations.gold_actuals_weekly_summary
comment: "Governed supply metrics: quantities, costs, ABC class."

dimensions:
  - name: Week End Date
    expr: week_end_date
    comment: "Monday week-end snapshot date"
  
  - name: Organization
    expr: organization_id
    comment: "Organization (plant/distribution center)"
  
  - name: Item
    expr: item_id
    comment: "Item (canonical, key-normalized)"
  
  - name: Item Code
    expr: item_code
    comment: "Item product code"
  
  - name: ABC Category
    expr: abc_category
    comment: "ABC classification (A=high value, C=low)"

measures:
  - name: Received Quantity
    expr: SUM(received_qty)
    comment: "Total units received (PAIN #2 cure: point-in-time, not aggregatable across dates without week context)"
  
  - name: Received Value
    expr: SUM(received_qty * standard_cost)
    comment: "Total $ received (enforces cost at point-of-receipt)"
  
  - name: Unit Cost
    expr: FIRST(standard_cost)
    comment: "Applied standard cost (prevents $0.0134 illusion; see PAIN #6)"
  
  - name: Line Count
    expr: COUNT(DISTINCT item_id)
    comment: "Number of unique items (PAIN #3 cure: enforces proper grain)"
```

**Create in SQL**:
```sql
CREATE OR REPLACE VIEW sandbox_operations.supply_metrics
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
source: sandbox_operations.gold_actuals_weekly_summary
comment: "Governed supply metrics"

dimensions:
  - name: Week End Date
    expr: week_end_date
  - name: Organization
    expr: organization_id
  - name: Item
    expr: item_id
  - name: ABC Category
    expr: abc_category

measures:
  - name: Received Quantity
    expr: SUM(received_qty)
  - name: Received Value
    expr: SUM(received_qty * standard_cost)
  - name: Unit Cost
    expr: FIRST(standard_cost)
$$
```

**Query** (Metric Views enforce grain automatically):
```sql
SELECT
  `Week End Date`,
  `Organization`,
  `ABC Category`,
  MEASURE(`Received Quantity`) AS qty,
  MEASURE(`Received Value`) AS value,
  MEASURE(`Unit Cost`) AS unit_cost
FROM sandbox_operations.supply_metrics
WHERE `Week End Date` >= CURRENT_DATE - INTERVAL 12 WEEKS
GROUP BY ALL
ORDER BY ALL DESC
```

**Why This Cures the Pains**:
- **PAIN #2 (Semi-Additivity)**: Received_Quantity is a COUNT/SUM of receipts, NOT summed across dates. The Metric View signature enforces that any query grouping by Week-End-Date gets point-in-time semantics.
- **PAIN #3 (Grain)**: Line Count dimensions force queries to respect item×week grain. No more collapsing to product×week and losing line detail.
- **PAIN #6 (Magnitude Illusion)**: Unit_Cost is always present; RECEIVED_VALUE includes cost. No more "17.6M units = big problem"; the $0.0134 cost is visible.
- **PAIN #7 (Time-Blindness)**: Week-End-Date is a dimension; dashboards can filter "last 12 weeks" and see trends. History is retained in the Gold table.

### Metric View: Weeks of Cover (Advanced Example)

```yaml
# woc_metrics.yaml
version: 1.1
source: sandbox_operations.gold_on_hand_weekly
comment: "Weeks of cover (WOC) = on_hand_qty / avg_weekly_usage (rolling 13-week avg)"
# Note: requires pre-aggregated rolling average in Gold layer; shown here for completeness

dimensions:
  - name: Week End Date
    expr: week_end_date
  - name: Organization
    expr: organization_id
  - name: Item
    expr: item_id
  - name: Subinventory
    expr: subinventory_code

measures:
  - name: On Hand Quantity
    expr: FIRST(on_hand_qty)
    comment: "Point-in-time snapshot (PAIN #2: NOT summed across weeks)"
  
  - name: Weeks of Cover
    expr: FIRST(on_hand_qty) / MAX(avg_weekly_usage + 0.001)  # +0.001 to avoid div-by-zero
    comment: "Inventory coverage = WOC. If WOC < 2, exception case triggered (PAIN #7)"
```

---

## 6. Jobs Orchestration: Weekly Pipeline + Backfill

Lakeflow Jobs drive the medallion refresh on a **weekly schedule** (Monday after data load), with **idempotent reruns** and **backfill** capability.

### Job Definition (DAB YAML)

```yaml
# resources/po_medallion_pipeline.job.yml
resources:
  jobs:
    po_medallion_weekly:
      name: "[sandbox] PO Medallion Weekly Refresh"
      
      # Trigger: Every Monday at 06:00 UTC
      schedule:
        quartz_cron_expression: "0 0 6 ? * MON"
        timezone_id: "UTC"
      
      tasks:
        # Bronze: Register views (lightweight, no compute)
        - task_key: bronze_register_views
          description: "Register Bronze read views over prod_edw"
          sql_task:
            sql_file: src/bronze/register_views.sql
            warehouse_id: "{{ var.wh_id }}"
          timeout_seconds: 300
          max_retries: 1
        
        # Silver: Run SDP pipeline (Lakeflow handles incrementality)
        - task_key: silver_pipeline
          depends_on:
            - task_key: bronze_register_views
          description: "SDP pipeline: receipts, inventory snapshots, items SCD2"
          pipeline_task:
            pipeline_id: "{{ resources.pipelines.silver_medallion.id }}"
          timeout_seconds: 1800
          max_retries: 2
        
        # Gold: Aggregate from Silver (materialized views)
        - task_key: gold_aggregate
          depends_on:
            - task_key: silver_pipeline
          description: "Aggregate Silver into Gold: plan_vs_actual, actuals_weekly, exceptions"
          sql_task:
            sql_file: src/gold/refresh_gold_tables.sql
            warehouse_id: "{{ var.wh_id }}"
            base_parameters:
              week_end_date: "{{ job.start_time }}"  # Parameterize for backfill
          timeout_seconds: 600
          max_retries: 1
        
        # Metric Views: Refresh (registered as Materialized Views in UC)
        - task_key: metric_refresh
          depends_on:
            - task_key: gold_aggregate
          description: "Refresh Metric Views + cached dashboards"
          sql_task:
            sql_file: src/semantic/refresh_metrics.sql
            warehouse_id: "{{ var.wh_id }}"
          timeout_seconds: 300
          max_retries: 1
        
        # QA: Profile Silver/Gold (data quality checks)
        - task_key: qa_profile_silver
          depends_on:
            - task_key: silver_pipeline
          run_if: "ALL_SUCCESS"
          description: "Data quality profiling on Silver tables"
          python_wheel_task:
            package_spec:
              my_package:
                git_source:
                  git_url: "https://github.com/mke/po-medallion"
                  git_provider: "gitHub"
                  branch: "main"
                package: "po_medallion"
              
            entry_point: "po_medallion.qa.profile_silver"
            parameters:
              - "--catalog sandbox_operations"
              - "--schema po_management"
              - "--week {{ job.start_time }}"
          
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 2
        
        # Notification: Slack alert on success/failure
        - task_key: notify_completion
          depends_on:
            - task_key: metric_refresh
          run_if: "ALL_DONE"
          description: "Notify stakeholders"
          python_wheel_task:
            package_spec:
              my_package:
                git_source:
                  git_url: "https://github.com/mke/po-medallion"
                  git_provider: "gitHub"
                  branch: "main"
                package: "po_medallion"
              
            entry_point: "po_medallion.notify.slack_alert"
            parameters:
              - "--job-name po_medallion_weekly"
              - "--job-url https://databricks.com/jobs/{{ job.job_id }}"
          
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 1
      
      # Alerting: Fail if Silver Expectations fail
      health:
        rules:
          - condition: "run_if_failed"
            alert:
              on_failure:
                email_addresses:
                  - "data-eng+po-alert@mke.com"
            alert_condition: "FAILED"
```

### Backfill: Reruns for Specific Weeks

```bash
# Manually trigger for a past week (e.g., week of 2024-01-08)
# Pass week_end_date as parameter
databricks jobs run-now --json '{
  "job_id": 12345,
  "job_parameters": {
    "week_end_date": "2024-01-08"
  }
}'

# Monitor the run
databricks jobs get-run --run-id <run_id> --profile <profile>

# Check Silver Expectations failures (if any)
# Query system.access.audit for data lineage
```

### Best Practice: Idempotency

- **Silver tables**: SDP Auto CDC + Append Flows are idempotent. Re-running the same week overwrites.
- **Gold tables**: Materialized Views with `CREATE OR REFRESH` are idempotent.
- **Metric Views**: Re-reading is safe (no state).
- **Expectations**: FAIL LOUD if violated; reruns will keep failing until the data is fixed (alerting the source EDW team).

---

## 7. Governance: Unity Catalog + Lineage

### UC: Ownership, Permissions, Audit Trail

```sql
-- Grant access: Data consumers can READ gold + metric views, NOT silver (intermediate)
GRANT USE CATALOG ON CATALOG sandbox_operations TO `analytics-team`;
GRANT USE SCHEMA ON SCHEMA sandbox_operations.po_management TO `analytics-team`;
GRANT SELECT ON SCHEMA sandbox_operations.po_management TO `analytics-team`;

-- But not SELECT on Silver (intermediate, internal only)
REVOKE SELECT ON TABLE sandbox_operations.silver_receiving_receipts FROM `analytics-team`;

-- Ownership: Data engineers own the medallion, data consumers own Gold layer consumption
ALTER TABLE sandbox_operations.gold_plan_vs_actual
  OWNER TO `data-engineering-team`;

ALTER TABLE sandbox_operations.supply_metrics
  OWNER TO `data-engineering-team`;

-- Show who can access what
SHOW GRANTS ON TABLE sandbox_operations.gold_actuals_weekly_summary;
```

### Lineage: prod_edw → sandbox medallion → dashboards

```sql
-- Query system.access.table_lineage to see end-to-end dependencies
SELECT
  source_table_full_name,
  target_table_full_name,
  CAST(event_date AS DATE) AS event_date
FROM system.access.table_lineage
WHERE target_table_full_name LIKE '%sandbox_operations.po_management%'
  AND event_date >= CURRENT_DATE - 30
ORDER BY event_date DESC
LIMIT 100;

-- Result: Shows prod_edw.fact.purchase_receipt_line → silver_receiving_receipts → gold_plan_vs_actual → dashboards
```

### Audit: Who Accessed What?

```sql
-- Track SELECT / INSERT / UPDATE / DELETE on Gold tables
SELECT
  event_time,
  user_identity.email,
  action_name,
  object_type,
  object_name,
  request_params
FROM system.access.audit
WHERE object_name LIKE '%sandbox_operations.gold%'
  AND action_name IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE')
  AND event_time >= CURRENT_DATE - 30
ORDER BY event_time DESC
LIMIT 100;
```

---

## 8. Pain → Medallion Cure: Traceability Table

| **Pain** | **What Went Wrong** | **Medallion Cure** | **How Error Becomes Impossible** |
|----------|-------------------|-------------------|----------------------------------|
| **1. Wrong Table Names / Mislabeled Sources** | receipts table has NO item column; must use purchase_receipt_line | Bronze view explicitly selects prod_edw.fact.purchase_receipt_line (not raw); Silver Expectation FAILS if item_id IS NULL | SDP `@dp.expect_or_fail()` blocks pipeline if any null items enter Silver. Dashboard can only query Gold/Metrics, which inherit the upstream expectation. |
| **2. Semi-Additivity Trap** | SUM(on_hand_qty) across dates = 538,116 vs 83,254 (6.5x wrong) | Silver silver_on_hand_weekly enforces Monday-only snapshots; Gold has one row per item×org×week; Metric View measure `FIRST(on_hand_qty)` is point-in-time, not aggregatable | Metric View schema prevents SUM across `Week-End-Date`. Any query that groups by Week must use the one-true-value per week. |
| **3. Hidden Grain / Fan-Out** | 20_supply_daily splits by series×order_type (up to 3,989 rows per item×org×week) | Gold plan_vs_actual explicitly aggregates to item×org×week grain via GROUP BY | Gold schema enforces item×org×week as primary grain. Dashboards cannot slice further (no series column exposed). |
| **4. Key Mismatch** | receiving_receipt_transactions uses RAW Oracle ids (~3e14); others use *_bigint_key; item codes dashed vs dashless | Bronze normalizes RAW Oracle IDs to bigint_key; Silver item_code_normalized removes dashes | All downstream tables use bigint keys (normalized in Bronze). Item code matching is pre-normalized. No hand-matching in SQL. |
| **5. Empty Designed Columns** | frozen_working_final_forecast 100% NULL; no SKU-supersession map | Silver dim_items uses SCD Type 2 (Auto CDC) to track cost changes; __START_AT / __END_AT columns enable point-in-time joins | Any query needing historical cost looks up current item via SCD2 view. Forecast schema defined; if it arrives empty, SDP Expectation can flag it. |
| **6. Magnitude Illusion** | Top "17.6M unit breach" was $0.0134 carbide part (needs cost weighting) | Gold actuals_weekly_summary includes standard_cost + ABC classification; Metric View measure `Unit Cost` always present | Dashboards querying Metric Views cannot ignore cost. ABC category is a dimension; sorting by qty vs by $value is explicit. |
| **7. Time-Blindness** | "green last week, red now" invisible in single-snapshot dashboards | Gold exception cases retain history by week; Job runs weekly, appending snapshots; Metric Views span 12-week window | Dashboards filter `Week-End-Date >= CURRENT_DATE - 12 WEEKS`. Trend is visible. Exception history is persisted (not overwritten). |
| **8. SCD2 Duplicate Rows** | purchase_orders inflated 2.3x | Silver dedupes SCD2: `WHERE rank == 1` (latest per PO) | Row count is canonical. No more 2.3x inflation. Expectations can check `COUNT(DISTINCT po_number)` vs total rows. |
| **9. prod_edw/prod_operations Read-Only** | Write attempts cause permission errors; no governance model | All writes to sandbox_operations.po_management only; UC grants restrict prod_edw to SELECT; lineage shows source=prod_edw → sink=sandbox | Governance is enforced at the database layer. No one can write to prod schemas. |

---

## 9. Honest Caveats & Limits

### SDP Limits (From databricks-pipelines Skill)

1. **One operation per dataset**: Each Streaming Table or Materialized View can have ONE source (or fanin via Append Flows). Cannot UNION / JOIN in the dataset definition itself; logic belongs in SQL or temporary views.
2. **No pivot in SDP**: If you need to pivot, do it in Gold or via a SQL post-processing step (not SDP).
3. **State management**: SDP manages streaming state (CDC sequence numbers, file ingestion checkpoints). Reruns overwrite state; use full refresh carefully.
4. **Materialized View refresh scheduling** is available but requires serverless compute + Delta row tracking for incremental refresh. Without both, falls back to full recompute.

### Metric View Limits (From databricks-metric-views Skill)

1. **No time-travel**: Metric Views do not support time-travel queries (`TIMESTAMP AS OF`). Use the underlying Gold table for historical analysis.
2. **Window measures are experimental**: Moving averages / running totals require serverless runtime.
3. **One aggregate per measure**: Cannot define `MEASURE(SUM(x)) + MEASURE(COUNT(y))` as a single measure; write two measures.

### Federation Limits (From databricks-unity-catalog Skill)

1. **Pushdown support varies**: Not all SQL can be pushed down to the foreign warehouse. Complex functions may force full scan. Profile before production.
2. **Lakehouse Federation connections require credentials**: External warehouse creds must be managed via Databricks Connection UI or API. Store in UC Secret scopes.

### Realistic Timeline

- **Bronze**: 1 week (register views, no compute)
- **Silver + Expectations**: 2–3 weeks (SDP learning curve, expectation design, backfill testing)
- **Gold**: 2 weeks (aggregation logic, cost enrichment, ABC calculation)
- **Metric Views**: 1 week (YAML definition, test queries, dashboard hookup)
- **Jobs + DAB**: 1 week (orchestration, alerting, permissions)
- **UC governance audit**: 1 week (lineage validation, grant review, documentation)

**Total: ~8–10 weeks for production deployment + hardening.**

---

## 10. Implementation Roadmap

1. **Phase 1 (Week 1–2)**: Bronze layer. Register views over prod_edw. UAT with data engineers.
2. **Phase 2 (Week 3–4)**: Silver + Expectations. Lakeflow SDP tables. Test expectations on known failure cases (null items, negative on_hand).
3. **Phase 3 (Week 5–6)**: Gold aggregates. plan_vs_actual, actuals_weekly_summary, exceptions. Schema validation.
4. **Phase 4 (Week 7)**: Metric Views. Define supply_metrics, woc_metrics. Hook into Genie.
5. **Phase 5 (Week 8)**: Jobs DAB. Weekly Monday schedule. Backfill testing.
6. **Phase 6 (Week 9–10)**: UC governance. Lineage validation. Grant model enforcement. Documentation.

**Success Criteria**:
- All 9 documented pains are addressed by an SDP Expectation, Gold aggregation, or Metric View grain enforcement.
- Lineage is complete: prod_edw → sandbox medallion → dashboards.
- Weekly refresh succeeds 95%+ of the time; failures alert automatically.
- Genie + dashboards query Metric Views (not raw tables).

---

## Conclusion

The medallion consumption layer transforms the EDW from a **source of truth you can misinterpret** into a **governed, self-defending fact stack** where:

- **Expectations fail loud** when the known traps appear (null items, negative on_hand, grain fan-out).
- **Metric Views enforce additivity** — no more hand-rolled semi-additive errors.
- **Lineage is transparent** — prod_edw → sandbox medallion → dashboard is traceable.
- **Costs are visible** — no more $0.0134 carbide parts masquerading as 17.6M-unit breaches.
- **History is retained** — dashboards can show "was OK last week, red now" (Pain #7).

By reading prod_edw (not copying), deriving Silver/Gold in sandbox, and governing via UC, we keep the EDW as the single source of truth while removing the friction of hand-rolled corrections in every dashboard.

