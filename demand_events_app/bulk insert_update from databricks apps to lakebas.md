<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# bulk insert/update from databricks apps to lakebase/delta or oracle .. ?

Yes—but the best pattern depends on the **system of record** and whether “bulk” means thousands of rows from an interactive Databricks App or scheduled/high-volume ingestion.

For a Databricks App, avoid issuing one database call per row. Have the app submit a batch to a backend endpoint/job, land it in a staging table, and perform a **set-based upsert** (`MERGE` for Delta; staging + `MERGE` for Lakebase/Oracle). Delta Lake supports transactional inserts, updates, deletes, and `MERGE`-based upserts.[^1_1][^1_2]

## Recommended architecture

```text
Databricks App
  → API / job / SQL warehouse (validation + authorization)
  → staging dataset/table
  → set-based MERGE into target
  → audit / error table / status returned to app
```

This provides:

- Fewer network round trips and better throughput.
- Atomic, repeatable writes with an idempotency key or batch ID.
- Data validation before modifying production data.
- Clear rollback/retry behavior.
- A safer separation between a user-facing app and direct production-table access.

For user-editable data, make each app submission an immutable request/batch, rather than letting the UI directly execute arbitrary update statements.

## Target-specific guidance

| Target | Best bulk-write pattern | Bulk update/upsert pattern | When to use it |
| :-- | :-- | :-- | :-- |
| **Delta Lake** | Write a DataFrame or staged Delta table | `MERGE INTO target USING staging` | Best when the lakehouse is the system of record and workloads are analytical or batch-oriented |
| **Lakebase (Postgres)** | Load/insert into a staging table, ideally with a native bulk-load mechanism such as PostgreSQL `COPY` where available | `INSERT ... ON CONFLICT ... DO UPDATE` or `MERGE` from staging | Best for low-latency app-serving / transactional tables |
| **Oracle** | Spark JDBC append with partitioned parallelism and tuned `batchsize`, or Oracle-native load tooling for very large volumes | Stage first, then Oracle `MERGE` | Best when Oracle remains the operational source of truth |

Lakebase is a managed PostgreSQL database integrated into Databricks, while Delta is the platform’s table/storage layer for analytical data. In particular, Databricks’ synced tables can load Unity Catalog Delta or Iceberg source data directly into the storage backing a Lakebase branch, avoiding routing the full bulk load through the live compute endpoint.[^1_3][^1_4]

## Delta Lake: preferred for lakehouse writes

### Bulk insert

For app-originated rows, convert the payload to a DataFrame and append it, or—preferably—write it to a per-batch staging table.

```python
incoming_df.write.format("delta") \
    .mode("append") \
    .saveAsTable("main.app_stage.customer_changes")
```


### Bulk insert/update

```sql
MERGE INTO main.gold.customers AS target
USING main.app_stage.customer_changes AS source
ON target.customer_id = source.customer_id

WHEN MATCHED AND source.operation = 'DELETE' THEN
  DELETE

WHEN MATCHED THEN
  UPDATE SET
    target.email = source.email,
    target.status = source.status,
    target.updated_at = current_timestamp()

WHEN NOT MATCHED THEN
  INSERT (
    customer_id,
    email,
    status,
    created_at,
    updated_at
  )
  VALUES (
    source.customer_id,
    source.email,
    source.status,
    current_timestamp(),
    current_timestamp()
  );
```


### Practical notes

- Include `batch_id`, `request_id`, source timestamp, and user identity in the staging data.
- Deduplicate source records before the `MERGE`; Delta `MERGE` expects that a target record does not ambiguously match multiple source rows.
- Use an explicit business key, such as `customer_id`, rather than relying on timestamps alone.
- For frequent small app edits, do not run a separate large `MERGE` for every click. Buffer requests for a short interval, or use a queue/job model.
- If downstream consumers need row-level changes, enable Delta Change Data Feed. Databricks documents CDF specifically for tracking table changes.[^1_5]


## Lakebase: preferred for transactional app data

If your app needs fast point reads/writes—orders, workflow states, user preferences, approval actions—Lakebase is normally the cleaner operational target. Then replicate/sync its changes to Delta for analytics.

### Pattern

1. App posts an array of records to a controlled backend.
2. Backend validates schema, permissions, and record limits.
3. Write to `stg_customer_changes`.
4. Execute one set-based PostgreSQL upsert.
5. Record batch status and row-level rejects.

Example PostgreSQL-style upsert:

