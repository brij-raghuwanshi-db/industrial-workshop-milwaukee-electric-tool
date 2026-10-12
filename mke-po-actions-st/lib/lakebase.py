"""Lakebase (serverless Postgres) access via psycopg with OAuth-token password.

The gotcha (from the lakebase skill + the React app's hard-won lessons):
- The Postgres password is a short-lived Databricks OAuth token, NOT a static secret.
- Generate it with the SDK (`generate_database_credential`), cache it (~55 min), and
  refresh on expiry or on a 401-style auth failure.
- SSL is required. The Postgres user is the app's service-principal client id (deployed)
  or the current user's id (local dev).

We keep a module-level connection and re-open it when the token is refreshed. Streamlit
reruns are single-threaded per session, so a simple guarded singleton is sufficient here.
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
_token_exp: float = 0.0
_user: str | None = None
TOKEN_TTL = 55 * 60  # refresh a little before the 1-hour expiry


def _workspace() -> WorkspaceClient:
    # In a deployed app the SDK picks up injected SP env vars; locally it uses the profile.
    return WorkspaceClient()


def _fresh_token(w: WorkspaceClient) -> tuple[str, str]:
    """Return (token, pg_username). Username is the SP/user client-id the token is minted for.

    Uses the Lakebase Autoscaling REST call the CLI uses:
      POST /api/2.0/postgres/credentials  body {"endpoint": "<endpoint-path>"}
    (The SDK's w.database.generate_database_credential is the legacy Provisioned API and 404s the
    Autoscaling endpoint path with 'Database instance ... not found' — do NOT use it.)"""
    raw = w.api_client.do(
        "POST", "/api/2.0/postgres/credentials",
        body={"endpoint": config.LAKEBASE_ENDPOINT},
    )
    tok = raw.get("token") if isinstance(raw, dict) else None
    # pg username = the identity the token belongs to (SP client id or user id)
    me = w.current_user.me()
    uid = getattr(me, "user_name", None) or getattr(me, "id", None) or ""
    return tok or "", uid


def _ensure_token(force: bool = False) -> None:
    global _token, _token_exp, _user
    now = time.time()
    if not force and _token and now < _token_exp:
        return
    w = _workspace()
    tok, uid = _fresh_token(w)
    _token = tok
    _user = uid
    _token_exp = now + TOKEN_TTL


def _open() -> psycopg.Connection:
    global _conn
    _ensure_token()
    conn = psycopg.connect(
        host=config.PGHOST,
        dbname=config.PGDATABASE,
        port=int(config.PGPORT),
        user=_user,
        password=_token,
        sslmode=config.PGSSLMODE,
        autocommit=True,
        connect_timeout=15,
        options=f"-c search_path={config.PG_SCHEMA},public",
    )
    return conn


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
    """Run a SELECT (or RETURNING) and return a list of dict rows. Retries once on auth/conn loss."""
    for attempt in (1, 2):
        try:
            conn = _get_conn(force_new=(attempt == 2))
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return []
                return list(cur.fetchall())
        except (psycopg.OperationalError, psycopg.InterfaceError):
            if attempt == 2:
                raise
            _ensure_token(force=True)  # token likely expired → refresh + reconnect
    return []


def execute(sql: str, params: tuple | list | None = None) -> None:
    """Run a non-returning statement."""
    for attempt in (1, 2):
        try:
            conn = _get_conn(force_new=(attempt == 2))
            with conn.cursor() as cur:
                cur.execute(sql, params)
            return
        except (psycopg.OperationalError, psycopg.InterfaceError):
            if attempt == 2:
                raise
            _ensure_token(force=True)


def transaction():
    """Context manager yielding a cursor inside a real transaction (BEGIN/COMMIT/ROLLBACK).

    Usage:
        with lakebase.transaction() as cur:
            cur.execute(...); cur.execute(...)
    Commits on clean exit, rolls back on exception.
    """
    return _Tx()


class _Tx:
    def __enter__(self):
        self.conn = _get_conn()
        self.conn.autocommit = False
        self.cur = self.conn.cursor(row_factory=psycopg.rows.dict_row)
        return self.cur

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.cur.close()
            self.conn.autocommit = True
        return False


def capabilities() -> dict[str, bool]:
    """Detect search capabilities (FTS column + pg_trgm) like the React app does at boot."""
    caps = {"fts": False, "trgm": False}
    try:
        r = query(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name='mirror_exceptions' AND column_name='search_tsv'",
            (config.PG_SCHEMA,),
        )
        caps["fts"] = bool(r)
    except Exception:
        pass
    try:
        r = query("SELECT 1 FROM pg_extension WHERE extname='pg_trgm'")
        caps["trgm"] = bool(r)
    except Exception:
        pass
    return caps
