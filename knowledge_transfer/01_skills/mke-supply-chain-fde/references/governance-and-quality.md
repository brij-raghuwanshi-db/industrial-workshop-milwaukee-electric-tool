# Governance, Data Quality & QA

"Databricks-native" does not mean "not software-engineered." Governance, quality, and testing are
part of the default deliverable, scaled to task size — not optional add-ons.

## Governance by design (Unity Catalog)

Assume Unity Catalog unless the environment explicitly lacks it. Use three-level names,
group-based ownership & grants, service principals for production automation, managed tables
where appropriate, lineage, auditability, and policy-based controls.

- Catalog/schema layout reflects the governance model (domain, environment, lifecycle, or a
  deliberate hybrid).
- Production objects are **not** owned by individuals — a group is the enduring steward.
- Prefer centralized sensitive-data controls via governed tags + ABAC where possible; use row
  filters and column masks for table-specific requirements.
- Development uses isolated schemas/catalogs so experiments never overwrite shared/production
  data. (Project boundary: reads from `prod_edw`/`prod_operations` only; writes to
  `sandbox_operations.po_management` + Lakebase — see `../SKILL.md`.)
- Delta history/time-travel aids audit and restore, but does not replace environment isolation,
  testing, or deployment control.

## Software-engineering discipline

Source-controlled modules (not logic trapped in notebooks); thin notebooks for exploration/demos/
entry points; parameterized config (no hard-coded workspace IDs, secrets, catalogs, paths, env
names); pure transformation functions where practical; unit/contract/integration/DQ/deployment
tests; pinned dependencies & reproducible builds; structured logging, exception handling,
actionable errors; code review, CI validation, staged deployment, rollback strategy. Use `pytest`
with Databricks Connect / the IDE extension; DABs are the recommended CI/CD mechanism.

## Data-quality expectations

Use pipeline **expectations** with deliberate `warn` / `drop` / `fail` behavior for critical
invariants; quarantine handling and repair/replay strategy; schema-evolution policy and detection
of rescued/corrupt records; freshness, volume, uniqueness, referential, and reconciliation checks.
Store expectation rules separately from pipeline logic so they can be reused across datasets/
pipelines (enterprise QA standardization). Structure Auto Loader flows with source → bronze →
clean → corrupt-record handling.

## Profiling contract (per new dataset)

Schema & datatype conformity · row counts & volume trends · null/blank rates · distinctness &
cardinality · primary-key candidates & duplicate patterns · referential integrity · numeric
ranges & outliers · categorical distributions · date coverage & impossible dates · freshness &
ingestion lag · UoM & currency consistency · cross-field business rules · schema & distribution
drift · source-to-target reconciliation · baseline comparison · sensitive-data discovery.

Profile economically: inspect schema/metadata first, then bounded aggregations and representative
samples — avoid unrestricted `collect()` or full `toPandas()`. Databricks data profiling provides
historical summary/distribution metrics for monitoring and alerting on quality shifts.

## QA layer matrix

| Layer | Example tests |
|---|---|
| Source | Connectivity, schema, extraction watermark, CDC completeness |
| Bronze | File/event counts, rescued data, duplicates, ingestion metadata |
| Silver | Keys, deduplication, SCD, referential integrity, business rules |
| Gold | Grain, measures, dimensions, reconciliation, historical behavior |
| Semantic | Metric definitions, filter behavior, aggregation correctness |
| Dashboard | Visual totals, filters, drill paths, security, freshness, performance |
| Genie | Question benchmark, generated SQL, numeric answer, refusal behavior |
| Application | APIs, forms, transactions, concurrency, authentication, authorization |
| Agent | Retrieval, tool selection, evidence, hallucination, safety, approvals |
| Deployment | Bundle validation, environment config, smoke tests |
| Operations | Rerun, retry, backfill, alert, failure, disaster-recovery behavior |

## Observability & operations

Pipeline event logs capture run progress, expectation pass/fail, data quality, audit, lineage;
system tables give historical views of cost, jobs, queries, security, compliance. Use `EXPLAIN`,
query history, and Query Profile (operators, rows, memory, time, expensive operators, full scans,
exploding joins) for **evidence-driven** tuning — not speculation. Include alerting thresholds,
ownership, SLA/SLO, and troubleshooting/runbook notes. `print()` is not observability.

## Genie Agent quality (semantic + testing project)

Keep it focused — preferably ≤ 5 necessary tables; use metric views / prejoined views to simplify
the model; express business semantics via SQL definitions & example queries before relying on
free-text instructions. Include: tightly scoped domain; well-described UC tables/columns; governed
metric views; trusted SQL examples; business synonyms & disambiguation; approved/prohibited
question categories; a benchmark question/answer set; SQL correctness & numerical reconciliation;
adversarial/ambiguous prompt tests; permission & sensitive-data tests; response-time & warehouse
performance tests; feedback, monitoring, iterative improvement. When exposed via an App, apply
least-privilege access and graceful handling when a request can't be interpreted reliably.

## Dashboard quality (product design, not chart placement)

Define: persona & decision supported; KPI hierarchy; semantic dataset & certified measures;
executive summary + operational detail; filters/drill-through/cross-filtering; targets, variance,
historical context; exception queues & actionable detail; freshness / "as of" indicators;
row-level security & sharing; performance, refresh schedule, subscriptions; visual QA, metric QA,
UAT; source control & deployment. (Presentation conventions & KPI layout: see
`supply-chain-domain.md`.)
