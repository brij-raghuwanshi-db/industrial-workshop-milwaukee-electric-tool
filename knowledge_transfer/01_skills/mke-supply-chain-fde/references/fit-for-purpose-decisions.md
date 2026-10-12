# Fit-for-Purpose Databricks Decision Framework

The governing rule:

> **Do not choose a Databricks product because it is available, modern, or familiar. Do not
> reject it merely because a simpler prototype can initially work. Select based on business
> responsibility, domain semantics, data and state behavior, maturity, operational obligations,
> and measured evidence.**

Think *where it sits fit*, not blind development. This applies to everything: languages,
pipelines, notebooks, Jobs, data models, compute, federation vs ingestion, dashboards, Genie,
Apps, Lakebase, ML, agents, Model Serving, AI Gateway, DABs, CI/CD, auth, networking.

## Business need → likely starting point

| Business need | Likely starting point | Usually unsuitable |
|---|---|---|
| Explore and reconcile | SQL or notebook | Production App |
| Maintain incremental tables | SDP / Lakeflow pipeline | Transactional App logic |
| Sequence heterogeneous operations | Lakeflow Job | One giant pipeline |
| Compare Actual vs Plan | Gold model + dashboard | Lakebase as warehouse |
| Ask governed questions | Focused Genie Agent | Unbounded enterprise Agent |
| Enter or edit events | App + Lakebase | Dashboard |
| Approve and execute actions | App + typed action service | Direct Genie writeback |
| Train periodic forecasts | Job + MLflow | Always-on endpoint by default |
| Serve interactive inference | Model Serving | Batch-only process |
| Standardize metrics | Metric View | Repeating formulas per dashboard |
| Discover remote EDW data | Lakehouse Federation | High-volume permanent serving |
| Deploy repeatably | DABs + CI/CD | Manual production copying |

## Language: SQL vs PySpark vs Python

Contextual, not ideological. Databricks recommends Python and SQL for new projects.

| Situation | Default | Reason |
|---|---|---|
| Joins, aggregations, windows, dimensional logic | SQL | Declarative, optimizer-friendly, BI-accessible |
| Straight bronze→silver→gold | SQL or mixed Lakeflow pipeline | Clear dataset defs, managed deps |
| Dynamically generate many similar datasets | Python Lakeflow API | Loops, config, modular composition |
| Complex nested data / reusable transforms | PySpark DataFrame API | Strong Spark-native programmatic transforms |
| Small driver-side control/config | Python | Metadata & orchestration, not bulk data movement |
| Data science / classical ML | Python + Spark ML + MLflow | Tracking, packaging, registration, eval |
| Deployment / workspace automation | DABs YAML, CLI/SDK/API | Repeatable lifecycle |

Inside Lakeflow dataset definitions: return a DataFrame, stay declarative. Avoid `collect()`,
`count()`, `toPandas()`, `saveAsTable()`, streaming `start()`, and other side effects there —
definitions are evaluated multiple times.

## SDP / Lakeflow pipelines — use when / avoid when

**Use when** the product is a maintained dataset with incremental batch, streaming, CDC (`AUTO
CDC`, SCD 1/2), managed data-quality expectations, or declarative dependency management.

**Avoid / don't force when**: profiling, one-time reconciliation, transactional writebacks,
external API actions, human approvals, or side-effect-heavy processing.

**Limits to respect**: a dataset normally has one defining operation; `pivot()` unsupported;
materialized views don't support time-travel; dataset definitions must not carry arbitrary
writes/side effects.

SDP may own *part* of a use case without owning all of it (e.g. incremental Silver/Gold
maintenance after semantics stabilize, but not rule administration or disposition workflow).

## Jobs — orchestration, not a crutch

Lakeflow Jobs sequence heterogeneous work: notebooks, Python, SQL, dbt, JAR, pipeline tasks,
with dependencies, conditional branches, retries. Use for profiling→validation→pipeline→SQL→ML
→publication→notification chains.

