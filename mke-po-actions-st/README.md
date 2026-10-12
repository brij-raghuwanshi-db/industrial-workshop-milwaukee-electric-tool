# MKE PO Action Cockpit — Streamlit twin

A **Streamlit** Databricks App that reproduces the production React/AppKit app
(`mke-po-actions`) with the same functionality, on the same governed data — proving the
agentic-ops pattern in a Python stack.

## What it does
See off-plan items (below safety stock, org 2012) → **ask why** (AI analysis streams live;
choose **LLM / Rules / Auto**) → **forecast** (`ai_forecast`) + **what-if** → capture the
decision → **approve & execute** (Lakebase write + audit trail + SIMULATED Oracle push) →
**analytics** + **scenarios** + **Genie** NL Q&A.

## Pages
- `app.py` — landing + one-time schema bootstrap
- `pages/1_Cockpit.py` — queue, KPIs, search, click-row → streaming explain + forecast + what-if + act
- `pages/2_Ask_Genie.py` — Genie NL Q&A over the SDP tables
- `pages/3_Dashboard.py` — native analytics (by ABC / planner / chronic / $ band) with teaching captions
- `pages/4_Scenarios.py` — the live playbook (cost-vs-units, chronic, hero trajectory)

## Architecture
- **Two planes.** Delta (`sandbox_operations.po_management.sdp_*`, read-only) is truth, read via the
  **SQL warehouse** only for `ai_forecast()`. **Lakebase** (Postgres) is the interactive OLTP surface.
- **Independent schema `app_po_st`.** A structural + data clone of the React app's `app_po`: identical
  mirror data (2,516 exceptions / 62,211 trajectory / KPI), but its **own writable tables** so this app's
  actions never collide with the React app's. Verified: a write here is invisible to `app_po`.
- **Both explanation engines.** `lib/serving.py` — real Claude Sonnet 4.5 via model serving, with a
  deterministic rules engine as the guaranteed answer/fallback.
- **Guardrails.** prod read-only; writes only to Lakebase `app_po_st` + `sandbox_operations.po_management`;
  Oracle writeback SIMULATED; all views scoped to org 2012.

## Separation from the React app (`mke-po-actions`)
This app is independent end-to-end. What it **owns** vs **shares** (shared = pointed-to infra, by design):

| Asset | This app | Separate? |
|---|---|---|
| Source directory | `mke-po-actions-st/` | ✅ own |
| Bundle (`databricks.yml`) | `mke-po-actions-st` | ✅ own |
| Runtime (`app.yaml`) | streamlit start cmd | ✅ own |
| Deployed app + Service Principal + URL | `mke-po-actions-st` | ✅ own |
| Lakebase **schema** | `app_po_st` (own writable tables) | ✅ own — writes never touch `app_po` (proven) |
| Lakebase **project/branch/endpoint** | `mke-po-actions` | ↔ shared compute, isolated schema |
| SQL warehouse / Genie space / serving endpoint | `7bd33a82…` / `01f1a542…` / `databricks-claude-sonnet-4-5` | ↔ shared workspace infra (no per-app copy exists for foundation models) |

The React app is never read, written, or redeployed by this app.

## Resources (referenced via `databricks.yml`)
| Resource | Value |
|---|---|
| SQL warehouse | `7bd33a82f4e92206` |
| Genie space | `01f1a542c3f7132681b64d8ff08b4033` |
| Lakebase | `projects/mke-po-actions/branches/production` |
| Serving endpoint | `databricks-claude-sonnet-4-5` |

## Deploy
```bash
databricks bundle deploy --profile mke-rsc
databricks apps deploy mke-po-actions-st --profile mke-rsc
```

## Local dev
`pip install -r requirements.txt` then `streamlit run app.py` with a `mke-rsc` credential in the
environment (the SDK picks up the profile). Requires network egress to PyPI + the workspace.
