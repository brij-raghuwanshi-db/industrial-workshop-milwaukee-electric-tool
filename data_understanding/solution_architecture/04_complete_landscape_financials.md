# Complete Landscape: Supply, Demand, Inventory, Items & Financials
## Single Governed Place for the Full Picture

---

## 1. Unity Catalog: The Governed Landscape Backbone

The MKE supply-chain data is mature, siloed in a Databricks EDW (prod_edw, prod_operations), and already well-governed within schema/object-level permissions. Unity Catalog (UC) provides the **single lineage model, audit surface, and permission framework** that unifies supply + demand + inventory + items + suppliers + financials in one governed place — both for the existing EDW tables and for all derived assets written to `sandbox_operations.po_management`.

### Why UC as the Backbone

**1. Unified lineage (table + column level)**

The gap noted in earlier work: "lineage not accessible to the user" → the system.access.table_lineage view exists in UC but requires explicit `SELECT` grant. Once enabled, it shows:
- Source table → target table dependencies (20_supply_daily reads dim_series_ext_vw, item_days_on_hand_vw; 10_demand_daily reads dg5_customer; all write to sandbox_operations.po_management derived tables)
- Column-level lineage for financials: inventory_days_on_hand.on_hand_cost ← inventory_org FK joins items_scd1 FK joins dim_series_ext_vw cost columns

**Implementation**: Enable system.access lineage with:
```sql
GRANT USE CATALOG ON CATALOG system TO `data_engineers`;
GRANT USE SCHEMA ON SCHEMA system.access TO `data_engineers`;
GRANT SELECT ON SCHEMA system.access TO `data_engineers`;

-- Then query:
SELECT source_table_full_name, target_table_full_name, event_date
FROM system.access.table_lineage
WHERE event_date >= current_date() - 7
  AND (source_table_full_name LIKE '%prod_edw%' OR source_table_full_name LIKE '%sandbox%')
ORDER BY event_date DESC;
```

This fixes the "no lineage" problem: UC system tables provide audit + lineage end-to-end, not just within a schema.

**2. One catalog = one permission model**

Instead of managing grants in prod_edw (read-only), sandbox_operations (derived), and Lakebase (state) separately:
- Create a **single `mke_supply_chain` catalog** that owns prod_edw (as external references), sandbox_operations.po_management (as managed), and Lakebase synced tables (OLTP state)
- Grant `USE CATALOG` + `USE SCHEMA` + `SELECT` to analysts, `CREATE TABLE` + `MODIFY` to engineers in sandbox schemas
- Audit all access via `system.access.audit` (who accessed what table, when, from which cluster/app)

**Implementation** (after workspace is ready):
```sql
-- Create the catalog (Unity Catalog resource)
CREATE CATALOG mke_supply_chain COMMENT 'MKE supply-chain single landscape';

-- Grant read access to analysts across the full catalog
GRANT USE CATALOG ON CATALOG mke_supply_chain TO `mke_data_analysts`;
GRANT USE SCHEMA ON SCHEMA mke_supply_chain.prod_edw_views TO `mke_data_analysts`;
GRANT SELECT ON SCHEMA mke_supply_chain.prod_edw_views TO `mke_data_analysts`;

-- Grant write access to engineers in sandbox only
GRANT CREATE TABLE ON SCHEMA mke_supply_chain.po_management TO `mke_data_engineers`;
GRANT MODIFY ON SCHEMA mke_supply_chain.po_management TO `mke_data_engineers`;

-- Audit queries: who accessed which tables
SELECT event_time, user_identity.email, action_name, resource_name
FROM system.access.audit
WHERE resource_name LIKE 'mke_supply_chain.%'
  AND event_time >= current_timestamp() - interval 7 days
ORDER BY event_time DESC;
```

**3. System tables for observability**

UC system tables provide **billing, job run history, query performance, and data quality** in one governed place:
- `system.billing.usage` — DBU consumption by workspace/resource type (helps justify cost of financial dashboards)
- `system.access.table_lineage` — confirm source→derived flow for audit/SOX
- `system.access.audit` — detect unauthorized access attempts or schema drift
- `system.compute.profiles` — expensive queries on financials (slow-running `MEASURE()` queries on materialized metrics)

**Reference**: databricks-unity-catalog skill, [references/5-system-tables.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-unity-catalog/references/5-system-tables.md).

### Tags & Certification for Trusted Assets

Mark tables as certified (trusted, documented) or sensitive:
```sql
-- Tag a dimension as certified
ALTER TABLE mke_supply_chain.prod_edw_views.items_scd1
  SET TBLPROPERTIES ('owner_email' = 'supply_data@mke.com', 'certified' = 'true', 'sla_uptime' = '99.9%');

-- Tag financial tables as sensitive (for audit trail)
ALTER TABLE mke_supply_chain.po_management.actuals_weekly_summary
  SET TBLPROPERTIES ('sensitivity' = 'financial', 'pii_columns' = 'none');

-- Query certified tables only
SELECT table_name
FROM system.information_schema.tables
WHERE table_schema = 'po_management'
  AND table_properties LIKE '%"certified":"true"%';
```

---

## 2. Financial Completeness via Metric Views + Gold Layer

