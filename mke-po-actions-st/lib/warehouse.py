"""SQL Warehouse access for the ONE thing that needs Delta + Spark SQL: ai_forecast().

Everything else reads Lakebase mirrors. This uses databricks-sql-connector; in a deployed
app the service principal authenticates automatically via the SDK credential provider.
"""
from __future__ import annotations
from typing import Any

from databricks import sql as dbsql
from databricks.sdk.core import Config

from lib import config

_HTTP_PATH = f"/sql/1.0/warehouses/{config.WAREHOUSE_ID}"


def _connect():
    cfg = Config()  # picks up SP creds (deployed) or the profile (local dev)
    return dbsql.connect(
        server_hostname=config.host_url().replace("https://", ""),
        http_path=_HTTP_PATH,
        credentials_provider=lambda: cfg.authenticate,
    )


def run_sql(sql: str) -> list[dict[str, Any]]:
    """Run a read-only SQL statement on the warehouse; return dict rows. Returns [] on failure."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cols = [c[0] for c in cur.description] if cur.description else []
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []
