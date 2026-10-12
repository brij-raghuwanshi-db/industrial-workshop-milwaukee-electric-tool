"""MKE PO Action Cockpit — Streamlit twin of the React/AppKit app.

Same job: see off-plan items → ask why (streaming LLM/rules) → forecast/what-if → approve →
write-back (Lakebase audit + SIMULATED Oracle) → analytics + scenarios + Genie. Reads/writes
the SAME Lakebase schema `app_po` the React app uses; both run side-by-side.

This is the landing page; the four surfaces live under pages/ (Streamlit multipage).
"""
import streamlit as st

from lib import config

st.set_page_config(  # noqa: E305
    page_title="MKE PO Action Cockpit (Streamlit)",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource(show_spinner="Preparing this app's data (independent copy of app_po)…")
def _bootstrap():
    """One-time (per session/process): create app_po_st + copy mirror data from app_po."""
    from lib import schema
    try:
        return schema.bootstrap()
    except Exception as e:  # never block the whole app on bootstrap
        return {"error": str(e)}


_boot = _bootstrap()

st.title("🛠️ MKE PO Action Cockpit")
st.caption(
    "Milwaukee Tool · Org 2012 (Olive Branch) · below-safety-stock items — "
    "**see it → ask why → forecast → simulate → approve → it's recorded live.** "
    "A Streamlit twin of the production React app, on the same governed data."
)

st.info(
    "**Only through actions can you fly.** The dashboard shows the fire; this app lets you "
    "put it out — and every move is captured for the feedback loop.",
    icon="🚀",
)

c1, c2, c3, c4 = st.columns(4)
c1.page_link("pages/1_Cockpit.py", label="**Cockpit** — act on the queue", icon="🎯")
c2.page_link("pages/2_Ask_Genie.py", label="**Ask (Genie)** — NL Q&A", icon="💬")
c3.page_link("pages/3_Dashboard.py", label="**Dashboard** — where the $ sits", icon="📊")
c4.page_link("pages/4_Scenarios.py", label="**Scenarios** — the playbook", icon="📖")

st.divider()
left, right = st.columns([2, 1])
with left:
    st.subheader("What this app does")
    st.markdown(
        """
1. **Cockpit** — a queue of below-safety-stock items ranked by **$ at risk**. Click any row and an
   **AI analysis streams in live** (real Claude Sonnet 4.5, or a deterministic rules engine — you choose),
   explaining *why* it's flagged and **recommending an action**.
2. **Forecast + what-if** — `ai_forecast()` projects on-hand forward; simulate an action (expedite, cancel,
   new PO…) and see whether it clears the safety-stock floor and the exposure delta.
3. **Approve & execute** — the human gate. One transaction writes to Lakebase (audit trail), stamps *you* as
   approver, captures your decision vs the recommendation, and fires a **SIMULATED** Oracle push.
4. **Dashboard & Scenarios** — where the exposure sits, and the story behind each pattern, pulled live.
"""
    )
with right:
    st.subheader("Guardrails")
    st.markdown(
        f"""
- `prod_edw` / `prod_operations` — **read-only**.
- Writes → **Lakebase `{config.PG_SCHEMA}`** + `sandbox_operations.po_management`.
- External writeback (Oracle) is **SIMULATED** — never a real call.
- All views scoped to **org {config.ORG}**.
"""
    )
    st.caption(config.GUARDRAIL_NOTE)