The supply-chain financials consist of **three layers**: raw source tables (purchase_orders.usd_price, dim_series_ext_vw.applied_standard_cost, inventory_days_on_hand.on_hand_cost, sales_order_line_transactions.base_extended_amount), Gold fact tables (po_management.actuals_weekly_summary, …plan_vs_actual), and **Metric Views** (reusable, governed KPI definitions).

### The Financial Boundary: Standard Cost + Order Pricing, NOT GL

**Critical caveat**: The cost figures come from **Oracle Business Suites standard-cost tables + purchasing system pricing**, not the General Ledger. This is fit-for-purpose for **supply-chain planning, inventory valuation, and exception management** but differs from accounting's GL COGS. Confirm with Finance before publishing as GAAP-reported cost.

**Data sources**:
- `dim_series_ext_vw`: **applied_standard_cost** (cost buildup: direct_material_cost + freight_cost + import_fees_cost + import_duty_cost + labor + overhead), currency_code
- `inventory_days_on_hand`: **on_hand_cost** = inventory quantity × applied_standard_cost (semi-additive: sum by item/org/date, NOT by currency)
- `purchase_orders`: **usd_price** / **usd_line_amount** = PO unit/line cost
- `sales_order_line_transactions`: **base_extended_amount** (revenue), **base_extended_cost** (COGS via standard cost)

### Metric Views: Define-Once Financial Measures

Metric Views separate **measure definitions** (SUM, COUNT, ratios) from **dimension groupings** (time, org, item, customer). Use `databricks-metric-views` skill to author them — they live in UC, support Genie + dashboards + SQL, and enable re-aggregation of ratios without double-counting.

**Example: Inventory Value Metric**

```yaml
CREATE OR REPLACE VIEW mke_supply_chain.po_management.inventory_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  source: mke_supply_chain.prod_edw_views.inventory_days_on_hand
  comment: "Inventory on-hand value, cost-of-goods, and aging"
  dimensions:
    - name: Organization
      expr: inventory_organization_id
      comment: "Distribution center / warehouse"
    - name: Item
      expr: item_bigint_key
      comment: "Item master key"
    - name: Snapshot Date
      expr: DATE_TRUNC('DAY', snapshot_date)
      comment: "Date of inventory snapshot"
    - name: Days On Hand Bucket
      expr: CASE
        WHEN on_hand_days <= 30 THEN 'Fast Moving'
        WHEN on_hand_days <= 90 THEN 'Normal'
        WHEN on_hand_days <= 180 THEN 'Slow Moving'
        ELSE 'Excess / Obsolete'
        END
      comment: "Aging bucket"
  measures:
    - name: On-Hand Quantity
      expr: SUM(on_hand_quantity)
      comment: "Units in stock"
    - name: On-Hand Cost USD
      expr: SUM(on_hand_cost)
      comment: "Total value in USD at standard cost (semi-additive)"
    - name: Cost per Unit
      expr: SUM(on_hand_cost) / SUM(on_hand_quantity)
      comment: "Average standard cost per unit"
    - name: Days On Hand - Average
      expr: AVG(on_hand_days)
      comment: "Average days in inventory"
$$
```

**Usage**: Dashboards/Genie query this without hand-writing aggregations:
```sql
SELECT
  `Organization`,
  `Days On Hand Bucket`,
  MEASURE(`On-Hand Quantity`) AS qty,
  MEASURE(`On-Hand Cost USD`) AS cost_usd,
  MEASURE(`Cost per Unit`) AS unit_cost
FROM mke_supply_chain.po_management.inventory_metrics
WHERE `Snapshot Date` = current_date()
GROUP BY 1, 2
ORDER BY cost_usd DESC;
```

### The Complete Financial KPI Set

Define these as Metric Views in `mke_supply_chain.po_management`:

| Metric View | Measures | Use Case |
|---|---|---|
| `inventory_metrics` | On-hand quantity, on-hand cost USD, cost/unit, days on hand avg | Inventory valuation, excess/obsolesce analysis |
| `purchase_order_metrics` | PO count, committed spend (usd_line_amount), received qty, variance $ | PO aging, supplier performance, budget vs. actual |
| `supply_plan_metrics` | Planned quantity, planned cost (qty × applied_standard_cost), variance to actuals | S&OP reconciliation, plan accuracy |
| `demand_metrics` | Demand quantity (by customer), revenue (base_extended_amount), margin (revenue - COGS) | Customer profitability, demand by region/product |
| `sales_actual_metrics` | Sales quantity, revenue, COGS (base_extended_cost), margin %, sell-through rate | Revenue recognition, gross margin by item/customer |
| `scrap_rework_metrics` | Scrap quantity, scrap cost (qty × applied_standard_cost), rework quantity, rework cost | Quality KPIs, waste analysis |
| `movements_metrics` | Movement count by type (receipt, shipment, transfer, etc.), cost impact | Supply-chain execution, network flow |

**Reference**: databricks-metric-views skill, [references/yaml-reference.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-metric-views/references/yaml-reference.md), [references/patterns.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-metric-views/references/patterns.md).

### Semi-Additive Gotcha: On-Hand Cost

`inventory_days_on_hand.on_hand_cost` is **semi-additive**: you can SUM it by **item + org + date**, but NOT across dates (a SUM of 30 daily snapshots double-counts inventory). Metric Views handle this declaratively — define the measure once, Genie/dashboards respect the grain.

