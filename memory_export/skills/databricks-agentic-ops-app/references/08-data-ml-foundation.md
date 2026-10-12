# 08 — Data & ML Foundation (what the app assumes underneath)

The app is the top of a stack. It reads governed **gold** tables and calls a **model endpoint**;
those are produced by a data + ML foundation you build (or that already exists). This file specifies
that foundation so the app has real data to serve. Each layer maps to a Databricks product skill.

## Layer 0 — Synthetic / source data (Volumes)

If there's no real source, generate a realistic dataset (skill: **synthetic-data-gen**). Pure Spark
(`spark.range` + `F.when` + broadcast joins + window functions — no driver loops / `.collect()` on
big tables). Write raw datasets as **parquet into a UC Volume** (`/Volumes/{catalog}/{schema}/raw_data/<dataset>/`),
one subdir per dataset — the SDP silver reads it via `read_files()` (no bronze pass-through).

Design the data to carry a **legible anomaly** — a single driver with visible symptoms, concentrated
in a recent time window, against a finite-capacity constraint — so the app's queue has an obvious
"red cluster" to act on. Representative raw tables: a record master (with geo lat/lng for the map, a
de-identified `summary_text`), an events/encounters history (18 months), open/closed gaps, daily
risk snapshots (with a free-text note column feeding `ai_classify`), an **intervention/outcome
history** (the training data — each historical action + its realized benefit/cost/hours), and a
weekly capacity table. Pin a deterministic **hero record** so the demo arc is repeatable. Use rolling
`NOW`-relative time anchors (`SURGE_ONSET = NOW − 3 weeks`, etc.) with a pin flag for recorded demos.

## Layer 1 — Medallion pipeline (silver → gold)

Skill: **pipelines** (Lakeflow Spark Declarative Pipelines) or **jobs**. Read the Volume via
`read_files()`, clean/conform to silver, then build the **gold** tables the app + Genie + dashboard
read:

- `gold_*_panel` — the current per-record position (classifying dims, `risk_score`, gap flags,
  `severity_weight`, `exposure_usd`, derived `risk_band`, geo, de-identified `summary_text`).
- `gold_open_*` — the actionable at-risk subset + `capacity_headroom_hours` + `candidate_provider_id`.
- `gold_*_outcomes` — per-historical-action outcomes (the model's training grain).
- `gold_*_recommendations` — the ranked action per record. **This can be produced by a pure-SQL
  heuristic in the pipeline** (rank actions by `benefit × unit_value − cost − capacity_penalty`) so
  the full app works end-to-end **with no ML at all**. The ML model (Layer 3) is an optional swap
  that overwrites the *same* table with learned scores — nothing downstream changes.
- Enrich with **AI functions** (skill: **ai-functions**): `ai_classify` over the note text → a
  `risk_signal_score` (0–1) column mirrored onto the panel row.

`risk_band` derivation is the app's single visual signal — e.g. `critical` (risk ≥ .75 with an open
priority gap), `elevated` (≥ .6), `watch` (≥ .4), else `stable`.

## Layer 2 — Governed metric view (one definition of the KPIs)

Skill: **metric-views**. Define ONE Unity Catalog metric view over `gold_*_panel` so the dashboard
tiles, Genie's headline answers, and the app's KPI cards all resolve to the *same* measures (numbers
match everywhere). Dimensions: the classifying dims + id. Measures (use `SUM(CASE WHEN …)` not
`MEASURE(x)/MEASURE(y)` so they're correct under any filter and safe on empty slices): `exposure`,
`open_gaps`, `record_count`, `critical_count`, `elevated_count`, `atrisk_count`, `avg_risk`.
Aggregated materialization, periodic refresh. **Renames here are breaking changes downstream** — the
dashboard/Genie/app reference measures by name.

## Layer 3 — The recommender model (optional ML swap)

Skill: **ml-training** + **model-serving**. A **regressor** predicting the *benefit* (e.g. risk
reduction) for a `(record situation, candidate action)` pair — trained on `gold_*_outcomes`
(XGBoost, Optuna ~10 trials, MLflow autolog), registered to UC (`{catalog}.{schema}.<recommender>`,
promote `@prod`).

- **Regression, not classification** — the app needs a *predicted benefit per action* to rank all
  options AND show the tradeoff (× unit_value − cost − capacity_penalty = net value), not a single
  best-action label.
- **Features** (reconstructable at scoring time): `action_type` (categorical, one-hot at inference),
  `risk_score`, recency (`days_since_*`), which gaps are open (boolean), `severity_weight`,
  `coordinator_hours` (the capacity-penalty input). Label: realized benefit. Carry `cost_usd` +
  `coordinator_hours` from history for the net-value math.
- **Two consumption modes:**
  1. **Batch** — score every open record's three candidate actions, apply the capacity penalty,
     overwrite `gold_*_recommendations` (JSONB ranking of all options). The Genie space + dashboard +
     the app's cached fallback read this table.
  2. **Real-time** — the app's `rank_actions`/`what_if` tools call the model's **serving endpoint**
     directly (`dataframe_records`, one row per candidate) for live scoring, with the batch table as
     fallback. Feature construction MUST match the training schema exactly.

## Layer 4 — Genie space (the `ask_data` brain)

Skill: **genie-agents**. Create a curated Genie space over the gold tables + the metric view. Make
it **self-sufficient**: a space `description`, a top `text_instruction` (WHAT HAPPENED · WHAT TO
HELP THE USER DO · TONE, honored every turn, with the baseline numbers + `risk_band` definitions +
an investigation flow), and `sample_questions` + matching `example_question_sqls` that walk the demo
arc in order (headline exposure → the cluster → the driver → the hero record → the recommendation).
Point headline answers at the metric view measures so Genie's numbers match the dashboard exactly.

## Layer 5 — AI/BI dashboard

Skill: **aibi-dashboards**. A Lakeview dashboard over the gold tables + metric view: KPI tiles
(exposure $, open items, at-risk count, critical count via `MEASURE(...)`), the risk trend, the
recommended-action mix. Embedded in the app's `/dashboard` page via SSO iframe. (Build/validate its
SQL via CLI before deploying; widgets have a specific JSON structure.)

## How the layers feed the app

| App feature | Reads |
|-------------|-------|
| Panel queue + KPI cards | `gold_*_panel` → Lakebase `record_position` mirror; metric view for tiles |
| `find_record` / `search_records` | `record_position` (+ FTS index) |
| `rank_actions` / `what_if` | model-serving endpoint (real-time) OR `gold_*_recommendations` mirror (fallback) |
| `search_providers` | `providers` mirror (Lakebase Search) |
| `ask_data` | Genie space over gold + metric view |
| Analytics charts | warehouse SQL over Delta gold |
| `/dashboard` | embedded AI/BI dashboard |
| `execute_action` | **writes** Lakebase `actions` (the only write) |
