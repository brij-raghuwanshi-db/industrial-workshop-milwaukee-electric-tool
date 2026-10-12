"""Central config: env resolution + resource ids + constants. No DB calls here.

Every workspace-specific value comes from env (injected by Databricks Apps via `valueFrom`);
local dev falls back to the bundle defaults so `streamlit run` works with a profile in the env.
"""
from __future__ import annotations
import os


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, "") or "").strip() or default


def host_url() -> str:
    """Workspace URL, normalized to https:// (a scheme-less host is a common bug)."""
    h = _env("DATABRICKS_HOST", "<WORKSPACE-HOST>")
    if h and not h.startswith(("http://", "https://")):
        h = "https://" + h
    return h.rstrip("/")


# ---- resource identifiers (env first, bundle default second) ----
WAREHOUSE_ID = _env("DATABRICKS_WAREHOUSE_ID", "<WAREHOUSE_ID>")
GENIE_SPACE_ID = _env("DATABRICKS_GENIE_SPACE_ID", "<GENIE_SPACE_ID>")
SERVING_ENDPOINT = _env("DATABRICKS_SERVING_ENDPOINT_NAME", "databricks-claude-sonnet-4-5")

# ---- Lakebase ----
PGHOST = _env("PGHOST", "<ENDPOINT_HOST>")
PGDATABASE = _env("PGDATABASE", "databricks_postgres")
PGPORT = _env("PGPORT", "5432")
PGSSLMODE = _env("PGSSLMODE", "require")
LAKEBASE_ENDPOINT = _env("LAKEBASE_ENDPOINT", "projects/<P>/branches/<B>/endpoints/<EP>")
PG_SCHEMA = _env("APP_PG_SCHEMA", "app_schema")

# ---- UC read-only source (only if you read Delta gold via the warehouse) ----
CATALOG_SCHEMA = "<catalog>.<schema>"

GUARDRAIL_NOTE = (
    "Writes go to Lakebase + the approved sandbox schema only. Production is read-only. "
    "External-system writeback is SIMULATED — no real external call."
)