---

## 3. The Item-360 Conformed View

Every supply-chain use case starts with **"What is the full story of this item?"** — its identity, demand, plan, on-hand position, receipts, suppliers, cost, ABC/PL, COO. A single conformed view (`item_360_gold`) assembles this, conforming by `item_bigint_key` and date.

### Item-360 Conformed View Definition

```sql
-- Read-only composite view joining all item dimensions and facts
-- Source: prod_edw (read-only) + items_scd1 dimension
CREATE OR REPLACE VIEW mke_supply_chain.po_management.item_360_gold AS

SELECT
  -- Identity
  i.item_bigint_key,
  i.item_id,
  i.item_name,
  i.item_description,
  
  -- Segmentation
  i.abc_classification,
  i.planning_family,
  i.country_of_origin,
  
  -- Demand (latest 4 weeks)
  d.demand_quantity_total,
  d.demand_by_customer,
  
  -- Supply Plan (current week + 12 weeks ahead)
  p.plan_quantity_this_week,
  p.plan_quantity_total_12w,
  p.plan_variance_units,
  
  -- On-Hand (latest snapshot)
  h.on_hand_quantity,
  h.on_hand_cost_usd,
  h.on_hand_days,
  h.on_hand_aging_bucket,
  
  -- Receipts (last 30 days)
  r.receipt_quantity_last_30d,
  r.receipt_count,
  
  -- Suppliers + Cost
  s.supplier_id,
  s.supplier_name,
  s.lead_time_days,
  s.applied_standard_cost,
  s.full_cost_breakdown_json,
  s.currency_code,
  
  -- Quality + Scrap
  q.scrap_quantity_ytd,
  q.scrap_cost_usd,
  q.rework_quantity_ytd,
  
  -- Movements (shipments, transfers)
  m.movement_count_last_7d,
  
  -- Calculated Financials
  ROUND(h.on_hand_quantity * s.applied_standard_cost, 2) AS inventory_value_usd,
  CASE WHEN h.on_hand_quantity > 0 THEN (s.applied_standard_cost / h.on_hand_quantity) ELSE 0 END AS cost_per_unit,
  
  -- Metadata
  CURRENT_TIMESTAMP() AS view_generated_at,
  MAX(h.snapshot_date) AS last_snapshot_date

FROM mke_supply_chain.prod_edw_views.items_scd1 i
LEFT JOIN (
  -- Demand: last 4 weeks, any customer
  SELECT item_bigint_key,
    SUM(order_quantity) AS demand_quantity_total,
    COUNT(DISTINCT customer_id) AS demand_by_customer
  FROM mke_supply_chain.prod_edw_views.demand_daily_aggregate
  WHERE order_date >= CURRENT_DATE() - 28
  GROUP BY item_bigint_key
) d ON i.item_bigint_key = d.item_bigint_key

LEFT JOIN (
  -- Supply Plan: weekly grain
  SELECT item_bigint_key,
    SUM(CASE WHEN plan_week = DATE_TRUNC('WEEK', CURRENT_DATE()) THEN plan_quantity ELSE 0 END) AS plan_quantity_this_week,
    SUM(plan_quantity) AS plan_quantity_total_12w,
    SUM(plan_quantity) - (SELECT SUM(order_quantity) FROM mke_supply_chain.prod_edw_views.demand_daily_aggregate
                          WHERE item_bigint_key = p.item_bigint_key AND order_date >= CURRENT_DATE() - 7) AS plan_variance_units
  FROM mke_supply_chain.prod_edw_views.supply_plan_weekly p
  WHERE plan_week BETWEEN DATE_TRUNC('WEEK', CURRENT_DATE()) AND DATE_TRUNC('WEEK', CURRENT_DATE() + 84)
  GROUP BY item_bigint_key
) p ON i.item_bigint_key = p.item_bigint_key

LEFT JOIN (
  -- On-Hand: latest snapshot per item
  SELECT item_bigint_key,
    on_hand_quantity,
    on_hand_cost,
    on_hand_days,
    CASE
      WHEN on_hand_days <= 30 THEN 'Fast Moving'
      WHEN on_hand_days <= 90 THEN 'Normal'
      WHEN on_hand_days <= 180 THEN 'Slow Moving'
      ELSE 'Excess / Obsolete'
    END AS on_hand_aging_bucket,
    snapshot_date
  FROM mke_supply_chain.prod_edw_views.inventory_days_on_hand
  WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM mke_supply_chain.prod_edw_views.inventory_days_on_hand)
) h ON i.item_bigint_key = h.item_bigint_key

LEFT JOIN (
  -- Receipts: last 30 days
  SELECT item_bigint_key,
    SUM(receipt_quantity) AS receipt_quantity_last_30d,
    COUNT(*) AS receipt_count
  FROM mke_supply_chain.prod_edw_views.purchase_receipt_line
  WHERE receipt_date >= CURRENT_DATE() - 30
  GROUP BY item_bigint_key
) r ON i.item_bigint_key = r.item_bigint_key

LEFT JOIN (
  -- Suppliers + Cost (primary supplier from dim_series_ext_vw)
  SELECT item_bigint_key,
    supplier_id,
    supplier_name,
    lead_time_days,
    applied_standard_cost,
    TO_JSON(MAP('direct_material', direct_material_cost, 'freight', freight_cost, 'import_fees', import_fees_cost, 'import_duty', import_duty_cost, 'labor', labor, 'overhead', overhead)) AS full_cost_breakdown_json,
    currency_code
  FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY item_bigint_key ORDER BY lead_time_days ASC) AS rn
    FROM mke_supply_chain.prod_edw_views.dim_series_ext_vw
  ) WHERE rn = 1
) s ON i.item_bigint_key = s.item_bigint_key

LEFT JOIN (
  -- Scrap + Rework YTD
  SELECT item_bigint_key,
    SUM(CASE WHEN movement_type = 'SCRAP' THEN quantity ELSE 0 END) AS scrap_quantity_ytd,
    SUM(CASE WHEN movement_type = 'SCRAP' THEN quantity * applied_standard_cost ELSE 0 END) AS scrap_cost_usd,
    SUM(CASE WHEN movement_type = 'REWORK' THEN quantity ELSE 0 END) AS rework_quantity_ytd
  FROM mke_supply_chain.prod_edw_views.movements
  WHERE movement_date >= DATE_TRUNC('YEAR', CURRENT_DATE())
  GROUP BY item_bigint_key
) q ON i.item_bigint_key = q.item_bigint_key

LEFT JOIN (
  -- Movements: shipments, transfers, etc. (last 7 days)
  SELECT item_bigint_key,
    COUNT(*) AS movement_count_last_7d
  FROM mke_supply_chain.prod_edw_views.movements
  WHERE movement_date >= CURRENT_DATE() - 7
  GROUP BY item_bigint_key
) m ON i.item_bigint_key = m.item_bigint_key

GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27;

-- Tag as certified
ALTER TABLE mke_supply_chain.po_management.item_360_gold
  SET TBLPROPERTIES ('certified' = 'true', 'grain' = 'item_bigint_key', 'owner_email' = 'supply_data@mke.com');
```

