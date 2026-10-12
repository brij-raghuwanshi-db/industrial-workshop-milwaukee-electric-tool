---
name: mke-genie-app-enablement
description: "Gold tables are Genie's knowledge and the App's data/action surface; enablement notes are source-of-truth"
metadata:
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

The three consumption surfaces over the reconciled gold in `sandbox_operations.po_management` are
deliberately split (fit-for-purpose): **AI/BI dashboard = read/show** (Rung-1/2 + Cross-Org page),
**Genie space = read/ask via AI**, **Databricks App = act** (search, write-back, on-click approve/reject,
alerts, supplier cases). The App is the ONLY surface that takes actions.

**Source-of-truth docs (all in `data_understanding/`):**
- `GENIE_ENABLEMENT_NOTE.md` — data surface + reasoning playbook + build recipe for a Genie space.
- `GENIE_QUESTION_BANK.md` — every question our observed scenarios imply, tied to answering table/measure +
  expected answer/gotcha, plus guardrail (wrong-if-naive) questions from the anti-patterns.
- `APP_ENABLEMENT_NOTE.md` — maps each read-signal → the App action it enables; the Lakebase entity list;
  the safe write-back path.

**Non-negotiable action-layer guardrail:** App reads Delta gold; transactional state → Lakebase (drafts,
locks, approvals, action_request, outbox, audit); Lakebase→Delta publish only into
`sandbox_operations.po_management`; external writeback (Oracle/SCC/WMS/TMS) via a separately-approved typed
auditable action path — NEVER a direct prod write, never App→Oracle directly. Search = Lakebase BM25, not
Vector. Genie/App both scope ONLY to the gold tables. See [[mke-project-guardrails]],
[[mke-orgs-are-not-interchangeable]], [[mke-order-lifecycle-flow-slice]].
