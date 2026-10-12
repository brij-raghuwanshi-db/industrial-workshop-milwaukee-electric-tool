# Session Log — MKE Supply-Chain Data Understanding (full record, as-is)

**Workspace:** `mke-rsc` (adb-4482605715640778) · **Date:** 2026-08-30 · **Mode:** READ-ONLY against
`prod_edw`/`prod_operations`; all outputs written to the local filesystem only (this folder). This file is a
faithful, chronological account of the whole session for export alongside the full chat transcript.

**Totals produced:** 53 markdown files, ~16,040 lines. 5 profiling findings + 39 data-story/scenario files +
5 solution-architecture files + 4 top-level (README, recipe, table map, synthesis) + this log.
**Subagents launched:** ~30 (5 profiling, ~18 scenario/story tracers, 4 solution-architecture, +retries).

---

## Ground rules honored throughout
- `prod_edw` + `prod_operations` = **READ-ONLY** (SELECT/DESCRIBE/SHOW only). No prod writes, ever.
- All derived/analytical writes target `sandbox_operations.po_management`; transactional state → Lakebase.
- Profile `mke-rsc`, default warehouse `7bd33a82f4e92206`; queries via
  `databricks experimental aitools tools query "<SQL>" --profile mke-rsc`.
- Skills used: `mke-supply-chain-fde` (operating pattern) + `databricks-core` and product skills
  (pipelines, jobs, metric-views, unity-catalog, dbsql, lakebase, apps, app-design, aibi-dashboards,
  data-discovery, genie-agents, agent-bricks, ai-functions, ml-training, mlflow-evaluation,
  model-serving, vector-search, lakeflow-connect, dabs, iceberg, python-sdk).
- Method: **query the data, don't assume**; label evidence; record every gotcha; anchor scenarios on
  IDs *discovered by query*, not picked at random.

---

## PHASE 1 — Data understanding (profiling)

**User ask:** go to the workspace, actually query the tables behind `customer_requirements/` (P1–P4),
build understanding of the underlying datasets; organize findings by P1/P2/P3/P4; note tables spanning
multiple priorities and any tables not found; write everything to files; use subagents; use skills.

**What I did:**
1. Loaded `mke-supply-chain-fde` + read all three requirement docs (`01_Requirements.md`,
   `Actuals_Supply_Plan_Requirements.md`, `Red_Keychain_Supply_Planning_Requirements.md`) + the
   project-scope reference (P1–P4 map).
2. Loaded `databricks-core`; verified auth (`mke-rsc` valid), found the warehouse, confirmed the three
   guardrail catalogs exist. Ran a sanity query on `20_supply_daily`: **13.45B rows, 366 daily snapshots
   (20250628→20260829)** — resolving open-item O10 (180-day backfill available).
3. Built the folder + a shared `_recipe.md` (exact connection + profiling conventions + naming gotcha for
   digit-leading tables) so every subagent worked identically and read-only.
4. Ran an existence sweep across `prod_edw` schemas; confirmed plan names (`20 Global Supply Plan`,
   `20 Mexico Supply Plan` both present) and located `receiving_receipt_transactions`.
5. **Dispatched 5 parallel profiling subagents** (clusters A–E), each writing to `subagent_findings/`:
   - **A** — `20_supply_daily` + `supply_and_demand_plans_scd1` (plan snapshot).
   - **B** — actuals sources: receipts, `sales_order_line_transactions`, `inventory_days_on_hand`,
     `purchase_order_delivery` (deprecated), `purchase_orders`.
   - **C** — shared dims: `items_scd1`, `date_scd1`, `inventory_organization_scd1`, `dim_series_ext_vw`.
   - **D** — demand: `10_demand_daily`, `dg5_customer_scd1`, `expansion_dims/loads`.
   - **E** — supporting/root-cause: `inventory_material_transaction`, `customer_shipments`,
     `order_line_fulfillment_accumulating_snapshot`, `inventory_on_hand_temporal`.
6. Wrote `00_table_priority_map.md` (every table → priorities), `README.md`, and `SYNTHESIS.md`
   (consolidated P1/P2/P3/P4 understanding).