**Usage**: Dashboard / Genie queries start with item_360_gold:
```sql
-- Show all items with excess inventory and high scrap
SELECT item_id, item_name, on_hand_quantity, on_hand_cost_usd, scrap_quantity_ytd, abc_classification
FROM mke_supply_chain.po_management.item_360_gold
WHERE on_hand_aging_bucket = 'Excess / Obsolete'
  AND scrap_quantity_ytd > 100
ORDER BY on_hand_cost_usd DESC;
```

---

## 4. Lakeflow Connect: Gaps & Enrichment Only

The EDW already ingests Oracle Business Suites (source of purchase_orders, dim_series_ext_vw, items_scd1). **Lakeflow Connect is NOT for re-ingesting EDW sources** — it solves three gaps:

### Gap 1: External Geocoding Enrichment

**Problem**: inventory_organization has region/state/country but NO lat/long. Mapping to regional dashboards requires external geocoding.

**Solution**: Lakeflow Connect to a **SFTP or cloud-hosted geocoding service** (e.g., Google Cloud Geocoding API results pushed to SFTP), then join:

```sql
-- External geocoding table (landing zone)
-- Created by Lakeflow Connect SFTP connector
CREATE TABLE mke_supply_chain.po_management.geocoding_addresses AS
SELECT org_id, address_line, city, state, country, latitude, longitude
FROM mke_supply_chain.po_management.geocoding_sftp_raw;

-- Enriched org dimension
CREATE OR REPLACE VIEW mke_supply_chain.po_management.inventory_org_geo AS
SELECT o.*, g.latitude, g.longitude
FROM mke_supply_chain.prod_edw_views.inventory_organization o
LEFT JOIN mke_supply_chain.po_management.geocoding_addresses g
  ON o.organization_id = g.org_id;
```

**Reference**: databricks-lakeflow-connect skill, [references/1-saas-connectors.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/1-saas-connectors.md).

### Gap 2: SaaS Enrichment (Workday, Salesforce, ServiceNow)

If Milwaukee uses **Workday for HR/Finance**, **Salesforce for CRM**, or **ServiceNow for supply-chain planning**:
- Lakeflow Connect pulls these via OAuth, lands in UC raw tables
- Join to supply chain facts: sales_order_line_transactions (Salesforce Opportunities) + demand (pipeline forecasts), purchase_orders + supplier info (ServiceNow catalog)
- Write joined results to sandbox_operations.po_management

**Example**: Salesforce Sales Cloud → demand enrichment
```json
{
  "name": "salesforce_opportunities_to_demand",
  "ingestion_definition": {
    "connection_name": "salesforce_oauth_u2m",
    "objects": [
      {
        "table": {
          "source_schema": "salesforce",
          "source_table": "Opportunity",
          "destination_catalog": "mke_supply_chain",
          "destination_schema": "po_management"
        }
      }
    ]
  }
}
```

**Reference**: databricks-lakeflow-connect skill, [references/1-saas-connectors.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/1-saas-connectors.md).

### Gap 3: CDC for Slowly-Changing Supplier Master

If supplier master changes frequently (lead times, cost, reliability), Lakeflow Connect **SQL Server or PostgreSQL CDC** can capture incremental changes:

