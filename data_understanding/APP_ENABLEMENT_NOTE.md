# App Enablement — from read-only stories to an interactive, write-back, action-taking planner App

**Written:** 2026-08-31 · companion to [GENIE_ENABLEMENT_NOTE.md](GENIE_ENABLEMENT_NOTE.md) +
[GENIE_QUESTION_BANK.md](GENIE_QUESTION_BANK.md).
**Why:** the user's directive — *"these things will also be part of the Databricks App development, because
many things here can be made interactive, searchable, write-backable, on-click approve/reject and other
actions, alerts sent across…"* This note maps everything we've built to the **three-surface** target and,
specifically, to the **action layer** only an App can provide. It is a grounded design map, **not a build** —
App development is a deliberate later decision (fit-for-purpose, after the slices reconcile).

## The three surfaces (each does what it's best at — don't force one to be all three)
| Surface | Job | Reads | Writes | Built with |
|---|---|---|---|---|
| **AI/BI dashboard** | show the story / KPIs | Delta gold | — | done (Rung-1/2 + Cross-Org) |
| **Genie space** | answer NL questions via AI | Delta gold | — | enablement note + question bank |
| **Databricks App** | **act** — search, edit, approve/reject, alert, write back | Delta gold **+** Lakebase | **Lakebase** (txn state) → publish to Delta; external via typed action path | this note (design) |

> **The App is the only surface that takes actions.** Dashboard = look; Genie = ask; App = *do*. The user's
> "approve/reject, write-back, alerts" all live here.

## The hard guardrail the App must honor (non-negotiable, from project rules)
- **Reads:** `sandbox_operations.po_management.*` gold (never prod raw).
- **Transactional App state → Lakebase** (Postgres): drafts, locks, comments, approvals, action requests,
  outbox, statuses, saved searches, idempotency records. Lakebase→Delta publication writes only into
  `sandbox_operations.po_management`.
- **External-system writeback** (Oracle Fusion / SCC / WMS / TMS — e.g. actually cancel/resize a PO) uses a
  **separately approved, typed, auditable action path** — NEVER a direct write to a Databricks prod schema,
  and never a direct App→Oracle hack. The App *queues* a typed action + captures approval; execution is the
  approved integration lane.
- `prod_edw` / `prod_operations` stay **READ-ONLY**.

## What we built → the App action it enables (the mapping the user asked for)
| Signal we built (read) | Table | App action (do) | State lands in |
|---|---|---|---|
| Exception queue (off-plan, cost-ranked) | `rung2_plan_vs_actual` | **Assign / snooze / comment / mark-reviewed** on an exception | Lakebase `exception_case`, `planner_comment` |
| Alert tier (org-aware escalate) | `rung2_plan_vs_actual` | **Send alert** (Slack/email) to owner/role; ack | Lakebase `notification_delivery`; role from planner_name/O-routing |
| Recommended maneuver (expedite/defer/resize) | `p1flow_order_stage_gold` | **On-click approve / reject** a maneuver; **request PO cancel/resize** | Lakebase `action_request` + `approval` → typed `integration_outbox` |
| Chronic-slipper (systemic vs one-off) | `p1flow_order_stage_gold` | **Open a supplier case / SRM follow-up** instead of per-order expedite | Lakebase `exception_case` (supplier-scoped) |
| DC imbalance (shared items) | `rung2_plan_vs_actual` shared-join | **Propose a rebalance transfer** (draft, approve) | Lakebase `action_request`; publish to Delta |
| Any story/scenario | all gold | **Saved search / search across items-orgs-suppliers** | Lakebase `saved_search`; BM25 search (NOT vector) |
| Every action | — | **Full audit: who/what/when/outcome** | Lakebase `action_audit_event`; publish `action_outcome_history` to Delta |

## Action patterns (the interactive behaviors, concretely)
- **On-click approve/reject:** a maneuver row → approve → writes an `approval` + a typed `action_request`;
  a background publisher moves approved requests to `integration_outbox` for the external lane; status
  reflects back (`integration_result`). Idempotency record prevents double-fire.
- **Write-back (safe):** never App→Oracle directly. App → Lakebase typed request → approved outbox →
  integration worker → Oracle; result + audit captured. Every step reversible/traceable.
- **Alerts across:** alert-tier or Very-late+chronic rows → notification with the *reason* (not just "late");
  delivery + ack tracked so nothing is silently dropped.
- **Search:** planners search items/orgs/suppliers/exceptions — use **Lakebase Search (BM25)**, not Vector
  Search (this is keyword/lookup, not semantic-similarity; fit-for-purpose).
- **Optimistic locking / drafts:** two planners on the same exception → `event_lock` + `event_draft` prevent
  clobbering.

## Known App gotchas to design for (from platform-gotchas reference — flag now, solve at build)
- **Apps SP / resource wiring:** the App runs as a service principal; it needs explicit GRANTs on the gold
  schema + the Lakebase instance wired as a resource. Empty-for-others-but-not-owner = a grant issue.
- **iframe / CORS / auth:** embedding the dashboard or Genie in the App hits iframe/CORS/CSP + auth — plan
  postMessage/embedding auth, don't assume it "just embeds."
- **Lakebase↔UC read-only boundary:** Lakebase reads UC tables read-only; the publish path (Lakebase→Delta)
  is the only write into `sandbox_operations.po_management`.
- **Genie-in-App:** an "Ask" panel powered by our Genie space is a legit App feature (conversational surface);
  keep its scope = the gold tables + the question bank.

## Fit-for-purpose stance (don't overengineer)
Build the App **only** for what genuinely needs action/write-back/interaction — the dashboard already covers
read-only KPIs and Genie covers NL Q&A. The App's earned scope: the **exception → decision → action → audit**
loop (approve/reject a maneuver, queue a typed writeback, alert an owner, record the outcome). Everything
needed is already in the gold (read) + the Lakebase entity list (write). When we build: walking skeleton →
one vertical slice (one exception type, end-to-end: view → act → approve → outbox → audit) → reconcile →
widen — the same vertical-slice discipline that built everything else here.

## Status
This is a **design map**, not a build. The data + action surfaces are ready; the App is the next deliberate
decision. Source-of-truth for that build = this note + the Genie enablement note + question bank + the two
build logs (RUNG2, P1FLOW).
