# Analytical + Transactional Serving Architecture

## Overview

On top of the medallion (Bronze → Silver → Gold), Milwaukee's supply-chain solution serves two distinct planes:

1. **Analytical plane** — read-only, low-latency access for dashboards and decision support (Lakeview AI/BI dashboards, Lakebase synced tables)
2. **Transactional plane** — write-through app state for human and agent workflows (Lakebase Postgres OLTP, idempotent action execution)

Together they close the loop: **Data → Recommendation → Decision → Action → Outcome → Learning**.

---

## Analytical Plane: Read-Layer for Insights & App Display

### Served from: Gold Layer + Metric Views

The analytical plane sits atop Gold tables and UC metric views, both read-only sources of truth for all consumption patterns (dashboards, app displays, external reporting). Gold tables are the normalized, dimensionally-modeled supply entities (`items`, `organizations`, `weeks`, `plans`, `actuals`, etc.); metric views are certified, semantic aggregations of those dimensions (e.g., `plan_vs_actual_weekly`, `inventory_position_by_org`, `planner_routed_exceptions`).

**Why separate read-layer products:**

| Need | Product | Why |
|------|---------|-----|
| **KPI dashboard, charts, multi-snapshot comparison, "was green now red" visual story** | **Lakeview (AI/BI)** | Managed, declarative; BI semantics (measures, dimensions); interactive filters; Genie Ask integration; CRITICAL: SQL is tested before deploy, no queries at read-time |
| **App needs sub-second item lookups, exception queue, routed assignments by planner/org** | **Lakebase synced tables** | Data synced from Gold Delta into read-only Postgres; point queries and full-text search at operational speed; app avoids warehouse round-trips; no concurrent edits (read-only in Postgres) |

### 1. Lakeview AI/BI Dashboards

**Purpose:** Standalone, governed KPI and trend surfaces for planners and operations leadership to see the supply state and spot exceptions at a glance.

**Dashboards to build:**

#### P1 Plan vs Actual Dashboard

Directly addresses the "manually pull from multiple systems every Monday" pain — a single, governed dashboard that shows the weekly plan-vs-actual position by item, organization, and week, with multi-snapshot comparison to surface "was green last week, red now."

**Data source:** Gold `plan_vs_actual_weekly` (or equivalent metric view, pre-aggregated at item × org × week × measure grain)
```sql
-- Example Gold dataset (NOT a production query; illustrates the structure)
SELECT 
  item_id, item_name,
  organization_id, organization_name,
  week_ending,
  plan_quantity, plan_value_usd,
  actual_quantity, actual_value_usd,
  variance_quantity, variance_pct,
  variance_status  -- 'green', 'yellow', 'red'
FROM gold.plan_vs_actual_weekly
WHERE week_ending >= DATE_SUB(CURRENT_DATE, 91)  -- last 13 weeks
ORDER BY week_ending DESC, variance_pct DESC
```

**Dashboard widgets (Lakeview, per `databricks-aibi-dashboards`):**

1. **KPI Row** (3 counters, width=4 each, height=3):
   - Total Items On Track (variance_status = 'green')
   - Items At Risk (variance_status = 'yellow' or 'red')
   - Largest Variance (MAX variance_pct)
   - Each displays current week snapshot + comparison to prior week (delta, % change)

2. **Trend Chart** (line chart, width=12, height=5):
   - Y-axis: Variance % (0–100)
   - X-axis: Week ending (last 13 weeks)
   - Color by organization (max 5; if more, TOP-5 + Other)
   - Sparkline on each counter shows the same trend
   - **CRITICAL (from skill): SQL tested before deploy; numbers certified by metric definition; freshness/source labeled**

3. **Exception Queue Table** (width=12, height=6):
   - Rows: items in red or yellow, sorted by variance descending
   - Columns: item name, org, plan qty, actual qty, variance %, status, week
   - Click an org to filter all widgets (cross-filtering via Lakebase synced dataset)

4. **Snapshot Comparison Selector** (filter, width=12):
   - Multi-select: pick 2–3 weeks to compare side-by-side
   - Renders a comparison matrix below (built as pivot or custom viz)

**Lakebase synced tables used in dashboard:** None (dashboard consumes Gold directly via warehouse query)

**Dashboard theme & notation (from `databricks-app-design`):**
- **60/30/10 rule:** Neutral #FCFCFC canvas, semantic variance color (green=#6DD980, yellow=#FFA600, red=#FF7E5C), accent blue #2272B4 for selection
- **IBCS notation:** 
  - Counter message: "Items On Track (vs. last week +2%)" 
  - Scenario marks: actual = solid line, plan = dashed, threshold = muted tone
  - Honest scales: if variance typically 5–15%, don't use 0–100 y-axis (compresses signal)

**Freshness & governance:** 
- Dashboard refreshed on medallion refresh cadence (nightly or per SLA)
- Every KPI shows period + comparison basis (e.g., "Week ending 2026-03-15 vs. 2026-03-08")
- Source label: "Data from Gold layer, certified 2026-03-15T06:30Z"
- Ask-Genie link (optional): wired to a read-only Genie space over the Gold tables; users can ask "Why did variance spike last week?" or "Which organizations have the most at-risk items?"

---

### 2. Lakebase Synced Tables: UC→Postgres Read-Only Serving Layer

**Purpose:** Low-latency, point-query access to app-grain analytical data. Planners and exceptions app reads current item state, routed assignments, and exception metadata without hitting the SQL warehouse.

**Why Lakebase synced tables (not direct warehouse queries from the app):**
- App needs **sub-second** lookups (e.g., "load all exceptions for this planner") — warehouse queries take 2–10 seconds
- **Operational data serving:** full-text search on item names, prefix search on item codes, filtering by planner + status — natural Postgres operations, poor fit for analytical warehouse
- **Read-only in Postgres:** prevents concurrent edits on synced data; changes flow back to Delta via CDC (see Transactional Plane section below), maintaining single source of truth in UC
- **App avoids warehouse scaling costs:** doesn't need warehouse compute for every cell in a list or every keystroke in a typeahead