```sql
-- CDC source (e.g., on-prem SQL Server with change tracking)
CREATE OR REPLACE TABLE mke_supply_chain.po_management.suppliers_cdc AS
SELECT supplier_id, supplier_name, lead_time_days, applied_standard_cost, _change_type, _change_timestamp
FROM (
  SELECT * FROM STREAM(
    -- Lakeflow Connect CDC pipeline output
    mke_supply_chain.po_management.suppliers_cdc_raw
  )
)
WHERE _change_type IN ('insert', 'update');
```

**Boundary**: Lakeflow Connect is the **managed pull layer**. Do NOT use it for pushing data back to Oracle — that path is a separate, typed, auditable action layer (future).

**Reference**: databricks-lakeflow-connect skill, [references/2-database-connectors.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/2-database-connectors.md), [references/4-ingestion-decision-tree.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/4-ingestion-decision-tree.md).

---

## 5. Geography: Mappable Now vs. Geocode Gap

### What's Mappable Today

- **Region / State / Country** — in inventory_organization table, can roll up to regional dashboards (e.g., "on-hand by region," "planned receipt by state")
- **Country-of-origin (COO)** — in items_scd1, enables "sourcing footprint" analysis; COO codes are unnormalized (US/USA, CN/CHN), requiring a lookup table

**Example**: Regional on-hand summary
```sql
SELECT o.region, o.state, o.country,
  SUM(h.on_hand_quantity) AS qty,
  SUM(h.on_hand_cost) AS cost_usd
FROM mke_supply_chain.prod_edw_views.inventory_organization o
JOIN mke_supply_chain.prod_edw_views.inventory_days_on_hand h ON o.organization_id = h.inventory_organization_id
GROUP BY o.region, o.state, o.country;
```

### The Geocode Gap: Addresses → Lat/Long

**Problem**: inventory_organization has street addresses but no lat/long. Mapping networks (e.g., shipment heatmaps, "closest warehouse") requires geocoding.

**Solution**: Lakeflow Connect SFTP to external geocoding service, join, write to sandbox:

```sql
-- Step 1: Create the geocoding landing zone (via Lakeflow Connect)
CREATE TABLE mke_supply_chain.po_management.org_addresses_geocoded (
  organization_id INT,
  address_line_1 STRING,
  city STRING,
  state STRING,
  country STRING,
  latitude DOUBLE,
  longitude DOUBLE,
  geocode_timestamp TIMESTAMP
);

-- Step 2: Join to supply-chain facts
CREATE OR REPLACE VIEW mke_supply_chain.po_management.inventory_network_geo AS
SELECT 
  o.organization_id,
  o.organization_name,
  o.region,
  g.latitude,
  g.longitude,
  SUM(h.on_hand_quantity) AS on_hand_qty,
  SUM(h.on_hand_cost) AS on_hand_cost_usd
FROM mke_supply_chain.prod_edw_views.inventory_organization o
LEFT JOIN mke_supply_chain.po_management.org_addresses_geocoded g
  ON o.organization_id = g.organization_id
LEFT JOIN mke_supply_chain.prod_edw_views.inventory_days_on_hand h
  ON o.organization_id = h.inventory_organization_id
GROUP BY 1, 2, 3, 4, 5;

-- Step 3: Expose lat/long via AI/BI Dashboard map widget
-- (dashboard queries `inventory_network_geo`, specifies `latitude` + `longitude` columns as geo)
```

### Country-of-Origin (COO) Normalization

COO codes are inconsistent (US/USA, CN/CHN, etc.). Create a lookup:

```sql
CREATE TABLE mke_supply_chain.po_management.coo_lookup (
  raw_coo STRING,
  coo_normalized STRING,
  coo_name STRING
);

INSERT INTO mke_supply_chain.po_management.coo_lookup VALUES
  ('US', 'US', 'United States'),
  ('USA', 'US', 'United States'),
  ('CN', 'CN', 'China'),
  ('CHN', 'CN', 'China'),
  ('MX', 'MX', 'Mexico'),
  ('MEX', 'MX', 'Mexico');

-- Use in supply-chain queries
SELECT c.coo_name, SUM(h.on_hand_cost) AS sourced_value_usd
FROM mke_supply_chain.prod_edw_views.items_scd1 i
JOIN mke_supply_chain.po_management.coo_lookup c ON i.country_of_origin = c.raw_coo
JOIN mke_supply_chain.prod_edw_views.inventory_days_on_hand h ON i.item_bigint_key = h.item_bigint_key
GROUP BY c.coo_name;
```

---

## 6. Deployment & Lifecycle: DABs + CI/CD

The complete landscape lives in code — metric views, derived tables, dashboards, apps, Lakebase state — all authored in **Declarative Automation Bundles (DABs)** and deployed via Git + GitHub Actions.

### Why DABs

- **Single source of truth**: databricks.yml (dev target) + databricks.yml-prod (prod) version-controlled
- **Repeatable promotion**: dev → staging → prod with parameter overrides (catalog name, refresh schedule)
- **Integrated CI/CD**: GitHub Actions validates bundle on every PR, deploys on merge to main
- **Resource permissions**: DABs declare GRANT statements (who can SELECT/MODIFY which table)

### Bundle Structure

