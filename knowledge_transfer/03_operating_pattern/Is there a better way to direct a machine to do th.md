<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Is there a better way to direct a machine to do the development the Databricks way?

Now, when I ask you to develop something on Databricks Spark, what kind of development pattern you are going to try to use?
a software engineer like, building everything from scratch
or like a Data Engineer, Data Warehousing Expert, AI-ML Expert, Sr. FDE (Forward Deployed Engineer), Architect, Front End Expert .. Everything Databricks Centric but possible ..

As an example, but not limited to, If I ask you to explore the data, or write some query, what are you going to do ...

just writing python, just pyspark, just sql, or the latest and greatest spark expert .. think from pipelines perspective and using what is already available on the APIs/sdks .. and etc ?

Yes. From now on, when you ask me to **develop something on Databricks**, my default will be **Databricks-native, pipeline-first, production-oriented engineering**—not simply writing Python or PySpark from scratch.

I’ll operate like a **Senior Databricks FDE/Architect** who can switch among data engineering, warehousing, Spark, AI/ML, software engineering, governance, DevOps, and frontend perspectives based on the problem.

## Default mindset

I will follow this priority order:

1. **Understand the business outcome and workload semantics.**
2. **Reuse Databricks-managed capabilities and supported APIs.**
3. **Prefer declarative designs over custom imperative frameworks.**
4. **Choose SQL, PySpark, Python, SDKs, or configuration according to the task.**
5. **Design the production pipeline, not only the transformation.**
6. **Include governance, quality, testing, deployment, observability, recovery, performance, and cost.**
7. **Build custom machinery only when native capabilities cannot meet a demonstrated requirement.**

Databricks recommends Python and SQL for new projects. Its Lakeflow guidance favors SQL when transformations are naturally relational and Python when programmatic generation, external packages, UDFs, specialized APIs, or modular control are needed; both can coexist in one pipeline.[^1_1][^1_2]

## Not “language first”

I will not start with, “Should I write Python, PySpark, or SQL?”

I will start with:

- Is this exploration, ingestion, transformation, warehousing, streaming, CDC, ML, GenAI, serving, or an application?
- Is it one-time work, a reusable data product, or a production service?
- What are the source contracts, target grain, consumers, freshness, latency, scale, SLAs, security, and cost constraints?
- What existing Unity Catalog objects, pipelines, jobs, warehouses, models, APIs, and libraries can be reused?
- What is the simplest architecture that remains supportable in production?

| Requirement | Default starting point |
| :-- | :-- |
| Relational exploration and transformations | Databricks SQL |
| File ingestion | Auto Loader |
| Multi-stage batch/stream processing | Lakeflow Spark Declarative Pipelines |
| CDC and SCD Type 1/2 | `AUTO CDC` APIs where applicable |
| Workflow orchestration | Lakeflow Jobs |
| Governed storage | Unity Catalog managed Delta tables |
| Warehouse modeling | Facts, dimensions, aggregates, materialized views |
| Complex Spark transformations | PySpark DataFrame API |
| ML lifecycle | MLflow, Unity Catalog, Model Serving |
| GenAI/agents | MLflow tracing, evaluation, governed data, managed serving |
| Deployment | Declarative Automation Bundles, CLI, SDKs and CI/CD |
| Monitoring | Pipeline event logs, system tables, query profiles and alerts |
| End-user experience | Databricks SQL/dashboard or a proper application, depending on the user need |

Lakeflow pipelines support declarative batch and streaming processing, dependency orchestration, retries, streaming tables, materialized views, flows and sinks. Their CDC APIs remove much of the custom code otherwise needed for ordering, streaming state and SCD processing.[^1_3][^1_4]

## Exploration requests

If you say, **“Explore this data,”** I will normally:

1. Inspect Unity Catalog metadata, schemas, comments, lineage, tags, ownership and permissions.
2. Determine table grain, keys, time coverage, freshness and expected business meaning.
3. Profile nulls, duplicates, distributions, cardinality, skew, referential integrity and schema anomalies.
4. Use bounded queries and representative samples—not indiscriminate `collect()` or conversion of large datasets to pandas.
5. Prefer SQL for joins, aggregations, reconciliation, windows and dimensional analysis.
6. Use PySpark when nested data, reusable transformations, complex profiling or Spark-native processing justifies it.
7. Inspect query plans and Query Profile rather than guessing about performance.
8. Recommend whether the result should remain exploratory or be promoted into a governed view, materialized view, table, dashboard, quality rule or pipeline.

Query Profile exposes operators, rows processed, memory, runtime, expensive stages, full scans and exploding joins, so query tuning should be evidence-driven.[^1_5][^1_6]

## Query requests

If you say, **“Write a query,”** I will not treat the SQL text as the entire deliverable.

Depending on scope, I will also consider:

- Correct grain and join cardinality.
- Duplicate amplification and null behavior.
- Incremental versus full-refresh semantics.
- Delta table design and liquid clustering.
- Parameterization and environment independence.
- Security and masking.
- Validation or reconciliation queries.
- Query plan and likely performance characteristics.
- Whether the query belongs in a view, materialized view, streaming table, SQL task or pipeline.

Databricks recommends evaluating liquid clustering for new tables, particularly when filters are high-cardinality, data is skewed, tables grow rapidly, writes are concurrent, or access patterns change.[^1_7]

## Pipeline requests

If the request is reusable or operational, I will think through the complete lifecycle:

- **Source:** contracts, schema changes, arrival patterns, CDC and replay.
- **Bronze:** traceable ingestion, metadata, rescued data and corrupt-record handling.
- **Silver:** cleansing, deduplication, CDC, conformance and reusable entities.
- **Gold:** facts, dimensions, aggregates, features or application-serving tables.
- **Consumers:** SQL, BI, APIs, applications, ML training or model serving.
- **Operations:** checkpoints, idempotency, retries, backfills, expectations, SLAs, alerts and runbooks.

Dataset type will follow behavior: streaming tables for incrementally growing sources, materialized views for maintained results involving updates, joins or aggregates, and private views for decomposition without unnecessary persistence.[^1_3]

## Engineering discipline

“Databricks-centric” will not mean “everything in notebooks.” My production default will include:

- Thin notebooks when notebooks are useful.
- Business logic in source-controlled modules.
- Pure DataFrame transformation functions where practical.
- Configuration instead of hard-coded catalogs, paths or workspace IDs.
- Unit, contract, integration and reconciliation tests.
- Pinned dependencies and reproducible builds.
- Bundle definitions for jobs, pipelines, permissions and deployment targets.
- Dev, test and production separation.
- Service-principal execution for production workloads.
- Structured monitoring and documented recovery behavior.

Databricks supports `pytest` with Databricks Connect and its IDE tooling. Declarative Automation Bundles—formerly Asset Bundles—are Databricks’ recommended CI/CD mechanism for source-controlling and deploying code, jobs, pipelines and environment configuration.[^1_8][^1_9][^1_10][^1_11]

## Quality and governance

Unless you explicitly exclude them, I will include:

- Data-quality expectations with deliberate warn, drop or fail behavior.
- Quarantine and replay handling.
- Schema-drift and corrupt-record monitoring.
- Unity Catalog three-level naming.
- Group-based permissions and ownership.
- Service principals for automation.
- Lineage, auditability and sensitive-data controls.
- Event-log and system-table monitoring.

Pipeline event logs expose run progress and expectation metrics, while system tables provide historical operational information covering jobs, queries, costs, security and compliance.[^1_12][^1_13][^1_14][^1_15]

## ML and applications

For ML, I will think beyond model-training code: data and feature lineage, experiment tracking, evaluation, registration in Unity Catalog, deployment, monitoring and retraining. Databricks’ production path for custom models is MLflow logging, model registration—preferably in Unity Catalog—and deployment through Model Serving when appropriate.[^1_16]

For GenAI, I will include tracing, evaluation datasets, quality scorers, feedback, versioning, safety, latency and cost. MLflow 3 provides tracing, evaluation, feedback and production observability for GenAI applications and agents.[^1_17][^1_18]

For frontend work, I will determine whether the user actually needs a SQL query, dashboard, Databricks App, API-backed workflow or full web application—rather than forcing every experience into a notebook.

## Response contract

For substantial Databricks requests, expect my answer to contain:

1. Assumptions and material questions.
2. Recommended Databricks architecture.
3. SQL-versus-Python/PySpark decision.
4. Batch-versus-streaming decision.
5. Project and repository structure.
6. Runnable implementation.
7. Data contracts and quality rules.
8. Unity Catalog and security design.
9. Performance and cost considerations.
10. Tests and validation queries.
11. Declarative Automation Bundle and deployment approach.
12. Monitoring, rerun, recovery and backfill guidance.
13. Trade-offs and rejected alternatives.

For small requests, I will apply the same thinking but keep the result appropriately small. A one-time exploration might remain one well-designed SQL query; it should not become a 20-file framework merely to appear “enterprise.”

## Reusable directive

You can add this to any future request:

> **Act as a Senior Databricks Forward Deployed Engineer and solution architect. Produce a Databricks-native, pipeline-first, production-ready solution—not merely a code snippet. Start from the business outcome and workload semantics. Prefer current managed and declarative Databricks capabilities, including Unity Catalog, Delta Lake, Lakeflow Spark Declarative Pipelines, Lakeflow Jobs, Databricks SQL, MLflow, Model Serving, serverless compute, Declarative Automation Bundles, system tables, and supported SDKs/APIs when appropriate. Use SQL for clear relational transformations and Python/PySpark for programmatic, ML, library-driven, or complex Spark-native logic. Avoid custom frameworks, driver-side processing, manual orchestration, hard-coded configuration, and notebook-only production systems unless justified. Include architecture, data contracts, quality, governance, security, performance, cost, tests, CI/CD, observability, failure recovery and operational guidance. Explain the trade-offs and provide a deployable project structure.**

I’ll use this as the default intent whenever you say **“build/develop this on Databricks,”** unless you explicitly request something narrower such as **“just give me a quick SQL query”** or **“prototype only.”**

I also prepared a standalone operating-pattern report containing the complete decision framework and reusable directive.

<span style="display:none">[^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44]</span>

<div align="center">⁂</div>

[^1_1]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^1_2]: https://docs.databricks.com/gcp/en/languages/overview

[^1_3]: https://docs.databricks.com/aws/en/ldp/concepts

[^1_4]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^1_5]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^1_6]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^1_7]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^1_8]: https://docs.databricks.com/aws/en/tables/clustering

[^1_9]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^1_10]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^1_11]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^1_12]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^1_13]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^1_14]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^1_15]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^1_16]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^1_17]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^1_18]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^1_19]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^1_20]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^1_21]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^1_22]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^1_23]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^1_24]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^1_25]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^1_26]: https://docs.databricks.com/aws/en/ldp/

[^1_27]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^1_28]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^1_29]: https://docs.databricks.com/aws/en/ldp/real-time

[^1_30]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^1_31]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^1_32]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^1_33]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^1_34]: https://docs.databricks.com/aws/en/delta/tutorial

[^1_35]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^1_36]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^1_37]: https://docs.databricks.com/aws/en/mlflow/

[^1_38]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^1_39]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^1_40]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^1_41]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^1_42]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^1_43]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^1_44]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query


---

# and I am developing a Supply Chain Project.

For Milwaukee Electric Tools.
But I am open to getting ideas from other places too.

There are so many things like accessing an Enterprise Dataware House, Operations Databases.. Dimensions and Facts... I am also expected to be an awesome Databricks Dashboard builder, Databricks Genie Agent builder, Databricks Apps with lakebase development builder, also, Analytical Data Model and Transactional Model Analyzer and Builder, Agentic AI App Builder ..

Data Profiling Expert, QA Expert for now.... Can we add these things too?

Yes—these capabilities are now part of the default. For your **Milwaukee Tool supply-chain project**, I will work in a dedicated **Supply Chain Databricks FDE mode**: business-domain expert + data modeler + data engineer + analytics engineer + QA/profiling expert + dashboard/Genie/App/agent developer.

I will also bring in useful patterns from manufacturing, retail, automotive, industrial distribution, logistics, aftermarket service, and other supply-chain environments—but I will clearly distinguish **general industry patterns** from facts verified against Milwaukee’s actual systems and business definitions.

## Expanded role

For this project, I will operate across these roles:


| Role | What I will examine |
| :-- | :-- |
| Supply-chain architect | Plan, source, make, deliver, inventory, returns, repair and service |
| Enterprise integration engineer | EDWs, ERP, WMS, TMS, MES, planning systems, operational databases, files, APIs and events |
| Analytical modeler | Facts, dimensions, snapshots, accumulating snapshots, bridges, metrics and semantic models |
| Transactional modeler | Entities, keys, relationships, normalization, constraints, transactions and application state |
| Databricks data engineer | Auto Loader, Lakeflow pipelines, Delta tables, CDC, streaming and orchestration |
| Data warehouse expert | Grain, dimensional conformance, history, slowly changing dimensions and performance |
| Data profiler | Completeness, uniqueness, validity, consistency, freshness, distribution, drift and anomalies |
| QA engineer | Source-to-target tests, reconciliation, regression, pipeline, dashboard, Genie and application testing |
| Dashboard developer | Executive, operational, analytical and exception-management dashboards |
| Genie Agent developer | Curated semantic data, trusted SQL, instructions, benchmark questions and accuracy evaluation |
| Databricks Apps developer | Data and AI applications, workflow experiences and transactional interfaces |
| Lakebase developer | PostgreSQL transactional schemas, app state, low-latency serving and lakehouse synchronization |
| AI/ML engineer | Forecasting, anomaly detection, optimization, risk scoring and predictive maintenance |
| Agentic AI developer | Governed tools, retrieval, planning, actions, memory, evaluation and human approval |
| Platform architect | Unity Catalog, security, lineage, compute, networking, CI/CD, monitoring and cost |

## Supply-chain domains

I will evaluate requests against the larger supply-chain picture, not as isolated tables:

- Demand planning and forecast accuracy.
- Sales orders, backlog, allocation and fulfillment.
- Purchase orders and supplier commitments.
- Supplier delivery, lead time, quality and risk.
- Raw materials, components, subassemblies and finished goods.
- Bills of material, routings, work orders and production.
- Capacity, schedule adherence, downtime, yield, scrap and rework.
- Inventory position, availability, safety stock and excess/obsolete inventory.
- Warehouse receipts, movements, picks, packs and shipments.
- Transportation, carrier performance and freight.
- Distribution centers, dealers, retailers, customers and channels.
- Returns, warranty, repair, replacement and reverse logistics.
- Product, battery platform, tool family, kit and accessory compatibility.
- Cost, purchase-price variance, landed cost and working capital.
- Supply-chain control tower, exceptions and recommended actions.

The exact scope will depend on the available Milwaukee data and authorized business definitions. I will not assume that a familiar manufacturing metric has the same definition inside Milwaukee.

## Source-system approach

When an Enterprise Data Warehouse or operational database is involved, I will first analyze:

- System purpose and ownership.
- Tables, views, procedures and source relationships.
- Business keys versus technical keys.
- Transaction boundaries and update behavior.
- CDC columns, timestamps and delete semantics.
- Source timezone and calendar behavior.
- Data volume, change rate and history availability.
- Allowed query load and extraction windows.
- Security, PII and contractual restrictions.
- Whether the source is authoritative, derived or merely convenient.

I will then choose deliberately among:


| Access pattern | Best fit |
| :-- | :-- |
| Lakehouse Federation | Discovery, governed live access and selective queries without initially copying data |
| Batch ingestion | Stable periodic extracts and moderate freshness requirements |
| CDC ingestion | Operational tables requiring inserts, updates and deletes with low latency |
| API integration | Business services that expose supported application contracts |
| File/event ingestion | Supplier feeds, IoT, telemetry, EDI-style exchanges and asynchronous events |
| Existing EDW consumption | Reuse of certified facts, dimensions and enterprise definitions |
| Direct source ingestion | Cases where the EDW lacks freshness, detail or required operational events |

Lakehouse Federation can expose external systems through Unity Catalog connections and foreign catalogs. Databricks supports sources including Oracle, SQL Server, PostgreSQL, MySQL, Teradata, Redshift, Snowflake, BigQuery and Azure Synapse, with pushdown support varying by source and query.[^2_1][^2_2][^2_3]

I will avoid placing uncontrolled analytical load on operational systems. Federation may be excellent for discovery but inappropriate for a frequently refreshed, high-volume dashboard; in that case, incremental ingestion and a purpose-built serving model will usually be safer.

## Analytical modeling

I will not create dimensions and facts merely because the source has dimension-like and fact-like names. I will establish the business process, grain, keys and history first.

Possible supply-chain facts include:

- Inventory periodic snapshot.
- Inventory movement transaction.
- Purchase-order line.
- Supplier shipment or ASN line.
- Receipt line.
- Work-order operation.
- Production output.
- Quality inspection.
- Sales-order line.
- Order-fulfillment accumulating snapshot.
- Shipment line.
- Forecast snapshot.
- Demand history.
- Return or warranty claim.
- Repair event.
- Supplier scorecard snapshot.

Possible conformed dimensions include date, time, product, SKU, component, facility, warehouse, storage location, supplier, customer, channel, geography, carrier, employee, reason code, order status and organizational hierarchy.

For every fact, I will document:

- Exact grain.
- Additivity.
- Business and surrogate keys.
- Event time and processing time.
- Currency and unit-of-measure handling.
- Late-arriving dimensions and facts.
- Corrections, cancellations and deletes.
- Required SCD behavior.
- Source-of-truth and reconciliation totals.
- Intended metrics and consumers.


## Semantic layer

A dashboard or Genie Agent should not independently redefine inventory, backlog, supplier on-time delivery or forecast accuracy. I will establish reusable metric definitions in governed views or Unity Catalog metric views where appropriate.

Metric views can declare sources, joins, fields, measures, filters, window measures and materialization. They serve as a reusable source of truth for metric meaning and can support time-series calculations such as running totals and period-over-period measures.[^2_4][^2_5][^2_6]

For example, “inventory availability” must explicitly establish:

- On-hand versus available-to-promise.
- Inclusion of quality hold and blocked stock.
- Treatment of inbound supply.
- Facility and network scope.
- Unit of measure.
- As-of timestamp.
- Product supersession.
- Whether backorders or allocations reduce availability.


## Dashboard builder mode

When you ask for a Databricks dashboard, I will behave as a dashboard product designer—not merely place several charts on a canvas.

I will define:

1. Persona and decision being supported.
2. KPI hierarchy.
3. Semantic dataset and certified measures.
4. Executive summary and operational detail.
5. Filters, drill-through and cross-filtering.
6. Targets, variance and historical context.
7. Exception queues and actionable detail.
8. Freshness and “as of” indicators.
9. Row-level security and sharing behavior.
10. Performance, refresh schedule and subscriptions.
11. Visual QA, metric QA and user-acceptance tests.
12. Source control and deployment.

AI/BI dashboards support governed datasets, calculated fields, interactive filters, cross-filtering, drill-through, scheduling, subscriptions, embedding, source control and deployment through Declarative Automation Bundles.[^2_7]

A dashboard-specific metric can begin as a local metric view and later be promoted to Unity Catalog after its semantics are validated and ready for organization-wide reuse.[^2_8]

## Genie Agent mode

A Genie Agent will be treated as a **semantic and testing project**, not a “connect tables and hope” exercise.

I will include:

- A tightly scoped business domain.
- Well-described Unity Catalog tables and columns.
- Governed metric views.
- Prejoined or simplified views where appropriate.
- Trusted SQL examples.
- Business synonyms and disambiguation rules.
- Approved and prohibited question categories.
- A benchmark set of expected questions and answers.
- SQL correctness and numerical reconciliation.
- Adversarial and ambiguous prompt testing.
- Permission and sensitive-data testing.
- Response-time and warehouse-performance testing.
- Feedback, monitoring and iterative improvement.

Databricks recommends keeping a Genie Agent focused, preferably around five or fewer necessary tables, using metric views or prejoined views to simplify the model, and expressing business semantics through SQL definitions and example queries before relying on free-text instructions.[^2_9]

When Genie is exposed through a Databricks App, I will apply least-privilege access, test expected natural-language questions, monitor query behavior and implement graceful handling when the request cannot be interpreted reliably.[^2_10]

## Transactional model mode

I will keep analytical and transactional modeling separate while designing their integration.


| Concern | Lakehouse analytical model | Lakebase transactional model |
| :-- | :-- | :-- |
| Primary purpose | History, analytics, AI and large scans | Low-latency application transactions |
| Typical modeling | Facts, dimensions and wide analytical tables | Normalized entities and application-oriented aggregates |
| Workload | Aggregation, exploration and training | Inserts, updates, point reads and short transactions |
| History | Long-term and often immutable | Current operational state plus necessary audit history |
| Integrity | Pipeline contracts and quality checks | PKs, FKs, uniqueness and transaction constraints |
| Example | Historical supplier-performance model | User-maintained supplier-risk case and action workflow |

Lakebase is managed PostgreSQL integrated with Databricks. It supports transactional application backends, low-latency serving of lakehouse data, persisting PostgreSQL changes into the lakehouse and state or memory for agents.[^2_11][^2_12]

Databricks Apps can use Lakebase as a managed PostgreSQL resource, with application identity provided through a service principal and managed connection configuration. Lakebase data can also be registered in Unity Catalog and queried alongside Delta data.[^2_13][^2_14]

For example, a supply-chain control-tower application might use:

- Delta tables for order, inventory, supplier and shipment history.
- A metric view for governed KPIs.
- Lakebase for exception cases, assignments, comments, approvals and action status.
- A Databricks App for the workflow.
- An agent for investigation and recommended actions.
- Human approval before changes reach ERP, WMS or planning systems.


## Agentic application mode

For an agentic supply-chain application, I will separate capabilities into controlled tools:

- Retrieve governed facts.
- Calculate trusted metrics.
- Explain an exception.
- Search procedures and business documentation.
- Identify likely root causes.
- Recommend possible actions.
- Simulate consequences where a validated model exists.
- Create or update a case in Lakebase.
- Request human approval.
- Call an operational API only with explicit authorization.
- Record evidence, decisions and outcomes.

The design will include:

- Read-only versus action-capable tools.
- Unity Catalog authorization.
- Prompt-injection and untrusted-data boundaries.
- Structured tool inputs and outputs.
- Idempotency and transaction safeguards.
- Human-in-the-loop approval.
- Agent memory boundaries.
- Traceability and MLflow evaluation.
- Accuracy, safety, latency and cost tests.
- Recovery when a tool or source system is unavailable.


## Profiling expert mode

For each new dataset, I will create or recommend a profiling contract covering:

- Schema and datatype conformity.
- Row counts and volume trends.
- Null and blank rates.
- Distinctness and cardinality.
- Primary-key candidates and duplicate patterns.
- Referential integrity.
- Numeric ranges and outliers.
- Categorical distributions.
- Date coverage and impossible dates.
- Freshness and ingestion lag.
- Unit-of-measure and currency consistency.
- Cross-field business rules.
- Schema and distribution drift.
- Source-to-target reconciliation.
- Baseline comparison.
- Sensitive-data discovery.

Databricks data profiling provides historical summary and distribution metrics that can be used to monitor changes and alert on data-quality shifts. Pipeline expectations can warn, drop invalid records or fail a pipeline update based on SQL Boolean constraints.[^2_15][^2_16][^2_17]

## QA expert mode

QA will cover multiple layers:


| Layer | Example tests |
| :-- | :-- |
| Source | Connectivity, schema, extraction watermark and CDC completeness |
| Bronze | File/event counts, rescued data, duplicates and ingestion metadata |
| Silver | Keys, deduplication, SCD, referential integrity and business rules |
| Gold | Grain, measures, dimensions, reconciliation and historical behavior |
| Semantic | Metric definitions, filter behavior and aggregation correctness |
| Dashboard | Visual totals, filters, drill paths, security, freshness and performance |
| Genie | Question benchmark, generated SQL, numerical answer and refusal behavior |
| Application | APIs, forms, transactions, concurrency, authentication and authorization |
| Agent | Retrieval, tool selection, evidence, hallucination, safety and approvals |
| Deployment | Bundle validation, environment configuration and smoke tests |
| Operations | Rerun, retry, backfill, alert, failure and disaster-recovery behavior |

Expectation rules can be stored separately from pipeline logic and reused across multiple datasets or pipelines, which is useful for enterprise QA standardization.[^2_18]

## External ideas

I will bring outside patterns into the project when they are useful, including:

- Manufacturing control towers.
- Retail demand and inventory analytics.
- Automotive supplier-quality models.
- Distribution-network and warehouse analytics.
- E-commerce order visibility.
- CPG forecast and promotion analytics.
- Airline or logistics exception management.
- Financial-services data-quality controls.
- Healthcare lineage and governance practices.
- Software/SRE observability and incident-management techniques.

However, outside ideas will be presented as **candidate patterns**, followed by:

1. Why the pattern might help Milwaukee.
2. Required Milwaukee data.
3. Assumptions that need validation.
4. Operational and governance risks.
5. A small proof-of-value approach.
6. Criteria for accepting or rejecting it.

## Updated default directive

For future requests, you can simply say:

> **Use Milwaukee Supply Chain Databricks FDE mode.**

I will interpret that as:

> Act as a senior Databricks supply-chain Forward Deployed Engineer and architect with expertise in enterprise integration, operational databases, EDWs, dimensional and transactional modeling, data engineering, data warehousing, Spark, SQL, data profiling, QA, AI/BI dashboards, Genie Agents, Databricks Apps, Lakebase, ML/AI and agentic applications. Understand the business process, grain, source-of-truth, consumers and operational decisions before coding. Prefer Databricks-native managed and declarative capabilities. Design the complete lifecycle: ingestion, modeling, semantics, quality, governance, security, performance, testing, CI/CD, observability, applications and operations. Reuse existing assets and supported APIs before creating custom frameworks. Bring relevant ideas from other industries, but identify them as candidate patterns and validate them against Milwaukee’s actual systems, definitions and constraints.

That is now the default development mode for this project.

<span style="display:none">[^2_19][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30]</span>

<div align="center">⁂</div>

[^2_1]: https://docs.databricks.com/aws/en/query-federation/oracle

[^2_2]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^2_3]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^2_4]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^2_5]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^2_6]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^2_7]: https://docs.databricks.com/aws/en/dashboards/

[^2_8]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^2_9]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^2_10]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^2_11]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^2_12]: https://docs.databricks.com/aws/en/oltp/projects/

[^2_13]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^2_14]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^2_15]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^2_16]: https://docs.databricks.com/aws/en/ldp/expectations

[^2_17]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^2_18]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^2_19]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^2_20]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^2_21]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^2_22]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^2_23]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^2_24]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^2_25]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^2_26]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^2_27]: https://docs.databricks.com/aws/en/ldp/concepts/

[^2_28]: https://docs.databricks.com/aws/en/query-federation/networking

[^2_29]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^2_30]: https://docs.databricks.com/aws/en/query-federation/databricks


---

# I also want you to be able to work with DABs, CICD, Bundle or something like that on Databricks

Before adding, can you do some research in this area?

Yes. The better approach is **workspace-first, promotion-ready development**—not automatically putting every experiment into a Declarative Automation Bundle.

The default lifecycle will be:

**Develop in the authorized workspace → validate with data and users → harden reusable assets → promote to Git, bundles, CI/CD, staging and production.**

## Research findings

Databricks supports notebooks, SQL queries, dashboards, YAML, Python modules, configuration files and small test fixtures directly as workspace files. Databricks recommends workspace files for code, notebooks and SQL queries, while Unity Catalog volumes should normally hold data files, libraries and build artifacts.[^3_1][^3_2]

Python modules can be developed beside notebooks and imported using standard Python imports. This provides a fast edit-run-debug cycle without having to build and install a wheel after every change.[^3_3][^3_4]

Therefore, developing directly in an assigned workspace folder is valid and often preferable during:

- Source-system discovery.
- EDW fact and dimension analysis.
- Operational-database investigation.
- Data profiling.
- SQL exploration.
- PySpark transformation development.
- Pipeline prototyping.
- KPI and semantic-model validation.
- Dashboard design.
- Genie Agent curation and testing.
- Databricks App prototyping.
- Lakebase transactional experiments.
- ML and agent evaluation.
- QA and reconciliation.


## New operating model

I will use three development stages.


| Stage | Primary goal | Typical assets |
| :-- | :-- | :-- |
| Workspace exploration | Learn and validate quickly | Notebooks, SQL, profiles, samples and diagrams |
| Workspace product development | Build a working vertical slice | Modules, pipelines, jobs, dashboards, Genie Agents and Apps |
| Production promotion | Make it repeatable and supportable | Git, tests, bundles, CI/CD, service principals and monitoring |

I will not introduce bundle scaffolding unless it provides immediate value or the work has reached the point where repeatability matters.

## In-place development

When you provide an authorized Databricks workspace folder, I will organize development approximately like this:

```text
milwaukee-supply-chain/
├── 00_admin/
│   ├── README
│   ├── assumptions
│   └── decision_log
├── 10_discovery/
│   ├── source_inventory
│   ├── edw_exploration
│   └── operational_db_analysis
├── 20_profiling/
│   ├── source_profiles
│   ├── key_analysis
│   └── reconciliation
├── 30_modeling/
│   ├── dimensional_models
│   ├── transactional_models
│   └── semantic_metrics
├── 40_pipelines/
│   ├── ingestion
│   ├── bronze
│   ├── silver
│   └── gold
├── 50_consumption/
│   ├── dashboards
│   ├── genie
│   └── apps
├── 60_qa/
│   ├── test_data
│   ├── test_queries
│   └── reconciliation
├── src/
├── tests/
└── docs/
```

This is a working convention rather than a mandatory Databricks structure. It can be simplified or aligned with your organization’s standards.

## Standard or Git folder

There are two good workspace-first options:


| Option | Best use |
| :-- | :-- |
| Standard workspace folder | Discovery, temporary experiments, collaborative troubleshooting and early prototypes |
| Databricks Git folder | Sustained development, branches, commits, pull requests and eventual bundle promotion |

Git folders are workspace folders synchronized with remote Git repositories, so development can remain inside the Databricks interface while gaining version control.[^3_5][^3_6]

For team development, each developer should have a separate Git folder and branch. Databricks advises against multiple developers performing Git operations in the same shared Git folder because branch changes can affect everyone using that folder.[^3_7]

Therefore:

- A **shared standard folder** can be our sandbox and integration location.
- A **personal Git folder** is preferable for sustained source development.
- One shared Git checkout should not be treated as a multiuser development branch.


## Notebook discipline

I will use notebooks, but I will not turn the project into notebook spaghetti.

Notebooks will primarily provide:

- Exploration and visualization.
- Business narrative.
- Interactive debugging.
- Parameter entry.
- Demonstrations.
- Pipeline or job entry points.
- QA evidence.

Reusable transformations, profiling functions and business rules will move into nearby `.py` modules as they stabilize. Databricks supports importing those modules directly from workspace files.[^3_4][^3_3]

That gives us rapid in-place development without requiring premature wheel packaging.

## Promotion triggers

Not everything developed in the workspace needs a bundle. I will recommend promotion when an asset becomes:

- Scheduled or event-driven.
- Shared by other teams or data products.
- An upstream dependency.
- Responsible for writing governed tables.
- Used by an executive or operational dashboard.
- Used by a production Genie Agent.
- Part of a Databricks App.
- Connected to a production Lakebase database.
- Associated with an SLA.
- Dependent on environment-specific configuration.
- Maintained by multiple engineers.
- Required to run under a service principal.
- Important enough to need repeatable recovery.
- Capable of affecting security, cost or business decisions.

A temporary profiling notebook does not automatically need a bundle. A supplier-performance pipeline feeding a dashboard and Genie Agent almost certainly does.

## Promotion process

When an in-place prototype is ready, I will:

1. Remove unnecessary notebook state and display commands.
2. Extract reusable code into importable modules.
3. Eliminate personal paths and hard-coded IDs.
4. Parameterize catalogs, schemas, warehouses, endpoints and schedules.
5. Add unit, contract, integration and reconciliation tests.
6. Connect the assets to Git.
7. Define relevant jobs, pipelines, dashboards, Apps and permissions in a bundle.
8. Define development, staging and production targets.
9. Add CI validation and staging tests.
10. Configure deployment and runtime service principals.
11. Add monitoring, recovery and deployment documentation.
12. Promote the same tested artifact into production.

Bundles themselves can also be authored from a Databricks Git folder. Databricks supports editing the bundle YAML, source files, notebooks, jobs, pipelines and dashboards in the workspace before committing and deploying them.[^3_8][^3_9]

## Development job policy

During rapid iteration, a development job or pipeline may reference code in the authorized workspace or Git folder. For staging and production, it should move to a controlled Git or bundle-based deployment.

Databricks recommends workspace paths in Git folders for rapid iteration and testing, but recommends remote Git sources for staging and production jobs.[^3_10][^3_11]

So the default distinction will be:

- **Development:** workspace source is acceptable.
- **Staging:** reproducible and versioned source required.
- **Production:** bundle/Git/CI/CD-controlled source and identity required.


## Storage guardrail

The workspace folder should hold code and development assets—not become a general data lake.


| Content | Preferred location |
| :-- | :-- |
| Notebooks and SQL | Workspace or Git folder |
| Python modules | Workspace or Git folder |
| Documentation and YAML | Workspace or Git folder |
| Small test fixtures | Workspace files or a test volume |
| Source extracts | Unity Catalog volume or governed table |
| Pipeline data | Unity Catalog Delta tables |
| Build artifacts | Unity Catalog volume or artifact repository |
| Checkpoints | Controlled cloud/UC location |
| Production application data | Lakebase or governed Delta tables, according to workload |

Databricks recommends Unity Catalog volumes for data, libraries and build artifacts.[^3_12][^3_1]

## Access needed

For actual in-place work, I would need an authorized Databricks connection—not only the textual folder path. Depending on the available integration, that means a Databricks CLI/SDK/API authentication context or another controlled mechanism that lets me operate in the workspace.

The working identity would typically need:

- Edit access to the assigned development folder.
- Use access to approved SQL warehouses or compute.
- Read access to authorized Unity Catalog source objects.
- Write access to a development catalog and schema.
- Access to a development volume if files are needed.
- Permission to create development jobs, pipelines, dashboards, Genie Agents or Apps when required.
- No default write access to production sources or production schemas.

Workspace notebooks and objects can be managed through the UI, CLI and Workspace APIs. Folder permissions are inherited by contained workspace objects, making the assigned folder a useful access-control boundary.[^3_13][^3_14][^3_15]

## Updated directive

Going forward, **Milwaukee Supply Chain Databricks FDE mode** will include this instruction:

> Start in the authorized Databricks development workspace when discovery, profiling, interactive debugging, business validation or rapid user-experience iteration is needed. Create organized notebooks, SQL, modules, pipelines, dashboards, Genie assets, Apps and approved development resources in place. Keep reusable logic modular and promotion-ready. Do not force every experiment into a bundle. When an asset becomes reusable, scheduled, shared, governed, SLA-backed or production-impacting, refactor it into Git, tests, Declarative Automation Bundles, CI/CD, service-principal execution, monitoring and controlled staging/production deployment.

The governing principle is:

> **Use the fastest safe development loop, while preserving a clear path to a reproducible and operable production product.**

<span style="display:none">[^3_100][^3_101][^3_102][^3_103][^3_104][^3_105][^3_106][^3_107][^3_108][^3_109][^3_110][^3_111][^3_112][^3_113][^3_114][^3_115][^3_116][^3_117][^3_118][^3_119][^3_120][^3_121][^3_122][^3_123][^3_124][^3_125][^3_126][^3_127][^3_128][^3_129][^3_130][^3_131][^3_132][^3_133][^3_134][^3_135][^3_136][^3_137][^3_138][^3_139][^3_140][^3_141][^3_16][^3_17][^3_18][^3_19][^3_20][^3_21][^3_22][^3_23][^3_24][^3_25][^3_26][^3_27][^3_28][^3_29][^3_30][^3_31][^3_32][^3_33][^3_34][^3_35][^3_36][^3_37][^3_38][^3_39][^3_40][^3_41][^3_42][^3_43][^3_44][^3_45][^3_46][^3_47][^3_48][^3_49][^3_50][^3_51][^3_52][^3_53][^3_54][^3_55][^3_56][^3_57][^3_58][^3_59][^3_60][^3_61][^3_62][^3_63][^3_64][^3_65][^3_66][^3_67][^3_68][^3_69][^3_70][^3_71][^3_72][^3_73][^3_74][^3_75][^3_76][^3_77][^3_78][^3_79][^3_80][^3_81][^3_82][^3_83][^3_84][^3_85][^3_86][^3_87][^3_88][^3_89][^3_90][^3_91][^3_92][^3_93][^3_94][^3_95][^3_96][^3_97][^3_98][^3_99]</span>

<div align="center">⁂</div>

[^3_1]: https://docs.databricks.com/aws/en/files/files-recommendations

[^3_2]: https://docs.databricks.com/gcp/en/files/workspace

[^3_3]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^3_4]: https://docs.databricks.com/aws/en/repos/ci-cd

[^3_5]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^3_6]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^3_7]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^3_8]: https://docs.databricks.com/aws/en/files/workspace-modules

[^3_9]: https://docs.databricks.com/aws/en/notebooks/share-code

[^3_10]: https://docs.databricks.com/aws/en/jobs/git

[^3_11]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^3_12]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^3_13]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^3_14]: https://docs.databricks.com/aws/en/volumes/volume-files

[^3_15]: https://docs.databricks.com/aws/en/tables/history

[^3_16]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^3_17]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^3_18]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^3_19]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^3_20]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^3_21]: https://docs.databricks.com/gcp/en/developers/best-practices

[^3_22]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^3_23]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^3_24]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^3_25]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^3_26]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^3_27]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^3_28]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^3_29]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^3_30]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^3_31]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^3_32]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^3_33]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^3_34]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^3_35]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^3_36]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^3_37]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^3_38]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^3_39]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^3_40]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^3_41]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^3_42]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^3_43]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^3_44]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^3_45]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^3_46]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^3_47]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^3_48]: https://docs.databricks.com/aws/en/developers/best-practices

[^3_49]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^3_50]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^3_51]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^3_52]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^3_53]: https://docs.databricks.com/aws/en/notebooks/testing

[^3_54]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^3_55]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^3_56]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^3_57]: https://docs.databricks.com/aws/en/release-notes/product/

[^3_58]: https://docs.databricks.com/aws/en/compute/web-terminal

[^3_59]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^3_60]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^3_61]: https://docs.databricks.com/aws/en/repos/limits

[^3_62]: https://docs.databricks.com/aws/en/files/workspace-interact

[^3_63]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^3_64]: https://docs.databricks.com/api/jobs/v2/job

[^3_65]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^3_66]: https://docs.databricks.com/aws/en/repos/repos-setup

[^3_67]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^3_68]: https://docs.databricks.com/aws/en/files/workspace

[^3_69]: https://docs.databricks.com/aws/en/jobs/privileges

[^3_70]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^3_71]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^3_72]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^3_73]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^3_74]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^3_75]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^3_76]: https://docs.databricks.com/aws/en/ldp/concepts

[^3_77]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^3_78]: https://docs.databricks.com/aws/en/ldp/

[^3_79]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^3_80]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^3_81]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^3_82]: https://docs.databricks.com/aws/en/ldp/real-time

[^3_83]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^3_84]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^3_85]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^3_86]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^3_87]: https://docs.databricks.com/aws/en/tables/clustering

[^3_88]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^3_89]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^3_90]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^3_91]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^3_92]: https://docs.databricks.com/aws/en/delta/tutorial

[^3_93]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^3_94]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^3_95]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^3_96]: https://docs.databricks.com/aws/en/mlflow/

[^3_97]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^3_98]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^3_99]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^3_100]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^3_101]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^3_102]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^3_103]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^3_104]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^3_105]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^3_106]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^3_107]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^3_108]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^3_109]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^3_110]: https://docs.databricks.com/gcp/en/languages/overview

[^3_111]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^3_112]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^3_113]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^3_114]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^3_115]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^3_116]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^3_117]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^3_118]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^3_119]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^3_120]: https://docs.databricks.com/aws/en/oltp/projects/

[^3_121]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^3_122]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^3_123]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^3_124]: https://docs.databricks.com/aws/en/dashboards/

[^3_125]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^3_126]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^3_127]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^3_128]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^3_129]: https://docs.databricks.com/aws/en/query-federation/oracle

[^3_130]: https://docs.databricks.com/aws/en/ldp/expectations

[^3_131]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^3_132]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^3_133]: https://docs.databricks.com/aws/en/ldp/concepts/

[^3_134]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^3_135]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^3_136]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^3_137]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^3_138]: https://docs.databricks.com/aws/en/query-federation/networking

[^3_139]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^3_140]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^3_141]: https://docs.databricks.com/aws/en/query-federation/databricks


---

# and the Databricks Apps will not be just any Apps, It will be Agentic AI App. Helping in the supply chain and will have writebacks and live actions with lakebase! I will be using Unity AI Gateway, Model Serving Endpoints, will train a few ML Models likely for forecasting!

I also want you to be able to have the platform and networking knowledge. I don't want to get stuck on silly authentication .. and wrong way to login issues!

Absolutely. I will expand **Milwaukee Supply Chain Databricks FDE mode** to include **Agentic AI application engineering, transactional Lakebase writebacks, live operational actions, Unity AI Gateway, Model Serving, forecasting/ML, platform architecture, networking, identity, and authentication troubleshooting**.

The application will not be treated as a generic dashboard or chatbot. It will be designed as a governed **supply-chain decision-and-action system** with clear separation between observing, recommending, approving, and executing.

## Reference architecture

The normal architecture will look like this:

```text
ERP / WMS / TMS / MES / Planning / EDW / Supplier Systems
                         │
                         ▼
        Lakeflow ingestion and transformation
                         │
                         ▼
      Unity Catalog + Delta analytical data products
         Facts │ Dimensions │ Features │ Metrics
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
 Forecasting / ML models          Genie / Agent tools
 MLflow + UC Registry             Unity AI Gateway
 Model Serving                    Model Serving
          └──────────────┬──────────────┘
                         ▼
              Agentic Databricks App
          Investigate │ Recommend │ Execute
                         │
                         ▼
                 Lakebase PostgreSQL
     Cases │ Actions │ Approvals │ Comments │ Audit
                         │
                         ▼
      Approved operational APIs and live actions
```

Databricks Apps can declare dependencies on model-serving endpoints, Genie Agents, SQL warehouses, jobs, secrets, volumes and other platform resources. Those dependencies receive explicit permissions for the App’s dedicated service principal.[^4_1][^4_2]

## Agentic supply-chain Apps

A typical application could support:

- Investigating late purchase orders and supplier shortages.
- Explaining forecast-versus-actual demand deviations.
- Identifying inventory at risk of shortage or obsolescence.
- Recommending transfers between distribution centers.
- Prioritizing production or replenishment exceptions.
- Investigating shipment delays.
- Creating supplier follow-up cases.
- Recommending revised safety-stock parameters.
- Preparing—but not silently submitting—operational transactions.
- Executing approved actions through governed APIs.
- Tracking whether an action improved the outcome.

Databricks supports custom tool-calling agents, retrieval-augmented applications and multi-agent systems, with Databricks Apps providing interactive UIs such as chat, forms and operational workflows.[^4_3][^4_4]

## Action safety model

The agent will not receive unrestricted write access merely because it can answer questions.


| Action class | Example | Default control |
| :-- | :-- | :-- |
| Observe | Retrieve inventory availability | Read-only, governed access |
| Analyze | Explain a shortage | Read-only tools with traceable evidence |
| Recommend | Suggest an inventory transfer | Persist proposal in Lakebase |
| Simulate | Estimate effect of the transfer | Validated calculation/model |
| Prepare | Construct an ERP transaction request | Schema validation and idempotency key |
| Approve | Planner accepts the proposal | Named user, role and approval record |
| Execute | Call ERP/WMS/TMS API | Dedicated action service principal |
| Verify | Confirm the external update | Read-back and reconciliation |
| Compensate | Reverse or repair a failed action | Approved recovery workflow |

High-impact actions will default to **human approval**, unless you explicitly identify a narrow, low-risk action suitable for controlled automation.

Every live action should have:

- A typed and validated command.
- Business-rule validation.
- User and agent identity.
- Source evidence.
- Approval status.
- Idempotency key.
- Transaction status.
- External-system correlation ID.
- Before-and-after values.
- Timestamp and reason.
- Retry and timeout rules.
- Verification query.
- Compensation or manual recovery path.


## Lakebase responsibility

Lakebase will serve as the transactional control plane for the App, not as a replacement for the analytical lakehouse.


| Lakebase | Delta and Unity Catalog |
| :-- | :-- |
| Cases and exceptions | Historical facts and dimensions |
| Recommendations | Large-scale analytical datasets |
| User comments | Feature engineering |
| Assignments | Forecast history |
| Approvals | Supply-chain metrics |
| Action status | Training datasets |
| Workflow state | Audit-scale event analytics |
| Short-lived agent state | Long-term trace and result analysis |
| Idempotency records | Batch and streaming transformations |

Lakebase provides managed PostgreSQL for transactional application backends, while Databricks Apps can attach a Lakebase database as a native resource.[^4_5][^4_6][^4_7]

The App’s Lakebase schema will use transactional engineering practices:

- Primary and foreign keys.
- Unique and check constraints.
- Optimistic locking or explicit locking where appropriate.
- Database transactions.
- Schema migrations.
- Idempotent write APIs.
- Outbox pattern for reliable external actions where justified.
- Audit/event tables.
- Application roles.
- Backup and recovery planning.
- Development, staging and production database separation.


## Identity for writebacks

Databricks Apps supports two complementary identity models:

- **App authorization:** the application acts using its dedicated service principal.
- **User authorization:** the application acts on behalf of the signed-in user and Databricks enforces that user’s existing permissions.[^4_8]

I will choose identity per operation rather than use one identity everywhere:


| Operation | Preferred identity |
| :-- | :-- |
| Read shared application configuration | App service principal |
| Run a background monitoring process | Runtime service principal |
| Access user-governed analytical data | On-behalf-of-user when appropriate |
| Insert an App workflow record | App service principal plus recorded user identity |
| Approve an operational action | Authenticated user identity |
| Execute an external-system action | Dedicated action service principal |
| Deploy the App or endpoint | CI/CD deployment service principal |
| Perform platform administration | Separate platform-admin identity |

This prevents the dangerous situation where every App user inherits broad access simply because the App’s service principal has it. Databricks notes that app-only authorization gives all App users the service principal’s shared effective access, whereas on-behalf-of-user authorization preserves user-level Unity Catalog enforcement.[^4_8]

## Lakebase authentication

For Databricks Apps, Lakebase OAuth tokens expire after one hour. The correct implementation creates an OAuth-enabled PostgreSQL role for the App’s service principal and obtains fresh credentials as new database connections are opened.[^4_9]

A subtle distinction matters:

- An application can use a **client-side connection pool** that creates new connections with refreshed OAuth credentials.
- Lakebase’s **built-in PgBouncer pooler** currently requires native PostgreSQL password roles and is not available for OAuth roles.[^4_10][^4_9]

I will not accidentally use one-hour OAuth credentials as static startup passwords. The connection factory will refresh credentials, expire old pool connections, configure sensible pool size and timeouts, and retry only safe operations.

## Unity AI Gateway

Unity AI Gateway will be the governed entry point for foundation models and external model providers when applicable. It can centralize access control, guardrails, traffic management, usage tracking and provider credentials through Unity Catalog securables.[^4_11][^4_12]

The application should authenticate to Databricks and invoke the governed provider service or endpoint; it should not receive the external provider’s raw API key. For model-provider services, the caller uses a Databricks token while Unity AI Gateway stores and applies the provider credentials.[^4_11]

I will account for:

- Endpoint or provider-service selection.
- `CAN QUERY` and management permissions.
- Rate and budget limits.
- Usage attribution.
- Input/output guardrails.
- Payload and trace logging policy.
- Sensitive-data handling.
- Model fallback behavior.
- Latency and token budgets.
- Region and data-residency constraints.
- Prompt and model versioning.
- Evaluation before promotion.


## Forecasting lifecycle

Forecasting will be treated as a supply-chain ML product, not just a notebook that fits a model.

The lifecycle will include:

1. Define the forecast decision, grain, horizon and refresh frequency.
2. Establish demand history and time-series identifiers.
3. Detect stockouts, lost sales, promotions, returns and one-time events.
4. Engineer calendar, product, customer, channel, price, promotion and supply features.
5. Establish naive and seasonal baselines.
6. Use time-aware train/validation/test splits.
7. Evaluate by business-relevant segments.
8. Track experiments, metrics and artifacts in MLflow.
9. Register approved models in Unity Catalog.
10. Run batch inference or deploy through Model Serving based on the use case.
11. Monitor actuals, residuals, bias, drift and business impact.
12. Define retraining and champion/challenger rules.

Databricks forecasting supports single- and multi-series workloads, forecast horizons, time-aware splits, weighting, holiday covariates, Unity Catalog prediction outputs and model registration.[^4_13][^4_14]

The model’s deployment will follow MLflow format → Unity Catalog registration → batch inference or Model Serving endpoint. Databricks integrates MLflow tracking, Feature Engineering, Models in Unity Catalog, Model Serving and request/response monitoring into the model lifecycle.[^4_15][^4_16][^4_17]

## Authentication standard

I will treat **authentication and authorization as architecture**, not as last-minute troubleshooting.


| Scenario | Default authentication |
| :-- | :-- |
| Interactive CLI and SDK development | OAuth user-to-machine |
| Automated jobs and services | OAuth machine-to-machine |
| CI/CD | Workload identity federation/OIDC where available |
| Databricks App acting as itself | Injected App service-principal identity |
| App respecting end-user permissions | On-behalf-of-user OAuth |
| Lakebase from Databricks App | OAuth database role with credential rotation |
| External App to Lakebase | Databricks SDK-generated database credentials |
| Model endpoint invocation | Databricks OAuth/token with endpoint permission |
| Foundation-model provider | Databricks authentication through Unity AI Gateway |
| Cloud-resource access | Workspace or serverless cloud identity, not embedded cloud keys |

Databricks recommends OAuth token federation when possible, OAuth U2M for interactive user access and OAuth M2M for unattended service-principal access. Unified authentication handles short-lived token generation and refresh for supported CLIs and SDKs.[^4_18][^4_19][^4_20]

Personal access tokens will not be the default for new automation. They may be used only when the environment or integration lacks a supported OAuth option and the security team permits them.

## Login troubleshooting

When authentication fails, I will diagnose it systematically instead of trying random token variations:

1. **Identify the target:** Databricks account, workspace, SQL warehouse, serving endpoint, Lakebase endpoint, cloud resource or external API.
2. **Identify the actor:** user, service principal, App service principal, CI workload, job runtime or on-behalf-of-user identity.
3. **Identify the protocol:** U2M OAuth, M2M OAuth, OIDC federation, App OAuth, database OAuth or native PostgreSQL.
4. **Confirm the host:** account URL versus workspace URL versus Lakebase hostname.
5. **Confirm workspace assignment and entitlements.**
6. **Confirm object permissions:** `CAN USE`, `CAN QUERY`, catalog privileges, endpoint permissions and database role.
7. **Confirm token audience, issuer and expiry.**
8. **Confirm the correct Databricks CLI/SDK profile and environment-variable precedence.**
9. **Confirm network reachability, DNS, ports, proxies, firewalls and PrivateLink.**
10. **Test with the smallest supported call before debugging application code.**
11. **Record the working identity and configuration without exposing secrets.**

A successful login only proves authentication. It does not prove authorization to use a warehouse, query a model, access Unity Catalog data, connect to Lakebase or invoke a live action.

## Platform knowledge

I will include platform-level understanding for:

- Account versus workspace administration.
- Identity federation and SCIM.
- Users, groups and service principals.
- Workspace assignment and entitlements.
- Unity Catalog metastores, catalogs, schemas and privileges.
- Compute policies.
- SQL warehouses.
- Serverless versus classic compute.
- Storage credentials and external locations.
- Secrets and OAuth.
- Jobs, pipelines and runtime identities.
- Model-serving endpoint permissions.
- App resources and App service principals.
- Lakebase projects, branches, endpoints, roles and databases.
- Audit logs and system tables.
- Terraform and account-level infrastructure.
- Bundles for workload delivery.
- Cross-environment and cross-workspace promotion.


## Network knowledge

Networking will be checked end-to-end:

```text
User browser
   → Databricks workspace/App ingress
   → App runtime
   → Unity AI Gateway/Model Serving
   → SQL warehouse/Unity Catalog
   → Lakebase
   → EDW and operational databases
   → ERP/WMS/TMS external action APIs
```

For serverless workloads, Network Connectivity Configurations are account-level, regional objects that manage private endpoints and can be attached to multiple workspaces in the same region.[^4_21][^4_22]

For AWS private connectivity, I will examine:

- Workspace region and VPC region.
- Inbound versus outbound PrivateLink.
- NCC attachment.
- Private endpoint rule status.
- NLB endpoint services.
- Resource policies and security groups.
- Route and firewall behavior.
- Private DNS resolution.
- Required FQDNs and ports.
- Proxy and egress allowlists.
- Cross-region behavior.
- Connectivity cost.

For other clouds, I will use the equivalent Azure or GCP design rather than blindly applying AWS terminology.

## App networking

Databricks Apps supports controlled ingress and egress. For private App ingress on AWS, DNS must correctly resolve the `databricksapps.com` domain through the private route; incorrect conditional DNS forwarding can cause an App URL to resolve publicly or fail from the corporate network.[^4_23]

For each App dependency, I will document a connectivity matrix:


| Source | Destination | Protocol/port | Identity | Network path |
| :-- | :-- | :-- | :-- | :-- |
| Browser | Databricks App | HTTPS/443 | User OAuth | Public or private ingress |
| App | Model Serving | HTTPS/443 | App or user identity | Databricks platform |
| App | Unity AI Gateway | HTTPS/443 | App identity | Databricks platform |
| App | Lakebase | PostgreSQL/5432 | OAuth database role | Platform/private path |
| App | SQL warehouse | HTTPS/443 | App or user identity | Databricks platform |
| Serverless pipeline | Operational database | Database-specific | Runtime identity | NCC/private endpoint |
| Action service | ERP/WMS API | HTTPS/443 | Action service principal | Approved private/egress path |

Databricks documents direct TCP testing of Lakebase on port 5432 and HTTPS-based platform access on port 443 when validating private connectivity.[^4_24]

## Default deliverables

For an Agentic Supply Chain App, I will now provide:

- Architecture and trust-boundary diagram.
- App personas and operational use cases.
- Agent/tool/action contract.
- Lakebase transactional model.
- Delta analytical and ML model.
- Writeback and live-action workflow.
- Identity and permission matrix.
- Network connectivity matrix.
- Authentication configuration.
- Local and workspace development instructions.
- Secret-free login approach.
- Unity AI Gateway configuration.
- Model-serving endpoint design.
- Forecasting lifecycle.
- Human-approval and safety controls.
- MLflow tracing and evaluation.
- Unit, integration, security and agent tests.
- Failure, retry, idempotency and recovery design.
- Workspace-first development approach.
- Bundle and CI/CD promotion approach.
- Monitoring, audit and operating runbook.


## Updated project mode

From now on, **Milwaukee Supply Chain Databricks FDE mode** also means:

> Build governed Agentic AI supply-chain applications—not generic Apps. Use Databricks Apps for the user experience, Unity AI Gateway for governed AI access, MLflow for tracing and evaluation, Model Serving for AI and ML inference, Unity Catalog for governance, Delta for analytical history, and Lakebase for transactional workflow state, writebacks, approvals and live actions. Separate observation, recommendation, approval, execution and verification. Apply transactional integrity, idempotency, auditability and human approval to operational actions. Include forecasting and ML lifecycle engineering. Design identity, OAuth, service principals, on-behalf-of-user authorization, permissions, networking, DNS, PrivateLink/NCC, ports and connectivity as first-class architecture. Diagnose authentication by target, actor, protocol, entitlement, permission and network path—never by randomly changing credentials.

This capability is now part of the default operating model.

<span style="display:none">[^4_25][^4_26][^4_27][^4_28][^4_29][^4_30][^4_31][^4_32][^4_33][^4_34][^4_35][^4_36][^4_37][^4_38][^4_39][^4_40][^4_41][^4_42][^4_43][^4_44][^4_45]</span>

<div align="center">⁂</div>

[^4_1]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^4_2]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^4_3]: https://docs.databricks.com/aws/en/agents/

[^4_4]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^4_5]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^4_6]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^4_7]: https://docs.databricks.com/aws/en/oltp/projects/

[^4_8]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^4_9]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^4_10]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^4_11]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^4_12]: https://docs.databricks.com/aws/en/ai-gateway/

[^4_13]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^4_14]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^4_15]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^4_16]: https://docs.databricks.com/aws/en/mlflow/

[^4_17]: https://docs.databricks.com/aws/en/machine-learning/

[^4_18]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^4_19]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^4_20]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^4_21]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^4_22]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^4_23]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^4_24]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^4_25]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^4_26]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^4_27]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^4_28]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^4_29]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^4_30]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^4_31]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^4_32]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^4_33]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^4_34]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^4_35]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^4_36]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^4_37]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^4_38]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^4_39]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^4_40]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^4_41]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^4_42]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^4_43]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^4_44]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^4_45]: https://docs.databricks.com/aws/en/machine-learning/automl/classification


---

# I also want you to learn about the Supply Chain Domain for Actual vs Plain, Demand Planning, Exceptions and other things ..

Yes—I will add **Supply Chain Planning and Exception Management expertise** to the operating model. I assume “Actual vs Plain” means **Actual vs Plan**; if “Plain” is the name of a Milwaukee dataset or internal process, I’ll treat it accordingly.

The key point is that **Actual vs Plan is not simply subtracting two columns**. A valid analysis must align planning version, forecast vintage, demand signal, grain, calendar, units, currency, product/location hierarchy, and the date on which the forecast was frozen.

## Domain scope

I will build working knowledge across:


| Area | Questions answered |
| :-- | :-- |
| Demand planning | What is expected to sell, ship, order or be consumed—and when and where? |
| Actual vs Plan | What happened compared with the frozen expectation? |
| Forecast performance | How large was the error, in which direction, and at what planning lag? |
| Demand sensing | Have recent orders, sales, inventory or market signals changed the near-term outlook? |
| Supply planning | Can suppliers, production, capacity and inventory satisfy demand? |
| Inventory planning | How much inventory is needed, where, and at what service/cost trade-off? |
| Exception management | Which deviations require action now, by whom, and why? |
| Scenario planning | What happens if demand, supply, capacity or lead time changes? |
| S\&OP/IBP | How should demand, supply and financial plans be reconciled? |
| Execution | What approved actions should reach ERP, WMS, TMS, MES or planning systems? |

Demand planning is the process of developing a credible view of future demand to guide inventory, capacity and service decisions. It combines statistical forecasting with market knowledge and cross-functional judgment; supply planning then determines how that demand can be fulfilled.[^5_1][^5_2]

## Actual vs Plan

For every comparison, I will explicitly identify:

- **Actual:** orders, shipments, point-of-sale, consumption, production, receipts or financial actuals.
- **Plan:** statistical forecast, planner-adjusted forecast, consensus demand plan, supply plan, production plan, budget or latest estimate.
- **Forecast vintage:** the exact version generated or approved at a particular date.
- **Lag:** how far before the demand period the plan was produced.
- **Grain:** product × location × customer/channel × time bucket.
- **Calendar:** day, fiscal week, month, quarter and planning calendar.
- **Unit:** each, case, pallet, standard unit, weight, currency or revenue.
- **Hierarchy:** SKU, product family, platform, facility, distribution center, region or customer.
- **Scenario:** baseline, upside, downside, constrained, unconstrained or approved consensus.
- **Status:** draft, submitted, approved, published, superseded or frozen.

A January forecast for June must not be overwritten by the May reforecast if we want to measure forecast quality at a five-month planning lag. **Forecast snapshots and version history are therefore foundational data-model requirements.**

## Demand signals

“Actual demand” can have several meanings:


| Signal | What it represents | Potential issue |
| :-- | :-- | :-- |
| Customer order | Expressed customer demand | Cancellations, duplicates or requested-date changes |
| Shipment | Fulfilled demand | Understates demand during shortages |
| Invoice | Financially recognized sale | Timing may differ from physical demand |
| Point-of-sale | Downstream consumer purchase | May arrive late or only from some channels |
| Consumption | Material/component usage | Represents dependent rather than independent demand |
| Lost sale | Demand that could not be fulfilled | Often estimated rather than directly observed |
| Transfer order | Internal network movement | Must not automatically be treated as external demand |
| Return | Reverse demand | Requires separate treatment from new demand |

Actual sales or shipments can understate true demand during stockouts because customers could not purchase available product. Historical demand must therefore be cleansed for stockouts, abnormal orders, promotions, product introductions and discontinuations before it is used for model training or forecast evaluation.[^5_2][^5_3]

Forecast consumption must also be modeled correctly. As actual sales orders arrive, they may consume the forecast so that the planning system does not count both forecast demand and actual demand; Oracle describes this as reducing gross forecast by sales-order demand to produce a net forecast.[^5_4]

## Planning versions

The analytical model should preserve a **plan-vintage fact**, for example:

```text
fact_demand_plan_snapshot
─────────────────────────
plan_version_key
snapshot_date_key
demand_period_key
product_key
location_key
customer_or_channel_key
scenario_key
forecast_lag
statistical_forecast_qty
planner_override_qty
consensus_plan_qty
financial_plan_amount
published_plan_qty
```

This enables comparisons such as:

- Actual versus original annual operating plan.
- Actual versus monthly consensus plan.
- Actual versus latest forecast.
- Actual versus statistical baseline.
- Actual versus planner override.
- Actual versus model forecast.
- Current forecast versus previous forecast.
- Consensus plan versus financial target.
- Unconstrained demand versus constrained supply.
- Forecast at one-, four-, eight- and twelve-week lags.

Without versioning, “actual versus forecast” usually becomes unreliable because the forecast changes as the actual period approaches.

## Performance metrics

I will not use one universal “forecast accuracy” formula without agreement. Different products, demand patterns and decision horizons require different metrics.


| Metric | What it reveals |
| :-- | :-- |
| Error | Signed difference between actual and forecast |
| Absolute error | Magnitude of the miss |
| WAPE/WMAPE | Volume-weighted aggregate error |
| MAE | Average absolute unit error |
| RMSE | Penalizes larger misses more heavily |
| MAPE | Percentage error, but unstable around zero actual demand |
| Bias | Persistent over- or under-forecasting |
| Tracking signal | Whether cumulative bias is becoming abnormal |
| Forecast Value Added | Whether overrides or process stages improve upon a baseline |
| Attainment | Actual as a percentage of plan |
| Plan variance | Absolute and percentage difference from plan |
| Service impact | Whether error caused shortages, lateness or excess stock |
| Inventory impact | Working capital or obsolescence created by planning error |

Accuracy measures error magnitude, while bias measures persistent error direction; both must be examined because acceptable aggregate accuracy can hide systematic over- or under-forecasting.[^5_5][^5_3]

I will also evaluate **Forecast Value Added** by comparing stages:

```text
Naive baseline
    → Statistical forecast
    → Planner override
    → Sales/marketing input
    → Consensus plan
    → Final published forecast
```

This determines whether each intervention improved the forecast or introduced noise. AWS recommends comparing actuals with naive and consensus forecasts to assess the value added during collaborative planning.[^5_6]

## Segmentation

Forecast and exception logic should change by segment. I will consider:

- ABC segmentation by volume or value.
- XYZ segmentation by demand variability.
- Stable, seasonal, intermittent and lumpy demand.
- New products with little or no history.
- End-of-life and superseded products.
- Promotional versus baseline demand.
- Strategic customers and channels.
- Long-lead-time components.
- Capacity-constrained products.
- High-margin or high-service-impact products.
- Repair parts versus finished tools.
- Product kits and component dependencies.

A low-volume intermittent repair part should not be measured or planned identically to a high-volume stable product.

## Exception management

The goal is not to show planners thousands of red rows. It is to identify a manageable set of **material, actionable and explainable exceptions**.

Potential demand exceptions include:

- Actual demand materially above or below plan.
- Forecast bias beyond threshold.
- Forecast accuracy deterioration.
- Large forecast change between versions.
- Planner override without documented reason.
- Statistical forecast and consensus plan divergence.
- Promotion missing from the plan.
- New-product forecast without an analogous product.
- Discontinued product still receiving demand.
- Demand spike, drop or outlier.
- Customer forecast and internal forecast misalignment.
- Forecast below booked orders.
- Forecast consumption anomaly.

Potential supply exceptions include:

- Demand not satisfied.
- Inventory projected below safety stock.
- Late replenishment.
- Supplier capacity shortage.
- Manufacturing-resource overload.
- Insufficient lead time.
- Purchase order delayed or short-shipped.
- Inventory excess or expiration risk.
- Supply-demand imbalance.
- Component shortage affecting a finished product.
- Transfer recommendation not executed.

Oracle’s predefined planning exceptions include unsatisfied demand, insufficient lead time, resource shortages, supplier-capacity shortages, projected inventory below safety stock and late replenishment for forecasts or sales orders.[^5_7]

## Exception prioritization

An exception should be ranked by business impact rather than deviation alone. A candidate model is:

```text
Priority =
    severity
  × financial impact
  × service impact
  × urgency
  × confidence
  × actionability
```

I will include:

- Exception type and severity.
- Product, location and affected period.
- Plan, actual or projected value.
- Absolute and percentage variance.
- Financial and service impact.
- Likely root cause.
- Evidence and related records.
- Recommended action.
- Responsible planner or team.
- Due date and escalation.
- Approval requirement.
- Action status and outcome.
- Suppression, snooze and deduplication controls.

This is the natural foundation for the planned **Agentic AI Supply Chain App**.

## Agentic workflow

The App can implement a closed-loop workflow:

1. Detect a material exception.
2. Rank it by impact and urgency.
3. Retrieve demand, inventory, supply, orders and planning context.
4. Explain likely causes.
5. Show plan versions and supporting evidence.
6. Recommend one or more actions.
7. Simulate likely consequences.
8. Capture planner decision and comments in Lakebase.
9. Obtain approval for impactful actions.
10. Execute through an approved live-action API.
11. Verify the external-system result.
12. Measure whether the action resolved the exception.
13. Use the outcome to improve future recommendations.

Lakebase would store the operational case, assignment, recommendation, approval, action and outcome. Delta and Unity Catalog would retain analytical history, forecast snapshots, model features and large-scale performance analysis.

## Milwaukee considerations

For Milwaukee Tool, I will expect—but verify rather than assume—planning challenges involving:

- Tools, batteries, chargers, accessories and kits.
- Product-family and battery-platform relationships.
- Components shared across multiple finished products.
- New-product introductions and product transitions.
- Dealer, retailer, distributor and direct-channel demand.
- Promotions and seasonal demand.
- Distribution-center inventory.
- Supplier and manufacturing constraints.
- Finished-goods versus service-part demand.
- Returns, warranty and repair demand.
- Geographic and channel-specific planning.
- Internal transfer orders versus customer demand.

These are candidate domain patterns until confirmed against Milwaukee’s systems, terminology and data.

## Added capability

**Milwaukee Supply Chain Databricks FDE mode** will now also mean:

> Understand demand planning, actual-versus-plan analysis, forecast vintages, planning horizons, demand signals, forecast consumption, statistical baselines, planner overrides, consensus planning, forecast accuracy, bias, Forecast Value Added, demand segmentation, constrained and unconstrained plans, supply-demand matching and exception-based planning. Never compare actual and plan without aligning version, lag, grain, calendar, units, hierarchy and business definition. Preserve forecast snapshots, distinguish true demand from fulfilled sales, identify actionable exceptions, calculate operational impact, support root-cause analysis, recommend and simulate actions, capture approvals and writebacks in Lakebase, execute authorized live actions safely, and measure the result in a closed loop.

This supply-chain domain model will guide the data model, dashboards, Genie Agent, forecasting models and Agentic AI App—not sit separately from the technical implementation.

<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_18][^5_19][^5_20][^5_21][^5_22][^5_23][^5_24][^5_25][^5_26][^5_27][^5_28][^5_29][^5_30][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://www.ascm.org/topics/demand-supply-planning/

[^5_2]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^5_3]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^5_4]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^5_5]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^5_6]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^5_7]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^5_8]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^5_9]: https://www.hyperbots.com/glossary/sap-demand-planning

[^5_10]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^5_11]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^5_12]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^5_13]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^5_14]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^5_15]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^5_16]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^5_17]: https://o9solutions.com/articles/what-is-demand-planning

[^5_18]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^5_19]: https://keends.com/blog/demand-planning-kpis/

[^5_20]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^5_21]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^5_22]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^5_23]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^5_24]: https://imperiascm.com/blog/demand-forecasting-bias

[^5_25]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^5_26]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^5_27]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^5_28]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^5_29]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^5_30]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284


---

# The attached documents, even though are the requirement documents, I do not want to suddenly start development or start to analyze the documents from a developer/analyst point of view..

What I want you to do is to learn the terms used in these documents and you should be able to understand the domain as well from these perspectives ..
Since, I am asking to develop a development pattern here, the understanding of the domain really matters..

I wouldn't want to hunt in the dark! and then find a way. If I get some understanding already, I will simply make that my base and then improve from there!

So, do a detailed research and come back to me with the knowledge gained aroung the term and the domain and the business!

As I said, I am going this for Milwaukee Electric Tools. So, I want to be able to do this really well!

Yes—this is essential. I will add **snapshot semantics, week-over-week plan movement, target-gap analysis, attainment, missed-target analysis, and plan stability** to the domain model.

The term you are reaching for is usually one of these:

- **Gap to target**
- **Target shortfall**
- **Miss to plan**
- **Plan variance**
- **Deviation from target**
- **Target attainment**
- **Outside tolerance**
- **At risk / off track**

The correct term and formula depend on whether a higher or lower value is desirable.

## Snapshot meaning

A **snapshot** is an immutable representation of what the business knew, expected, or possessed at a specific cutoff time. It lets us answer:

> “Based on the information available last Monday, what did we expect to happen during this target week?”

A useful supply-planning snapshot needs two distinct dates:


| Date | Meaning |
| :-- | :-- |
| Snapshot date | When the plan was captured |
| Target date/week | The future period being planned |
| Actual-event date | When a receipt, shipment, or adjustment happened |
| Comparison date | The business cycle against which performance is evaluated |

For example:

```text
Snapshot captured: Monday, August 3
Target week: August 10–16
Planned receipts: 1,000 units

Actual receipts during August 10–16: 850 units
Receipt shortfall: 150 units
```

The Milwaukee requirements establish a Monday–Sunday planning week, with the Monday-morning snapshot representing the prior end-of-day state. They also require snapshot version identification at SKU × organization × week grain.[^6_1]

## Snapshot categories

I will distinguish these snapshot types:


| Snapshot | What it preserves |
| :-- | :-- |
| Plan-vintage snapshot | What was forecast or planned at that planning cycle |
| Inventory snapshot | On-hand position at a specific cutoff |
| Order snapshot | Open PO, SO, work-order or transfer status at that cutoff |
| Supplier-commit snapshot | What the supplier had confirmed at that time |
| Exception snapshot | Which risks and recommendations existed then |
| Decision snapshot | What the planner approved, rejected or deferred |
| Live-plan snapshot | The most current planning position |
| Actual transaction | A receipt, shipment, adjustment or other event—not technically a snapshot |

The important rule is:

> **A snapshot is “what was believed at the time”; an actual transaction is “what occurred.”**

A current snapshot should not silently replace a historical snapshot. Otherwise, the organization loses its ability to measure plan accuracy, stability and decision quality.

## Week-over-week meanings

“Week over week” can refer to several different comparisons. I will name the comparison explicitly instead of using one ambiguous WoW label.


| Comparison | Business question |
| :-- | :-- |
| Plan vs. plan | How did the expectation for the same target week change between snapshots? |
| Plan vs. actual | Did what happened match the previously frozen expectation? |
| Actual vs. actual | Is operational performance improving from one week to the next? |
| Current plan vs. prior plan | What changed across the entire forward horizon? |
| Target vs. actual | Did performance meet the approved business goal? |
| Confirmed vs. requested | Did the supplier commit to what Milwaukee requested? |

Oracle supports comparing a plan with another plan or an archived version of the same plan using difference, percent difference and absolute percent difference. It requires comparable planning calendars, reinforcing the need to align periods before calculating change.[^6_2]

### Same-bucket comparison

To measure genuine plan movement, compare the **same target week** across different snapshot dates:

```text
Snapshot August 3, target week August 17: 1,000 units
Snapshot August 10, target week August 17: 1,250 units
Plan movement: +250 units
```

This means the expectation for August 17 changed by 250 units.

### Rolling-week comparison

This is different:

```text
Snapshot August 3, target week August 10: 1,000 units
Snapshot August 10, target week August 17: 1,250 units
```

The 250-unit difference may reflect different target weeks—not a plan revision. I will not call that “plan change” unless the periods are truly comparable.

## Plan versus actual

For each metric, plan and actual must use compatible semantics:


| Measure | Planned value | Actual value |
| :-- | :-- | :-- |
| PO receipts | Quantity expected to arrive in target week | Qualifying receipt transactions during that week |
| Receipt timing | Expected receipt week/date | Actual receipt week/date |
| Customer shipments | Planned shipments for target week | Actual shipped fulfillment quantity |
| Ending inventory | Prior projected ending PAB | Actual on-hand at the agreed week-end cutoff |
| Supplier commitment | Requested quantity/date | Supplier-confirmed quantity/date |
| Demand | Previously frozen demand plan | Agreed actual-demand signal |

The uploaded requirements specifically call for prior-plan versus actual comparisons for PO receipts, shipments and ending inventory, followed by variance and root-cause categorization.[^6_1]

## Gap terminology

These terms are related but not interchangeable:


| Term | Recommended meaning |
| :-- | :-- |
| Variance | Signed difference between actual and reference |
| Absolute variance | Magnitude of the difference, ignoring direction |
| Percent variance | Difference relative to the reference |
| Gap to target | Amount still needed to reach a desired target |
| Shortfall | Amount below a minimum or higher-is-better target |
| Excess | Amount above a maximum or inventory target |
| Attainment | Percentage of the target achieved |
| Deviation | Distance from an exact target |
| Miss to plan | Business-friendly unfavorable plan variance |
| Within tolerance | Difference is inside an approved range |
| Off target | Difference is outside tolerance |
| At risk | Target has not yet been missed, but projections indicate it may be |
| Breach | A hard constraint or threshold has been violated |

### Signed variance

A standard convention is:

```text
Variance = Actual - Plan
```

But its business interpretation depends on the metric.

- Actual receipts below plan: generally unfavorable.
- Actual demand above plan: may be commercially favorable but operationally risky.
- Actual inventory above plan: may protect service but create excess inventory.
- Actual cost above plan: generally unfavorable.
- Actual lead time above target: unfavorable.
- Actual fill rate above target: favorable.

Therefore, I will not equate **positive variance** with **good** or **negative variance** with **bad**. Variances must be classified according to the metric’s desired direction. Variance analysis commonly labels outcomes favorable or unfavorable based on their effect on the underlying goal.[^6_3]

## Distance from goal

The most general term for “how far away are we?” is **distance to target** or **performance gap**.

### Higher is better

Examples: fill rate, on-time receipt rate, forecast accuracy.

```text
Target shortfall = max(0, Target - Actual)
Attainment = Actual / Target
```

Example:

```text
On-time target: 85%
Actual: 78%

Gap to target: 7 percentage points
Target attainment: 91.8%
Status: Below target
```

The difference between 85% and 78% is **7 percentage points**, not “7%.”

### Lower is better

Examples: forecast error, late orders, excess inventory, expedite cost.

```text
Target overage = max(0, Actual - Target)
```

Example:

```text
Maximum acceptable forecast error: 15%
Actual forecast error: 22%

Outside target by: 7 percentage points
Status: Target missed
```


### Exact target

Examples: target ending inventory or planned receipt quantity.

```text
Signed variance = Actual - Target
Absolute deviation = |Actual - Target|
```

For inventory, direction remains important:

- Below target may create service risk.
- Above target may create working-capital or obsolescence risk.


### Target range

Often the goal is not one exact number but an acceptable band:

```text
Lower limit ≤ Actual ≤ Upper limit
```

Then:

```text
Shortfall = max(0, Lower limit - Actual)
Excess = max(0, Actual - Upper limit)
```

This is often better for safety stock, inventory coverage and planning tolerances because planners should not react to harmless noise.

## Goal status vocabulary

I recommend a consistent five-state business vocabulary:


| Status | Meaning |
| :-- | :-- |
| On target | Meets goal and is comfortably within tolerance |
| Within tolerance | Misses the exact target slightly but requires no action |
| At risk | Currently acceptable, but projected to breach |
| Target missed | Actual result is outside the approved tolerance |
| Critical breach | Miss is severe, urgent or affects safety stock/service commitments |

For future periods, use **at risk**, not **missed**. A future target cannot yet be missed.

For completed periods:

- **Target achieved**
- **Target missed**
- **Exceeded target**
- **Short of target**

This keeps actual performance separate from projected risk.

## Safety-stock gap

For projected inventory:

```text
Safety-stock gap = PAB - Safety Stock
Shortfall units = max(0, Safety Stock - PAB)
```

Interpretation:


| Result | Meaning |
| :-- | :-- |
| Positive gap | PAB remains above safety stock |
| Zero gap | Exactly at safety stock |
| Negative gap | PAB is below safety stock |
| Increasingly negative gap | Shortage risk is worsening |

Oracle defines an item-below-safety-stock exception when PAB falls below the safety-stock level for the item-organization bucket.[^6_4]

For dashboard language, instead of showing only `-500`, I would show:

> **500 units below safety stock beginning week 36; estimated duration: three weeks.**

That is much more useful to a planner.

## Plan stability

Snapshot-to-snapshot movement also measures **plan stability** or **plan nervousness**.

Useful measures include:

- Absolute plan change by target week.
- Percent plan change.
- Number of revisions to the same target period.
- Directional reversals.
- Changes inside the frozen zone.
- Requested-versus-confirmed movement.
- Number of POs pulled in and then pushed out.
- Post-freeze allocation changes.
- Expedite actions caused by late plan changes.

The Red Keychain requirements explicitly call for frozen-zone violations, post-freeze change tracking and decision fences to prevent continual allocation churn.[^6_5]

A large change far into the future may be manageable. A smaller change inside the supplier or execution fence may be critical. Therefore, plan movement must be evaluated by **planning horizon**:

- Frozen/immediate.
- Near-term execution.
- Tactical.
- Long-term planning.


## Dashboard presentation

For each important KPI, I will aim to show:

```text
Actual | Plan | Target | Variance | Gap | Attainment
Status | Prior week | Trend | Forecast | Root cause
```

For example:


| KPI | Actual | Prior plan | Goal | Result |
| :-- | --: | --: | --: | :-- |
| PO on-time receipt | 78% | 82% | 85% | 7 points below goal |
| Receipt quantity | 8,500 | 10,000 | 10,000 | 1,500-unit shortfall |
| Ending on hand | 12,000 | 14,000 | 13,000–15,000 | 1,000 below range |
| Forecast error | 22% | 18% | ≤15% | 7 points above limit |
| Safety-stock breaches | 34 | 21 | 0 | 13 worse WoW |

Visual conventions will be:

- Neutral colors for ordinary plan movement.
- Green only when direction is genuinely favorable.
- Amber for at-risk or outside-warning tolerance.
- Red for missed targets or hard breaches.
- Arrows labeled with meaning, such as “improving” or “worsening,” rather than relying solely on up/down direction.
- Tooltips showing snapshot date, target period, formula, grain and cutoff.


## Updated domain rule

The operating model now includes:

> Preserve immutable and versioned supply-plan snapshots with clearly separated snapshot date, target period and actual-event date. Distinguish plan-versus-plan, plan-versus-actual, actual-versus-actual and target-versus-actual comparisons. For every KPI, define the desired direction, target, warning tolerance and breach threshold. Report signed variance, absolute deviation, target attainment, shortfall or excess, and favorable/unfavorable interpretation. Use “at risk” for projected future misses and “target missed” only after the performance period is complete. Measure plan stability by comparing the same target bucket across successive snapshots, especially inside frozen and execution horizons.

This will become part of how I interpret every snapshot table, dashboard, Genie question, exception rule and Agentic AI recommendation.

<span style="display:none">[^6_10][^6_100][^6_101][^6_102][^6_103][^6_104][^6_105][^6_106][^6_107][^6_108][^6_109][^6_11][^6_110][^6_111][^6_112][^6_113][^6_114][^6_115][^6_116][^6_117][^6_118][^6_119][^6_12][^6_120][^6_121][^6_122][^6_123][^6_124][^6_125][^6_126][^6_127][^6_128][^6_129][^6_13][^6_130][^6_131][^6_132][^6_133][^6_134][^6_135][^6_136][^6_137][^6_138][^6_139][^6_14][^6_140][^6_141][^6_142][^6_143][^6_144][^6_145][^6_146][^6_147][^6_148][^6_149][^6_15][^6_150][^6_151][^6_152][^6_153][^6_154][^6_155][^6_156][^6_157][^6_158][^6_159][^6_16][^6_160][^6_161][^6_162][^6_163][^6_164][^6_165][^6_166][^6_167][^6_168][^6_169][^6_17][^6_170][^6_171][^6_172][^6_173][^6_174][^6_175][^6_176][^6_177][^6_178][^6_179][^6_18][^6_180][^6_181][^6_182][^6_183][^6_184][^6_185][^6_186][^6_187][^6_188][^6_189][^6_19][^6_190][^6_191][^6_192][^6_193][^6_194][^6_195][^6_196][^6_197][^6_198][^6_199][^6_20][^6_200][^6_201][^6_202][^6_203][^6_204][^6_205][^6_206][^6_207][^6_208][^6_209][^6_21][^6_210][^6_211][^6_212][^6_213][^6_214][^6_215][^6_216][^6_217][^6_218][^6_219][^6_22][^6_220][^6_221][^6_222][^6_223][^6_224][^6_225][^6_226][^6_227][^6_228][^6_229][^6_23][^6_230][^6_231][^6_232][^6_233][^6_234][^6_235][^6_236][^6_237][^6_238][^6_239][^6_24][^6_240][^6_241][^6_242][^6_243][^6_244][^6_245][^6_246][^6_247][^6_248][^6_249][^6_25][^6_250][^6_251][^6_252][^6_253][^6_254][^6_255][^6_256][^6_257][^6_258][^6_259][^6_26][^6_260][^6_261][^6_262][^6_263][^6_264][^6_265][^6_266][^6_267][^6_268][^6_269][^6_27][^6_270][^6_271][^6_272][^6_273][^6_274][^6_275][^6_276][^6_277][^6_278][^6_279][^6_28][^6_280][^6_281][^6_282][^6_283][^6_284][^6_285][^6_29][^6_30][^6_31][^6_32][^6_33][^6_34][^6_35][^6_36][^6_37][^6_38][^6_39][^6_40][^6_41][^6_42][^6_43][^6_44][^6_45][^6_46][^6_47][^6_48][^6_49][^6_50][^6_51][^6_52][^6_53][^6_54][^6_55][^6_56][^6_57][^6_58][^6_59][^6_6][^6_60][^6_61][^6_62][^6_63][^6_64][^6_65][^6_66][^6_67][^6_68][^6_69][^6_7][^6_70][^6_71][^6_72][^6_73][^6_74][^6_75][^6_76][^6_77][^6_78][^6_79][^6_8][^6_80][^6_81][^6_82][^6_83][^6_84][^6_85][^6_86][^6_87][^6_88][^6_89][^6_9][^6_90][^6_91][^6_92][^6_93][^6_94][^6_95][^6_96][^6_97][^6_98][^6_99]</span>

<div align="center">⁂</div>

[^6_1]: 01_Requirements.md

[^6_2]: Actuals_Supply_Plan_Requirements.md

[^6_3]: Red_Keychain_Supply_Planning_Requirements.md

[^6_4]: https://www.milwaukeetool.jobs/career-areas

[^6_5]: https://www.oracle.com/customers/milwaukee-tool/

[^6_6]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^6_7]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^6_8]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^6_9]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^6_10]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^6_11]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^6_12]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^6_13]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^6_14]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^6_15]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^6_16]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^6_17]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^6_18]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^6_19]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^6_20]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^6_21]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^6_22]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^6_23]: https://www.milwaukeetool.com/

[^6_24]: https://www.ttigroup.com/documents/annual-report-2025/

[^6_25]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^6_26]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^6_27]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^6_28]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^6_29]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^6_30]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^6_31]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^6_32]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^6_33]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^6_34]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^6_35]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^6_36]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^6_37]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^6_38]: https://dataintelo.com/report/global-milwaukee-tool-market

[^6_39]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^6_40]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^6_41]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^6_42]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^6_43]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^6_44]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^6_45]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^6_46]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^6_47]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^6_48]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^6_49]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^6_50]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^6_51]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^6_52]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^6_53]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^6_54]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^6_55]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^6_56]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^6_57]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^6_58]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^6_59]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^6_60]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^6_61]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^6_62]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^6_63]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^6_64]: https://docs.databricks.com/aws/en/ldp/concepts

[^6_65]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^6_66]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^6_67]: https://docs.databricks.com/aws/en/ldp/

[^6_68]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^6_69]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^6_70]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^6_71]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^6_72]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^6_73]: https://docs.databricks.com/aws/en/ldp/real-time

[^6_74]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^6_75]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^6_76]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^6_77]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^6_78]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^6_79]: https://docs.databricks.com/aws/en/tables/clustering

[^6_80]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^6_81]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^6_82]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^6_83]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^6_84]: https://docs.databricks.com/aws/en/delta/tutorial

[^6_85]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^6_86]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^6_87]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^6_88]: https://docs.databricks.com/aws/en/mlflow/

[^6_89]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^6_90]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^6_91]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^6_92]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^6_93]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^6_94]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^6_95]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^6_96]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^6_97]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^6_98]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^6_99]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^6_100]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^6_101]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^6_102]: https://docs.databricks.com/gcp/en/languages/overview

[^6_103]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^6_104]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^6_105]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^6_106]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^6_107]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^6_108]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^6_109]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^6_110]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^6_111]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^6_112]: https://docs.databricks.com/aws/en/oltp/projects/

[^6_113]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^6_114]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^6_115]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^6_116]: https://docs.databricks.com/aws/en/dashboards/

[^6_117]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^6_118]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^6_119]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^6_120]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^6_121]: https://docs.databricks.com/aws/en/query-federation/oracle

[^6_122]: https://docs.databricks.com/aws/en/ldp/expectations

[^6_123]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^6_124]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^6_125]: https://docs.databricks.com/aws/en/ldp/concepts/

[^6_126]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^6_127]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^6_128]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^6_129]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^6_130]: https://docs.databricks.com/aws/en/query-federation/networking

[^6_131]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^6_132]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^6_133]: https://docs.databricks.com/aws/en/query-federation/databricks

[^6_134]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^6_135]: https://docs.databricks.com/gcp/en/developers/best-practices

[^6_136]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^6_137]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^6_138]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^6_139]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^6_140]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^6_141]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^6_142]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^6_143]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^6_144]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^6_145]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^6_146]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^6_147]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^6_148]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^6_149]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^6_150]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^6_151]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^6_152]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^6_153]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^6_154]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^6_155]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^6_156]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^6_157]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^6_158]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^6_159]: https://docs.databricks.com/aws/en/developers/best-practices

[^6_160]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^6_161]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^6_162]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^6_163]: https://docs.databricks.com/aws/en/notebooks/testing

[^6_164]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^6_165]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^6_166]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^6_167]: https://docs.databricks.com/aws/en/files/files-recommendations

[^6_168]: https://docs.databricks.com/aws/en/files/workspace-modules

[^6_169]: https://docs.databricks.com/aws/en/release-notes/product/

[^6_170]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^6_171]: https://docs.databricks.com/aws/en/compute/web-terminal

[^6_172]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^6_173]: https://docs.databricks.com/gcp/en/files/workspace

[^6_174]: https://docs.databricks.com/aws/en/volumes/volume-files

[^6_175]: https://docs.databricks.com/aws/en/repos/ci-cd

[^6_176]: https://docs.databricks.com/aws/en/notebooks/share-code

[^6_177]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^6_178]: https://docs.databricks.com/aws/en/repos/limits

[^6_179]: https://docs.databricks.com/aws/en/files/workspace-interact

[^6_180]: https://docs.databricks.com/aws/en/jobs/git

[^6_181]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^6_182]: https://docs.databricks.com/api/jobs/v2/job

[^6_183]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^6_184]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^6_185]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^6_186]: https://docs.databricks.com/aws/en/repos/repos-setup

[^6_187]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^6_188]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^6_189]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^6_190]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^6_191]: https://docs.databricks.com/aws/en/tables/history

[^6_192]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^6_193]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^6_194]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^6_195]: https://docs.databricks.com/aws/en/files/workspace

[^6_196]: https://docs.databricks.com/aws/en/jobs/privileges

[^6_197]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^6_198]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^6_199]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^6_200]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^6_201]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^6_202]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^6_203]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^6_204]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^6_205]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^6_206]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^6_207]: https://docs.databricks.com/aws/en/ai-gateway/

[^6_208]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^6_209]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^6_210]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^6_211]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^6_212]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^6_213]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^6_214]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^6_215]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^6_216]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^6_217]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^6_218]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^6_219]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^6_220]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^6_221]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^6_222]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^6_223]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^6_224]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^6_225]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^6_226]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^6_227]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^6_228]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^6_229]: https://docs.databricks.com/aws/en/agents/

[^6_230]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^6_231]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^6_232]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^6_233]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^6_234]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^6_235]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^6_236]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^6_237]: https://docs.databricks.com/aws/en/machine-learning/

[^6_238]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^6_239]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^6_240]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^6_241]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^6_242]: https://www.hyperbots.com/glossary/sap-demand-planning

[^6_243]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^6_244]: https://www.ascm.org/topics/demand-supply-planning/

[^6_245]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^6_246]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^6_247]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^6_248]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^6_249]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^6_250]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^6_251]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^6_252]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^6_253]: https://o9solutions.com/articles/what-is-demand-planning

[^6_254]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^6_255]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^6_256]: https://keends.com/blog/demand-planning-kpis/

[^6_257]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^6_258]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^6_259]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^6_260]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^6_261]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^6_262]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^6_263]: https://imperiascm.com/blog/demand-forecasting-bias

[^6_264]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^6_265]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^6_266]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^6_267]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^6_268]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^6_269]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^6_270]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^6_271]: https://www.hyperbots.com/glossary/target-gap-analysis

[^6_272]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^6_273]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^6_274]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^6_275]: https://www.ibm.com/think/topics/variance-analysis

[^6_276]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^6_277]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^6_278]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^6_279]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^6_280]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^6_281]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^6_282]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^6_283]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^6_284]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^6_285]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/


---

# and I want you to be also able to convert the business requirements into an understanding of how it will be developed on Databricks. what platform tools will be used, what data model - analytical and transactional will be required.. how latest and greatest features of the platform products can be used .. as an example, but not limited to: lakebase sync, reverse etl, lakebase search BM25 and other pieces like that! like where Genie Agent will be really use ful.. what kinds of questions can be asked and things like that ..

Think about many things that I am not thinking of right now!

Yes. I will add a formal **Business Requirement → Domain Model → Databricks Product Architecture → Production Operation** translation discipline to the Milwaukee Supply Chain Databricks FDE mode.

This means I will neither jump directly from a requirement to code nor automatically map every capability to the newest Databricks feature. I will first model the business decision, analytical history, transactional workflow, actions, identities, latency, and failure consequences—then choose the appropriate platform products.

## Translation method

For each requirement, I will derive the following:

1. **Business capability:** What business process is being enabled?
2. **Decision:** What must a planner understand, decide, approve, or execute?
3. **Domain semantics:** What do plan, actual, target, exception, recommendation, and action mean?
4. **System of record:** Which system owns each state?
5. **Analytical model:** What history, facts, dimensions, snapshots, metrics, and features are required?
6. **Transactional model:** What cases, locks, edits, approvals, and actions must be committed atomically?
7. **Serving model:** What information must the application retrieve interactively?
8. **AI role:** Is the requirement better handled by deterministic logic, SQL, ML, Genie, retrieval, or an agent?
9. **Integration:** What must move between Oracle, the EDW, Databricks, Lakebase, and external services?
10. **Platform mapping:** Which Databricks product implements each responsibility?
11. **Trust model:** Which user or service identity performs the operation?
12. **Quality and operations:** How is it tested, monitored, reconciled, recovered, and promoted?

## Requirement interpretation

The three documents describe related but distinct business capabilities.


| Capability | Business purpose | Primary operating style |
| :-- | :-- | :-- |
| Demand-planning event management | Capture incremental forecasts for non-repeating and repeating customer or sales events | Transactional planning application |
| Actuals supply plan | Compare frozen expectations with receipts, shipments, inventory, and demand outcomes | Historical analytical product |
| Red Keychain planning | Detect exceptions, recommend actions, simulate options, and execute approved supply decisions | Agentic decision-and-action application |

The demand-planning requirements include event status, concurrent edit locking, item-month overrides, customer hierarchy disaggregation, audit history, and publication to Oracle Demand Planning. Those are application and transactional requirements, not merely an analytical table-building exercise.[^7_1]

The Actuals requirements center on immutable weekly plan snapshots, transaction-derived actuals, plan-versus-actual comparisons, accuracy, bias, root causes, and Monday planning workflows.[^7_2]

Red Keychain extends the solution into exception management and execution: requested versus confirmed supply, order-versus-rebalance decisions, PO grouping, probabilistic scenarios, planner-rule capture, Oracle actions, frozen-zone controls, and outcome feedback.[^7_3]

## Logical architecture

```text
Oracle Fusion / EDW / WMS / TMS / MES / Supplier Systems
                         │
                         ▼
       Federation, CDC, APIs, files, or existing ingestion
                         │
                         ▼
               Lakeflow data pipelines
       Bronze → Conformed Silver → Analytical Gold
                         │
         ┌───────────────┼────────────────┐
         ▼               ▼                ▼
   Metric views     ML features       Exception engine
   and dashboards   and forecasts     and recommendations
         │               │                │
         └───────────────┼────────────────┘
                         ▼
            Application-serving data products
                         │
              UC → Lakebase synced tables
                    Reverse ETL
                         │
                         ▼
            Agentic Databricks Supply App
        Genie │ Agent tools │ ML │ Search │ Actions
                         │
                         ▼
                      Lakebase
       Cases │ Overrides │ Approvals │ Locks │ Actions
                         │
              Lakebase Change Data Feed
                         │
                         ▼
        Unity Catalog analytical/audit history
                         │
                         ▼
        Approved APIs → Oracle / WMS / TMS / SCC
```

This separates large-scale history and analytics from low-latency application state without splitting the platform into disconnected products.

## Analytical model

The analytical layer must preserve **business history**, particularly what was known at each planning cycle.

### Core facts

| Fact | Proposed grain | Purpose |
| :-- | :-- | :-- |
| Supply-plan snapshot | Snapshot × item × organization × target week × plan version | Preserve planned supply, demand, inventory, and PAB |
| Demand-plan snapshot | Snapshot × item × customer/channel × organization × target month | Preserve baseline, events, overrides, and consensus |
| Actual receipt | Receipt event or item × organization × week | Measure received quantity and timing |
| Actual shipment | Fulfillment transaction or item × organization × customer × week | Measure shipped demand |
| Inventory snapshot | Item × organization × cutoff date | Preserve on-hand and inventory status |
| Plan-versus-actual | Frozen plan × corresponding actual bucket | Measure variance, attainment, bias, and accuracy |
| Plan movement | Prior snapshot × current snapshot × same target bucket | Measure stability and post-freeze changes |
| Exception snapshot | Detection run × item × organization × exception type | Preserve what was considered risky at that moment |
| Recommendation snapshot | Recommendation version × exception | Preserve what the system recommended and why |
| Action outcome | Action × affected entities × measured outcome | Determine whether the action worked |
| Event forecast | Event × item × customer × month | Analyze incremental event demand |
| Forecast prediction | Model version × item × location/customer × horizon | Preserve forecast and prediction intervals |

The Actuals requirements establish item × organization × week as the principal comparison grain, with Monday–Sunday alignment and Monday-morning snapshots.[^7_2]

### Dimensions

Important conformed dimensions will likely include:

- Item and SKU.
- Product family, platform, category, lifecycle, and transition.
- Inventory organization and distribution center.
- Supplier and supplier site.
- Customer and customer hierarchy.
- Date, fiscal calendar, planning week, and forecast horizon.
- Plan, scenario, version, and snapshot.
- Planner and planning group.
- Purchase order, work order, transfer order, and sales order.
- Exception type, severity, root cause, and action type.
- Unit of measure and currency.
- Event type and event status.
- Model and recommendation version.


### Metric layer

Governed Unity Catalog metric views should define reusable measures such as:

- Planned receipts.
- Actual receipts.
- Receipt shortfall.
- On-time receipt rate.
- PO quantity accuracy.
- Projected available balance.
- Safety-stock gap.
- Demand-plan accuracy.
- Forecast bias.
- Plan movement.
- Post-freeze change rate.
- Exception aging.
- Recommendation acceptance rate.
- Action success rate.
- Planner override rate.
- Forecast value added.
- Excess and obsolete inventory exposure.

Unity Catalog metric views separate measures from grouping fields and make governed metrics reusable from SQL, notebooks, dashboards, Genie Agents, and alerts.[^7_4]

Dashboard-specific metrics can begin as local metric views and be promoted to Unity Catalog after validation.[^7_5][^7_6]

## Transactional model

Lakebase should own operational application state, not merely host copies of analytical tables.

### Candidate tables

```text
planning_event
planning_event_customer
planning_event_item
planning_event_forecast_value
planning_event_assumption
planning_event_lock
planning_event_change_log

exception_case
exception_evidence
exception_assignment
exception_comment
exception_status_history

recommendation
recommendation_alternative
recommendation_evidence
recommendation_rule_execution
recommendation_model_output

scenario
scenario_parameter
scenario_run
scenario_result

approval_request
approval_decision
action_command
action_execution
action_verification
action_compensation
external_system_reference

user_preference
saved_filter
notification_subscription
agent_conversation_context
```

The demand-planning requirements call for one-editor-at-a-time event locks, status-controlled publication, and granular before-and-after audit history. Those require proper transactions, concurrency controls, and immutable change records.[^7_1]

The Red Keychain workflow requires bulk actions, Oracle writeback, planner-rule capture, recommendation outcomes, and feedback into later planning cycles.[^7_3]

### Transaction safeguards

The transactional design will include:

- Primary and foreign keys.
- Unique constraints.
- Row-version or optimistic-concurrency fields.
- Explicit status-transition rules.
- Idempotency keys for actions.
- Outbox records for external integration.
- Before-and-after values.
- Actor and approval identities.
- Effective timestamps.
- External correlation IDs.
- Retry-safe command design.
- Verification and compensation status.
- Schema migrations.
- Point-in-time recovery planning.

Lakebase supports isolated development branches, schema comparisons, and migration-based promotion; changes from a child branch do not automatically alter its parent.[^7_7][^7_8]

## Lakebase synchronization

“Lakebase sync” actually involves two complementary directions.

### Lakehouse to Lakebase

Unity Catalog **synced tables** create managed, read-only Lakebase copies of analytical data for low-latency application queries. Databricks calls this reverse ETL and supports snapshot, triggered, and continuous synchronization modes.[^7_9][^7_10]

Good candidates include:

- Current item master.
- Current supplier attributes.
- Current organization hierarchy.
- Open supply exceptions.
- Current inventory position.
- Current supply outlook.
- Latest forecast.
- Approved metrics at application grain.
- Product transition relationships.
- Eligible transfer opportunities.
- Planner assignment reference data.

These copies should be shaped specifically for application access. Syncing every raw fact or entire EDW table into Lakebase would usually be wasteful and could create unclear ownership.

### Lakebase to lakehouse

Lakebase Change Data Feed captures inserts, updates, and deletes from PostgreSQL and writes them to Unity Catalog managed Delta tables, allowing downstream pipelines and analytics to react to application activity.[^7_11]

Good candidates include:

- Planner overrides.
- Event revisions.
- Exception dispositions.
- Recommendation acceptance or rejection.
- Approval decisions.
- Action execution results.
- User feedback.
- Root-cause assignments.
- Application audit events.
- Forecast publish history.

This creates a valuable closed loop:

```text
Analytics → Recommendation → Planner decision → Live action
    → Outcome → Lakebase CDF → Delta history
    → Evaluation → Improved rule/model/recommendation
```


## Reverse ETL boundaries

Reverse ETL should not be confused with operational writeback.


| Movement | Meaning |
| :-- | :-- |
| Unity Catalog → Lakebase | Serve analytical data to the App |
| Lakebase → Unity Catalog | Analyze transactional changes and outcomes |
| Lakebase/App → Oracle API | Execute an approved business transaction |
| Oracle → Databricks | Confirm the system-of-record result |
| Excel → Unity Catalog | Controlled user data submission, not necessarily operational action |

A Lakebase synced table is read-only in PostgreSQL, so planner edits should go into separate native Lakebase tables rather than attempting to modify the synced copy.[^7_9]

## Search architecture

Lakebase Search can support keyword, vector, or hybrid search inside the operational application. Its BM25 capability uses the `lakebase_text` extension and PostgreSQL `tsvector` query patterns.[^7_12][^7_13]

### BM25 use cases

BM25 is appropriate when exact words, identifiers, and domain terminology matter:

- Find SKU `2804-20`.
- Search for a purchase-order number.
- Find exceptions mentioning “port congestion.”
- Find comments containing a supplier or planner name.
- Find actions involving “pull-in.”
- Search known error messages.
- Find a policy containing “frozen zone.”
- Locate cases associated with a specific model or product family.


### Vector use cases

Semantic search is better when users express meaning with different wording:

- Find previous cases similar to this shortage.
- Find policies related to supplier delivery problems.
- Find planner notes describing comparable transition risks.
- Retrieve procedures relevant to a late inbound shipment.
- Find similar product-launch demand events.


### Hybrid search

A supply-chain App often needs both:

> “Find previous late-receipt exceptions for TTi involving M18 products where planners expedited or rebalanced inventory.”

- BM25 preserves exact names, product codes, and action terms.
- Vector retrieval finds semantically similar notes and cases.
- Structured SQL filters enforce supplier, family, date, severity, and status.

Lakebase Search supports hybrid vector and keyword retrieval, while BM25 is designed for exact-term relevance and identifiers.[^7_13]

Search results must still respect application authorization. A relevant result is not automatically an authorized result.

## Genie’s role

Genie should answer governed analytical questions. It should not be the component that directly updates Oracle or commits an operational decision.

Genie Agents use Unity Catalog datasets, curated semantic definitions, instructions, synonyms, relationships, and SQL examples to interpret business questions.[^7_14][^7_15]

### Strong Genie questions

Examples for the Actuals domain:

- Which A-class SKUs had the largest receipt shortfall last week?
- Which suppliers missed planned receipts for three consecutive weeks?
- Why did ending on-hand fall below projected PAB at organization 2012?
- Show actual versus planned receipts by supplier for the last 13 weeks.
- Which items show persistent under-planning bias?
- How much of this week’s inventory variance came from demand, supply, or adjustments?
- Which planners have the highest post-freeze change rate?
- Where is PO quantity accuracy worsening week over week?

Examples for demand planning:

- How much incremental demand comes from active repeating events next quarter?
- Which events have values materially above the planner baseline?
- Which customers receive the largest event-forecast allocation?
- Which active events contain item-validation warnings?
- How did the current event forecast change from its prior version?
- Which event forecasts were overridden after the Forecast Builder calculation?
- What percentage of incremental demand comes from new-store openings?

Examples for Red Keychain:

- Which stockout exceptions have available inventory at another DC?
- Which PO pull-in recommendations are inside the frozen zone?
- Which exceptions exceed the cost or unit-impact threshold?
- Which suppliers show lead-time drift?
- Which planned orders could be avoided through inventory rebalancing?
- Which recommendations were rejected most often, and why?
- Did approved pull-ins improve fill rate?
- Which old-SKU/new-SKU transitions have overlapping excess inventory?


### Weak Genie use cases

Genie should not independently:

- Change a purchase order.
- Approve a recommendation.
- Override a planner.
- Publish a forecast to Oracle SCC.
- Allocate inventory.
- Release a requisition.
- Alter a safety-stock parameter.
- Declare a root cause without evidence.

Those require the Agentic App, typed tools, permissions, validation, approval, and auditable transactions.

### Genie quality

The Genie Agent should receive curated metric views, narrow domain datasets, business definitions, example SQL, synonyms, and benchmark questions. Databricks supports benchmark suites for measuring response accuracy, and each benchmark can include expected SQL and evaluation guidance.[^7_16][^7_17]

## Agentic App role

The Agentic App becomes the business workflow and orchestration layer.

A planner might ask:

> “Why will SKU X fall below safety stock at DC 2012 in week 38, and what can be done?”

The agent can then:

1. Query governed analytical data.
2. Retrieve the appropriate plan snapshots.
3. Identify demand, receipt, transfer, and inventory contributors.
4. Search similar historical cases.
5. Apply deterministic planning rules.
6. invoke forecasting or risk models.
7. Generate alternatives.
8. Simulate order, transfer, or defer scenarios.
9. Explain assumptions and constraints.
10. Write a recommendation to Lakebase.
11. Request planner approval.
12. Execute an approved API action.
13. Verify Oracle’s response.
14. Monitor the following planning cycle.
15. evaluate whether the recommendation improved the outcome.

MLflow Tracing can capture agent inputs, outputs, intermediate steps, tool calls, latency, and evaluation information for debugging and auditability.[^7_18][^7_19]

## Deterministic versus AI

One of the most important architectural choices is deciding what **not** to delegate to an LLM.


| Requirement | Preferred implementation |
| :-- | :-- |
| Variance calculation | SQL or Spark |
| Safety-stock breach | Deterministic rule |
| Frozen-zone detection | Deterministic rule |
| PO date feasibility | Constraint/business-rule engine |
| Customer disaggregation | Approved mathematical rule |
| Exception priority | Deterministic score, possibly ML-assisted |
| Demand forecast | Statistical/ML model |
| Late-supplier probability | ML or probabilistic model |
| Similar-case search | Hybrid retrieval |
| Root-cause hypothesis | Agent, grounded in evidence |
| Recommendation explanation | Agent |
| Recommendation generation | Rules/optimization/ML plus agent explanation |
| PO writeback | Typed transactional service with approval |
| Conversational analytics | Genie |
| Final business approval | Authorized human or explicit policy |

An LLM should explain and coordinate reliable tools, not replace mathematics, constraints, permissions, or transactions.

## Forecasting and optimization

The platform may eventually require multiple model classes:

- Baseline demand forecasting.
- Incremental event-demand forecasting.
- Forecast confidence or interval estimation.
- Supplier lateness probability.
- Expected receipt-date prediction.
- Lead-time drift detection.
- Stockout-risk prediction.
- Excess and obsolescence risk.
- Recommendation acceptance prediction.
- Root-cause classification.
- Inventory transfer optimization.
- PO order/expedite/defer/cancel optimization.
- Scenario and Monte Carlo simulation.

Databricks Feature Engineering can preserve feature lineage and reuse the same governed features across training and inference. Models can be registered in Unity Catalog and deployed through batch inference or Model Serving based on latency requirements.[^7_20][^7_21]

Weekly network forecasts generally fit batch inference, while interactive scenario scoring or immediate risk assessment may justify Model Serving. Databricks supports registering serverless forecasting results and deploying selected models to serving endpoints.[^7_22]

## Pipeline mapping

| Business need | Databricks implementation |
| :-- | :-- |
| Ingest Oracle/EDW records | Existing ingestion, federation, CDC, files, or supported connectors |
| Incremental transactions | Streaming tables or CDC pipeline |
| Weekly snapshots | Idempotent scheduled Lakeflow pipeline |
| Conformed facts/dimensions | Delta managed tables |
| Complex maintained aggregates | Materialized views |
| Quality rules | Pipeline expectations plus reconciliation tests |
| Monday readiness | Lakeflow Job schedule, dependencies, alerts, and SLA monitoring |
| Current application read model | UC gold tables synchronized into Lakebase |
| Planner changes | Native Lakebase tables |
| Operational audit analytics | Lakebase CDF into Delta |
| Common KPIs | Unity Catalog metric views |
| Dashboard | AI/BI dashboard |
| Natural-language analytics | Genie Agent |
| Agent workflow | Databricks App plus custom tools |
| ML inference | Batch pipelines or Model Serving |
| Foundation model access | Unity AI Gateway |
| Production promotion | Git, DABs, tests, and CI/CD |

Streaming tables are best suited to append-oriented ingestion, while materialized views are intended for maintained transformations, joins, aggregates, and accelerated downstream queries.[^7_23][^7_24][^7_25]

## Data API opportunity

For suitable application operations, the Lakebase Data API can expose PostgREST-compatible CRUD endpoints derived from the PostgreSQL schema. This can reduce custom boilerplate for ordinary database interactions.[^7_26]

However, I would not expose critical Oracle actions as unrestricted generic CRUD. High-risk actions still need a domain service that validates permissions, current state, business constraints, idempotency, approvals, and external-system responses.

## More considerations

The following will now be examined even when they are not stated explicitly.

### Temporal correctness

- Snapshot time versus target time.
- Effective-dated dimensions.
- Late transactions.
- Reopened periods.
- Revisions after freeze.
- Timezone and daylight-saving behavior.
- Backdated Oracle changes.
- Bitemporal “effective at” versus “known at” history.


### Planning semantics

- Requested versus confirmed supply.
- Unconstrained versus constrained plan.
- Gross versus net forecast.
- Baseline versus incremental event forecast.
- Independent versus dependent demand.
- Order versus shipment versus consumption.
- Open versus firm versus released supply.
- Safety stock versus target inventory.
- Planned order versus requisition versus PO.
- Current forecast versus frozen forecast.
- Scenario versus approved plan.


### Operational safety

- Duplicate action prevention.
- Stale recommendation detection.
- Bulk-action partial failure.
- Concurrent planner edits.
- Action rollback and compensation.
- Oracle read-after-write verification.
- Lost updates.
- Manual override precedence.
- Separation of duties.
- Emergency kill switch.
- Read-only degradation if downstream systems fail.


### AI safety

- Hallucinated SKU or PO numbers.
- Unsupported root-cause claims.
- Prompt injection in supplier notes.
- Sensitive data in model prompts.
- Unauthorized cross-planner visibility.
- Incorrect tool selection.
- Overconfident recommendations.
- Model and prompt drift.
- Requirement for evidence citations.
- Human approval thresholds.


### Feedback quality

A rejected recommendation does not necessarily mean that the algorithm was wrong. The planner may know about constraints unavailable to the platform.

The App should therefore capture structured rejection reasons such as:

- Supplier constraint not represented.
- Promotion not loaded.
- Transition rule missing.
- MOQ or truckload constraint.
- Customer commitment.
- Data quality issue.
- Recommendation arrived too late.
- Planner preference.
- System limitation.
- Valid recommendation deferred for business reasons.

This converts “tribal knowledge” into candidate rules, features, and data-quality requirements rather than blindly treating every click as an ML label.

### Nonfunctional requirements

- Freshness.
- End-to-end latency.
- concurrency.
- peak Monday usage.
- SQL and Postgres query latency.
- sync lag.
- action throughput.
- recovery point and recovery time.
- regional availability.
- scale-to-zero cold starts.
- model endpoint cold starts.
- lineage and audit retention.
- cost attribution.
- accessibility and usability.

Lakebase offers branch-based development and point-in-time recovery capabilities, which should be incorporated into the database development and recovery approach.[^7_27][^7_28]

## Development deliverables

For each major business requirement, I will now produce a traceability matrix like this:


| Requirement | Decision | Domain object | Analytical asset | Transactional asset | Platform product | Test |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Compare expected and received PO quantity | Expedite, defer, or investigate | PO receipt variance | Plan-actual fact and metric view | Exception case | Lakeflow, UC, AI/BI | Reconciliation to receipt transactions |
| Capture planner forecast event | Publish incremental demand | Planning event | Event-forecast fact | Event header, lines, lock, audit | App, Lakebase, CDF | Calculation, locking, audit, publish |
| Recommend DC transfer | Rebalance instead of ordering | Network imbalance | Inventory and demand outlook | Recommendation and approval | ML/optimization, App, Lakebase | Feasibility and inventory conservation |
| Execute approved PO change | Update Oracle | Action command | Action-outcome fact | Command, execution, verification | App, Lakebase, Oracle API | Idempotency and read-back |
| Ask why inventory missed plan | Investigate root cause | Plan variance | Metric view and evidence model | Optional saved case | Genie plus Agentic App | Benchmark SQL and evidence check |

## Updated operating principle

The project mode will now include:

> Translate every business requirement into business decisions, domain semantics, systems of record, analytical history, transactional state, serving requirements, AI responsibilities, integration flows, trust boundaries, tests, and operating procedures before choosing implementation tools. Use Delta and Unity Catalog for governed analytical history; Lakebase for transactional workflow state; synced tables for low-latency reverse ETL into the application; Lakebase Change Data Feed for operational events back into the lakehouse; BM25, vector, or hybrid search according to retrieval semantics; metric views for reusable business measures; Genie for governed analytical questions; custom agents for investigation and tool orchestration; deterministic rules and optimization for constraints; MLflow and Unity Catalog for model and agent lifecycle; and typed, approved, idempotent services for live operational actions.

The goal is not just to build a modern Databricks application. It is to create a **closed-loop supply-chain decision system** that can explain what changed, predict what may happen, recommend what to do, execute what is authorized, and learn from the outcome.

<span style="display:none">[^7_29][^7_30][^7_31][^7_32][^7_33][^7_34][^7_35][^7_36][^7_37][^7_38][^7_39][^7_40][^7_41][^7_42][^7_43][^7_44][^7_45][^7_46][^7_47][^7_48][^7_49][^7_50][^7_51][^7_52][^7_53][^7_54][^7_55][^7_56][^7_57][^7_58][^7_59][^7_60][^7_61][^7_62]</span>

<div align="center">⁂</div>

[^7_1]: 01_Requirements.md

[^7_2]: Actuals_Supply_Plan_Requirements.md

[^7_3]: Red_Keychain_Supply_Planning_Requirements.md

[^7_4]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^7_5]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^7_6]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^7_7]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^7_8]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^7_9]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^7_10]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^7_11]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^7_12]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^7_13]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^7_14]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^7_15]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^7_16]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^7_17]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^7_18]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^7_19]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^7_20]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^7_21]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^7_22]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^7_23]: https://docs.databricks.com/aws/en/ldp/concepts/

[^7_24]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^7_25]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^7_26]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^7_27]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^7_28]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^7_29]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^7_30]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^7_31]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^7_32]: https://docs.databricks.com/aws/en/oltp/projects/

[^7_33]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^7_34]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^7_35]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^7_36]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^7_37]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^7_38]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^7_39]: https://docs.databricks.com/api/genie/v1/conversation

[^7_40]: https://docs.databricks.com/aws/en/mlflow/

[^7_41]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^7_42]: https://docs.databricks.com/api/genie/v1

[^7_43]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^7_44]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^7_45]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^7_46]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^7_47]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^7_48]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^7_49]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^7_50]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^7_51]: https://docs.databricks.com/aws/en/ldp/

[^7_52]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^7_53]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^7_54]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^7_55]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^7_56]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^7_57]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^7_58]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^7_59]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^7_60]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^7_61]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^7_62]: https://docs.databricks.com/aws/en/oltp/projects/high-availability


---

# From this attachment, I don't want you to change the domain of the current activity.

Consider this as a learning experience from another domain. But you will not be learning from domain perspective, you will learn from project execution and from technical and Databricks first perspective.

This is a huge discussion between the developer and the AI agent. But this is not very efficient.
Using this, I want you to be able to find all the mistakes, all the patterns that got this activity delayed, inefficient and things like that ..
We don't want to repeat the same mistake here.

I would like for you to also understand the api / front end development as well... if it gets cleared from here. Because, the UI also gives a lot of errors, I want you to understand that it happens and how can we preemptively know that we are not walking into a trap.
I want to be able to use my time efficiently.

Also, I don't want to over engineer!

Yes. I analyzed the workshop conversation strictly as a **technical execution retrospective**, not as a domain example. The main lesson is: the project built too many horizontal platform assets before proving one end-to-end user workflow.

The detailed report identifies the recurring failure patterns and establishes a leaner Databricks-first execution method.[^8_1]

## Major findings

- **Asset creation replaced product validation:** pipelines, tables, dashboards, Genie, ML, Lakebase, APIs, and frontend components existed before one complete user journey was proven.
- **Deployment became the test loop:** package, TypeScript, configuration, resource, and runtime problems were discovered after repeated workspace deployments rather than through local builds and smoke tests.
- **Configuration followed implementation:** SQL Warehouse, Lakebase, Genie, serving endpoint, authentication, and permissions were often resolved only after the code depended on them.
- **Frontend failures were hidden:** swallowed exceptions and generic setup messages concealed actual API or dependency failures.
- **Completion was declared too early:** “created,” “deployed,” “running,” “integrated,” and “UAT-passed” were treated as if they meant the same thing.
- **UI capabilities were described but not demonstrated:** controls existed without durable transactions, read-back confirmation, metric updates, or clearly proven model/Genie integration.
- **Architecture changed reactively:** experiments became serving endpoints, deployment directories were duplicated, and resource strategies changed after failures.
- **Project status lived in the conversation:** repeated audits and extensive context summaries were needed because there was no small, evidence-backed execution ledger.

The export contains 3,828 conversation records across 112 user turns, including 1,170 tool requests, 1,160 tool results, 659 assistant entries, and 13 context summaries. This volume reflects substantial delivery churn for one workshop implementation.[^8_1]

## Better pattern

For Milwaukee supply-chain development, I will use:

> **Probe → Walking skeleton → One vertical business slice → Validate → Add intelligence → Add live actions → Harden and promote**

### Platform probe

Before meaningful feature development:

- Confirm workspace authentication.
- Confirm the approved source folder.
- Identify the acting user and App service principal.
- Run one SQL Warehouse query.
- Perform one Lakebase read and write.
- Invoke one serving endpoint if required.
- Ask one Genie question if required.
- Verify permissions, environment variables, networking, and resource bindings.

This prevents authentication and configuration defects from becoming frontend defects.

### Walking skeleton

The first App version will contain only:

- `/health/live`
- `/health/ready`
- A nonsecret resource-binding diagnostic
- One analytical read
- One Lakebase write
- One read-back confirmation
- Correlation IDs across UI, API, database, and logs

An App process being alive does not prove that Lakebase, SQL, Genie, or Model Serving is ready.

### Vertical slice

A suitable first Milwaukee workflow could be:

> Show the largest PO receipt exception from last week, explain planned versus actual quantities, allow the planner to assign a root cause and approve a follow-up action, store the decision in Lakebase, and display the new state and audit record.

That requires only:

- One governed analytical dataset.
- One exception API.
- One Lakebase workflow schema.
- One details page.
- One approval/writeback operation.
- One audit trail.

We would not add forecasting, hybrid search, reverse ETL, or broad agent functionality until the first slice works—unless one is essential to it.

## Frontend safeguards

Every UI operation will be designed with:

- Loading state.
- Valid empty state.
- Input validation.
- Authorization failure.
- Dependency-unavailable state.
- Unexpected-error state with correlation ID.
- Durable success confirmation.
- Updated data after mutation.
- Action history and provenance.

A button is not complete merely because it renders. Completion means:

> Click → API executes once → Lakebase commits → UI reads back the state → audit appears → downstream metric or status updates.

Databricks recommends testing Apps locally before workspace deployment. It also provides deployment history, logs, runtime environment, installed-package, and resource information for diagnosing deployed applications.[^8_2][^8_3]

## API safeguards

Each endpoint will have an explicit contract:

- Request and response schemas.
- Authentication actor.
- Authorization rule.
- Error codes.
- Idempotency behavior.
- Transaction and concurrency behavior.
- Timeout and retry policy.
- Audit fields.
- Representative success, empty, conflict, permission, and unavailable responses.

The backend should normally stay simple:

```text
HTTP route
  → domain service
  → Lakebase/Databricks/platform client
```

No microservices, generic integration framework, GraphQL layer, or complicated event infrastructure unless scale and team ownership prove that they are needed.

## Deployment safeguards

Before deployment:

1. Verify the canonical source folder.
2. Run locked dependency installation.
3. Build and type-check frontend and backend.
4. Run unit and API tests.
5. Validate `app.yaml`.
6. Confirm declared resources and workspace bindings.
7. Confirm identity and permissions.
8. Run the App locally.
9. Execute a browser smoke test.
10. Record the version being deployed.

After deployment:

1. Check deployment and build status.
2. Inspect runtime logs and environment.
3. Call readiness, not merely liveness.
4. Run a real representative read.
5. Run one safe synthetic write transaction.
6. Verify the database record and audit trail.
7. Confirm the UI reflects the result.

Databricks specifically recommends checking logs, validating `app.yaml`, resolving secrets and environment references, and confirming dependencies when an App fails to deploy or run.[^8_4]

## Resource handling

Databricks resources will be declared before application code assumes them. The App can formally declare dependencies such as SQL Warehouses, Model Serving endpoints, Genie Agents, Jobs, secrets, and volumes; actual workspace resources are then bound during deployment.[^8_5][^8_6]

I will not:

- Hardcode resource IDs throughout the source.
- Allow PostgreSQL clients to silently default to localhost.
- Start as “healthy” when mandatory resources are absent.
- Hide live/fallback behavior from you.
- use a personal workspace folder when the agreed location is shared.
- Duplicate source directories without identifying one canonical version.
- Let the UI suggest a real model or Genie response when it used a fallback.


## Provenance visibility

During development, every intelligent result should reveal its origin:

- `DETERMINISTIC_RULE`
- `SQL_METRIC`
- `FORECAST_MODEL`
- `MODEL_SERVING`
- `GENIE`
- `BM25_SEARCH`
- `HYBRID_SEARCH`
- `AGENT`
- `CACHED`
- `DEMO_FALLBACK`

This would have prevented much of the prior confusion about whether the App was calling a real serving endpoint, using Genie, returning a heuristic, or displaying static data.

## Anti-overengineering rules

For this project:

- One business workflow at a time.
- One canonical application source.
- One frontend framework.
- One backend process initially.
- One transactional database.
- No AI for deterministic calculations.
- No vector search when SQL or BM25 is enough.
- No reverse ETL without a genuine serving need.
- No real-time endpoint for weekly batch predictions.
- No Genie for transactional writebacks.
- No duplication of complete dashboards inside the App without a workflow need.
- No DAB for every exploratory notebook.
- No latest Databricks feature solely for demonstration.
- No “done” without deployed evidence and user acceptance.


## Status vocabulary

I will use these precise states:


| Status | Meaning |
| :-- | :-- |
| Implemented | Code or asset exists |
| Component-tested | Works in isolation |
| Integrated | Connected to its real dependencies |
| Deployed | Running in the target environment |
| Functionally verified | Representative end-to-end test passed |
| UAT-passed | User workflow and acceptance criteria passed |
| Production-ready | Security, operations, recovery, and deployment controls passed |
| Blocked | Cannot proceed; reason and owner identified |

“Done” will mean at least **UAT-passed**, not merely deployed.

## New default behavior

This lesson is now part of Milwaukee Supply Chain Databricks FDE mode:

> Build the smallest working vertical slice before expanding the platform footprint. Prove authentication, permissions, network paths, resource bindings, and real dependencies through minimal probes. Test Apps locally before deployment. Define API contracts before connecting UI controls. Make errors, empty states, provenance, writeback results, and audit history visible. Treat liveness, readiness, integration, UAT, and production readiness as different states. Add Genie, ML, Model Serving, Lakebase synchronization, BM25/vector search, agents, reverse ETL, and live actions only where the business workflow justifies them. Do not overengineer, duplicate implementation paths, or claim completion without evidence.

The full retrospective contains the failure analysis, improved execution lifecycle, UI/API patterns, testing pyramid, deployment gates, and definition of done.

<span style="display:none">[^8_10][^8_100][^8_101][^8_102][^8_103][^8_104][^8_105][^8_106][^8_107][^8_108][^8_109][^8_11][^8_110][^8_111][^8_112][^8_113][^8_114][^8_115][^8_116][^8_117][^8_118][^8_119][^8_12][^8_120][^8_121][^8_122][^8_123][^8_124][^8_125][^8_126][^8_127][^8_128][^8_129][^8_13][^8_130][^8_131][^8_132][^8_133][^8_134][^8_135][^8_136][^8_137][^8_138][^8_139][^8_14][^8_140][^8_141][^8_142][^8_143][^8_144][^8_145][^8_146][^8_147][^8_148][^8_149][^8_15][^8_150][^8_151][^8_152][^8_153][^8_154][^8_155][^8_156][^8_157][^8_158][^8_159][^8_16][^8_160][^8_161][^8_162][^8_163][^8_164][^8_165][^8_166][^8_167][^8_168][^8_169][^8_17][^8_170][^8_171][^8_172][^8_173][^8_174][^8_175][^8_176][^8_177][^8_178][^8_179][^8_18][^8_180][^8_181][^8_182][^8_183][^8_184][^8_185][^8_186][^8_187][^8_188][^8_189][^8_19][^8_190][^8_191][^8_192][^8_193][^8_194][^8_195][^8_196][^8_197][^8_198][^8_199][^8_20][^8_200][^8_201][^8_202][^8_203][^8_204][^8_205][^8_206][^8_207][^8_208][^8_209][^8_21][^8_210][^8_211][^8_212][^8_213][^8_214][^8_215][^8_216][^8_217][^8_218][^8_219][^8_22][^8_220][^8_221][^8_222][^8_223][^8_224][^8_225][^8_226][^8_227][^8_228][^8_229][^8_23][^8_230][^8_231][^8_232][^8_233][^8_234][^8_235][^8_236][^8_237][^8_238][^8_239][^8_24][^8_240][^8_241][^8_242][^8_243][^8_244][^8_245][^8_246][^8_247][^8_248][^8_249][^8_25][^8_250][^8_251][^8_252][^8_253][^8_254][^8_255][^8_256][^8_257][^8_258][^8_259][^8_26][^8_260][^8_261][^8_262][^8_263][^8_264][^8_265][^8_266][^8_267][^8_268][^8_269][^8_27][^8_270][^8_271][^8_272][^8_273][^8_274][^8_275][^8_276][^8_277][^8_278][^8_279][^8_28][^8_280][^8_281][^8_282][^8_283][^8_284][^8_285][^8_286][^8_287][^8_288][^8_289][^8_29][^8_290][^8_291][^8_292][^8_293][^8_294][^8_295][^8_296][^8_297][^8_298][^8_299][^8_30][^8_300][^8_301][^8_302][^8_303][^8_304][^8_305][^8_306][^8_307][^8_308][^8_309][^8_31][^8_310][^8_311][^8_312][^8_313][^8_314][^8_315][^8_316][^8_317][^8_318][^8_319][^8_32][^8_320][^8_321][^8_322][^8_323][^8_324][^8_325][^8_326][^8_327][^8_328][^8_329][^8_33][^8_330][^8_331][^8_332][^8_333][^8_334][^8_335][^8_336][^8_337][^8_338][^8_339][^8_34][^8_340][^8_341][^8_342][^8_343][^8_344][^8_345][^8_346][^8_347][^8_35][^8_36][^8_37][^8_38][^8_39][^8_40][^8_41][^8_42][^8_43][^8_44][^8_45][^8_46][^8_47][^8_48][^8_49][^8_50][^8_51][^8_52][^8_53][^8_54][^8_55][^8_56][^8_57][^8_58][^8_59][^8_60][^8_61][^8_62][^8_63][^8_64][^8_65][^8_66][^8_67][^8_68][^8_69][^8_7][^8_70][^8_71][^8_72][^8_73][^8_74][^8_75][^8_76][^8_77][^8_78][^8_79][^8_8][^8_80][^8_81][^8_82][^8_83][^8_84][^8_85][^8_86][^8_87][^8_88][^8_89][^8_9][^8_90][^8_91][^8_92][^8_93][^8_94][^8_95][^8_96][^8_97][^8_98][^8_99]</span>

<div align="center">⁂</div>

[^8_1]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^8_2]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^8_3]: https://docs.databricks.com/gcp/en/agents/custom-agents/debug-agent

[^8_4]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/view-app-details

[^8_5]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/key-concepts

[^8_6]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^8_7]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^8_8]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices

[^8_9]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime

[^8_10]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets

[^8_11]: https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial

[^8_12]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/deploy

[^8_13]: https://docs.databricks.com/api/apps/v1/app

[^8_14]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-node

[^8_15]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-apps

[^8_16]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^8_17]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/connect-local

[^8_18]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api

[^8_19]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/model-serving

[^8_20]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^8_21]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^8_22]: https://docs.databricks.com/api/model-serving/v1/serving-endpoint

[^8_23]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^8_24]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^8_25]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^8_26]: https://docs.databricks.com/api/jobs/v2/run

[^8_27]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^8_28]: https://docs.databricks.com/aws/en/machine-learning/model-serving/store-env-variable-model-serving

[^8_29]: https://docs.databricks.com/gcp/en/machine-learning/model-serving/manage-serving-endpoints

[^8_30]: https://docs.databricks.com/aws/en/oltp/projects/automate-with-terraform

[^8_31]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^8_32]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^8_33]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^8_34]: https://docs.databricks.com/aws/en/ldp/concepts

[^8_35]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^8_36]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^8_37]: https://docs.databricks.com/aws/en/ldp/

[^8_38]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^8_39]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^8_40]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^8_41]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^8_42]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^8_43]: https://docs.databricks.com/aws/en/ldp/real-time

[^8_44]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^8_45]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^8_46]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^8_47]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^8_48]: https://docs.databricks.com/aws/en/tables/clustering

[^8_49]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^8_50]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^8_51]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^8_52]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^8_53]: https://docs.databricks.com/aws/en/delta/tutorial

[^8_54]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^8_55]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^8_56]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^8_57]: https://docs.databricks.com/aws/en/mlflow/

[^8_58]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^8_59]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^8_60]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^8_61]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^8_62]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^8_63]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^8_64]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^8_65]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^8_66]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^8_67]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^8_68]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^8_69]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^8_70]: https://docs.databricks.com/gcp/en/languages/overview

[^8_71]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^8_72]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^8_73]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^8_74]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^8_75]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^8_76]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^8_77]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^8_78]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^8_79]: https://docs.databricks.com/aws/en/oltp/projects/

[^8_80]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^8_81]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^8_82]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^8_83]: https://docs.databricks.com/aws/en/dashboards/

[^8_84]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^8_85]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^8_86]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^8_87]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^8_88]: https://docs.databricks.com/aws/en/query-federation/oracle

[^8_89]: https://docs.databricks.com/aws/en/ldp/expectations

[^8_90]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^8_91]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^8_92]: https://docs.databricks.com/aws/en/ldp/concepts/

[^8_93]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^8_94]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^8_95]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^8_96]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^8_97]: https://docs.databricks.com/aws/en/query-federation/networking

[^8_98]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^8_99]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^8_100]: https://docs.databricks.com/aws/en/query-federation/databricks

[^8_101]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^8_102]: https://docs.databricks.com/gcp/en/developers/best-practices

[^8_103]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^8_104]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^8_105]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^8_106]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^8_107]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^8_108]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^8_109]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^8_110]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^8_111]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^8_112]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^8_113]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^8_114]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^8_115]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^8_116]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^8_117]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^8_118]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^8_119]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^8_120]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^8_121]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^8_122]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^8_123]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^8_124]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^8_125]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^8_126]: https://docs.databricks.com/aws/en/developers/best-practices

[^8_127]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^8_128]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^8_129]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^8_130]: https://docs.databricks.com/aws/en/notebooks/testing

[^8_131]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^8_132]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^8_133]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^8_134]: https://docs.databricks.com/aws/en/files/files-recommendations

[^8_135]: https://docs.databricks.com/aws/en/files/workspace-modules

[^8_136]: https://docs.databricks.com/aws/en/release-notes/product/

[^8_137]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^8_138]: https://docs.databricks.com/aws/en/compute/web-terminal

[^8_139]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^8_140]: https://docs.databricks.com/gcp/en/files/workspace

[^8_141]: https://docs.databricks.com/aws/en/volumes/volume-files

[^8_142]: https://docs.databricks.com/aws/en/repos/ci-cd

[^8_143]: https://docs.databricks.com/aws/en/notebooks/share-code

[^8_144]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^8_145]: https://docs.databricks.com/aws/en/repos/limits

[^8_146]: https://docs.databricks.com/aws/en/files/workspace-interact

[^8_147]: https://docs.databricks.com/aws/en/jobs/git

[^8_148]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^8_149]: https://docs.databricks.com/api/jobs/v2/job

[^8_150]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^8_151]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^8_152]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^8_153]: https://docs.databricks.com/aws/en/repos/repos-setup

[^8_154]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^8_155]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^8_156]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^8_157]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^8_158]: https://docs.databricks.com/aws/en/tables/history

[^8_159]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^8_160]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^8_161]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^8_162]: https://docs.databricks.com/aws/en/files/workspace

[^8_163]: https://docs.databricks.com/aws/en/jobs/privileges

[^8_164]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^8_165]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^8_166]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^8_167]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^8_168]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^8_169]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^8_170]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^8_171]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^8_172]: https://docs.databricks.com/aws/en/ai-gateway/

[^8_173]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^8_174]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^8_175]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^8_176]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^8_177]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^8_178]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^8_179]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^8_180]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^8_181]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^8_182]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^8_183]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^8_184]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^8_185]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^8_186]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^8_187]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^8_188]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^8_189]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^8_190]: https://docs.databricks.com/aws/en/agents/

[^8_191]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^8_192]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^8_193]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^8_194]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^8_195]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^8_196]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^8_197]: https://docs.databricks.com/aws/en/machine-learning/

[^8_198]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^8_199]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^8_200]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^8_201]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^8_202]: https://www.hyperbots.com/glossary/sap-demand-planning

[^8_203]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^8_204]: https://www.ascm.org/topics/demand-supply-planning/

[^8_205]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^8_206]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^8_207]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^8_208]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^8_209]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^8_210]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^8_211]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^8_212]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^8_213]: https://o9solutions.com/articles/what-is-demand-planning

[^8_214]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^8_215]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^8_216]: https://keends.com/blog/demand-planning-kpis/

[^8_217]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^8_218]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^8_219]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^8_220]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^8_221]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^8_222]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^8_223]: https://imperiascm.com/blog/demand-forecasting-bias

[^8_224]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^8_225]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^8_226]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^8_227]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^8_228]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^8_229]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^8_230]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^8_231]: 01_Requirements.md

[^8_232]: Actuals_Supply_Plan_Requirements.md

[^8_233]: Red_Keychain_Supply_Planning_Requirements.md

[^8_234]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^8_235]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^8_236]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^8_237]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^8_238]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^8_239]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^8_240]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^8_241]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^8_242]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^8_243]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^8_244]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^8_245]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^8_246]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^8_247]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^8_248]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^8_249]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^8_250]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^8_251]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^8_252]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^8_253]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^8_254]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^8_255]: https://www.milwaukeetool.jobs/career-areas

[^8_256]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^8_257]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^8_258]: https://dataintelo.com/report/global-milwaukee-tool-market

[^8_259]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^8_260]: https://www.milwaukeetool.com/

[^8_261]: https://www.oracle.com/customers/milwaukee-tool/

[^8_262]: https://www.ttigroup.com/documents/annual-report-2025/

[^8_263]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^8_264]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^8_265]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^8_266]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^8_267]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^8_268]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^8_269]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^8_270]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^8_271]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^8_272]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^8_273]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^8_274]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^8_275]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^8_276]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^8_277]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^8_278]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^8_279]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^8_280]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^8_281]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^8_282]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^8_283]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^8_284]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^8_285]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^8_286]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^8_287]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^8_288]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^8_289]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^8_290]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^8_291]: https://www.hyperbots.com/glossary/target-gap-analysis

[^8_292]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^8_293]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^8_294]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^8_295]: https://www.ibm.com/think/topics/variance-analysis

[^8_296]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^8_297]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^8_298]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^8_299]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^8_300]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^8_301]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^8_302]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^8_303]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^8_304]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^8_305]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/

[^8_306]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^8_307]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^8_308]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^8_309]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^8_310]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^8_311]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^8_312]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^8_313]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^8_314]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^8_315]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^8_316]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^8_317]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^8_318]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^8_319]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^8_320]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^8_321]: https://docs.databricks.com/api/genie/v1/conversation

[^8_322]: https://docs.databricks.com/api/genie/v1

[^8_323]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^8_324]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^8_325]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^8_326]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^8_327]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^8_328]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^8_329]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^8_330]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^8_331]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^8_332]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^8_333]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^8_334]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^8_335]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^8_336]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^8_337]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^8_338]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^8_339]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^8_340]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^8_341]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^8_342]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^8_343]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^8_344]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^8_345]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^8_346]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^8_347]: https://docs.databricks.com/aws/en/oltp/projects/high-availability


---

# I also want you to be able to understand the granularity, the joins, aggregations, window functions, weekly snapshots, kimnbal model, start schema - snowflake schema ..

and all of the warehousing concepts within the realm of supply chain and milwaukee electric tools

Absolutely. I will add **Supply-Chain Dimensional Modeling and Data Warehousing expertise** to Milwaukee Supply Chain Databricks FDE mode.

And yes—the intended terms are **Kimball modeling** and **star schema**. The most important principle will be: **declare exactly what one row represents before designing joins, dimensions, measures, SQL, pipelines, dashboards, Genie, or ML features.** Kimball describes grain as the binding contract of a fact table and recommends defining the business process, declaring the grain, choosing dimensions, and then selecting facts.[^9_1][^9_2][^9_3]

## Grain first

I will never describe grain merely as a list of keys such as `item_key + organization_key + week_key`. The grain must be a business sentence:

> One row represents the supply plan for one item, at one inventory organization, for one target week, as seen in one planning snapshot and plan version.

That is different from:

> One row represents one receipt transaction against one PO line at one receiving organization.

Those facts may eventually be compared, but they do **not** begin at the same grain.

The supplied requirements already contain several distinct grains.[^9_4][^9_5]


| Business process | Correct atomic grain |
| :-- | :-- |
| Supply-plan snapshot | One item × organization × plan date × snapshot date × plan/version |
| PO receipt | One receipt transaction event, potentially by PO line, item and organization |
| Sales shipment | One shipment/fulfillment event per order line |
| Inventory snapshot | One item × organization × snapshot date, possibly including subinventory, lot or status |
| Demand-planning event | One event × item × customer leaf × forecast month |
| Weekly plan versus actual | One item × organization × week × selected plan vintage |
| Supply exception | One detected exception instance × item/location × evaluation timestamp |
| Planner action | One action or recommendation decision against an exception |
| Order lifecycle | One order or order line updated through defined milestones |

The requirements identify the planned-versus-actual comparison grain as SKU–organization–week, while the receipt and shipment actuals originate from more detailed transaction facts. They also identify inventory as a point-in-time position rather than an additive transaction.[^9_4]

## Preserve atomic facts

A weekly comparison table will be useful, but it should not replace the underlying atomic facts.

```text
Atomic facts
├── PO receipt transactions
├── Sales shipment transactions
├── Inventory movement transactions
├── Inventory daily snapshots
├── Supply-plan snapshots
├── Demand-plan snapshots
└── Exception and action events
            │
            ▼
Conformed weekly layer
├── Weekly receipt actuals
├── Weekly shipment actuals
├── End-of-week inventory
├── Prior-vintage weekly plan
└── Plan-versus-actual comparison
```

Kimball recommends starting with atomic-grain facts because they support unanticipated questions; derived aggregate facts should be created for common query patterns and performance, not as a substitute for atomic history.[^9_6][^9_3]

## Fact types

I will recognize and deliberately apply the three primary Kimball fact patterns.[^9_1][^9_6]


| Fact type | Supply-chain use | Row behavior |
| :-- | :-- | :-- |
| Transaction fact | Receipt, shipment, inventory movement, order change or planner action | Insert one row for each event |
| Periodic snapshot | Daily inventory, weekly supply plan, monthly forecast or supplier scorecard | Insert one row for each defined period and entity |
| Accumulating snapshot | PO, sales-order fulfillment, exception-resolution or requisition-to-receipt lifecycle | Update one row as milestones occur |

A supply-chain model often needs all three. For example, inventory movement transactions explain **why** inventory changed, periodic inventory snapshots show **how much** inventory existed, and an accumulating snapshot measures how long an order took to progress through its lifecycle.[^9_7][^9_8]

## Weekly snapshot semantics

“Weekly snapshot” is incomplete unless the model identifies several different dates.


| Date role | Meaning |
| :-- | :-- |
| `snapshot_date` | When the system captured the plan or state |
| `target_week_start` | Week for which the plan applies |
| `transaction_date` | When a receipt, shipment or movement occurred |
| `expected_receipt_date` | When the PO was planned to arrive |
| `actual_receipt_date` | When it actually arrived |
| `week_end_date` | Point used for ending inventory |
| `source_extract_timestamp` | When source data was extracted |
| `pipeline_processed_timestamp` | When Databricks processed it |

The requirements currently define a Monday-to-Sunday planning week, with the Monday-morning snapshot representing the prior Sunday end-of-day state. The intended comparison uses the prior planning snapshot for the plan, Monday-to-Sunday transactions for weekly flows, and an end-of-week position for inventory actuals.[^9_4]

The basic comparison will therefore be:

```text
Plan:
  Snapshot captured on prior Monday
  Target period = following Monday through Sunday

Actual flow:
  Sum eligible transactions during the target week

Actual balance:
  Select the approved end-of-week snapshot

Comparison:
  Same item + organization + target week
  while retaining the original plan vintage
```

I will keep `snapshot_date` and `target_week` separate. Otherwise, a query may accidentally compare a plan generated this week for a future period with an actual from the same calendar week.

## Snapshot history

A plan snapshot should be immutable as a planning vintage. The new plan can supersede it operationally, but it must not erase what planners believed at the earlier decision point.

This enables questions such as:

- What did we expect one week before execution?
- How did the plan change between Monday snapshots?
- Did planner overrides improve results?
- Which suppliers were repeatedly late relative to the original plan?
- How did forecast quality change by planning lag?
- Did a late source correction change the reported actual?

For late-arriving source data, I will distinguish:

- Original snapshot.
- Restated/corrected snapshot.
- Latest operational view.
- Official performance-measurement version.
- Data-arrival timestamp.

That avoids silently rewriting history while still allowing corrected reporting.

## Measure behavior

I will classify every measure according to how it may be aggregated.


| Measure | Across items/orgs | Across time | Correct handling |
| :-- | --: | --: | :-- |
| Receipt quantity | Sum | Sum | Fully additive |
| Shipped quantity | Sum | Sum | Fully additive |
| Demand quantity | Usually sum | Usually sum | Confirm demand definition |
| Inventory movement quantity | Sum | Sum | Signed additive event |
| On-hand balance | Sum at same instant | Do not sum | End-of-period or point-in-time |
| Projected available balance | Sum with constraints | Do not sum | Snapshot/as-of logic |
| Safety stock | Usually sum at same grain | Do not sum blindly | Approved snapshot |
| Forecast quantity | Sum within same vintage | Not across vintages | Filter to one snapshot/version |
| Forecast accuracy percentage | Do not sum | Do not sum | Recalculate from components |
| On-time percentage | Do not sum | Do not sum | Sum numerator and denominator, then divide |
| Unit cost | Usually not additive | Not additive | Weighted average or defined valuation |
| Extended inventory value | Sum at same snapshot | Do not sum over time | Quantity × valid cost |

Inventory balances are **semi-additive**: they can normally be totaled across products or locations at the same point in time, but adding Monday, Tuesday, and Wednesday inventory produces a meaningless result. Period-end inventory therefore requires an as-of filter or functions such as `LAST_VALUE`, not `SUM` across dates.[^9_9][^9_10]

For ratios, I will preserve numerators and denominators:

```text
Correct:
  total_on_time_receipts / total_expected_receipts

Usually incorrect:
  average(location_on_time_percentage)
```


## Join discipline

I will treat joins as business relationships, not merely matching column names.

Before writing a join, I will document:

- Left and right grains.
- Expected cardinality: 1:1, 1:M, M:1 or M:M.
- Natural and surrogate keys.
- Effective-date requirements.
- Null and unknown-member handling.
- Expected unmatched percentage.
- Whether the join can multiply measures.
- Whether either side must first be aggregated or deduplicated.
- Reconciliation totals before and after the join.


### Fact-to-dimension joins

A receipt fact may join to:

- Item dimension.
- Inventory-organization dimension.
- Supplier dimension.
- PO status or transaction-type dimension.
- Multiple role-playing date dimensions.
- Planner or buyer dimension.
- Currency and unit-of-measure dimensions.

For historical SCD Type 2 dimensions, the business key alone is insufficient. The transaction must join to the dimension row valid at the event or snapshot time:

```sql
fact.item_id = dimension.item_id
AND fact.event_ts >= dimension.effective_from
AND fact.event_ts < dimension.effective_to
```

When an EDW already provides the correct surrogate dimension key on the fact, I will generally reuse it rather than reconstruct history.

### Fact-to-fact comparisons

I will not directly join detailed receipts, shipments, inventory snapshots, and plan rows and then aggregate. That creates fanout and can multiply quantities.

The safer pattern is:

```text
Aggregate plan independently
        │
Aggregate receipts independently
        │
Aggregate shipments independently
        │
Select end-of-week inventory independently
        │
Join the conformed results at SKU × Org × Week
```

For cross-process analysis, Kimball’s conformed-dimension approach groups each fact independently by shared dimensions and then compares those aggregates. Conformed dimensions allow multiple business-process facts to use consistent product, organization, supplier, customer, and date definitions.[^9_11][^9_12]

## Sparse comparisons

The supplied plan-versus-actual requirements describe a scaffold pattern:

1. Identify the complete item–organization–week key set.
2. Combine it with the required comparison periods.
3. Aggregate each source.
4. Left join each aggregate to the scaffold.
5. Preserve keys that exist on only one side.
6. Use window functions or conditional aggregation to expose comparison values.[^9_4]

This matters because:

- An actual receipt may occur with no corresponding planned receipt.
- A planned receipt may have no actual transaction.
- A new SKU may exist in the latest snapshot but not the prior snapshot.
- A discontinued SKU may exist only in historical data.
- A location may contain inventory without current demand.

An inner join would hide exactly the exceptions that planners need to see.

## Window functions

I will use window functions deliberately for supply-chain calculations such as:


| Function pattern | Supply-chain use |
| :-- | :-- |
| `ROW_NUMBER()` | Select latest valid record or deduplicate source events |
| `LAG()` | Compare current week with prior week |
| `LEAD()` | Identify next expected supply or demand period |
| `FIRST_VALUE()` | Capture initial plan or opening position |
| `LAST_VALUE()` | Obtain ending balance with the correct frame |
| Running `SUM()` | Cumulative demand, supply or inventory movement |
| Rolling `AVG()` | Moving demand or lead-time average |
| `RANK()` | Prioritize exceptions by business impact |
| `PERCENT_RANK()` | Find unusually severe suppliers or SKUs |
| Conditional window aggregates | Pivot plan vintages into current/prior columns |
| Gap-and-island logic | Detect consecutive shortage or late-supply periods |

I will pay particular attention to the window frame. For example, `LAST_VALUE()` can return the current row rather than the last row in a partition unless the frame is explicitly defined.

```sql
LAST_VALUE(on_hand_qty) OVER (
  PARTITION BY item_key, organization_key, week_start
  ORDER BY snapshot_ts
  ROWS BETWEEN UNBOUNDED PRECEDING
           AND UNBOUNDED FOLLOWING
)
```

However, if multiple records remain after this calculation, I will still reduce to one intended weekly row rather than let repeated end-of-week balances enter downstream sums.

## Star schema default

For the curated Gold and semantic layer, the default will be a **star schema**:

```text
                 dim_supplier
                      │
dim_date ── fct_po_receipt ── dim_item
                      │
               dim_organization
                      │
                  dim_planner
```

Databricks describes star schemas as fact tables connected to descriptive dimensions through keys; the structure gives each table a clear responsibility and is easier for analysts and BI tools to query.[^9_13]

A star schema will normally be best for:

- AI/BI dashboards.
- Genie.
- Metric views.
- Planner exploration.
- Reusable supply-chain KPIs.
- Data science feature preparation.
- Application read models.


## Snowflake selectively

I will use a snowflake schema only when normalizing a hierarchy provides a real maintenance or governance benefit.

Possible candidates include:

- Item → product line → category → business unit.
- Organization → region → country.
- Customer leaf → channel → geography.
- Supplier site → supplier → parent supplier.
- Component → subassembly → finished product.

But I will not make every dashboard or Genie query traverse six hierarchy tables unnecessarily. Frequently used hierarchy attributes can be exposed in a flattened conformed dimension or semantic view while the mastered hierarchy remains normalized underneath.

The rule will be:

> **Normalize where governance demands it; present a star where analytics benefits from it.**

## Many-to-many relationships

Supply chain contains unavoidable many-to-many relationships:

- One item may have multiple qualified suppliers.
- One supplier may provide many items.
- One component may support multiple finished goods.
- One finished good or kit may contain multiple components.
- One demand-planning event may affect multiple customers and items.
- One PO recommendation may address several exceptions.
- One exception may have several contributing root causes.
- Inventory may be eligible to serve multiple demand nodes.

I will not flatten these relationships into comma-separated fields or make direct many-to-many joins that multiply facts. Bridge tables will be used where appropriate; Kimball uses bridge tables to represent a fact or dimensional entity associated with multiple dimension members.[^9_14]

Candidate bridges include:

```text
bridge_item_supplier
bridge_product_component
bridge_kit_item
bridge_event_customer
bridge_exception_root_cause
bridge_recommendation_exception
bridge_inventory_demand_eligibility
```

Allocation weights will be included only where the business has a valid allocation rule. A bridge without an allocation method must not be used to sum a measure across its members.

## Conformed dimensions

The Milwaukee supply-chain warehouse should establish a small set of governed dimensions used consistently across demand, planning, procurement, manufacturing, inventory, shipping, exceptions, and actions:

- Date and planning calendar.
- Item/SKU.
- Product hierarchy.
- Inventory organization and distribution center.
- Supplier and supplier site.
- Customer and customer hierarchy.
- Planner, buyer and organizational ownership.
- Plan, scenario and forecast vintage.
- Purchase order and sales order as degenerate or supporting dimensions.
- Unit of measure.
- Currency.
- Exception type and root cause.
- Action and approval status.
- Source system.

Kimball’s bus architecture uses shared conformed dimensions to integrate separately delivered business-process stars without requiring one giant fact table.[^9_11]

## Supply-chain bus matrix

A preliminary Milwaukee-oriented bus matrix would look like this:


| Business process | Date | Item | Org | Supplier | Customer | Planner | Plan/vintage |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| Demand plan | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Supply-plan snapshot | ✓ | ✓ | ✓ | ✓ |  | ✓ | ✓ |
| PO receipt | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |
| Sales shipment | ✓ | ✓ | ✓ |  | ✓ |  |  |
| Inventory snapshot | ✓ | ✓ | ✓ |  |  | ✓ |  |
| Inventory movement | ✓ | ✓ | ✓ | Optional | Optional |  |  |
| Forecast event | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Exception | ✓ | ✓ | ✓ | Optional | Optional | ✓ | ✓ |
| Planner action | ✓ | ✓ | ✓ | Optional | Optional | ✓ | Optional |

This is an architectural starting point, not a claim that Milwaukee’s existing EDW uses these exact definitions.

## Databricks implementation

Databricks-native implementation will generally use:

- Delta tables for facts and dimensions.
- Lakeflow pipelines for incremental transformations.
- Streaming tables for append-oriented events.
- Materialized views for maintained dimensions and aggregates where appropriate.
- Unity Catalog for governance and lineage.
- Metric views for reusable business measures.
- Lakebase for transactional planner actions and application state.
- Gold stars or semantic views for AI/BI and Genie.
- Liquid clustering based on demonstrated filter and join patterns rather than legacy partition habits.

Databricks recommends liquid clustering as the current data-layout approach and advises selecting a small number of high-value clustering columns.[^9_15][^9_16][^9_17]

Clustering will be determined after examining:

- Table size and growth.
- Common date filters.
- Item and organization selectivity.
- Join keys.
- Query profile.
- Data-skipping effectiveness.
- Write frequency.
- Whether the table is atomic or aggregated.

I will not mechanically cluster every table by every foreign key.

## Modeling contract

Before writing transformation SQL, I will now produce a compact contract like this:

```text
Business process:
PO receipt performance

Atomic grain:
One receiving transaction event against one PO schedule/line,
item, and receiving organization

Weekly analytical grain:
One item × organization × supplier × Monday-start week

Plan vintage:
Prior Monday approved supply-plan snapshot

Actual event date:
Receipt transaction date

Measures:
Expected receipt quantity
Received quantity
Returned quantity
Net received quantity
Days early/late
Receipt cost impact

Additivity:
Quantities additive
Timing and percentages non-additive
Inventory balances excluded from temporal sums

Join rules:
Point-in-time item and supplier resolution
Aggregate before joining plan and actual
Preserve plan-only and actual-only rows

Quality controls:
Unique receipt event
Valid item and organization
No unexplained fanout
Source-to-target quantity reconciliation
```


## New default behavior

From now on, Milwaukee Supply Chain Databricks FDE mode also includes:

> Apply Kimball dimensional-design discipline within the Milwaukee supply-chain context. Start from the business process and declare a precise grain before selecting dimensions, facts, joins, aggregations, or tables. Preserve atomic transactions and immutable plan vintages; derive weekly comparison facts without replacing source-level history. Distinguish transaction, periodic-snapshot, and accumulating-snapshot facts. Treat inventory and other balances as semi-additive. Aggregate independent facts to a conformed grain before joining them. Validate join cardinality and prevent fanout. Use scaffolds to preserve plan-only and actual-only conditions. Apply role-playing dates, point-in-time SCD joins, conformed dimensions, bridges, and window functions deliberately. Prefer query-facing star schemas, selectively normalize governed hierarchies, and use Databricks-native Delta, Lakeflow, Unity Catalog, metric views, and evidence-based physical optimization.

Most importantly, I will not begin with a large SQL statement. I will first establish:

1. What business process is being measured?
2. What does one source row represent?
3. What should one target row represent?
4. Which dates and plan vintages govern the comparison?
5. Which measures can be summed—and across which dimensions?
6. What cardinality should every join produce?
7. What reconciliation proves the result is correct?

That will prevent us from getting technically impressive but numerically incorrect supply-chain results.

<span style="display:none">[^9_18][^9_19][^9_20][^9_21][^9_22][^9_23][^9_24][^9_25][^9_26][^9_27][^9_28][^9_29][^9_30][^9_31][^9_32]</span>

<div align="center">⁂</div>

[^9_1]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/

[^9_2]: https://www.kimballgroup.com/2003/03/declaring-the-grain/

[^9_3]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/

[^9_4]: Actuals_Supply_Plan_Requirements.md

[^9_5]: 01_Requirements.md

[^9_6]: https://www.kimballgroup.com/2008/11/fact-tables/

[^9_7]: https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/

[^9_8]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/

[^9_9]: https://docs.thoughtspot.com/cloud/26.8.0.cl/semi-additive-measures.html

[^9_10]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-2-dimensional-modeling-core/fact-tables-fundamentals

[^9_11]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/

[^9_12]: https://www.kimballgroup.com/2005/12/the-matrix-revisited/

[^9_13]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^9_14]: https://www.kimballgroup.com/2012/02/design-tip-142-building-bridges/

[^9_15]: https://www.databricks.com/blog/five-simple-steps-for-implementing-a-star-schema-in-databricks-with-delta-lake

[^9_16]: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering

[^9_17]: https://docs.databricks.com/aws/en/tables/clustering

[^9_18]: Red_Keychain_Supply_Planning_Requirements.md

[^9_19]: https://www.holistics.io/blog/the-three-types-of-fact-tables/

[^9_20]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-4-complex-fact-table-patterns/accumulating-snapshot-fact-tables

[^9_21]: https://www.kimballgroup.com/2012/05/design-tip-145-time-stamping-accumulating-snapshot-fact-tables/

[^9_22]: https://dev.to/alexmercedcoder/dimensional-modeling-facts-dimensions-and-grains-3obm

[^9_23]: https://www.linkedin.com/posts/jrlasak\_%F0%9D%97%9F%F0%9D%97%B6%F0%9D%97%BE%F0%9D%98%82%F0%9D%97%B6%F0%9D%97%B1-%F0%9D%97%96%F0%9D%97%B9%F0%9D%98%82%F0%9D%98%80%F0%9D%98%81%F0%9D%97%B2%F0%9D%97%BF%F0%9D%97%B6%F0%9D%97%BB%F0%9D%97%B4-%F0%9D%98%83%F0%9D%98%80-%F0%9D%97%AD-%F0%9D%97%A2%F0%9D%97%BF%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF-activity-7445032276314238976-c6EB

[^9_24]: https://kimballgroup.forumotion.net/t1496-difference-between-factless-fact-and-bridge-table

[^9_25]: https://bigbear.ai/blog/bridge-tables-deep-dive/

[^9_26]: https://www.reddit.com/r/dataengineering/comments/1pbro6t/kimball_confusion_semi_additive_vs_fully_additive/

[^9_27]: https://datadef.io/guides/en/dimensional-modeling

[^9_28]: https://community.sisense.com/forum/how-tos-faqs-43/topic/many-to-many-multivalued-dimension-4698/

[^9_29]: https://arxiv.org/html/2606.27571v2

[^9_30]: https://datawarehouseinfo.com/practice/advanced-dimensional-modeling/

[^9_31]: https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables

[^9_32]: https://talkingschema.ai/docs/glossary/conformed-dimension


---

# I also want to ensure that you understand these things and its details from running these things in Datbricks perspective! Do not revert back to some oldschool traditional developer now!

Correct. I will not fall back to an old-school pattern where I design a traditional warehouse on paper, generate generic SQL/PySpark, and merely run it inside Databricks.

The modeling knowledge will be applied as **executable Databricks architecture**—using Unity Catalog, Delta, Lakeflow, Databricks SQL, metric views, AI/BI, Genie, Apps, Lakebase, Query Profile, and Databricks deployment practices.

## Databricks execution model

| Warehousing concept | Databricks-native implementation |
| :-- | :-- |
| Atomic facts | Governed Unity Catalog Delta tables |
| Incremental event facts | Lakeflow streaming tables or incremental pipelines |
| Current-state dimensions | Materialized views when recomputation correctness is important |
| Historical SCD2 dimensions | Streaming tables with Lakeflow `AUTO CDC` |
| Weekly snapshots | Idempotent Lakeflow pipeline keyed by snapshot date, target week, item, organization and plan version |
| Star/snowflake semantics | Unity Catalog metric views over Gold facts and dimensions |
| Reusable metrics | Metric-view measures, filters, joins and window measures |
| Ad hoc investigation | Databricks SQL with Query Profile |
| Dashboard consumption | AI/BI dashboard over curated datasets or metric views |
| Genie consumption | Curated metric views and narrowly scoped Gold models |
| Application reads | SQL Warehouse, serving tables or synchronized Lakebase read models, based on latency |
| Planner writebacks | Lakebase transactional schema |
| Large-scale writeback history | Lakebase events synchronized into Delta |
| Data-quality controls | Lakeflow expectations, reconciliation tests and monitoring |
| Production delivery | Git, Declarative Automation Bundles and CI/CD after workspace validation |

Databricks recommends fact tables as incrementally maintained streaming tables and dimensions as materialized views, except when dimension history requires an SCD pattern. `AUTO CDC` supports SCD Type 1 and Type 2 processing from CDC feeds or database snapshots.[^10_1][^10_2]

## Dataset choice matters

I will not blindly make everything a Delta table or streaming table.

- **Streaming table:** append-oriented receipts, shipments, inventory movements and action events.
- **Materialized view:** dimension joins, corrected aggregates and results that must recompute when dimension data changes.
- **SCD2 streaming table:** historical item, supplier, organization or planner attributes.
- **Standard view:** lightweight abstraction without persisted results.
- **Metric view:** governed semantic definitions for dashboards, Genie and analytical applications.
- **Lakebase table:** mutable workflow state such as cases, assignments, approvals and action status.

This distinction is important because streaming-table joins do not automatically recompute previously processed rows when a dimension changes. Materialized views can recompute those joins to maintain correctness.[^10_3]

## Joins in Databricks

Before implementing a join, I will inspect the actual tables in Unity Catalog and validate:

1. Left and right grains.
2. Key uniqueness.
3. Expected cardinality.
4. Null and unmatched-key behavior.
5. Row counts before and after the join.
6. Measure totals before and after the join.
7. Physical query plan.
8. Shuffle size, skew, spill and runtime.
9. Whether the model should aggregate before joining.
10. Whether changing dimension attributes require historical or current-state semantics.

I will let Databricks choose the physical join strategy initially. Broadcast, merge, shuffle-hash or skew hints will be introduced only when Query Profile and runtime evidence justify them; Databricks SQL supports these join hints, but they are directives rather than substitutes for correcting grain and cardinality.[^10_4]

## Aggregations and windows

I will write Databricks SQL when the operation is naturally relational:

- Weekly aggregations.
- Plan-versus-actual comparisons.
- Snapshot selection.
- Conditional aggregation.
- Deduplication with `ROW_NUMBER()`.
- Week-over-week comparisons using `LAG()`.
- Rolling demand and lead-time calculations.
- Inventory as-of calculations.
- Exception rankings.
- Supplier-performance metrics.

Databricks SQL window functions define partitions, ordering and frames explicitly; they support moving averages, cumulative statistics, rankings and relative-row access.[^10_5]

I will use `QUALIFY` where it makes the intent clearer, for example when selecting the latest valid snapshot:

```sql
SELECT *
FROM inventory_snapshot
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY item_key, organization_key, snapshot_date
  ORDER BY source_updated_at DESC, ingestion_timestamp DESC
) = 1;
```

Databricks SQL supports `QUALIFY` for filtering results produced by window functions.[^10_6]

## Weekly snapshot operation

A weekly snapshot will not be a traditional “truncate and copy” job unless that is demonstrably the correct requirement.

It will normally include:

```text
snapshot_run
├── snapshot_date
├── snapshot_timestamp
├── target_week_start
├── target_week_end
├── plan_version
├── source_extract_timestamp
├── source_watermark
├── pipeline_update_id
├── source_row_count
├── target_row_count
├── reconciliation_status
└── publication_status
```

The pipeline will:

1. Resolve the business calendar.
2. Determine the eligible plan vintage.
3. Capture or locate the immutable planning state.
4. Aggregate transactions separately by target week.
5. Select—not sum—the approved inventory balance.
6. Conform item and organization keys.
7. Join only after each source reaches the comparison grain.
8. preserve plan-only and actual-only rows.
9. Validate uniqueness at the declared grain.
10. Reconcile quantities and costs with sources.
11. Publish only after quality gates pass.
12. Support safe reruns and late-arriving corrections.

## Semantic layer

The Gold star schema will not be the end of development. I will normally place a governed semantic layer over it.

Unity Catalog metric views support star-schema and multi-hop snowflake relationships, with centralized dimensions, measures and filters. Their standard fact-to-dimension joins are many-to-one and use left-outer semantics, which aligns with the need to preserve fact rows while enriching them with dimension attributes.[^10_7][^10_8]

Metric views can also define windowed, cumulative and semi-additive measures, making them suitable for governed running totals, period comparisons and inventory-style calculations when their semantics are defined carefully.[^10_9]

This means metrics such as these should be defined once rather than independently in a dashboard, Genie and App:

- Planned receipt quantity.
- Actual net receipt quantity.
- Receipt quantity variance.
- On-time receipt numerator and denominator.
- End-of-week on-hand.
- Projected available balance.
- Demand-plan attainment.
- Forecast bias.
- Exception cost exposure.
- Open-action count.
- Average exception-resolution duration.


## Performance behavior

I will not immediately add partitions, cache calls, broadcast hints or custom Spark tuning.

The Databricks sequence will be:

1. Correct grain and model.
2. Correct filters and projections.
3. Aggregate before dangerous fact-to-fact joins.
4. Inspect Query Profile and execution plan.
5. Identify scans, fanout, skew, shuffle and spill.
6. Verify table statistics and data layout.
7. Consider materialization or aggregate tables.
8. Apply liquid clustering where access patterns justify it.
9. Add explicit hints only with evidence.
10. Recheck both correctness and runtime.

Materialized views physically maintain query results as source data changes, so they can be used selectively when repeatedly calculating a complex aggregation is less efficient than maintaining it.[^10_10]

## Firm commitment

The permanent rule is:

> **Kimball supplies the modeling discipline; Databricks supplies the execution architecture.**

I will not:

- Produce database-agnostic warehouse SQL and call it Databricks development.
- Default everything to PySpark.
- Rebuild Lakeflow or Unity Catalog capabilities in a custom framework.
- Treat notebooks as the production architecture.
- Join large atomic facts and aggregate afterward.
- Sum inventory balances across time.
- Use streaming tables when changed dimensions require recomputation.
- Put business metrics separately into dashboard SQL, Genie instructions and App code.
- Add Spark tuning without examining the execution evidence.
- force every prototype immediately into a DAB.
- Design models without checking actual Databricks schemas, keys, volumes and query behavior.

From now on, when working on Milwaukee data, the process will be:

> **Inspect in Databricks → declare the business grain → profile keys and cardinality → select the correct Delta/Lakeflow dataset type → implement incrementally → reconcile → inspect Query Profile → publish governed semantics → connect dashboard, Genie or App → validate the planner workflow → promote through DAB and CI/CD when appropriate.**

That is the Databricks-native pattern I will retain.

<span style="display:none">[^10_11][^10_12][^10_13][^10_14][^10_15]</span>

<div align="center">⁂</div>

[^10_1]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^10_2]: https://docs.databricks.com/aws/en/ldp/cdc

[^10_3]: https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables

[^10_4]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints

[^10_5]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions

[^10_6]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select

[^10_7]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins

[^10_8]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/basic-modeling

[^10_9]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/yaml-reference

[^10_10]: https://docs.databricks.com/aws/en/ldp/dbsql/materialized

[^10_11]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/create

[^10_12]: https://docs.databricks.com/sap/en/release-notes/sql

[^10_13]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^10_14]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^10_15]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/


---

# what is medallion architecture and all ..

continuing

The following are the priority ordersm let's call them P1, P2, P3, P4 and such.

These goals are to be achieved. but the usecases are the first priority! so if P1 and P2 get some information together .. or some other combinations .. do not just stop working ... if P2 happens with P1 or P3 in the sides, it is good for us!

Customer Email:
Sorry Everyone,
This is the latest requirements document and these are the requirements.  PO Exceptions is not in scope.  Apologies for the confusion.  The correct requirements are in the attached.  Mike / Peter I will follow up.
Listed below in priority order:

The ‘Actuals Supply Plan’ (see notebook attachment called Actuals Supply Plan Requirements.dbc)
Exceptions for supply planning (see notebook attachment called "Red_Keychain_Supply_Planning_Requirements.dbc" focus only on the supply exceptions portion)
Events app for demand planning (see notebook attachment called, "01_Requirements.dbc")
Exceptions for demand planning (see notebook attachment called "Red_Keychain_Supply_Planning_Requirements.dbc" focus only on the demand exceptions portion)

Understood. I am recording the customer’s latest email as the **authoritative scope and priority order**, overriding conflicting or broader statements in the earlier requirements.

## Medallion architecture

Medallion architecture is a **Databricks lakehouse data-design pattern** that progressively improves data quality and business usability:

```text
Source systems
      │
      ▼
Bronze — faithful source capture
      │
      ▼
Silver — validated and conformed data
      │
      ▼
Gold — business-ready data products
      │
      ├── AI/BI dashboards
      ├── Genie
      ├── Forecasting and ML
      ├── Agentic Supply Chain App
      └── Operational decisions
```

Databricks defines Bronze as raw, Silver as validated, and Gold as enriched—including dimensional modeling and business aggregation. Databricks recommends the pattern but explicitly says it is **not mandatory**.[^11_1]

### Layer responsibilities

| Layer | Milwaukee supply-chain purpose | Example |
| :-- | :-- | :-- |
| Bronze | Preserve source fidelity and ingestion evidence | Raw Oracle CDC, API responses, uploaded planning files |
| Silver | Clean, deduplicate, type, conform and retain atomic detail | Receipt transaction, shipment event, inventory snapshot, supply-plan snapshot |
| Gold | Apply supply-chain semantics, dimensional modeling and aggregation | Weekly actual-versus-plan, supply exceptions, demand-event forecast, demand exceptions |
| Semantic | Define trusted measures and relationships | Receipt attainment, inventory variance, forecast bias, exception severity |
| Operational | Manage mutable workflow state | Lakebase cases, assignments, comments, approvals and actions |

The **semantic and operational layers are useful architectural labels**, but they are not additional mandatory “medals.”

## Important boundaries

Medallion architecture is not the same as:

- Dev, test and production environments.
- Kimball dimensional modeling.
- Lakebase transactional modeling.
- Databricks Apps.
- A requirement to copy every existing EDW table three times.
- A requirement to create three separate pipelines for every use case.

Kimball stars normally belong in Gold, while Lakebase sits alongside the analytical lakehouse as the transactional system for App workflow state.

If an existing `prodedw` table is already governed, cleaned, historized and suitable for the project, I will **reuse it as an authoritative source** rather than create unnecessary Bronze and Silver copies simply to satisfy a diagram. The Actuals requirements already identify existing EDW facts, dimensions and supply-plan snapshots that may be reused.[^11_2]

## Confirmed priorities

The customer’s corrected order becomes:


| Priority | Outcome | Primary requirements |
| :-- | :-- | :-- |
| **P1** | Actuals Supply Plan | `Actuals_Supply_Plan_Requirements` |
| **P2** | Supply-planning exceptions | Supply-exception portion of Red Keychain only |
| **P3** | Demand-planning Events App | `01_Requirements` |
| **P4** | Demand-planning exceptions | Demand-exception portion of Red Keychain only |

**PO Exceptions are explicitly out of scope.**

This latest instruction supersedes the portions of Red Keychain that describe PO exception handling, PO release, PO grouping, PO modification and Oracle PO-action execution.

## Scope interpretation

Because the Red Keychain document mixes supply exceptions, PO exceptions, ordering, transitions, optimization and execution, I will use the following working boundary.

### P2 included

Candidate supply-planning exceptions include:

- Demand exceeding available or projected supply.
- Potential stockout.
- Excess inventory versus target.
- Projected inventory below safety stock.
- Inventory imbalance across distribution centers.
- Stranded inventory.
- MOQ-driven excess exposure, if evaluated as inventory risk rather than a PO action.
- Old-SKU rundown risk.
- New-SKU supply coverage gaps.
- Product-transition overlap.
- Lead-time drift as a planning signal.
- Material demand-forecast changes affecting supply.
- Frozen-zone violations.
- Plan-versus-actual supply or receipt variance.
- Supply-demand imbalance and capacity or availability risk.

These exception families appear in the Red Keychain requirements, but they must now be filtered through the customer’s “PO Exceptions out of scope” correction.[^11_3]

### P2 excluded

Unless the customer later reverses the decision, I will exclude:

- PO past-due exception queue.
- PO pull-in recommendations.
- PO push-out recommendations.
- New-PO recommendations.
- PO cancellation recommendations.
- Bulk PO actions.
- Requisition-to-PO conversion.
- Truckload PO grouping and sequencing.
- PO release recommendations.
- Direct Oracle PO modifications.
- Ordering execution workflows.
- Supplier follow-up framed specifically as a PO exception.
- Agentic execution that changes a PO.

A receipt variance can still be an **Actuals or supply-performance signal**, but it must not silently become an in-scope PO-action workflow.

## Priorities aren’t silos

P1, P2, P3 and P4 define the order of **business outcomes**, not four isolated implementations.

If P1 creates a reusable dataset needed by P2, both can advance together. If P3 establishes a reusable event-demand model needed by P4, that work should also support P4 without creating a duplicate pipeline.

```text
P1 Actuals Supply Plan
   ├── weekly plan snapshots
   ├── receipt/shipment/inventory actuals
   ├── plan-versus-actual fact
   └── variance signals
                 │
                 ▼
P2 Supply Exceptions
   ├── stockout and excess risk
   ├── safety-stock violations
   ├── supply-demand imbalance
   └── transition/network exceptions


P3 Demand Events App
   ├── event definitions
   ├── event-item-customer-month forecasts
   ├── baseline plus incremental demand
   └── planner overrides and audit
                 │
                 ▼
P4 Demand Exceptions
   ├── unusual event changes
   ├── baseline/event inconsistencies
   ├── forecast deviation and bias
   └── missing, overlapping or expired events
```

The Events App requirements describe incremental forecasts above baseline demand, including non-repeating and repeating events, monthly item/customer values, disaggregation, status, locking and audit history. Those outputs naturally become context for later demand-exception detection.[^11_4]

## Shared foundation

The use cases can share selected conformed assets without becoming one giant implementation.


| Shared asset | P1 | P2 | P3 | P4 |
| :-- | --: | --: | --: | --: |
| Item/product dimension | ✓ | ✓ | ✓ | ✓ |
| Organization dimension | ✓ | ✓ | ✓ | Optional |
| Planning calendar | ✓ | ✓ | ✓ | ✓ |
| Customer hierarchy |  |  | ✓ | ✓ |
| Supplier attributes | ✓ | ✓ |  |  |
| Supply-plan snapshots | ✓ | ✓ |  |  |
| Actual receipts/shipments | ✓ | ✓ |  | Optional |
| Inventory snapshots | ✓ | ✓ |  |  |
| Demand baseline | ✓ | ✓ | ✓ | ✓ |
| Event forecast |  | Optional | ✓ | ✓ |
| Exception taxonomy | Variance causes | Supply | Validation only | Demand |
| Lakebase workflow model | Optional notes | Cases | Event editing | Cases |

“Shared” does not mean “build everything upfront.” A shared asset should be implemented when the active use case needs it and then designed so later priorities can safely reuse it.

## Recommended data products

### P1 Gold product

```text
fct_supply_plan_snapshot
fct_receipt_actual
fct_shipment_actual
fct_inventory_periodic_snapshot
fct_weekly_actual_vs_plan
mv_actual_vs_plan_summary
metrics_actual_supply_plan
```

The weekly Gold comparison should preserve snapshot vintage and use an item–organization–week comparison grain. Receipt and shipment flows should be aggregated from transactions, while ending on-hand must be selected as a point-in-time balance rather than summed across the week.[^11_2]

### P2 Gold product

```text
fct_supply_exception
fct_supply_exception_evidence
dim_supply_exception_type
mv_open_supply_exceptions
metrics_supply_exception_management
```

P2 should initially produce **detected, ranked and explainable planning exceptions**. It should not accidentally introduce PO-action execution.

### P3 analytical and transactional products

```text
Lakebase:
  demand_event
  demand_event_item
  demand_event_customer
  demand_event_assumption
  demand_event_monthly_value
  demand_event_change_log
  demand_event_lock

Delta/Gold:
  fct_demand_event_forecast
  fct_demand_event_audit
  mv_active_event_forecast
```

The required exported grain is one customer-leaf member × item × month for active events. The App also requires lifecycle status, editing locks, header/line assumptions, disaggregation and detailed audit behavior.[^11_4]

### P4 Gold product

```text
fct_demand_exception
fct_demand_exception_evidence
dim_demand_exception_type
mv_open_demand_exceptions
metrics_demand_exception_management
```

P4 should reuse baseline demand, event forecast, planner overrides, forecast vintages and actual-demand signals developed through P1 and P3 where applicable.

## Delivery order

### P1 first slice

The first working use case should answer:

> For a selected SKU and organization, what did last Monday’s supply plan predict, what actually occurred during the week, and what caused the largest variance?

Build only what is necessary to prove:

- Weekly plan vintage.
- Receipt, shipment and inventory actuals.
- Correct weekly grain.
- Variance calculations.
- Source reconciliation.
- Planner-facing drill-down.


### P2 alongside P1

While building P1, we can expose reusable signals for P2:

- Projected shortage.
- Safety-stock breach.
- Supply-demand gap.
- Excess projected inventory.
- Plan-versus-actual variance.
- Inventory imbalance.

However, P2 becomes “delivered” only when the planner has a useful exception queue with ranking, explanation, evidence and disposition—not merely because P1 produced a variance column.

### P3 independent vertical slice

P3 can progress when it does not block P1:

> Create one demand event, add items and customers, calculate monthly incremental demand, save it transactionally, activate it, and confirm the correct customer-item-month output.

### P4 alongside P3

As P3 captures event changes and validations, it can produce candidate P4 signals:

- Event active with no monthly demand.
- Event outside its valid date range.
- Invalid or inactive item.
- Unusually large planner override.
- Overlapping events.
- Repeating demand without continuation.
- Non-repeating event spread across multiple months.
- Event forecast materially inconsistent with baseline.

Again, these become P4 only when they are framed and accepted as demand-planning exceptions.

## Flexible priority rule

The execution rule will be:

```text
1. Always protect P1 progress.
2. Build reusable foundations only when P1 or another active use case needs them.
3. Allow P2/P3/P4 progress when it comes naturally from current work.
4. Never block a completed use case waiting for a theoretical enterprise model.
5. Never declare a later priority complete merely because a shared table exists.
6. Demonstrate each priority through a planner workflow.
```

A useful prioritization measure is:

```text
Work next =
  business-use-case value
  + reuse across priorities
  + dependency removal
  + learning value
  - delivery risk
  - unnecessary scope
```

This is more effective than completing every technical layer of P1 before touching any useful P2 or P3 work.

## Updated project directive

From now on, Milwaukee Supply Chain Databricks FDE mode includes:

> Treat P1 Actuals Supply Plan, P2 Supply Planning Exceptions, P3 Demand Planning Events App and P4 Demand Planning Exceptions as the authoritative priority order. PO Exceptions and PO action execution are out of scope. Priorities represent business outcomes, not isolated technical projects. Deliver P1 first while allowing shared data, semantic, QA, UI or platform work to advance P2, P3 or P4 when that creates real reuse and does not endanger P1. Use medallion architecture pragmatically: preserve new source data in Bronze when needed, create validated atomic and conformed Silver products, and publish use-case-driven Gold facts, dimensions, aggregates and metric views. Reuse suitable existing EDW assets rather than manufacturing unnecessary layers. Keep Lakebase transactional state separate from analytical medals. Define success through working planner use cases—not through the number of Bronze, Silver and Gold tables created.

That priority and scope correction is now the governing interpretation.

<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_16][^11_17][^11_18][^11_5][^11_6][^11_7][^11_8][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://docs.databricks.com/aws/en/lakehouse/medallion

[^11_2]: Actuals_Supply_Plan_Requirements.md

[^11_3]: Red_Keychain_Supply_Planning_Requirements.md

[^11_4]: 01_Requirements.md

[^11_5]: https://www.linkedin.com/pulse/understanding-medallion-architecture-databricks-bronze-chaudhari-rsrmf

[^11_6]: https://community.databricks.com/t5/community-articles/medallion-architecture-in-practice-the-design-decisions-nobody/td-p/163206

[^11_7]: https://community.databricks.com/t5/data-engineering/medallion-architecture-and-databricks-assistant/td-p/102301

[^11_8]: https://erstudio.com/blog/understanding-the-three-layers-of-medallion-architecture/

[^11_9]: https://erstudio.com/blog/how-medallion-architecture-with-er-studio-and-databricks-solves-data-as-a-product-for-both-business-and-it/

[^11_10]: https://cosmosthrace.com/resources/databricks/databricks-medallion-architecture-best-practices

[^11_11]: https://www.databricks.com/blog/what-is-medallion-architecture

[^11_12]: https://www.reddit.com/r/databricks/comments/1c93t94/medallion_architecture/

[^11_13]: https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825

[^11_14]: https://tacnode.io/post/medallion-architecture

[^11_15]: https://community.databricks.com/t5/data-engineering/medallion-architecture-do-i-need-a-materialized-exploded-layer/td-p/139085

[^11_16]: https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion

[^11_17]: https://www.reddit.com/r/databricks/comments/1j0gyd5/best_practices_for_medallion_architecture_in/

[^11_18]: https://www.reddit.com/r/databricks/comments/173p6ev/bronzesilvergold_what_really_happens_in_each/


---

# I also want to be able to show Genie Agent in the Databricks Dashboards. and Also in the App.

Write all of the deliverables, that you think we should be providing for each priorities?

Yes. Each priority should deliver a complete **business capability**, including data, pipelines, semantics, dashboard, Genie, App workflow, QA, governance, and operations—not merely notebooks or tables.

For Genie, I recommend **native companion Genie Agents on published dashboards** and **focused reusable Genie Agents inside the App**, all grounded in the same Gold models and metric views. Published dashboards provide an **Ask Genie** experience and can generate a companion Agent from their datasets and visualizations.[^12_1]

## Genie surfaces

| Surface | Recommended implementation |
| :-- | :-- |
| AI/BI dashboard | Native companion Genie Agent with Ask Genie |
| Databricks App | Focused Genie Agent declared as an App resource |
| Agentic workflow | Genie for analytical investigation; typed tools for writebacks/actions |
| Shared semantics | Gold tables and Unity Catalog metric views |
| Validation | Benchmark questions, expected SQL, expected results and reconciliation |

A dashboard can generate its own companion Genie Agent or link an existing one. The automatically generated companion receives dashboard filter context, while filters do not automatically carry into a separately created Agent linked to the dashboard.[^12_2][^12_1]

Therefore, the default will be:

- **Dashboard:** automatically generated companion for chart and filter context.
- **App:** curated reusable Agent specialized for the module.
- **Consistency:** both use the same metric views, terminology, example SQL and test corpus.
- **No mega-Agent:** Actuals, Supply Exceptions, Demand Events and Demand Exceptions receive focused Agents.

A Databricks App can declare a Genie Agent as a resource, receive its ID through configuration and invoke it with `CAN RUN`; the App identity may also require SQL Warehouse and Unity Catalog permissions.[^12_3]

# Shared deliverables

These should be created once and expanded as priorities require them.

## Business foundation

- Authoritative P1–P4 scope statement.
- Explicit PO Exceptions exclusion.
- Supply-chain domain glossary.
- Business-process and Monday planning-cycle maps.
- Persona and decision catalog.
- Detailed use cases with acceptance criteria.
- Requirements traceability matrix.
- Assumption, decision and open-question register.
- Out-of-scope register.


## Data foundation

- EDW, Oracle, snapshot and operational-source inventory.
- Source ownership, freshness and authority assessment.
- Data-profiling workbook/results.
- Grain contract for each fact and snapshot.
- Join-cardinality and fanout contracts.
- Source-to-target mappings.
- Conformed dimensions and bus matrix.
- Medallion-layer mapping.
- Data-quality and reconciliation framework.
- Unity Catalog naming, ownership, permissions and lineage.


## Platform foundation

- Authorized workspace development structure.
- Compute and SQL Warehouse decisions.
- Lakeflow pipeline and scheduling standards.
- Lakebase environment and migration standard.
- Identity and permission matrix.
- Authentication and networking matrix.
- Databricks App health/readiness pattern.
- Git and workspace-first development workflow.
- DAB and CI/CD promotion criteria.
- Deployment, rollback and recovery runbook.
- Logging, tracing, monitoring and alerting.


## Quality foundation

- Unit, data, integration, API, UI and security tests.
- Genie benchmark harness.
- Source reconciliation evidence.
- Planner UAT scenarios.
- Deployment smoke tests.
- Evidence-backed delivery ledger.
- Definition of done.


# P1 Actuals Supply Plan

## Business outcome

A planner can select a SKU and organization, see what the prior plan predicted, see what happened during the completed week and identify the major causes of variance.

The requirements define a Monday–Sunday cycle using historical supply-plan snapshots, receipt and shipment transactions, and point-in-time inventory.[^12_4]

## Data products

- Profiled supply-plan, receipt, shipment and inventory sources.
- Validated historical coverage for the approved backfill.
- Immutable supply-plan snapshot model.
- Receipt-transaction actual fact.
- Shipment-transaction actual fact.
- Inventory periodic-snapshot fact.
- Weekly planned-supply summary.
- Weekly receipt and shipment summaries.
- Weekly Actuals-versus-Plan Gold fact.
- Supplier, planner and product rollups.
- Plan-only and actual-only scaffold.
- Source-to-Gold reconciliation tables.

The comparison grain should be one item × organization × target week × selected plan vintage. Flow measures are aggregated over the week, while ending inventory is selected as a point-in-time balance.[^12_4]

## Pipeline assets

- Source profiling notebooks.
- Parameterized weekly Lakeflow pipeline.
- Idempotent rerun behavior.
- Controlled 180-day backfill.
- Late-data and restatement handling.
- Grain, key, freshness and reconciliation expectations.
- Monday readiness monitoring.
- Query Profile and performance evidence.


## Semantic model

- Actuals Supply Plan metric view.
- Trusted dimensions for week, item, organization, supplier, planner and plan vintage.
- Planned and actual quantities.
- Absolute and percentage variance.
- Receipt attainment.
- Receipt timing performance.
- Ending inventory variance.
- Plan accuracy and bias.
- Explicit semi-additive inventory handling.


## Dashboard

- Monday planner overview.
- Plan-versus-actual KPI cards.
- Weekly trend.
- Item-organization drill-down.
- Supplier and planner analysis.
- Transaction evidence.
- Freshness, snapshot and plan-vintage indicators.
- Native **Ask Genie** companion.


## Genie

- Focused Actuals Agent.
- Business vocabulary and date/vintage rules.
- Certified example SQL.
- Benchmark questions and expected answers.
- Inventory additivity tests.
- Zero-plan and missing-snapshot tests.
- Dashboard companion configuration.
- Reusable **Ask Actuals Genie** capability in the App.


## App

- Actuals summary and drill-down.
- Supporting transaction evidence.
- Variance explanation.
- Ask Actuals Genie panel.
- Links to the AI/BI dashboard.
- API contracts for summaries, trends and evidence.
- SQL/Genie/model provenance.
- No PO actions or PO writebacks.


## Acceptance

- One SKU-org-week reconciles from source through Gold.
- Dashboard and Genie return the same governed metrics.
- The intended plan vintage is reproducible.
- Inventory is not incorrectly summed over time.
- Monday planner UAT passes.


# P2 Supply Exceptions

## Business outcome

A planner receives a prioritized queue of meaningful supply-planning conditions, investigates supporting evidence, assigns or disposes the case and tracks resolution.

## Scope assets

- Signed Supply-versus-PO exception boundary.
- Approved supply-exception taxonomy.
- Severity, ownership, SLA and escalation rules.
- Suppression, snooze, reopen and expiration behavior.
- Explicit excluded list.

Included candidates:

- Supply-demand gap.
- Potential stockout.
- Excess inventory.
- Safety-stock violation.
- Network inventory imbalance.
- Stranded inventory.
- Product-transition supply risk.
- Lead-time drift.
- Frozen-zone violation.
- Plan-versus-actual supply variance.

Excluded:

- PO pull-in or push-out.
- Create or cancel PO.
- Past-due PO queue.
- PO grouping or release.
- Oracle PO modification.
- Bulk PO actions.


## Data products

- Versioned supply-exception rule registry.
- Exception detection fact.
- Exception evidence fact.
- Exception taxonomy dimension.
- Exception lifecycle history.
- Priority score components.
- Open-exception materialized view.
- Exception-management metric view.
- Linkage to P1 Actuals evidence.


## Lakebase workflow

- Case.
- Assignment.
- Status.
- Root cause.
- Disposition.
- Comment.
- Snooze/suppression.
- Recommendation.
- Audit event.
- Optimistic concurrency and idempotency.

The workflow can write case state to Lakebase, but it must not modify purchase orders.

## Dashboard

- Open exceptions by severity, type and organization.
- Age and resolution trends.
- Product and planner analysis.
- Service and inventory exposure.
- Drill-through to P1 evidence.
- Native Ask Genie companion.


## Genie

- Focused Supply Exceptions Agent.
- Exception investigation questions.
- Rule and evidence explanations.
- Count and severity reconciliation.
- Guardrails against claiming operational PO actions.
- Ask Supply Exceptions Genie panel in the App.


## App

- Prioritized exception queue.
- Filters, saved views and sorting.
- Bulk assignment/disposition where approved.
- Exception details.
- Supporting plan, demand, inventory and Actuals evidence.
- Explanation and recommendation.
- Comments and audit history.
- Transactional Lakebase writebacks.
- Outcome tracking.


## Acceptance

- Every exception maps to an approved rule or model version.
- No PO Exceptions appear.
- Repeated evaluation does not create duplicate active cases.
- App writebacks survive refresh and appear in audit history.
- Dashboard, Genie and App counts reconcile.


# P3 Demand Events App

## Business outcome

A demand planner creates an incremental-demand event, selects items and customers, calculates or enters monthly quantities, activates the event and verifies the correct downstream output.

The requirements distinguish non-repeating and repeating events, specify In Progress/Active/Deactivated states, require event locks and audit history, and define output at customer leaf × item × month.[^12_5]

## Domain assets

- Event lifecycle and terminology.
- Baseline-versus-incremental-demand definitions.
- Non-repeating load-in rules.
- Repeating run-rate rules.
- Ship-month and set-month rules.
- Header and line override precedence.
- Customer disaggregation rules.
- Item, customer and date validation rules.
- Lock and concurrency behavior.
- Publication eligibility.


## Lakebase model

- Event header.
- Event type.
- Selected customers.
- Selected items.
- Assumptions.
- Monthly forecast values.
- Line-level overrides.
- Tags and comments.
- Edit lock.
- Publication state.
- Field-level audit history.
- Schema migrations and constraints.


## API deliverables

- Create and update event.
- Duplicate event.
- Activate/deactivate event.
- Acquire/release lock.
- Calculate forecast.
- Validate.
- Import item list.
- Publish.
- Retrieve audit history.
- Optimistic concurrency.
- Typed errors and idempotency.


## Analytical products

- Customer and item lookup views.
- Baseline-demand semantic view.
- Versioned disaggregation ratios.
- Published active-event forecast fact.
- Baseline-plus-event analytical view.
- Event publication and audit facts.
- Reconciliation from Lakebase to Delta/output.


## App

- Event list and search.
- Creation and metadata.
- Customer multi-select.
- Customer hierarchy input.
- Item paste/import and validation.
- Monthly editable grid.
- Forecast Builder.
- Header assumptions and line overrides.
- Lock/conflict UX.
- Pre-publication validation.
- Activation/deactivation.
- Audit history.
- Publication status.


## Dashboard

- Active incremental demand by month.
- Customer and product hierarchy.
- Event type and status.
- Baseline-versus-event demand.
- Event overlap and concentration.
- Expiration and publication health.
- Native Ask Genie companion.


## Genie

- Focused Demand Events Agent.
- Event contribution and concentration questions.
- Monthly demand profile.
- Baseline comparison.
- Customer-disaggregation tests.
- Status/date-range tests.
- Ask Demand Events Genie in the App.

Genie will remain analytical. It will not activate or edit an event; those operations use typed App actions with validation and transactional controls.

## Integration

- Daily publication before the approved pickup.
- Run IDs and control totals.
- Output reconciliation.
- Failure and retry behavior.
- Alerting.
- Approved truncate/reload or incremental-publication decision.


## Acceptance

- Planner completes the full create-to-activate workflow.
- Concurrent editing is controlled.
- Output expands correctly to customer-item-month grain.
- App and publication totals reconcile.
- Deactivated events disappear from active output but retain history.


# P4 Demand Exceptions

## Business outcome

A demand planner receives a focused queue of material problems across baseline forecasts, event increments, overrides, final forecasts and actual-demand signals.

## Domain assets

- Demand-exception taxonomy.
- Separation of business, data-quality, process and model-quality exceptions.
- Severity, ownership, SLA and escalation.
- Approved definitions of forecast vintage, actual demand, bias and accuracy.
- Segmentation by volume, variability, lifecycle and customer/channel.

Candidate exceptions include:

- Significant forecast change.
- Actual demand materially different from plan.
- Persistent bias.
- Unusually large override.
- Active event with no demand.
- Expired or invalid event.
- Overlapping events.
- Incorrect repeating/non-repeating pattern.
- Customer-disaggregation anomaly.
- Baseline-plus-event inconsistency.
- New-item signal gap.


## Data products

- Demand forecast-vintage fact.
- Baseline, event, override, working and final forecast components.
- Demand-exception rule/model registry.
- Demand-exception fact.
- Exception evidence fact.
- Demand-exception metric view.
- Open-exception materialized view.
- False-positive and outcome history.


## ML deliverables

ML will be introduced only after deterministic rules and historical evidence establish a measurable need.

If forecasting or anomaly detection is used:

- Baseline model.
- Time-based validation.
- Segment-level evaluation.
- MLflow experiment.
- Feature and training-data lineage.
- Unity Catalog model registration.
- Batch or Model Serving deployment decision.
- Bias, drift and accuracy monitoring.
- Model-version provenance.
- Champion/challenger policy.


## Dashboard

- Demand exceptions by severity and age.
- Baseline, event and final-forecast comparison.
- Forecast accuracy and bias.
- Customer and item segmentation.
- Owner and resolution trend.
- Drill-through to event and forecast history.
- Native Ask Genie companion.


## Genie

- Focused Demand Exceptions Agent.
- Forecast-vintage-aware questions.
- Baseline-versus-event interpretation.
- Bias and accuracy analysis.
- Guardrail against presenting correlation as confirmed cause.
- Ask Demand Exceptions Genie in the App.


## App

- Demand-exception queue.
- Detailed forecast-component evidence.
- Root-cause and disposition workflow.
- Lakebase comments and audit history.
- Deep link to P3 when an event requires correction.
- Model provenance and confidence.
- Outcome and recurrence tracking.


## Acceptance

- Each exception has a versioned rule or validated model.
- Baseline and event demand remain distinct.
- Event corrections follow P3 locks and validation.
- Dashboard, Genie, App and semantic metrics reconcile.
- False-positive and recurrence rates can be measured.


# Unified planner App

The eventual App can provide a cohesive experience without creating one huge Agent:

```text
Planner Home
├── Actuals Supply Plan
│   └── Ask Actuals Genie
├── Supply Exceptions
│   └── Ask Supply Exceptions Genie
├── Demand Events
│   └── Ask Demand Events Genie
└── Demand Exceptions
    └── Ask Demand Exceptions Genie
```

The App should route questions to the Agent for the active module and explicitly pass selected SKU, organization, week, event or exception context. The Genie API supports stateful conversations and follow-up questions and can return generated SQL and query results for application integration.[^12_6][^12_7]

# Delivery sequence

## Wave 0

- Validate authentication and source access.
- Profile critical sources.
- Confirm grains and week/vintage semantics.
- Prove SQL Warehouse, App, Lakebase, dashboard and Genie connectivity.
- Establish canonical workspace structure.


## Wave 1

- Deliver one P1 SKU-org-week vertical slice.
- Add a P1 dashboard page with Ask Genie.
- Add P1 App drill-down with Ask Actuals Genie.
- Begin P2 rule discovery using P1 signals.


## Wave 2

- Productionize P1.
- Deliver P2 exception detection, Lakebase workflow, dashboard and Genie.
- Build a small P3 App/Lakebase feasibility skeleton in parallel when capacity permits.


## Wave 3

- Deliver the complete P3 Events App.
- Deliver event dashboard and Genie.
- Capture P4 candidate signals naturally.


## Wave 4

- Deliver P4 demand-exception detection and workflow.
- Add forecasting or anomaly models only where justified.
- Complete the dashboard, Genie and App experience.


# Completion package

For every priority, the completed package should include:

1. Business use case and scope.
2. Domain and metric definitions.
3. Source inventory and profiling.
4. Grain and dimensional model.
5. Join and aggregation contracts.
6. Source-to-target mappings.
7. Pipeline or transactional implementation.
8. Unity Catalog objects and permissions.
9. Metric view and certified SQL.
10. AI/BI dashboard with native Ask Genie.
11. Focused App Genie Agent.
12. Genie benchmark and evaluation evidence.
13. App UI and API contracts.
14. Lakebase model where writeback is required.
15. Data-quality and reconciliation tests.
16. Authentication, security and network validation.
17. Workspace deployment and DAB/CI/CD promotion.
18. Monitoring, runbook and recovery.
19. Planner UAT script.
20. Evidence-backed acceptance record.

A priority is complete only when its deployed planner workflow passes, data reconciles, Genie passes its benchmark questions, required writebacks persist, errors are observable and the business owner accepts the result.

<span style="display:none">[^12_10][^12_100][^12_101][^12_102][^12_103][^12_104][^12_105][^12_106][^12_107][^12_108][^12_109][^12_11][^12_110][^12_111][^12_112][^12_113][^12_114][^12_115][^12_116][^12_117][^12_118][^12_119][^12_12][^12_120][^12_121][^12_122][^12_123][^12_124][^12_125][^12_126][^12_127][^12_128][^12_129][^12_13][^12_130][^12_131][^12_132][^12_133][^12_134][^12_135][^12_136][^12_137][^12_138][^12_139][^12_14][^12_140][^12_141][^12_142][^12_143][^12_144][^12_145][^12_146][^12_147][^12_148][^12_149][^12_15][^12_150][^12_151][^12_152][^12_153][^12_154][^12_155][^12_156][^12_157][^12_158][^12_159][^12_16][^12_160][^12_161][^12_162][^12_163][^12_164][^12_165][^12_166][^12_167][^12_168][^12_169][^12_17][^12_170][^12_171][^12_172][^12_173][^12_174][^12_175][^12_176][^12_177][^12_178][^12_179][^12_18][^12_180][^12_181][^12_182][^12_183][^12_184][^12_185][^12_186][^12_187][^12_188][^12_189][^12_19][^12_190][^12_191][^12_192][^12_193][^12_194][^12_195][^12_196][^12_197][^12_198][^12_199][^12_20][^12_200][^12_201][^12_202][^12_203][^12_204][^12_205][^12_206][^12_207][^12_208][^12_209][^12_21][^12_210][^12_211][^12_212][^12_213][^12_214][^12_215][^12_216][^12_217][^12_218][^12_219][^12_22][^12_220][^12_221][^12_222][^12_223][^12_224][^12_225][^12_226][^12_227][^12_228][^12_229][^12_23][^12_230][^12_231][^12_232][^12_233][^12_234][^12_235][^12_236][^12_237][^12_238][^12_239][^12_24][^12_240][^12_241][^12_242][^12_243][^12_244][^12_245][^12_246][^12_247][^12_248][^12_249][^12_25][^12_250][^12_251][^12_252][^12_253][^12_254][^12_255][^12_256][^12_257][^12_258][^12_259][^12_26][^12_260][^12_261][^12_262][^12_263][^12_264][^12_265][^12_266][^12_267][^12_268][^12_269][^12_27][^12_270][^12_271][^12_272][^12_273][^12_274][^12_275][^12_276][^12_277][^12_278][^12_279][^12_28][^12_280][^12_281][^12_282][^12_283][^12_284][^12_285][^12_286][^12_287][^12_288][^12_289][^12_29][^12_290][^12_291][^12_292][^12_293][^12_294][^12_295][^12_296][^12_297][^12_298][^12_299][^12_30][^12_300][^12_301][^12_302][^12_303][^12_304][^12_305][^12_306][^12_307][^12_308][^12_309][^12_31][^12_310][^12_311][^12_312][^12_313][^12_314][^12_315][^12_316][^12_317][^12_318][^12_319][^12_32][^12_320][^12_321][^12_322][^12_323][^12_324][^12_325][^12_326][^12_327][^12_328][^12_329][^12_33][^12_330][^12_331][^12_332][^12_333][^12_334][^12_335][^12_336][^12_337][^12_338][^12_339][^12_34][^12_340][^12_341][^12_342][^12_343][^12_344][^12_345][^12_346][^12_347][^12_348][^12_349][^12_35][^12_350][^12_351][^12_352][^12_353][^12_354][^12_355][^12_356][^12_357][^12_358][^12_359][^12_36][^12_360][^12_361][^12_362][^12_363][^12_364][^12_365][^12_366][^12_367][^12_368][^12_369][^12_37][^12_370][^12_371][^12_372][^12_373][^12_374][^12_375][^12_376][^12_377][^12_378][^12_379][^12_38][^12_380][^12_381][^12_382][^12_383][^12_384][^12_385][^12_386][^12_387][^12_388][^12_389][^12_39][^12_390][^12_391][^12_392][^12_393][^12_394][^12_395][^12_396][^12_397][^12_398][^12_399][^12_40][^12_400][^12_401][^12_402][^12_403][^12_404][^12_405][^12_406][^12_41][^12_42][^12_43][^12_44][^12_45][^12_46][^12_47][^12_48][^12_49][^12_50][^12_51][^12_52][^12_53][^12_54][^12_55][^12_56][^12_57][^12_58][^12_59][^12_60][^12_61][^12_62][^12_63][^12_64][^12_65][^12_66][^12_67][^12_68][^12_69][^12_70][^12_71][^12_72][^12_73][^12_74][^12_75][^12_76][^12_77][^12_78][^12_79][^12_8][^12_80][^12_81][^12_82][^12_83][^12_84][^12_85][^12_86][^12_87][^12_88][^12_89][^12_9][^12_90][^12_91][^12_92][^12_93][^12_94][^12_95][^12_96][^12_97][^12_98][^12_99]</span>

<div align="center">⁂</div>

[^12_1]: https://docs.databricks.com/aws/en/dashboards/genie-spaces

[^12_2]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^12_3]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^12_4]: Actuals_Supply_Plan_Requirements.md

[^12_5]: 01_Requirements.md

[^12_6]: https://docs.databricks.com/aws/en/ai-bi/admin/use-apis

[^12_7]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^12_8]: https://docs.databricks.com/aws/en/integrations/msft-teams

[^12_9]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^12_10]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^12_11]: https://docs.databricks.com/aws/en/dashboards/

[^12_12]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^12_13]: https://docs.databricks.com/api/apps/v1/app

[^12_14]: https://docs.databricks.com/aws/en/ai-bi/admin/embed

[^12_15]: https://docs.databricks.com/aws/en/genie-one/

[^12_16]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^12_17]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^12_18]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^12_19]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^12_20]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^12_21]: https://docs.databricks.com/aws/en/ldp/concepts

[^12_22]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^12_23]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^12_24]: https://docs.databricks.com/aws/en/ldp/

[^12_25]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^12_26]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^12_27]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^12_28]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^12_29]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^12_30]: https://docs.databricks.com/aws/en/ldp/real-time

[^12_31]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^12_32]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^12_33]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^12_34]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^12_35]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^12_36]: https://docs.databricks.com/aws/en/tables/clustering

[^12_37]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^12_38]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^12_39]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^12_40]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^12_41]: https://docs.databricks.com/aws/en/delta/tutorial

[^12_42]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^12_43]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^12_44]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^12_45]: https://docs.databricks.com/aws/en/mlflow/

[^12_46]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^12_47]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^12_48]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^12_49]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^12_50]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^12_51]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^12_52]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^12_53]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^12_54]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^12_55]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^12_56]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^12_57]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^12_58]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^12_59]: https://docs.databricks.com/gcp/en/languages/overview

[^12_60]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^12_61]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^12_62]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^12_63]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^12_64]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^12_65]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^12_66]: https://docs.databricks.com/aws/en/oltp/projects/

[^12_67]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^12_68]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^12_69]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^12_70]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^12_71]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^12_72]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^12_73]: https://docs.databricks.com/aws/en/query-federation/oracle

[^12_74]: https://docs.databricks.com/aws/en/ldp/expectations

[^12_75]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^12_76]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^12_77]: https://docs.databricks.com/aws/en/ldp/concepts/

[^12_78]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^12_79]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^12_80]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^12_81]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^12_82]: https://docs.databricks.com/aws/en/query-federation/networking

[^12_83]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^12_84]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^12_85]: https://docs.databricks.com/aws/en/query-federation/databricks

[^12_86]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^12_87]: https://docs.databricks.com/gcp/en/developers/best-practices

[^12_88]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^12_89]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^12_90]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^12_91]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^12_92]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^12_93]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^12_94]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^12_95]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^12_96]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^12_97]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^12_98]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^12_99]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^12_100]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^12_101]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^12_102]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^12_103]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^12_104]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^12_105]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^12_106]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^12_107]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^12_108]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^12_109]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^12_110]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^12_111]: https://docs.databricks.com/aws/en/developers/best-practices

[^12_112]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^12_113]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^12_114]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^12_115]: https://docs.databricks.com/aws/en/notebooks/testing

[^12_116]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^12_117]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^12_118]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^12_119]: https://docs.databricks.com/aws/en/files/files-recommendations

[^12_120]: https://docs.databricks.com/aws/en/files/workspace-modules

[^12_121]: https://docs.databricks.com/aws/en/release-notes/product/

[^12_122]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^12_123]: https://docs.databricks.com/aws/en/compute/web-terminal

[^12_124]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^12_125]: https://docs.databricks.com/gcp/en/files/workspace

[^12_126]: https://docs.databricks.com/aws/en/volumes/volume-files

[^12_127]: https://docs.databricks.com/aws/en/repos/ci-cd

[^12_128]: https://docs.databricks.com/aws/en/notebooks/share-code

[^12_129]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^12_130]: https://docs.databricks.com/aws/en/repos/limits

[^12_131]: https://docs.databricks.com/aws/en/files/workspace-interact

[^12_132]: https://docs.databricks.com/aws/en/jobs/git

[^12_133]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^12_134]: https://docs.databricks.com/api/jobs/v2/job

[^12_135]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^12_136]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^12_137]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^12_138]: https://docs.databricks.com/aws/en/repos/repos-setup

[^12_139]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^12_140]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^12_141]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^12_142]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^12_143]: https://docs.databricks.com/aws/en/tables/history

[^12_144]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^12_145]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^12_146]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^12_147]: https://docs.databricks.com/aws/en/files/workspace

[^12_148]: https://docs.databricks.com/aws/en/jobs/privileges

[^12_149]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^12_150]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^12_151]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^12_152]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^12_153]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^12_154]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^12_155]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^12_156]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^12_157]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^12_158]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^12_159]: https://docs.databricks.com/aws/en/ai-gateway/

[^12_160]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^12_161]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^12_162]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^12_163]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^12_164]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^12_165]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^12_166]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^12_167]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^12_168]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^12_169]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^12_170]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^12_171]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^12_172]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^12_173]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^12_174]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^12_175]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^12_176]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^12_177]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^12_178]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^12_179]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^12_180]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^12_181]: https://docs.databricks.com/aws/en/agents/

[^12_182]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^12_183]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^12_184]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^12_185]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^12_186]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^12_187]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^12_188]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^12_189]: https://docs.databricks.com/aws/en/machine-learning/

[^12_190]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^12_191]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^12_192]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^12_193]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^12_194]: https://www.hyperbots.com/glossary/sap-demand-planning

[^12_195]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^12_196]: https://www.ascm.org/topics/demand-supply-planning/

[^12_197]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^12_198]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^12_199]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^12_200]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^12_201]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^12_202]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^12_203]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^12_204]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^12_205]: https://o9solutions.com/articles/what-is-demand-planning

[^12_206]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^12_207]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^12_208]: https://keends.com/blog/demand-planning-kpis/

[^12_209]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^12_210]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^12_211]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^12_212]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^12_213]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^12_214]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^12_215]: https://imperiascm.com/blog/demand-forecasting-bias

[^12_216]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^12_217]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^12_218]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^12_219]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^12_220]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^12_221]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^12_222]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^12_223]: Red_Keychain_Supply_Planning_Requirements.md

[^12_224]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^12_225]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^12_226]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^12_227]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^12_228]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^12_229]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^12_230]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^12_231]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^12_232]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^12_233]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^12_234]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^12_235]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^12_236]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^12_237]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^12_238]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^12_239]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^12_240]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^12_241]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^12_242]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^12_243]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^12_244]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^12_245]: https://www.milwaukeetool.jobs/career-areas

[^12_246]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^12_247]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^12_248]: https://dataintelo.com/report/global-milwaukee-tool-market

[^12_249]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^12_250]: https://www.milwaukeetool.com/

[^12_251]: https://www.oracle.com/customers/milwaukee-tool/

[^12_252]: https://www.ttigroup.com/documents/annual-report-2025/

[^12_253]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^12_254]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^12_255]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^12_256]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^12_257]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^12_258]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^12_259]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^12_260]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^12_261]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^12_262]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^12_263]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^12_264]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^12_265]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^12_266]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^12_267]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^12_268]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^12_269]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^12_270]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^12_271]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^12_272]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^12_273]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^12_274]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^12_275]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^12_276]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^12_277]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^12_278]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^12_279]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^12_280]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^12_281]: https://www.hyperbots.com/glossary/target-gap-analysis

[^12_282]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^12_283]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^12_284]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^12_285]: https://www.ibm.com/think/topics/variance-analysis

[^12_286]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^12_287]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^12_288]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^12_289]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^12_290]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^12_291]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^12_292]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^12_293]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^12_294]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^12_295]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/

[^12_296]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^12_297]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^12_298]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^12_299]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^12_300]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^12_301]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^12_302]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^12_303]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^12_304]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^12_305]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^12_306]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^12_307]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^12_308]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^12_309]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^12_310]: https://docs.databricks.com/api/genie/v1/conversation

[^12_311]: https://docs.databricks.com/api/genie/v1

[^12_312]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^12_313]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^12_314]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^12_315]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^12_316]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^12_317]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^12_318]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^12_319]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^12_320]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^12_321]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^12_322]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^12_323]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^12_324]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^12_325]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^12_326]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^12_327]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^12_328]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^12_329]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^12_330]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^12_331]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^12_332]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^12_333]: https://docs.databricks.com/aws/en/oltp/projects/high-availability

[^12_334]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^12_335]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-node

[^12_336]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime

[^12_337]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-apps

[^12_338]: https://docs.databricks.com/gcp/en/agents/custom-agents/debug-agent

[^12_339]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/deploy

[^12_340]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices

[^12_341]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/key-concepts

[^12_342]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets

[^12_343]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/connect-local

[^12_344]: https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial

[^12_345]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/view-app-details

[^12_346]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api

[^12_347]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/model-serving

[^12_348]: https://docs.databricks.com/api/model-serving/v1/serving-endpoint

[^12_349]: https://docs.databricks.com/api/jobs/v2/run

[^12_350]: https://docs.databricks.com/aws/en/machine-learning/model-serving/store-env-variable-model-serving

[^12_351]: https://docs.databricks.com/gcp/en/machine-learning/model-serving/manage-serving-endpoints

[^12_352]: https://docs.databricks.com/aws/en/oltp/projects/automate-with-terraform

[^12_353]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/

[^12_354]: https://www.holistics.io/blog/the-three-types-of-fact-tables/

[^12_355]: https://www.databricks.com/blog/five-simple-steps-for-implementing-a-star-schema-in-databricks-with-delta-lake

[^12_356]: https://www.kimballgroup.com/2003/03/declaring-the-grain/

[^12_357]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-4-complex-fact-table-patterns/accumulating-snapshot-fact-tables

[^12_358]: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering

[^12_359]: https://www.kimballgroup.com/2008/11/fact-tables/

[^12_360]: https://www.kimballgroup.com/2012/05/design-tip-145-time-stamping-accumulating-snapshot-fact-tables/

[^12_361]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^12_362]: https://dev.to/alexmercedcoder/dimensional-modeling-facts-dimensions-and-grains-3obm

[^12_363]: https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/

[^12_364]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/

[^12_365]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/

[^12_366]: https://www.linkedin.com/posts/jrlasak\_%F0%9D%97%9F%F0%9D%97%B6%F0%9D%97%BE%F0%9D%98%82%F0%9D%97%B6%F0%9D%97%B1-%F0%9D%97%96%F0%9D%97%B9%F0%9D%98%82%F0%9D%98%80%F0%9D%98%81%F0%9D%97%B2%F0%9D%97%BF%F0%9D%97%B6%F0%9D%97%BB%F0%9D%97%B4-%F0%9D%98%83%F0%9D%98%80-%F0%9D%97%AD-%F0%9D%97%A2%F0%9D%97%BF%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF-activity-7445032276314238976-c6EB

[^12_367]: https://kimballgroup.forumotion.net/t1496-difference-between-factless-fact-and-bridge-table

[^12_368]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/

[^12_369]: https://bigbear.ai/blog/bridge-tables-deep-dive/

[^12_370]: https://www.reddit.com/r/dataengineering/comments/1pbro6t/kimball_confusion_semi_additive_vs_fully_additive/

[^12_371]: https://datadef.io/guides/en/dimensional-modeling

[^12_372]: https://www.kimballgroup.com/2012/02/design-tip-142-building-bridges/

[^12_373]: https://docs.thoughtspot.com/cloud/26.8.0.cl/semi-additive-measures.html

[^12_374]: https://www.kimballgroup.com/2005/12/the-matrix-revisited/

[^12_375]: https://community.sisense.com/forum/how-tos-faqs-43/topic/many-to-many-multivalued-dimension-4698/

[^12_376]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-2-dimensional-modeling-core/fact-tables-fundamentals

[^12_377]: https://arxiv.org/html/2606.27571v2

[^12_378]: https://datawarehouseinfo.com/practice/advanced-dimensional-modeling/

[^12_379]: https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables

[^12_380]: https://talkingschema.ai/docs/glossary/conformed-dimension

[^12_381]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions

[^12_382]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins

[^12_383]: https://docs.databricks.com/aws/en/ldp/dbsql/materialized

[^12_384]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/yaml-reference

[^12_385]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/create

[^12_386]: https://docs.databricks.com/aws/en/ldp/cdc

[^12_387]: https://docs.databricks.com/sap/en/release-notes/sql

[^12_388]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/basic-modeling

[^12_389]: https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables

[^12_390]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints

[^12_391]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select

[^12_392]: https://www.linkedin.com/pulse/understanding-medallion-architecture-databricks-bronze-chaudhari-rsrmf

[^12_393]: https://community.databricks.com/t5/community-articles/medallion-architecture-in-practice-the-design-decisions-nobody/td-p/163206

[^12_394]: https://community.databricks.com/t5/data-engineering/medallion-architecture-and-databricks-assistant/td-p/102301

[^12_395]: https://erstudio.com/blog/understanding-the-three-layers-of-medallion-architecture/

[^12_396]: https://erstudio.com/blog/how-medallion-architecture-with-er-studio-and-databricks-solves-data-as-a-product-for-both-business-and-it/

[^12_397]: https://cosmosthrace.com/resources/databricks/databricks-medallion-architecture-best-practices

[^12_398]: https://www.databricks.com/blog/what-is-medallion-architecture

[^12_399]: https://www.reddit.com/r/databricks/comments/1c93t94/medallion_architecture/

[^12_400]: https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825

[^12_401]: https://tacnode.io/post/medallion-architecture

[^12_402]: https://community.databricks.com/t5/data-engineering/medallion-architecture-do-i-need-a-materialized-exploded-layer/td-p/139085

[^12_403]: https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion

[^12_404]: https://www.reddit.com/r/databricks/comments/1j0gyd5/best_practices_for_medallion_architecture_in/

[^12_405]: https://docs.databricks.com/aws/en/lakehouse/medallion

[^12_406]: https://www.reddit.com/r/databricks/comments/173p6ev/bronzesilvergold_what_really_happens_in_each/


---

# Now, I have done some past work that I will be providing the details to you. Use those for reference, not for loosing your course and just following some mistake, if it is or irrespective!!

Understood. I will treat your past work as **evidence and reference material—not as instructions to copy its architecture or repeat its assumptions**.

## Evaluation approach

For each past artifact, I will separate:


| Category | How it will be used |
| :-- | :-- |
| Business knowledge | Preserve terminology, workflows and validated business rules |
| Confirmed facts | Reuse only after checking they remain applicable |
| Data discoveries | Validate tables, columns, grain, coverage and authority in the current workspace |
| Useful patterns | Adopt when they support the current use case |
| Candidate ideas | Evaluate independently before adoption |
| Technical implementation | Review against current Databricks capabilities and project constraints |
| Workarounds | Determine whether the underlying limitation still exists |
| Mistakes and dead ends | Record as lessons, not reproduce |
| Hard-coded assumptions | Replace with configuration or explicit decisions |
| Out-of-scope capabilities | Do not allow them to expand the approved scope |

## Governing precedence

When information conflicts, I will use this order:

1. **Latest customer scope and priority correction.**
2. **Current business-owner clarification.**
3. **Current Milwaukee use-case acceptance criteria.**
4. **Validated current workspace data and platform behavior.**
5. **Latest official Databricks guidance and supported capabilities.**
6. **Current requirement documents.**
7. **Past Milwaukee work and artifacts.**
8. **General industry patterns.**
9. **Assumptions requiring confirmation.**

Therefore, older work cannot reintroduce PO Exceptions or PO actions merely because they were previously developed or documented.

## Review output

When you provide past work, I will classify the findings as:

- **Reuse as-is:** current, correct and directly applicable.
- **Reuse conceptually:** valuable idea, but implementation should change.
- **Refactor:** correct intent but weak structure, performance, security or maintainability.
- **Validate first:** plausible but unproven against current data.
- **Superseded:** replaced by newer Databricks capability or customer requirement.
- **Reject:** incorrect, unsafe, unnecessary or out of scope.
- **Archive as lesson:** useful only for avoiding a repeated mistake.


## Guardrail

Past implementation will not automatically determine:

- Medallion layers.
- Target grains.
- Fact and dimension design.
- Join strategy.
- SQL versus PySpark.
- Streaming versus batch.
- Lakeflow dataset types.
- Genie structure.
- Dashboard layout.
- App architecture.
- Lakebase transaction model.
- Authentication method.
- DAB and CI/CD scope.
- Model Serving strategy.
- Exception rules.

Those decisions will come from the current use case, data behavior, platform capabilities and acceptance criteria.

## Expected benefit

Past work can accelerate the project by revealing:

- Already-discovered source tables and keys.
- Existing SQL and profiling knowledge.
- Business vocabulary.
- Previously tested metrics.
- Planner feedback.
- Known data-quality problems.
- Authentication and permission pitfalls.
- Performance bottlenecks.
- UI patterns that users liked or rejected.
- Deployment and integration lessons.

But every reuse decision will answer:

> **Does this help the current P1–P4 use cases, and can it be validated in the present Milwaukee Databricks environment?**

That will keep us from either discarding valuable work or blindly inheriting its mistakes.

---

# Here's the most recent chat/history of the work that I have been doing.

Again, learn from it, learn from what I am trying to ask, where I need help and all!

Understood. I have reviewed the recent history as a record of your **goals, working style, architectural reasoning, frustrations, unresolved questions, and prior experiments**—not as an implementation specification that must be copied.

The strongest lesson is that you need an assistant that can simultaneously preserve project continuity, question weak assumptions, use Databricks effectively, understand supply planning, and remain honest about what has actually been verified.

## What you expect

You do not want a code generator that immediately creates notebooks, tables, dashboards, or an App. You want help moving through this progression:

```text
Business question
    → domain interpretation
    → requirement authority
    → source discovery
    → metadata and data profiling
    → grain and semantic validation
    → architecture
    → Silver contracts
    → Gold products
    → dashboard / Genie / App
    → QA and reconciliation
    → user acceptance
    → production promotion
```

The history repeatedly shows that you value **learning and validating before construction**, while still expecting tangible progress rather than endless analysis.[^14_1]

## Your working principles

I have extracted these as your operating preferences:

- Use all available project knowledge, but do not blindly inherit earlier mistakes.
- Read complete source materials rather than trusting partial copies or summaries.
- Distinguish customer requirements from internal proposals and generated ideas.
- Do not invent Milwaukee business rules to fill unanswered questions.
- Do not label something complete merely because code ran successfully.
- Develop interactively in the Databricks workspace first when that is efficient.
- Use supported Databricks features rather than writing unnecessary frameworks.
- Use DABs and CI/CD when assets become reusable or production-relevant—not for every exploratory notebook.
- Reuse P1 work in P2, and P3 work in P4, without collapsing the priorities into one model.
- Match the Databricks product to the user’s job rather than assuming every persona needs an App.
- Preserve the distinction between a prototype, internal mimic, Milwaukee workspace validation, UAT, and production.
- Make authentication, permissions and networking part of the design from the beginning.

The history also shows that you want parallel work where dependencies allow it, while preserving true gates such as profiling before conformance and conformance before trusted Gold.[^14_1]

## Domain understanding

The history reinforces that these priorities have different business questions and time directions:


| Priority | Primary question | Time orientation | Natural grain |
| :-- | :-- | :-- | :-- |
| P1 Actuals Supply Plan | What did the frozen plan say, what happened, and why is there variance? | Backward-looking | Item × organization × week × plan vintage × metric |
| P2 Supply Exceptions | What future supply condition requires attention? | Forward-looking | Exception type × item × organization × horizon × rule version |
| P3 Demand Events | What incremental demand should be created, approved and published? | Planning/publication lifecycle | Event × version × item × customer × month |
| P4 Demand Exceptions | Why might the demand number be unreliable or require planner action? | Forward-looking and evaluative | Demand exception × item/customer/time × forecast vintage |

These products share dimensions and platform capabilities, but they should not share one giant Gold fact. The history correctly identifies that Actuals, supply exceptions and demand events have different grains, state models and “time arrows.”[^14_1]

## P1 lessons

Several P1 principles from the history are technically and analytically important:

- **Plan snapshots are versioned:** `processdate` represents the plan vintage and should normally be filtered before large joins.
- **Flow and stock differ:** receipts, shipments and demand are flows that may be aggregated across a week; on-hand and projected available balance are point-in-time or semi-additive measures.
- **Missing is not zero:** plan-only and actual-only combinations should remain visible.
- **Zero-plan variance is undefined:** it should not become infinity or a misleading zero percentage.
- **Receipts have competing sources:** differences between RCV and purchase-order delivery must be profiled and reconciled before selecting an authoritative metric.
- **Joining is a business contract:** item, organization, date/week, series, PO bridge and UOM mappings require explicit validation.
- **A successful pipeline is not business acceptance:** at least one named SKU–organization–week must reconcile against trusted Milwaukee evidence.

The history reports that a P1 prototype was built in an internal mimic, including Silver/Gold assets, an `actualsweekly` job and an AI/BI dashboard. I will treat that as **historical reported state requiring workspace verification**, not as independently proven current state or Milwaukee acceptance.[^14_1]

## P1 is broader

The history discovered that “Actuals Supply Plan” is not only one weekly comparison grid. It includes at least three related capabilities:


| Capability | Business purpose |
| :-- | :-- |
| Frozen plan versus ERP actuals | Determine whether last week’s approved plan happened |
| Current/live plan versus prior frozen plan | Understand what changed between planning snapshots |
| PO-line timing performance | Evaluate requested/confirmed/receipt timing at PO-line grain |

Those capabilities may share sources and dimensions, but PO-line timing cannot be truthfully produced from only an item-organization-week aggregate.[^14_1]

This does **not** reintroduce PO Exceptions. PO receipt timing can remain part of P1 performance analysis while PO exception queues, pull-in/push-out recommendations and PO-changing actions remain out of scope.

## Surface selection

One of the strongest insights from the history is:

> **Match the surface to the verb.**


| User need | Default Databricks surface |
| :-- | :-- |
| Look, compare, filter and investigate | AI/BI dashboard |
| Ask governed analytical questions | Dashboard companion Genie or focused App Genie |
| Inspect rows and validate calculations | Databricks SQL and notebooks |
| Rerun, backfill and monitor data production | Lakeflow Jobs/pipelines |
| Enter, edit, lock, activate or disposition | Databricks App |
| Persist transactional workflow state | Lakebase |
| Govern shared calculations | Metric views and certified Gold data |
| Train and evaluate a challenger forecast | MLflow and governed training pipelines |
| Serve predictions or agents | Model Serving and Unity AI Gateway |
| Execute a live operational action | Typed, authorized tool with approval and audit |

Therefore:

- P1 is initially dashboard-centric, with Genie available for governed follow-up analysis.
- P2 begins with exception analytics but naturally benefits from an App when assignment, disposition and comments are required.
- P3 is App-first because event creation, editing, locking, activation and publication are transactional.
- P4 should not receive an impressive interface before its exception semantics and rules are validated.

The prior history reached the same general conclusion: an App is necessary when the user changes state, but it should not become a second calculation engine that disagrees with Gold.[^14_1]

## Genie interpretation

Your newer direction expands the earlier history: Genie must be available in both the AI/BI dashboards and the Agentic AI App.

I will use this model:

- Each dashboard receives a focused companion Genie experience.
- Each App module receives a focused Genie Agent.
- Both are grounded in the same metric views and certified Gold products.
- The App explicitly provides selected item, organization, week, event or exception context.
- Genie explains and investigates.
- Typed application services perform writebacks and live actions.
- Genie is evaluated with expected questions, expected SQL, numerical reconciliation and refusal tests.
- Genie does not silently become the source of business metrics or unrestricted operational commands.


## Forecasting interpretation

The history contains an important distinction: Milwaukee already has demand- and supply-planning outputs. P1 should first evaluate existing plan outputs rather than train a replacement model simply to demonstrate ML.[^14_1]

New Databricks forecasting should normally enter as:

1. A baseline or challenger to the existing forecast.
2. A component of P4 demand-exception detection.
3. A scenario or forecast-building aid for P3.
4. A monitored model whose results remain distinct from the approved system-of-record plan.
5. A model promoted only after time-based evaluation and business acceptance.

I will not allow a new model’s output to overwrite or masquerade as an approved demand plan.

## Prior assets

The history identifies several categories of past work:

- Requirement documents and derived BRD/FRD/TSD materials.
- Source inventories and Unity Catalog discovery.
- Compact-schema captures and metadata.
- Proposed join maps and data contracts.
- An internal workspace mimic of Milwaukee object names.
- Development fixtures for specific P1 edge cases.
- P1 Silver and Gold designs.
- A reported P1 job and dashboard.
- Lakebase DDL and App concepts.
- Exception and event designs.
- Workspace development and authentication setup.
- Databricks-specific skills and operating instructions.[^14_1]

I will evaluate these with the following evidence levels:


| Level | Meaning |
| :-- | :-- |
| Mentioned | An object or rule appears in a document |
| Discovered | Its current existence was observed |
| Accessible | An identity successfully accessed it |
| Profiled | Schema and meaningful data behavior were examined |
| Semantically validated | Business meaning, grain and treatment were confirmed |
| Accepted for prototype | Approved for a bounded demonstration |
| Reconciled | Results matched trusted business evidence |
| UAT accepted | Intended users approved the workflow |
| Production approved | Security, reliability and operating requirements passed |

A schema captured in an old chat is **not automatically current metadata**. A generated mimic table is **not a Milwaukee source**, and a successful job run is **not business reconciliation**.

## Recurring mistakes

The history gives useful warnings that I will retain:

- Reading incomplete requirement copies and treating missing sections as missing requirements.
- Building a broad inventory and accidentally treating every discovered object as in scope.
- Creating shape-compatible stub tables without clearly distinguishing them from fully captured schemas.
- Treating agent-reported row counts as validated current facts.
- Overstating completion because notebooks, jobs or dashboards exist.
- Allowing an App or dashboard to recompute business metrics.
- Introducing attractive features before trusted Gold data exists.
- Treating proposed KPI thresholds as Milwaukee policy.
- Summing inventory snapshots across time.
- Choosing one receipt source silently.
- Full-scanning extremely large planning tables without early filters.
- Confusing demand accuracy with supply-plan execution.
- Treating P1 supply variance as a P4 demand exception.
- Allowing older APOM/PO concepts to leak back into the corrected scope.
- Debugging authentication by trying random credentials rather than identifying the target, actor, protocol and running process.

These are lessons to prevent recurrence—not fixed rules that prohibit better approaches when current evidence supports them.

## Where you need help

Your most important need is not additional code-writing capacity. It is **decision-quality engineering support** across several boundaries:

### Requirement authority

You need help identifying which customer statement is current, what has been superseded, and what remains only an internal idea.

### Domain semantics

You need support distinguishing plan from actual, snapshot from transaction, stock from flow, demand exception from supply exception, and analytical state from transactional state.

### Evidence management

You need every claim labeled so that “found in a chat,” “seen in a mimic,” “profiled in Milwaukee,” and “accepted by the planner” never become interchangeable.

### Databricks product judgment

You need someone to choose among SQL, PySpark, Lakeflow, Jobs, dashboards, Genie, Apps, Lakebase, Model Serving, Unity AI Gateway, notebooks, bundles and APIs according to the use case.

### Platform reliability

You need authentication, service principals, profiles, OAuth, permissions, host selection, workspace assignment, warehouse access and process restarts handled methodically, without wasting project time.

### Product completion

You need more than successful pipelines: use-case acceptance, reconciliation, semantic consistency, Genie accuracy, transactional integrity, operational monitoring and user satisfaction.

## Course corrections

Some older conclusions will now be adjusted to match the latest conversation:

- Genie is no longer merely optional after the dashboard; it is an explicit deliverable in dashboards and the App, but still depends on trusted semantics.
- The end-state App is explicitly an Agentic AI supply-chain App with Lakebase writebacks and governed live actions.
- DABs and CI/CD are part of promotion, but workspace-first development remains the preferred early loop.
- Platform, network and authentication design are mandatory deliverables.
- P1–P4 remain the priority framework, with opportunities for parallel shared-foundation work.
- PO Exceptions remain excluded despite older Red Keychain designs.
- The past internal mimic and P1 prototype are reference implementations—not proof of current workspace state or customer acceptance.


## Default behavior

When you give me the next artifact or development task, I will:

1. Identify its authority, date, environment and relationship to P1–P4.
2. Separate facts, assumptions, proposals, historical decisions and generated content.
3. Extract useful domain and technical knowledge.
4. Compare it against the latest requirements and scope.
5. Validate current workspace facts before acting on historical claims.
6. State what is reusable, questionable, superseded or still unverified.
7. Recommend the smallest valuable next step.
8. Develop in the authorized workspace when appropriate.
9. Preserve reusable logic and a promotion path.
10. Report status honestly as designed, implemented, tested, reconciled or accepted.

The history is now a **project-learning source and behavioral guide**. It will improve continuity and prevent repeated mistakes, but it will not be allowed to overrule current customer scope, present workspace evidence, sound supply-chain semantics or better Databricks engineering.

<div align="center">⁂</div>

[^14_1]: cursor_databricks_project_upload_cleanu.md


---

# Also, understand the limitations and drawbacks of ... let's say using SDPs , or notebooks. or workflows or jobs. .. as an example, we don't need to use SDP everywhere, but also, we don't need to not use it! so, based on the domain, and the project and the requirement, think where it sits fit rather than blind development!

and it is not limited to just this. it is for everything! design choices, product choices and many other things ..
Understand my intentions and expand the hoizons of my question into different dimensions and then think about it, get the right resources and then build an understanding and tell me!

You are asking for something broader than knowledge of Databricks products: **architecture judgment**. The development pattern should understand each business requirement, evaluate competing designs, recognize product limitations, and choose the smallest suitable solution—not reflexively select Spark Declarative Pipelines, notebooks, Jobs, Lakebase, Apps, or AI.

I have created a detailed **Fit-for-Purpose Databricks Decision Framework** covering these choices and their trade-offs.

## Intention understood

The default behavior will now be:

> **Business decision → domain semantics → data behavior → nonfunctional requirements → alternatives → trade-offs → product selection → workspace prototype → evidence → production promotion.**

It will **not** be:

> Requirement → fashionable Databricks product → implementation.

Nor will it be:

> Familiar Python/notebook pattern → force every requirement into it.

## SDP is conditional

Spark Declarative Pipelines—implemented on Databricks through Lakeflow pipelines—are a strong choice when the product is a maintained dataset involving incremental batch, streaming, CDC, managed data quality, or declarative dependency management. They are not automatically the best choice for profiling, one-time reconciliation, transactional writebacks, external API actions, human approvals, or side-effect-heavy processing.[^15_1][^15_2]

Pipeline definitions are evaluated multiple times and should principally return DataFrames; arbitrary side effects and writes inside dataset definitions can cause unexpected behavior. Pipelines also have concrete constraints—for example, a dataset can normally have only one defining operation, `pivot()` is unsupported, and materialized views do not support time-travel queries.[^15_3][^15_1]

Therefore, SDP may fit one portion of a use case without owning all of it:

- **P1 Actuals:** possibly incremental Silver/Gold maintenance after semantics stabilize.
- **P2 Supply Exceptions:** potentially append-only rule-evaluation publication, but not necessarily rule administration or disposition workflow.
- **P3 Demand Events:** perhaps publication from approved Lakebase state into Delta, but not event editing, locking, approval, or transactional behavior.
- **P4 Demand Exceptions:** potentially forecast preparation and incremental exception outputs, but only after the exception taxonomy is defined.


## Jobs are orchestration

Lakeflow Jobs are appropriate when heterogeneous operations need sequencing: profiling, validation, pipelines, SQL, ML training, publication, notifications, conditional branches, retries, or external calls. Jobs can run notebook, Python, SQL, dbt, JAR, and pipeline tasks, with dependencies and conditional control flow.[^15_4][^15_5]

However, I will not use a giant Job DAG to compensate for unclear data products. Nor will I use retries around a non-idempotent live action and assume that makes the operation reliable.

The separation will be:

- **Pipeline:** “What datasets should be maintained?”
- **Job:** “What work must run, in what order, under which conditions?”
- **Lakebase/App:** “What transactional state changes under user or agent interaction?”
- **Action service:** “What governed external operation must be executed and verified?”


## Notebooks have a role

Notebooks are valuable for:

- Source discovery.
- Business-semantic exploration.
- Profiling.
- One-SKU or one-week vertical slices.
- Reconciliation.
- Interactive debugging.
- Demonstrations and evidence.
- Thin development entry points.

They become problematic when they accumulate hidden state, duplicated transformations, manual execution order, inline secrets, mixed exploration and production logic, or calculations that cannot be unit-tested.

Databricks recommends moving reusable logic into source-controlled Python modules and SQL files while using notebooks primarily as thin orchestration and visualization layers.[^15_6][^15_7]

Therefore, the policy is:

> **Notebook-first may be appropriate; notebook-only production architecture usually is not.**

## Product responsibility

The correct product depends heavily on the user’s business verb:


| Business need | Likely starting point | Usually unsuitable |
| :-- | :-- | :-- |
| Explore and reconcile | SQL or notebook | Production App |
| Maintain incremental tables | SDP/Lakeflow pipeline | Transactional App logic |
| Sequence heterogeneous operations | Lakeflow Job | One giant pipeline |
| Compare Actual versus Plan | Gold model + dashboard | Lakebase as warehouse |
| Ask governed questions | Focused Genie Agent | Unbounded enterprise Agent |
| Enter or edit events | App + Lakebase | Dashboard |
| Approve and execute actions | App + typed action service | Direct Genie writeback |
| Train periodic forecasts | Job + MLflow | Always-on endpoint by default |
| Serve interactive inference | Model Serving | Batch-only process |
| Standardize metrics | Metric View | Repeating formulas per dashboard |
| Discover remote EDW data | Federation | High-volume permanent serving |
| Deploy repeatably | Bundle + CI/CD | Manual production copying |

## Lakebase versus Delta

Lakebase will hold mutable transactional state such as event edits, assignments, comments, locks, approvals, idempotency records, and action status. Delta will hold large-scale history, plan snapshots, Actuals, forecast vintages, exception evaluations, features, and analytical outcomes.

A Lakebase database exposed through Unity Catalog is currently read-only through Unity Catalog queries and requires a serverless SQL warehouse. This reinforces an important separation: writebacks use PostgreSQL/App transactions; analytical consumption can use governed lakehouse access.[^15_8]

I will not:

- Duplicate the EDW in Lakebase.
- Use Delta tables as an improvised concurrent approval database.
- Let an Agent issue unrestricted SQL updates.
- Confuse an application transaction with an analytical pipeline update.


## Federation versus ingestion

Federation is useful for discovery and bounded live access without initially copying data. But federated queries are read-only, do not receive Databricks result/disk caching, can affect the remote system, and may have performance or memory limitations when large results travel through the connection.[^15_9]

Ingestion or CDC becomes preferable when the use case needs:

- Repeated high-volume access.
- Historical reconstruction.
- Stable analytical performance.
- Isolation from the operational source.
- Resilience to source downtime.
- Data-quality remediation.
- Long-term versioning.

Pushdown behavior also depends on the remote engine and query shape, so I will inspect the physical query plan rather than assume a federated join or filter executes remotely.[^15_10]

## Metric Views

Metric Views are appropriate when measures such as Plan Attainment, Supply Plan Variance, Receipt Performance, Shipment Performance, and Forecast Accuracy need governed reuse across dashboards, Genie, Apps, and SQL.

They are not a universal substitute for Gold tables. Metric Views have limitations around profiling, downstream joins, and how measures must be queried.[^15_11][^15_12][^15_13]

The normal layering will therefore be:

```text
Gold fact/view with record-level evidence
                  ↓
Governed Metric View
                  ↓
Dashboard / Genie / App
```


## Agent and ML discipline

An Agent may:

- Investigate an exception.
- Retrieve evidence.
- Explain likely causes.
- Compare scenarios.
- Recommend actions.
- Invoke validated tools.

An Agent should not independently define a business metric, improvise transaction semantics, or bypass authorization. Calculations, approvals, Lakebase mutations, and operational actions remain deterministic and typed.

Similarly, P1 Actuals does not need an ML model simply because forecasting is planned elsewhere. Forecasting belongs where prediction changes a decision and can outperform an accepted baseline—likely P4 or a subsequent planning capability after forecast vintage, true demand, segmentation, and evaluation horizons are trustworthy.

## Expanded evaluation

Every significant decision will be examined across:

- Business outcome and decision.
- Domain grain and time orientation.
- Plan version or forecast vintage.
- Stock, flow, snapshot, event, or transaction behavior.
- Append, correction, CDC, late-arriving, and deletion semantics.
- Latency and freshness.
- User concurrency and state.
- Failure, retry, idempotency, and compensation.
- Reconciliation and data-quality contracts.
- Security and Unity Catalog authorization.
- User versus service-principal identity.
- Network route, DNS, firewall, and source-system load.
- Performance and cost.
- Development speed.
- Testing and deployment maturity.
- Operability and ownership.
- Portability and product lock-in.
- Product limitations and roadmap risk.


## Decision evidence

For important design choices, I will provide a short architecture decision record containing:

1. Business decision being supported.
2. Domain semantics and grain.
3. Functional and nonfunctional requirements.
4. Options considered.
5. Recommended option.
6. Why it fits.
7. Drawbacks and accepted risks.
8. Rejected or deferred alternatives.
9. Security, networking, cost, and operational effects.
10. Testing and validation required.
11. Conditions that would cause reconsideration.

Recommendations will carry an evidence status:

- **Validated**
- **Preferred with assumptions**
- **Prototype choice**
- **Blocked pending evidence**
- **Rejected**


## Project application

For the Milwaukee priorities, the current likely—not final—technology posture is:


| Priority | Likely initial posture |
| :-- | :-- |
| P1 Actuals | Profile with notebooks/SQL; build aligned Silver and Gold models; orchestrate with a Job; dashboard and companion Genie; consider SDP after incremental behavior and semantics are validated |
| P2 Supply Exceptions | Versioned deterministic rules; append-only evidence; Job or pipeline depending on cadence; dashboard first; Lakebase/App when case disposition begins |
| P3 Demand Events | Databricks App + Lakebase for edits, locking, and approvals; Delta for publication history; Job/pipeline for validated publication |
| P4 Demand Exceptions | Discover real rules first; preserve forecast vintage; implement deterministic baseline; add ML only when it demonstrably improves decisions |

This is deliberately provisional. Final decisions must reflect the actual Milwaukee data, existing platform resources, operating model, release standards, and constraints.

## Governing rule

The expanded development pattern is now:

> **Do not choose a Databricks product because it is available, modern, or familiar. Do not reject it merely because a simpler prototype can initially work. Select based on the business responsibility, domain semantics, data and state behavior, maturity, operational obligations, and measured evidence. Use workspace-first development to learn quickly; promote only the parts that become reusable, governed, scheduled, shared, SLA-backed, or production-impacting.**

That principle will apply to everything: languages, pipelines, notebooks, Jobs, data models, compute, federation, ingestion, dashboards, Genie, Apps, Lakebase, ML, Agents, Model Serving, AI Gateway, bundles, CI/CD, authentication, and networking.

<span style="display:none">[^15_100][^15_101][^15_102][^15_103][^15_104][^15_105][^15_106][^15_107][^15_108][^15_109][^15_110][^15_111][^15_112][^15_113][^15_114][^15_115][^15_116][^15_117][^15_118][^15_119][^15_120][^15_121][^15_122][^15_123][^15_124][^15_125][^15_126][^15_127][^15_128][^15_129][^15_130][^15_131][^15_132][^15_133][^15_134][^15_135][^15_136][^15_137][^15_138][^15_139][^15_14][^15_140][^15_141][^15_142][^15_143][^15_144][^15_145][^15_146][^15_147][^15_148][^15_149][^15_15][^15_150][^15_151][^15_152][^15_153][^15_154][^15_155][^15_156][^15_157][^15_158][^15_159][^15_16][^15_160][^15_161][^15_162][^15_163][^15_164][^15_165][^15_166][^15_167][^15_168][^15_169][^15_17][^15_170][^15_171][^15_172][^15_173][^15_174][^15_175][^15_176][^15_177][^15_178][^15_179][^15_18][^15_180][^15_181][^15_182][^15_183][^15_184][^15_185][^15_186][^15_187][^15_188][^15_189][^15_19][^15_190][^15_191][^15_192][^15_193][^15_194][^15_195][^15_196][^15_197][^15_198][^15_199][^15_20][^15_200][^15_201][^15_202][^15_203][^15_204][^15_205][^15_206][^15_207][^15_208][^15_209][^15_21][^15_210][^15_211][^15_212][^15_213][^15_214][^15_215][^15_216][^15_217][^15_218][^15_219][^15_22][^15_220][^15_221][^15_222][^15_223][^15_224][^15_225][^15_226][^15_227][^15_228][^15_229][^15_23][^15_230][^15_231][^15_232][^15_233][^15_234][^15_235][^15_236][^15_237][^15_238][^15_239][^15_24][^15_240][^15_241][^15_242][^15_243][^15_244][^15_245][^15_246][^15_247][^15_248][^15_249][^15_25][^15_250][^15_251][^15_252][^15_253][^15_254][^15_255][^15_256][^15_257][^15_258][^15_259][^15_26][^15_260][^15_261][^15_262][^15_263][^15_264][^15_265][^15_266][^15_267][^15_268][^15_269][^15_27][^15_270][^15_271][^15_272][^15_273][^15_274][^15_275][^15_276][^15_277][^15_278][^15_279][^15_28][^15_280][^15_281][^15_282][^15_283][^15_284][^15_285][^15_286][^15_287][^15_288][^15_289][^15_29][^15_290][^15_291][^15_292][^15_293][^15_294][^15_295][^15_296][^15_297][^15_298][^15_299][^15_30][^15_300][^15_301][^15_302][^15_303][^15_304][^15_305][^15_306][^15_307][^15_308][^15_309][^15_31][^15_310][^15_311][^15_312][^15_313][^15_314][^15_315][^15_316][^15_317][^15_318][^15_319][^15_32][^15_320][^15_321][^15_322][^15_323][^15_324][^15_325][^15_326][^15_327][^15_328][^15_329][^15_33][^15_330][^15_331][^15_332][^15_333][^15_334][^15_335][^15_336][^15_337][^15_338][^15_339][^15_34][^15_340][^15_341][^15_342][^15_343][^15_344][^15_345][^15_346][^15_347][^15_348][^15_349][^15_35][^15_350][^15_351][^15_352][^15_353][^15_354][^15_355][^15_356][^15_357][^15_358][^15_359][^15_36][^15_360][^15_361][^15_362][^15_363][^15_364][^15_365][^15_366][^15_367][^15_368][^15_369][^15_37][^15_370][^15_371][^15_372][^15_373][^15_374][^15_375][^15_376][^15_377][^15_378][^15_379][^15_38][^15_380][^15_381][^15_382][^15_383][^15_384][^15_385][^15_386][^15_387][^15_388][^15_389][^15_39][^15_390][^15_391][^15_392][^15_393][^15_394][^15_395][^15_396][^15_397][^15_398][^15_399][^15_40][^15_400][^15_401][^15_402][^15_403][^15_404][^15_405][^15_406][^15_407][^15_408][^15_409][^15_41][^15_410][^15_411][^15_412][^15_413][^15_414][^15_415][^15_416][^15_417][^15_418][^15_419][^15_42][^15_420][^15_421][^15_422][^15_423][^15_424][^15_425][^15_426][^15_43][^15_44][^15_45][^15_46][^15_47][^15_48][^15_49][^15_50][^15_51][^15_52][^15_53][^15_54][^15_55][^15_56][^15_57][^15_58][^15_59][^15_60][^15_61][^15_62][^15_63][^15_64][^15_65][^15_66][^15_67][^15_68][^15_69][^15_70][^15_71][^15_72][^15_73][^15_74][^15_75][^15_76][^15_77][^15_78][^15_79][^15_80][^15_81][^15_82][^15_83][^15_84][^15_85][^15_86][^15_87][^15_88][^15_89][^15_90][^15_91][^15_92][^15_93][^15_94][^15_95][^15_96][^15_97][^15_98][^15_99]</span>

<div align="center">⁂</div>

[^15_1]: https://docs.databricks.com/aws/en/jobs/

[^15_2]: https://docs.databricks.com/aws/en/jobs/control-flow

[^15_3]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^15_4]: https://docs.databricks.com/aws/en/ldp/

[^15_5]: https://docs.databricks.com/aws/en/ldp/limitations

[^15_6]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^15_7]: https://docs.databricks.com/aws/en/developers/best-practices

[^15_8]: https://docs.databricks.com/aws/en/dashboards/limits

[^15_9]: https://docs.databricks.com/gcp/en/dashboards/concepts

[^15_10]: https://docs.databricks.com/aws/en/dashboards/genie-spaces

[^15_11]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^15_12]: https://docs.databricks.com/aws/en/oltp/projects/manage-projects

[^15_13]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^15_14]: https://docs.databricks.com/gcp/en/query-federation/performance-recommendations

[^15_15]: https://docs.databricks.com/aws/en/query-federation/database-federation

[^15_16]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage

[^15_17]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^15_18]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^15_19]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^15_20]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^15_21]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^15_22]: https://docs.databricks.com/aws/en/jobs/compute

[^15_23]: https://docs.databricks.com/aws/en/jobs/run-serverless-jobs

[^15_24]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^15_25]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^15_26]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^15_27]: https://docs.databricks.com/aws/en/dev-tools/auth/pat

[^15_28]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^15_29]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^15_30]: https://docs.databricks.com/aws/en/ldp/concepts/

[^15_31]: https://docs.databricks.com/aws/en/jobs/jobs-quickstart

[^15_32]: https://docs.databricks.com/aws/en/ldp/real-time

[^15_33]: https://docs.databricks.com/aws/en/getting-started/best-practices

[^15_34]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^15_35]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^15_36]: https://docs.databricks.com/aws/en/resources/limits

[^15_37]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^15_38]: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations

[^15_39]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^15_40]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^15_41]: https://docs.databricks.com/gcp/en/query-federation/salesforce-data-cloud

[^15_42]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^15_43]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^15_44]: https://docs.databricks.com/aws/en/query-federation/snowflake

[^15_45]: https://docs.databricks.com/aws/en/query-federation/remote-queries

[^15_46]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^15_47]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^15_48]: https://docs.databricks.com/aws/en/ldp/concepts

[^15_49]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^15_50]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^15_51]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^15_52]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^15_53]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^15_54]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^15_55]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^15_56]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^15_57]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^15_58]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^15_59]: https://docs.databricks.com/aws/en/tables/clustering

[^15_60]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^15_61]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^15_62]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^15_63]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^15_64]: https://docs.databricks.com/aws/en/delta/tutorial

[^15_65]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^15_66]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^15_67]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^15_68]: https://docs.databricks.com/aws/en/mlflow/

[^15_69]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^15_70]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^15_71]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^15_72]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^15_73]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^15_74]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^15_75]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^15_76]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^15_77]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^15_78]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^15_79]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^15_80]: https://docs.databricks.com/gcp/en/languages/overview

[^15_81]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^15_82]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^15_83]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^15_84]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^15_85]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^15_86]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^15_87]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^15_88]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^15_89]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^15_90]: https://docs.databricks.com/aws/en/oltp/projects/

[^15_91]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^15_92]: https://docs.databricks.com/aws/en/dashboards/

[^15_93]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^15_94]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^15_95]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^15_96]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^15_97]: https://docs.databricks.com/aws/en/query-federation/oracle

[^15_98]: https://docs.databricks.com/aws/en/ldp/expectations

[^15_99]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^15_100]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^15_101]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^15_102]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^15_103]: https://docs.databricks.com/aws/en/query-federation/networking

[^15_104]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^15_105]: https://docs.databricks.com/aws/en/query-federation/databricks

[^15_106]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^15_107]: https://docs.databricks.com/gcp/en/developers/best-practices

[^15_108]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^15_109]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^15_110]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^15_111]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^15_112]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^15_113]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^15_114]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^15_115]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^15_116]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^15_117]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^15_118]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^15_119]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^15_120]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^15_121]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^15_122]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^15_123]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^15_124]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^15_125]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^15_126]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^15_127]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^15_128]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^15_129]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^15_130]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^15_131]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^15_132]: https://docs.databricks.com/aws/en/notebooks/testing

[^15_133]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^15_134]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^15_135]: https://docs.databricks.com/aws/en/files/files-recommendations

[^15_136]: https://docs.databricks.com/aws/en/files/workspace-modules

[^15_137]: https://docs.databricks.com/aws/en/release-notes/product/

[^15_138]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^15_139]: https://docs.databricks.com/aws/en/compute/web-terminal

[^15_140]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^15_141]: https://docs.databricks.com/gcp/en/files/workspace

[^15_142]: https://docs.databricks.com/aws/en/volumes/volume-files

[^15_143]: https://docs.databricks.com/aws/en/repos/ci-cd

[^15_144]: https://docs.databricks.com/aws/en/notebooks/share-code

[^15_145]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^15_146]: https://docs.databricks.com/aws/en/repos/limits

[^15_147]: https://docs.databricks.com/aws/en/files/workspace-interact

[^15_148]: https://docs.databricks.com/aws/en/jobs/git

[^15_149]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^15_150]: https://docs.databricks.com/api/jobs/v2/job

[^15_151]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^15_152]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^15_153]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^15_154]: https://docs.databricks.com/aws/en/repos/repos-setup

[^15_155]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^15_156]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^15_157]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^15_158]: https://docs.databricks.com/aws/en/tables/history

[^15_159]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^15_160]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^15_161]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^15_162]: https://docs.databricks.com/aws/en/files/workspace

[^15_163]: https://docs.databricks.com/aws/en/jobs/privileges

[^15_164]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^15_165]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^15_166]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^15_167]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^15_168]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^15_169]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^15_170]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^15_171]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^15_172]: https://docs.databricks.com/aws/en/ai-gateway/

[^15_173]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^15_174]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^15_175]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^15_176]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^15_177]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^15_178]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^15_179]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^15_180]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^15_181]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^15_182]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^15_183]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^15_184]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^15_185]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^15_186]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^15_187]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^15_188]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^15_189]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^15_190]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^15_191]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^15_192]: https://docs.databricks.com/aws/en/agents/

[^15_193]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^15_194]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^15_195]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^15_196]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^15_197]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^15_198]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^15_199]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^15_200]: https://docs.databricks.com/aws/en/machine-learning/

[^15_201]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^15_202]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^15_203]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^15_204]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^15_205]: https://www.hyperbots.com/glossary/sap-demand-planning

[^15_206]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^15_207]: https://www.ascm.org/topics/demand-supply-planning/

[^15_208]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^15_209]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^15_210]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^15_211]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^15_212]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^15_213]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^15_214]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^15_215]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^15_216]: https://o9solutions.com/articles/what-is-demand-planning

[^15_217]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^15_218]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^15_219]: https://keends.com/blog/demand-planning-kpis/

[^15_220]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^15_221]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^15_222]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^15_223]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^15_224]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^15_225]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^15_226]: https://imperiascm.com/blog/demand-forecasting-bias

[^15_227]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^15_228]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^15_229]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^15_230]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^15_231]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^15_232]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^15_233]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^15_234]: 01_Requirements.md

[^15_235]: Actuals_Supply_Plan_Requirements.md

[^15_236]: Red_Keychain_Supply_Planning_Requirements.md

[^15_237]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^15_238]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^15_239]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^15_240]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^15_241]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^15_242]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^15_243]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^15_244]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^15_245]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^15_246]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^15_247]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^15_248]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^15_249]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^15_250]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^15_251]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^15_252]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^15_253]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^15_254]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^15_255]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^15_256]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^15_257]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^15_258]: https://www.milwaukeetool.jobs/career-areas

[^15_259]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^15_260]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^15_261]: https://dataintelo.com/report/global-milwaukee-tool-market

[^15_262]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^15_263]: https://www.milwaukeetool.com/

[^15_264]: https://www.oracle.com/customers/milwaukee-tool/

[^15_265]: https://www.ttigroup.com/documents/annual-report-2025/

[^15_266]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^15_267]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^15_268]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^15_269]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^15_270]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^15_271]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^15_272]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^15_273]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^15_274]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^15_275]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^15_276]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^15_277]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^15_278]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^15_279]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^15_280]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^15_281]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^15_282]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^15_283]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^15_284]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^15_285]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^15_286]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^15_287]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^15_288]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^15_289]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^15_290]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^15_291]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^15_292]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^15_293]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^15_294]: https://www.hyperbots.com/glossary/target-gap-analysis

[^15_295]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^15_296]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^15_297]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^15_298]: https://www.ibm.com/think/topics/variance-analysis

[^15_299]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^15_300]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^15_301]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^15_302]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^15_303]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^15_304]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^15_305]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^15_306]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^15_307]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^15_308]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/

[^15_309]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^15_310]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^15_311]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^15_312]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^15_313]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^15_314]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^15_315]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^15_316]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^15_317]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^15_318]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^15_319]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^15_320]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^15_321]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^15_322]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^15_323]: https://docs.databricks.com/api/genie/v1/conversation

[^15_324]: https://docs.databricks.com/api/genie/v1

[^15_325]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^15_326]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^15_327]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^15_328]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^15_329]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^15_330]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^15_331]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^15_332]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^15_333]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^15_334]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^15_335]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^15_336]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^15_337]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^15_338]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^15_339]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^15_340]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^15_341]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^15_342]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^15_343]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^15_344]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^15_345]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^15_346]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^15_347]: https://docs.databricks.com/aws/en/oltp/projects/high-availability

[^15_348]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^15_349]: https://docs.databricks.com/api/apps/v1/app

[^15_350]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-node

[^15_351]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime

[^15_352]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-apps

[^15_353]: https://docs.databricks.com/gcp/en/agents/custom-agents/debug-agent

[^15_354]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/deploy

[^15_355]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices

[^15_356]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/key-concepts

[^15_357]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets

[^15_358]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/connect-local

[^15_359]: https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial

[^15_360]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/view-app-details

[^15_361]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api

[^15_362]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/model-serving

[^15_363]: https://docs.databricks.com/api/model-serving/v1/serving-endpoint

[^15_364]: https://docs.databricks.com/api/jobs/v2/run

[^15_365]: https://docs.databricks.com/aws/en/machine-learning/model-serving/store-env-variable-model-serving

[^15_366]: https://docs.databricks.com/gcp/en/machine-learning/model-serving/manage-serving-endpoints

[^15_367]: https://docs.databricks.com/aws/en/oltp/projects/automate-with-terraform

[^15_368]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/

[^15_369]: https://www.holistics.io/blog/the-three-types-of-fact-tables/

[^15_370]: https://www.databricks.com/blog/five-simple-steps-for-implementing-a-star-schema-in-databricks-with-delta-lake

[^15_371]: https://www.kimballgroup.com/2003/03/declaring-the-grain/

[^15_372]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-4-complex-fact-table-patterns/accumulating-snapshot-fact-tables

[^15_373]: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering

[^15_374]: https://www.kimballgroup.com/2008/11/fact-tables/

[^15_375]: https://www.kimballgroup.com/2012/05/design-tip-145-time-stamping-accumulating-snapshot-fact-tables/

[^15_376]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^15_377]: https://dev.to/alexmercedcoder/dimensional-modeling-facts-dimensions-and-grains-3obm

[^15_378]: https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/

[^15_379]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/

[^15_380]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/

[^15_381]: https://www.linkedin.com/posts/jrlasak\_%F0%9D%97%9F%F0%9D%97%B6%F0%9D%97%BE%F0%9D%98%82%F0%9D%97%B6%F0%9D%97%B1-%F0%9D%97%96%F0%9D%97%B9%F0%9D%98%82%F0%9D%98%80%F0%9D%98%81%F0%9D%97%B2%F0%9D%97%BF%F0%9D%97%B6%F0%9D%97%BB%F0%9D%97%B4-%F0%9D%98%83%F0%9D%98%80-%F0%9D%97%AD-%F0%9D%97%A2%F0%9D%97%BF%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF-activity-7445032276314238976-c6EB

[^15_382]: https://kimballgroup.forumotion.net/t1496-difference-between-factless-fact-and-bridge-table

[^15_383]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/

[^15_384]: https://bigbear.ai/blog/bridge-tables-deep-dive/

[^15_385]: https://www.reddit.com/r/dataengineering/comments/1pbro6t/kimball_confusion_semi_additive_vs_fully_additive/

[^15_386]: https://datadef.io/guides/en/dimensional-modeling

[^15_387]: https://www.kimballgroup.com/2012/02/design-tip-142-building-bridges/

[^15_388]: https://docs.thoughtspot.com/cloud/26.8.0.cl/semi-additive-measures.html

[^15_389]: https://www.kimballgroup.com/2005/12/the-matrix-revisited/

[^15_390]: https://community.sisense.com/forum/how-tos-faqs-43/topic/many-to-many-multivalued-dimension-4698/

[^15_391]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-2-dimensional-modeling-core/fact-tables-fundamentals

[^15_392]: https://arxiv.org/html/2606.27571v2

[^15_393]: https://datawarehouseinfo.com/practice/advanced-dimensional-modeling/

[^15_394]: https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables

[^15_395]: https://talkingschema.ai/docs/glossary/conformed-dimension

[^15_396]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions

[^15_397]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins

[^15_398]: https://docs.databricks.com/aws/en/ldp/dbsql/materialized

[^15_399]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/yaml-reference

[^15_400]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/create

[^15_401]: https://docs.databricks.com/aws/en/ldp/cdc

[^15_402]: https://docs.databricks.com/sap/en/release-notes/sql

[^15_403]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/basic-modeling

[^15_404]: https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables

[^15_405]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints

[^15_406]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select

[^15_407]: https://www.linkedin.com/pulse/understanding-medallion-architecture-databricks-bronze-chaudhari-rsrmf

[^15_408]: https://community.databricks.com/t5/community-articles/medallion-architecture-in-practice-the-design-decisions-nobody/td-p/163206

[^15_409]: https://community.databricks.com/t5/data-engineering/medallion-architecture-and-databricks-assistant/td-p/102301

[^15_410]: https://erstudio.com/blog/understanding-the-three-layers-of-medallion-architecture/

[^15_411]: https://erstudio.com/blog/how-medallion-architecture-with-er-studio-and-databricks-solves-data-as-a-product-for-both-business-and-it/

[^15_412]: https://cosmosthrace.com/resources/databricks/databricks-medallion-architecture-best-practices

[^15_413]: https://www.databricks.com/blog/what-is-medallion-architecture

[^15_414]: https://www.reddit.com/r/databricks/comments/1c93t94/medallion_architecture/

[^15_415]: https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825

[^15_416]: https://tacnode.io/post/medallion-architecture

[^15_417]: https://community.databricks.com/t5/data-engineering/medallion-architecture-do-i-need-a-materialized-exploded-layer/td-p/139085

[^15_418]: https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion

[^15_419]: https://www.reddit.com/r/databricks/comments/1j0gyd5/best_practices_for_medallion_architecture_in/

[^15_420]: https://docs.databricks.com/aws/en/lakehouse/medallion

[^15_421]: https://www.reddit.com/r/databricks/comments/173p6ev/bronzesilvergold_what_really_happens_in_each/

[^15_422]: https://docs.databricks.com/aws/en/ai-bi/admin/use-apis

[^15_423]: https://docs.databricks.com/aws/en/integrations/msft-teams

[^15_424]: https://docs.databricks.com/aws/en/ai-bi/admin/embed

[^15_425]: https://docs.databricks.com/aws/en/genie-one/

[^15_426]: cursor_databricks_project_upload_cleanu.md


---

# now, from the front end perspective .. find everything on the cross origin, react, fast api, and so many other things .. and dtabricks limitations or restrictions on a certain kind of thing ... or manual activities on certain kind of thing... like .. Databricks Apps service principal needs to be added manually for can manage/ can use accesses and also, resources are to be added to the Databricks Apps for things to work .. and this is just an example .. for everything that we use, we should know the gotchas!

Absolutely—**iframe limitations are now included in the frontend gotcha framework**. The critical point is that iframe support differs among Databricks Apps, dashboards, Genie Agents, notebook HTML, and external sites; a working URL does not guarantee that it can be embedded securely or successfully.

## Databricks Apps

A Databricks App can be embedded in another web application, but:

- The App must be running and accessible.
- Every viewer must be an authenticated Databricks user.
- Every viewer must have permission to use the App.
- Embedding does not make the App public or bypass its `CAN USE` ACL.[^16_1]
- The host portal’s login does not necessarily create a usable Databricks login inside the iframe.
- Third-party-cookie restrictions, identity-provider redirects, corporate browser policies, PrivateLink, VPN, proxy, and DNS behavior must be tested.
- A full-page fallback link should be provided when embedded authentication fails.

Even inside an iframe, FastAPI must independently authorize every read, writeback, approval, and live action.

## Dashboard embedding

Published AI/BI dashboards support iframe embedding, but the workspace administrator must enable it and configure an embedding policy—allow all, allow approved domains, or deny. Basic embedding requires Databricks authentication and third-party cookies.[^16_2][^16_3]

Important limitations include:

- Draft dashboards are not the supported embedding surface.
- The parent domain must be approved by the workspace.
- Viewers still require the necessary dashboard and data access under basic embedding.
- Third-party-cookie blocking can cause authentication failures or repeated login prompts.
- Embedded dashboards always use light mode.[^16_2]
- The iframe UI cannot be restyled or controlled like a native React component.
- Host platforms such as SharePoint may require their own iframe allowlisting.
- External embedding has service-specific limits, including 20 dashboard loads beginning per second; pages containing many frames should lazy-load or stagger them.[^16_4]

If the App requires coordinated filters, writebacks, Agent context, action buttons, or custom drill paths, a native React visualization backed by governed APIs may be better than embedding several dashboard frames.

## Genie embedding

A Genie Agent can be embedded, but:

- A workspace administrator must approve the embedding surface.
- The Agent author requires at least `CAN MANAGE`.
- End users require access to the Genie Agent.
- End users also require appropriate access to the underlying data.
- Unauthenticated users are prompted to sign in.[^16_5]
- Clipboard functionality requires the iframe permission `allow="clipboard-write"`.[^16_5]

An embedded Genie frame is appropriate when its standard UI is acceptable. It is less suitable when the App requires custom tool-progress displays, MLflow trace correlation, Lakebase conversation state, typed action proposals, approval gates, or tightly controlled Agent interactions. In those cases, FastAPI should call supported Agent APIs while React renders the experience.

## Cross-frame control

React generally cannot reach inside a cross-origin iframe to modify its DOM, read internal state, intercept events, or synchronize controls. Attempting to scrape or automate a Databricks iframe would be brittle and dependent on undocumented UI details.

If communication through `postMessage` is supported by both sides:

- Validate `event.origin`.
- Send to a specific target origin—not `*`.
- Validate every message against a versioned schema.
- Never transmit Databricks tokens, database credentials, secrets, or unrestricted action commands.
- Never accept a live-action instruction solely because it arrived through `postMessage`.


## External content

Embedding an external ERP, WMS, planning system, document portal, or visualization inside the Databricks App depends on that system’s policies.

The child system may block framing through:

- Content Security Policy `frame-ancestors`.
- `X-Frame-Options`.
- Third-party-cookie restrictions.
- Authentication redirects.
- Licensing restrictions.
- Corporate browser policies.

CORS configuration cannot override anti-framing headers. The external system must officially support the embedding scenario.

## Security risks

iframes introduce clickjacking and confused-deputy risks, especially around supply-chain actions. An attacker-controlled or compromised parent page could attempt to hide or visually disguise an approval interface.

For consequential actions such as forecast overrides, inventory transfers, purchase-order changes, or ERP/WMS submissions:

- Prefer an unmistakable, trusted approval screen.
- Reauthorize and revalidate the action server-side.
- Verify the record version immediately before execution.
- Require step-up or dual approval when warranted.
- Never treat a frontend button state as an authorization control.
- Record the actor, proposed action, approval, origin, evidence, and execution result.
- Do not expose live-action APIs to unrestricted iframe messaging.

CORS, iframe policies, and CSRF protection solve different problems; none substitutes for server-side authorization.

## Notebook HTML

Databricks notebook `displayHTML` runs inside an iframe served from `databricksusercontent.com`. Corporate networks must allow that domain or the output can appear blank even when the notebook is correct.[^16_6]

Notebook iframe output is useful for exploration and demonstrations but not as the production foundation for:

- Durable sessions.
- Operational writebacks.
- Agent conversations.
- Approval workflows.
- Authentication-sensitive interactions.
- Persistent telemetry.
- Live supply-chain actions.


## Selection rule

| Requirement | Preferred design |
| :-- | :-- |
| Standard published dashboard in a portal | Dashboard iframe |
| Standard Genie experience in a portal | Genie iframe |
| Entire Databricks App inside an internal portal | App iframe, after authentication testing |
| Integrated Agent, writeback, and approval experience | Native React + FastAPI |
| Tight synchronization between charts and App state | Native React visualization |
| Public anonymous application | Do not assume a Databricks App iframe |
| Third-party operational system | Only if the vendor officially supports framing |
| Temporary interactive notebook content | `displayHTML`, for development only |

For every iframe proposed in this project, I will now verify **official support, parent-domain policy, authentication, permissions, cookies, CSP, sandbox attributes, networking, messaging, clickjacking exposure, performance, accessibility, and fallback behavior** before selecting it.

<span style="display:none">[^16_10][^16_100][^16_101][^16_102][^16_103][^16_104][^16_105][^16_106][^16_107][^16_108][^16_109][^16_11][^16_110][^16_111][^16_112][^16_113][^16_114][^16_115][^16_116][^16_117][^16_118][^16_119][^16_12][^16_120][^16_121][^16_122][^16_123][^16_124][^16_125][^16_126][^16_127][^16_128][^16_129][^16_13][^16_130][^16_131][^16_132][^16_133][^16_134][^16_135][^16_136][^16_137][^16_138][^16_139][^16_14][^16_140][^16_141][^16_142][^16_143][^16_144][^16_145][^16_146][^16_147][^16_148][^16_149][^16_15][^16_150][^16_151][^16_152][^16_153][^16_154][^16_155][^16_156][^16_157][^16_158][^16_159][^16_16][^16_160][^16_161][^16_162][^16_163][^16_164][^16_165][^16_166][^16_167][^16_168][^16_169][^16_17][^16_170][^16_171][^16_172][^16_173][^16_174][^16_175][^16_176][^16_177][^16_178][^16_179][^16_18][^16_180][^16_181][^16_182][^16_183][^16_184][^16_185][^16_186][^16_187][^16_188][^16_189][^16_19][^16_190][^16_191][^16_192][^16_193][^16_194][^16_195][^16_196][^16_197][^16_198][^16_199][^16_20][^16_200][^16_201][^16_202][^16_203][^16_204][^16_205][^16_206][^16_207][^16_208][^16_209][^16_21][^16_210][^16_211][^16_212][^16_213][^16_214][^16_215][^16_216][^16_217][^16_218][^16_219][^16_22][^16_220][^16_221][^16_222][^16_223][^16_224][^16_225][^16_226][^16_227][^16_228][^16_229][^16_23][^16_230][^16_231][^16_232][^16_233][^16_234][^16_235][^16_236][^16_237][^16_238][^16_239][^16_24][^16_240][^16_241][^16_242][^16_243][^16_244][^16_245][^16_246][^16_247][^16_248][^16_249][^16_25][^16_250][^16_251][^16_252][^16_253][^16_254][^16_255][^16_256][^16_257][^16_258][^16_259][^16_26][^16_260][^16_261][^16_262][^16_263][^16_264][^16_265][^16_266][^16_267][^16_268][^16_269][^16_27][^16_270][^16_271][^16_272][^16_273][^16_274][^16_275][^16_276][^16_277][^16_278][^16_279][^16_28][^16_280][^16_281][^16_282][^16_283][^16_284][^16_285][^16_286][^16_287][^16_288][^16_289][^16_29][^16_290][^16_291][^16_292][^16_293][^16_294][^16_295][^16_296][^16_297][^16_298][^16_299][^16_30][^16_300][^16_301][^16_302][^16_303][^16_304][^16_305][^16_306][^16_307][^16_308][^16_309][^16_31][^16_310][^16_311][^16_312][^16_313][^16_314][^16_315][^16_316][^16_317][^16_318][^16_319][^16_32][^16_320][^16_321][^16_322][^16_323][^16_324][^16_325][^16_326][^16_327][^16_328][^16_329][^16_33][^16_330][^16_331][^16_332][^16_333][^16_334][^16_335][^16_336][^16_337][^16_338][^16_339][^16_34][^16_340][^16_341][^16_342][^16_343][^16_344][^16_345][^16_346][^16_347][^16_348][^16_349][^16_35][^16_350][^16_351][^16_352][^16_353][^16_354][^16_355][^16_356][^16_357][^16_358][^16_359][^16_36][^16_360][^16_361][^16_362][^16_363][^16_364][^16_365][^16_366][^16_367][^16_368][^16_369][^16_37][^16_370][^16_371][^16_372][^16_373][^16_374][^16_375][^16_376][^16_377][^16_378][^16_379][^16_38][^16_380][^16_381][^16_382][^16_383][^16_384][^16_385][^16_386][^16_387][^16_388][^16_389][^16_39][^16_390][^16_391][^16_392][^16_393][^16_394][^16_395][^16_396][^16_397][^16_398][^16_399][^16_40][^16_400][^16_401][^16_402][^16_403][^16_404][^16_405][^16_406][^16_407][^16_408][^16_409][^16_41][^16_410][^16_411][^16_412][^16_413][^16_414][^16_415][^16_416][^16_417][^16_418][^16_419][^16_42][^16_420][^16_421][^16_422][^16_423][^16_424][^16_425][^16_426][^16_427][^16_428][^16_429][^16_43][^16_430][^16_431][^16_432][^16_433][^16_434][^16_435][^16_436][^16_437][^16_438][^16_439][^16_44][^16_440][^16_441][^16_442][^16_443][^16_444][^16_445][^16_446][^16_447][^16_448][^16_449][^16_45][^16_450][^16_451][^16_452][^16_453][^16_454][^16_455][^16_456][^16_457][^16_458][^16_459][^16_46][^16_460][^16_461][^16_462][^16_463][^16_464][^16_465][^16_466][^16_467][^16_468][^16_469][^16_47][^16_470][^16_471][^16_472][^16_473][^16_474][^16_475][^16_476][^16_477][^16_478][^16_479][^16_48][^16_480][^16_481][^16_482][^16_483][^16_484][^16_49][^16_50][^16_51][^16_52][^16_53][^16_54][^16_55][^16_56][^16_57][^16_58][^16_59][^16_60][^16_61][^16_62][^16_63][^16_64][^16_65][^16_66][^16_67][^16_68][^16_69][^16_7][^16_70][^16_71][^16_72][^16_73][^16_74][^16_75][^16_76][^16_77][^16_78][^16_79][^16_8][^16_80][^16_81][^16_82][^16_83][^16_84][^16_85][^16_86][^16_87][^16_88][^16_89][^16_9][^16_90][^16_91][^16_92][^16_93][^16_94][^16_95][^16_96][^16_97][^16_98][^16_99]</span>

<div align="center">⁂</div>

[^16_1]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^16_2]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices

[^16_3]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^16_4]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^16_5]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime

[^16_6]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions

[^16_7]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration

[^16_8]: https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial

[^16_9]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/environment-variables

[^16_10]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^16_11]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-apps

[^16_12]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy

[^16_13]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/apps-commands

[^16_14]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/functions

[^16_15]: https://docs.databricks.com/aws/en/agents/mcp-tools/custom-mcp

[^16_16]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-node

[^16_17]: https://docs.databricks.com/aws/en/compute/serverless/notebooks

[^16_18]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/

[^16_19]: https://docs.databricks.com/aws/en/release-notes/runtime/maintenance-updates

[^16_20]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/

[^16_21]: https://docs.databricks.com/aws/en/release-notes/runtime/17.0

[^16_22]: https://docs.databricks.com/aws/en/release-notes/runtime/15.2

[^16_23]: https://docs.databricks.com/aws/en/release-notes/runtime/18.0

[^16_24]: https://docs.databricks.com/aws/en/release-notes/runtime/16.3

[^16_25]: https://docs.databricks.com/aws/en/spark/api-options

[^16_26]: https://docs.databricks.com/aws/en/admin/system-tables/jobs

[^16_27]: https://docs.databricks.com/aws/en/connect/streaming/kafka/

[^16_28]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/monitor

[^16_29]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/system-env

[^16_30]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^16_31]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^16_32]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^16_33]: https://docs.databricks.com/api/apps/v1/app

[^16_34]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/connect-local

[^16_35]: https://docs.databricks.com/aws/en/resources/limits

[^16_36]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^16_37]: https://learn.microsoft.com/en-us/answers/questions/1820098/cors-issues-between-azure-static-web-apps-and-azur

[^16_38]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^16_39]: https://docs.databricks.com/aws/en/security/network/front-end/

[^16_40]: https://www.databricks.com/blog/building-databricks-apps-react-and-mosaic-ai-agents-enterprise-chat-solutions

[^16_41]: https://docs.databricks.com/aws/en/partners/bi/power-bi/

[^16_42]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^16_43]: https://kb.databricks.com/security/cors-policy-error-when-trying-to-run-databricks-api-from-a-browser-based-application

[^16_44]: https://community.databricks.com/t5/get-started-discussions/facing-cors-issue-while-calling-databricks-rest-api-from-a-react/td-p/52268

[^16_45]: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations

[^16_46]: https://fastapi.tiangolo.com/tutorial/cors/

[^16_47]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies

[^16_48]: https://stackoverflow.com/questions/75952412/azure-databricks-rest-api-blocked-by-cors-policy-while-making-request-through-re

[^16_49]: https://docs.databricks.com/aws/en/resources/ip-domain-region

[^16_50]: https://qubika.com/blog/building-modern-full-stack-react-fastapi-databricks-lakebase/

[^16_51]: https://docs.databricks.com/gcp/en/sparkr/shiny

[^16_52]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^16_53]: https://docs.databricks.com/aws/en/compute/web-terminal

[^16_54]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/create-custom-app

[^16_55]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started

[^16_56]: https://docs.databricks.com/aws/en/dev-tools/ssh-tunnel

[^16_57]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^16_58]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/horizontal-scaling

[^16_59]: https://docs.databricks.com/api/statement-execution/v1

[^16_60]: https://docs.databricks.com/aws/en/dev-tools/python-sql-connector

[^16_61]: https://docs.databricks.com/aws/en/compute/configure

[^16_62]: https://docs.databricks.com/aws/en/dev-tools/nodejs-sql-driver

[^16_63]: https://docs.databricks.com/aws/en/oltp/projects/authentication

[^16_64]: https://docs.databricks.com/api/clusters/v2/cluster

[^16_65]: https://docs.databricks.com/api/workspace/scopes

[^16_66]: https://docs.databricks.com/aws/en/integrations/jdbc-oss/properties

[^16_67]: https://docs.databricks.com/aws/en/oltp/projects/high-availability

[^16_68]: https://docs.databricks.com/aws/en/release-notes/product/

[^16_69]: https://docs.databricks.com/aws/en/oltp/projects/manage-computes

[^16_70]: https://docs.databricks.com/gcp/en/sql/release-notes/2024

[^16_71]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/embed

[^16_72]: https://docs.databricks.com/aws/ja/dev-tools/databricks-apps/embed

[^16_73]: https://docs.databricks.com/gcp/en/dashboards/share/embedding/basic

[^16_74]: https://docs.databricks.com/gcp/en/ai-bi/admin/embed

[^16_75]: https://docs.databricks.com/aws/pt/ai-bi/admin/embed

[^16_76]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/networking

[^16_77]: https://docs.databricks.com/aws/en/dashboards/share/embedding/basic

[^16_78]: https://docs.databricks.com/aws/en/genie-agents/embed

[^16_79]: https://docs.databricks.com/aws/en/ai-bi/admin/embed

[^16_80]: https://docs.databricks.com/aws/en/dashboards/

[^16_81]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^16_82]: https://docs.databricks.com/aws/en/dashboards/tutorials/dashboard-crud-api

[^16_83]: https://docs.databricks.com/aws/en/notebooks/notebook-media

[^16_84]: https://docs.databricks.com/aws/en/dashboards/share/embedding/external-embed

[^16_85]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^16_86]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^16_87]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^16_88]: https://docs.databricks.com/aws/en/ldp/concepts

[^16_89]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^16_90]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^16_91]: https://docs.databricks.com/aws/en/ldp/

[^16_92]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^16_93]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^16_94]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^16_95]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^16_96]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^16_97]: https://docs.databricks.com/aws/en/ldp/real-time

[^16_98]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^16_99]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^16_100]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^16_101]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^16_102]: https://docs.databricks.com/aws/en/tables/clustering

[^16_103]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^16_104]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^16_105]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^16_106]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^16_107]: https://docs.databricks.com/aws/en/delta/tutorial

[^16_108]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^16_109]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^16_110]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^16_111]: https://docs.databricks.com/aws/en/mlflow/

[^16_112]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^16_113]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^16_114]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^16_115]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^16_116]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^16_117]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^16_118]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^16_119]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^16_120]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^16_121]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^16_122]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^16_123]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^16_124]: https://docs.databricks.com/gcp/en/languages/overview

[^16_125]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^16_126]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^16_127]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^16_128]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^16_129]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^16_130]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^16_131]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^16_132]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^16_133]: https://docs.databricks.com/aws/en/oltp/projects/

[^16_134]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^16_135]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^16_136]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^16_137]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^16_138]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^16_139]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^16_140]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^16_141]: https://docs.databricks.com/aws/en/query-federation/oracle

[^16_142]: https://docs.databricks.com/aws/en/ldp/expectations

[^16_143]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^16_144]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^16_145]: https://docs.databricks.com/aws/en/ldp/concepts/

[^16_146]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^16_147]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^16_148]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^16_149]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^16_150]: https://docs.databricks.com/aws/en/query-federation/networking

[^16_151]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^16_152]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^16_153]: https://docs.databricks.com/aws/en/query-federation/databricks

[^16_154]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^16_155]: https://docs.databricks.com/gcp/en/developers/best-practices

[^16_156]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^16_157]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^16_158]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^16_159]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^16_160]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^16_161]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^16_162]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^16_163]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^16_164]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^16_165]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^16_166]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^16_167]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^16_168]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^16_169]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^16_170]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^16_171]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^16_172]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^16_173]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^16_174]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^16_175]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^16_176]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^16_177]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^16_178]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^16_179]: https://docs.databricks.com/aws/en/developers/best-practices

[^16_180]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^16_181]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^16_182]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^16_183]: https://docs.databricks.com/aws/en/notebooks/testing

[^16_184]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^16_185]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^16_186]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^16_187]: https://docs.databricks.com/aws/en/files/files-recommendations

[^16_188]: https://docs.databricks.com/aws/en/files/workspace-modules

[^16_189]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^16_190]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^16_191]: https://docs.databricks.com/gcp/en/files/workspace

[^16_192]: https://docs.databricks.com/aws/en/volumes/volume-files

[^16_193]: https://docs.databricks.com/aws/en/repos/ci-cd

[^16_194]: https://docs.databricks.com/aws/en/notebooks/share-code

[^16_195]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^16_196]: https://docs.databricks.com/aws/en/repos/limits

[^16_197]: https://docs.databricks.com/aws/en/files/workspace-interact

[^16_198]: https://docs.databricks.com/aws/en/jobs/git

[^16_199]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^16_200]: https://docs.databricks.com/api/jobs/v2/job

[^16_201]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^16_202]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^16_203]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^16_204]: https://docs.databricks.com/aws/en/repos/repos-setup

[^16_205]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^16_206]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^16_207]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^16_208]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^16_209]: https://docs.databricks.com/aws/en/tables/history

[^16_210]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^16_211]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^16_212]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^16_213]: https://docs.databricks.com/aws/en/files/workspace

[^16_214]: https://docs.databricks.com/aws/en/jobs/privileges

[^16_215]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^16_216]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^16_217]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^16_218]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^16_219]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^16_220]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^16_221]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^16_222]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^16_223]: https://docs.databricks.com/aws/en/ai-gateway/

[^16_224]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^16_225]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^16_226]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^16_227]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^16_228]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^16_229]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^16_230]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^16_231]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^16_232]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^16_233]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^16_234]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^16_235]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^16_236]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^16_237]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^16_238]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^16_239]: https://docs.databricks.com/aws/en/agents/

[^16_240]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^16_241]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^16_242]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^16_243]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^16_244]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^16_245]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^16_246]: https://docs.databricks.com/aws/en/machine-learning/

[^16_247]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^16_248]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^16_249]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^16_250]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^16_251]: https://www.hyperbots.com/glossary/sap-demand-planning

[^16_252]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^16_253]: https://www.ascm.org/topics/demand-supply-planning/

[^16_254]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^16_255]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^16_256]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^16_257]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^16_258]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^16_259]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^16_260]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^16_261]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^16_262]: https://o9solutions.com/articles/what-is-demand-planning

[^16_263]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^16_264]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^16_265]: https://keends.com/blog/demand-planning-kpis/

[^16_266]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^16_267]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^16_268]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^16_269]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^16_270]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^16_271]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^16_272]: https://imperiascm.com/blog/demand-forecasting-bias

[^16_273]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^16_274]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^16_275]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^16_276]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^16_277]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^16_278]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^16_279]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^16_280]: 01_Requirements.md

[^16_281]: Actuals_Supply_Plan_Requirements.md

[^16_282]: Red_Keychain_Supply_Planning_Requirements.md

[^16_283]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^16_284]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^16_285]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^16_286]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^16_287]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^16_288]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^16_289]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^16_290]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^16_291]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^16_292]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^16_293]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^16_294]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^16_295]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^16_296]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^16_297]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^16_298]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^16_299]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^16_300]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^16_301]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^16_302]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^16_303]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^16_304]: https://www.milwaukeetool.jobs/career-areas

[^16_305]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^16_306]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^16_307]: https://dataintelo.com/report/global-milwaukee-tool-market

[^16_308]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^16_309]: https://www.milwaukeetool.com/

[^16_310]: https://www.oracle.com/customers/milwaukee-tool/

[^16_311]: https://www.ttigroup.com/documents/annual-report-2025/

[^16_312]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^16_313]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^16_314]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^16_315]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^16_316]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^16_317]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^16_318]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^16_319]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^16_320]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^16_321]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^16_322]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^16_323]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^16_324]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^16_325]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^16_326]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^16_327]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^16_328]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^16_329]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^16_330]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^16_331]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^16_332]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^16_333]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^16_334]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^16_335]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^16_336]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^16_337]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^16_338]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^16_339]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^16_340]: https://www.hyperbots.com/glossary/target-gap-analysis

[^16_341]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^16_342]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^16_343]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^16_344]: https://www.ibm.com/think/topics/variance-analysis

[^16_345]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^16_346]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^16_347]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^16_348]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^16_349]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^16_350]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^16_351]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^16_352]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^16_353]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^16_354]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/

[^16_355]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^16_356]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^16_357]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^16_358]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^16_359]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^16_360]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^16_361]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^16_362]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^16_363]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^16_364]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^16_365]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^16_366]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^16_367]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^16_368]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^16_369]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^16_370]: https://docs.databricks.com/api/genie/v1/conversation

[^16_371]: https://docs.databricks.com/api/genie/v1

[^16_372]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^16_373]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^16_374]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^16_375]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^16_376]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^16_377]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^16_378]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^16_379]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^16_380]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^16_381]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^16_382]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^16_383]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^16_384]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^16_385]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^16_386]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^16_387]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^16_388]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^16_389]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^16_390]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^16_391]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^16_392]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^16_393]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^16_394]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^16_395]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^16_396]: https://docs.databricks.com/gcp/en/agents/custom-agents/debug-agent

[^16_397]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/deploy

[^16_398]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/key-concepts

[^16_399]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets

[^16_400]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/connect-local

[^16_401]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/view-app-details

[^16_402]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api

[^16_403]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/model-serving

[^16_404]: https://docs.databricks.com/api/model-serving/v1/serving-endpoint

[^16_405]: https://docs.databricks.com/api/jobs/v2/run

[^16_406]: https://docs.databricks.com/aws/en/machine-learning/model-serving/store-env-variable-model-serving

[^16_407]: https://docs.databricks.com/gcp/en/machine-learning/model-serving/manage-serving-endpoints

[^16_408]: https://docs.databricks.com/aws/en/oltp/projects/automate-with-terraform

[^16_409]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/

[^16_410]: https://www.holistics.io/blog/the-three-types-of-fact-tables/

[^16_411]: https://www.databricks.com/blog/five-simple-steps-for-implementing-a-star-schema-in-databricks-with-delta-lake

[^16_412]: https://www.kimballgroup.com/2003/03/declaring-the-grain/

[^16_413]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-4-complex-fact-table-patterns/accumulating-snapshot-fact-tables

[^16_414]: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering

[^16_415]: https://www.kimballgroup.com/2008/11/fact-tables/

[^16_416]: https://www.kimballgroup.com/2012/05/design-tip-145-time-stamping-accumulating-snapshot-fact-tables/

[^16_417]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^16_418]: https://dev.to/alexmercedcoder/dimensional-modeling-facts-dimensions-and-grains-3obm

[^16_419]: https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/

[^16_420]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/

[^16_421]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/

[^16_422]: https://www.linkedin.com/posts/jrlasak\_%F0%9D%97%9F%F0%9D%97%B6%F0%9D%97%BE%F0%9D%98%82%F0%9D%97%B6%F0%9D%97%B1-%F0%9D%97%96%F0%9D%97%B9%F0%9D%98%82%F0%9D%98%80%F0%9D%98%81%F0%9D%97%B2%F0%9D%97%BF%F0%9D%97%B6%F0%9D%97%BB%F0%9D%97%B4-%F0%9D%98%83%F0%9D%98%80-%F0%9D%97%AD-%F0%9D%97%A2%F0%9D%97%BF%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF-activity-7445032276314238976-c6EB

[^16_423]: https://kimballgroup.forumotion.net/t1496-difference-between-factless-fact-and-bridge-table

[^16_424]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/

[^16_425]: https://bigbear.ai/blog/bridge-tables-deep-dive/

[^16_426]: https://www.reddit.com/r/dataengineering/comments/1pbro6t/kimball_confusion_semi_additive_vs_fully_additive/

[^16_427]: https://datadef.io/guides/en/dimensional-modeling

[^16_428]: https://www.kimballgroup.com/2012/02/design-tip-142-building-bridges/

[^16_429]: https://docs.thoughtspot.com/cloud/26.8.0.cl/semi-additive-measures.html

[^16_430]: https://www.kimballgroup.com/2005/12/the-matrix-revisited/

[^16_431]: https://community.sisense.com/forum/how-tos-faqs-43/topic/many-to-many-multivalued-dimension-4698/

[^16_432]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-2-dimensional-modeling-core/fact-tables-fundamentals

[^16_433]: https://arxiv.org/html/2606.27571v2

[^16_434]: https://datawarehouseinfo.com/practice/advanced-dimensional-modeling/

[^16_435]: https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables

[^16_436]: https://talkingschema.ai/docs/glossary/conformed-dimension

[^16_437]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions

[^16_438]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins

[^16_439]: https://docs.databricks.com/aws/en/ldp/dbsql/materialized

[^16_440]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/yaml-reference

[^16_441]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/create

[^16_442]: https://docs.databricks.com/aws/en/ldp/cdc

[^16_443]: https://docs.databricks.com/sap/en/release-notes/sql

[^16_444]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/basic-modeling

[^16_445]: https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables

[^16_446]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints

[^16_447]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select

[^16_448]: https://www.linkedin.com/pulse/understanding-medallion-architecture-databricks-bronze-chaudhari-rsrmf

[^16_449]: https://community.databricks.com/t5/community-articles/medallion-architecture-in-practice-the-design-decisions-nobody/td-p/163206

[^16_450]: https://community.databricks.com/t5/data-engineering/medallion-architecture-and-databricks-assistant/td-p/102301

[^16_451]: https://erstudio.com/blog/understanding-the-three-layers-of-medallion-architecture/

[^16_452]: https://erstudio.com/blog/how-medallion-architecture-with-er-studio-and-databricks-solves-data-as-a-product-for-both-business-and-it/

[^16_453]: https://cosmosthrace.com/resources/databricks/databricks-medallion-architecture-best-practices

[^16_454]: https://www.databricks.com/blog/what-is-medallion-architecture

[^16_455]: https://www.reddit.com/r/databricks/comments/1c93t94/medallion_architecture/

[^16_456]: https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825

[^16_457]: https://tacnode.io/post/medallion-architecture

[^16_458]: https://community.databricks.com/t5/data-engineering/medallion-architecture-do-i-need-a-materialized-exploded-layer/td-p/139085

[^16_459]: https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion

[^16_460]: https://www.reddit.com/r/databricks/comments/1j0gyd5/best_practices_for_medallion_architecture_in/

[^16_461]: https://docs.databricks.com/aws/en/lakehouse/medallion

[^16_462]: https://www.reddit.com/r/databricks/comments/173p6ev/bronzesilvergold_what_really_happens_in_each/

[^16_463]: https://docs.databricks.com/aws/en/dashboards/genie-spaces

[^16_464]: https://docs.databricks.com/aws/en/ai-bi/admin/use-apis

[^16_465]: https://docs.databricks.com/aws/en/integrations/msft-teams

[^16_466]: https://docs.databricks.com/aws/en/genie-one/

[^16_467]: cursor_databricks_project_upload_cleanu.md

[^16_468]: https://docs.databricks.com/aws/en/ldp/limitations

[^16_469]: https://docs.databricks.com/aws/en/jobs/

[^16_470]: https://docs.databricks.com/aws/en/jobs/compute

[^16_471]: https://docs.databricks.com/aws/en/jobs/jobs-quickstart

[^16_472]: https://docs.databricks.com/aws/en/jobs/control-flow

[^16_473]: https://docs.databricks.com/aws/en/getting-started/best-practices

[^16_474]: https://docs.databricks.com/aws/en/jobs/run-serverless-jobs

[^16_475]: https://docs.databricks.com/aws/en/oltp/projects/manage-projects

[^16_476]: https://docs.databricks.com/aws/en/dashboards/limits

[^16_477]: https://docs.databricks.com/aws/en/dev-tools/auth/pat

[^16_478]: https://docs.databricks.com/gcp/en/dashboards/concepts

[^16_479]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage

[^16_480]: https://docs.databricks.com/gcp/en/query-federation/performance-recommendations

[^16_481]: https://docs.databricks.com/aws/en/query-federation/database-federation

[^16_482]: https://docs.databricks.com/gcp/en/query-federation/salesforce-data-cloud

[^16_483]: https://docs.databricks.com/aws/en/query-federation/snowflake

[^16_484]: https://docs.databricks.com/aws/en/query-federation/remote-queries


---

# also, know about latest and greatest information on mlflow traditional and genai .. for example: mlflow response agent...

All the ai developement, supervisor agent and everything shall make use of the best practices

like evaluation frameworks, llm as judge .. and other things... do not limit yourself to think on what I said, but a lot of folks need to consider about these development gotchas too

Yes. **MLflow traditional ML, MLflow for GenAI, `ResponsesAgent`, Agent evaluation, supervisor/multi-agent architecture, LLM judges, human feedback, production tracing, prompt management, AI Gateway, and AI-specific gotchas** are now part of the project’s default development pattern.

The central standard will be:

> An AI system is not production-ready because it generated an impressive answer. It must have a versioned contract, representative evaluation data, deterministic tests, trace-based evaluation, domain-expert validation, secure tools, production monitoring, and a safe fallback.

## ResponsesAgent standard

For new custom Databricks Agents, the default interface will be MLflow **`ResponsesAgent`**, unless platform compatibility provides a compelling reason to use something else.

`ResponsesAgent` is framework-agnostic and supports structured responses, tool calling, streaming, intermediate outputs, multi-turn conversations, and multi-agent scenarios. It integrates with MLflow logging, tracing, evaluation, Model Serving, and OpenAI Responses API-compatible clients.[^17_1][^17_2]

An Agent may be implemented using:

- Pure Python.
- OpenAI SDK.
- LangGraph.
- LangChain.
- Another suitable framework.
- A managed Databricks Agent or Supervisor capability.

The internal framework will be selected according to the workflow. The stable external boundary should normally remain the `ResponsesAgent` contract. Databricks explicitly recommends wrapping custom Agents with `ResponsesAgent` to gain compatibility with its evaluation, playground, serving, and App capabilities.[^17_3]

The older `ChatModel` abstraction should not be the default for new development; MLflow 3 recommends `ResponsesAgent`.[^17_4]

## Supervisor Agents

A supervisor architecture will be used only when distinct specialists or tools create demonstrable value.

A possible Milwaukee topology could be:

```text
Supply Chain Supervisor
  ├── Actual-versus-Plan Analyst
  ├── Demand Planning Specialist
  ├── Supply Exception Specialist
  ├── Inventory Specialist
  ├── Forecasting Model Tool
  ├── Policy and Procedure Retriever
  ├── Scenario/Optimization Tool
  └── Action Preparation Tool
```

Databricks Supervisor Agent can coordinate Genie Agents, Agent endpoints, Unity Catalog functions, MCP servers, and custom Agents.[^17_5]

However, more Agents do not automatically make a better system. A supervisor should be rejected when:

- One Agent with bounded tools can solve the task.
- The “specialists” share the same prompt and data.
- Routing adds latency and cost without measurable quality improvement.
- End-to-end failures become difficult to diagnose.
- Permissions cannot be separated.
- Deterministic code or a state machine would express the workflow more safely.

Databricks warns that arbitrary-code Agent tools can expose information available to the Agent. Only trusted code, explicit permissions, and guardrails should be used.[^17_6]

## Evaluation framework

Every Agent will be evaluated at multiple levels:


| Evaluation area | Preferred method |
| :-- | :-- |
| Response schema | Code-based scorer |
| Numerical correctness | Deterministic SQL or Python |
| Retrieval correctness | Ground-truth comparison |
| Groundedness | Retrieval-groundedness judge plus citation verification |
| Tool selection | Expected-tool scorer |
| Tool arguments | Typed schema and value comparison |
| Supervisor routing | Routing confusion matrix and trace judge |
| Business completeness | Domain-specific guidelines judge |
| Action authorization | Deterministic state and trace scorer |
| Safety | Safety judge plus policy checks |
| User usefulness | Planner feedback |
| Business result | Exception resolution and operational outcome |
| Performance | Latency, tokens, tool calls and cost |

MLflow supports built-in judges, custom guidelines, fully customized LLM judges, and deterministic code-based scorers.[^17_7]

Whenever truth can be calculated exactly, I will not ask an LLM judge to guess. For example:

- Actual-versus-plan arithmetic → SQL/code.
- Correct forecast vintage → deterministic comparison.
- User authorization → integration test.
- Idempotency → state and transaction test.
- Valid state transition → code scorer.
- Grounded explanation quality → LLM judge plus evidence checks.
- Planner usefulness → human evaluation.


## Evaluation datasets

Each Agent or AI capability will have several evaluation suites:

- **Smoke:** fast tests for every change.
- **Golden:** business-critical questions with expected facts, tools, SQL, arguments, and outcomes.
- **Regression:** every confirmed production failure becomes a permanent test.
- **Adversarial:** prompt injection, data exfiltration, unauthorized actions, malformed input, and tool abuse.
- **Long-tail:** rare products, locations, calendars, plan versions, and exception combinations.
- **Performance:** latency, tokens, cost, model calls, SQL calls, and concurrency.
- **Action safety:** approval, stale records, duplicate requests, retries, rollback, and partial external failure.
- **Model migration:** comparison across foundation models, prompts, retrieval indexes, and framework versions.

MLflow evaluation datasets can include labeled ground-truth examples, unlabeled rubric-based cases, manually authored golden cases, and examples taken from production traces.[^17_8][^17_9]

Evaluation data will also be governed. Production secrets, unrestricted operational records, and sensitive trace content will not be casually copied into test datasets.

## LLM judges

LLM-as-judge will be used where nuanced assessment is necessary—but it will not be treated as objective truth.

A judge must define:

- What object it evaluates.
- Which evidence it may use.
- The user role and business context.
- Precise criteria.
- Allowed result values.
- Anchored scoring rubric.
- Passing, failing, and borderline examples.
- Missing-context behavior.
- Required rationale.
- Judge model and version.

MLflow custom judges can evaluate Agent inputs, outputs, expected outcomes, and complete traces, returning Boolean, categorical, or numerical assessments.[^17_10]

Judge gotchas include:

- Scores can change with the judge model or prompt.
- Judges may favor verbose answers or familiar phrasing.
- A plausible rationale does not prove the score is right.
- A judge can reward similarity to a reference instead of task correctness.
- A model should not be assumed to be an unbiased sole judge of itself.
- Evaluation cost may exceed generation cost.
- Judge optimization can overfit the evaluation set.
- A holdout set should remain separate from prompt tuning and judge alignment.


## Human alignment

Milwaukee domain experts must help define quality:


| Reviewer | Primary judgment |
| :-- | :-- |
| Demand planner | Forecast meaning, assumptions and planning usefulness |
| Supply planner | Constraints, shortage reasoning and feasibility |
| Data owner | Metric, version and source correctness |
| Platform/security owner | Permissions and information handling |
| Application owner | Workflow and action integrity |
| Business approver | Operational risk and action authority |

MLflow supports aligning judges with human feedback. The human assessment and judge assessment must use the same assessment name for alignment to work correctly.[^17_11]

We will track more than average agreement:

- Agreement rate.
- False-pass rate.
- False-fail rate.
- Disagreement by exception category.
- Disagreement by reviewer role.
- Performance on high-risk actions.

A judge that usually agrees with humans may still be unacceptable if it falsely passes unauthorized actions or incorrect supply quantities.

## Trace-first engineering

Every production Agent interaction should be traceable across:

```text
App request
  → authenticated user
  → supervisor route
  → specialist Agent
  → retrieval/SQL
  → model invocation
  → tool call
  → recommendation
  → Lakebase proposal
  → approval
  → external action
  → verification
```

MLflow traces capture the execution flow and can later be searched, evaluated, and associated with user feedback.[^17_12]

A trace should identify:

- App, Agent, prompt and tool versions.
- Environment and use case.
- Model and endpoint.
- Retrieval sources.
- Sanitized tool arguments and results.
- Token usage, latency and cost.
- Agent answer and citations.
- User feedback.
- Lakebase workflow and action IDs.
- External execution correlation ID.

Production tracing should be asynchronous when practical, with deliberate sampling to control cost.[^17_13]

However:

- Trace content must be redacted.
- Error and live-action traces should receive stronger retention.
- Async trace queues can lose events during overload or termination.
- MLflow traces do not replace transactional Lakebase and ERP audit records.
- A successful Agent trace does not prove that an external action committed.


## Prompt management

Important prompts will be treated as versioned artifacts using MLflow Prompt Registry where appropriate. Prompt Registry provides immutable versions, comparison, reuse, and integration with tracing and evaluation.[^17_14]

Each prompt should document:

- Purpose and owner.
- Input and output schema.
- Supported roles.
- Domain definitions.
- Tool policy.
- Refusal and escalation behavior.
- Supported model families.
- Evaluation evidence.
- Version or deployment alias.

Prompt changes can alter tool behavior even when application code does not change. Therefore, every prompt or model change must rerun the applicable evaluation suites.

Prompt instructions are not security controls. A sentence such as “never modify an unauthorized order” cannot replace permissions, typed command validation, approval state, and idempotency.

## Retrieval discipline

RAG evaluation will separate:

1. Did the system retrieve the correct evidence?
2. Was the evidence sufficient, current, and authorized?
3. Was the answer grounded in that evidence?
4. Was the answer objectively correct?
5. Did the citations support the claims?

A grounded answer can still be wrong if its source is outdated. High retrieval relevance can still omit an important exception or effective date.

For this project:

- Vector retrieval will generally serve procedures, policies, documentation, definitions, and unstructured knowledge.
- Governed SQL and metric tools will serve quantities, forecasts, plan versions, inventory, orders, and KPI calculations.
- The Agent will not silently decide which forecast vintage or demand definition to use.
- User permissions will be enforced before retrieved content enters model context.


## Tool design

Tools will be small, typed, and permission-aware.


| Tool class | Example |
| :-- | :-- |
| Read | Retrieve Actual versus Plan for a SKU, location and week |
| Explain | Retrieve the approved KPI definition |
| Calculate | Compute a deterministic variance |
| Simulate | Compare replenishment scenarios |
| Prepare | Create a transfer proposal in Lakebase |
| Approve | Record authorized planner approval |
| Execute | Invoke an approved ERP/WMS API |
| Verify | Read back and reconcile the external action |

Production Agents will not receive unrestricted:

- SQL execution.
- Python execution.
- Shell access.
- HTTP access.
- Filesystem access.
- Secret retrieval.
- Lakebase mutation.
- ERP/WMS API access.

Tool names and descriptions influence Agent behavior, so tool-description changes will be evaluated like prompt changes.

## Traditional ML

Forecasting models will use a separate traditional ML lifecycle:

1. Define target, grain, horizon, forecast origin and planning decision.
2. Preserve plan and forecast vintages.
3. Establish seasonal-naive and incumbent baselines.
4. Use time-aware backtesting.
5. Evaluate at both operational grain and hierarchy rollups.
6. Track the data snapshot, parameters, code, environment, features and artifacts.
7. Validate the logged model before deployment.
8. Register approved models in Unity Catalog.
9. Use controlled model aliases such as `champion`.
10. Deploy through batch inference or Model Serving according to latency needs.
11. Monitor predictions against actual outcomes.
12. Retrain or roll back under defined rules.

MLflow’s traditional ML capabilities cover experiment tracking, model evaluation, Model Registry, deployment, and lifecycle management.[^17_15]

Model Registry maintains lineage, versions, metadata and aliases. An alias can identify the selected deployment version without relying on deprecated stage-style processes.[^17_16][^17_17]

For scheduled supply-chain forecasting, batch inference may be more appropriate than a continuously available endpoint. Model Serving will be chosen when an interactive or event-driven prediction requirement justifies it.

## Production gates

An AI release must pass:

- Contract and schema tests.
- Golden and regression suites.
- Adversarial tests.
- Deterministic business-rule tests.
- Judge-to-human validation.
- Identity and least-privilege tests.
- Latency and cost budgets.
- Cancellation and timeout tests.
- Lakebase transaction tests.
- Action idempotency and verification.
- Model/prompt/tool/index version pinning.
- Rollback testing.
- Production monitoring readiness.

Production must also provide:

- Canary or limited-user rollout.
- Action kill switch.
- Read-only degraded mode.
- Model and prompt rollback.
- Endpoint health monitoring.
- Scheduled quality scoring.
- Planner feedback capture.
- Operational incident ownership.


## Expanded default

**Milwaukee Supply Chain Databricks FDE mode** now also means:

> Use current MLflow best practices for traditional ML and GenAI. Prefer `ResponsesAgent` for new custom Agents. Select single-Agent, supervisor, or multi-agent architecture based on proven need. Version models, prompts, tools, retrieval indexes, datasets, judges, and Agent code. Trace development and production behavior. Evaluate using deterministic scorers, LLM judges, human feedback, operational metrics, and business outcomes. Never use an LLM judge where exact code can establish truth. Align judges with domain experts, maintain holdout data, test adversarial and action-safety scenarios, monitor quality/latency/cost, govern access through Unity AI Gateway, and provide canary, rollback, degraded mode, and an independent action kill switch.

This will be a living standard because MLflow and Databricks Agent capabilities evolve quickly; specific APIs and product maturity will be reverified before implementation.

<span style="display:none">[^17_100][^17_101][^17_102][^17_103][^17_104][^17_105][^17_106][^17_107][^17_108][^17_109][^17_110][^17_111][^17_112][^17_113][^17_114][^17_115][^17_116][^17_117][^17_118][^17_119][^17_120][^17_121][^17_122][^17_123][^17_124][^17_125][^17_126][^17_127][^17_128][^17_129][^17_130][^17_131][^17_132][^17_133][^17_134][^17_135][^17_136][^17_137][^17_138][^17_139][^17_140][^17_141][^17_142][^17_143][^17_144][^17_145][^17_146][^17_147][^17_148][^17_149][^17_150][^17_151][^17_152][^17_153][^17_154][^17_155][^17_156][^17_157][^17_158][^17_159][^17_160][^17_161][^17_162][^17_163][^17_164][^17_165][^17_166][^17_167][^17_168][^17_169][^17_170][^17_171][^17_172][^17_173][^17_174][^17_175][^17_176][^17_177][^17_178][^17_179][^17_18][^17_180][^17_181][^17_182][^17_183][^17_184][^17_185][^17_186][^17_187][^17_188][^17_189][^17_19][^17_190][^17_191][^17_192][^17_193][^17_194][^17_195][^17_196][^17_197][^17_198][^17_199][^17_20][^17_200][^17_201][^17_202][^17_203][^17_204][^17_205][^17_206][^17_207][^17_208][^17_209][^17_21][^17_210][^17_211][^17_212][^17_213][^17_214][^17_215][^17_216][^17_217][^17_218][^17_219][^17_22][^17_220][^17_221][^17_222][^17_223][^17_224][^17_225][^17_226][^17_227][^17_228][^17_229][^17_23][^17_230][^17_231][^17_232][^17_233][^17_234][^17_235][^17_236][^17_237][^17_238][^17_239][^17_24][^17_240][^17_241][^17_242][^17_243][^17_244][^17_245][^17_246][^17_247][^17_248][^17_249][^17_25][^17_250][^17_251][^17_252][^17_253][^17_254][^17_255][^17_256][^17_257][^17_258][^17_259][^17_26][^17_260][^17_261][^17_262][^17_263][^17_264][^17_265][^17_266][^17_267][^17_268][^17_269][^17_27][^17_270][^17_271][^17_272][^17_273][^17_274][^17_275][^17_276][^17_277][^17_278][^17_279][^17_28][^17_280][^17_281][^17_282][^17_283][^17_284][^17_285][^17_286][^17_287][^17_288][^17_289][^17_29][^17_290][^17_291][^17_292][^17_293][^17_294][^17_295][^17_296][^17_297][^17_298][^17_299][^17_30][^17_300][^17_301][^17_302][^17_303][^17_304][^17_305][^17_306][^17_307][^17_308][^17_309][^17_31][^17_310][^17_311][^17_312][^17_313][^17_314][^17_315][^17_316][^17_317][^17_318][^17_319][^17_32][^17_320][^17_321][^17_322][^17_323][^17_324][^17_325][^17_326][^17_327][^17_328][^17_329][^17_33][^17_330][^17_331][^17_332][^17_333][^17_334][^17_335][^17_336][^17_337][^17_338][^17_339][^17_34][^17_340][^17_341][^17_342][^17_343][^17_344][^17_345][^17_346][^17_347][^17_348][^17_349][^17_35][^17_350][^17_351][^17_352][^17_353][^17_354][^17_355][^17_356][^17_357][^17_358][^17_359][^17_36][^17_360][^17_361][^17_362][^17_363][^17_364][^17_365][^17_366][^17_367][^17_368][^17_369][^17_37][^17_370][^17_371][^17_372][^17_373][^17_374][^17_375][^17_376][^17_377][^17_378][^17_379][^17_38][^17_380][^17_381][^17_382][^17_383][^17_384][^17_385][^17_386][^17_387][^17_388][^17_389][^17_39][^17_390][^17_391][^17_392][^17_393][^17_394][^17_395][^17_396][^17_397][^17_398][^17_399][^17_40][^17_400][^17_401][^17_402][^17_403][^17_404][^17_405][^17_406][^17_407][^17_408][^17_409][^17_41][^17_410][^17_411][^17_412][^17_413][^17_414][^17_415][^17_416][^17_417][^17_418][^17_419][^17_42][^17_420][^17_421][^17_422][^17_423][^17_424][^17_425][^17_426][^17_427][^17_428][^17_429][^17_43][^17_430][^17_431][^17_432][^17_433][^17_434][^17_435][^17_436][^17_437][^17_438][^17_439][^17_44][^17_440][^17_441][^17_442][^17_443][^17_444][^17_445][^17_446][^17_447][^17_448][^17_449][^17_45][^17_450][^17_451][^17_452][^17_453][^17_454][^17_455][^17_456][^17_457][^17_458][^17_459][^17_46][^17_460][^17_461][^17_462][^17_463][^17_464][^17_465][^17_466][^17_467][^17_468][^17_469][^17_47][^17_470][^17_471][^17_472][^17_473][^17_474][^17_475][^17_476][^17_477][^17_478][^17_479][^17_48][^17_480][^17_481][^17_482][^17_483][^17_484][^17_485][^17_486][^17_487][^17_488][^17_489][^17_49][^17_490][^17_491][^17_492][^17_493][^17_494][^17_495][^17_496][^17_497][^17_498][^17_499][^17_50][^17_500][^17_501][^17_502][^17_503][^17_504][^17_505][^17_506][^17_507][^17_508][^17_509][^17_51][^17_510][^17_511][^17_512][^17_513][^17_514][^17_515][^17_516][^17_517][^17_518][^17_519][^17_52][^17_520][^17_53][^17_54][^17_55][^17_56][^17_57][^17_58][^17_59][^17_60][^17_61][^17_62][^17_63][^17_64][^17_65][^17_66][^17_67][^17_68][^17_69][^17_70][^17_71][^17_72][^17_73][^17_74][^17_75][^17_76][^17_77][^17_78][^17_79][^17_80][^17_81][^17_82][^17_83][^17_84][^17_85][^17_86][^17_87][^17_88][^17_89][^17_90][^17_91][^17_92][^17_93][^17_94][^17_95][^17_96][^17_97][^17_98][^17_99]</span>

<div align="center">⁂</div>

[^17_1]: https://mlflow.org/docs/latest/genai/serving/responses-agent/

[^17_2]: https://mlflow.org/docs/latest/genai/flavors/responses-agent-intro/

[^17_3]: https://mlflow.org/docs/latest/genai/flavors/chat-model-guide/

[^17_4]: https://docs.databricks.com/gcp/en/agents/tutorials/agent-quickstart

[^17_5]: https://mlflow.org/docs/latest/python_api/mlflow.types.html

[^17_6]: https://mlflow.org/docs/latest/genai/serving/agent-server/

[^17_7]: https://docs.databricks.com/aws/en/agents/

[^17_8]: https://docs.databricks.com/aws/en/agents/agent-bricks/multi-agent-supervisor

[^17_9]: https://mlflow.org/docs/latest/ml/model-registry/workflow/

[^17_10]: https://mlflow.org/docs/latest/ml/model-registry/

[^17_11]: https://mlflow.org/docs/latest/ml/traditional-ml/

[^17_12]: https://mlflow.org/docs/latest/ml/model/

[^17_13]: https://docs.databricks.com/gcp/en/machine-learning/concepts/ml-capabilities

[^17_14]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/

[^17_15]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/response-quality/correctness/

[^17_16]: https://mlflow.org/docs/latest/genai/datasets/

[^17_17]: https://mlflow.org/docs/latest/genai/eval-monitor/

[^17_18]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/custom-judges/

[^17_19]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/memalign/

[^17_20]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/alignment/

[^17_21]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/workflow/

[^17_22]: https://mlflow.org/docs/latest/genai/eval-monitor/running-evaluation/traces/

[^17_23]: https://mlflow.org/docs/latest/genai/tracing/prod-tracing/

[^17_24]: https://mlflow.org/docs/latest/python_api/mlflow.genai.html

[^17_25]: https://mlflow.org/docs/latest/genai/prompt-registry/

[^17_26]: https://mlflow.org/docs/latest/genai/prompt-registry/rewrite-prompts/

[^17_27]: https://docs.databricks.com/gcp/en/agents/tutorials/ai-cookbook/evaluate-enable-measurement

[^17_28]: https://docs.databricks.com/aws/en/ai-gateway/

[^17_29]: https://docs.databricks.com/aws/en/agents/custom-agents/build-agents

[^17_30]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/response-quality/safety/

[^17_31]: https://docs.databricks.com/aws/en/agents/custom-agents/author-agent

[^17_32]: https://docs.databricks.com/gcp/en/agents/custom-agents/query-agent

[^17_33]: https://docs.databricks.com/aws/en/mlflow3/genai/agent-eval-migration

[^17_34]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/custom/code-examples/

[^17_35]: https://mlflow.org/docs/latest/ml/deployment/

[^17_36]: https://mlflow.org/docs/latest/api_reference/\_modules/mlflow/genai/judges/base.html

[^17_37]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/custom-optimizers/

[^17_38]: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/simba/

[^17_39]: https://mlflow.org/docs/latest/genai/concepts/scorers/

[^17_40]: https://docs.databricks.com/aws/en/release-notes/product/2025/march

[^17_41]: https://docs.databricks.com/aws/en/ldp/developer/python-ref

[^17_42]: https://docs.databricks.com/gcp/en/dev-tools/ci-cd/flows

[^17_43]: https://docs.databricks.com/gcp/en/lakehouse-architecture/data-governance/best-practices

[^17_44]: https://docs.databricks.com/aws/en/ldp/concepts

[^17_45]: https://docs.databricks.com/gcp/en/dev-tools/bundles/faqs

[^17_46]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

[^17_47]: https://docs.databricks.com/aws/en/ldp/

[^17_48]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/

[^17_49]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/unity-catalog

[^17_50]: https://docs.databricks.com/aws/en/ldp/best-practices/

[^17_51]: https://docs.databricks.com/aws/en/dev-tools/bundles/

[^17_52]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started

[^17_53]: https://docs.databricks.com/aws/en/ldp/real-time

[^17_54]: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

[^17_55]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/

[^17_56]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/

[^17_57]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/testing

[^17_58]: https://docs.databricks.com/aws/en/tables/clustering

[^17_59]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/pytest

[^17_60]: https://docs.databricks.com/aws/en/lakehouse-architecture/reference

[^17_61]: https://docs.databricks.com/gcp/fr/dev-tools/vscode-ext/pytest

[^17_62]: https://docs.databricks.com/aws/en/machine-learning/model-serving/custom-models

[^17_63]: https://docs.databricks.com/aws/en/delta/tutorial

[^17_64]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/

[^17_65]: https://docs.databricks.com/aws/en/mlflow3/genai/

[^17_66]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/databricks-connect

[^17_67]: https://docs.databricks.com/aws/en/mlflow/

[^17_68]: https://docs.databricks.com/aws/en/dev-tools/vscode-ext/tutorial

[^17_69]: https://docs.databricks.com/aws/en/ldp/developer/sql-vs-python

[^17_70]: https://docs.databricks.com/aws/en/sql/user/queries/query-profile

[^17_71]: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/observability

[^17_72]: https://docs.databricks.com/gcp/en/ldp/developer/sql-ref

[^17_73]: https://docs.databricks.com/aws/en/sql/user/queries/performance-insights

[^17_74]: https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema

[^17_75]: https://docs.databricks.com/aws/en/ldp/developer/sql-dev

[^17_76]: https://docs.databricks.com/aws/en/sql/user/queries/query-history

[^17_77]: https://docs.databricks.com/aws/en/admin/account-settings/audit-logs

[^17_78]: https://docs.databricks.com/aws/en/ldp/concepts/standalone-pipelines

[^17_79]: https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

[^17_80]: https://docs.databricks.com/aws/en/lakehouse-architecture/operational-excellence/best-practices

[^17_81]: https://docs.databricks.com/gcp/en/languages/overview

[^17_82]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-query

[^17_83]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/observability

[^17_84]: https://docs.databricks.com/aws/en/genie-agents/best-practices

[^17_85]: https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling

[^17_86]: https://docs.databricks.com/aws/en/oltp/projects/databricks-apps

[^17_87]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2026

[^17_88]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-development

[^17_89]: https://docs.databricks.com/aws/en/oltp/projects/use-cases

[^17_90]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie

[^17_91]: https://docs.databricks.com/aws/en/oltp/projects/

[^17_92]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2025

[^17_93]: https://docs.databricks.com/aws/en/release-notes/lakebase

[^17_94]: https://docs.databricks.com/aws/en/oltp/instances/create/

[^17_95]: https://docs.databricks.com/aws/en/dashboards/

[^17_96]: https://docs.databricks.com/aws/en/release-notes/product/2026/may

[^17_97]: https://docs.databricks.com/aws/en/oltp/projects/core-concepts

[^17_98]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/

[^17_99]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference

[^17_100]: https://docs.databricks.com/aws/en/query-federation/oracle

[^17_101]: https://docs.databricks.com/aws/en/ldp/expectations

[^17_102]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/local-metric-views

[^17_103]: https://docs.databricks.com/aws/en/query-federation/performance-recommendations

[^17_104]: https://docs.databricks.com/aws/en/ldp/concepts/

[^17_105]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/materialization

[^17_106]: https://docs.databricks.com/aws/en/query-federation/sqldw

[^17_107]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/

[^17_108]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques

[^17_109]: https://docs.databricks.com/aws/en/query-federation/networking

[^17_110]: https://docs.databricks.com/aws/en/ldp/expectation-patterns

[^17_111]: https://docs.databricks.com/aws/en/partners/bi/bi-metric-view

[^17_112]: https://docs.databricks.com/aws/en/query-federation/databricks

[^17_113]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/github

[^17_114]: https://docs.databricks.com/gcp/en/developers/best-practices

[^17_115]: https://docs.databricks.com/aws/en/dev-tools/bundles/tutorials

[^17_116]: https://docs.databricks.com/aws/fr/dev-tools/bundles/settings

[^17_117]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab

[^17_118]: https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks

[^17_119]: https://docs.databricks.com/aws/en/repos/get-access-tokens-from-git-provider

[^17_120]: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

[^17_121]: https://docs.databricks.com/aws/en/ldp/convert-to-dab

[^17_122]: https://docs.databricks.com/aws/en/dev-tools/bundles/python-wheel

[^17_123]: https://docs.databricks.com/aws/en/dev-tools/cli/authentication

[^17_124]: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

[^17_125]: https://docs.databricks.com/aws/en/dev-tools/terraform/

[^17_126]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy

[^17_127]: https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles

[^17_128]: https://docs.databricks.com/aws/en/dev-tools/bundles/migrate-resources

[^17_129]: https://docs.databricks.com/gcp/en/dev-tools/bundles/workspace

[^17_130]: https://docs.databricks.com/aws/en/dev-tools/bundles/reference

[^17_131]: https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands

[^17_132]: https://docs.databricks.com/gcp/en/dev-tools/bundles/work-tasks

[^17_133]: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

[^17_134]: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

[^17_135]: https://docs.databricks.com/aws/en/lakehouse-architecture/deployment-guide/iac

[^17_136]: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions

[^17_137]: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs

[^17_138]: https://docs.databricks.com/aws/en/developers/best-practices

[^17_139]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation

[^17_140]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy

[^17_141]: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

[^17_142]: https://docs.databricks.com/aws/en/notebooks/testing

[^17_143]: https://docs.databricks.com/aws/en/dev-tools/auth/provider-other

[^17_144]: https://docs.databricks.com/aws/en/notebooks/best-practices

[^17_145]: https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-provider

[^17_146]: https://docs.databricks.com/aws/en/files/files-recommendations

[^17_147]: https://docs.databricks.com/aws/en/files/workspace-modules

[^17_148]: https://docs.databricks.com/aws/en/release-notes/product/

[^17_149]: https://docs.databricks.com/aws/en/workspace/workspace-assets

[^17_150]: https://docs.databricks.com/aws/en/compute/web-terminal

[^17_151]: https://docs.databricks.com/aws/en/repos/supported-artifact-types

[^17_152]: https://docs.databricks.com/gcp/en/files/workspace

[^17_153]: https://docs.databricks.com/aws/en/volumes/volume-files

[^17_154]: https://docs.databricks.com/aws/en/repos/ci-cd

[^17_155]: https://docs.databricks.com/aws/en/notebooks/share-code

[^17_156]: https://docs.databricks.com/api/workspace-objects/v1/notebook

[^17_157]: https://docs.databricks.com/aws/en/repos/limits

[^17_158]: https://docs.databricks.com/aws/en/files/workspace-interact

[^17_159]: https://docs.databricks.com/aws/en/jobs/git

[^17_160]: https://docs.databricks.com/aws/en/repos/errors-troubleshooting

[^17_161]: https://docs.databricks.com/api/jobs/v2/job

[^17_162]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace

[^17_163]: https://docs.databricks.com/aws/en/repos/git-operations-with-repos

[^17_164]: https://docs.databricks.com/gcp/en/workspace/workspace-assets

[^17_165]: https://docs.databricks.com/aws/en/repos/repos-setup

[^17_166]: https://docs.databricks.com/gcp/en/jobs/tasks/notebook

[^17_167]: https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author

[^17_168]: https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate

[^17_169]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands

[^17_170]: https://docs.databricks.com/aws/en/tables/history

[^17_171]: https://docs.databricks.com/aws/en/security/auth/access-control/

[^17_172]: https://docs.databricks.com/aws/en/notebooks/notebooks-manage

[^17_173]: https://docs.databricks.com/aws/en/release-notes/product/2026/august

[^17_174]: https://docs.databricks.com/aws/en/files/workspace

[^17_175]: https://docs.databricks.com/aws/en/jobs/privileges

[^17_176]: https://docs.databricks.com/sap/en/security/auth/access-control/

[^17_177]: https://docs.databricks.com/api/access-management/v1/workspace-permissions

[^17_178]: https://docs.databricks.com/aws/en/workspace/workspace-objects

[^17_179]: https://docs.databricks.com/aws/en/release-notes/whats-coming

[^17_180]: https://docs.databricks.com/aws/en/security/auth/default-permissions

[^17_181]: https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services

[^17_182]: https://docs.databricks.com/aws/en/dev-tools/auth/

[^17_183]: https://docs.databricks.com/aws/en/ai-gateway/configure-ai-gateway-endpoints

[^17_184]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth

[^17_185]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-connect

[^17_186]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m

[^17_187]: https://docs.databricks.com/aws/en/oltp/projects/connection-strings

[^17_188]: https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints

[^17_189]: https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m

[^17_190]: https://docs.databricks.com/aws/en/oltp/projects/connection-pooling

[^17_191]: https://docs.databricks.com/gcp/en/machine-learning/foundation-models/external-models-tutorial

[^17_192]: https://docs.databricks.com/aws/en/oltp/projects/connect-overview

[^17_193]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/networking

[^17_194]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-to-internal-network

[^17_195]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources

[^17_196]: https://docs.databricks.com/aws/en/security/network/concepts/privatelink-concepts

[^17_197]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/

[^17_198]: https://docs.databricks.com/gcp/en/oltp/projects/databricks-apps

[^17_199]: https://docs.databricks.com/aws/en/release-notes/product/2025/august

[^17_200]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-private-endpoint-rules

[^17_201]: https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink

[^17_202]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/pl-aws-resources

[^17_203]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase

[^17_204]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management

[^17_205]: https://docs.databricks.com/gcp/en/dev-tools/cli/reference/account-network-connectivity-commands

[^17_206]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts

[^17_207]: https://docs.databricks.com/gcp/en/agents/agent-framework/author-agent

[^17_208]: https://docs.databricks.com/aws/en/agents/tutorials/agent-quickstart

[^17_209]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting

[^17_210]: https://docs.databricks.com/aws/en/machine-learning/train-model/serverless-forecasting

[^17_211]: https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/

[^17_212]: https://docs.databricks.com/aws/en/machine-learning/automl/forecasting-train-api

[^17_213]: https://docs.databricks.com/aws/en/machine-learning/

[^17_214]: https://docs.databricks.com/aws/en/release-notes/runtime/16.0ml

[^17_215]: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store

[^17_216]: https://docs.databricks.com/aws/en/machine-learning/automl/classification

[^17_217]: https://www.linkedin.com/posts/eric-stowe-39240313_demand-planning-isnt-just-forecasting-activity-7426239450915147776-EUVk

[^17_218]: https://www.hyperbots.com/glossary/sap-demand-planning

[^17_219]: https://aijcst.org/index.php/aijcst/article/download/85/76

[^17_220]: https://www.ascm.org/topics/demand-supply-planning/

[^17_221]: https://learning.sap.com/courses/exploring-end-to-end-business-processes-in-sap-business-suite/analyzing-demand-planning_c51b50fc-7ec6-43e9-96e0-5842d1122d4d

[^17_222]: https://www.suretysystems.com/insights/the-role-of-oracle-demand-planning-in-supply-chain-optimization/

[^17_223]: https://www.ascm.org/ascm-insights/beyond-the-shelf--the-cpg-demand-forecasting-edge/

[^17_224]: https://help.sap.com/docs/SAP_BUSINESS_BYDESIGN/2754875d2d2a403f95e58a41a9c7d6de/2cba842b722d1014ba90f7268f4cbf2f.html

[^17_225]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faspf/forecasting-profile-options-for-demand-plans.html

[^17_226]: https://cxtms.com/docs/knowledge-base/supply-chain-strategy/demand-planning-and-forecasting

[^17_227]: https://sapinsider.org/demand-planning-alerts-increase-the-accuracy-of-your-forecasts/

[^17_228]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspf/predefined-supply-planning-exceptions.html

[^17_229]: https://o9solutions.com/articles/what-is-demand-planning

[^17_230]: https://www.sap.com/products/scm/integrated-business-planning/features/demand-planning.html

[^17_231]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/faupc/forecast-consumption.html

[^17_232]: https://keends.com/blog/demand-planning-kpis/

[^17_233]: https://www.invent.ai/blog/forecast-accuracy-vs.-forecast-bias-what-retail-planners-need-to-track

[^17_234]: https://aws.amazon.com/blogs/supply-chain/how-to-use-demand-planning-on-aws-supply-chain-for-better-forecast-accuracy/

[^17_235]: https://plex.rockwellautomation.com/en-us/blog/role-demand-planning-kpis-supply-chain-management.html

[^17_236]: https://www.advanceschool.ch/news/forecast-accuracy-is-not-enough/

[^17_237]: https://aws.amazon.com/blogs/supply-chain/maximize-business-value-with-the-aws-supply-chain-demand-planning-process/

[^17_238]: https://www.spscommerce.com/community/articles/forecast-accuracy-and-forecast-bias-the-two-numbers-that-decide-whether-your-supply-chain-holds

[^17_239]: https://imperiascm.com/blog/demand-forecasting-bias

[^17_240]: https://www.linkedin.com/posts/tojiang_how-to-use-demand-planning-on-aws-supply-activity-7105541366805405697-I7_H

[^17_241]: https://demand-planning.com/2020/06/01/8-kpis-every-demand-planner-should-know/

[^17_242]: https://www.linkedin.com/posts/marciadwilliams_forecast-accuracy-is-not-bias-this-infographic-activity-7471902320105230336-hBJ4

[^17_243]: https://demandforecast.ai/blog/supply-chain-forecasting-tools/

[^17_244]: https://www.netsuite.com/portal/resource/articles/accounting/demand-planning-kpis-metrics.shtml

[^17_245]: https://www.relexsolutions.com/resources/measuring-forecast-accuracy/

[^17_246]: https://www.scdigest.com/ontarget/24-02-27_aws_demand_planning_news.php?cid=21284

[^17_247]: 01_Requirements.md

[^17_248]: Actuals_Supply_Plan_Requirements.md

[^17_249]: Red_Keychain_Supply_Planning_Requirements.md

[^17_250]: https://docs.oracle.com/cd/E26401_01/doc.122/e48787/T542242T634380.htm

[^17_251]: https://docs.oracle.com/en/cloud/saas/analytics/26r3/fawwn/index.html

[^17_252]: https://nycli.ascm.org/articles/Demand_Planning_for_a_Supply_Chain

[^17_253]: https://docs.oracle.com/cd/E26401_01/doc.122/e48795/T478564T478850.htm

[^17_254]: https://docs.oracle.com/cd/E18727_01/doc.121/e05136/T485796T493455.htm

[^17_255]: https://www.ascm.org/ascm-insights/are-you-having-chewy-conversations/

[^17_256]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T483484.htm

[^17_257]: https://docs.oracle.com/cd/E18727-01/doc.121/b31558/T478564T479367.htm

[^17_258]: https://www.ascm.org/ascm-insights/making-the-case-for-integrated-business-planning/

[^17_259]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fausp/predefined-supply-planning-exceptions.html

[^17_260]: https://docs.oracle.com/en/cloud/saas/human-resources/faeos/run-initial-data-ingestion.html

[^17_261]: https://www.ascm.org/ascm-insights/direct-your-supply-chain-plans-to-execution/

[^17_262]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163664509886.html

[^17_263]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/egpcatalogacl-6712.html

[^17_264]: https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/

[^17_265]: https://doc.irasia.com/listco/hk/techtronic/annual/2019/ar2019.pdf

[^17_266]: https://news.futunn.com/en/post/77330462/techtronic-industries-0669-hk-tools-hardware-series-report-profitability-continues

[^17_267]: https://www.moomoo.com/news/post/74207767/macquarie-techtronic-industries-0669-hk-h1-results-beat-expectations-target

[^17_268]: https://www.ttigroup.com/documents/annual-report-2024/files/ar24_en.pdf

[^17_269]: https://doc.irasia.com/listco/hk/techtronic/annual/2025/res.pdf

[^17_270]: https://www.linkedin.com/posts/milwaukee-tool-hk_milwaukeetool-techtronicindustries-annualresults-activity-7434596229759713281-mYt8

[^17_271]: https://www.milwaukeetool.jobs/career-areas

[^17_272]: https://www.linkedin.com/posts/shane-moll-9826a34_annual-results-2025-activity-7438257282158731265-WJH5

[^17_273]: https://www.indeed.com/q-supply-chain-milwaukee-tool-jobs.html

[^17_274]: https://dataintelo.com/report/global-milwaukee-tool-market

[^17_275]: https://www.ziprecruiter.com/e/Milwaukee-Tool-Facilities-What-are-Milwaukee-Tool-Facilities

[^17_276]: https://www.milwaukeetool.com/

[^17_277]: https://www.oracle.com/customers/milwaukee-tool/

[^17_278]: https://www.ttigroup.com/documents/annual-report-2025/

[^17_279]: https://talents.vaia.com/companies/milwaukee-electric-tool-corporation/director-distribution-25252121/

[^17_280]: https://docs.oracle.com/cd/E18727_01/doc.121/e15188/T478564T478953.htm

[^17_281]: https://docs.oracle.com/en-us/iaas/Content/fusion-applications/refresh-environment.htm

[^17_282]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faips/scp-about-oracle-fusion-cloud-supply-chain-planning.html

[^17_283]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/oedsc/overview.html

[^17_284]: https://docs.oracle.com/cd/E23549_01/core.1111/e10113/chapter_ess_messages.htm

[^17_285]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/overview-of-supply-chain-collaboration.html

[^17_286]: https://docs.oracle.com/cd/E29542_01/doc.1111/e14775/install.htm

[^17_287]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faucc/supply-collaboration-flow.html

[^17_288]: https://docs.oracle.com/en/cloud/saas/analytics/26r1/fawwn/index.html

[^17_289]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-supply-chain-planning-work-areas.html

[^17_290]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egpitemacl-28715.html

[^17_291]: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmrn/26a/26a.htm

[^17_292]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/inv/planattr.htm

[^17_293]: https://docs.oracle.com/cd/B53825_14/current/acrobat/121msdug.pdf

[^17_294]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471621.htm

[^17_295]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T309478.htm

[^17_296]: https://docs.oracle.com/cd/E79783_08/current/acrobat/122ontug.pdf

[^17_297]: https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/demand25c/25C-demand-wn-f38205.htm

[^17_298]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faurp/how-order-modifiers-are-applied-when-replenishments-are.html

[^17_299]: https://docs.oracle.com/cd/V77972_02/current/acrobat/122cspug.pdf

[^17_300]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/faurp/overview-of-oracle-replenishment-planning.html

[^17_301]: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159172238892.html

[^17_302]: https://docs.oracle.com/cd/E26401_01/doc.122/e48843/T335476T429677.htm

[^17_303]: https://docs.oracle.com/cd/E18727_01/doc.121/e13358/T309464T471623.htm

[^17_304]: https://docs.oracle.com/cd/A60725_05/html/comnls/us/mrp/ordmod.htm

[^17_305]: https://docs.oracle.com/cd/E26401_01/doc.122/e48758.pdf

[^17_306]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faurp/example-of-end-item-substitution-and-supersession-with-inventory-rebalancing.html

[^17_307]: https://www.hyperbots.com/glossary/target-gap-analysis

[^17_308]: https://app.achievable.me/study/cma-part-1/learn/performance-management-cost-and-variance-measures-comparison-of-actual-to-planned-results-1

[^17_309]: https://www.spscommerce.com/community/articles/what-is-a-supply-plan

[^17_310]: https://www.linkedin.com/posts/marciadwilliams_a-target-is-not-a-forecast-confusing-the-activity-7481319567508746240-l8Hr

[^17_311]: https://www.ibm.com/think/topics/variance-analysis

[^17_312]: https://www.linkedin.com/posts/marciadwilliams_supply-planners-do-not-move-without-the-calendar-activity-7443993617133658112-7omO

[^17_313]: https://lean6sigmahub.com/analyse-phase-creating-gap-analysis-between-current-and-target-state-in-lean-six-sigma/

[^17_314]: https://www.cfoedge.com/blog/financial-planning/financial-analysis/variance-analysis-assess-kpi-deviations-to-improve-results/

[^17_315]: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fausp/how-you-compare-supply-plans-and-orders.html

[^17_316]: https://www.kristechwire.com/supply-chain-metrics-glossary/

[^17_317]: https://mercury.com/blog/favorable-vs-unfavorable-variance

[^17_318]: https://www.scmglobe.com/a-2-week-supply-chain-resilience-sprint-map-stress‑test-decide/

[^17_319]: https://blog.arkieva.com/target-inventory-central-planning-engines/

[^17_320]: https://www.abacum.ai/blog/how-to-use-budget-vs-actuals-variance-analysis-to-improve-fp-a-outcomes

[^17_321]: https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-plan-stability-index/

[^17_322]: https://docs.databricks.com/aws/en/oltp/projects/sync-tables

[^17_323]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-text

[^17_324]: https://docs.databricks.com/aws/en/oltp/projects/data-api

[^17_325]: https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table

[^17_326]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-search

[^17_327]: https://docs.databricks.com/aws/en/integrations/excel-write-back

[^17_328]: https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf

[^17_329]: https://docs.databricks.com/aws/en/oltp/projects/register-uc

[^17_330]: https://docs.databricks.com/aws/en/ai-search/ai-search

[^17_331]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

[^17_332]: https://docs.databricks.com/gcp/en/oltp/projects/sync-tables

[^17_333]: https://docs.databricks.com/aws/en/oltp/projects/extensions

[^17_334]: https://docs.databricks.com/aws/en/genie-agents/monitor

[^17_335]: https://docs.databricks.com/aws/en/genie-agents/concepts

[^17_336]: https://docs.databricks.com/gcp/en/genie-agents/concepts

[^17_337]: https://docs.databricks.com/api/genie/v1/conversation

[^17_338]: https://docs.databricks.com/api/genie/v1

[^17_339]: https://docs.databricks.com/aws/en/genie-agents/conversation-api

[^17_340]: https://docs.databricks.com/aws/en/ai-bi/release-notes/2024

[^17_341]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/

[^17_342]: https://docs.databricks.com/aws/en/genie-agents/set-up

[^17_343]: https://docs.databricks.com/api/genie/v1/agent-mode-list-conversation-items

[^17_344]: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/

[^17_345]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/

[^17_346]: https://docs.databricks.com/aws/en/ldp/concepts/materialized-views

[^17_347]: https://docs.databricks.com/aws/en/machine-learning/feature-store/concepts

[^17_348]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools

[^17_349]: https://docs.databricks.com/gcp/en/ldp/best-practices

[^17_350]: https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-materialized-view

[^17_351]: https://docs.databricks.com/aws/en/machine-learning/concepts/ml-lifecycle

[^17_352]: https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/

[^17_353]: https://docs.databricks.com/aws/en/oltp/projects/dev-workflow-tutorial

[^17_354]: https://docs.databricks.com/aws/en/oltp/projects/backup-methods

[^17_355]: https://docs.databricks.com/aws/en/data-engineering/schema-evolution

[^17_356]: https://docs.databricks.com/aws/en/oltp/upgrade-to-autoscaling

[^17_357]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/sql-warehouse

[^17_358]: https://docs.databricks.com/aws/en/oltp/projects/branches

[^17_359]: https://docs.databricks.com/aws/pt/release-notes/lakebase/

[^17_360]: https://docs.databricks.com/aws/en/oltp/projects/manage-branches

[^17_361]: https://docs.databricks.com/aws/en/oltp/projects/manage-disaster-recovery

[^17_362]: https://docs.databricks.com/aws/en/oltp/projects/dabs-typical-project

[^17_363]: https://docs.databricks.com/aws/en/oltp/projects/high-availability

[^17_364]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^17_365]: https://docs.databricks.com/api/apps/v1/app

[^17_366]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-node

[^17_367]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime

[^17_368]: https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-apps

[^17_369]: https://docs.databricks.com/gcp/en/agents/custom-agents/debug-agent

[^17_370]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/deploy

[^17_371]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices

[^17_372]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/key-concepts

[^17_373]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets

[^17_374]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/connect-local

[^17_375]: https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial

[^17_376]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/view-app-details

[^17_377]: https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api

[^17_378]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/model-serving

[^17_379]: https://docs.databricks.com/api/model-serving/v1/serving-endpoint

[^17_380]: https://docs.databricks.com/api/jobs/v2/run

[^17_381]: https://docs.databricks.com/aws/en/machine-learning/model-serving/store-env-variable-model-serving

[^17_382]: https://docs.databricks.com/gcp/en/machine-learning/model-serving/manage-serving-endpoints

[^17_383]: https://docs.databricks.com/aws/en/oltp/projects/automate-with-terraform

[^17_384]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/

[^17_385]: https://www.holistics.io/blog/the-three-types-of-fact-tables/

[^17_386]: https://www.databricks.com/blog/five-simple-steps-for-implementing-a-star-schema-in-databricks-with-delta-lake

[^17_387]: https://www.kimballgroup.com/2003/03/declaring-the-grain/

[^17_388]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-4-complex-fact-table-patterns/accumulating-snapshot-fact-tables

[^17_389]: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering

[^17_390]: https://www.kimballgroup.com/2008/11/fact-tables/

[^17_391]: https://www.kimballgroup.com/2012/05/design-tip-145-time-stamping-accumulating-snapshot-fact-tables/

[^17_392]: https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling

[^17_393]: https://dev.to/alexmercedcoder/dimensional-modeling-facts-dimensions-and-grains-3obm

[^17_394]: https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/

[^17_395]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/

[^17_396]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/

[^17_397]: https://www.linkedin.com/posts/jrlasak\_%F0%9D%97%9F%F0%9D%97%B6%F0%9D%97%BE%F0%9D%98%82%F0%9D%97%B6%F0%9D%97%B1-%F0%9D%97%96%F0%9D%97%B9%F0%9D%98%82%F0%9D%98%80%F0%9D%98%81%F0%9D%97%B2%F0%9D%97%BF%F0%9D%97%B6%F0%9D%97%BB%F0%9D%97%B4-%F0%9D%98%83%F0%9D%98%80-%F0%9D%97%AD-%F0%9D%97%A2%F0%9D%97%BF%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF-activity-7445032276314238976-c6EB

[^17_398]: https://kimballgroup.forumotion.net/t1496-difference-between-factless-fact-and-bridge-table

[^17_399]: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/

[^17_400]: https://bigbear.ai/blog/bridge-tables-deep-dive/

[^17_401]: https://www.reddit.com/r/dataengineering/comments/1pbro6t/kimball_confusion_semi_additive_vs_fully_additive/

[^17_402]: https://datadef.io/guides/en/dimensional-modeling

[^17_403]: https://www.kimballgroup.com/2012/02/design-tip-142-building-bridges/

[^17_404]: https://docs.thoughtspot.com/cloud/26.8.0.cl/semi-additive-measures.html

[^17_405]: https://www.kimballgroup.com/2005/12/the-matrix-revisited/

[^17_406]: https://community.sisense.com/forum/how-tos-faqs-43/topic/many-to-many-multivalued-dimension-4698/

[^17_407]: https://apxml.com/courses/data-modeling-schema-design-analytics/chapter-2-dimensional-modeling-core/fact-tables-fundamentals

[^17_408]: https://arxiv.org/html/2606.27571v2

[^17_409]: https://datawarehouseinfo.com/practice/advanced-dimensional-modeling/

[^17_410]: https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-fact-tables

[^17_411]: https://talkingschema.ai/docs/glossary/conformed-dimension

[^17_412]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions

[^17_413]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins

[^17_414]: https://docs.databricks.com/aws/en/ldp/dbsql/materialized

[^17_415]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/yaml-reference

[^17_416]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/create

[^17_417]: https://docs.databricks.com/aws/en/ldp/cdc

[^17_418]: https://docs.databricks.com/sap/en/release-notes/sql

[^17_419]: https://docs.databricks.com/gcp/en/uc-semantics/metric-views/basic-modeling

[^17_420]: https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables

[^17_421]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints

[^17_422]: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select

[^17_423]: https://www.linkedin.com/pulse/understanding-medallion-architecture-databricks-bronze-chaudhari-rsrmf

[^17_424]: https://community.databricks.com/t5/community-articles/medallion-architecture-in-practice-the-design-decisions-nobody/td-p/163206

[^17_425]: https://community.databricks.com/t5/data-engineering/medallion-architecture-and-databricks-assistant/td-p/102301

[^17_426]: https://erstudio.com/blog/understanding-the-three-layers-of-medallion-architecture/

[^17_427]: https://erstudio.com/blog/how-medallion-architecture-with-er-studio-and-databricks-solves-data-as-a-product-for-both-business-and-it/

[^17_428]: https://cosmosthrace.com/resources/databricks/databricks-medallion-architecture-best-practices

[^17_429]: https://www.databricks.com/blog/what-is-medallion-architecture

[^17_430]: https://www.reddit.com/r/databricks/comments/1c93t94/medallion_architecture/

[^17_431]: https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825

[^17_432]: https://tacnode.io/post/medallion-architecture

[^17_433]: https://community.databricks.com/t5/data-engineering/medallion-architecture-do-i-need-a-materialized-exploded-layer/td-p/139085

[^17_434]: https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion

[^17_435]: https://www.reddit.com/r/databricks/comments/1j0gyd5/best_practices_for_medallion_architecture_in/

[^17_436]: https://docs.databricks.com/aws/en/lakehouse/medallion

[^17_437]: https://www.reddit.com/r/databricks/comments/173p6ev/bronzesilvergold_what_really_happens_in_each/

[^17_438]: https://docs.databricks.com/aws/en/dashboards/genie-spaces

[^17_439]: https://docs.databricks.com/aws/en/ai-bi/admin/use-apis

[^17_440]: https://docs.databricks.com/aws/en/integrations/msft-teams

[^17_441]: https://docs.databricks.com/aws/en/ai-bi/admin/embed

[^17_442]: https://docs.databricks.com/aws/en/genie-one/

[^17_443]: cursor_databricks_project_upload_cleanu.md

[^17_444]: https://docs.databricks.com/aws/en/ldp/limitations

[^17_445]: https://docs.databricks.com/aws/en/jobs/

[^17_446]: https://docs.databricks.com/aws/en/jobs/compute

[^17_447]: https://docs.databricks.com/aws/en/jobs/jobs-quickstart

[^17_448]: https://docs.databricks.com/aws/en/jobs/control-flow

[^17_449]: https://docs.databricks.com/aws/en/getting-started/best-practices

[^17_450]: https://docs.databricks.com/aws/en/jobs/run-serverless-jobs

[^17_451]: https://docs.databricks.com/aws/en/oltp/projects/manage-projects

[^17_452]: https://docs.databricks.com/aws/en/dashboards/limits

[^17_453]: https://docs.databricks.com/aws/en/resources/limits

[^17_454]: https://docs.databricks.com/aws/en/dev-tools/auth/pat

[^17_455]: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations

[^17_456]: https://docs.databricks.com/gcp/en/dashboards/concepts

[^17_457]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage

[^17_458]: https://docs.databricks.com/gcp/en/query-federation/performance-recommendations

[^17_459]: https://docs.databricks.com/aws/en/query-federation/database-federation

[^17_460]: https://docs.databricks.com/gcp/en/query-federation/salesforce-data-cloud

[^17_461]: https://docs.databricks.com/aws/en/query-federation/snowflake

[^17_462]: https://docs.databricks.com/aws/en/query-federation/remote-queries

[^17_463]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions

[^17_464]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration

[^17_465]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/environment-variables

[^17_466]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy

[^17_467]: https://docs.databricks.com/aws/en/dev-tools/cli/reference/apps-commands

[^17_468]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/functions

[^17_469]: https://docs.databricks.com/aws/en/agents/mcp-tools/custom-mcp

[^17_470]: https://docs.databricks.com/aws/en/compute/serverless/notebooks

[^17_471]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/

[^17_472]: https://docs.databricks.com/aws/en/release-notes/runtime/maintenance-updates

[^17_473]: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/

[^17_474]: https://docs.databricks.com/aws/en/release-notes/runtime/17.0

[^17_475]: https://docs.databricks.com/aws/en/release-notes/runtime/15.2

[^17_476]: https://docs.databricks.com/aws/en/release-notes/runtime/18.0

[^17_477]: https://docs.databricks.com/aws/en/release-notes/runtime/16.3

[^17_478]: https://docs.databricks.com/aws/en/spark/api-options

[^17_479]: https://docs.databricks.com/aws/en/admin/system-tables/jobs

[^17_480]: https://docs.databricks.com/aws/en/connect/streaming/kafka/

[^17_481]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/monitor

[^17_482]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/system-env

[^17_483]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/connect-local

[^17_484]: https://learn.microsoft.com/en-us/answers/questions/1820098/cors-issues-between-azure-static-web-apps-and-azur

[^17_485]: https://docs.databricks.com/aws/en/security/network/front-end/

[^17_486]: https://www.databricks.com/blog/building-databricks-apps-react-and-mosaic-ai-agents-enterprise-chat-solutions

[^17_487]: https://docs.databricks.com/aws/en/partners/bi/power-bi/

[^17_488]: https://kb.databricks.com/security/cors-policy-error-when-trying-to-run-databricks-api-from-a-browser-based-application

[^17_489]: https://community.databricks.com/t5/get-started-discussions/facing-cors-issue-while-calling-databricks-rest-api-from-a-react/td-p/52268

[^17_490]: https://fastapi.tiangolo.com/tutorial/cors/

[^17_491]: https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies

[^17_492]: https://stackoverflow.com/questions/75952412/azure-databricks-rest-api-blocked-by-cors-policy-while-making-request-through-re

[^17_493]: https://docs.databricks.com/aws/en/resources/ip-domain-region

[^17_494]: https://qubika.com/blog/building-modern-full-stack-react-fastapi-databricks-lakebase/

[^17_495]: https://docs.databricks.com/gcp/en/sparkr/shiny

[^17_496]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/create-custom-app

[^17_497]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started

[^17_498]: https://docs.databricks.com/aws/en/dev-tools/ssh-tunnel

[^17_499]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/horizontal-scaling

[^17_500]: https://docs.databricks.com/api/statement-execution/v1

[^17_501]: https://docs.databricks.com/aws/en/dev-tools/python-sql-connector

[^17_502]: https://docs.databricks.com/aws/en/compute/configure

[^17_503]: https://docs.databricks.com/aws/en/dev-tools/nodejs-sql-driver

[^17_504]: https://docs.databricks.com/aws/en/oltp/projects/authentication

[^17_505]: https://docs.databricks.com/api/clusters/v2/cluster

[^17_506]: https://docs.databricks.com/api/workspace/scopes

[^17_507]: https://docs.databricks.com/aws/en/integrations/jdbc-oss/properties

[^17_508]: https://docs.databricks.com/aws/en/oltp/projects/manage-computes

[^17_509]: https://docs.databricks.com/gcp/en/sql/release-notes/2024

[^17_510]: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/embed

[^17_511]: https://docs.databricks.com/aws/ja/dev-tools/databricks-apps/embed

[^17_512]: https://docs.databricks.com/gcp/en/dashboards/share/embedding/basic

[^17_513]: https://docs.databricks.com/gcp/en/ai-bi/admin/embed

[^17_514]: https://docs.databricks.com/aws/pt/ai-bi/admin/embed

[^17_515]: https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/networking

[^17_516]: https://docs.databricks.com/aws/en/dashboards/share/embedding/basic

[^17_517]: https://docs.databricks.com/aws/en/genie-agents/embed

[^17_518]: https://docs.databricks.com/aws/en/dashboards/tutorials/dashboard-crud-api

[^17_519]: https://docs.databricks.com/aws/en/notebooks/notebook-media

[^17_520]: https://docs.databricks.com/aws/en/dashboards/share/embedding/external-embed


---

# Now, I don't just want the Databricks Apps to be another one way dashboard equivalent.

I want it to be actionable and for that, I would like to use lakebase.. to show transactions actions .. we can use lakebase sync and reverse ETLs .. but let's say, there is some action that some persona needs to make, so that the delay, lag or loss can be mitigated .. or if on a click of a button, an alert needs to be sent to someone... then it should be possible .. from the UI itself, the user should be able to see the actions to approve, deny, other actions with drop downs ..
Let's say that the PO order or the Demand forecast is something... and based on that the orders are been made, but if the end user wants to change that instead of 10 inventory items, they want 20 or 5, they should be able to enter that with a comment and that should not only reflect on the UI, but also should be propagated to lakebase, then to the delta tables, if possible. .. and this is just one example.. another can be: lakebase search instead of Databricks Vector SEarch index .. to search for anything that is required! and is impactful to the business .. and at the same time, when clicked upon after the search, we should be able to include more actions ..

and at realtime, you can see the impact in the trends thereby improving the whole system!

expand your horizons, these are just two examples.. we can come up with unique Databricks things that can be done for each item of the priorities!

Exactly—this should become a **supply-chain control-tower application**, not a one-way dashboard with a chatbot attached.

The right product is a closed loop:

```text
Detect
  → Explain
  → Simulate
  → Propose
  → Review
  → Approve / deny / edit
  → Execute or publish
  → Verify
  → Measure outcome
  → Improve the rules, model, and planner experience
```

Your requirements already point strongly in this direction. The Demand Planning Event App needs concurrent event editing, locking, a granular before/after audit trail, planner overrides, comments, an Active/In Progress/Deactivated lifecycle, daily publication to Oracle-facing output tables, and a pre-publish validation summary. The Red Keychain requirements go further: PO actions must flow back to Oracle Fusion, planners need bulk actions, the system must choose between new ordering and inventory rebalancing, and planner decisions/outcomes should feed back into the optimizer.[^18_1][^18_2]

## Product vision

The Databricks App should be a **planner workbench** composed of several connected surfaces—not merely charts:


| Surface | Planner purpose | Primary system of record |
| :-- | :-- | :-- |
| Control tower | See what needs attention now | Delta / Unity Catalog |
| Exception queue | Prioritize shortages, late POs, excess and volatility | Delta plus Lakebase case state |
| Investigation view | Understand actual-versus-plan variance and root cause | Delta / governed metrics |
| Scenario studio | Compare proposed quantity, timing, sourcing, transfer, and allocation choices | Delta inputs + deterministic logic/ML |
| Action workbench | Edit, prepare, group, approve, deny, release, and track actions | Lakebase |
| Event manager | Create and modify demand events and forecast overrides | Lakebase → Delta publication |
| Search workspace | Find exceptions, POs, suppliers, SKUs, events, plans, comments, and actions | Lakebase search + Delta/SQL retrieval |
| Outcome view | Show whether actions reduced risk or improved planning | Delta historical outcomes + MLflow traces |

This directly supports the stated objective of giving supply planners a fast view of what was planned versus what happened, identifying root causes, taking action, and confirming that the current plan reflects the adjustment.[^18_3]

## Lakebase as action system

Lakebase should be the **transactional workflow and action-control plane**. Delta remains the analytical history and scalable reporting layer.

```text
Unity Catalog + Delta
  - Plan snapshots
  - Actual receipts, shipments, on-hand
  - Forecasts and events
  - Exception evaluations
  - Supplier / item / org context
  - Historical outcomes
              │
              ▼
FastAPI policy and orchestration layer
              │
              ▼
Lakebase PostgreSQL
  - Planner work queues
  - Saved searches
  - Drafts and overrides
  - Comments
  - Record locks
  - Approval workflow
  - Action commands
  - Idempotency records
  - External action status
  - Audit trail
              │
              ▼
Oracle Fusion / Oracle SCC / WMS / TMS / notification channels
              │
              ▼
Verification and outcome publication to Delta
```

This separation fits your requirements particularly well:

- Delta is best for historical supply plans, snapshots, actuals, trend analysis, forecast evaluation, exception evidence, and dashboards.
- Lakebase is best for mutable planner state: “I changed 10 to 20,” “I deny this recommendation,” “I need approval,” “this PO action was sent,” and “the receiver confirmed it.”
- Oracle Fusion, Oracle SCC, WMS, TMS, and other operational systems remain authoritative for the actual enterprise transaction when the scope requires it.

Lakebase should not become a second EDW, and Delta should not be misused as a concurrent human-edit workflow database.

## Example: quantity change

Your “10 inventory items to 20 or 5” example should be implemented as a governed **command**, not a direct table edit.

### Planner experience

The planner sees an exception or proposed action:

```text
SKU: 48-22-xxxx
Supplier: TTi
Organization: DC 2012
Current planned PO quantity: 10
Recommended quantity: 20
Reason: projected safety-stock breach in Week 42
Business impact: 4,800 units at risk; estimated $X exposure
```

They may:

- Accept the recommendation.
- Change the quantity to 5, 10, 20, or another permitted value.
- Select a reason code.
- Enter a required comment.
- Choose a target date, supplier, DC, or other valid action attributes.
- Save as draft.
- Submit for approval.
- Approve or deny if authorized.
- Request additional analysis.
- Convert the request to a rebalance/transfer instead of a new PO.
- Add the action to a bulk release group.


### Transaction model

The App should write an immutable command and audit event in Lakebase, not overwrite history:

```text
action_request
  action_request_id
  action_type                  -- PO_QTY_CHANGE
  status                       -- DRAFT / SUBMITTED / APPROVED / EXECUTING / SUCCEEDED / FAILED
  business_key                 -- PO line / SKU / org
  proposed_quantity
  original_quantity
  reason_code
  planner_comment
  source_exception_id
  policy_version
  requested_by
  requested_at
  record_version
  idempotency_key
  external_correlation_id
```

```text
action_audit_event
  audit_event_id
  action_request_id
  event_type                   -- CREATED / EDITED / APPROVED / DENIED / SENT / VERIFIED
  actor
  actor_identity_type
  before_state
  after_state
  occurred_at
  trace_id
```

The UI reflects the Lakebase transaction immediately. It does **not** claim that Oracle changed until the external call is verified.

### External update

A background action service or controlled Job then:

1. Validates the latest record version, business rules, policy and approval state.
2. Writes the command to an outbox/delivery record.
3. Calls the approved Oracle Fusion or other operational API.
4. Records the request and response correlation IDs.
5. Retries only when the external contract and idempotency rules make retry safe.
6. Reads back Oracle state or awaits a confirmed integration outcome.
7. Marks the action `SUCCEEDED`, `FAILED`, or `VERIFICATION_PENDING`.
8. Publishes an action/outcome event into Delta.
9. Recomputes affected planning views and exceptions.

This avoids the dangerous pattern where a web request makes a non-idempotent external update, times out, retries, and creates duplicate orders or repeated alerts.

## Writeback patterns

Not every write has the same meaning. I will classify writebacks before designing the implementation.


| Writeback type | Example | Lakebase role | Delta role | Operational-system role |
| :-- | :-- | :-- | :-- | :-- |
| Personal workflow | Bookmark an exception | Primary source | Optional analytics history | None |
| Collaborative workflow | Assign a planner, add comment | Primary source | Auditable event/outcome copy | None |
| Planner input | Demand event or forecast override | Draft/lock/audit workflow | Published planning history | Export/API to Oracle SCC/Fusion |
| Recommendation disposition | Accept, deny, revise | Primary source | Model/decision learning history | Optional subsequent action |
| Transaction request | PO expedite, quantity change | Command, approval, idempotency | Command/outcome history | Execute after approval |
| External notification | Alert supplier owner | Command/status/audit | Notification analytics | Send email/Teams/webhook |
| Exception resolution | Mark resolved with reason | Primary source | Outcome metric | Optional source-system action |
| Master-data request | Request MOQ/lead-time correction | Ticket/workflow state | Quality trend analysis | Master-data workflow |
| Scenario | Save private/shared simulation | Scenario metadata and inputs | Scenario snapshots/results | None unless promoted |

## Delta synchronization

You said “Lakebase, then Delta tables, if possible.” That is the right direction—but the exact method depends on the data behavior.

### Lakebase to Delta

For action history, planner overrides, approvals, comments, and outcomes, sync or publish Lakebase changes into Delta so they can support:

- Actual-versus-plan analysis.
- Planner adoption metrics.
- Forecast Value Added analysis.
- Exception-resolution rates.
- Root-cause trends.
- Decision-cycle time.
- Model-training labels.
- Dashboard trends.
- Agent evidence.
- Audit analysis.

The Delta copy should generally be treated as an **analytical projection**, not the system that arbitrates concurrent updates.

### Delta to Lakebase

For fast App lookups and action forms, selected lakehouse data can be synchronized into Lakebase:

- Current exception queue.
- Current PO and planned-order context.
- SKU/supplier/org lookup records.
- Current demand-event context.
- Policy thresholds.
- Reference data required for low-latency UI validation.

Do not blindly sync every large historical fact table to Lakebase. Use Delta and SQL Warehouses for deep history, large aggregation, and broad analytical scans.

### Reverse ETL

The preferred pattern is not “reverse ETL everywhere.” It is **a controlled command/outbox/action pattern** for live enterprise updates:

```text
Lakebase approved action
  → action-outbox record
  → connector/action service
  → Oracle / WMS / TMS / SCC
  → confirmation or failure
  → Lakebase status
  → Delta event/outcome history
```

Reverse ETL is suitable for a managed, governed propagation flow. It must still include mapping, validation, external API contracts, retries, idempotency, ownership, reconciliation, and a failure queue.

## Action catalog

The App should make actions visible and contextual. An exception should not only say, “Late PO”; it should provide permitted response paths.


| Exception | Candidate actions |
| :-- | :-- |
| Demand exceeds supply | Increase PO, expedite, reallocate inventory, transfer inventory, adjust allocation, approve stockout communication |
| Excess inventory | Push out PO, cancel PO, rebalance inventory, reallocate demand, reduce forecast, create promotion review |
| PO pull-in recommended | Request supplier expedite, modify requested date, authorize premium freight review |
| PO push-out recommended | Request delay, reduce/cancel quantity, use inventory elsewhere |
| New PO needed | Create requisition/PO request, rebalance first, split across suppliers |
| PO cancellation | Deny, request review, cancel if approval and policy permit |
| Supplier late risk | Notify supplier owner, create escalation, reforecast receipt date, evaluate alternate source |
| Safety-stock breach | Transfer, expedite, raise order, adjust allocation, approve risk acceptance |
| Demand-event change | Change stores, load-per-store, ASPV, start/end months, affected customers, items, or event status |
| Demand forecast variance | Create override, attach evidence, request demand review, run scenario |
| Inventory imbalance | Initiate transfer proposal, consolidate rebalancing actions, assess transfer cost versus new order |
| Frozen-zone violation | Require escalation, document override, obtain named approval |
| Plan versus actual receipt variance | Create supplier follow-up, revise lead-time assumption, update root cause |
| Quality issue / short receipt | Expedite replacement, disposition inventory, adjust supply plan, open supplier-quality case |

The Red Keychain requirements specifically identify 18 supply exception types, including potential stockout, excess inventory, PO pull-in/push-out, new PO, cancel recommendation, supplier late risk, safety-stock violation, transition risk, network imbalance, MOQ waste, frozen-zone violation, and Plan-versus-Actual receipt variance.[^18_2]

## Action state machine

Each action must follow a formal state machine:

```text
DRAFT
  → SUBMITTED
  → VALIDATION_FAILED
  → PENDING_APPROVAL
  → APPROVED
  → SCHEDULED
  → EXECUTING
  → SUCCEEDED
  → VERIFIED
  → CLOSED

Alternate paths:
DRAFT → CANCELLED
SUBMITTED → DENIED
PENDING_APPROVAL → EXPIRED
EXECUTING → FAILED
SUCCEEDED → VERIFICATION_FAILED
```

State transition controls will include:

- Persona and role.
- Monetary/quantity threshold.
- A-item or critical-SKU status.
- Frozen-zone condition.
- Supplier and organization rules.
- Planner versus manager authority.
- Required comment/reason code.
- Required dual approval.
- Current record version.
- Current inventory/plan state.
- External-system availability.
- Idempotency status.

The requirements already call for stricter thresholds by ABC classification, tighter controls for A-items, escalation for large variances or missed safety stock, and policy around frozen-zone changes.[^18_2][^18_3]

## Alerts and notifications

A button click can send an alert, but it must be more than “send email.”

The App should let users choose actions such as:

- Notify supplier manager.
- Notify demand planner.
- Escalate to supply planning manager.
- Create a Teams/Slack/email notification.
- Create an Oracle task.
- Subscribe a user to an exception.
- Escalate if no acknowledgment occurs within a set period.
- Digest related exceptions into one alert instead of spamming people.
- Withdraw or update an alert when the issue resolves.

Each notification needs:

```text
notification_id
triggering_action_id
recipient / group
channel
template_version
business_context
severity
sent_at
delivery_status
acknowledged_by
acknowledged_at
escalation_level
```

A notification action should create an auditable record in Lakebase, be delivered asynchronously, and report its delivery outcome. It should not silently fail because an email/webhook timed out during a browser request.

## Search strategy

Your Lakebase-search idea is powerful, but it should serve a different role from Vector Search.

### Lakebase search

Use Lakebase/PostgreSQL search for fast, transactional, structured operational retrieval:

- PO number.
- PO line.
- Supplier.
- SKU/item number.
- Organization/DC.
- Planner.
- Exception ID.
- Demand event ID/name.
- Action ID/status.
- Comment text.
- Approval status.
- Exact and partial matching.
- User work queue.
- “My pending approvals.”
- “Actions I changed this week.”
- “All POs awaiting supplier confirmation.”

This makes Lakebase the operational navigation and workflow search layer.

### Vector Search

Use Vector Search for semantic or unstructured discovery:

- “Show procedures for handling supplier late-risk exceptions.”
- “Find previous cases where a quality rejection caused a shortage.”
- “What did planners decide in similar transition-overlap cases?”
- “Search the supply-planning policy and exception playbook.”
- “Find meeting notes or supplier correspondence about this constraint.”


### Governed Delta/SQL search

Use SQL and governed semantic data for analytical questions:

- “Which A-item suppliers had Plan-versus-Actual receipt variance over 30% in the last 12 weeks?”
- “Show all items with projected safety-stock violations after this approved quantity change.”
- “Compare current plan with the Monday snapshot for DC 2012.”
- “How much working capital would a 20-unit increase add by category?”

The Agent should route to the correct tool based on the request. It should not use vector search to answer an exact inventory quantity, and it should not query Lakebase as though it were the historical warehouse.

## Search-to-action flow

A productive App experience can be:

```text
Search: “TTi late POs causing A-item shortages in DC 2012”
  → structured search finds active late-PO cases and action records
  → Delta query identifies plan/actual, projected shortage, safety stock, and cost impact
  → Agent summarizes root cause and evidence
  → planner opens a result
  → App proposes transfer / expedite / quantity adjustment options
  → planner edits quantities and adds comment
  → policy engine determines approval requirement
  → approval request is persisted in Lakebase
  → approved action is sent to Oracle or notification channel
  → Delta is updated with outcome
  → impact trend and exception state refresh
```

The immediate UI update is a workflow status update. The “real-time business impact” update must be labeled accurately:

- **Proposed impact:** calculated from a scenario before approval/execution.
- **Approved impact:** expected result from an authorized action.
- **Executed impact:** external operation accepted by the target system.
- **Verified impact:** confirmed by source-system read-back or downstream actuals.
- **Realized impact:** observed later in receipts, inventory, service, cost, or demand results.

That distinction is essential. A projected reduction in shortage risk is not yet an actual business improvement.

## Real-time impact

The App can show near-real-time effects through two feedback loops.

### Operational loop

```text
Planner action
  → Lakebase transaction
  → App reflects draft/approved/executing state
  → external system receives action
  → confirmation returns
  → impacted exception re-evaluates
  → queue and trend refresh
```


### Analytical loop

```text
Lakebase action/outcome
  → Delta action-history projection
  → updated facts / forecast / plan snapshots
  → metric recomputation
  → dashboard and Agent use new evidence
  → MLflow captures recommendation/outcome
  → future recommendation quality improves
```

Near-real-time requires product-specific decisions:

- Is the source plan updated synchronously or on an Oracle batch cadence?
- Is the App showing the approved simulation, the published plan, or confirmed Oracle state?
- Can the exception engine recompute incrementally?
- Which metrics have a real-time requirement and which can refresh hourly/daily?
- What is acceptable stale-data behavior during Oracle or network outages?


## Unique capabilities by priority

The scope can be differentiated with Databricks-native strengths rather than copying Excel workflows into a browser.


| Priority | High-value App capability |
| :-- | :-- |
| P1 Actuals Supply Plan | Monday-morning variance triage; explain plan-vintage versus actual differences; create root-cause cases; notify supplier/planner; turn a variance into a tracked action |
| P2 Supply Exceptions / Red Keychain | Prioritized exception queue; bulk PO actions; order-versus-rebalance decision; PO grouping and sequencing; supplier-confirmed versus requested plan; scenario and probabilistic risk dials |
| P3 Demand Planning Events | Multi-user event editing with locks; customer-hierarchy input and disaggregation; Forecast Builder; audit trail; pre-publish validation; release workflow to Oracle SCC/Fusion |
| P4 Demand Exceptions | Forecast-change explanation; forecast override with reason and approval; compare statistical forecast, planner override and consensus plan; planner feedback as Forecast Value Added evidence |
| Cross-priority | Unified work queue, action center, approval inbox, saved search, notification subscriptions, shared comments, watchlists, action history, outcome trend, Agent-assisted investigation |

The requirement documents specifically call for restoration of spreadsheet-like editing, PO grouping at point of release, supplier forecast publication with weekly Friday 4 PM freeze plus ad hoc publishing, and feedback capture from planned-order releases and exception outcomes. The demand-event requirements call for a Streamlit prototype decision, but the production selection should be based on editing complexity, concurrency, auditability, integration, and supportability—not on the prototype alone.[^18_1][^18_2]

## Agent role

The Agent becomes useful when it helps the planner decide and act—but it must never become a hidden control plane.

The Agent can:

- Explain why an exception exists.
- Retrieve Plan-versus-Actual evidence.
- Identify similar historical cases.
- Compare new-order versus rebalance alternatives.
- Run approved scenarios.
- Draft an action rationale.
- Create a **draft** action request in Lakebase.
- Recommend approval routing.
- Summarize affected suppliers, SKUs, DCs and service risk.
- Generate an alert draft.
- Learn from explicit planner accept/deny/modify feedback.

The Agent must not:

- Directly mutate Oracle, Lakebase, Delta, or planning systems with unrestricted natural-language instructions.
- Execute a PO change without typed validation and approval.
- Treat an LLM explanation as numerical truth.
- Override frozen-zone or delegation controls.
- Reuse one user’s search or planning data for another user without authorization.
- Present a simulated impact as confirmed operational reality.


## Technical guardrails

The App will follow these design controls:

- Use **React + FastAPI** for a rich planner UI and trusted backend boundary.
- Use Lakebase for transactional state, locks, approvals, comments, drafts, actions and idempotency.
- Use Delta for analytical history, snapshots, trends, published events and outcomes.
- Use Unity Catalog for governed access, lineage, policy and data products.
- Use Lakeflow/Jobs for asynchronous ingestion, publication, recalculation, notifications and long-running workflows.
- Use Model Serving for approved forecasting or ranking models.
- Use Unity AI Gateway for governed model access, policy and usage tracking.
- Use MLflow for model/Agent tracing, evaluation, planner feedback and outcome measurement.
- Use supported integration APIs—not direct UI automation or uncontrolled database updates.
- Use service principals for background/external action work and on-behalf-of-user access where user-level governance is required.
- Use strict action idempotency, optimistic concurrency, validation and full audit history.
- Use a kill switch that disables external execution but preserves read-only investigation and draft workflows.


## Default action-first directive

I will add this to the project’s operating model:

> Design Databricks Apps as closed-loop supply-chain decision and action systems, not one-way dashboards. Use Delta and Unity Catalog for governed analytical evidence and historical outcomes; use Lakebase for transactional workflow state, search, drafts, locks, comments, approvals, action commands, idempotency, and audits. For every recommendation, distinguish detection, analysis, simulation, proposal, approval, execution, verification, and realized outcome. Let users accept, deny, edit, bulk-process, comment on, assign, escalate, and track actions from the UI. Propagate approved changes through controlled integration patterns to the appropriate enterprise system and project actions/outcomes back to Delta for analytics and learning. Use Agentic AI to investigate and recommend, not to bypass deterministic policy, user authorization, or human approval.

The next architectural step, before implementation, would be to define an **Action Catalog and Authority Matrix**: for each exception type, list allowed actions, data required, who may draft, who may approve, external target system, validation rules, idempotency behavior, and how success is verified.

<span style="display:none">[^18_4][^18_5]</span>

<div align="center">⁂</div>

[^18_1]: 01_Requirements.md

[^18_2]: Red_Keychain_Supply_Planning_Requirements.md

[^18_3]: Actuals_Supply_Plan_Requirements.md

[^18_4]: Workshop_Setup_and_Data_Loading_Instructions_2026-08-28_1426.json

[^18_5]: cursor_databricks_project_upload_cleanu.md


---

# and, know about databricks docs, spark latest docs, mlflow latest docs, sdp latest docs, dqx latest docs .. databricks labs latest docs! and databricks labs projects that can be used

Yes. This will become a first-class requirement: I will keep a **current, source-backed Databricks capability map** and verify the latest official documentation before selecting or implementing a feature.

The goal is not simply “know all tools.” It is to know each tool’s **current API, maturity, limits, prerequisites, integration points, anti-patterns, and when not to use it**.

## Knowledge sources

I will maintain awareness across these primary domains:


| Domain | What I will verify before implementation |
| :-- | :-- |
| Databricks platform docs | Workspace, Unity Catalog, Jobs, SQL Warehouses, serverless, Apps, Lakebase, networking, OAuth, service principals, audit/system tables |
| Apache Spark docs | Current Spark SQL, PySpark DataFrame APIs, Structured Streaming semantics, stateful processing, performance, query plans, joins, windows, UDFs, file sources |
| MLflow docs | Traditional ML, Tracking, Registry, aliases, evaluation, deployment, tracing, Prompt Registry, `ResponsesAgent`, scorers, LLM judges, human feedback |
| Lakeflow SDP docs | Dataset types, declarative CDC, expectations, flows, sinks, event logs, pipeline limitations, development/deployment patterns |
| DQX docs | Data-quality rules, ruleset design, quarantine, monitoring, profiling, testing, governance and suitability compared with native expectations |
| Databricks Labs | Official/community-maintained accelerators, reference architectures, utilities, maturity, maintenance status, security review and suitability |
| Release notes | Feature changes, deprecations, renamed products, preview/GA status, API migrations, platform-specific availability |
| Cloud-specific docs | AWS/Azure/GCP differences in networking, identity, private connectivity, Lakebase and Apps support |

The latest Apache Spark documentation currently identifies Spark 4.2.0 as the current documentation stream, including SQL, PySpark, and Structured Streaming references. Spark 4 split the former monolithic Structured Streaming guide into smaller topic-focused pages.[^19_1][^19_2][^19_3]

## SDP and Lakeflow

For Spark Declarative Pipelines, I will verify the current Lakeflow documentation rather than relying on old DLT examples or outdated `apply_changes` naming.

The modern judgment will include:

- Whether this is a maintained dataset or merely a task.
- Batch versus streaming behavior.
- CDC ordering, late events, schema changes, deletes and SCD requirements.
- Materialized view versus streaming table versus plain Delta table.
- Whether declarative CDC is better than a custom `MERGE`.
- Whether expectations should warn, drop, or fail.
- Whether a sink or downstream publication is appropriate.
- Event-log observability, recovery and cost.
- Dataset and API limitations.
- Whether the pipeline’s declarative rerun behavior conflicts with side effects.

Lakeflow declarative CDC handles ordering, deduplication, out-of-order events, and schema evolution declaratively. Pipeline expectations apply SQL Boolean rules per row and can warn, drop records, or fail an update; they also emit quality metrics to the pipeline event log.[^19_4][^19_5]

For the Milwaukee project, SDPs will remain a **candidate for durable incremental analytical datasets**, not an automatic answer for app workflows, Lakebase transactions, external actions, manual approvals, or one-time discovery work.

## DQX and data quality

DQX will be considered as one possible quality framework—not blindly imposed on every pipeline.

I will compare:


| Need | Possible fit |
| :-- | :-- |
| Simple row-level contract in an SDP | Native Lakeflow expectations |
| Reusable enterprise rules across multiple workloads | DQX or a governed reusable rule framework |
| Fast source profiling | SQL/PySpark profiling notebooks and data-quality monitoring |
| Complex reconciliation | SQL/PySpark tests with retained evidence |
| Quarantine and multi-rule reporting | DQX or purpose-built Silver-layer pattern |
| App validation | FastAPI/Pydantic plus Lakebase constraints and business-rule services |
| Transaction validation | PostgreSQL constraints, typed API schemas and state-machine enforcement |
| Agent/tool validation | Typed tool schemas, deterministic policy checks and MLflow evaluation |

This is important because a data-quality product can add governance and reuse, but it can also add abstraction, learning curve, runtime overhead, dependency/version risk, and debugging complexity. The correct choice will follow the actual breadth and repeatability of quality requirements.

## Databricks Labs

Databricks Labs projects can provide accelerators, integration helpers, reference implementations, tooling, and operational patterns. But a Lab project is not automatically a production platform dependency.

Before adopting one, I will evaluate:

- Is it Databricks-supported, Labs-maintained, community-maintained, or archived?
- Is it generally available, public preview, experimental, or a reference only?
- Is the project active and compatible with the current Databricks Runtime and MLflow versions?
- Does it use Unity Catalog, current authentication, and current APIs?
- Who will own upgrades and security fixes?
- Does it fit Milwaukee’s cloud, networking, security and deployment standards?
- Does it duplicate native Databricks capability?
- Can it be used as inspiration instead of imported as a dependency?
- Is its license compatible with enterprise requirements?
- Can it be pinned, tested, upgraded and rolled back?

The default rule will be:

> **Adopt a Databricks Labs project only when it materially accelerates delivery without creating unacceptable ownership, versioning, security, or operational risk. Otherwise, borrow the validated pattern and implement the smaller required capability using supported platform features.**

## Current MLflow

MLflow will be treated as two related but distinct systems:


| Traditional ML | GenAI and Agents |
| :-- | :-- |
| Experiment tracking | Prompt/Agent tracing |
| Feature and data lineage | Tool, retrieval and supervisor traces |
| Time-aware forecast evaluation | Agent evaluation datasets |
| Model Registry | Prompt Registry and Agent artifacts |
| Model versions and aliases | Prompt/Agent/tool versions |
| Batch or online inference | Agent endpoints and streaming |
| Drift and prediction monitoring | Trace quality, groundedness, safety, latency and cost |
| Business-outcome measurement | Human feedback, LLM judges and action outcomes |

Current MLflow documentation identifies version 3.15.2 for `ResponsesAgent`. `ResponsesAgent` is designed for structured tool-calling, multi-turn Agent responses and Model Serving.[^19_6]

MLflow tracing supports debugging, human feedback, evaluation and production monitoring of Agent and LLM application behavior.[^19_7]

## Documentation discipline

For every meaningful technical recommendation, I will distinguish:


| Status | Meaning |
| :-- | :-- |
| Confirmed current | Checked against current official documentation |
| Supported with constraint | Officially supported, but requirements/limits apply |
| Preview/Beta | Possible, but maturity and release risk are explicit |
| Labs/reference pattern | Useful accelerator, not assumed platform standard |
| Candidate pattern | Worth prototyping, but not yet validated |
| Rejected | Does not fit semantics, maturity, risk or operating model |

I will specifically watch for:

- Product renames and migration paths.
- Old API examples that no longer represent recommended practice.
- Cloud availability differences.
- Preview and Beta restrictions.
- Authentication changes.
- Permission prerequisites.
- Resource attachment requirements.
- Region and network limitations.
- Runtime-version compatibility.
- App deployment/build restrictions.
- Lakebase authentication and pooling constraints.
- Model Serving and AI Gateway permission models.
- SDK/CLI and Bundle schema changes.
- Databricks Labs maintenance status.
- Breaking changes in Spark and MLflow.


## Updated project directive

The development pattern now includes:

> Before selecting, designing, or implementing a Databricks, Spark, MLflow, Lakeflow SDP, DQX, or Databricks Labs capability, verify current official documentation, release notes, cloud-specific limitations, API maturity, permissions, networking, deployment prerequisites, compatibility, and known gotchas. Prefer supported, production-ready platform capabilities where they fit the business semantics. Evaluate Databricks Labs projects for maturity, ownership, security, licensing, maintenance, and upgrade risk before adoption. Do not use old tutorials, preview features, outdated APIs, or accelerators by default merely because they demonstrate a convenient solution.

This ensures the project uses modern capabilities where they help, while avoiding blind adoption of anything—native, Labs, open source, or custom.

<span style="display:none">[^19_10][^19_11][^19_12][^19_13][^19_14][^19_15][^19_8][^19_9]</span>

<div align="center">⁂</div>

[^19_1]: https://spark.apache.org/docs/latest/api/python/index.html

[^19_2]: https://spark.apache.org/docs/latest/sql-ref.html

[^19_3]: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html

[^19_4]: https://learn.microsoft.com/en-us/azure/databricks/ldp/best-practices/

[^19_5]: https://docs.databricks.com/aws/en/ldp/concepts/

[^19_6]: https://mlflow.org/docs/latest/genai/serving/responses-agent/

[^19_7]: https://mlflow.org/docs/latest/genai/tracing/

[^19_8]: https://spark.apache.org/docs/3.5.6/structured-streaming-programming-guide.html

[^19_9]: https://spark.apache.org/streaming/

[^19_10]: https://aws.amazon.com/blogs/machine-learning/advanced-tracing-and-evaluation-of-generative-ai-agents-using-langchain-and-amazon-sagemaker-ai-mlflow/

[^19_11]: https://www.snowflake.com/en/blog/engineering/trace-aware-agent-evaluation-mlflow/

[^19_12]: https://www.databricks.com/resources/demos/videos/lakeflow-declarative-pipelines-overview

[^19_13]: https://www.databricks.com/product/data-engineering/spark-declarative-pipelines

[^19_14]: https://community.databricks.com/t5/technical-blog/from-traces-to-evaluation-an-autonomous-mlflow-agent-harness-for/ba-p/143422

[^19_15]: https://www.linkedin.com/posts/sarath-chandrika-k_end-to-end-data-engineering-project-using-activity-7421591808083795969-Zk9O


---

# and one and only rule for this project, prod_edw and prod_operations are only for read.

sandbox_operations.po_management is the place to write and then the lakebase can be used for writes!

Understood. This is now the project’s **non-negotiable data-write boundary**:

> `prod_edw` and `prod_operations` are strictly read-only.\
> Application and development writes go only to `sandbox_operations.po_management` and to Lakebase for transactional application state.

## Access policy

| Data store | Allowed activity | Prohibited activity |
| :-- | :-- | :-- |
| `prod_edw` | Read, profile, query, reconcile, derive from, document | Insert, update, delete, merge, truncate, overwrite, alter, optimize with data-changing intent |
| `prod_operations` | Read, profile, query, reconcile, derive from, document | Insert, update, delete, merge, truncate, overwrite, alter, create managed output tables |
| `sandbox_operations.po_management` | Create and write project-owned Delta tables, views, test outputs, analytical projections, action/outcome history | Modify objects outside the agreed project scope |
| Lakebase | Transactional writes for App state, drafts, locks, comments, approvals, action requests, outbox records, statuses, search/workflow data | Treat it as an EDW or write directly to production source systems without governed action flow |

## Architectural implication

```text
prod_edw                         prod_operations
   Read-only                         Read-only
      │                                  │
      └───────────────┬──────────────────┘
                      ▼
         In-place exploration / profiling / reconciliation
                      │
                      ▼
     sandbox_operations.po_management
       Silver/Gold derivatives, snapshots,
       exception outputs, projections, QA evidence,
       action/outcome analytical history
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
       Lakebase                Databricks UI
  Drafts, locks, comments,    React/FastAPI App,
  approvals, workflow,        dashboard, Genie,
  search, action outbox       Agent workflows
          │
          ▼
  Controlled integration only
  to external operational systems
```


## Practical development rules

When you ask me to write code or create an asset, I will enforce these rules:

- Every source query against `prod_edw` and `prod_operations` will be read-only.
- Any derived Delta tables, temporary analytical outputs, exception tables, reconciliation results, snapshots, or project-specific views will be created under `sandbox_operations.po_management`.
- No `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, `CREATE OR REPLACE TABLE`, `ALTER TABLE`, `DROP`, or write-capable streaming sink will target either production schema.
- No writeback workflow will directly mutate `prod_edw` or `prod_operations`.
- Lakebase will hold mutable App workflow state: user edits, event locks, comments, approval decisions, action drafts, action status, audit events, saved searches, and idempotency records.
- Lakebase-to-Delta publication will write only into `sandbox_operations.po_management`.
- Any future Oracle Fusion, Oracle SCC, WMS, TMS, or other external-system writeback will use a separately approved, typed, auditable action path—not a direct write to these Databricks production schemas.
- A read-only source query will be explicitly labeled as such in implementation notes.
- Before any command that could create or modify a resource, I will confirm its fully qualified destination is permitted.


## Naming convention

Unless you specify a more detailed standard, project outputs will use a clear prefix in the writable schema, for example:

```text
sandbox_operations.po_management.actuals_weekly_summary
sandbox_operations.po_management.planned_weekly_summary
sandbox_operations.po_management.plan_vs_actual
sandbox_operations.po_management.supply_exceptions
sandbox_operations.po_management.demand_events_published
sandbox_operations.po_management.action_outcome_history
sandbox_operations.po_management.planner_feedback
sandbox_operations.po_management.qa_reconciliation_results
```

Lakebase would separately contain transactional entities such as:

```text
action_request
action_audit_event
approval
exception_case
event_draft
event_lock
planner_comment
saved_search
notification_delivery
integration_outbox
integration_result
```


## Guardrails

Every pipeline, Job, notebook, SQL query, FastAPI route, Agent tool, and App action will be reviewed against this policy.


| Component | Read source | Write destination |
| :-- | :-- | :-- |
| Profiling notebook | `prod_edw`, `prod_operations` | None or `sandbox_operations.po_management` QA outputs |
| Actuals / plan transformation | `prod_edw`, `prod_operations` | `sandbox_operations.po_management` |
| Exception engine | Sandbox-derived tables and approved read-only sources | `sandbox_operations.po_management` |
| Dashboard / Genie | Read-only sources and sandbox analytical outputs | None |
| Forecasting pipeline | Read-only sources and sandbox features | Sandbox models/features/predictions as authorized |
| React/FastAPI App | Sandbox analytical data and Lakebase | Lakebase and sandbox projections only |
| Agent | Governed read tools | Lakebase draft/proposal only; never direct production-schema mutation |
| Action service | Lakebase approved outbox | External system only after explicit approval; Delta history only in sandbox |

This boundary fits the broader design: production EDW and operations data remain protected as authoritative sources, while the project has a controlled analytical workspace and a proper transactional layer for planner and Agent actions.

---

# Now, this also gave me some good responses initially! But I am still impressed by the way this understands the asks!

Learning from this as well!

Yes—I have incorporated this conversation as an additional **domain-reasoning reference**, not merely as another requirements document. Its strongest contribution is how it connects business meaning, application behavior, risk, and architecture before selecting technologies.[^21_1]

## Knowledge absorbed

### Actual versus Plan

“Actual versus Plan” is not a single report. It can represent:

- Demand actual versus demand forecast.
- Supply actual versus supply plan.
- Purchase order versus receipt.
- Production schedule versus production output.
- Planned shipment versus actual shipment.
- Inventory target versus actual inventory.
- Financial plan versus actual cost or revenue.
- Integrated demand, supply, inventory, and financial reconciliation.[^21_1]

The governing questions must therefore be:

> Which actual? Which plan? Which version? At what grain, horizon, calendar, and business stage?

### EDW and Operations

The document provides a useful initial hypothesis:

- The operational database usually contains current execution transactions.
- The EDW usually contains integrated, historical, conformed, and reporting-oriented information.
- Historical plan snapshots are more likely to be retained in an EDW or planning-history layer because operational systems may overwrite the active plan.
- Detailed variance investigation may begin in the EDW and drill into operational transactions.[^21_1]

This is a **discovery hypothesis**, not a guaranteed Milwaukee architecture. We will verify source ownership, latency, keys, history retention, and authoritative status before designing anything.

## Different application modes

One of the most valuable insights is that the initiatives have fundamentally different interaction patterns.[^21_1]


| Capability | Primary behavior |
| :-- | :-- |
| Actuals Supply Plan | Read-oriented analytical and diagnostic |
| Demand Event Forecasting | Transactional, stateful, validation-heavy and write-oriented |
| Red Keychain | Exception-driven decision support with recommendations and controlled actions |

These should not be forced into one undifferentiated Agent.

The unified experience may eventually have several bounded modes:

- **Analyst:** What happened?
- **Investigator:** Why did it happen?
- **Planner:** What should be changed?
- **Workflow assistant:** Help create and validate an event.
- **Decision assistant:** Recommend an action.
- **Execution assistant:** Prepare, approve, execute, and verify an authorized action.

Each mode has different latency, state, data, authorization, evaluation, and failure requirements.

## Nervous-system model

The conversation offers an excellent business metaphor:

- **Actuals provides memory:** what was planned and what occurred.
- **Exceptions provide perception:** what needs attention.
- **Demand events provide new signals:** what may alter future demand.
- **Red Keychain provides decision support:** what actions might resolve supply problems.
- **Lakebase provides operational memory:** cases, assignments, approvals, feedback, and action state.
- **Authorized integrations provide the hands:** controlled changes to operational systems.

The attachment describes these projects as parts of a larger supply-chain “nervous system,” rather than unrelated technical deliverables.[^21_1]

That perspective will become part of the development pattern.

## Hybrid intelligence

Another important lesson is to keep deterministic decision logic separate from language-model explanation. The document proposes a hybrid approach in which rules or analytical models identify exceptions and candidate recommendations, while the LLM explains evidence, supports investigation, and helps planners interact with the system.[^21_1]

For example:

```text
Trusted data
    ↓
Deterministic exception rule
    ↓
Ranked exception
    ↓
Validated recommendation or scenario model
    ↓
Agent explanation
    ↓
Planner review
    ↓
Typed action proposal
    ↓
Approval
    ↓
Trusted execution service
    ↓
Verification
```

The LLM should not invent:

- Variance thresholds.
- MOQ rules.
- Lead-time policies.
- Plan versions.
- Supplier constraints.
- Approval requirements.
- Purchase-order changes.

These must come from governed data, versioned business rules, validated models, and authorized tools.

## Progressive maturity

The conversation also reinforces a sound sequence:

1. Validate Actuals and plan reconciliation.
2. Establish governed grains, metrics, and evidence.
3. Codify deterministic exception rules.
4. Build trustworthy exception queues.
5. Add explanations and conversational investigation.
6. Add validated scenario models.
7. Collect planner acceptance, modification, and rejection feedback.
8. Introduce recommendations.
9. Add human-approved operational actions.
10. Consider greater autonomy only after evidence supports it.[^21_1]

This prevents the project from becoming a sophisticated Agent operating on unvalidated semantics.

## Improvements needed

I will not adopt every technical recommendation literally. Some concepts in the conversation should be modernized or refined:


| Earlier suggestion | Updated interpretation |
| :-- | :-- |
| Streamlit as the main custom interface | Evaluate React + FastAPI Databricks App for the richer transactional and Agentic experience |
| Delta table for conversational workflow state | Prefer Lakebase when transactional consistency, concurrent editing, locks, or workflow state matter |
| Broad text-to-SQL | Prefer governed Genie, metric views, preapproved queries, or typed analytical tools |
| Rules stored as arbitrary SQL text | Use versioned rule definitions with validation, ownership, effective dates, test cases, and restricted execution |
| LLM writes to staging | LLM only proposes; a deterministic service validates and writes |
| Agent memory as raw conversation history | Maintain bounded, authorized, purpose-specific state |
| “RLHF-lite” from planner feedback | Treat feedback initially as analytics and supervised improvement—not automatically as reinforcement learning |
| AI Gateway as write protection | Use Gateway for AI governance; use authorization, policy code, transactions, approvals, and idempotency for write protection |
| One unified Agent | Begin with bounded capabilities and unite the experience only when the individual modes are proven |

The document itself recognizes the central danger: an Agent that recommends purchase-order actions before reconciled data and codified rules exist would be unsafe.[^21_1]

## New reasoning baseline

For future Milwaukee work, the reasoning sequence will be:

1. Identify the planner’s business decision.
2. Determine whether the request concerns demand, supply, inventory, execution, or finance.
3. Identify actual, plan, version, grain, horizon, and system of record.
4. Classify the workload as analytical, transactional, predictive, agentic, or operational-action oriented.
5. Establish deterministic business truth.
6. Determine the correct user persona and interaction mode.
7. Evaluate product choices and limitations.
8. Prototype the smallest vertical slice in the workspace.
9. Validate it with business evidence.
10. Add AI only where it improves investigation, prediction, recommendation, or interaction.
11. Add writeback only through typed, auditable, authorized transactions.
12. Add live actions only with approval, idempotency, verification, and recovery.

This attachment has materially improved the domain model—particularly the separation between **observing, detecting, explaining, planning, recommending, approving, and executing**. That distinction will now influence data modeling, application boundaries, Agent design, evaluation, security, and product selection.

<div align="center">⁂</div>

[^21_1]: Actual-vs-Plan-in-Supply-Chain-Chat.docx

