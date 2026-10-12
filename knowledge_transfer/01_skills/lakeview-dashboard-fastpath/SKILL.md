---
name: lakeview-dashboard-fastpath
description: >
  Ground-truth fast path for building a Databricks AI/BI (Lakeview) dashboard right the FIRST time.
  Use ALONGSIDE the databricks-aibi-dashboards skill (that skill has the full widget spec; this one
  encodes the hard-won build discipline + a symptom→fix register learned by shipping a real dashboard).
  Invoke whenever creating/editing a Lakeview dashboard via serialized JSON + the `databricks lakeview`
  CLI, or debugging empty/errored tiles ("No data", "Select fields to visualize", "Unable to render").
---

# Lakeview Dashboard Fast Path

Built after shipping `sandbox_operations.po_management.p1slice_plan_vs_actual`'s dashboard the hard way —
**five** avoidable corrections. This skill exists so the next one is ONE clean pass. It complements, does not
replace, `databricks-aibi-dashboards` (read that for the widget-version table and full JSON spec).

## The Iron Rule
> **Do not hand-invent widget JSON, and do not publish before running the exact concatenated dataset query
> via CLI.** Every mistake below came from breaking one of those two.

## The Second Rule — design each widget, don't stamp them (wear the developer + business-owner hat)
A code generator that stamps widgets from one template produces structurally-valid JSON that is
business-nonsense. Before each widget ask: **what question does it answer, and would a planner learn
anything from it as drawn?** Specific traps this catches (all hit on the real build):
- **A series named by a color MUST have its color pinned to that meaning.** Multi-series lines default to
  theme color-cycling → a line labeled "Red items" renders BLUE. Pin every multi-series color via
  `color.scale.mappings` keyed on `displayName` (off-plan→red, on-plan→green, etc.). Never leave it to cycle.
- **A legend that just restates the color is useless.** "red/yellow/green" teaches nothing. Encode the
  BUSINESS BAND: `On plan (≤15%)` / `Drifting (15–30%)` / `Off plan (>30%)` / `No actual` — the legend must
  teach the rule. Do this via a `status_label` derived column in the dataset (sort-prefixed `1 · / 2 · …`).
- **Color and label must never contradict.** Audit every chart: does the pinned color agree with the word?
- **A drill-down page needs a way to pick the ONE thing** (page-level single-select filter), not just global filters.
- **Don't ship a 2-chart page and call it a dashboard.** Each page should answer its use-case with enough
  views (KPIs + trend + breakdown + a "what's worst right now" list).
- **Audit before deploy:** enumerate every chart's `y.fields` vs its `color` mappings and confirm
  single-series has no color, multi-series has pinned meaningful color, and no label/color inversion.

## The 7-step loop (do in order, every time)
1. **Warehouse + schema.** `databricks warehouses list`; `discover-schema catalog.schema.table`.
2. **Copy a known-good widget structure** from `databricks-aibi-dashboards/references/4-examples.md` (or
   `lakeview get` on a working dashboard). Swap dataset/fields — don't author encodings from memory.
3. **Author the dataset SQL with ALL business logic as aliased columns** (see gotcha #3). Bare table name OR
   fully-qualified both work; fully-qualified removes ambiguity for a single-env slice.
4. **TEST the concatenated dataset query verbatim via CLI** — this is non-negotiable and catches the
   syntax/data errors that otherwise surface as broken tiles:
   ```bash
   Q=$(python3 -c "import json;print(''.join(json.load(open('dash.json'))['datasets'][0]['queryLines']))")
   DATABRICKS_WAREHOUSE_ID=<WH> databricks experimental aitools tools query "$Q" --profile <p>
   ```
   Expect the row count you designed for. If it errors, fix JSON, re-test — do NOT deploy.
5. **Deploy:** `lakeview create` (first time) → capture id. Thereafter `lakeview update <id>
   --dataset-catalog <c> --dataset-schema <s> ...` then `lakeview publish <id> --warehouse-id <WH>`.
   **Never re-`create` to update** (mints a new URL).
6. **Verify the deployed JSON** with `lakeview get <id>` — confirm query names, formats, filters landed.
7. **The human confirms the render.** CLI proves structure + data; only the browser proves the visual.
   State this explicitly; never claim "done" from CLI alone.

## Symptom → cause → fix register (the five, learned on the ground)

| Symptom (in browser) | Real cause | Fix |
|---|---|---|
| **Every tile "Select fields to visualize"** (dataset resolves, query returns rows) | widget query named anything but `main_query` | name EVERY data widget's query `"main_query"`; keep `queries[].name` == encodings `queryName` for filters |
| **Some counters "No data"**, others fine | widget expression wraps a function: `AVG(ABS(x))`, `SUM(CASE…)` — rejected. Only plain `SUM/AVG/COUNT/MIN/MAX/COUNT(DISTINCT)/DATE_TRUNC` on a **bare column** allowed | push ABS/CASE/ratios into the DATASET SELECT as aliased cols; counter aggregates the bare alias |
| **All tiles "Unable to render / Show error"** | dataset SQL is broken — usually a **missing comma** between `queryLines` (they join VERBATIM, no separator) | rewrite the whole queryLines block cleanly; re-run step 4. Each line ends with `, ` or ` ` |
| **No filter bar / filters only on canvas** | page-level filter widgets ≠ global filters | put filters on a `PAGE_TYPE_GLOBAL_FILTERS` page (listed FIRST in `pages[]`); field-based binding, `disaggregated:false` |
| **% shows as bare number** (e.g. 172.65) | value is 0–100, not 0–1 | `number-plain` + `"suffix":"%"` — NOT `number-percent` (that expects 0–1 → would show 17265%). Apply to BOTH the counter AND the table column |

## Field-name contract (the binding that must hold)
- `queries[].query.fields[].name` **==** `spec.encodings.<enc>.fieldName` (exact string, e.g. both `sum(x)`).
- Data widget query name = `main_query`. Filter query name = its own string, matched by `encodings.fields[].queryName`.
- `disaggregated`: `true` for pre-aggregated/raw rows (table, chart on pre-agg dataset); `false` for widgets that aggregate (counters, filters).

## Formatting cheatsheet
- Currency: `{"type":"number-currency","currencyCode":"USD","decimalPlaces":{"type":"exact","places":0}}` (add `"abbreviation":"compact"` for $3M-style).
- Percent on a 0–100 value: `{"type":"number-plain","decimalPlaces":{"type":"exact","places":1},"suffix":"%"}`.
- Plain thousands: `{"type":"number","decimalPlaces":{"type":"exact","places":0}}`.
- Counters take NO per-widget color (renders "unsupported") — color via `uiSettings.theme.fontColor`.
- Format the SAME metric identically in counter AND table (a % in one place must be a % everywhere).

## Guardrail carry-over (this project)
Read `prod_edw`/`prod_operations` only; dashboards read from `sandbox_operations.po_management`. If a
published dashboard is empty for OTHER viewers (not you the owner), it's a GRANT issue on the run-as identity
(`GRANT USE CATALOG/USE SCHEMA/SELECT`) — but if it's empty for YOU the owner, it's NEVER grants; use this
register instead.

## Template
`templates/dashboard_skeleton.json` — a minimal known-good serialized dashboard (1 dataset with a derived
column, 1 counter, 1 line chart, 1 bar w/ status color mappings, 1 table with %/$ formats, a global-filters
page). Copy it, swap the table/fields, run step 4, deploy. It embodies every fix above.