```
mke_rsc_isaac/
├── databricks.yml                      # Dev target (default)
├── databricks.prod.yml                 # Prod target overrides
├── resources/
│   ├── catalogs/
│   │   └── mke_supply_chain.catalog.yml
│   ├── schemas/
│   │   ├── po_management.schema.yml
│   │   └── prod_edw_views.schema.yml
│   ├── tables/
│   │   ├── item_360_gold.table.yml
│   │   ├── actuals_weekly_summary.table.yml
│   │   └── …
│   ├── metric_views/
│   │   ├── inventory_metrics.metric_view.yml
│   │   ├── purchase_order_metrics.metric_view.yml
│   │   └── …
│   ├── pipelines/
│   │   ├── supply_daily_ingestion.pipeline.yml
│   │   ├── demand_daily_ingestion.pipeline.yml
│   │   └── po_management_derived.pipeline.yml
│   ├── jobs/
│   │   ├── daily_refresh_items_360.job.yml
│   │   └── weekly_financial_reconciliation.job.yml
│   ├── dashboards/
│   │   ├── supply_chain_overview.dashboard.yml
│   │   └── inventory_financials.dashboard.yml
│   ├── apps/
│   │   └── supply_chain_app.app.yml
│   └── grants/
│       ├── analyst_read_access.grant.yml
│       └── engineer_write_access.grant.yml
└── .github/workflows/
    ├── validate.yml                    # PR: validate bundle syntax
    └── deploy.yml                      # merge to main: deploy to prod
```

### Sample DAB Resource Files

**databricks.yml (dev target)**:
```yaml
bundle:
  name: mke_supply_chain
  target: dev

variables:
  catalog: "mke_supply_chain"
  schema_sandbox: "po_management"
  environment: "dev"
  warehouse_id: "dev-warehouse-id"

resources:
  # Catalog (created once, managed centrally)
  catalogs:
    main:
      name: ${var.catalog}

  # Schemas
  schemas:
    po_management:
      name: ${var.schema_sandbox}
      catalog_name: ${var.catalog}

  # Metric Views
  metric_views:
    inventory_metrics:
      name: inventory_metrics
      source_table_full_name: ${var.catalog}.prod_edw_views.inventory_days_on_hand
      yaml_definition: |
        version: 1.1
        dimensions:
          - name: Organization
            expr: inventory_organization_id
          - name: Snapshot Date
            expr: DATE_TRUNC('DAY', snapshot_date)
        measures:
          - name: On-Hand Quantity
            expr: SUM(on_hand_quantity)
          - name: On-Hand Cost USD
            expr: SUM(on_hand_cost)

  # Lakeflow Pipelines (ingestion)
  pipelines:
    supply_daily:
      name: supply_daily_incremental
      catalog: ${var.catalog}
      schema: ${var.schema_sandbox}
      continuous: false
      ingestion_definition:
        source: "oracle_ebs"  # via Lakeflow Connect for any SaaS/CDC sources
        target_schema: ${var.schema_sandbox}

  # Gold tables (SQL transforms)
  tables:
    item_360_gold:
      name: item_360_gold
      schema: ${var.schema_sandbox}
      sql_file: resources/tables/item_360_gold.sql

  # Jobs (scheduled pipelines + refreshes)
  jobs:
    daily_item_360_refresh:
      name: "Daily Item 360 Refresh"
      tasks:
        - task_key: refresh_gold
          sql_task:
            file: resources/jobs/refresh_item_360_gold.sql
            warehouse_id: ${var.warehouse_id}
      schedule:
        quartz_cron_expression: "0 2 * * *"  # 2 AM daily
        timezone_id: "America/Chicago"
        pause_status: "UNPAUSED"

  # Dashboards
  dashboards:
    supply_overview:
      name: "Supply Chain Overview"
      display_name: "Supply Chain Overview"
      dashboard_data: resources/dashboards/supply_chain_overview.json

  # Access Control
  grants:
    analyst_read:
      resources:
        - schema: ${var.schema_sandbox}
      grants:
        - principal: "mke_data_analysts"
          privileges: ["USE_SCHEMA", "SELECT"]
```

**databricks.prod.yml (prod overrides)**:
```yaml
bundle:
  target: prod

variable_overrides:
  environment: "prod"
  catalog: "mke_supply_chain_prod"
  schema_sandbox: "po_management"
  warehouse_id: "prod-warehouse-id"

resources:
  # Production-only: SLA-backed jobs
  jobs:
    daily_item_360_refresh:
      max_retries: 3
      timeout_seconds: 3600
      notification_settings:
        on_failure:
          - email_address: "supply_data@mke.com"
```

**Reference**: databricks-dabs skill, [references/bundle-structure.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-dabs/references/bundle-structure.md).

### CI/CD Workflow

**.github/workflows/validate.yml** (runs on every PR):
```yaml
name: Validate Bundle

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: databricks/setup-cli@v0
      - run: databricks bundle validate --profile mke-rsc --target dev
```

**.github/workflows/deploy.yml** (runs on merge to main):
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: databricks/setup-cli@v0
      - run: |
          databricks bundle validate --profile mke-rsc --target prod
          databricks bundle deploy --profile mke-rsc --target prod
```

---

## 7. Iceberg & Interop: External Engine Read

The complete landscape lives in Databricks, but external tools (Python scripts, Tableau, external analytics platforms) may need to read it.

### External Iceberg Read via UniForm

Configure **Iceberg UniForm** (formerly External Iceberg Reads) on Delta tables so external engines (Spark, Presto, Athena) read them directly:

```sql
-- Enable UniForm on a Delta table (one-time)
ALTER TABLE mke_supply_chain.po_management.actuals_weekly_summary
  SET TBLPROPERTIES ('delta.universalFormat.enabledFormats' = 'iceberg');

