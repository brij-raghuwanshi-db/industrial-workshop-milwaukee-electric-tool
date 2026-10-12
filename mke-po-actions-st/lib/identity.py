"""On-behalf-of planner identity from the Databricks Apps forwarded headers.

Deployed apps forward the signed-in user's identity; we stamp it as `approved_by` on
every action — the same OBO attribution the React app does via x-forwarded-email.
"""
from __future__ import annotations
import streamlit as st


def planner_email() -> str:
    try:
        h = st.context.headers or {}
    except Exception:
        h = {}
    for key in ("x-forwarded-email", "x-forwarded-preferred-username", "x-forwarded-user"):
        v = h.get(key)
        if v:
            return v
    return "local-dev@databricks.com"
