"""Dashboard — native analytics from the Lakebase mirrors (no catalog dependency).

Where the below-safety-stock exposure sits: by value class, by owner, by supplier type,
by $ band — each with a teaching caption. Live from the action queue; updates as you act.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib import domain
from lib.theme import money, BLUE, VIOLET, CORAL, EMERALD, RED

st.set_page_config(page_title="Dashboard · MKE PO Actions", page_icon="📊", layout="wide")
st.title("📊 Stockout Analytics")
st.caption("Where the below-safety-stock exposure sits — by value class, by owner, and by supplier "
           "type — so you know **where to spend the morning**. Live from the action queue.")

# progress banner
p = domain.progress()
total = float(p.get("total_usd") or 0)
resolved = float(p.get("resolved_usd") or 0)
pct = round(100 * resolved / total) if total else 0
b1, b2 = st.columns([1, 2])
b1.metric("Exposure resolved this session", money(resolved), f"of {money(total)}", delta_color="off")
b2.progress(min(100, pct) / 100.0,
            text=f"{p.get('executed', 0)} of {p.get('total_items', 0)} items actioned · {pct}% of $ resolved")
st.divider()


def _hbar(rows, label_key, val_key, color, title, why):
    st.subheader(title)
    st.caption(why)
    if not rows:
        st.info("No data.")
        return
    df = pd.DataFrame(rows)
    df[val_key] = pd.to_numeric(df[val_key], errors="coerce").fillna(0)
    df = df.sort_values(val_key)
    fig = px.bar(df, x=val_key, y=label_key, orientation="h")
    fig.update_traces(marker_color=color,
                      text=[money(v) for v in df[val_key]], textposition="outside")
    fig.update_layout(height=max(240, 40 * len(df)), margin=dict(l=10, r=40, t=10, b=10),
                      xaxis_title="$ at risk", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)


r1c1, r1c2 = st.columns(2)
with r1c1:
    _hbar(domain.by_abc(), "abc", "dollar_at_risk", BLUE, "$ at risk by ABC class",
          "ABC = value tier (A = the vital few). A-items carry most of the exposure — "
          "focus discipline there first.")
with r1c2:
    st.subheader("Systemic vs one-off exposure")
    st.caption("Chronic-supplier items ($) are a recurring problem — fix the SOURCE, not the symptom. "
               "One-offs just need expediting.")
    cs = domain.chronic_split()
    if cs:
        df = pd.DataFrame(cs)
        df["dollar_at_risk"] = pd.to_numeric(df["dollar_at_risk"], errors="coerce").fillna(0)
        fig = px.pie(df, names="kind", values="dollar_at_risk", hole=0.45,
                     color_discrete_sequence=[BLUE, EMERALD])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

r2c1, r2c2 = st.columns(2)
with r2c1:
    _hbar(domain.by_planner(), "planner", "dollar_at_risk", VIOLET,
          "Who owns the fires — $ at risk by planner",
          "The work has to be routed to a human. This ranks planners by the exposure they own.")
with r2c2:
    _hbar(domain.risk_bands(), "band", "dollar_at_risk", CORAL,
          "Exposure concentration — by $ band",
          "A few huge items usually carry most of the risk (Pareto). Act on the ≥$1M band first.")

st.caption("Our own governed data rendered natively. The full SDP AI/BI dashboard remains in Databricks; "
           "here we surface the action-relevant cuts that update live as you act.")