-- External engine (e.g., AWS Athena) reads the same table via Iceberg
-- SELECT * FROM mke_supply_chain.po_management.actuals_weekly_summary (Iceberg format)
```

**Reference**: databricks-iceberg skill.

### Python SDK for Automation

Use the **Databricks Python SDK** to automate metric view creation, table refreshes, or lineage queries:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile='mke-rsc')

# Query lineage: what tables feed into item_360_gold?
result = w.statement_execution.execute_statement(
    warehouse_id='prod-warehouse-id',
    statement="""
        SELECT source_table_full_name, target_table_full_name, event_date
        FROM system.access.table_lineage
        WHERE target_table_full_name = 'mke_supply_chain.po_management.item_360_gold'
        AND event_date >= current_date() - 7
    """
)
for row in result.result.data_array or []:
    print(row)

# Create a metric view programmatically
metric_yaml = """
version: 1.1
source: mke_supply_chain.prod_edw_views.inventory_days_on_hand
dimensions:
  - name: Organization
    expr: inventory_organization_id
measures:
  - name: On-Hand Quantity
    expr: SUM(on_hand_quantity)
"""

w.statement_execution.execute_statement(
    warehouse_id='prod-warehouse-id',
    statement=f"""
        CREATE OR REPLACE VIEW mke_supply_chain.po_management.inventory_metrics
        WITH METRICS
        LANGUAGE YAML
        AS $$
        {metric_yaml}
        $$
    """
)
```

**Reference**: databricks-core, databricks-python-sdk (available via skill).

---

## 8. Complete Landscape Table

Consolidated view of all domains, their key tables, conforming keys, financial columns, and UC readiness:

| Domain | Key Tables | Conforming Key | $ Column | In UC Catalog? | Gap |
|--------|------------|----------------|----------|---|---|
| **Supply Plan** | 20_supply_daily (13.4B rows, 366 snapshots), supply_plan_weekly | item_bigint_key, org_id, plan_week | plan_quantity × applied_standard_cost | Yes (prod_edw_views) | None; Lakeflow Connect for CDC if source changes frequently |
| **Demand** | 10_demand_daily (17.8B rows), dg5_customer (56 MKE customers) | item_bigint_key, customer_id, order_date | base_extended_amount (revenue) | Yes (prod_edw_views) | None; Lakeflow Connect for SaaS CRM enrichment (Salesforce) |
| **Inventory** | inventory_days_on_hand (2.73B rows), inventory_organization (126 orgs) | item_bigint_key, inventory_org_id, snapshot_date | on_hand_cost (semi-additive) | Yes (prod_edw_views) | Lat/long geocoding (external); COO normalization rule |
| **Receipts** | purchase_receipt_line | item_bigint_key, receipt_id, receipt_date | receipt_quantity × applied_standard_cost | Yes (prod_edw_views) | None |
| **Shipments** | shipments fact table (movements filtered) | item_bigint_key, shipment_id, ship_date | shipment_quantity × applied_standard_cost | Yes (prod_edw_views) | None |
| **Movements** | movements (27 types: receipt, shipment, transfer, scrap, rework, etc.) | item_bigint_key, movement_id, movement_date | quantity × applied_standard_cost | Yes (prod_edw_views) | None |
| **Items** | items_scd1 (300K items, ABC/PL/COO) | item_bigint_key | None (dimension) | Yes (prod_edw_views) | COO normalization |
| **Customers** | dg5_customer (56 orgs, 56 customers) | customer_id | None (dimension) | Yes (prod_edw_views) | None; enrichment via Lakeflow Connect (Salesforce) |
| **Suppliers** | dim_series_ext_vw (supplier/planner/lead-time/cost buildup) | supplier_id, item_bigint_key | applied_standard_cost (direct_material + freight + import_fees + import_duty + labor + overhead), currency_code | Yes (prod_edw_views) | CDC via Lakeflow Connect for supplier master changes |
| **Purchase Orders** | purchase_orders | po_id, item_bigint_key, po_date | usd_price, usd_line_amount (spend) | Yes (prod_edw_views) | None; consider Lakeflow Connect for supplier catalog (ServiceNow) |
| **Sales Orders** | sales_order_line_transactions | order_id, item_bigint_key, order_date | base_extended_amount (revenue), base_extended_cost (COGS via standard cost) | Yes (prod_edw_views) | None; Lakeflow Connect for SaaS CRM |
| **Scrap / Rework** | movements (filtered to SCRAP, REWORK) | item_bigint_key, movement_id | quantity × applied_standard_cost | Yes (prod_edw_views) | None |
| **Geography** | inventory_organization (region/state/country/addresses), items_scd1 (COO) | organization_id, item_bigint_key | None (dimension) | Yes (prod_edw_views) | Lat/long geocoding (external Lakeflow Connect); COO normalization |
| **Financial KPIs** | Derived: actuals_weekly_summary, plan_vs_actual, supply_exceptions, action_outcome_history | date, item_bigint_key, org_id | Various: on_hand_cost, plan_cost, actual_cost, variance $ | Yes (sandbox_operations.po_management) | None; Metric Views define KPI measures |

