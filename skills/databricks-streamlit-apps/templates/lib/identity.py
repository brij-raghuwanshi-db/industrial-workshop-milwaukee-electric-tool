"""On-behalf-of user identity from Databricks Apps forwarded headers.

Stamp this as approved_by / decided_by on every write so the audit trail is attributable.
"""
from __future__ import annotations
import streamlit as st


def user_email() -> str:
    try:
        h = st.context.headers or {}
    except Exception:
        h = {}
    for key in ("x-forwarded-email", "x-forwarded-preferred-username", "x-forwarded-user"):
        if h.get(key):
            return h[key]
    return "local-dev@example.com"
