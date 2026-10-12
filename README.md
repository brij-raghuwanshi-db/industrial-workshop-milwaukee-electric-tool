# MKE Supply Chain on Databricks — project workspace

Milwaukee Electric Tool (TTI) supply-chain analytics + operational apps on Databricks.
Roadmap: **AI/BI dashboard → SDP pipeline → Genie agent → Databricks Apps with actions.**

## Directory map

| Path | What it is | Notes |
|------|-----------|-------|
| `CLAUDE.md` | Project operating instructions (auto-loaded by the agent) | **root — do not move** |
| `WORKLOG.md` | Durable, phase-by-phase decision trail | **root — do not move**; append after each accepted change |
| `README.md` | This file | |
| `mke-po-actions/` | **Deployed React/AppKit app** (roadmap step 3) — DAB-tracked, synced to Databricks | ⚠️ app code — do not reorganize |
| `mke-po-actions-st/` | **Deployed Streamlit app** (parallel twin) — DAB-tracked, synced to Databricks | ⚠️ app code — do not reorganize |
| `docs/` | Design & reference documents | see `docs/` below |
| `customer_requirements/` | Authoritative P1–P4 scope (source of truth for requirements) | input |
| `data_understanding/` | Data exploration + the scenarios we uncovered (S/G/P/AP/V/T/2120/flow) | input |
| `development_pattern/` | Operating-pattern discussions | input |
| `memory_export/` | Point-in-time export of the agent's project memory (raw files + index) **plus bundled skills** | snapshot |
| `memory_export/skills/databricks-agentic-ops-app/` | The agentic-ops-app skill used to build the apps | reference (bundled in the export) |
| `backups/` | Timestamped `WORKLOG.md` snapshots (all history, one folder) | 32 snapshots |
| `.claude/skills/` | **Live, auto-loaded** project skills (`databricks-streamlit-apps`, `lakeview-dashboard-fastpath`, `mke-supply-chain-fde`) | ⚠️ edit here — this is the path that auto-loads |
| `skills/` | **Browsable copy** of the above 3 skills (for reading/sharing) | mirror; edits here do NOT take effect |

## `docs/`
- `P1_ACTIONS_APP_TECHNICAL_DESIGN.md` — the App design doc (problems → architecture → actions).
- `P1_ACTUALS_SDP_DASHBOARD_WALKTHROUGH.md` — the SDP dashboard walkthrough.
- `MEMORY_EXPORT.md` — consolidated, organized export of all agent memories (also raw in `memory_export/`).

## Guardrails (always)
`prod_edw` / `prod_operations` are **read-only**. All writes go to `sandbox_operations.po_management`
(Delta) + Lakebase. External-system writeback (Oracle) is **SIMULATED**. Always pass `--profile mke-rsc`.

## Deployed assets
- Apps: `mke-po-actions` (React) + `mke-po-actions-st` (Streamlit) — live on Databricks Apps.
- SDP dashboard, weekly Job, and Genie space `01f1a542c3f7132681b64d8ff08b4033` — see `WORKLOG.md`.