**Key Phase-1 findings (verified):**
- `20_supply_daily`: within a snapshot, `date_key` buckets are **weekly, Monday-aligned, ~111 weeks
  forward** (NOT daily, NOT 55 years — corrected subagent A's miscalc with a direct query). True grain =
  plan × date_key × product × org × series × order_type.
- **Item "Status 20" = `item_status='PurchPlan'`** (8,716 of 299,966 items); `item_status_description`
  is truncated in the data. Resolves requirements open-item #1.
- Orgs **2012 Olive Branch** + **2120 Mexico** confirmed.
- **`receiving_receipt_transactions` uses raw Oracle ids and has NO item column** → crosswalk needed
  (later superseded — see Phase 2 KEY_FINDING).
- `inventory_days_on_hand`: 2.73B rows, point-in-time, zero negatives. `inventory_material_transaction`
  = 27-type root-cause ledger.
- `10_demand_daily`: 17.8B rows; measure is **`planner_baseline`** (doc said `planner_baseline_forecast`);
  already carries `expansions_loadin/runrate/non_repeating_events`. `dg5_customer_scd1` = 56 mkedg5;
  `expansion_loads` populated (8.09M rows).
- **Nothing doc-named was missing**; two things mis-described; several richer than documented.
- Saved durable facts to memory (`mke-data-profiling-facts.md`).

---

## PHASE 2 — Data stories / scenarios (query-driven journeys)

**User ask (evolved across many messages):** walk the *data story / data flow*; take an ID that lives
across many tables and satisfies a real scenario, follow its journey and show what attributes come
along; do it for multiple scenarios; first tell what scenarios exist; narrate; tag whether each pointer
answers an end-user question (yes → what it shows / no → what it actually shows); cover positive AND
negative (good-for-business vs red-flag); unique/anti/hidden patterns; approve/reject/on-time/delayed +
"on track last week, not now"; received/not-received; all P1–P4 exceptions + handling; whatever wasn't
asked; group non-priority ones separately; too-much-variance; forecast-vs-actual; beyond 2012/Mexico;
weekly snapshots; Monday–Sunday rolling windows; latest evolving patterns; lineage; plant/warehouse +
persona; "type 18"; where-is-it/what-stage; quantity-split & multi-supplier; geography; common causes;
agentic-app record impact; losses; the search pain story.

**Method:** discovered a **hero item** by query — started from the hardest link (receipts), found they
have no item column, tested candidates across facts, learned `PurchPlan` items ≠ actively-shipping items,
and anchored on **item_bigint_key 3879620845706693458 = 48111850 "M18 XC5.0 BATTERY"** (richest
cross-table presence). Other scenarios discovered their own scenario-fit anchors.

**Files written (in `data_stories/`, 39):**
- Navigation: `INDEX.md`, `STORIES_CATALOG.md`, `STORIES_SYNTHESIS.md`, `PRIORITY_MAP.md`,
  `BEYOND_P1P4_scenarios.md`, `KEY_FINDING_receipt_source.md`.
- Core P1 journeys: `S0_hero_item_discovery`, `S1_receipt_attainment`, `S2_onhand_and_why`,
  `S3_shipment_attainment`.
- P2: `S5_stockout_priority`, `S6_dc_imbalance`, `E2_supply_exceptions` (all 18 types).
- P3/P4: `S7_demand_event_journey`, `S9_forecast_drift`, `E34_demand_exceptions`.
- Polarity/time/workflow: `G_positive_scenarios`, `R_received_notreceived`, `V_extreme_variance`,
  `T_status_transitions_workflow`, `C_recoverable_counterfactuals`, `RW_rolling_windows`.
- Pattern hunts: `P_hidden_patterns`, `AP_anti_patterns`, `X_uncovered_scenarios`, `EM_emergent_patterns`.
- Cross-cutting/traceability: `L_lineage`, `LG_logistics_delays`, `N_multiorg_weekly`,
  `O_location_persona`, `HOP_product_journey`, `STATE_pointintime_stage`, `QTY_status_breakdown`,
  `GEO_geography_data`.
- Finance & meta: `FIN_finance_data`, `LOSS_supply_chain_losses`, `CAUSES_common_root_causes`,
  `IMPACT_agentic_app`, `THE_SEARCH_PAIN_JOURNEY`.

**Standout verified findings (with real numbers):**
- **`prod_edw.fact.purchase_receipt_line`** discovered = the CLEAN receipt fact (2.72M rows, 69,871 items,
  EDW keys, received/accepted qty + dates) → **dissolves the raw-Oracle-id crosswalk blocker.**
- **S2:** M18 battery at Olive Branch — demand spike −32,088 in one day (8/27), transfer +87K arrived a day
  late; summing on-hand across 6 days gives 538,116 vs correct 83,254 (semi-additivity, 6.5× wrong).
- **S3:** 87%-null `shipped_quantity` (14.8% non-null at item grain) → must filter shipped/invoiced.
- **S5:** top "17.6M-unit breach" was a **$0.0134 carbide part at a plant** (~$235K, 58-day lead) →
  raw unit-miss over-ranks penny parts; weight by cost×ABC×org-role.
- **S6:** glove item 869K @ Olive Branch vs 393K @ Byhalia; 129 transfers/mo prove rebalance is real.
- **S7:** item match 4.8%→**98.7%** after dash-normalization (not a data crisis, a punctuation rule);
  event round-trips into `10_demand_daily`.
- **S9:** +184K-unit (+23,016%) baseline revision; `frozen_*` cols 100% NULL → use process_date deltas.
- **T:** week Oct-5 flipped PAB **151,929 (green) → −3,464 (red)** across snapshots; 227-day-overdue PO.
- **R:** 1.23M PO lines fully received; **356K past-due-not-received**; over-received +23M units.
- **V:** Inkzall marker forecast 269K vs shipped 4K; several A-items forecast 100K+ shipped 0.
- **P:** phantom demand 8.4M units; 69M-unit reversals; MOQ 41,667×; 919 A-items single-source China.
- **AP:** quantified errors — priority flip 70×, on-hand inflate 5.48×, fulfillment understate 6.7×.
- **EM:** demand +705,033% (NPD launch); past-due cluster 46.5K lines (90% TTI).
- **N:** non-2012 orgs material (1019 Grenada 199M units); clean weekly Mondays 6/6; branches = order-only.
- **O:** plants hold 79.5% of units (components), DCs 75% of $ (finished goods); 69% items no named planner.
- **HOP:** supplier→plant→transit→DC→customer reconstructable as QUANTITY flows; from→to works within an
  org not across; **no serial/lot** (no unit-level track-and-trace); outbound leg fully tracked (carrier/BOL).
- **STATE:** where/what-stage as-of a date (169.5K on-hand / 721 in-transit / 2,297 scheduled); time-lapse
  across snapshots = the temporal half of lineage.
- **QTY:** ordered→received→open split (PO + schedule lines); multi-supplier per item (49960060 = 6
  suppliers incl. Fastenal/SUS Cast; `allocation_percent`).
- **GEO:** region/state/country + COO present; **no lat/long** (needs geocode); COO codes unnormalized.
- **FIN:** money in `dim_series_ext_vw` (applied_standard_cost + buildup + currency), `on_hand_cost`,
  PO `usd_*`, sales revenue/COGS — standard-cost, **not GL**.
- **LOSS:** ~$1.68B on-hand value; ~$4–5B overdue PO (deduped from $10.8B raw). The losses query itself hit
  two documented traps live (series-key mismatch → $0; SCD2 2.3× inflation) — left as caveats, not faked.
- **IMPACT:** prod EDW architecturally unwritable (safe); adverse surface = external writeback + P3 daily
  publish + data-trap recommendations; rails = human gate + typed idempotent audited actions + certified
  metrics + read-only Genie.
- **THE_SEARCH_PAIN_JOURNEY:** 7-chapter first-person account — the data being *there* ≠ *usable*; every
  question re-pays the full understanding cost; each user re-walks it weekly.

**Corrections applied mid-phase (user-directed or self-caught):**
- Corrected A's "55-year horizon" → 111 weeks (my direct query authoritative).
- Corrected S7's "95% items missing" → dash-normalization artifact (98.7% match).
- Completed S5's enrichment the subagent left as TBD (supplier/planner/cost, real $ impact).
- Flagged C's illustrative anchors; flagged EM's incorrect "snapshot tables not available" note.
- Kept all index/synthesis files reconciled as new files landed (verified all-in-INDEX).

---

## PHASE 3 — Solution architecture (how Databricks removes the pain)

**User ask:** now that the pain is documented, show how the Databricks **medallion architecture** makes
things consumable; on the new architecture (analytical + transactional), which products and **AI products**
enable quick decisions and the complete landscape of data, items, financials; go through all skills; think
in detail; use subagents. **Correction mid-phase:** wherever Vector Search index was used, use **Lakebase
Search BM25** instead.

**What I did:** read the fit-for-purpose decision reference; dispatched **4 solution-architecture
subagents** (each loading the relevant product skills, mapping to *our specific* pains), one re-run after a
transient API error, and sent the BM25 correction to the AI agent mid-run. Wrote the capstone; linked from
the parent README.

**Files (in `solution_architecture/`, 5):**
- `00_CAPSTONE.md` — pain→platform thesis + one-screen pain→cure map + what we deliberately did NOT pick.
- `01_medallion_foundation.md` — governed consumption medallion over the read-only EDW: Bronze read-views
  (right source), Silver SDP (crosswalk, dash-norm, RECEIVE-only, SCD2-dedup, weekly grain, fail-loud
  expectations), Gold cost-enriched facts, **Metric Views** semantic layer; Jobs orchestration; UC governance.
- `02_analytical_transactional.md` — analytical read (AI/BI Lakeview + UC→Lakebase synced tables) +
  transactional write (Lakebase native: cases/events/locks/approvals/audit/idempotency); closed loop;
  Databricks App shell + human gate + persona routing.
- `03_ai_decision_products.md` — focused Genie Agents (per P1–P4, certified, evaluated), AI Functions,
  Agent Bricks KA, **Lakebase Search BM25 (Vector Search deferred, per user direction)**, ML+Serving
  only-when-justified, MLflow evaluation; strict deterministic-vs-AI split.
- `04_complete_landscape_financials.md` — UC as lineage/permission backbone (fixes the no-lineage gap via
  system tables), item-360 view, financial completeness via metric views (standard-cost-not-GL), Lakeflow
  Connect for gaps/enrichment + geocode path, DABs + CI/CD, Iceberg/SDK interop.

**Verified consistency:** no accidental prod-write language in any section; BM25-not-Vector honored;
guardrails intact. One build-time note flagged: the Silver crosswalk is a lookup join, not a `CAST`.

---

## Honest caveats carried across the whole session
- Standard-cost + order pricing, **not the GL** (no landed-cost / margin actuals).
- **No lat/long** (mapping needs geocode); COO codes need normalization (US/USA, CN/CHN).
- **No serial/lot** — traceability is quantity-by-node-by-day, not unit-level.
- `purchase_orders` is **SCD2** — dedupe to latest before summing (2.3× inflation otherwise).
- Semi-additive on-hand — never sum across dates; net inter-org transfer double-counts.
- SDP limits (one op/dataset, no pivot; MV no time-travel); federation pushdown must be plan-verified.
- `frozen_*` columns unpopulated; no SKU-supersession map (P2 #9–11 undetectable today).
- `system.access` lineage not accessible to the user as-is → needs grants.
- Some Phase-2 subagent outputs contained a few illustrative (non-live) anchors or minor slips; these are
  flagged inline in the respective files and in this log rather than silently corrected.

## Where to start reading
1. `README.md` (this folder) → the map.
2. `SYNTHESIS.md` → P1–P4 data understanding.
3. `data_stories/INDEX.md` → all 39 scenario/journey files; `PRIORITY_MAP.md` for P-tags; `THE_SEARCH_PAIN_JOURNEY.md` for the narrative.
4. `solution_architecture/00_CAPSTONE.md` → the platform answer.
