# Demand Events App — Build Notes

**What:** P3 Demand Events App, built on **Databricks AppKit** (React/TS + typed Node backend).
**Where:** `demand_events_app/mke-demand-events/` (app code); design docs in `demand_events_app/`.
**Status:** Scaffolded, coded, and **`databricks apps validate` passes** (types, ast-grep lint, typecheck, build, tests). **Not yet deployed** — deploy is the next gate (see below). Evidence ladder: *Implemented + build-validated*, not yet UAT.

## Platform wiring (probed live on `--profile mke-rsc`)

| Resource | Value |
|---|---|
| Lakebase project | `projects/mke-demand-events` (created this session; **separate** from supply's `mke-po-actions`) |
| Branch / DB | `.../branches/production` · `databricks_postgres` |
| Endpoint host | `ep-withered-cell-e8ts9gso.database.centralus.azuredatabricks.net` |
| SQL Warehouse (reads) | `7bd33a82f4e92206` (consumers-small, RUNNING) |
| App name | `mke-demand-events` |

`app.yaml` binds `sql-warehouse` (analytics reads) + `postgres` (Lakebase writes). Both plugins wired via `databricks apps init --features analytics,lakebase`.

## Guardrails honored
- **Reads** `prod_edw` only (analytics plugin, `config/queries/*.sql`, labelled READ-ONLY). Never writes it.
- **Writes** land only in **Lakebase** (`demand_events` schema) — transactional state.
- **Publish** records an acknowledgement in Lakebase; the Delta MERGE into `sandbox_operations.po_management.demand_events_published` is a **separate Job** (not an app-owned prod write).
- No LLM in the value math — disaggregation / lift / status are deterministic SQL.

## What's built (vertical slice + requested features)

**Backend** (`server/routes/demand-events/`)
- `schema.ts` — idempotent DDL for the full `demand_events` schema (event, header/tranche, customers, items, cells, lock, audit, bulk batch/stage, publication_ack). Created on startup (SP owns it after deploy).
- `routes.ts` — Express routes:
  - `GET/POST /api/events`, `GET /api/events/:id` — event list/detail/create (EXP ID = max+1).
  - `POST /api/events/:id/lock`, `DELETE …/lock` — event locking (30-min timeout, server-enforced).
  - `POST …/customers`, `…/items`, `…/cells` — multi-customer, bulk item paste, direct signed cell edits.
  - `POST …/disaggregate` — **ratio disaggregation** vs a base measure (even-split fallback).
  - **`POST /api/bulk-edit`** — the requested capability: stage → **one set-based apply** (SET_STATUS / CLOSE / ADJUST_VALUE / APPLY_LIFT), idempotent by `batch_id`, dedup by business key, transactional (`BEGIN/COMMIT`), audited.
  - `GET …/audit`, `POST /api/publish`, `GET /api/publish/history` — audit trail + publish acknowledgement.

**Reads** (`config/queries/`, types generated & warehouse-validated)
- `customer_hierarchy.sql` — dg5 6-level hierarchy.
- `validate_items.sql` — dash-normalized item validation (WARN, non-blocking, rule-versioned).
- `disaggregation_base.sql` — `planner_baseline` shares per mkedg5 for an item (hero `369722`).

**Frontend** (`client/src/pages/events/`)
- `EventsPage.tsx` — create/list/detail, status lifecycle (4 states), publish with **acknowledgement banner**, item/cell tables (negatives flagged red).
- `BulkEditPage.tsx` — pick category (events) → operation → one staged apply, with idempotent-replay + matched/changed result.

## Next gate — DEPLOY (deploy-first, per Lakebase skill)
The app SP must create & own the `demand_events` schema, so **deploy before running locally**:
```bash
cd demand_events_app/mke-demand-events
databricks apps deploy mke-demand-events --profile mke-rsc
databricks apps get mke-demand-events --profile mke-rsc -o json   # app_status.state RUNNING, note url
```
Then a real smoke test: create an event → add customers/items → disaggregate hero `3697-22` against `planner_baseline` → bulk-close a customer → publish → confirm acknowledgement + audit rows in Lakebase.

## Known follow-ups (from design §16)
- Item validation criterion (`PurchPlan` flags valid events) — reconfirm with analytics eng; flag is non-blocking + rule-versioned so it's swappable.
- Publication Delta MERGE Job into `sandbox_operations.po_management` (separate asset).
- Seed/normalize existing `expansion_*` events (Excel-serial dates, tranche aggregation) into Lakebase.

---

## Deploy attempt 1 — BLOCKED on prod_edw read grant (2026-09-01)

**Outcome:** app resource created (URL `https://mke-demand-events-4482605715640778.18.azure.databricksapps.com`,
compute ACTIVE), but **deployment FAILED → app_status UNAVAILABLE**.

**Root cause (from `databricks apps logs`):**
```
[INSUFFICIENT_PERMISSIONS] User does not have USE CATALOG on Catalog 'prod_edw'. SQLSTATE: 42501
```
The workspace build runs `appkit generate-types --wait` (typegen) against warehouse 7bd33a82f4e92206
**as the app service principal**, which lacks read on `prod_edw`. Local `databricks apps validate` passed
because it ran as the developer identity (which has read). typegen failure fails the whole build.

**Why I couldn't fix it:** I lack `MANAGE` on `prod_edw` (owner `ca23c982-…`, a customer prod catalog) and
can't self-add to the reader group `udp-dbx-uc-prod-edw-reader`. Read-only grant is within guardrail; it's
purely an authorization boundary I can't cross.

**ACTION NEEDED (customer / catalog admin), then resume:**
Grant the app SP read on `prod_edw` — either:
- add SP `2c32a222-5c61-41c7-8a51-9e3578962074` to group `udp-dbx-uc-prod-edw-reader`, or
- `GRANT USE CATALOG ON CATALOG prod_edw TO \`2c32a222-...\`;` plus `USE SCHEMA` + `SELECT` on
  `prod_edw.dimension` and `prod_edw.fact` (at least `dg5_customer_scd1`, `items_scd1`, `10_demand_daily`).

**Resume steps once granted:**
```bash
cd demand_events_app/mke-demand-events
databricks apps deploy --profile mke-rsc          # from project dir (create+deploy+run)
databricks apps get mke-demand-events --profile mke-rsc -o json   # expect app_status.state RUNNING
```
Then smoke-test hero 3697-22 (create → disaggregate vs planner_baseline → bulk-close a customer → publish →
verify ack + audit in Lakebase). Lakebase project `projects/mke-demand-events` already exists; the SP will
create/own schema `demand_events` on first successful start (deploy-first ownership).

**User decision (2026-09-01):** "Stop for now. I will get the access first."

---

## Deploy attempt 2 — DEPLOYED & SMOKE-TESTED (2026-09-01)

Customer granted the app SP read on `prod_edw` (via reader group). Redeployed → **App started successfully / RUNNING**.
URL: https://mke-demand-events-4482605715640778.18.azure.databricksapps.com
Startup log confirms `[demand-events] schema 'demand_events' ready` (SP owns the schema, deploy-first honored).

**Live smoke test (hero 3697-22, real prod_edw planner_baseline):**
- Create event (EXP ID 1000/1001, created_by resolved from x-forwarded-email) ✓
- Multi-customer add (HOME DEPOT + CONST_IND + FERGUSON) ✓
- Item add (3697-22 → item_id 369722, ShipSO, WARN non-blocking) ✓
- Ratio disaggregation of 10,000 units by planner_baseline shares → HOME DEPOT 9888 / CONST_IND 70 / FERGUSON 42 (sum 10,000, fallback_even_split=false) ✓
- Bulk SET_STATUS ACTIVE (changed:1) + idempotent replay (idempotent:true) ✓
- Bulk APPLY_LIFT 20% → 9930→11916, 70→84 (×1.2 exact) — reproduces the call's "20% lift on 3697" ✓
- Bulk CLOSE customer (CONST_IND → CLOSED, changed:1) — the "remove plumbing customer" case ✓
- Publish → acknowledgement (run_id, 1 active event, 3 rows, SUCCEEDED) ✓
- Audit trail: CREATED/EDITED/DISAGGREGATED rows with actor + timestamp ✓

**Two bugs found & fixed by the smoke test** (would not have surfaced in local validate):
1. `changed` count used `r.rows.length` (0 for UPDATE) → switched to `r.rowCount`.
2. APPLY_LIFT failed `invalid input syntax for type integer: "0.2"` → cast param `$1::numeric`.

**Status: DEPLOYED + smoke-tested (self-serve).** Next: real planner UAT; publication Delta-MERGE Job into
sandbox_operations.po_management; seed existing expansion_* events; reconfirm item-validation criterion.
