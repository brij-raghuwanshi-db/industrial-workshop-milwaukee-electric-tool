"""Lakebase (serverless Postgres) via psycopg with an OAuth-token password.

Copy this verbatim — the token cache/refresh + retry + transaction context are the parts that are
hard to get right. Password = a short-lived Databricks OAuth token (NOT a static secret): mint via the
SDK, cache ~55 min, refresh on expiry / dropped connection. SSL required. The PG user is the identity
the token is minted for (SP client id when deployed, current user locally).
"""
from __future__ import annotations
import time
import threading
from typing import Any

import psycopg
from databricks.sdk import WorkspaceClient

from lib import config

_LOCK = threading.Lock()
_conn: psycopg.Connection | None = None
_token: str | None = None
_exp: float = 0.0
_user: str | None = None
TTL = 55 * 60  # refresh a little before the ~1h token expiry


def _mint() -> tuple[str, str]:
    w = WorkspaceClient()  # SP when deployed, profile locally
    # Lakebase Autoscaling credential — the exact call the CLI makes.
    # POST /api/2.0/postgres/credentials  body {"endpoint": "<endpoint-path>"}
    # DO NOT use w.database.generate_database_credential — that's the legacy Provisioned API and
    # 404s the Autoscaling endpoint path with "Database instance ... not found".
    raw = w.api_client.do(
        "POST", "/api/2.0/postgres/credentials",
        body={"endpoint": config.LAKEBASE_ENDPOINT},
    )
    tok = raw.get("token") if isinstance(raw, dict) else None
    me = w.current_user.me()
    uid = getattr(me, "user_name", None) or getattr(me, "id", None) or ""
    return tok or "", uid


def _ensure(force: bool = False) -> None:
    global _token, _exp, _user
    if not force and _token and time.time() < _exp:
        return
    _token, _user = _mint()
    _exp = time.time() + TTL


def _open() -> psycopg.Connection:
    _ensure()
    return psycopg.connect(
        host=config.PGHOST, dbname=config.PGDATABASE, port=int(config.PGPORT),
        user=_user, password=_token, sslmode=config.PGSSLMODE,
        autocommit=True, connect_timeout=15,
        options=f"-c search_path={config.PG_SCHEMA},public",
    )


def _get_conn(force_new: bool = False) -> psycopg.Connection:
    global _conn
    with _LOCK:
        if force_new and _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
        if _conn is None or _conn.closed:
            _conn = _open()
        return _conn


def query(sql: str, params: tuple | list | None = None) -> list[dict[str, Any]]:
    """SELECT / RETURNING → list of dict rows. Retries once on auth/connection loss."""
    for attempt in (1, 2):
        try:
            conn = _get_conn(force_new=(attempt == 2))
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return list(cur.fetchall()) if cur.description else []
        except (psycopg.OperationalError, psycopg.InterfaceError):
            if attempt == 2:
                raise
            _ensure(force=True)
    return []


def execute(sql: str, params: tuple | list | None = None) -> None:
    for attempt in (1, 2):
        try:
            conn = _get_conn(force_new=(attempt == 2))
            with conn.cursor() as cur:
                cur.execute(sql, params)
            return
        except (psycopg.OperationalError, psycopg.InterfaceError):
            if attempt == 2:
                raise
            _ensure(force=True)


class Tx:
    """Multi-statement transaction: `with Tx() as cur: cur.execute(...); cur.execute(...)`.
    Commits on clean exit, rolls back on exception."""

    def __enter__(self):
        self.conn = _get_conn()
        self.conn.autocommit = False
        self.cur = self.conn.cursor(row_factory=psycopg.rows.dict_row)
        return self.cur

    def __exit__(self, et, e, tb):
        try:
            self.conn.commit() if et is None else self.conn.rollback()
        finally:
            self.cur.close()
            self.conn.autocommit = True
        return False


def capabilities() -> dict[str, bool]:
    """Detect FTS (search_tsv column) + pg_trgm so search can degrade FTS→trigram→ILIKE."""
    caps = {"fts": False, "trgm": False}
    try:
        caps["fts"] = bool(query(
            "SELECT 1 FROM information_schema.columns WHERE table_schema=%s "
            "AND table_name='<your_search_table>' AND column_name='search_tsv'",
            (config.PG_SCHEMA,),
        ))
    except Exception:
        pass
    try:
        caps["trgm"] = bool(query("SELECT 1 FROM pg_extension WHERE extname='pg_trgm'"))
    except Exception:
        pass
    return caps
