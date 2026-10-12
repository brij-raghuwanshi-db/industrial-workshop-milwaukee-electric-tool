# Workspace-First Databricks Development and Bundle Promotion

## Recommendation

Use a **workspace-first, promotion-ready development model** rather than forcing every idea into a Declarative Automation Bundle on day one. The normal path should be:

1. Discover and prototype in an authorized Databricks workspace development folder.
2. Validate the source data, transformations, metrics, dashboard behavior, Genie semantics, application workflow, and user requirements in place.
3. Refactor successful work into modular, testable assets.
4. Promote only reusable or production-intended assets into Git, a bundle, CI/CD, and controlled environments.

Databricks explicitly supports notebooks, SQL queries, dashboards, YAML, Python modules, small test files, and other code as workspace files. It recommends workspace files for notebooks, queries, and source code, while recommending Unity Catalog volumes for data, libraries, and build artifacts.[^1][^2]

## Why this fits

Supply-chain development is often investigative. Source-system semantics, fact grain, late-arriving transactions, units of measure, operational statuses, and KPI definitions are rarely understood well enough to design the final deployment package before exploration.

A workspace-first model supports rapid interaction with Spark, SQL warehouses, Unity Catalog, EDW sources, Lakehouse Federation, dashboards, and business users. However, it must preserve a deliberate path to source control and production; otherwise, the workspace becomes a collection of undocumented, user-owned notebooks.

The principle is:

> **Develop in place when learning and iteration dominate; productize through Git, bundles, and CI/CD when repeatability, collaboration, scheduling, governance, or production support dominates.**

## Two workspace options

| Option | Appropriate use | Main limitation |
|---|---|---|
| Standard workspace folder | Fast discovery, temporary notebooks, collaborative troubleshooting, profiling, demonstrations | No remote-Git lifecycle by default; easier to accumulate untracked changes |
| Databricks Git folder | In-workspace coding with branches, commits, pull requests, and later bundle authoring | Each developer should use a separate clone; some workspace asset types have Git limitations |

Git folders are workspace folders whose files and notebooks are synchronized with a remote Git repository. They allow development to remain inside the Databricks UI while adding branch and version-control workflows.[^3][^4]

For effective collaboration, Databricks recommends that each developer use a separate Git folder and development branch. Multiple users performing Git operations in one shared Git folder can switch branches for one another and create branch-management problems.[^5]

Therefore, if the supplied location is a standard shared workspace folder, it can be used as a **sandbox/integration area**. If it is possible to provision a Git folder, that is preferable for sustained implementation. A single shared Git checkout should not be used for concurrent Git operations.

## Development phases

### Phase A: workspace setup

Create a clear project layout in the authorized folder:

```text
/Workspace/.../milwaukee-supply-chain/
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
│   ├── sql
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

This layout is a suggested working convention, not a Databricks requirement. The folder should inherit group-based ACLs so authorized users receive consistent read, run, edit, or manage permissions; Databricks workspace objects inherit permissions from their containing folder.[^6][^7]

### Phase B: in-place discovery

Use notebooks and SQL files to:

- Inventory catalogs, schemas, sources, tables, views, keys, data owners, lineage, and freshness.
- Profile completeness, uniqueness, relationships, distributions, drift, and business rules.
- Reverse-engineer EDW facts and dimensions.
- Analyze transactional schemas and CDC behavior.
- Reconcile source systems, the EDW, and proposed lakehouse outputs.
- Prototype supply-chain KPIs and metric definitions.
- Explore dashboard layouts and Genie questions.
- Validate whether a proposed App, Lakebase workflow, ML model, or agent solves a real operational problem.

Notebooks should contain enough narrative to preserve assumptions and findings, but reusable logic should move early into nearby `.py` modules. Databricks supports standard imports from Python modules stored beside notebooks in workspace files, enabling a tighter edit-run-debug loop without immediately building a wheel.[^8][^9]

### Phase C: in-place functional development

Build a minimal vertical slice inside the development workspace:

- One bounded source or data domain.
- One ingestion or federated-access path.
- One bronze/silver/gold flow where needed.
- One governed metric or semantic view.
- One dashboard page or Genie subject area.
- One set of profiling and QA checks.
- One operational scenario with representative users.

Jobs and pipelines may initially reference development workspace assets for rapid iteration. Databricks recommends workspace paths in Git folders only for rapid development and testing; staging and production jobs should instead use controlled remote-Git sources or an equivalent deployment workflow.[^10][^11]

### Phase D: promotion assessment

Not every asset needs a bundle. Promote an asset when one or more of these conditions apply:

- It is scheduled or event-driven.
- Other data products depend on it.
- It writes governed tables or application state.
- It supports a dashboard, Genie Agent, App, model, or operational decision.
- It needs dev/staging/prod configuration.
- Multiple engineers maintain it.
- It has an SLA, support owner, alert, or recovery procedure.
- It requires repeatable permissions or service-principal execution.
- A change could affect production cost, security, data quality, or business decisions.

Keep an asset workspace-only when it is clearly disposable, exploratory, personal, short-lived, non-scheduled, and harmless if deleted. Even then, record its purpose and avoid placing durable business dependencies on it.

### Phase E: hardening

Before bundle promotion:

1. Remove notebook state, display-only commands, hard-coded IDs, personal paths, and embedded credentials.
2. Move reusable transforms into importable modules.
3. Parameterize catalogs, schemas, warehouses, compute, checkpoints, endpoints, and schedules.
4. Add unit, data-contract, integration, reconciliation, security, and user-acceptance tests.
5. Define jobs, pipelines, dashboards, Apps, models, permissions, and artifacts as source-controlled resources where supported.
6. Build an immutable wheel or other versioned artifact where appropriate.
7. Define development, staging, and production targets.
8. Add CI validation and controlled deployment.
9. Assign separate deployment and runtime service principals.
10. Add monitoring, runbook, backfill, recovery, and rollback/roll-forward behavior.

Declarative Automation Bundles can also be authored directly inside a workspace Git folder. Databricks supports editing bundle YAML, notebooks, source files, jobs, pipelines, and dashboards in the workspace, then committing changes and deploying through the UI or an external CI/CD workflow.[^12][^13]

## Working asset policy

| Asset | Initial workspace development | Production disposition |
|---|---|---|
| Exploratory notebook | Standard or Git folder | Archive, delete, or retain as documentation; do not schedule casually |
| Reusable Python/PySpark | Workspace `.py` module | Tested package/wheel or bundle-synchronized source |
| SQL exploration | Notebook or SQL query | Governed view, metric view, materialized view, pipeline SQL, or versioned query |
| Lakeflow pipeline | UI/in-place prototype | Bundle-defined pipeline with environment targets |
| Lakeflow Job | Development workspace job | Bundle-defined job using controlled source and runtime identity |
| Dashboard | In-place draft with business users | Source-controlled/bundle-managed dashboard after KPI certification |
| Genie Agent | Curated in-place iteration and benchmark development | Governed production Agent with permissions and regression suite |
| Databricks App | Workspace development App | Bundle-managed App plus controlled backend resources |
| Lakebase schema | Development database and migration experiments | Versioned database migrations; do not treat bundle YAML as the migration engine |
| ML/agent code | Notebook-based experiments and evaluation | MLflow-governed model/agent, versioned code, serving resources, and CI/CD |
| Test data and outputs | Small workspace fixtures or governed dev schemas | UC volumes/tables with lifecycle and permissions |

## Data and artifact placement

Do not use the workspace folder as general data storage. Workspace files are appropriate for code, notebooks, configuration, documentation, and small test fixtures; Unity Catalog volumes are preferred for data files, libraries, and build artifacts.[^14][^1]

Production tables should reside in governed Unity Catalog catalogs and schemas. Development should use isolated schemas or catalogs so experiments do not overwrite shared or production data. Delta history and time travel can help audit and restore table changes, but they do not replace environment isolation, testing, or deployment control.[^15]

## Workspace access requirements

To perform in-place development safely, access should include only what is needed:

- `CAN EDIT` or `CAN MANAGE` on the assigned development folder, depending on whether asset creation and permissions management are required.
- `CAN USE` on the relevant SQL warehouse or compute policy.
- Unity Catalog access to approved source objects.
- Write access only to designated development catalogs, schemas, volumes, or Lakebase databases.
- Permission to create approved development jobs, pipelines, dashboards, Genie Agents, or Apps if those are in scope.
- No default write access to production source systems or production catalogs.
- Secrets or OAuth access through approved Databricks mechanisms, never pasted into notebooks.

Databricks supports management of notebooks through the UI, CLI, and Workspace API, and workspace-object permissions can also be managed programmatically.[^16][^17][^18]

Actual remote development requires a connected execution environment with the workspace host, authenticated identity, folder path, and necessary Databricks permissions. Merely sharing a folder name in a chat does not establish access; an authorized Databricks integration, CLI/SDK authentication context, or equivalent controlled tool connection must be available.

## Collaboration guardrails

- Treat the assigned folder as development, not production.
- Use one owner group rather than an individual as the enduring steward.
- Give contributors the least folder permission they need.
- Use separate developer Git clones if Git integration is enabled.[^5]
- Avoid multiple users editing the same critical notebook simultaneously without coordination, even though real-time notebook collaboration is supported.[^6]
- Add a README, source inventory, naming rules, assumptions, and ownership matrix from the beginning.
- Tag or label experimental assets clearly.
- Establish cleanup dates for temporary tables, checkpoints, jobs, and dashboards.
- Do not make a prototype job the permanent scheduler merely because it works.
- Do not promote notebook outputs; promote source, resource definitions, tests, and reproducible transformations.

## Hybrid workflow

The recommended operating model is:

```text
Authorized workspace folder
        ↓
Discovery and profiling notebooks
        ↓
In-place SQL/PySpark/pipeline/dashboard/Genie/App prototype
        ↓
Business validation and QA
        ↓
Promotion decision
        ↓
Refactor into modules + tests + Git
        ↓
Declarative Automation Bundle
        ↓
CI validation → staging → production
```

This avoids two bad extremes:

- **Premature productization:** extensive bundle scaffolding before the source data and requirement are understood.
- **Permanent prototyping:** valuable workloads left as manually maintained, user-owned workspace artifacts.

## Updated development directive

> Start Databricks work in the authorized Milwaukee supply-chain development workspace when rapid discovery, profiling, interactive debugging, business validation, or user-experience iteration is required. Create organized notebooks, SQL queries, modules, dashboards, Genie assets, Apps, and other approved development resources in place. Prefer a personal Databricks Git folder for sustained source development; use a shared standard workspace folder as a controlled sandbox or integration area, not as an unmanaged production source. Keep reusable logic modular and promotion-ready, store production data in Unity Catalog rather than workspace files, isolate development writes, document assumptions and tests, and avoid hard-coded identities, paths, credentials, and environments. Do not force every experiment into a bundle. Once an asset becomes reusable, scheduled, shared, governed, SLA-backed, or production-impacting, refactor it into source control, tests, Declarative Automation Bundles, CI/CD, least-privilege service-principal execution, observability, and controlled staging/production promotion. Preserve the fastest safe feedback loop while maintaining a clear route from exploration to an operable product.

## Decision

Add this capability as **Workspace-First, Promotion-Ready Databricks Development**. It should coexist with—not replace—the bundle and CI/CD capability. Workspace development is the default for learning and rapid iteration; bundles and CI/CD are the default for repeatable production delivery.

---

## References

1. [Recommendations for files in volumes and workspace files](https://docs.databricks.com/aws/en/files/files-recommendations) - Store notebooks, SQL queries, and code files as workspace files. You can configure workspace file di...

2. [What are workspace files? | Databricks on Google Cloud](https://docs.databricks.com/gcp/en/files/workspace) - Workspace files are the files stored and managed in the Databricks workspace file system. You can cr...

3. [Introduction to workspace objects | Databricks on AWS](https://docs.databricks.com/aws/en/workspace/workspace-assets) - For information about how to use files to modularize your code as you develop with Databricks notebo...

4. [CI/CD with Databricks Git folders](https://docs.databricks.com/aws/en/repos/ci-cd) - Review the remote Git repositories you will use. Choose the right repos and branches. Edit Databrick...

5. [Create and manage Git folders | Databricks on AWS](https://docs.databricks.com/aws/en/repos/git-operations-with-repos) - Learn how to create and manage Databricks Git folders, including cloning repositories, branching, co...

6. [Collaborate using Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/notebooks-collaborate) - You can manage notebook permissions by adding notebook to folders. Notebooks in a folder inherit all...

7. [Access control lists | Databricks on AWS](https://docs.databricks.com/aws/en/security/auth/access-control/) - You can manage workspace object permissions by adding objects to folders. Objects in a folder inheri...

8. [Work with Python and R modules | Databricks on AWS](https://docs.databricks.com/aws/en/files/workspace-modules) - This article describes how you can use relative paths to import custom Python and R modules stored i...

9. [Share code between Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/share-code) - You can modularize your code by creating Python files in the Databricks workspace and importing them...

10. [Use Git with Lakeflow Jobs | Databricks on AWS](https://docs.databricks.com/aws/en/jobs/git) - Databricks recommends referencing workspace paths in Git folders only for rapid iteration and testin...

11. [Notebook task for jobs | Databricks on Google Cloud](https://docs.databricks.com/gcp/en/jobs/tasks/notebook) - Databricks recommends using the Git provider option and a remote Git repository for versioning asset...

12. [Collaborate on bundles in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace) - Bundles in the workspace provides a mechanism for workspace users to edit, commit, test, and deploy ...

13. [Author bundles in the workspace | Databricks on AWS](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author) - you can create and edit these configurations directly in the UI. Click the deployment icon for the b...

14. [Work with files in Unity Catalog volumes | Databricks on AWS](https://docs.databricks.com/aws/en/volumes/volume-files) - To interact with files in a volume, do the following: In your Databricks workspace, click Data icon....

15. [Work with table history | Databricks on AWS](https://docs.databricks.com/aws/en/tables/history) - Use the RESTORE command to restore a table to a previous version or timestamp, including for these s...

16. [permissions command group | Databricks on AWS](https://docs.databricks.com/aws/en/dev-tools/cli/reference/permissions-commands) - Workspace object permissions Manage which users can read, run, edit, or manage alerts, dbsql-dashboa...

17. [Manage Databricks notebooks | Databricks on AWS](https://docs.databricks.com/aws/en/notebooks/notebooks-manage) - If your Databricks account has the Premium plan or above, you can use Workspace access control to co...

18. [Manage workspace objects | Databricks on AWS](https://docs.databricks.com/aws/en/workspace/workspace-objects) - 2026 Manage workspace objects. Set permissions on the following workspace objects: For notebooks, wi...

