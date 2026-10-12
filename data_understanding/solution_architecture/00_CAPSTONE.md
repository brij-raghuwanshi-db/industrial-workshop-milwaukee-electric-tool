# Solution Architecture — Capstone: from the pain to the platform

**As-of 2026-08-30.** This ties the documented **search pain** (`../data_stories/THE_SEARCH_PAIN_JOURNEY.md`)
to the Databricks architecture that removes it. Read this first, then the four sections. All choices honor the
project guardrails: `prod_edw`/`prod_operations` **READ-ONLY**; derived writes → `sandbox_operations.po_management`;
transactional state → **Lakebase**; external writeback via a **typed, approved, audited** action path only.

## The core thesis
The EDW is mature — storing the data is a solved problem. The unmet need is **meaning**: every user re-pays
the full cost of understanding (right table, right grain, right key, right cost weighting, right time window)
on every question. The architecture's job is to **pay that cost ONCE, in a governed layer, so it's never
re-paid** — turning a hundreds-of-queries adventure into an English question with a certified answer.

## The four sections
1. **`01_medallion_foundation.md`** — a *governed consumption medallion* over the read-only EDW: Bronze
   (governed read views picking the RIGHT source), Silver (Lakeflow SDP that bakes in key-crosswalk,
   dash-normalization, RECEIVE-only, SCD2-dedup, weekly-Monday grain + fail-loud data-quality expectations),
   Gold (cost-enriched item×org×week facts), and **Metric Views** (define-once measures that make
   semi-additive / grain / cost mistakes impossible). Orchestrated by Lakeflow Jobs; governed by Unity Catalog.
2. **`02_analytical_transactional.md`** — the two serving planes: **analytical read** (AI/BI Lakeview
   dashboards on Gold+metrics with multi-snapshot "was-green-now-red"; UC→Lakebase **synced tables** for
   sub-second app reads) and **transactional write** (Lakebase native Postgres: cases, event drafts, locks,
   approvals, action_request/audit, idempotency). Closed loop: analytics → recommendation → decision → typed
   action → outcome → CDF→Delta → learning. Databricks App = the unified planner shell with a human gate.
3. **`03_ai_decision_products.md`** — the AI layer that collapses the search pain: **focused Genie Agents**
   (one per P1–P4, on certified metric views, evaluated), **AI Functions** (in-SQL classify/summarize/extract/
   forecast), **Agent Bricks KA** (policy/tribal-knowledge Q&A), **Lakebase Search BM25** (similar-case
   retrieval — *NOT* Vector Search), **ML + Model Serving** only where justified, and **MLflow evaluation**
   to keep it trustworthy. Strict deterministic-vs-AI split: the LLM explains and coordinates; it never invents
   thresholds, math, constraints, permissions, or transactions.
4. **`04_complete_landscape_financials.md`** — the full picture in one governed place: **Unity Catalog** as the
   lineage/permission backbone (fixes the "no lineage" gap via system tables), an **item-360** conformed view,
   **financial completeness** via metric views (inventory value, $ variance, spend, revenue/COGS, loss KPIs —
   standard-cost-not-GL), **Lakeflow Connect** for gaps/enrichment only (incl. the geocode path), and
   **DABs + CI/CD** so the whole thing is source-controlled and promotable (not notebook-only).

## Pain → cure (the one-screen map)
| Documented pain (from the journey) | Architectural cure | Section |
|---|---|---|
| Wrong table / mislabeled source (receipts have no item col; "Status 20"='PurchPlan') | Bronze picks the RIGHT source (`purchase_receipt_line`); Silver encodes the real filter | 01 |
| Semi-additive sum (on-hand 6.5× wrong) | Metric View defines on_hand as point-in-time; can't be summed across dates | 01 |
| Hidden grain / fan-out (3,989 rows) + transfer double-count | Silver rolls to declared grain; Metric View enforces it; DQ row-count checks | 01 |
| Key mismatch (raw Oracle vs bigint) + dash codes (4.8%→98.7%) | Silver crosswalk + dash-normalization baked once | 01 |
| Empty designed columns (frozen_* NULL) | Gold derives the drift from snapshot deltas; DQ flags the gap | 01 |
| Magnitude illusion ($0.0134 part as #1) | Gold cost-enriches; priority = deterministic unit×cost×ABC×org-role score | 01 / 03 |
| Time-blindness ("green last week, red now") | Retained snapshot history + multi-snapshot dashboard + metric-view vintages | 01 / 02 |
| SCD2 duplicates (2.3× inflation) | Silver dedupes to latest valid version | 01 |
| Manual multi-system pull every Monday | One governed layer + focused Genie Agent → English question, certified answer | 02 / 03 |
| No exception workflow / no locking / no audit / 69% unrouted | Lakebase cases + locks + audit + persona routing via synced profiles | 02 |
| No lineage visible to user | UC system tables (table/column lineage + audit) with proper grants | 04 |
| "Is this trustworthy?" | Certified metric views + MLflow-evaluated Genie + human gate on actions | 03 |
| Adverse-write risk (external + P3 publish) | Typed, idempotent, approved action path; prod read-only by architecture | 02 / IMPACT |

## The before/after for a planner
- **Before:** Monday morning, pull from multiple systems, ~15+ queries per question, re-learn the same ~15
  gotchas, ship a 6.5×-inflated number if you don't know them, no audit, no routing. Per person, every week.
- **After:** open the app → "Which A-items breach safety stock this week, ranked by $ impact?" → focused Genie
  Agent answers off certified metrics in seconds (grain/additivity/cost correct *by construction*), similar
  past cases surfaced via Lakebase BM25, disposition + approval captured in Lakebase with full audit, any
  external action goes through the typed approved path. The understanding cost was paid once.

## Fit-for-purpose discipline (what we deliberately did NOT pick)
- **Vector Search** — deferred; Lakebase Search BM25 fits the exact-term transactional retrieval (per your direction).
- **Lakebase as a warehouse** — no; Delta/Gold for analytics, Lakebase for state only.
- **Dashboard for data entry / Delta for concurrent edits / Genie writeback** — no; App+Lakebase for writes,
  Genie stays read-only.
- **One giant enterprise Agent** — no; four focused, evaluated Genie Agents + a plain app shell.
- **Always-on ML endpoints by default** — no; periodic Job+MLflow for forecasts, serve only for interactive.
- **Re-ingesting the EDW** — no; read in place, derive in sandbox; Lakeflow Connect only for genuine gaps.

## Honest caveats carried forward
- Standard-cost + order pricing, **not the GL** — true landed cost / margin actuals are a separate finance system.
- No lat/long (mapping needs a geocode enrichment); COO codes need normalization.
- No serial/lot — traceability is quantity-by-node, not unit-level.
- SDP limits (one op/dataset, no pivot, MV no time-travel); federation pushdown must be plan-verified.
- The crosswalk is a lookup join, not a cast; validate row-count parity after each Silver build.

## Bottom line
Milwaukee already won the hard *storage* battle. This architecture wins the *meaning* battle: **pay the
understanding cost once, in a governed medallion + semantic layer; serve it read-side (dashboards, synced
tables) and write-side (Lakebase, typed actions); and put a certified, evaluated, English-language AI surface
on top** — so hundreds of users stop re-walking the pain journey every week, and decisions get faster,
cheaper, and trustworthy.
