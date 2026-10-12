# Query Recipe — hand this to every subagent

## Connection (validated, known-good)
- Profile: `mke-rsc`
- Warehouse: default `7bd33a82f4e92206` (the query tool uses it automatically)
- Run SQL with:
```bash
databricks experimental aitools tools query "<SQL>" --profile mke-rsc
```
- Describe a table with:
```bash
databricks experimental aitools tools discover-schema <catalog>.<schema>.<table> --profile mke-rsc
```

## Naming gotcha (MANDATORY)
Names are literal. Tables that START WITH A DIGIT must be backticked, and inside a double-quoted
Bash string the backtick must be escaped:
- Correct: `prod_edw.fact.\`20_supply_daily\`` and `prod_edw.fact.\`10_demand_daily\``
- Use exact catalog/schema/table as written in the docs. Do not swap `-`/`_`.

## READ-ONLY. Only these verbs:
`SELECT`, `DESCRIBE`, `SHOW`. Never write to prod. Findings go to a local .md file only.

## Profiling conventions — for EACH table, capture:
1. **Existence + schema** — `discover-schema`; list every column with type. If it errors
   (`RESOURCE_DOES_NOT_EXIST` / `TABLE_OR_VIEW_NOT_FOUND`), record as **Missing** and stop on it.
2. **Row count + grain proof** — `COUNT(*)` and `COUNT(*)` vs `COUNT(DISTINCT <candidate key set>)`
   to prove/deny the claimed grain. State the true grain.
3. **Time coverage** — MIN/MAX/COUNT(DISTINCT) of the primary date/snapshot column
   (`process_date`, `date_key`, `transaction_date`, `fulfillment_timestamp`, etc.).
4. **Key cardinality** — distinct counts of the join keys (item key, org key, series key, plan id,
   customer key) so we know fan-out risk.
5. **Categorical domains** — for status/type/plan-name/UOM columns, `GROUP BY ... COUNT(*)` top
   values (e.g. `transaction_type`, `order_type`, `sales_fulfillment_line_status`,
   `item_status_description`, plan `name`, `mkedg0..5`). These drive scenario/filters.
6. **Measure sanity** — MIN/MAX/AVG and NULL rate for the money columns (quantities, on_hand,
   forecast measures, standard cost) — enough to spot negatives, nulls, absurd ranges.
7. **A couple of real sample rows** (LIMIT 5) to see actual shapes/values.
8. **Uniqueness / unique standing** — one paragraph: what does THIS table uniquely provide that no
   other does? Where does it overlap another table, and how do they differ (grain, timing, source
   system)? This is the most important qualitative output.
9. **Gotchas** — semi-additivity (on_hand must NOT be summed over dates), deprecation, multi-source
   blending, SCD1 vs SCD2, nullable keys, filters required to avoid double counting.

Keep queries cheap: always LIMIT samples; use COUNT/GROUP BY/approx where the table is huge
(`20_supply_daily` is 13.4B rows — filter to a single `process_date` before any per-row work, and
prefer `approx_count_distinct` for cardinality on the big fact).

## Output file template (write to data_understanding/subagent_findings/<letter>_<name>.md)
```
# Cluster <letter> — <title>

## Summary (3–5 bullets, plain english)

## Per-table findings
### <fully.qualified.table>  — STATUS: Profiled|Exists-not-profiled|Missing|Deprecated
- Priorities using it: Pn...
- Grain (proven): ...
- Row count: ... ; time coverage: ...
- Key cardinalities: ...
- Categorical domains (with counts): ...
- Measures (min/max/avg/null%): ...
- Sample rows: (compact)
- **Unique standing:** ...
- Gotchas: ...
- Queries run: (list the SQL, labeled READ-ONLY)

## Cross-table notes for this cluster
## Open questions / anything missing
```
