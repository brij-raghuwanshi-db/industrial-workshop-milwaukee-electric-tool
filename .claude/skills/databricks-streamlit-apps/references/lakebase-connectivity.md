# Lakebase connectivity (the hardest part — get this right first)

Lakebase is serverless Postgres. From a Streamlit app you connect with **`psycopg` (v3)**, and the
password is a **short-lived Databricks OAuth token**, not a static secret. This is the single most
error-prone piece; the template `lib/lakebase.py` has it correct — copy it.

## The connection facts
- **host** — the endpoint DNS host, e.g. `ep-...-.database.<region>.azuredatabricks.net` (env `PGHOST`,
  or from `databricks postgres get-endpoint <endpoint-path>` → `.status.hosts.host`). NO port in it.
- **dbname** — usually `databricks_postgres` (env `PGDATABASE`).
- **user** — the identity the token is minted for: the app's **SP client id** when deployed, or the
  current user id locally (`WorkspaceClient().current_user.me().user_name`).
- **password** — a fresh OAuth token (below). **SSL required** (`sslmode=require`).
- **endpoint resource path** — `projects/<proj>/branches/<branch>/endpoints/<ep>` — needed to MINT the
  token (env `LAKEBASE_ENDPOINT`, injected via the `postgres` resource's `valueFrom`).

## Minting + caching the token (the core discipline)
Tokens expire after ~1h. Cache ~55 min; refresh on expiry and whenever a connection drops.

```python
import time, threading, psycopg
from databricks.sdk import WorkspaceClient

_LOCK = threading.Lock(); _conn=None; _token=None; _exp=0.0; _user=None
TTL = 55*60

def _mint():
    w = WorkspaceClient()                       # SP when deployed, profile locally
    # SDK surface varies by version; the CLI-equivalent REST call always works:
    raw = w.api_client.do("POST",
        f"/api/2.0/postgres/{ENDPOINT_PATH}:generateDatabaseCredential")
    tok = raw.get("token")
    uid = w.current_user.me().user_name
    return tok, uid

def _ensure(force=False):
    global _token,_exp,_user
    if not force and _token and time.time() < _exp: return
    _token,_user = _mint(); _exp = time.time()+TTL

def _open():
    _ensure()
    return psycopg.connect(host=PGHOST, dbname=PGDATABASE, port=5432, user=_user,
        password=_token, sslmode="require", autocommit=True, connect_timeout=15,
        options=f"-c search_path={SCHEMA},public")

def query(sql, params=None):
    for attempt in (1,2):
        try:
            conn = _get_conn(force_new=(attempt==2))
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return list(cur.fetchall()) if cur.description else []
        except (psycopg.OperationalError, psycopg.InterfaceError):
            if attempt==2: raise
            _ensure(force=True)                 # token likely expired → refresh + reconnect
```
- `_get_conn(force_new)` is a guarded singleton that reopens on `force_new` or if `conn.closed`.
- `autocommit=True` for reads/one-shot writes; use an explicit transaction object (below) for multi-stmt writes.
- **Parameterize** with `%s` (psycopg), never string-format user input. Escape a literal `%` as `%%`.

## Transactions (multi-statement writes)
Wrap the write path — status flip + audit + outbox + result — in ONE transaction so it's atomic:

```python
class Tx:
    def __enter__(self):
        self.conn=_get_conn(); self.conn.autocommit=False
        self.cur=self.conn.cursor(row_factory=psycopg.rows.dict_row); return self.cur
    def __exit__(self, et, e, tb):
        (self.conn.commit() if et is None else self.conn.rollback())
        self.cur.close(); self.conn.autocommit=True; return False
# usage:  with Tx() as cur: cur.execute(...); cur.execute(...)
```

## Search capability detection (FTS → trigram → ILIKE)
Lakebase supports Postgres full-text (`to_tsvector`/`websearch_to_tsquery`/`ts_rank`) and `pg_trgm`
fuzzy. BM25 (`tsquery_bm25`) is usually NOT provisioned. Detect at boot, degrade gracefully:
```sql
-- FTS (best): generated tsvector column + GIN index, then
WHERE search_tsv @@ websearch_to_tsquery('simple', %s) ORDER BY ts_rank(...) DESC
-- trigram (fuzzy): CREATE EXTENSION pg_trgm; GIN gin_trgm_ops; WHERE col % %s ORDER BY similarity(...)
-- ILIKE (always works): WHERE col ILIKE '%%'||%s||'%%'
```
Detect: `search_tsv` column present? `pg_trgm` in `pg_extension`? Fall through in that order.

## Owning / forking a schema (SP ownership + independence)
The app SP has `CAN_CONNECT_AND_CREATE` — it can create new objects but **cannot read a schema someone
else owns** unless granted. Two clean setups:

**A — app owns its schema (default).** Deploy first; the app's startup creates its schema + tables, so
the SP owns them. Local dev after that works because you can be granted `databricks_superuser`.

**B — fork an existing schema (independent copy of another app's).** Structure-clone + copy data +
grant the SP explicitly (run as project owner via psql):
```sql
CREATE SCHEMA IF NOT EXISTS app_new;
CREATE TABLE app_new.t (LIKE app_src.t INCLUDING ALL);     -- clones cols + generated + indexes + PK
INSERT INTO app_new.t (<cols, skipping GENERATED>) SELECT <cols> FROM app_src.t ON CONFLICT DO NOTHING;
GRANT USAGE ON SCHEMA app_new TO "<sp-client-id>";
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE ON ALL TABLES IN SCHEMA app_new TO "<sp-client-id>";
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA app_new TO "<sp-client-id>";
ALTER DEFAULT PRIVILEGES IN SCHEMA app_new GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO "<sp-client-id>";
```
`LIKE … INCLUDING ALL` carries the generated `search_tsv` + FTS/trigram indexes + PK in one step — the
cleanest way to fork a schema so two apps are write-independent. Prove independence: write a row to the
new schema, confirm it's absent in the source; delete it.

## Run SQL against Lakebase from the shell (for verification)
```bash
EP=projects/<proj>/branches/<branch>/endpoints/<ep>
HOST=$(databricks postgres get-endpoint $EP --profile <p> -o json | jq -r .status.hosts.host)
TOK=$(databricks postgres generate-database-credential $EP --profile <p> -o json | jq -r .token)
ME=$(databricks current-user me --profile <p> -o json | jq -r .userName)
PGPASSWORD="$TOK" psql "host=$HOST user=$ME dbname=databricks_postgres sslmode=require" -c "SELECT 1"
# (macOS: brew install libpq → /opt/homebrew/opt/libpq/bin/psql)
```

## The `postgres` resource (app.yaml / databricks.yml)
```yaml
# databricks.yml resource
- name: postgres
  postgres:
    branch:   projects/<proj>/branches/<branch>
    database: projects/<proj>/branches/<branch>/databases/<db>
    permission: CAN_CONNECT_AND_CREATE
# app.yaml env — the endpoint path is injected here:
- name: LAKEBASE_ENDPOINT
  valueFrom: postgres
```
