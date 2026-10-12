# Project structure — the file tree + the lib/pages split

Streamlit multipage app. **One `lib/` module per concern; thin `pages/`.** The `pages/` are UI only;
all data/logic lives in `lib/` so it's testable and the SQL is verifiable in isolation. This mirrors the
"separate the plumbing from the screen" discipline that made the real build reproducible.

```
my-app/
  app.py                     # entry: page config, sidebar/nav, one-time bootstrap, guardrail note
  pages/
    1_First.py               # Streamlit auto-orders by the numeric prefix; "_"→space in the nav label
    2_Second.py
    ...
  lib/
    __init__.py
    config.py                # ALL env resolution + resource ids + constants (verbs, guardrails). No logic.
    lakebase.py              # psycopg + OAuth token cache/refresh; query()/execute()/Tx()/capabilities()
    warehouse.py             # databricks-sql-connector; run_sql() for ai_forecast / Delta reads
    serving.py               # llm() one-shot + rules_*() deterministic + stream_words() generator
    identity.py              # OBO email from st.context.headers
    domain.py                # read functions — every query the pages need (verbatim, verified SQL)
    actions.py               # write path — propose/execute(ONE txn)/reject + decision capture
    schema.py                # (if app-managed mirrors) idempotent DDL + copy-from-source bootstrap
    theme.py                 # money()/num() formatting, semantic colors, shared chart helpers
  app.yaml                   # runtime: shell-wrapped streamlit command + env valueFrom resources
  databricks.yml             # DAB: app + resources (+ sync.exclude for .venv)
  requirements.txt           # pinned deps
  .gitignore                 # .venv/, __pycache__/, *.pyc
  .streamlit/config.toml     # theme + server.headless (optional but nice)
  README.md                  # what it does + the ownership/separation matrix + deploy commands
```

## Why this split (each rule earned)
- **`config.py` is pure declaration** — env with sensible bundle-default fallbacks so `streamlit run`
  works locally with a profile, and the deployed app reads injected `valueFrom` values. Put the org
  filter, action verbs, catalog/schema names, guardrail text here. No DB calls.
- **`lakebase.py` owns ALL connection state** — the token cache, refresh, retry, transaction ctx. Pages
  and `domain.py` never touch psycopg directly. This is where the hard connectivity lessons live once.
- **`domain.py` = one function per read route.** Copy the SQL verbatim from a known-good source and
  verify each against the real backend before wiring a page to it. Return plain `list[dict]`.
- **`actions.py` = the write path, transactional.** `propose()` inserts (status='proposed'); `execute()`
  runs the ONE transaction (status→executed, OBO approver, audit append, SIMULATED outbox+ack, decision
  capture); `reject()` flips to rejected. Nothing else writes.
- **`serving.py` keeps rules + LLM side by side.** `rules_explain(facts)` is the guaranteed answer;
  `llm(...)` is the enhancement; the page picks via an engine toggle and falls back on error.
- **Pages are thin.** A page fetches via `domain`/`actions`, lays out widgets, and calls `st.rerun()`
  after a write. No SQL, no connection code, no business math in a page.

## Streamlit multipage mechanics
- Files in `pages/` become nav entries automatically, ordered by the leading number; `_` → space.
- `app.py` is the landing page. Put `st.set_page_config(...)` at the top of `app.py` AND each page.
- Use `@st.cache_resource` for the one-time bootstrap (schema create / mirror copy) and for a shared
  `WorkspaceClient()`; use `@st.cache_data(ttl=...)` for read results you want memoized between reruns.
- `st.session_state` holds per-session UI state (selected row, streamed explanation, chosen engine).

## Scaffolding
The `databricks apps init` scaffolder is AppKit/Node-oriented. For Streamlit, **copy this skill's
`templates/` tree** instead — it's a complete, correct minimal app. Rename, drop in your
fully-qualified names + SQL, add pages. Don't hand-write `app.yaml`/`databricks.yml` from memory; start
from the templates (the shell-wrapped command + `sync.exclude` + resource blocks are the parts that are
easy to get wrong).