**Synced tables to create (from Gold layer, continuous or triggered sync per Lakebase `databricks-lakebase` skill):**

| Synced Table | Source | Grain | Frequency | App Use Case |
|--------------|--------|-------|-----------|--------------|
| `public.items_current` | `gold.item_master` | item | Continuous or triggered (daily) | Item lookup, typeahead search, detail view |
| `public.organizations_current` | `gold.organization_master` | org | Continuous | Org filter, routing |
| `public.planners_current` | `gold.planner_master` | planner | Triggered (daily) | Planner assignment, routing, user context |
| `public.exception_summary_current` | `gold.supply_exceptions_summary` (or pre-agg view) | item × org × exception_type | Triggered (hourly) | Exception queue, counts, status rollup |
| `public.inventory_position_current` | `gold.inventory_position` | item × org × location | Continuous | Inventory context on exceptions, details |
| `public.forecast_by_item_org` | `gold.demand_forecast` | item × org × week | Triggered (daily) | Demand event context, safety checks |

**Sync strategy (from Lakebase skill):**
- **Continuous sync** for frequently-changing tables (items, inventory — new stock arrives constantly)
- **Triggered sync** for slower-changing metadata (orgs, planners) or heavy aggregations (exception summary) — daily or hourly jobs kick off the sync
- **CDF enabled** on source Gold tables if continuous sync uses PITR or snapshot-only—not required for triggered (sync just re-copies the table)
- **Read-only in Postgres:** No writes to synced tables in Lakebase; app writes go to native Lakebase tables (exception_case, event_draft, etc.; see Transactional Plane)

**App reads from synced tables (example from `databricks-apps` AppKit pattern):**

```typescript
// In Databricks App, via Lakebase native queries:
// Synced tables are read-only in Postgres; app fetches them for operational display.
const exceptionQueue = await lakebase.query(
  `SELECT 
    id, item_id, item_name, org_id, org_name, 
    exception_type, severity, status, created_date
   FROM public.exception_summary_current 
   WHERE org_id = $1 AND status IN ('new', 'assigned')
   ORDER BY severity DESC, created_date ASC
   LIMIT 50`,
  [orgId]
);

// Typeahead search on item names (Postgres strength):
const itemMatches = await lakebase.query(
  `SELECT id, item_code, item_name, upc 
   FROM public.items_current 
   WHERE item_name ILIKE $1 OR item_code ILIKE $1
   LIMIT 10`,
  [`${searchTerm}%`]
);
```

**Gotcha (from Lakebase skill):**
- **Synced tables are READ-ONLY in Postgres.** Do not INSERT/UPDATE/DELETE them in Lakebase. Any modification breaks the sync pipeline. App writes (exception cases, event drafts, assignments) go to native Lakebase tables instead (see Transactional Plane).
- **UC→Postgres is one-way.** Delta table is the source of truth. If the source Delta table is deleted or schema changes, the synced table in Postgres becomes stale or orphaned. Always treat the synced table as a cache.
- **Data type mapping:** Some UC types (ARRAY, MAP, STRUCT) may not sync cleanly to Postgres native types. Flatten or pre-aggregate in Gold if needed (e.g., ARRAY of tags → exploded rows or JSON column).
- **Capacity:** Synced tables count against Lakebase storage. For very large tables (>100 GB), consider syncing aggregations or recent partitions only (e.g., last 90 days).

---

## Transactional Plane: Write-Layer for App State & Workflows

### Served from: Lakebase Postgres (Native Tables) + Integration Outbox

The transactional plane is the source of truth for all app state: exceptions in flight, assignments, approvals, user-generated event drafts, audit logs, and action requests awaiting execution. It is **NOT** the data warehouse — it is the operational state machine that powers the planners' workflow.

### 1. Lakebase Native Tables (OLTP State)

**Purpose:** Concurrent, transactional storage of app state with optimistic locking, audit trails, and idempotent execution guarantees. Solves the "no tracking, no locking, no audit" pain.

**Tables to create (from `databricks-lakebase` skill, in the `production` branch of a dedicated Lakebase project):**

#### Exception Workflow State

```sql
-- exception_case: root exception entity
CREATE TABLE exception_case (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  exception_type TEXT NOT NULL,  -- 'supply_shortage', 'demand_spike', etc.
  severity TEXT NOT NULL,         -- 'critical', 'high', 'medium', 'low'
  status TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'assigned' | 'in_review' | 'resolved' | 'closed'
  
  -- Optimistic locking: version incremented on every write
  version INTEGER NOT NULL DEFAULT 1,
  
  -- Assignment & routing
  assigned_to_planner_id TEXT,    -- NULL until assigned
  assigned_to_team_id TEXT,       -- NULL until assigned (from O finding: 69% have no named planner)
  route_context JSONB,            -- { "org_role": "...", "criticality": "...", "sku_category": "..." }
  
  -- Audit trail
  created_by TEXT NOT NULL,       -- username or service principal
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_by TEXT NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_item FOREIGN KEY (item_id) REFERENCES items_current(item_id),
  CONSTRAINT fk_org FOREIGN KEY (organization_id) REFERENCES organizations_current(org_id)
);

-- disposition: resolution actions on an exception
CREATE TABLE disposition (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exception_case_id UUID NOT NULL REFERENCES exception_case(id),
  action TEXT NOT NULL,           -- 'increase_stock', 'adjust_forecast', 'escalate', 'close_no_action'
  action_detail JSONB NOT NULL,   -- { "qty": 500, "supplier_id": "...", "due_date": "..." }
  
  disposition_by TEXT NOT NULL,   -- who made the decision
  disposition_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reason TEXT,
  
  -- Flag for external action
  requires_external_sync BOOLEAN DEFAULT FALSE,  -- TRUE if this needs Oracle/SCC writeback
  external_sync_status TEXT DEFAULT 'pending',   -- 'pending' | 'sent' | 'confirmed' | 'failed'
  
  CONSTRAINT fk_exception FOREIGN KEY (exception_case_id) REFERENCES exception_case(id)
);
```