Do **not** use a giant Job DAG to compensate for unclear data products, and do **not** wrap a
non-idempotent live action in retries and call it reliable. Separation of concerns:

- **Pipeline:** what datasets should be maintained?
- **Job:** what work runs, in what order, under which conditions?
- **Lakebase/App:** what transactional state changes under user/agent interaction?
- **Action service:** what governed external operation must be executed and verified?

## Notebooks — first, not only

**Good for:** source discovery, semantic exploration, profiling, one-SKU/one-week vertical
slices, reconciliation, interactive debugging, demos/evidence, thin entry points.

**Problematic when** they accumulate hidden state, duplicated transforms, manual execution
order, inline secrets, mixed exploration+production logic, or untestable calculations.

> **Notebook-first may be appropriate; notebook-only production architecture usually is not.**
Move reusable logic into source-controlled `.py` modules and SQL files as it stabilizes.

## Lakebase vs Delta

- **Lakebase (managed Postgres):** mutable transactional state — event edits, assignments,
  comments, locks, approvals, idempotency records, action status, saved searches.
- **Delta:** large-scale history, plan snapshots, actuals, forecast vintages, exception
  evaluations, features, analytical outcomes.

Do not duplicate the EDW in Lakebase; do not use Delta as a concurrent human-edit approval DB;
do not let an agent issue unrestricted SQL updates; do not confuse an app transaction with an
analytical pipeline update. Note: a Lakebase DB exposed through Unity Catalog is read-only via UC
queries and needs a serverless SQL warehouse — reinforcing the write/read split.

## Federation vs ingestion

**Federation** — discovery and bounded live access without first copying. But federated queries
are read-only, don't get Databricks result/disk caching, can load the remote system, and may hit
performance/memory limits on large results. Pushdown depends on remote engine + query shape —
**inspect the physical plan**, don't assume a filter/join runs remotely.

**Ingestion / CDC** — preferable for repeated high-volume access, historical reconstruction,
stable analytical performance, isolation from the source, resilience to source downtime,
data-quality remediation, long-term versioning.

Avoid placing uncontrolled analytical load on operational systems: federation is great for
discovery, usually wrong for a frequently refreshed high-volume dashboard.

## Metric Views

Use when governed measures (Plan Attainment, Supply Plan Variance, Receipt/Shipment Performance,
Forecast Accuracy) need reuse across dashboards, Genie, Apps, and SQL. Not a universal substitute
for Gold tables (limits around profiling, downstream joins, and how measures must be queried).
Normal layering:

```
Gold fact/view with record-level evidence → governed Metric View → Dashboard / Genie / App
```

A dashboard-local metric view can be promoted to Unity Catalog once its semantics are validated.

## Requirements → Databricks translation method

Translate every business requirement into: business decisions → domain semantics → systems of
record → analytical history → transactional state → serving requirements → AI responsibilities →
integration flows → trust boundaries → tests → operating procedures — **before** choosing
implementation tools. Produce a per-requirement traceability row: `Requirement | Decision | Domain
object | Analytical asset | Transactional asset | Platform product | Test`.

## Deterministic vs AI (decide what NOT to delegate to an LLM)

An LLM should **explain and coordinate reliable tools — not replace mathematics, constraints,
permissions, or transactions.**

| Requirement | Preferred implementation |
|---|---|
| Variance calculation | SQL or Spark |
| Safety-stock breach / frozen-zone / PO date feasibility | Deterministic rule / constraint engine |
| Customer disaggregation | Approved mathematical rule |
| Exception priority | Deterministic score, possibly ML-assisted |
| Demand forecast / late-supplier probability | Statistical / ML model |
| Similar-case search | Hybrid retrieval |
| Root-cause hypothesis / recommendation explanation | Agent, grounded in evidence |
| Recommendation generation | Rules/optimization/ML + agent explanation |
| PO writeback | Typed transactional service with approval |
| Conversational analytics | Genie |
| Final business approval | Authorized human or explicit policy |

The LLM must not invent variance thresholds, MOQ rules, lead-time policies, plan versions, supplier
constraints, approval requirements, or PO changes — these come from governed data, versioned
business rules, validated models, and authorized tools.

## Search: BM25 vs Vector vs Hybrid

Choose by retrieval semantics; a relevant result is not an authorized result — enforce app
authorization on results either way.

- **BM25 / keyword** (Lakebase Search `lakebase_text`, PostgreSQL `tsvector`) — exact words,
  identifiers, domain terms: find SKU `2804-20`, a PO number, comments with a supplier/planner
  name, "frozen zone" policy, actions involving "pull-in", known error messages.
- **Vector / semantic** — meaning in different words: similar shortages, policies related to
  supplier delivery problems, comparable transition-risk notes, procedures for a late inbound,
  similar product-launch demand events.
- **Hybrid** — most supply-chain retrieval: BM25 preserves exact names/codes/action terms, vector
  finds semantically similar notes/cases, structured SQL filters enforce supplier/family/date/
  severity/status. Use Vector Search for narrative knowledge; use governed SQL/metric tools for
  quantitative truth.

## Lakebase sync & reverse-ETL boundaries

"Lakebase sync" is two directions; don't confuse either with operational writeback:

| Movement | Meaning | Mechanism |
|---|---|---|
| UC → Lakebase | Serve analytical data to the App (low-latency reads) | UC **synced tables** (snapshot / triggered / continuous) — read-only in Postgres |
| Lakebase → UC | Analyze transactional changes & outcomes | Lakebase **Change Data Feed** → Delta |
| Lakebase/App → Oracle API | Execute an approved business transaction | Typed action service + approval |
| Oracle → Databricks | Confirm the system-of-record result | Read-back / integration outcome |

A Lakebase **synced table is read-only in Postgres** — planner edits go into separate native
Lakebase tables, never into the synced copy. Shape synced tables for app access (current item/
supplier/org, open exceptions, current inventory/outlook, latest forecast, app-grain metrics) —
don't sync every raw fact or whole EDW table. Good CDF→Delta candidates: planner overrides, event
revisions, dispositions, recommendation accept/reject, approvals, action results, feedback,
root-cause assignments, audit events, forecast-publish history. This closes the loop:
`analytics → recommendation → planner decision → live action → outcome → CDF → Delta → evaluation
→ improved rule/model`. Note the **Lakebase Data API** (PostgREST-style CRUD) can cut boilerplate
for ordinary operations — but do NOT expose high-risk Oracle actions as unrestricted generic CRUD;
those need a domain service enforcing permissions, state, constraints, idempotency, approvals, and
external-response verification.

## Architecture Decision Record (for important choices)

1. Business decision being supported
2. Domain semantics and grain
3. Functional and nonfunctional requirements
4. Options considered
5. Recommended option
6. Why it fits
7. Drawbacks and accepted risks
8. Rejected / deferred alternatives
9. Security, networking, cost, operational effects
10. Testing and validation required
11. Conditions that would trigger reconsideration

Evidence status: **Validated** / **Preferred with assumptions** / **Prototype choice** /
**Blocked pending evidence** / **Rejected**.

## Expanded evaluation lenses

Examine every significant decision across: business outcome & decision; domain grain & time
orientation; plan version / forecast vintage; stock vs flow vs snapshot vs event vs transaction;
append/correction/CDC/late-arriving/delete semantics; latency & freshness; user concurrency &
state; failure/retry/idempotency/compensation; reconciliation & DQ contracts; UC authorization;
user vs service-principal identity; network route/DNS/firewall/source load; performance & cost;
development speed; testing & deployment maturity; operability & ownership; portability &
product lock-in; product limitations & roadmap risk.
