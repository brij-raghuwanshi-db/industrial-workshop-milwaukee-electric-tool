"""Central config: env resolution, resource IDs, constants, guardrails.

Mirrors the React app's resource wiring. Everything workspace-specific comes from env
(injected by Databricks Apps via `valueFrom`); local dev falls back to the same defaults
the bundle uses so `streamlit run` works with a `--profile mke-rsc` credential in the env.
"""
from __future__ import annotations
import os

# ---- Unity Catalog: the read-only Delta source (ai_forecast reads this; NEVER written) ----
CATALOG_SCHEMA = "sandbox_operations.po_management"
SDP_PLAN_VS_ACTUAL = f"{CATALOG_SCHEMA}.sdp_plan_vs_actual"

ORG = "2012"  # Olive Branch — the in-scope org, matching the React app
# Source schema the React app owns (read-only reference we copy mirror data FROM).
SOURCE_PG_SCHEMA = "app_po"

# ---- resource identifiers (env first, then bundle defaults) ----
def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, "").strip()
    return v or default

# This app's OWN Lakebase schema — an independent copy of app_po (its own writable tables so
# actions never collide with the React app). Mirror data is copied from SOURCE_PG_SCHEMA.
PG_SCHEMA = _env("APP_PG_SCHEMA", "app_po_st")

WAREHOUSE_ID = _env("DATABRICKS_WAREHOUSE_ID", "7bd33a82f4e92206")
GENIE_SPACE_ID = _env("DATABRICKS_GENIE_SPACE_ID", "01f1a542c3f7132681b64d8ff08b4033")
SERVING_ENDPOINT = _env("DATABRICKS_SERVING_ENDPOINT_NAME", "databricks-claude-sonnet-4-5")

# Lakebase connection: host + endpoint path (for OAuth credential minting).
PGHOST = _env("PGHOST", "ep-blue-sound-e8lle8po.database.centralus.azuredatabricks.net")
PGDATABASE = _env("PGDATABASE", "databricks_postgres")
PGPORT = _env("PGPORT", "5432")
PGSSLMODE = _env("PGSSLMODE", "require")
# The endpoint resource path is needed to generate a database credential via the SDK.
LAKEBASE_ENDPOINT = _env(
    "LAKEBASE_ENDPOINT",
    "projects/mke-po-actions/branches/production/endpoints/primary",
)

def host_url() -> str:
    """Workspace URL, normalized to https:// (the React app's #1 bug was a scheme-less host)."""
    h = _env("DATABRICKS_HOST", "adb-4482605715640778.18.azuredatabricks.net")
    if h and not h.startswith(("http://", "https://")):
        h = "https://" + h
    return h.rstrip("/")

# ---- the 10-verb action vocabulary (ported 1:1 from the React CockpitPage) ----
# key, label, direction (+1 adds supply, -1 removes, 0 neutral), tone
ACTIONS = [
    ("EXPEDITE", "Expedite", 1, "good"),
    ("PULL_IN", "Pull in", 1, "good"),
    ("NEW_PO", "New PO", 1, "good"),
    ("INCREASE_QTY", "Increase", 1, "good"),
    ("DECREASE_QTY", "Decrease", -1, "warn"),
    ("PUSH_OUT", "Push out", -1, "warn"),
    ("CANCEL", "Cancel", -1, "bad"),
    ("WAIT_HOLD", "Wait / hold", 0, "warn"),
    ("FIX_SUPPLIER", "Fix supplier", 1, "good"),
    ("REVIEW", "Review", 0, "neutral"),
]
ACTION_KEYS = [a[0] for a in ACTIONS]
ACTION_DIR = {a[0]: a[2] for a in ACTIONS}

GUARDRAIL_NOTE = (
    "Writes go to Lakebase (audit trail) + a SIMULATED Oracle push — no real external "
    "call. prod_edw / prod_operations are read-only. Decision captured for MLflow eval."
)