#### Event (Demand Event Lifecycle) Workflow State

```sql
-- event_draft: user creates a new demand event, begins edit cycle
CREATE TABLE event_draft (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_name TEXT NOT NULL,
  event_description TEXT,
  
  -- Lifecycle state
  status TEXT NOT NULL DEFAULT 'draft',  -- 'draft' | 'pending_review' | 'in_activation' | 'active' | 'deactivated'
  
  -- Event detail
  item_id TEXT NOT NULL REFERENCES items_current(item_id),
  organization_id TEXT NOT NULL REFERENCES organizations_current(org_id),
  event_type TEXT NOT NULL,              -- 'promotional', 'seasonal', 'supply_constraint', etc.
  
  demand_qty_delta INTEGER,              -- incremental demand (positive or negative)
  effective_week_start DATE NOT NULL,
  effective_week_end DATE NOT NULL,
  
  -- Locking: prevents concurrent edits (fixes Excel pain)
  locked_by TEXT,                        -- NULL if unlocked; planner username if locked
  locked_at TIMESTAMP,
  lock_expires_at TIMESTAMP,             -- lock auto-expires after 24h (from event_lock table, see below)
  
  version INTEGER NOT NULL DEFAULT 1,    -- optimistic concurrency
  
  created_by TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_by TEXT NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT lock_consistency CHECK (
    (locked_by IS NULL AND locked_at IS NULL) OR 
    (locked_by IS NOT NULL AND locked_at IS NOT NULL)
  )
);

-- event_lock: separate lock table for pessimistic locking (fixes "can't edit while Joe has it open" problem)
CREATE TABLE event_lock (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_draft_id UUID NOT NULL REFERENCES event_draft(id),
  locked_by TEXT NOT NULL,               -- planner username
  locked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,         -- e.g., locked_at + INTERVAL '24 hours'
  
  UNIQUE(event_draft_id)                 -- only one lock per event
);

-- planner_comment: inline comments during event edit/review (audit trail)
CREATE TABLE planner_comment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_draft_id UUID NOT NULL REFERENCES event_draft(id),
  comment_text TEXT NOT NULL,
  
  commented_by TEXT NOT NULL,
  commented_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  -- Resolve/reopen comment threads
  resolved_at TIMESTAMP,
  resolved_by TEXT
);

-- approval: gating step before event activation
CREATE TABLE approval (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_draft_id UUID NOT NULL REFERENCES event_draft(id),
  approval_type TEXT NOT NULL,  -- 'demand_planning_review', 'supply_chain_review'
  
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected'
  approved_by TEXT,
  approved_at TIMESTAMP,
  rejection_reason TEXT,
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Action Request & Execution

```sql
-- action_request: typed, auditable request for external system changes (e.g., Oracle Fusion, SCC)
CREATE TABLE action_request (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Origin: what triggered this action
  origin_type TEXT NOT NULL,  -- 'exception_disposition' | 'event_activation' | 'manual_planning'
  origin_id UUID NOT NULL,    -- exception_case.id or event_draft.id or null
  
  -- Action contract
  action_type TEXT NOT NULL,  -- 'create_purchase_order' | 'update_forecast' | 'adjust_safety_stock' | 'transfer_inventory'
  action_params JSONB NOT NULL,  -- { "supplier_id": "...", "qty": 500, "delivery_date": "..." }
  
  -- Execution state
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'submitted' | 'confirmed' | 'failed' | 'rolled_back'
  
  -- Idempotency (prevents duplicate execution if retried)
  idempotency_key TEXT UNIQUE NOT NULL,
  
  -- Audit
  requested_by TEXT NOT NULL,
  requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  executed_at TIMESTAMP,
  executed_by TEXT,  -- service principal or human
  
  external_system_ref TEXT,  -- e.g., PO# in Oracle, SCC request ID
  error_message TEXT,        -- if failed
  
  version INTEGER NOT NULL DEFAULT 1
);

