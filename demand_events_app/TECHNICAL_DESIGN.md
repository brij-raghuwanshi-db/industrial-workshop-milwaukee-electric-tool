# Demand Events App — Technical Design & Data Contract

**Status:** Pre-build design (no code yet). Produced for review before development.
**Project priority:** P3 — Demand Events App (per `mke-supply-chain-fde`).
**Author stance:** Databricks FDE / solution architect. Every choice labelled with an evidence status.
**Sources:** `customer_requirements/01_Requirements.md` (formal), `demand_events_app/requirement_discussion.md` (business call), `demand_events_app/bulk insert_update…md` (bulk-write reference), live data profiling 2026-08-30 (`data_understanding/`), project skill `mke-supply-chain-fde`.

Evidence legend: **[V]** Validated against Milwaukee data · **[P]** Preferred-with-assumptions · **[PC]** Prototype choice · **[B]** Blocked pending evidence · **[R]** Rejected.

---

## 0. How to read this document

This is the "before development" package you asked for. It answers four questions:

1. **What are we actually building?** (§1 business framing, §2 goals)
2. **What data does it need, and what does it interact with?** (§4 read sources, §5 transactional state, §6 publication history)
3. **How does it stay modular — sharing the supply learnings without diluting them?** (§3 architecture, §13 modularization)
4. **What must be decided before we build?** (§7 the output-table guardrail collision, §16 open decisions)

The specifically-requested capability — **bulk edit on a category, written directly to Lakebase** — is §11.

---

## 1. Business framing (the pointers extracted from the call)

The formal requirements doc is accurate but flat. The call carries the *why*, which changes several design decisions. Extracted pointers:

### 1.1 What this app IS
- Replaces the **Excel "expansion" files** that collect **incremental demand** (above the statistical baseline) driven by intelligence from sales/marketing — e.g. "Home Depot adds this assortment to 100 more stores." **[V]** (call + doc)
- The forecast values **don't live anywhere else** — they originate as an Excel/email from sales or marketing; the demand team curates and submits them. **[V]**
- The reason this is the *first* app being built: **the Oracle integration already exists** and reads the output staging tables. "We're already in Oracle. We don't have to worry about integration" — historically the blocker at Milwaukee. **[V]** This is the crux of the output-table decision in §7.

### 1.2 What this app is explicitly NOT (scope guards)
- **NOT promo** — separate enterprise Salesforce/PwC project; we're a stakeholder, not the builder. **[V]**
- **NOT NPD (new product development)** — separate existing app. **[V]**
- **NOT the base statistical forecast** — that is built *in Oracle*, exported to Databricks ~6 AM daily. Getting out of Oracle for the base is "the hardest part" and is deliberately last. **[V]**
- **NOT store-level / regional granularity** — the forecast grain stops at **mkedg5** ("all the Ace Hardware," not a store in Ohio). One giant DC (Mississippi) today; regional is a *future* bridge, explicitly "cross that bridge later." Do **not** over-build regional now. **[V]**

### 1.3 The core semantic distinction (drives everything)
Two event natures, and the difference is about **forecast history**, not just labels:

| Nature | Old term | History behavior | Forecast behavior |
|---|---|---|---|
| **Non-repeating** | Expansion Load-In | **Pegged in history, EXCLUDED** from future statistical forecast | One-time volume (e.g. 40,000-unit load-in) placed on the start month |
| **Repeating** | Run Rate | **Retained in history, INCLUDED** so future statistical forecast learns it | Ongoing run-rate spread across months |

An event can be **both** (a load-in *and* a subsequent run-rate). **[V]**