```sql
INSERT INTO app.customers (
  customer_id,
  email,
  status,
  updated_at
)
SELECT
  customer_id,
  email,
  status,
  now()
FROM app.stg_customer_changes
WHERE batch_id = :batch_id

ON CONFLICT (customer_id) DO UPDATE
SET
  email = EXCLUDED.email,
  status = EXCLUDED.status,
  updated_at = now();
```

For high-volume initial loads, PostgreSQL’s `COPY`-style ingestion is generally more appropriate than application-side row-by-row `INSERT`s. After unusually large loads, maintenance such as `VACUUM` can be relevant for Lakebase/Postgres workloads.[^1_6]

If your directional flow is Lakebase → Delta, Lakebase Change Data Feed captures Postgres inserts, updates, and deletes from the write-ahead log into a Unity Catalog-managed Delta table, with documented batching/flushing of roughly 15 seconds.[^1_7]

## Oracle: stage first, then MERGE

For Oracle, a Databricks App should not normally hold a powerful Oracle username in client-side code. Put credentials in Databricks secrets / governed connections and use a service layer or scheduled job.

### Spark JDBC insert

```python
(
  incoming_df
    .repartition(8)
    .write
    .format("jdbc")
    .option("url", oracle_jdbc_url)
    .option("dbtable", "APP.STG_CUSTOMER_CHANGES")
    .option("user", oracle_user)
    .option("password", oracle_password)
    .option("driver", "oracle.jdbc.OracleDriver")
    .option("batchsize", "10000")
    .mode("append")
    .save()
)
```

Then run one Oracle-side merge:

```sql
MERGE INTO app.customers t
USING (
  SELECT customer_id, email, status
  FROM app.stg_customer_changes
  WHERE batch_id = :batch_id
) s
ON (t.customer_id = s.customer_id)

WHEN MATCHED THEN
  UPDATE SET
    t.email = s.email,
    t.status = s.status,
    t.updated_at = SYSTIMESTAMP

WHEN NOT MATCHED THEN
  INSERT (
    customer_id,
    email,
    status,
    created_at,
    updated_at
  )
  VALUES (
    s.customer_id,
    s.email,
    s.status,
    SYSTIMESTAMP,
    SYSTIMESTAMP);
```

Oracle JDBC batching reduces database round trips: statements are added with `addBatch` and sent together with batch execution. Databricks supports JDBC connections configured through Unity Catalog connections, which is preferable to embedding connection details in app code.[^1_8][^1_9][^1_10]

For multi-million-row Oracle loads, consider Oracle-native bulk mechanisms—such as external tables, SQL\*Loader, or direct-path loading—rather than generic JDBC alone, especially where network throughput and redo/undo behavior matter.

## Choosing the direction

Use this decision rule:

- **App is transactional and requires low-latency reads/updates:** write to **Lakebase**, then use Lakebase CDF or sync to Delta.
- **App submits files, corrections, operational events, or curated datasets for analytics:** write to **Delta staging**, then `MERGE` to Delta targets.
- **Oracle is the enterprise system of record:** load to an **Oracle staging table**, then run an Oracle-side `MERGE`; optionally read/replicate Oracle data into Delta for reporting.
- **Delta is canonical but Lakebase powers an app:** use **Delta → Lakebase synced tables** for serving/reference data, and decide carefully whether user-created transactional records belong in Lakebase or should be written back to Delta in controlled batches. Synced tables are designed to serve Unity Catalog Delta/Iceberg data through Lakebase.[^1_4]


## Guardrails worth adding

- Require a `request_id`/`batch_id` and enforce a unique constraint or processed-batch ledger for retries.
- Validate payload size, schema, nullability, key uniqueness, and user authorization before the staging write.
- Separate `INSERT`, `UPDATE`, and `DELETE` intent explicitly, rather than inferring it.
- Maintain `created_at`, `updated_at`, `created_by`, `updated_by`, and source/application identifiers.
- Keep rejected rows and validation errors in a quarantine/error table.
- Set an upper limit per app request; use a Databricks Workflow/job for large files or bulk uploads.
- Do not expose direct write credentials or unrestricted SQL execution in the browser-facing app.

The default I would choose is: **Databricks App → append-only Delta staging → validation/deduplication → Delta `MERGE`** for analytical data, and **Databricks App → Lakebase staging → Postgres upsert → Lakebase CDF to Delta** for true application/OLTP data.

<span style="display:none">[^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://docs.delta.io/delta-update/

[^1_2]: https://docs.databricks.com/aws/en/delta/

[^1_3]: https://docs.databricks.com/aws/en/oltp/projects/

[^1_4]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^1_5]: https://docs.databricks.com/aws/en/tables/features/change-data-feed