-- integration_outbox: outbound event for external systems (CDC-like pattern)
CREATE TABLE integration_outbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_request_id UUID REFERENCES action_request(id),
  
  target_system TEXT NOT NULL,  -- 'oracle_fusion' | 'scc' | 'wms' | 'tms'
  event_type TEXT NOT NULL,     -- 'purchase_order.create' | 'forecast.update'
  payload JSONB NOT NULL,
  
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'sent' | 'acknowledged' | 'failed'
  retry_count INTEGER DEFAULT 0,
  last_retry_at TIMESTAMP,
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- integration_result: confirmation from external system
CREATE TABLE integration_result (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_request_id UUID REFERENCES action_request(id),
  
  target_system TEXT NOT NULL,
  external_ref TEXT NOT NULL,  -- e.g., PO number returned by Oracle
  
  status TEXT NOT NULL,  -- 'success' | 'partial' | 'failed'
  result_payload JSONB,
  
  received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Idempotency & Notification

```sql
-- idempotency_record: prevent duplicate actions on retry
CREATE TABLE idempotency_record (
  idempotency_key TEXT PRIMARY KEY,
  result_type TEXT NOT NULL,
  result_payload JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL  -- TTL: 30 days
);

-- notification_delivery: tracking sent notifications (optional; for audit & retry)
CREATE TABLE notification_delivery (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient_email TEXT NOT NULL,
  notification_type TEXT NOT NULL,  -- 'exception_assigned' | 'event_approved' | 'action_failed'
  
  related_id UUID,  -- exception_case.id or event_draft.id
  
  status TEXT NOT NULL DEFAULT 'pending',  -- 'sent' | 'bounced' | 'read'
  sent_at TIMESTAMP,
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- saved_search: remember user's filter/sort preferences in the app
CREATE TABLE saved_search (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  search_name TEXT NOT NULL,
  
  filter_spec JSONB NOT NULL,  -- { "org_id": "...", "status": "open", "severity": "critical" }
  sort_spec TEXT,              -- 'created_at DESC' | 'severity DESC, item_name ASC'
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, search_name)
);
```

**Schema design principles:**
- **Optimistic locking** (version field): App reads `version`, makes changes, writes back with `WHERE version = @oldVersion; IF @@ROWCOUNT = 0 THEN CONFLICT`. Handles non-blocking concurrent edits (exceptions and events can be modified by different planners without explicit locks).
- **Pessimistic locking** (event_lock table): For demand events, a separate lock entity prevents two planners from editing the same draft simultaneously. Lock TTL auto-expires (fixes stuck-lock pain from Excel).
- **Audit trail**: Every table has `created_by`, `created_at`, `updated_by`, `updated_at`. Comments, approvals, and dispositions are immutable snapshots (no UPDATE; new rows for state changes).
- **Idempotency key**: Action requests include a UUID generated client-side; if the request is retried, the same key guarantees the action only executes once. Prevents duplicate PO creation if a network error causes the client to retry.
- **Type safety**: Action params are JSONB with a schema (enforced at app layer, not DB); validated on insert to catch mismatches early.

---

### 2. Change Data Capture (CDC) → Delta: Closing the Loop

**Purpose:** Write outcomes back to sandbox_operations.po_management for analysis and feedback.

**From Lakebase skill:**
- Lakebase supports **Lakehouse CDC** (UI-only; cannot be configured via CLI/API): captures all writes to a native Lakebase table, publishes change events to Delta, and maintains a CDC-enabled table in UC with `_change_type` (`insert`/`update`/`delete`) and `_commit_version` columns.
- Not all Lakebase tables need CDC; enable it only for tables whose writes you want to log (exception_case, disposition, event_draft, action_request, integration_result).

**CDC flow:**
```
Lakebase (native table)
  ↓ [Write: INSERT/UPDATE on exception_case]
  ↓ [CDC captures: type='INSERT', row={...}, commit_version=123]
  ↓
Delta table: sandbox_operations.po_management.exception_case_cdc
  [schema: id, item_id, org_id, ..., _change_type, _commit_version, _commit_timestamp]
  ↓
[Analytics queries read from CDC table to reconstruct state over time]
```

**Benefits:**
- **Audit trail versioning:** Track how each exception evolved from `open` → `assigned` → `resolved` → `closed`
- **Outcome measurement:** Join CDC `disposition` writes with historical exceptions to measure resolution effectiveness (e.g., "73% of critical exceptions resolved within 24h")
- **Feedback loop:** Recommendations engine reads historical outcomes to improve routing logic ("Planner X resolves supply_shortage faster than avg; route more to them")

**Sandbox tables to populate via CDC:**
- `sandbox_operations.po_management.exception_case_cdc` — exception state over time
- `sandbox_operations.po_management.event_draft_cdc` — event lifecycle (draft → active → deactivated)
- `sandbox_operations.po_management.disposition_cdc` — resolution actions
- `sandbox_operations.po_management.action_request_cdc` — external system requests and their outcomes

---

### 3. Databricks Apps: Unified Planner Workflow

**Purpose:** Single, auth-gated app that all planners use to view exceptions, manage demand events, approve actions, and collaborate — replacing email, Excel, and manual multi-system hunting.

**From `databricks-apps` and `databricks-app-design` skills:**

#### Architecture

The app is an **AppKit TypeScript/React app** with Lakebase resource wiring:

```
Databricks App (mke-supply-planner)
  ├── Frontend (React/AppKit-UI)
  │    ├── Dashboard: KPI overview (synced table reads)
  │    ├── Exception Queue: list/filter/assign (synced table reads + Lakebase native table writes)
  │    ├── Demand Events: create/edit/lock/approve (Lakebase native table CRUD)
  │    ├── Action Review: approve/execute typed actions (Lakebase native table writes)
  │    └── Ask-Genie module (optional): natural-language questions over Gold tables
  │
  ├── Backend (Node.js + Express)
  │    ├── /api/exceptions (GET synced + native tables, POST assignment/disposition)
  │    ├── /api/events (GET drafts, POST create/lock/unlock/activate)
  │    ├── /api/actions (GET pending, PUT execute/approve)
  │    ├── /api/identity (GET current user, POST assignment preferences)
  │    └── Service principal auth (OAuth token refresh, user context via x-forwarded-email)
  │
  ├── Lakebase Postgres (OLTP state)
  │    ├── Native: exception_case, event_draft, event_lock, approval, action_request, ...
  │    ├── Synced (read-only): items_current, organizations_current, planners_current, exception_summary_current, ...
  │    └── CDC back to Delta: exception_case_cdc, event_draft_cdc, action_request_cdc, ...
  │
  └── Deployment
       ├── Service Principal credentials (scoped: Lakebase connection, Delta read)
       ├── Resource wiring in app.yaml (Lakebase postgres resource)
       └── CI/CD: validate → deploy → run smoke tests
```

#### Four Modules (Personas: P2, P3, P4 aligned)

**Module 1: Actuals & Plan vs Actual (P1 support)**
- **Users:** Operations managers, demand planners
- **Screens:**
  - Overview: 3-column KPI (On Track, At Risk, Max Variance) with sparklines
  - Trend: line chart (variance % over last 13 weeks) with org filter
  - Details: full table of items + plan/actual/variance, sortable, exportable
- **Data source:** Gold `plan_vs_actual_weekly` (synced into Lakebase for fast lookup)
- **Interaction:** Click org in KPI → filters all charts to that org (cross-widget filtering via Lakebase query)
- **From app-design:** Use `counter` for KPIs (height=3-4, width=4), `line` chart (width=6–12), `table` (width=12) — all with semantic color (green/#6DD980, yellow/#FFA600, red/#FF7E5C) and IBCS notation (counter message: "Items On Track (vs. last week +2%)")

**Module 2: Supply Exceptions (P2 core)**
- **Users:** Supply planners, exception specialists
- **Screens:**
  - Queue: sortable list of open/assigned exceptions (from Lakebase `exception_case` + synced `exception_summary_current`)
  - Filters: status, severity, organization, item code (typeahead from synced `items_current`), planner assignment
  - Detail: exception info + linked disposition history + planner comment thread + assignment controls
  - Bulk actions: select multiple exceptions → batch-assign to team/planner, batch-mark-resolved
- **Data source:** Lakebase native `exception_case` (write) + synced `exception_summary_current`, `planners_current` (read)
- **Workflow:**
  1. Planner views queue, filters by "severity=critical, org=NA, status=open"
  2. Clicks an exception → opens detail pane
  3. Reads comments from exception workflow thread
  4. Selects "Assign to Planner" → autocomplete (from synced `planners_current`) → clicks "Mike T" → writes to `exception_case.assigned_to_planner_id`, `updated_at`, `updated_by` (optimistic concurrency: version check)
  5. Planner (Mike) now sees exception in "Assigned to Me" queue
  6. Enters disposition: action=`increase_stock`, qty=500, supplier=ABC → writes to `disposition` table
  7. If requires Oracle PO, app auto-creates `action_request` with idempotency key → external action service picks it up → writes to `integration_outbox` → Oracle confirms → `integration_result` recorded
- **From app-design:** `table` with server-side sort/filter/pagination (avoid loading 10K rows client-side), `badge` for severity/status colors, typeahead `input` for planner search, bulk checkbox column, action buttons (Assign, Resolve, Escalate) with confirmation modals

**Module 3: Demand Events (P3 core)**
- **Users:** Demand planners, event lifecycle managers
- **Screens:**
  - List: all events (draft, pending review, active, deactivated) with status badges
  - Create: form (item code typeahead, org selector, event type, demand delta, effective dates)
  - Edit: form with lock indicator ("Locked by Mike T since 14:22, expires 14:52") and lock/unlock buttons
  - Approve: review event detail + comments → Approve / Reject buttons (writes to `approval` table)
  - Activation: once approved, activate to `active` status (triggers publish to Oracle Demand Planning)
- **Data source:** Lakebase native `event_draft`, `event_lock`, `planner_comment`, `approval` (writes); synced `items_current`, `organizations_current`, `forecast_by_item_org` (reads)
- **Workflow:**
  1. Planner clicks "New Event"
  2. Form: "Item=ABC (typeahead from synced `items_current`), Org=EMEA, Type=Promotional, Delta=+500 units, Weeks=2026-04-01 to 2026-04-14"
  3. App generates UUID for event, inserts into `event_draft` with `status='draft'`, `created_by=user`, `locked_by=NULL`
  4. Planner edits; app acquires lock: INSERT into `event_lock` with `expires_at=now+24h`. Display "You have the lock" in UI.
  5. Planner adds comment ("Promotional spike, expect high demand this week") → INSERT into `planner_comment`
  6. Planner clicks "Submit for Review" → updates `event_draft.status='pending_review'` + releases lock (DELETE from `event_lock`)
  7. Approver (different user) views "Pending Review" tab → clicks event → reviews detail + comments → clicks Approve → INSERT into `approval` with `status='approved'`, `approved_by=approver`
  8. Once approved, planner activates: UPDATE `event_draft.status='active'` → app publishes to Oracle Demand Planning (async job picks up from `integration_outbox`)
- **From app-design:** `form` with conditional fields (event type selects sub-fields), `badge` for lock status (color=orange if locked by someone else, green if locked by me), **error/empty states:** "No events created yet — Create your first event" with a button; "Event locked by Jane, expires at 15:30" (clear UX); `badge` for approval status (pending/approved/rejected)

**Module 4: Demand Exceptions (P4)**
- **Users:** Demand managers
- **Screens:**
  - Similar to Module 2 (exceptions) but filtered to demand-specific exception types (demand_spike, demand_drop, forecast_variance_large)
  - Disposition: adjust forecast, transfer stock, notify supplier
- **Data source:** Lakebase native `exception_case` (exception_type IN demand_*), `disposition` (writes)

**Ask-Genie Integration (Optional per module)**
- Embed a `GenieChat` component in each module's detail pane
- User can ask: "Why did this exception trigger?" or "What's the forecast for this item next quarter?"
- Query runs over Gold tables (read-only Genie space); answers show generated SQL + source + [AI-generated, verify] disclaimer
- From `databricks-app-design`: Genie surfaces require identity (x-forwarded-email badge), generated SQL card, streaming status, disclaimer, execution-identity note (OBO if user-scoped, else service principal)

**Typed Actions & Human Gate**
- `action_request` is a **typed data contract**: schema defines allowed actions (`create_purchase_order`, `update_forecast`, etc.) and required params (supplier_id, qty, delivery_date)
- App validates params before inserting into `action_request` → enforces data quality before external systems see it
- Action review screen shows pending actions with risk indicators (e.g., "High: PO for $50K to new supplier ABC")
- Planner can "Approve" or "Reject" (writes to `action_request.status`, adds execution audit)
- Approved actions go to async executor (not shown in app; runs via Lakeflow Job): reads from `integration_outbox`, calls Oracle API, writes result to `integration_result`
- If external system rejects (e.g., Oracle validation error), action status becomes `failed` + error_message populated; planner is notified

---

### 4. Persona Routing (Fixes O Finding: 69% of Items Have No Named Planner)

**Problem:** Exceptions and events arrive unrouted; planners manually hunt them down or they get lost.

**Solution:** Lakebase-backed routing engine filters the queue by persona + context.

**Routing rules (in app filters + backend query logic):**

```sql
-- Backend route_recommendations(user_id, org_id) pseudo-query
-- Returns exceptions this planner should see
SELECT 
  ec.id, ec.item_id, ec.status, ec.severity,
  CASE 
    WHEN p.specialized_categories ? ec.item_category THEN 1
    WHEN ec.organization_id = ANY(p.primary_orgs) THEN 2
    WHEN ec.severity = 'critical' THEN 3
    ELSE 4
  END AS route_priority,
  ec.created_at
FROM public.exception_case ec
JOIN public.planners_current p ON p.id = $1  -- current user
WHERE 
  ec.status IN ('open', 'assigned') 
  AND (
    -- Primary routing: my org + specialized category
    (ec.organization_id = ANY(p.primary_orgs) AND ec.item_category = ANY(p.specialized_categories))
    -- Secondary: any exception in my orgs
    OR ec.organization_id = ANY(p.primary_orgs)
    -- Fallback: critical exceptions (no named planner → route to oncall team)
    OR ec.severity = 'critical'
  )
ORDER BY route_priority, ec.severity DESC, ec.created_at ASC;
```

**Planner profile (synced table `planners_current`):**
```json
{
  "id": "planner_001",
  "name": "Mike T",
  "primary_orgs": ["NA", "LATAM"],
  "specialized_categories": ["electronics", "semiconductors"],
  "is_oncall": false,
  "team": "supply_na"
}
```

**In the app:** 
- Planner signs in → app fetches user context from synced `planners_current`
- Exception queue filters to "My Queue" (routed exceptions) vs. "All Open" (for escalation/helping out)
- Assignment filter shows "Assign to My Team" (prepopulates from team_id in planner profile) or "Assign to User" (autocomplete on planner names + specializations)

---

## Closed Loop Diagram (Text)

```
┌──────────────────────────────────────────────────────────────────┐
│                    ANALYTICAL + TRANSACTIONAL LOOP                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [1] SOURCES (READ-ONLY)                                          │
│      ├─ prod_edw.actuals, prod_edw.plans                          │
│      ├─ prod_operations.supply_state, prod_operations.forecast    │
│      └─ External: Oracle Fusion, SCC, WMS                         │
│           ↓                                                        │
│  [2] MEDALLION TRANSFORMATION (Gold Layer)                        │
│      ├─ gold.plan_vs_actual_weekly (item×org×week grain)          │
│      ├─ gold.supply_exceptions_summary (pre-agg)                  │
│      ├─ gold.item_master, gold.organization_master, ...           │
│      ├─ Metric Views: plan_vs_actual, inventory_position, ...     │
│      └─ UC certified + governed (metadata, lineage, SLA)          │
│           ├─────────────────────┐                                 │
│           ↓                     ↓                                  │
│  [3A] ANALYTICAL READ           [3B] TRANSACTIONAL READ           │
│      (Low-latency dashboards)       (Operational app state)       │
│                                                                    │
│      Lakeview AI/BI Dashboards  Lakebase Synced Tables            │
│      ├─ P1 Plan vs Actual       ├─ items_current                  │
│      ├─ Exception trends        ├─ exception_summary_current      │
│      ├─ KPI cards + Ask-Genie   ├─ planners_current               │
│      └─ Semantic color + IBCS   ├─ inventory_position_current     │
│           notation              └─ (Postgres: sub-second reads)    │
│           ↓                     ↓                                  │
│      Dashboard users view       App users see routed exceptions,  │
│      "was green now red"        current inventory, etc.            │
│      multi-snapshot story       (filters by org/planner/severity)│
│                                                                    │
│           ↓                     ↓                                  │
│      (RO analysis)    [4] HUMAN DECISION LOOP    (RO context)     │
│                                                                    │
│                      ┌─────────────────────────┐                  │
│                      │  Databricks Apps         │                 │
│                      │  (Unified planner app)  │                 │
│                      ├─────────────────────────┤                  │
│                      │ Exception Queue Module  │                  │
│                      │ - Review exception      │                  │
│                      │ - Assign to planner     │                  │
│                      │ - Enter disposition     │                  │
│                      │ - Approve action        │                  │
│                      ├─────────────────────────┤                  │
│                      │ Event Lifecycle Module  │                  │
│                      │ - Create demand event   │                  │
│                      │ - Lock (pessimistic)    │                  │
│                      │ - Approve               │                  │
│                      │ - Activate to Oracle    │                  │
│                      ├─────────────────────────┤                  │
│                      │ Typed Actions           │                  │
│                      │ - Create purchase order │                  │
│                      │ - Adjust forecast       │                  │
│                      │ - Validate params       │                  │
│                      │ - Require human approval│                  │
│                      └─────────────────────────┘                  │
│                       ↓ (Lakebase writes)                         │
│  [5] TRANSACTIONAL WRITE (App State)                              │
│      ├─ Lakebase native tables                                    │
│      │  ├─ exception_case (optimistic locking + audit)            │
│      │  ├─ event_draft (pessimistic lock: event_lock table)       │
│      │  ├─ disposition (immutable decision log)                   │
│      │  ├─ approval (gating step)                                 │
│      │  ├─ action_request (typed, idempotent)                     │
│      │  └─ planner_comment (thread)                               │
│      └─ Every write: version check + (created/updated)_by audit  │
│           ↓                                                        │
│  [6] EXTERNAL SYSTEM WRITEBACK (Typed Action Executor)            │
│      ├─ integration_outbox (async queued actions)                 │
│      ├─ Oracle Fusion: create PO, update forecast                 │
│      ├─ SCC: adjust safety stock                                  │
│      ├─ WMS: transfer inventory                                   │
│      └─ Executor validates + retries (idempotency key) + logs    │
│           ↓ (HTTP PUT/POST)                                       │
│      External system returns result → integration_result written │
│           ↓                                                        │
│  [7] OUTCOME CAPTURE (CDC → Delta)                                │
│      ├─ Lakebase CDC: exception_case_cdc, disposition_cdc,       │
│      │  event_draft_cdc, action_request_cdc, ...                  │
│      │  (schema: [all columns] + _change_type + _commit_version)  │
│      └─ Synced to Delta: sandbox_operations.po_management.*_cdc  │
│           ↓ (Append-only audit trail)                             │
│      Analytics reads outcomes:                                    │
│      - "73% critical exceptions resolved <24h"                    │
│      - "Planner X closes supply_shortage 30% faster than avg"     │
│      - "Event activation → Oracle publish latency: 4.2min avg"    │
│           ↓                                                        │
│  [8] FEEDBACK LOOP                                                │
│      ├─ Recommendations engine learns from outcomes               │
│      ├─ Routing rules updated (e.g., route more to fast planners) │
│      ├─ Alerts refined (reduce false positives)                   │
│      └─ Dashboard metrics roll into next week's KPI (loop closes) │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Analytical vs Transactional: Decision Table

**Use this to route each need to the correct product(s) and explain why unsuitable choices fail.**

| Need | Primary Product | Why | Secondary / Unsuitable |
|------|-----------------|-----|------------------------|
| **Compare plan vs actual across weeks; show "was green now red"** | Lakeview Dashboard (AI/BI) + Metric Views | Declarative SQL (pre-tested); managed UI; filters; Genie Ask link; certified metrics | **NOT Lakebase:** OLTP design wrong for scan-aggregation; **NOT Delta:** no low-latency reads; **NOT Apps:** overkill for read-only KPI |
| **Planners see exception queue in real-time; filter by org/severity/planner** | Databricks App (AppKit) + Lakebase synced tables (read) | App provides UI state + filtering; synced tables sub-second lookups; Postgres WHERE/JOIN fast | **NOT Dashboard:** static, can't click-filter; **NOT Delta:** warehouse too slow for every filter click; **NOT Lakebase native (read only):** synced tables are the RO layer, native for writes |
| **Typeahead search for item name while user types** | Lakebase synced tables (Postgres ILIKE) | Postgres full-text / ILIKE operators; sub-100ms response | **NOT Delta:** no FTS; **NOT Lakebase native:** not for reads; **NOT Dashboard:** not an input widget |
| **Store exception state + lock it so Joe can't edit while Mike has it open** | Lakebase native tables (pessimistic locking via event_lock) | Postgres transactions + advisory locks; app acquires lock on edit, releases on save; lock TTL auto-expires | **NOT Delta:** no locking; **NOT Dashboard:** no write UI; **NOT synced tables:** read-only; **NOT SQL warehouse:** no row-level locking |
| **Audit trail: track exception from open → assigned → resolved → closed** | Lakebase CDC (exception_case_cdc in Delta) | CDC captures every state change; immutable log; analytics can reconstruct timeline | **NOT Lakebase native alone:** no versioning; **NOT live tables:** UDL captures schema changes, not data edits |
| **User enters disposition: "increase stock +500, supplier ABC"** | Lakebase native + App form | Form validates params (typed contract); writes to disposition table with audit (user, timestamp); idempotency key prevents duplicate on retry | **NOT Dashboard:** no forms; **NOT Delta:** no ACID writes; **NOT synced tables:** read-only |
| **Route exception to the right planner based on org + specialty** | App filter query + Lakebase synced tables (planners_current) | Query joins exception_case with planners_current.specialized_categories; app renders "My Queue" | **NOT Dashboard:** no routing logic; **NOT Delta:** too slow; **NOT hand-coded:** brittle, hard to update |
| **External action (create PO in Oracle) with retry if network fails** | action_request + idempotency_key + integration_outbox | Typed contract guarantees valid params; idempotency key = same request never double-executes; integration_outbox queues retries | **NOT Delta:** no transactional support; **NOT Dashboard:** no writeback; **NOT Lakebase native alone:** need outbox + result tables |
| **Planners see "Jane has this event locked, expires at 15:30"** | Lakebase event_lock table + App UI | event_lock record = lock acquired; lock_expires_at = deadline; UI queries event_lock, shows badge | **NOT Delta:** no real-time queries; **NOT Dashboard:** static, can't poll; **NOT Postgres advisory locks alone:** need app-readable record |
| **Demand planner approves a demand event before it publishes to Oracle** | Lakebase approval table + App review screen | approval row stores decision + approver + timestamp; event_draft.status='active' only if approved; audit trail | **NOT Delta:** read-only source; **NOT Dashboard:** no approval workflow; **NOT action_request:** that's for external actions, not internal approvals |
| **Show planner their own saved filters (e.g., "My Critical NA Exceptions")** | Lakebase saved_search table + App sidebar | App stores filter spec + sort spec in saved_search; user clicks "My Critical NA" → app rewrites query | **NOT Dashboard:** global, not per-user; **NOT Delta:** analytics, not app state; **NOT app state alone:** no persistence |
| **Ask Genie: "Why did this exception trigger?" (read Gold tables)** | Ask-Genie (embedded in App) + read-only Genie space over Gold | Natural language → SQL over Gold tables; shows generated SQL + source + [AI-generated, verify] | **NOT Dashboard Ask:** limited context; **NOT exception_case table:** synced for ops only, not historical analysis; **NOT Lakebase native:** transactional, not analytical |

---

## Key Gotchas & Design Rules

### From Lakebase Skill

1. **Synced tables are READ-ONLY in Postgres.** App writes go to native Lakebase tables, never to synced tables. Modifying a synced table breaks the sync pipeline.
2. **UC→Postgres is one-way.** Delta is the source of truth. If the source table is dropped, synced table becomes orphaned.
3. **Data type mapping:** UC ARRAY/MAP/STRUCT columns may not sync cleanly to Postgres. Flatten or pre-aggregate in Gold if needed.
4. **CDF requires the source table to have Change Data Feed enabled.** Continuous sync uses CDF; if the Gold table doesn't have `delta.enableChangeDataFeed = true`, sync fails silently or falls back to snapshot-only mode.
5. **Lakebase is NOT a warehouse.** Don't try to run a 10-billion-row full scan on it; Postgres will timeout or run out of RAM. Use it for OLTP (point queries, full-text search) and bounded scans (LIMIT 1000).

### From Apps Skill

1. **Service Principal ownership of schemas:** The app's SP must own the schema it creates in Lakebase. Deploy the app FIRST before running it locally, so the SP creates the schema. If you run locally first (your credentials create the schema), the SP won't have access and you'll hit `permission denied 42501`. Workaround: drop the schema + redeploy, or export data + redeploy.
2. **AppKit version:** Never override `@databricks/appkit` in package.json. Let scaffolding set it. If you need a different version, re-scaffold with `--version <VERSION>`.
3. **Smoke tests:** MUST update `tests/smoke.spec.ts` selectors before validating. Default template checks for "Minimal Databricks App" and "hello world" — these WILL fail in your custom app.
4. **Large result sets:** Keep query results <1 MB (analytics event payload cap). Returning 50K raw rows causes `INVALID_REQUEST: Event exceeds max size`, leaving every assertion absent (the whole UI looks "no selected fields").
5. **SQL queries must be tested before deploy.** Use `databricks experimental aitools tools query --warehouse WH "SELECT ..."` to verify every query returns expected data, no errors, reasonable cardinality.

### From App-Design Skill

1. **Loading/empty/error states are mandatory.** Every data view must handle:
   - Loading: `Skeleton`
   - Empty: `Empty` with a next-step button (e.g., "Create your first exception")
   - Error: inline `Alert` with the message
   - Partial/stale: show what you have + a freshness note
2. **KPI freshness:** Every KPI shows unit + period + comparison + source + freshness (e.g., "12,345 items on track this week (vs. 11,890 last week), data current as of 2026-03-15 06:30Z").
3. **Semantic color:** Use the dashboard's `uiSettings.theme.visualizationColors` palette and semantic hex pins (good=green, bad=red, warning=orange). Don't hardcode colors in widgets; reference the theme.
4. **Cardinality limits:** Charts can show ≤8 distinct color groups. If higher (e.g., 50 product lines), use a table or TOP-N + "Other" bucket.
5. **Field name matching:** Every widget `fieldName` in encodings must exactly match a dataset column or alias. Mismatch = "no selected fields to visualize" error.

### From AI/BI Dashboard Skill

1. **SQL queries in dashboard must use bare table names.** No catalog or schema prefix. Example: `FROM trips`, not `FROM samples.nyctaxi.trips`. The `--dataset-catalog` and `--dataset-schema` flags only fill in missing parts; hardcoded prefixes are NOT overridden.
2. **Dashboard JSON: `queryLines` is an array of strings, NOT a `query` field.** Lines are joined verbatim with no separator — end each with ` ` or `\n`.
3. **`pageType` is required on every page.** Must be `PAGE_TYPE_CANVAS` or `PAGE_TYPE_GLOBAL_FILTERS`.
4. **Widget field name matching:** The `name` in `query.fields` MUST exactly match the `fieldName` in `encodings`. Mismatch = no visualization error.
5. **Cardinality: color-group charts max 8 distinct values.** Tables can show more; charts must aggregate or use TOP-N + "Other."
6. **12-column grid, no gaps.** Each row should fill width=12 exactly. Use standard widget sizes: counter (w=4, h=3-4), chart (w=6, h=5-6), table (w=12, h=5-8).
7. **Theme with 60/30/10 rule:** 60% neutral (background), 30% secondary (content), 10% accent (selection). Palette: ordered array of colors; `position: N` (0-indexed) pins to the Nth color.

---

## Operational Handoff: Freshness, SLA, & Monitoring

1. **Medallion refresh SLA:** Gold tables refresh on medallion schedule (nightly or per business requirement). Dashboard data is fresh as of last medallion run.
2. **Lakebase synced table refresh:** Continuous or triggered (hourly/daily) depending on table volatility. `exception_summary_current` should refresh hourly so app always sees recent exceptions; `planners_current` can refresh daily.
3. **Lakebase native write audit:** All writes include `created_at`, `updated_at`, `created_by`, `updated_by`. Enable CDC on `exception_case`, `event_draft`, `disposition`, `action_request` to feed sandbox_operations CDC tables for auditing.
4. **External action executor:** Async job (Lakeflow) reads `integration_outbox` every 5 minutes, executes actions, writes results to `integration_result`. Retry logic: up to 3 attempts, exponential backoff. If failed after retries, action_request status = `failed`, planner notified.
5. **Dashboard SLA:** P1 dashboard should have refresh cadence ≤1h (for operational freshness); refreshes on medallion schedule by default.
6. **App availability:** Lakebase SPA auto-scales 0.5–32 CU. For production, consider fixed compute ≥1 CU (avoid cold start delays).
7. **Monitoring & alerting:** Track key metrics:
   - Medallion refresh latency (SLA breach if Gold not updated by 08:00 UTC)
   - Synced table lag (Postgres should be ≤30 min behind Delta)
   - App exceptions (errors, locks held >24h, action failures)
   - External action success rate (target: >95% on first attempt)

---

## Summary

- **Analytical plane** serves read-only KPI insights (Lakeview) and operational lookups (Lakebase synced tables) for app and BI users.
- **Transactional plane** manages app state in Lakebase Postgres (native tables) with optimistic/pessimistic locking, audit trails, and idempotent external actions.
- **Closed loop** connects analytics (discovery) → recommendation → decision (app) → action (typed contract + external executor) → outcome (CDC to Delta) → learning (feedback loop).
- **Persona routing** solves the "69% no named planner" problem by filtering exceptions to the right planner based on org, specialty, and severity.
- **Decision table** routes each need (view, search, lock, audit, action, route, Ask) to the correct product; unsuitable choices fail on specific axes (latency, ACID, UI, locking, audit).
- **Gotchas** span Lakebase (read-only synced tables, CDC setup, data types), Apps (SP schema ownership, smoke tests, large result sets), App-Design (states, freshness, cardinality), and Dashboards (bare table names, field matching, grid layout).

