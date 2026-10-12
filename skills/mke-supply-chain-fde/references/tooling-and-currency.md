# Tooling Currency, DQX & Databricks Labs

> The goal is not to "know all tools." It is to know each tool's **current API, maturity, limits,
> prerequisites, integration points, anti-patterns, and when NOT to use it** — and to verify
> against current docs rather than old tutorials.

Before selecting/designing/implementing any Databricks, Spark, MLflow, Lakeflow SDP, DQX, or
Databricks Labs capability, verify current official docs, release notes, cloud-specific
limitations, API maturity, permissions, networking, deployment prerequisites, compatibility, and
known gotchas.

## Recommendation status labels

Attach one to every meaningful technical recommendation:

| Status | Meaning |
|---|---|
| Confirmed current | Checked against current official documentation |
| Supported with constraint | Officially supported, but requirements/limits apply |
| Preview/Beta | Possible, but maturity and release risk are explicit |
| Labs/reference pattern | Useful accelerator, not an assumed platform standard |
| Candidate pattern | Worth prototyping, not yet validated |
| Rejected | Doesn't fit semantics, maturity, risk, or operating model |

## Knowledge sources to verify against

Databricks platform docs · Apache Spark docs (Spark 4.x split the monolithic Structured Streaming
guide into topic pages) · MLflow docs (traditional ML **and** GenAI/`ResponsesAgent`) · Lakeflow
SDP docs (not old DLT / `apply_changes` naming) · DQX docs · Databricks Labs · release notes ·
cloud-specific docs (AWS/Azure/GCP differences in networking, identity, private connectivity,
Lakebase, Apps).

## Gotcha watchlist

Product renames & migration paths · old API examples no longer recommended · cloud availability
differences · preview/Beta restrictions · authentication changes · permission prerequisites ·
resource-attachment requirements · region/network limits · runtime-version compatibility · App
deployment/build restrictions · Lakebase auth & pooling constraints · Model Serving & AI Gateway
permission models · SDK/CLI & Bundle schema changes · Databricks Labs maintenance status ·
breaking changes in Spark and MLflow. (Concrete product gotchas live in `platform-gotchas.md`.)

## SDP / Lakeflow — verify current, judge fit

Verify current Lakeflow docs, not old DLT examples. Judgment factors: maintained dataset vs a mere
task; batch vs streaming; CDC ordering, late events, schema changes, deletes, SCD; MV vs streaming
table vs plain Delta; declarative CDC vs a custom `MERGE`; whether expectations should warn/drop/
fail; whether a sink/publication is appropriate; event-log observability/recovery/cost; dataset &
API limits; whether declarative rerun behavior conflicts with side effects. Lakeflow declarative
CDC handles ordering, dedup, out-of-order events, and schema evolution declaratively. SDPs remain
a **candidate for durable incremental analytical datasets** — not an automatic answer for app
workflows, Lakebase transactions, external actions, manual approvals, or one-time discovery.

## DQX & data quality — compare, don't impose

| Need | Possible fit |
|---|---|
| Simple row-level contract in an SDP | Native Lakeflow expectations |
| Reusable enterprise rules across workloads | DQX or a governed reusable rule framework |
| Fast source profiling | SQL/PySpark profiling notebooks + data-quality monitoring |
| Complex reconciliation | SQL/PySpark tests with retained evidence |
| Quarantine + multi-rule reporting | DQX or a purpose-built Silver-layer pattern |
| App validation | FastAPI/Pydantic + Lakebase constraints + business-rule services |
| Transaction validation | PostgreSQL constraints + typed API schemas + state-machine enforcement |
| Agent/tool validation | Typed tool schemas + deterministic policy checks + MLflow evaluation |

A DQ product adds governance and reuse but also abstraction, learning curve, runtime overhead,
dependency/version risk, and debugging complexity. Choose by the actual breadth and repeatability
of the quality requirements.

## Databricks Labs — evaluate before adopting

A Labs project is not automatically a production dependency. Evaluate: supported / Labs-maintained
/ community / archived? GA / preview / experimental / reference-only? active and compatible with
current Runtime & MLflow? uses UC, current auth, current APIs? who owns upgrades & security fixes?
fits Milwaukee cloud/networking/security/deployment standards? duplicates native capability? usable
as inspiration vs imported as a dependency? license compatible? can it be pinned/tested/upgraded/
rolled back?

> **Adopt a Databricks Labs project only when it materially accelerates delivery without creating
> unacceptable ownership, versioning, security, or operational risk. Otherwise borrow the
> validated pattern and implement the smaller required capability using supported platform
> features.**

## Default directive

Prefer supported, production-ready platform capabilities where they fit the business semantics.
Do not use old tutorials, preview features, outdated APIs, or accelerators by default merely
because they demonstrate a convenient solution. Use modern capabilities where they help while
avoiding blind adoption of anything — native, Labs, open source, or custom.
