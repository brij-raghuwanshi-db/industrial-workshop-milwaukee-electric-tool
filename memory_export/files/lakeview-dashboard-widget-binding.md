---
name: lakeview-dashboard-widget-binding
description: "Lakeview/AI-BI dashboard widgets need query name \"main_query\"; copy working JSON, don't hand-invent"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

When building a Databricks AI/BI (Lakeview) dashboard by authoring the serialized JSON: **every widget's
query must be named `"main_query"`** (`layout[].widget.queries[].name = "main_query"`). Naming it anything
else (e.g. `"q"`) makes the encodings fail to bind — the UI shows **"Select fields to visualize"** on every
tile even though the dataset resolves and the query returns rows. This is NOT a grant, data, catalog/schema,
or publish issue; those are the wrong things to chase.

**Why:** I hit exactly this on the MKE P1 dashboard (2026-08-31) — hand-wrote widget JSON with `name:"q"`,
every tile empty, and wasted cycles on grants + fully-qualified tables + republish before finding the real
cause by diffing against the skill's working example (`databricks-aibi-dashboards/references/4-examples.md`),
where all 10 data widgets use `main_query`.

**Second gotcha (same project, same day):** widget field expressions may ONLY be a plain aggregation of a
BARE column — `COUNT(x)`, `AVG(x)`, `MAX(x)`, `SUM(x)`, `MIN(x)`, `COUNT(DISTINCT x)`, `DATE_TRUNC('WEEK',x)`.
A wrapped expression like `AVG(ABS(x))`, `MAX(ABS(x))`, or `SUM(CASE WHEN ...)` is silently rejected → that
counter shows "No data" while a sibling `COUNT(bare)` counter works. Fix: push ABS/CASE/ratios into the
DATASET SELECT as aliased columns, then aggregate the bare alias in the widget. All business logic lives in
dataset SQL, never in widget expressions.

**How to apply:** Don't hand-invent Lakeview widget JSON. Start from a KNOWN-GOOD serialized dashboard
(the skill's `4-examples.md`, or `lakeview get` on a working dashboard) and copy its exact widget
query/encoding structure — then swap dataset/fields. Verify the field-name contract holds:
`queries[].query.fields[].name` == `spec.encodings.*.fieldName`, query name == `main_query`. Deploy with
`--dataset-catalog`/`--dataset-schema` flags (bare or fully-qualified table both work once binding is right),
then `update`+`publish` on the same ID. The CLI can only verify structure/data — the visual render must be
confirmed in the browser. See [[mke-workspace-dev-location]].

**A project skill now encodes all of this:** `.claude/skills/lakeview-dashboard-fastpath/` (SKILL.md + a
known-good `templates/dashboard_skeleton.json`). It has the 7-step loop, the symptom→cause→fix register (all
five gotchas: main_query, no-func-in-widget-expr, missing-comma-breaks-dataset, global-filters-page,
%-suffix-not-number-percent), and the field-name contract. For any future Lakeview dashboard: invoke that
skill + `databricks-aibi-dashboards`, copy the skeleton, swap fields, TEST the concatenated dataset query via
CLI, then create/update+publish. Don't relearn this from scratch.
