# Architecture — the data-plane decision + the two-plane pattern

## The Decision Gate (do this before scaffolding)
Ask what the app actually does, then pick the plane(s):

| Need | Plane | Why |
|---|---|---|
| Dashboards, KPIs, aggregations, filtered browsing, `ai_forecast`, reading Delta gold | **SQL Warehouse** | Query-at-read-time on governed Delta; seconds-latency is fine |
| Sub-second lookups, typeahead / full-text search, real-time per-record reads | **Lakebase** (synced or mirrored) | OLTP latency; Postgres FTS/trgm |
| **Write-back**: forms, actions, approvals, audit, drafts, status, comments | **Lakebase** (a writable table) | The warehouse/Delta is read-only truth; OLTP is where state lives |
| NL Q&A over tables | **Genie** | NL→SQL over the same gold |
| LLM reasoning / recommendations | **Model Serving** | foundation model, rules-first fallback |

Most **operational** apps (see → decide → act) are **two-plane**: warehouse for heavy read-only compute,
Lakebase for interactive state + writes. Pure dashboards are warehouse-only (and honestly may not need a
custom app at all — a managed AI/BI dashboard is simpler; reach for Streamlit when you need write-back,
bespoke interactivity, an embedded chat/agent, or auth-gated workflows).

## The two-plane pattern (OLAP truth + OLTP surface)
```
   Delta gold (catalog.schema.*)          Lakebase (Postgres, schema app_x)
   READ-ONLY source of truth              interactive OLTP surface
        │                                      │
        │  (optional) mirror/copy the read     │  read mirrors (fast) + ai_forecast (warehouse)
        │  set the app browses ─────────────▶  ├─ mirror_* tables  (read-only in the app)
        │                                      └─ ONE writable table(s): action/audit/outbox
        ▼                                             ▲
   SQL Warehouse (ai_forecast, ad-hoc)                │ every write: status + OBO approver + append-only audit
                                                       │ + SIMULATED external push (never a real prod write)
```

Rules that make it robust (learned on the real build):
- **One writable table (or a small owned set).** Mirrors are read-only *in the app*; never write to a
  synced mirror. The write path is a single transaction: flip status, stamp the OBO approver, append to
  an audit-trail JSONB, enqueue a SIMULATED external message + its ack, capture a decision/eval row.
- **Respect the project's write boundary.** Read-only prod; writes only to the approved sandbox schema +
  Lakebase; external-system writeback (Oracle/SCC/WMS) is SIMULATED unless a separate approved, typed,
  auditable path exists. A governance guardrail OVERRIDES convenience.
- **Deterministic first, model second.** The rules answer is the product; the LLM is an enhancement with
  graceful fallback. This is a *trust* decision, not just resilience.
- **Live cascade = `st.rerun()`.** After a write, rerun so KPIs/queue re-query Lakebase and visibly move.
  In Streamlit the rerun IS the cascade; you don't need an event bus.
- **Independence when you fork.** A second app that must not collide gets its OWN schema (structure-clone
  `LIKE … INCLUDING ALL`, copy mirror data, empty writable tables) and its OWN app + SP. Shared infra
  (warehouse, Genie, serving, the Lakebase project compute) is fine to share by reference.

## Loading the read mirrors (if you mirror gold into Lakebase)
Two ways to get gold into Lakebase mirrors:
- **Lakebase synced tables** (managed CDC from Delta) — best when the source is a real UC table and you
  want it continuously fresh. See the `databricks-lakebase` skill.
- **App-managed copy** — a small idempotent bootstrap that reads gold via the warehouse and inserts into
  the mirror if empty. Simple, good for a bounded snapshot; guard on emptiness so it doesn't re-copy each
  boot; tolerate a missing source table (leave the mirror empty rather than crash).
Either way the writable tables start EMPTY and are never synced.

## What "done" means
Full arc runs on the deployed URL: open the app → see the ranked worklist → ask why (streamed
explanation + recommendation) → forecast/what-if → approve → the write lands with an audit trail and the
queue/KPIs move — and it degrades visibly (missing table, model error) instead of crashing.