[^1_6]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^1_7]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^1_8]: https://docs.oracle.com/en/database/oracle/oracle-database/26/jjdbc/performance-extensions.html

[^1_9]: https://docs.databricks.com/aws/en/connect/jdbc-connection

[^1_10]: https://learn.microsoft.com/en-us/azure/databricks/connect/jdbc-connection

[^1_11]: https://blogs.oracle.com/autonomous-ai-database/query-databricks-delta-tables-using-uniform

[^1_12]: https://www.databricks.com/blog/lakebase-holiday-update

[^1_13]: https://www.flexera.com/blog/finops/databricks-delta-lake/

[^1_14]: https://community.databricks.com/t5/data-engineering/databricks-jdbc-odbc-write-batch-size/td-p/10059

[^1_15]: https://community.databricks.com/t5/get-started-discussions/issue-with-non-bulk-inserts-using-jdbc-on-databricks-runtime-14/td-p/98782


---

# how do we do bulk update?

Use a **staging table + one set-based `MERGE`**. Do not loop through app rows and run individual `UPDATE` statements.

The sequence is:

1. The Databricks App sends an array/file of changed rows.
2. A backend/job bulk-loads those rows to a staging table with a `batch_id`.
3. Validate and deduplicate the staging set.
4. Run one `MERGE` that updates all matched business keys.
5. Record the result, then retain or clean up the staging rows.

Delta Lake `MERGE` is designed to apply a source set of updates, inserts, and deletes to a target Delta table.[^2_1][^2_2]

## Delta bulk update

Assume the app submits records like:


| customer_id | status | email | request_id |
| --: | :-- | :-- | :-- |
| 1001 | ACTIVE | brij@example.com | `req-abc-001` |
| 1002 | SUSPENDED | user2@example.com | `req-abc-001` |

First, bulk append these rows to staging:

```python
(
    updates_df
    .withColumn("batch_id", F.lit(batch_id))
    .write
    .format("delta")
    .mode("append")
    .saveAsTable("main.app_staging.customer_updates")
)
```

Then deduplicate and bulk-update the target in a single operation:

```sql
MERGE INTO main.gold.customers AS t
USING (
  SELECT
    customer_id,
    email,
    status,
    request_id
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY submitted_at DESC
      ) AS rn
    FROM main.app_staging.customer_updates
    WHERE batch_id = :batch_id
  )
  WHERE rn = 1
) AS s
ON t.customer_id = s.customer_id

WHEN MATCHED THEN UPDATE SET
  t.email = s.email,
  t.status = s.status,
  t.updated_at = current_timestamp(),
  t.updated_by_request_id = s.request_id;
```

That performs a **bulk update only**: records absent from `main.gold.customers` are ignored because there is no `WHEN NOT MATCHED THEN INSERT` clause.

### Bulk upsert instead

Add this clause if new customer IDs should be inserted:

```sql
WHEN NOT MATCHED THEN INSERT (
  customer_id,
  email,
  status,
  created_at,
  updated_at,
  updated_by_request_id
)
VALUES (
  s.customer_id,
  s.email,
  s.status,
  current_timestamp(),
  current_timestamp(),
  s.request_id
);
```

A `MERGE` should have one unambiguous source row per target key; deduplicating `customer_id` before the merge prevents multiple source records from attempting to update the same target row.[^2_2][^2_3]

## Lakebase bulk update

Lakebase is PostgreSQL-oriented, so the same staging pattern applies:

```sql
CREATE TABLE IF NOT EXISTS app.stg_customer_updates (
  batch_id       text NOT NULL,
  customer_id    bigint NOT NULL,
  email          text,
  status         text,
  submitted_at   timestamptz NOT NULL DEFAULT now()
);
```

Bulk-load the app payload into this table, then update all matching target rows:

```sql
UPDATE app.customers AS t
SET
  email = s.email,
  status = s.status,
  updated_at = now()
FROM app.stg_customer_updates AS s
WHERE t.customer_id = s.customer_id
  AND s.batch_id = :batch_id;
```

If the batch can contain both updates and new records, use a PostgreSQL upsert:

```sql
INSERT INTO app.customers (
  customer_id,
  email,
  status,
  updated_at
)
SELECT
  customer_id,
  email,
  status,
  now()
FROM app.stg_customer_updates
WHERE batch_id = :batch_id

ON CONFLICT (customer_id) DO UPDATE
SET
  email = EXCLUDED.email,
  status = EXCLUDED.status,
  updated_at = now();
```

For larger Lakebase/PostgreSQL batches, bulk-loading into a staging table without target-table indexes or constraints, followed by one server-side merge/upsert, avoids the bottleneck of per-row remote writes.[^2_4]

