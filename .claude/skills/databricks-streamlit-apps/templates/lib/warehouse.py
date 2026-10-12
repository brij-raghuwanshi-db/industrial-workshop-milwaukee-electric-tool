"""SQL Warehouse access (Delta reads, aggregations, ai_forecast) via databricks-sql-connector.

The SP authenticates automatically in a deployed app via the SDK Config credential provider.
Use this for heavy read-only compute; use Lakebase for sub-second interactive reads.
"""
from __future__ import annotations
from typing import Any

from databricks import sql as dbsql
from databricks.sdk.core import Config

from lib import config


def run_sql(sql: str) -> list[dict[str, Any]]:
    """Run a read-only statement on the warehouse; return dict rows. [] on failure (degrade, don't crash)."""
    try:
        cfg = Config()  # SP when deployed, profile locally
        with dbsql.connect(
            server_hostname=config.host_url().replace("https://", ""),
            http_path=f"/sql/1.0/warehouses/{config.WAREHOUSE_ID}",
            credentials_provider=lambda: cfg.authenticate,
        ) as conn, conn.cursor() as cur:
            cur.execute(sql)
            cols = [c[0] for c in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []
