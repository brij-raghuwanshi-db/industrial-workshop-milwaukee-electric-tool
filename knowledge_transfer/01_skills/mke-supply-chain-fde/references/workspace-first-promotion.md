# Workspace-First, Promotion-Ready Development

Governing principle:

> **Use the fastest safe development loop, while preserving a clear path to a reproducible and
> operable production product.**

Develop in place when learning and iteration dominate; productize through Git, DABs, and CI/CD
when repeatability, collaboration, scheduling, governance, or production support dominates. This
avoids two failure modes: **premature productization** (bundle scaffolding before the data and
requirement are understood) and **permanent prototyping** (valuable workloads stuck as
hand-maintained, user-owned notebooks).

## Three development stages

| Stage | Goal | Typical assets |
|---|---|---|
| Workspace exploration | Learn and validate quickly | Notebooks, SQL, profiles, samples, diagrams |
| Workspace product development | Build a working vertical slice | Modules, pipelines, jobs, dashboards, Genie, Apps |
| Production promotion | Make it repeatable & supportable | Git, tests, DABs, CI/CD, service principals, monitoring |

Do not introduce bundle scaffolding unless it provides immediate value or the work has reached
the point where repeatability matters.

## Standard folder vs Git folder

| Option | Best use |
|---|---|
| Standard workspace folder | Discovery, temporary experiments, collaborative troubleshooting, early prototypes — a controlled sandbox / integration area |
| Databricks Git folder | Sustained development with branches, commits, PRs, and eventual bundle promotion |

Each developer should use a **separate Git folder and branch**; multiple users doing Git ops in
one shared Git folder cause branch-management problems. A single shared Git checkout is not a
multiuser development branch.

## Suggested project layout (convention, not a requirement)

```
milwaukee-supply-chain/
├── 00_admin/         README, assumptions, decision_log
├── 10_discovery/     source_inventory, edw_exploration, operational_db_analysis
├── 20_profiling/     source_profiles, key_analysis, reconciliation
├── 30_modeling/      dimensional_models, transactional_models, semantic_metrics
├── 40_pipelines/     ingestion, bronze, silver, gold
├── 50_consumption/   sql, dashboards, genie, apps
├── 60_qa/            test_data, test_queries, reconciliation
├── src/  tests/  docs/
```

The folder should inherit group-based ACLs (workspace objects inherit permissions from their
containing folder). Add a README, source inventory, naming rules, assumptions, and ownership
matrix from the start; tag experimental assets; set cleanup dates for temp tables, checkpoints,
jobs, dashboards.

## Notebook discipline

Notebooks primarily provide: exploration & visualization, business narrative, interactive
debugging, parameter entry, demos, pipeline/job entry points, QA evidence. Reusable transforms,
profiling functions, and business rules move into nearby `.py` modules (imported directly from
workspace files) as they stabilize — a fast edit-run-debug loop without premature wheel
packaging. Don't promote notebook *outputs*; promote source, resource definitions, tests, and
reproducible transformations.

## Promotion triggers

Promote an asset when it becomes any of: scheduled or event-driven; shared by other teams/data
products; an upstream dependency; responsible for writing governed tables; feeding an executive/
operational dashboard, a production Genie Agent, or a Databricks App; connected to a production
Lakebase database; SLA-backed; dependent on environment-specific config; maintained by multiple
engineers; required to run under a service principal; needing repeatable recovery; or capable of
affecting security, cost, or business decisions.

Keep an asset workspace-only when it is clearly disposable, exploratory, personal, short-lived,
non-scheduled, and harmless if deleted — but still record its purpose.

## Promotion process

1. Remove notebook state, display-only commands, hard-coded IDs, personal paths, embedded creds.
2. Extract reusable code into importable modules.
3. Parameterize catalogs, schemas, warehouses, compute, checkpoints, endpoints, schedules.
4. Add unit, data-contract, integration, reconciliation, security, and UAT tests.
5. Connect to Git; define jobs/pipelines/dashboards/Apps/permissions as source-controlled DAB
   resources where supported.
6. Build an immutable versioned artifact (wheel) where appropriate.
7. Define dev / staging / prod targets.
8. Add CI validation and controlled deployment.
9. Assign separate deployment and runtime service principals.
10. Add monitoring, runbook, backfill, recovery, rollback/roll-forward.

Bundles can be authored directly inside a workspace Git folder (edit YAML/source/notebooks/
jobs/pipelines/dashboards, commit, deploy via UI or external CI/CD).

## Dev / staging / prod source policy

- **Development:** workspace source (Git folder path) is acceptable for rapid iteration.
- **Staging:** reproducible, versioned source required.
- **Production:** DAB / remote-Git / CI-CD-controlled source and runtime identity required.

## Data & artifact placement (workspace ≠ data lake)

| Content | Preferred location |
|---|---|
| Notebooks, SQL, Python modules, YAML, docs | Workspace or Git folder |
| Small test fixtures | Workspace files or a test volume |
| Source extracts | Unity Catalog volume or governed table |
| Pipeline data | Unity Catalog Delta tables |
| Build artifacts / libraries | Unity Catalog volume or artifact repository |
| Checkpoints | Controlled cloud/UC location |
| Production application data | Lakebase or governed Delta tables, per workload |

(Project-specific write boundary — `sandbox_operations.po_management` + Lakebase only — is in
`../SKILL.md` guardrails. Production tables live in governed UC; isolate development writes.)

## Access needed for in-place work

An authorized Databricks connection (CLI/SDK/API auth context) — not just a folder path. The
working identity typically needs: `CAN EDIT`/`CAN MANAGE` on the dev folder; `CAN USE` on the
SQL warehouse/compute; read on authorized UC source objects; write only to the designated
development catalog/schema/volume/Lakebase; permission to create approved dev jobs/pipelines/
dashboards/Genie/Apps if in scope; **no default write** to production sources or catalogs;
secrets/OAuth via approved Databricks mechanisms, never pasted into notebooks.
