"""Entry / landing page for a Streamlit Databricks App.

st.set_page_config must be first. Do any one-time bootstrap here behind @st.cache_resource so it
runs once per process, not per rerun. Pages live under pages/ (auto-added to the nav).
"""
import streamlit as st

from lib import config

st.set_page_config(page_title="My App", page_icon="🛠️", layout="wide",
                   initial_sidebar_state="expanded")


@st.cache_resource(show_spinner="Preparing data…")
def _bootstrap():
    """One-time per process: e.g. create the app's schema / copy read mirrors if empty.
    Return a small status dict; never let bootstrap crash the whole app."""
    # from lib import schema; return schema.bootstrap()
    return {"ok": True}


_boot = _bootstrap()

st.title("🛠️ My App")
st.caption("What this app does, in one line — the workload, the user, the outcome.")

st.info("See it → ask why → act. Only through actions can you move the number.", icon="🚀")

st.subheader("Guardrails")
st.markdown(f"- {config.GUARDRAIL_NOTE}")

st.page_link("pages/1_Example.py", label="Open the Example page", icon="➡️")