### 1.4 Signals the formal doc under-states (and their design impact)
- **Incremental can be NEGATIVE.** Events also *reduce* the forecast (Oracle go-live push-pull pulled volume forward). `load_value` must accept negatives. **[V]** → schema + validation must allow signed quantities.
- **The killer feature = higher-level input + disaggregation.** Sales says "increase by **$1M** across **these 100 items × 6 customers**." Today that's thousands of Excel rows; only Oracle can input high and disaggregate down. Bringing this into the app is *the* win. Disaggregate against a measure (`planner_baseline`), MVP could even start 50/50 across two orgs then refine. **[V]** → §8.
- **Dollar input → unit output.** Planners want to type **$1M** (or a **% lift**) and have the app compute **units** (base measure is $; convert to units). Chrissy: "I still want to put units in, but I want it to calculate it for us." **[V]** → §8.
- **Static vs dynamic values.** When the underlying baseline changes later, do event values rebalance? **Decision: STATIC by default.** Automatic daily rebalance = "chaos." Rebalance is a **planner-pressed button** ("red disaggregate button") with a **recommendation of candidates**; never a silent cron. **[V]** → §8.4.
- **Remove a customer from an allocation** (the "plumbing" example): mechanism is **Status = Closed** at event / customer / item level → **output to Oracle becomes ZERO**, record retained. Not a physical delete. **[V]** → §9 lifecycle (adds a 4th state beyond the doc's three).
- **Submission acknowledgement is a real, named pain.** Taylor made an update and "didn't see her change the next day"; there have been "thought it submitted but it didn't" incidents. **"Did it get submitted successfully" is more important than "was it good for business."** **[V]** → acknowledgement is a first-class feature, not a nicety (§9.4, §10).
- **Day-over-day event delta is the reporting they actually want.** "Event was $15M day 1; planner adds $5M; show 'this event increases the forecast for these months by $5M.'" More useful than today's static Power BI. **[V]** → §6 publication history + §12 outcome view.
- **One-customer-per-file is today's biggest limitation.** 50 files for 50 customers during Oracle go-live, thousands of SKUs each. **Multi-customer per event** is core. **[V]**
- **% lift must be dynamic-capable but arrive as units.** Chrissy wants a % lift that recalculates if the base it's applied to changes — but the value passed to Oracle is still units. Reconcile with "static by default": the *stored, published* value is static units; a lift is one input mode, and re-applying it is a rebalance action. **[V]**
- **Who submits:** the **demand team** (4 named individuals), working from sales/marketing intelligence — not Home Depot/HQ directly. **[V]** All planners can see all events; edit gated by lock; **no approval workflow** (planner submit = ready to load). **[V]**

### 1.5 Platform decision from the call (conflicts with earlier assets)
- Business has chosen **React** for this build (over Streamlit), because they want "a really clean way to write SQL back and forth." The formal doc still says "Streamlit prototype." **[V]** call — but see §13/§16: this is a real decision to confirm, and it diverges from the existing Streamlit `data_apps` repo and our `databricks-streamlit-apps` skill. New repo + CI/CD from the start, but nothing wired to auto-publish until SME/QA validate. **[V]**

---

## 2. Goals that can be accomplished (business outcomes, not features)

Framed as outcomes so we can judge "done" by acceptance, not deployment.

| # | Goal | Outcome measure | Priority |
|---|---|---|---|
| G1 | Retire the 50-file, one-customer-per-file Excel process | One event carries **multiple customers**; file count → 0 | MVP |
| G2 | Enter high, disaggregate down | Planner enters **$/units/% at mkedg0–4**; app outputs mkedg5 × item × month | MVP-core |
| G3 | Input in **$ or % lift**, publish in **units** | App computes units from a chosen base measure | MVP-core |
| G4 | Preserve **repeating vs non-repeating** so forecast attribution is clean | Non-repeating excluded from history, repeating included; correct target-table classification | MVP |
| G5 | Kill the "thought it submitted but it didn't" failure | Every publish returns a **durable acknowledgement**; planner sees today's published state and its delta | MVP |
| G6 | Full **audit + change log + concurrent-edit awareness** | Who changed what value, when, before/after, at item/month/field grain; notify on same-SKU recent edit | MVP |
| G7 | **Day-over-day event delta** reporting | "This event adds $X to months M1–M3 vs yesterday" | Fast-follow |
| G8 | **Bulk category edits** written safely | Status/close/value/lift/rebalance across a selected category via staged set-based write | MVP (see §11) |
| G9 | **Event locking** for concurrent planners | One editor at a time; view-only for others; lock releases on save/close/timeout | MVP |
| G10 | Attribution reporting | "Of our 10% growth, 3% is this event" — segment incremental by event | Fast-follow |
| G11 | Candidate-based **rebalance / double-dip management** | Planner-triggered rebalance with recommended candidates; close over-scanned customers to zero | Fast-follow |
| G12 | Produce the Oracle-ready output in the expansion shape | Publish to `sandbox_operations.po_management` in the `expansion_dims/loads` contract; DW team's integration consumes it — **no new integration built by us** | MVP |

**Non-goals (guard against scope creep):** base forecast authoring, promo, NPD, regional/store granularity, an always-on ML endpoint, a general agent. Forecasting/ML is *not* required for P3 — this is transactional/stateful work.

---

## 3. Architecture (modularized, sharing supply learnings)

The supply work (P1/P2) is **read/analytical**: gold tables → AI/BI dashboard + Genie + a read-mostly app. The Demand Events App is **transactional / stateful / write-heavy** — a fundamentally different interaction pattern (the skill calls this out explicitly). So it is a **separate module** that **reuses the patterns, not the assets**.

```
AppKit (React UI + typed Node backend, plugin-based)  →  { Analytics plugin → SQL Warehouse : prod_edw dims/facts (READ-ONLY, incl. expansion_* as SOURCE ONLY)
          (owns identity, policy, validation,             Lakebase plugin  → Postgres      : all app/transactional state (read+write)
           transactions, every read/write/action)         sandbox_operations.po_management  : Delta — the ONLY write target (strict) }

    prod_edw  = READ-ONLY, always.   Oracle-inbound staging = external DW team's job, reads FROM our sandbox output; never written by this app.
```

- **Stack: Databricks AppKit** (`github.com/databricks/appkit`) — TypeScript SDK on **Node.js + React**, plugin-based. Confirmed by the business. It gives us, out-of-the-box and aligned to our needs:
  - **Analytics plugin** → SQL against the SQL Warehouse (read `prod_edw` dims/measures) with caching, parameterization, and generated types.
  - **Lakebase plugin** → OLTP against Lakebase (Prisma/Drizzle ORM) — our transactional state (drafts, cells, locks, audit, bulk batches).
  - **Genie plugin** (optional, later) and **Files plugin** (UC Volumes) — not needed for MVP.
  - **OAuth / on-behalf-of user** token management — matches the identity discipline the skill requires.
  This replaces hand-building a bespoke React + FastAPI BFF: AppKit *is* the React front end + a typed Node backend with the platform clients already wired. One app, one canonical source dir, one framework. **[V]**
- **Backend shape (within AppKit):** thin `route → domain service → platform plugin`. No microservices, GraphQL, or event bus. Every route independently authorizes — never trust frontend/button state. **[P]**
- **Reads:** SQL Warehouse over `prod_edw` (dims/measures) — **read-only**, labelled as such. **[V]**
- **Transactional state:** **Lakebase** (managed Postgres) — drafts, cells, locks, audit, bulk batches, acknowledgements. **[V]**
- **Analytical history (OUTPUT we write, not a source we read):** **Delta** in `sandbox_operations.po_management`, demand-namespaced — published event snapshots, publish deltas, audit projections, QA reconciliation. This is the **only** Delta write target (strict, §7). Historical *reads* come from `prod_edw` (§4); the "history" here is what the app produces. **[V]**
- **Oracle-inbound publication:** **out of scope for this app.** We write only to `sandbox_operations.po_management`; the DW team's separately-approved integration reads that and handles the Oracle hop (§7). This app never writes `prod_edw`. **[V]**

### What is SHARED from supply (learning, not tables)
- The operating pattern & guardrails (`mke-supply-chain-fde`).
- The Lakebase transactional model: `action_request` / `action_audit_event`, idempotency keys, record-version optimistic concurrency, outbox pattern.
- The **bulk stage → validate → dedupe → one set-based MERGE/upsert** pattern (from the bulk-write reference).
- Provenance markers, required UI states, deployment gates (probe → walking skeleton → vertical slice).
- Auth/identity/resource-wiring discipline for Databricks Apps.

### What is OWNED (kept separate, so we don't dilute)
- Its **own repo** (new, AppKit/React/TypeScript) — not the Streamlit `data_apps` repo. **[V]**
- Its **own Lakebase database/schema** (`demand_events`) — never mixed with supply Lakebase entities.
- Its **own Delta namespace** — `sandbox_operations.po_management.demand_events_*`, kept away from supply's `p1slice_*` / `sdp_*`.
- Its **own domain services** (events, disaggregation, publication) — no shared code with supply exception logic.

---

## 4. Data the app READS (sources — `prod_edw`, READ-ONLY)

Profiled **live at source this session** (`DATA_PROFILE.md`) on `--profile mke-rsc` / warehouse `7bd33a82f4e92206`, plus prior profiling 2026-08-30. Live facts below **supersede** both the requirements doc and earlier assumptions. Re-validate at build start (§16).

| Source | What we use it for | Live-verified facts | Evidence |
|---|---|---|---|
| `prod_edw.dimension.dg5_customer_scd1` | Customer multi-select + 6-level hierarchy (mkedg0→mkedg5); disaggregation grouping | Full hierarchy real & populated (`3RD PARTY→DOM→THD→…→HOME DEPOT`; `…→HDW→FARM→RURAL_KING`). Output grain = mkedg5. **`mkedg0` has case variants** (`3RD PARTY` vs `3rd Party`) → **case-normalize when grouping**. 53 customers appear in events; ~56 in the dim | **[V]** live |
| `prod_edw.dimension.items_scd1` | Item validation | **~1 row per item** (300,013 rows / 300,007 distinct `item_id`) → status is **item-level, not org-level**. `item_status='PurchPlan'` = 8,727 items. **⚠️ See validation finding below — PurchPlan flags 100% of a real event.** | **[V]** live |
| `prod_edw.fact.10_demand_daily` | Disaggregation base measure + $/%-lift base | **`planner_baseline`** confirmed (doc's `planner_baseline_forecast` is wrong) + `working_final_forecast`. `_amount` columns = **dollar** counterparts → back the $-input path. Fact already carries `expansions_loadin` / `expansions_runrate` / `non_repeating_events` (+ `_by_org`, `_override`, `frozen_*`) | **[V]** live |
| `prod_edw.dimension.inventory_organization_scd1` | Org auto-populate / override | Column is **`organization_code`** (NOT `org_code`). **2012 = Olive Branch** (US default); **2120 = Mexico** (THD MEX). Also `organization_name`, `designated_org_code`, `forecasted_organization`, `ship_from_org`. Orgs not interchangeable | **[V]** live |
| `prod_edw.staging_flat_files.expansion_loads` / `expansion_dims` | **SOURCE only** — (a) schema ref, (b) **pull in existing events to adjust**, (c) reconcile | `expansion_loads` **8,088,876 rows · 1,462 events · 53 customers · 15,170 items**. dims schema = 10 cols, loads = 11 cols, both match doc. `file_name` = `"EXP001442 TOL THD…"` (EXP ID + name); `expansion_name` = clean name. **item_number dashed** (`2438-20`) → join `REPLACE(item_number,'-','')` (100% match on traced event). Read-only, never our write target (§7) | **[V]** live |

### ⚠️ Validation finding (changes the design — resolves open-item #1 with evidence)
Traced a real Home Depot event **`EXP001442`** (TOL THD 2026 HDC): all **24/24 items matched** the item master via dash-normalization, but statuses are **ShipSO (22), DiscExtrnl (2), PurchPlan (0)**. So the requirements' primary rule **`item_status='PurchPlan'` would flag 100% of a legitimate event.** Events carry **sellable/shippable** SKUs (`ShipSO`), not purchase-planning SKUs. Design impact:
- Validation stays **non-blocking warning** (per §4.2) — nothing breaks — but the **criterion must be reconfirmed** with analytics engineering before hardcoding (§16.3, now the top risk). Likely correct set ≠ PurchPlan for events.
- `event_item.validation_flag` must be **rule-version-tagged** (store which criterion produced the flag), so a criterion change re-flags cleanly.

### Data-quality findings on the value grid (change ingest + schema)
- **`load_value` allows negatives** — 6,883 negative rows (min −8,640); **~88% zero, ~4% blank**. → schema stores **signed** values; store **only non-zero cells** (sparse).
- **`variable` (month) has MIXED formats** — 8,080,739 ISO timestamps + **8,137 Excel serial integers** (`45748`). → **normalize-on-read DQ step** (`1899-12-30 + n days` → first-of-month) before any use.
- **An event is MULTI-TRANCHE** — `EXP001442` has 4 `expansion_dims` rows (`file_index` 0–3, stores 22/42/9/28) and value rows repeat per tranche; the grid is **not pre-aggregated**. → import must **aggregate tranches** to the mkedg5 × item × month output grain and decide preserve-vs-collapse (§16.7).
- **Existing events are single-customer** — confirms the #1 pain; multi-customer per event is the core enhancement (§2 G1), verified.

**Item bulk-import gotcha:** planners paste dashed SKUs; dash-normalize on read/write. Validation warning is non-blocking. **[V]**

---

## 5. Data the app WRITES as transactional state (Lakebase — `demand_events` schema)

This is the app's operational memory: fast point reads/writes, concurrent editing, drafts, locks, audit. **All demand-namespaced; never mixed with supply.** Entity sketch (columns illustrative, finalize in build):

**Event core**
- `event` — `exp_id` (auto = max+1, immutable), `event_name`, `event_type` {non_repeating, repeating, both}, `status` {IN_PROGRESS, ACTIVE, DEACTIVATED, **CLOSED**}, `organization_code` (default 2012 Olive Branch; 2120 Mexico), `record_version`, `created_by/at`, `last_modified_by/at`. *(Renamed to `organization_code` — the live dim column is `organization_code`, not `org_code`.)*
- `event_header` — **one row per store-tranche** (`tranche_index`, mirrors source `file_index`): `number_of_stores`, `ship_date`, `ship_month` (derived), `set_month`, plus header-level Forecast Builder assumptions. *(Multi-row because the profile showed a real event = 4 tranches with different store counts 22/42/9/28; a single header row would lose that.)*
- `event_tag` — multi-select tags (categorization = a **bulk-edit category**, §11).
- `event_comment` — freeform collaboration notes.

**Selection & grain**
- `event_customer` — event × selected customer(s) + the **hierarchy input level** chosen (mkedg0–5); per-customer `status` (supports close-one-customer).
- `event_item` — event × item, `validation_flag` + **`validation_rule_version`** (which criterion produced the flag), per-item Forecast Builder overrides. *(Rule-version added because the profile proved the `PurchPlan` criterion flags 100% of a valid event — when the criterion is corrected, versioning lets us re-flag cleanly rather than silently mismatch.)*
- `event_cell` — **event × item × mkedg5 × month → value** (units, **signed**). Disaggregated output grain + manual-override store. `source` {DIRECT, BUILDER, DISAGGREGATED, OVERRIDE} for provenance. *(Store **only non-zero cells** — profile showed ~88% zero / ~4% blank; a dense grid is wasteful. **Signed** because 6,883 real rows are negative — reduce-the-forecast events.)*

**Concurrency, audit, workflow**
- `event_lock` — `exp_id`, `locked_by`, `locked_at`, `expires_at` (timeout release).
- `event_audit_event` — granular who/what/when/before/after at **item/month/field** grain (G6).
- `disaggregation_run` — a static snapshot of the base measure used, method, scope, candidates (so a rebalance is reproducible and never silently drifts, §8.4).
- `saved_search`, `notification_delivery`.

**Bulk edit (the requested capability, §11)**
- `bulk_edit_batch` — `batch_id`, `request_id`/idempotency key, `category_type` {EVENT, CUSTOMER, TAG, ITEM_FAMILY, STATUS, ORG}, `category_selector`, `operation` {SET_STATUS, CLOSE, ADJUST_VALUE, APPLY_LIFT, REBALANCE}, `requested_by/at`, `status`.
- `bulk_edit_stage` — the staged rows for one batch (validated, deduped) before the single set-based apply.

**Publication acknowledgement (G5)**
- `publication_ack` / `integration_result` — per publish run: rows published, hash, run_id, external correlation id, SUCCEEDED/FAILED/VERIFICATION_PENDING, timestamp. This is what the planner sees to trust the submit.

**Why Lakebase, not Delta, for these:** concurrent human edits, locks, drafts, and approvals are OLTP — Delta is not a concurrent-edit approval DB (fit-for-purpose). A UC-exposed Lakebase table is read-only via UC; writes go through Postgres. **[V]**

---

## 6. Data the app WRITES as analytical history (Delta — `sandbox_operations.po_management`, demand-namespaced)

Large-scale history, snapshots, and the day-over-day analysis. Fed from Lakebase via Change Data Feed → Delta (the analytical loop).

- `demand_events_published` — the **Active-event output** (expansion_dims/loads shape) as published each day; append-only snapshots keyed by publish date → enables G7/G10.
- `demand_events_publish_history` — day-over-day deltas ("+$5M to months M1–M3").
- `demand_events_audit_projection` — Lakebase audit CDF → Delta for reporting.
- `demand_events_disaggregation_audit` — every rebalance run + candidates + base snapshot.
- `demand_events_qa_reconciliation` — publish-vs-source tie-outs, validation summary.
- `demand_events_seed_normalized` — the cleaned import of existing `expansion_*` events used to hydrate Lakebase. *(New, forced by the profile: source needs a normalize pass before it's usable — Excel-serial→date on `variable`, drop zero/blank cells, dash-normalize items, and **aggregate tranches** to mkedg5 × item × month. Keeps the messy source read separate from the clean event state.)*

**Publication rule (from doc §8.2):** only **Active** events exported; **daily** before **5 PM** DW pickup; grain = **one row per mkedg5 × item × month**. Truncate/reload vs incremental merge is an open production decision (§16) — prototype with staged **MERGE** for idempotency + acknowledgement, not blind truncate.

---

## 7. Output tables — STRICT: all writes go to `sandbox_operations.po_management`

**Hard rule (this session, non-negotiable):** **every output this app produces is written PURELY to `sandbox_operations.po_management` — strictly.** Nothing is written anywhere else. `prod_edw` (including `staging_flat_files`) is **READ-ONLY, always.** There is no app write, no exception, no "eventual" prod hop owned by us.

**`prod_edw.staging_flat_files.expansion_dims` / `expansion_loads` — SOURCE ONLY, with caveats:**
The app may **read** these to (a) learn the exact output **schema/shape**, and (b) **pull in existing Excel-originated events** so planners can *adjust* them in the app.
> *"these are the output tables… so this will be source for us"* / *"pull them in so we could build an app that would adjust them"* / *"I probably shouldn't be able to write to that… don't write into production."*

Caveats on treating them as a source:
- **Read-only, always** — never `INSERT/UPDATE/DELETE/MERGE/TRUNCATE/ALTER/DROP`, no write-capable streaming sink. Label every such query "READ-ONLY source" in implementation notes.
- **They are Oracle-integration *outputs*, not a clean event system-of-record** — an event's current truth may already be mixed with baseline in Oracle; treat pulled-in rows as a **seed/starting point**, not gospel. Reconcile before trusting.
- **item_number is dashed** (`49-56-0507`) vs dash-less `items_scd1` → normalize on read (`REPLACE(item_number,'-','')`).
- **They can lag / be truncate-reloaded by the existing daily batch** — a read is a point-in-time snapshot; don't assume it reflects an edit made moments ago.
- **Seed once, then own state in Lakebase** — after import, the app's source-of-truth for a live event is Lakebase, not a re-read of `expansion_*`. Avoid two writers of the same truth.

**So the data flow is strictly:**
- **Read** `expansion_*` + demand dims/measures (`prod_edw`) → seed events + disaggregation base. ✅ read-only.
- **App working/transactional state** → **Lakebase** (`demand_events`). ✅
- **All published/derived output** → **`sandbox_operations.po_management.demand_events_*`** (Delta) — the *only* write target. ✅
- **Oracle-inbound `staging_flat_files`** → **NOT this app's concern.** If/when productionized, a separately-approved integration owned by the DW team reads from our `sandbox_operations.po_management` output — we never write prod. ⏳ external, out of scope here.

This is fully buildable now with zero dependency on any prod-write decision.

---

## 8. Core mechanics (the math the app must own deterministically)

Per fit-for-purpose: **the LLM never does this math** — disaggregation, $→unit, lift, and rebalance are deterministic rules.

### 8.1 Ratio disaggregation (G2)
Planner inputs a total at a hierarchy level (mkedg0–4) for an item × month. App prorates to mkedg5:
```
share(mkedg5_i) = base_measure(mkedg5_i) / Σ base_measure(all mkedg5 in group)
output(mkedg5_i) = total_input × share(mkedg5_i)
```
`base_measure` default = `planner_baseline` (from `10_demand_daily`); allow choosing `working_final_forecast` and (open-item #3) 4–5 more. Output grain = mkedg5 × item × month. **MVP fallback:** if a base is zero/absent, offer even split (the "50/50 across two orgs" starting point) and flag it. **[V/PC]**

### 8.2 Dollar → unit (G3)
When input is $: disaggregate the **$** against the base measure in $, then convert each mkedg5 cell to units using that cell's price/unit basis, so the published value is always **units**. Confirm the unit-conversion basis at build (open decision). **[P]**

### 8.3 Percent lift (G3, Chrissy)
`lift_units(cell) = base_measure(cell) × lift_pct`. Stored/published as **units**. A lift is an *input mode*; the published value is static units (§8.4). **[V]**

### 8.4 Static vs dynamic — the rebalance button (G11)
- **Stored/published values are STATIC.** They do **not** move when the baseline changes. **[V]**
- **Rebalance is planner-triggered** (a "red disaggregate button"), never automatic. It:
  1. snapshots the current base measure into `disaggregation_run`,
  2. recomputes shares,
  3. shows the planner **candidates** (which cells would move materially) + a recommendation,
  4. applies only on confirm, writing an audit row.
- **Close-to-zero** (the plumbing removal): setting a customer/item/event to **CLOSED** forces its published output to **0** while retaining the record — this is how you "remove from allocation" without deleting. **[V]**

### 8.5 Non-repeating vs repeating placement (G4)
- Non-repeating: `# stores × Load Per Store` placed on the **start month**; classified so it is **excluded** from statistical history downstream.
- Repeating: `# stores × ASPV` **spread across all months**; classified so it is **included** in history.
Header-level assumptions apply to all items; line-level overrides win. **[V]**

---

## 9. Event lifecycle, locking, audit, acknowledgement

### 9.1 Lifecycle — four states (doc has three; call adds Closed)
`IN_PROGRESS` (draft, not exported) → `ACTIVE` (exported daily) → `DEACTIVATED` (soft-delete, retained, not exported). **`CLOSED`** (call): output forced to zero at event/customer/item grain, record retained (double-dip / over-scan management). Auto-expiry past date range is a fast-follow (doc §9.4). **[V]**

### 9.2 Locking (G9)
One editor per event; others view-only; lock releases on save/close/**timeout**. Enforced in Lakebase (`event_lock`), checked server-side on every mutation — never trust the UI. **[V]**

### 9.3 Audit (G6)
Every value change logged at **item/month/field** grain with actor + before/after + timestamp. Concurrent-edit **notification**: "an action touched this SKU N hours ago." **[V]**

### 9.4 Acknowledgement (G5 — the real pain)
Every publish writes `publication_ack` and surfaces it: rows published, run_id, timestamp, SUCCEEDED/FAILED. The planner sees **"your change was submitted"** with evidence — this directly answers "did it get submitted successfully," which the business ranked above "was it good." **[V]**

---

## 10. Publication path (Active events → Oracle-inbound)

```
Lakebase (Active events, cells) 
  → publication service (validate: status=ACTIVE, PurchPlan flags, grain, signed values)
  → staged rows + hash_diff + run_id + record_source + load_date  (expansion_dims/loads shape)
  → set-based MERGE into sandbox_operations.po_management.demand_events_published   [the ONLY write target — strict]
  → publication_ack written + surfaced to planner
  ─────────────────────────────────────────────────────────────────────────────
  (production, external, NOT this app) DW team's approved integration reads FROM
   sandbox_operations.po_management.demand_events_published → Oracle-inbound staging → read-back
```

Daily, before 5 PM. Our responsibility ends at the `sandbox_operations.po_management` write + acknowledgement; the Oracle hop is owned by the DW team and reads our output. **Truncate/reload vs merge** = open production decision (doc open-item #4); prototype with **staged MERGE** for idempotency and a real acknowledgement rather than blind truncate. **[P]**

---

## 11. Bulk edit on a category → Lakebase (the specifically-requested feature)

You want to **bulk-edit by category and write directly to Lakebase**. Here is the concrete design, using the staged set-based pattern from your bulk-write reference (never one DB call per row).

### 11.1 What "a category" means here
The planner picks a **category dimension** and a **selector**, then an **operation**:

| Category | Example selector | Typical operation |
|---|---|---|
| **Event** | one or many `exp_id` | Activate / Deactivate / Close many at once (doc §9.2 bulk status) |
| **Customer (mkedg0–5)** | "close all `plumbing` mkedg5 rows in event X" | Close / remove-from-allocation (the plumbing example) |
| **Tag** | "all events tagged `THD-Expansion`" | Bulk status change, bulk rebalance |
| **Item / family** | "these 100 SKUs" | Apply $ / % lift, adjust value |
| **Status** | "all IN_PROGRESS older than N days" | Deactivate / notify |
| **Org** | 2012 vs 2120 | Scope any of the above org-aware |

### 11.2 The write pattern (matches your reference doc)
```
React (planner selects category + selector + operation + value)
  → BFF /bulk-edit  (authorize actor; enforce max rows, schema, permitted fields, org-awareness)
  → bulk_edit_batch (batch_id, request_id, idempotency_key, category, operation)   [Lakebase]
  → bulk_edit_stage  (one bulk insert of all affected rows, validated + deduped)   [Lakebase]
  → ONE set-based apply:  UPDATE … FROM stage  /  INSERT … ON CONFLICT DO UPDATE   [Lakebase]
  → event_audit_event rows for every changed cell (before/after)                   [Lakebase]
  → return {batch_id, matched, changed, rejected[]}  → UI reads back the new state
```

Key guardrails (all from the reference + skill):
- **Idempotent:** `request_id` + a processed-batch ledger; safe to retry.
- **Deduplicate by business key** (`exp_id × item × mkedg5 × month`) before the apply — pick newest by `submitted_at`.
- **Only permitted fields** change; never blindly overwrite every column from the payload.
- **Per-request row cap;** very large edits (e.g. thousands of SKUs) go through a Databricks Job, not a long-held web request.
- **Direct-to-Lakebase means the app's transactional state**, *not* the Oracle-inbound tables — publication to Oracle still goes through §10. "Bulk edit writes to Lakebase" and "publish Active events" are two separate steps.
- **Rejected rows** returned + quarantined; the acknowledgement pattern (§9.4) applies to bulk too.

### 11.3 Why not write the bulk edit straight to Delta/Oracle
Delta is not a concurrent human-edit store; Oracle-inbound is gated by §7. Bulk edits are **draft/working transactional state** → Lakebase is the correct target, then normal publication applies. **[V]**

---

## 12. Required UI surfaces & states

**Surfaces:** Event list/search (by name, customer, status, date, **tag**) · Event editor (header, customers, items, month grid) · Forecast Builder (separate page) · **Bulk-edit workbench** (§11) · Outcome/day-over-day view (G7/G10) · Validation summary (pre-publish checklist).

**Every operation must show** (skill mandate): loading · valid-empty · input-validation · authorization-failure · dependency-unavailable · unexpected-error **with correlation ID** · durable success · updated data after mutation · action history/provenance. A button is "done" only when: **click → API executes once → Lakebase commits → UI reads back → audit appears → status updates.**

**Provenance markers** on every computed value: `DETERMINISTIC_RULE` (disaggregation, lift), `SQL_METRIC` (base measures), `CACHED`, `DEMO_FALLBACK`. Never imply a real result when a fallback was used.

---

## 13. Modularization plan (share the learning, don't dilute)

| Concern | Supply (P1/P2) | Demand Events (P3) | Shared? |
|---|---|---|---|
| Repo | existing Streamlit `data_apps` / analysis in `data_understanding/` | **new React repo** | ✗ code |
| UI framework | Streamlit / AI-BI | **React + FastAPI BFF** | ✗ |
| Lakebase schema | supply entities | **`demand_events`** schema | ✗ data, ✓ pattern |
| Delta namespace | `p1slice_*`, `sdp_*` | **`demand_events_*`** | ✗ tables, ✓ location |
| Read sources | supply facts (`20_supply_daily`, receipts) | demand dims + `10_demand_daily` | ✗ |
| Patterns (audit, idempotency, bulk-merge, UI states, deployment gates, guardrails) | — | — | **✓ reuse fully** |
| Operating skill | `mke-supply-chain-fde` | `mke-supply-chain-fde` | **✓** |

Net: **one shared operating pattern and one shared set of transactional/bulk patterns; separate repo, schema, namespace, and domain services.** That's how we carry the learning forward without the demand app inheriting supply's tables or coupling to its code.

---

## 14. Requirement → Databricks traceability (per fit-for-purpose method)

| Requirement (doc §) | Decision | Domain object | Analytical asset (Delta) | Transactional asset (Lakebase) | Product | Evidence |
|---|---|---|---|---|---|---|
| Event identity/status (§1) | 4-state lifecycle | event | published snapshots | `event`, `event_lock` | Lakebase+App | [V] |
| Audit/change log (§1.4) | item/month/field audit | audit event | audit projection | `event_audit_event` | Lakebase | [V] |
| Header metadata (§2) | header inputs | event_header | — | `event_header` | Lakebase | [V] |
| Multi-customer + hierarchy (§3) | multi-select, level input | event_customer | — | `event_customer` | App+dims | [V] |
| Disaggregation (§3.3) | ratio vs `planner_baseline` | cell | disaggregation audit | `event_cell`, `disaggregation_run` | Deterministic rule | [V] |
| Item entry/validation (§4) | `item_status='PurchPlan'`, warn-only, dash-normalize | event_item | — | `event_item` | SQL + App | [V] |
| Time dimension (§5) | monthly buckets, 23-mo max | cell | — | `event_cell` | App | [V] |
| Forecast values/Builder (§6,§7) | deterministic builder + $/%-lift | builder inputs | — | `event_header`/`event_item` | Deterministic rule | [V] |
| Output tables (§8) | expansion_* = READ source; publish to our Delta; Oracle hop external | published output | `demand_events_published` | — | AppKit + existing integration | [V] |
| Seed existing events (§7) | pull Excel-originated events in to adjust | event/cell | — | `event`, `event_cell` | Analytics plugin read | [V] |
| Bulk status / bulk edit (§9.2) | staged set-based apply | bulk batch | — | `bulk_edit_batch/stage` | Lakebase | [V] |
| Summary/day-over-day (§9.3) | publish history deltas | outcome | `demand_events_publish_history` | — | Delta + dashboard | [P] |
| Notifications/ack (§9.4) | publish acknowledgement | ack | — | `publication_ack` | Lakebase | [V] |
| Users/access (§10) | all-see, lock-gated, no approval | — | — | `event_lock` | App authz | [V] |

---

## 15. What I deliberately did NOT choose (rejected/deferred)

- **[R]** Direct App→Oracle or App→`prod_edw` write — violates guardrail; business explicitly said no writes to prod. expansion_* is a read source; publication lands in our Delta and the existing integration owns the Oracle hop.
- **[R]** Genie/LLM for disaggregation, lift, or value math — deterministic rules only.
- **[R]** An always-on ML/forecast endpoint — P3 is transactional; no prediction changes a decision here.
- **[R]** Automatic daily rebalance — business called it "chaos"; planner-triggered only.
- **[R]** Streamlit for this build — business chose **AppKit (React/TS)**; it diverges from the existing Streamlit `data_apps` repo, hence a new repo (§13).
- **[R]** Hand-rolled React + FastAPI BFF — AppKit already provides the React UI + typed Node backend + SQL/Lakebase/Genie plugins; no reason to rebuild that plumbing.
- **[Deferred]** Regional/store granularity, auto-expiry, export-to-Excel, duplicate-as-template, approval workflow — fast-follow, not MVP.
- **[Deferred]** Vector search — structured operational records → Lakebase BM25 if search is needed, not vectors.

---

## 16. Open decisions & pre-build validation gates

**Must decide (you / Milwaukee):**
1. **⚠️ TOP RISK — item validation criterion.** The live profile proved `item_status='PurchPlan'` flags **100% of a real valid event** (`EXP001442`: 22 ShipSO, 2 DiscExtrnl, 0 PurchPlan). Reconfirm with analytics engineering **what status set actually characterizes valid event SKUs** (likely `ShipSO` + others, not PurchPlan). Non-blocking to build (warning-only), but blocks a *correct* validation rule. *(Was open-item #1; now evidence-backed.)*
2. **Oracle hop ownership (external, not this app, not blocking)** — at production time, which DW-team integration reads our `sandbox_operations.po_management.demand_events_published` and writes it into `prod_edw.staging_flat_files`? This app writes **only** to `sandbox_operations.po_management` — strictly — never touches prod.
3. **New AppKit repo + CI/CD** — confirm repo name/location; CI/CD from the start but **no auto-publish** until SME/QA validate.
4. **Disaggregation measures** — confirm the 4–5 additional measures beyond `planner_baseline` / `working_final_forecast` (open-item #3). Profile confirmed many candidates exist (`final_demand_forecast`, `total_statistical_forecast`, `customer_forecast`, …).
5. **$→unit conversion basis** — what price/unit basis converts disaggregated $ to units? (Profile: `_amount` columns are the $ counterparts.)
6. **Truncate/reload vs merge** for daily publication (open-item #4).
7. **Tag taxonomy** (open-item #6) and **notification recipients/channels** (open-item #5).
8. **Seed scope** — import *all* 1,462 existing events for adjustment, or only Active/recent on first load?
9. **Tranche handling (new, from profile)** — on import, **preserve** per-tranche detail (`file_index`) or **collapse** to mkedg5 × item × month? Affects `event_header` grain and re-publish fidelity.

**Must re-validate live before build:**
- ✅ **Done this session** (`DATA_PROFILE.md`): all 6 §4 tables read on `mke-rsc`/`7bd33a82f4e92206`; hierarchy, item statuses, `planner_baseline`, orgs, and event shape confirmed live.
- Confirm `sandbox_operations.po_management` is writable and pick the `demand_events_*` namespace.
- Confirm Lakebase availability and the `demand_events` schema location.
- Profile item-status distribution across **many** events (not just `EXP001442`) to pin the real validation set for decision #1.

**Recommended first vertical slice (data is validated; can start once §16.2–3 are answered):**
> Seed/normalize one real event (e.g. `EXP001442`: Excel-serial→date, drop zero cells, dash-normalize, aggregate tranches) → create a multi-customer event → add items (validation **warning only**, rule-version-tagged — do NOT hardcode PurchPlan per §16.1) → enter a total at mkedg4 → **disaggregate to mkedg5 × item × month against `planner_baseline`** → save to Lakebase with lock + audit → read-back + audit → run one **bulk close** on a customer (→ zero) → **publish Active** to `sandbox_operations.po_management.demand_events_published` with an acknowledgement.

That single journey exercises reads, the DQ/seed normalize, disaggregation math, Lakebase transactional state, the bulk-category write, locking, audit, and the acknowledgement — proving the whole spine before any horizontal assets. The validation *criterion* (§16.1) can be corrected without reworking the slice because the flag is rule-versioned and non-blocking.

---

*Nothing in this document has been built. It is the design and data contract for review, now updated against a live source profile (`DATA_PROFILE.md`). The data is validated; on your go-ahead (and §16.2–3), the next step is the platform probe + walking skeleton, then the vertical slice above.*