---

## 9. Caveats & Gotchas

### 1. Standard Cost ≠ GL COGS

The applied_standard_cost columns are from Oracle Business Suites **standard-cost tables**, not the General Ledger. Fit for supply-chain planning / inventory valuation. **Not GAAP-reported COGS.** Confirm with Finance before publishing as accounting numbers.

### 2. On-Hand Cost is Semi-Additive

`inventory_days_on_hand.on_hand_cost = on_hand_quantity × applied_standard_cost`. SUM across items/orgs/dates is valid; SUM across multiple snapshot dates is NOT (double-counts). **Metric Views enforce this grain** — define the measure once with proper aggregation.

### 3. COO Codes Need Normalization

Country-of-origin codes are unnormalized (US/USA, CN/CHN). Join to a lookup table; don't hand-normalize in queries.

### 4. 126 Inventory Organizations, NO Lat/Long

Mapping requires external geocoding (Lakeflow Connect + join). Regional/state rollups work today.

### 5. Lineage System Tables Require Explicit Grant

`system.access.table_lineage` exists but is hidden until you grant `SELECT` on `system.access` schema. Plan for grant in DAB or upfront.

### 6. Metric Views Need DBR 17.2+, Semantic Metadata Needs 17.3+

Older clusters cannot author metric views. Update cluster policies.

### 7. Iceberg UniForm is Delta+Iceberg, Not Migration

Enabling UniForm on a Delta table means external engines read the same table in Iceberg format. No migration, no separate copy. Optional.

### 8. Lakeflow Connect is Pull-Only, Triggered

No continuous mode, no push-back to Oracle. Triggered pipelines only (on-demand or via Jobs schedule).

### 9. Sandbox Write Boundary is Strict

All project writes → `sandbox_operations.po_management` or Lakebase OLTP. No writes to prod_edw or prod_operations. This is enforced via IAM grants.

### 10. Loss Figures Are Derived, Not Raw

$1.68B on-hand inventory value is derived (SUM on_hand_cost across all items/orgs/latest snapshot). ~$4-5B overdue POs (deduped from $10.8B raw) requires date logic + reconciliation rules. Document the derivation in table properties or a Lakebase comment.

---

## Implementation Roadmap

### Phase 1: UC Foundation (1-2 weeks)
- Create `mke_supply_chain` catalog
- Grant read on prod_edw_views, write on sandbox_operations.po_management
- Enable system.access lineage (GRANT SELECT on system.access)
- Tag prod tables as certified

### Phase 2: Metric Views (2-3 weeks)
- Define 6 metric views (inventory, PO, supply plan, demand, sales, scrap)
- Test queries with MEASURE() syntax
- Publish in Genie + dashboards

### Phase 3: Derived Gold Layer (2-3 weeks)
- Author item_360_gold conformed view
- Build actuals_weekly_summary, plan_vs_actual fact tables
- Create supply_exceptions / action_outcome_history tables

### Phase 4: Lakeflow Connect (1-2 weeks, optional)
- Set up SFTP connector for geocoding enrichment
- (If needed) Add Salesforce / ServiceNow connectors

### Phase 5: DABs + CI/CD (2-3 weeks)
- Version-control metric views, gold tables, dashboards in DABs
- Set up GitHub Actions for validate/deploy
- Deploy to dev, then prod

### Phase 6: Documentation + Training (1-2 weeks)
- Document item_360_gold, metric views, KPI definitions
- Train analysts on querying metric views (MEASURE() syntax, grain)
- Publish lineage/audit queries as templates

---

## Conclusion

The **complete landscape** is the union of:
1. **Unity Catalog** as the single lineage + permission + audit backbone
2. **Metric Views** for governed financial KPI definitions (one source of truth)
3. **item_360_gold** as the conformed item view (demand + supply + on-hand + suppliers + costs)
4. **Lakeflow Connect** for gaps (geocoding, SaaS enrichment, CDC) — not re-ingesting EDW
5. **Geography** today: region/state/country/COO; future: lat/long via geocoding
6. **DABs + CI/CD** for repeatable, auditable promotion (dev → prod)
7. **Iceberg + SDK** for external-engine read and automation

This delivers **one governed place** where data engineers, analysts, and apps see the same supply-chain data, financials, and lineage — eliminating silos and enabling both planning and execution.

---

## References

- **databricks-unity-catalog** skill: [references/1-access-control.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-unity-catalog/references/1-access-control.md), [references/5-system-tables.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-unity-catalog/references/5-system-tables.md)
- **databricks-metric-views** skill: [references/yaml-reference.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-metric-views/references/yaml-reference.md), [references/patterns.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-metric-views/references/patterns.md)
- **databricks-lakeflow-connect** skill: [references/1-saas-connectors.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/1-saas-connectors.md), [references/2-database-connectors.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/2-database-connectors.md), [references/4-ingestion-decision-tree.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-lakeflow-connect/references/4-ingestion-decision-tree.md)
- **databricks-dabs** skill: [references/bundle-structure.md](file:///Users/brijendra.raghuwanshi/.claude/plugins/cache/claude-plugins-official/databricks/0.2.12/skills/databricks-dabs/references/bundle-structure.md)
