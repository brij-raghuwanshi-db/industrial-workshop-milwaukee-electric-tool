"""Scenarios — the playbook. Each situation we uncovered, told as a story with LIVE evidence.

Story → why it matters → the real numbers (pulled live, never hardcoded) → recommended +
probable actions. This is how a new planner learns the business from the app itself.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import domain
from lib.theme import money, BLUE, EMERALD, RED

st.set_page_config(page_title="Scenarios · MKE PO Actions", page_icon="📖", layout="wide")
st.title("📖 Supply Scenarios — the playbook")
st.caption("Every situation we uncovered, told as a story: **what's happening → why it matters → "
           "the live evidence → what to do**. Open a section, see the real numbers, then act in the Cockpit.")


def _mini_table(rows, title):
    st.caption(title)
    if not rows:
        st.info("No data.")
        return
    df = pd.DataFrame(rows)
    show = pd.DataFrame({
        "Item": df["item_id"],
        "Description": df.get("item_description"),
        "Gap (u)": df.get("gap_units"),
        "$ at risk": df.get("dollar"),
    })
    st.dataframe(show, hide_index=True, use_container_width=True,
                 column_config={"$ at risk": st.column_config.NumberColumn(format="$%d"),
                                "Gap (u)": st.column_config.NumberColumn(format="%d")})


def _actions_block(recommended, probable):
    a, b = st.columns(2)
    a.success(f"**Recommended action**  \n{recommended}")
    b.info("**Probable actions**  \n" + " · ".join(probable))


# ---- S0: orientation ----
with st.expander("**Start here** — Why this app exists: insight ≠ action", expanded=True):
    st.markdown(
        "**Story.** The dashboard tells you thousands of items at Olive Branch (org 2012) are below "
        "safety stock — tens of millions in exposure. But a chart can't cancel a PO. Planners still had "
        "to leave the screen and act in Oracle/Excel.")
    st.markdown(
        "**Why it matters.** This app closes the loop: see the ranked queue → ask why → forecast the "
        "future → simulate a what-if → approve → it's recorded with an audit trail and a (simulated) "
        "Oracle push. The dashboard is where you sit; here is where you fly.")
    _actions_block("Go to the Cockpit, open the top item, and walk one action end-to-end.",
                   ["Expedite the below-safety-stock item", "Fix the supplier if chronically late"])

# ---- S5: $ not units ----
with st.expander("**S5 · Prioritization** — Rank by dollars, not units (the $0.01-part trap)"):
    st.markdown(
        "**Story.** A planner naturally sorts by the biggest unit shortfall. But a 50,000-unit gap on a "
        "$0.01 scrap part matters far less than a 500-unit gap on a $500 battery.")
    st.markdown(
        "**Why it matters.** We rank by **$ at risk** = gap × standard cost. Watch how the top-5-by-units "
        "list is almost entirely different items than the top-5-by-dollars.")
    st.markdown("**Live evidence.**")
    data = domain.scenario_cost_vs_units()
    c1, c2 = st.columns(2)
    with c1:
        _mini_table(data["by_dollar"], "Top 5 by $ at risk (correct)")
    with c2:
        _mini_table(data["by_units"], "Top 5 by units (misleading)")
    _actions_block("Always work the queue top-down by $ at risk (the Cockpit default).",
                   ["Expedite the high-$ batteries first", "Ignore high-unit / low-$ scrap items"])

# ---- chronic ----
with st.expander("**Supply signal** — Systemic vs one-off: fix the supplier, don't just expedite"):
    st.markdown(
        "**Story.** Some items miss safety stock because a supplier is chronically late (>60% of the time), "
        "not a one-time hiccup. Expediting the same item every week treats the symptom forever.")
    st.markdown(
        "**Why it matters.** For chronic items the right action is FIX SUPPLIER (a sourcing conversation), "
        "not another expedite.")
    st.markdown("**Live evidence.**")
    ch = domain.scenario_chronic()
    tot = ch.get("total") or {}
    st.markdown(f"Systemic exposure: **{money(tot.get('dollar'))}** across **{tot.get('items', 0)}** items.")
    _mini_table(ch["rows"], "Chronic-supplier items (fix the source)")
    _actions_block("For chronic items, escalate to sourcing; for the rest, expedite.",
                   ["FIX SUPPLIER on chronic items", "EXPEDITE on one-offs"])

# ---- hero ----
with st.expander("**S2 · On-hand & why** — One SKU's story: how it drifted below safety stock"):
    st.markdown(
        "**Story.** Take the single highest-$ item. Its plan said it would be fine; the actuals tell a "
        "different story — receipts stalled, on-hand slid under the safety-stock floor.")
    st.markdown(
        "**Why it matters.** Overlay planned on-hand (PAB) vs actual on-hand vs the safety-stock floor. "
        "When actual crosses below the floor, that's the stockout risk crystallizing.")
    hero = domain.scenario_hero()
    st.markdown(f"**Live evidence.** Hero item: `{hero.get('item_id') or '—'}`")
    rows = hero.get("rows") or []
    if rows:
        df = pd.DataFrame(rows)
        for col in ("planned_pab", "actual_end_on_hand", "planned_safety_stock"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["week_start"], y=df["planned_pab"],
                                 name="planned PAB", line=dict(color=BLUE)))
        fig.add_trace(go.Scatter(x=df["week_start"], y=df["actual_end_on_hand"],
                                 name="actual on-hand", line=dict(color=EMERALD)))
        fig.add_trace(go.Scatter(x=df["week_start"], y=df["planned_safety_stock"],
                                 name="safety stock", line=dict(color=RED, dash="dash")))
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
    _actions_block("Open this SKU in the Cockpit, run the forecast + what-if, then approve the fix.",
                   ["Expedite / pull in the next receipt", "Increase the next order qty if demand is rising"])