## Oracle bulk update

For Oracle, write the app’s payload to an Oracle staging table—via JDBC batches for moderate volumes or an Oracle-native loader for large volumes—then use Oracle `MERGE`.

```sql
MERGE INTO app.customers t
USING (
  SELECT
    customer_id,
    email,
    status
  FROM app.stg_customer_updates
  WHERE batch_id = :batch_id
) s
ON (t.customer_id = s.customer_id)

WHEN MATCHED THEN
  UPDATE SET
    t.email = s.email,
    t.status = s.status,
    t.updated_at = SYSTIMESTAMP;
```

This is update-only because it contains `WHEN MATCHED` but no insert clause. Oracle documents `MERGE` as selecting source rows to update or insert into a target table/view.[^2_5]

For an Oracle upsert, append:

```sql
WHEN NOT MATCHED THEN
  INSERT (
    customer_id,
    email,
    status,
    created_at,
    updated_at
  )
  VALUES (
    s.customer_id,
    s.email,
    s.status,
    SYSTIMESTAMP,
    SYSTIMESTAMP
  );
```


## App implementation pattern

Your Databricks App should call a controlled server-side function/job, not embed unrestricted SQL in the browser.

```python
def submit_customer_updates(records, user_id):
    batch_id = str(uuid.uuid4())

    # 1. Enforce max rows, schema, authorization, and valid keys.
    validated_df = validate_customer_updates(records, user_id)

    # 2. Bulk write once to staging.
    write_to_staging(validated_df, batch_id, user_id)

    # 3. Run exactly one parameterized MERGE/UPDATE.
    execute_bulk_merge(batch_id)

    # 4. Return status, matched count, rejected count, and batch ID.
    return {"batch_id": batch_id, "status": "completed"}
```

For bulk file upload, have the app land the file in a governed volume/storage location and trigger a Databricks Workflow. The workflow can parse, validate, deduplicate, stage, and merge far more reliably than trying to hold a long-running database operation inside the UI request.

## Important safeguards

- Use a stable key such as `customer_id`, `order_id`, or a composite business key in the join condition.
- Add a `batch_id` and `request_id` to make retries idempotent.
- Deduplicate by key before `MERGE`; select the newest version using a timestamp or source sequence number.
- Update only fields the caller is authorized to modify—do not blindly update every column from the app payload.
- Record the user/service identity and timestamps in the target audit columns.
- Run the update as a single transaction where supported, and return affected-row counts plus per-row validation failures.
- Partition or cluster large Delta targets by a useful access pattern, and avoid issuing many tiny `MERGE`s against a very large table.

For your scenario, the usual default is:

```text
Databricks App
→ Delta staging table
→ one MERGE INTO Delta target
→ optional downstream sync/export to Lakebase or Oracle
```

If Lakebase or Oracle is the true application/system-of-record database, reverse the final step: bulk-stage there and execute the database-native `UPDATE ... FROM` / `MERGE` there.

<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://docs.databricks.com/aws/en/sql/language-manual/delta-merge-into

[^2_2]: https://docs.databricks.com/aws/en/delta/merge

[^2_3]: https://learn.microsoft.com/en-us/azure/databricks/delta/merge

[^2_4]: https://community.databricks.com/t5/data-engineering/how-to-use-multi-threading-and-batch-inserts-for-large-upsert-to/td-p/148655

[^2_5]: https://docs.oracle.com/en/database/oracle/oracle-database/18/sqlrf/MERGE.html

[^2_6]: https://help.salesforce.com/s/articleView?id=001115425\&language=en_US\&type=1

[^2_7]: https://stackoverflow.com/questions/19151288/update-vs-merge-in-oracle-for-a-list-of-record-not-for-bulk-record-set-performa

[^2_8]: https://stackoverflow.com/questions/79634024/how-to-insert-update-delete-data-using-databricks-for-large-records-in-postgresq

[^2_9]: https://builder.ai2sql.io/blog/oracle-merge-into-tutorial

[^2_10]: https://www.orafaq.com/node/2450

[^2_11]: https://www.reddit.com/r/PostgreSQL/comments/1uyhygg/lakebase_branching/

[^2_12]: https://community.databricks.com/t5/community-articles/wait-did-databricks-just-put-git-inside-my-database/td-p/146805

[^2_13]: https://paths.grasp.study/modules/a1c84921-06ab-4258-9a5c-962767ec5a64/lessons/ef768fea-716d-4fb4-a2f7-c4552ab24c15

[^2_14]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^2_15]: https://docs.delta.io/delta-update/

