"""Cockpit — the core operational surface (the see→explain→act loop).

Queue ranked by $ at risk → click a row → AI analysis streams in (LLM/Rules/Auto) with a
recommendation → forecast + what-if → decision capture → Approve & execute (Lakebase write +
audit + SIMULATED Oracle). KPIs + queue refresh on rerun after an action (the live cascade).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import domain, actions, serving, config
from lib.theme import money, num, TONE_COLOR, BLUE, RED

st.set_page_config(page_title="Cockpit · MKE PO Actions", page_icon="🎯", layout="wide")


@st.cache_resource
def _caps():
    from lib import lakebase
    return lakebase.capabilities()


def _kpi_row():
    k = domain.kpis()
    base = k.get("base") or {}
    act = k.get("actioned") or {}
    total = float(base.get("total_stockout_risk_usd") or 0)
    resolved = float(act.get("resolved_usd") or 0)
    remaining = total - resolved
    pct = round(100 * resolved / total) if total else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stockout items", num(base.get("total_stockout_items")),
              f"{act.get('resolved_items') or 0} actioned", delta_color="off")
    c2.metric("$ at risk remaining", money(remaining), f"{pct}% resolved", delta_color="off")
    c3.metric("Chronic-supplier", num(base.get("chronic_supplier_items")),
              "systemic — fix source", delta_color="off")
    c4.metric("Planners affected", num(base.get("distinct_planners")),
              "route the work", delta_color="off")
    st.progress(min(100, pct) / 100.0, text=f"${resolved:,.0f} resolved of ${total:,.0f}")


def _forecast_chart(item_id: str):
    fc = domain.forecast(item_id)
    rows = fc.get("forecast") or []
    if not rows:
        st.caption("Forecast unavailable — heuristic trend.")
        return
    df = pd.DataFrame(rows)
    for col in ("y_forecast", "y_lower", "y_upper"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ds"], y=df["y_upper"], line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=df["ds"], y=df["y_lower"], fill="tonexty",
                             fillcolor="rgba(34,114,180,0.12)", line=dict(width=0),
                             name="range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=df["ds"], y=df["y_forecast"], line=dict(color=BLUE, width=2),
                             name="forecast on-hand"))
    ss = fc.get("safety_stock")
    if ss is not None:
        fig.add_hline(y=float(ss), line=dict(color=RED, dash="dash"),
                      annotation_text="safety stock", annotation_position="top left")
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)


@st.dialog("Item analysis & action", width="large")
def _detail(row: dict):
    item_id = row["item_id"]
    st.markdown(f"### {item_id}")
    st.caption(row.get("item_description") or "")
    chips = st.columns(6)
    chips[0].metric("ABC", row.get("abc") or "—")
    chips[1].metric("$ at risk", money(row.get("stockout_risk_usd")))
    chips[2].metric("Gap (u)", num(row.get("stockout_gap_units")))
    chips[3].metric("On-hand", num(row.get("actual_end_on_hand")))
    chips[4].metric("Safety stock", num(row.get("planned_safety_stock")))
    chips[5].metric("Chronic", "yes" if row.get("is_chronic") == 1 else "no")

    facts = domain.facts(item_id)
    if not facts:
        st.error("Item facts unavailable.")
        return

    # ---- AI analysis (both engines, live-streaming) ----
    st.markdown("#### ✨ AI analysis")
    engine = st.radio("engine", ["Auto", "LLM", "Rules"], horizontal=True,
                      label_visibility="collapsed", key=f"eng_{item_id}")
    eng = engine.lower()
    state_key = f"explain_{item_id}_{eng}"
    if state_key not in st.session_state or st.button("↻ Re-run live", key=f"rerun_{item_id}"):
        with st.spinner(f"Analyzing ({engine})…"):
            result = serving.explain(facts, engine=eng)
        # live-typing render
        holder = st.empty()
        acc = ""
        for tok in serving.stream_words(result["explanation"]):
            acc += tok
            holder.markdown(acc + " ▌")
        holder.markdown(acc)
        st.session_state[state_key] = result
    result = st.session_state[state_key]
    src = result.get("source")
    st.markdown(result["explanation"])
    rec_action = result.get("recommended_action")
    rec_qty = result.get("recommended_qty")
    badge = f"**Recommends: `{rec_action}`**"
    if rec_qty is not None:
        badge += f" · {round(float(rec_qty)):,} u"
    if result.get("confidence"):
        badge += f" · confidence: {result['confidence']}"
    st.success(badge + f"  \n_{result.get('reason','')}_  · engine: **{src}**")

    # ---- forecast ----
    st.markdown("#### 📈 On-hand forecast vs safety stock")
    _forecast_chart(item_id)

    # ---- action + what-if ----
    st.markdown("#### 🔧 Choose an action — what-if simulates the effect on cover")
    default_ix = config.ACTION_KEYS.index(rec_action) if rec_action in config.ACTION_KEYS else 0
    labels = [f"{k} · {lbl}" for (k, lbl, *_ ) in config.ACTIONS]
    chosen_label = st.selectbox("action", labels, index=default_ix,
                                label_visibility="collapsed", key=f"act_{item_id}")
    chosen = chosen_label.split(" · ")[0]
    wi = domain.whatif(item_id, chosen, qty=None)
    if not wi.get("error"):
        breach = wi.get("simulated_breaches_ss")
        base_min, sim_min = num(wi["baseline_min_onhand"]), num(wi["simulated_min_onhand"])
        floor = num(wi["safety_stock_floor"])
        msg = (f"**What-if: {wi['action']} · {num(wi['simulated_units'])} u** — projected min on-hand "
               f"{base_min} → **{sim_min}** (floor {floor}) · exposure Δ {money(wi['exposure_delta_usd'])}")
        (st.error if breach else st.success)(
            ("⚠ still breaches safety stock  \n" if breach else "✓ clears safety stock  \n") + msg
        )

    # ---- decision capture ----
    st.markdown("#### ✅ Decision")
    d1, d2 = st.columns(2)
    final_qty = d1.text_input("Final quantity (override the rec)",
                              value=str(round(float(rec_qty))) if rec_qty is not None else "",
                              key=f"fq_{item_id}")
    reason = d2.text_input("Reason if changed", placeholder="why 100 → 75?", key=f"rsn_{item_id}")

    if st.button(f"✓ Approve & execute {chosen}", type="primary", use_container_width=True,
                 key=f"approve_{item_id}"):
        try:
            fq = float(final_qty) if final_qty.strip() else (float(rec_qty) if rec_qty is not None else None)
            prop = actions.propose(item_id, chosen, drafted_note=f"Planner-approved {chosen}",
                                   requested_qty=fq, decision_mode="order")
            actions.execute(prop["id"], reason=reason or None,
                            recommended_action=rec_action, recommended_qty=rec_qty,
                            final_action=chosen, final_qty=fq,
                            forecast_context={"engine": src, "confidence": result.get("confidence")})
            st.session_state["flash"] = f"Executed {chosen} on {item_id} — written to Lakebase + SIMULATED Oracle."
            st.rerun()
        except Exception as e:
            st.error(f"Execute failed: {e}")
    st.caption(config.GUARDRAIL_NOTE)


# ============================= page body =============================
st.title("🎯 Stockout Action Cockpit")
st.caption("Org 2012 · below-safety-stock items · ranked by $ at risk · act, forecast, and commit — live.")

if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"), icon="✅")

_kpi_row()
st.divider()

# search
scol, rcol = st.columns([3, 1])
q = scol.text_input("Search item id or description", placeholder="M18 battery, 48111…",
                    label_visibility="collapsed")
if rcol.button("↻ Reset demo", use_container_width=True):
    try:
        actions.reset_demo()
        st.session_state["flash"] = "Demo reset — actions cleared."
        st.rerun()
    except Exception as e:
        st.error(f"Reset failed: {e}")

# queue (or search results)
if q.strip():
    res = domain.search(q, _caps())
    rows = res["rows"]
    st.caption(f"Search · “{q}” · {len(rows)} items · mode: **{res['mode']}**")
    # search rows are lean; refetch full queue rows for those ids for the detail dialog
    full = {r["item_id"]: r for r in domain.queue(400)}
    rows = [full.get(r["item_id"], r) for r in rows]
else:
    rows = domain.queue(200)

if not rows:
    st.info("No items in the queue. (If this is unexpected, the Lakebase mirrors may be empty.)")
    st.stop()

# ---- explicit, unmistakable way to open the detail (row-select in st.dataframe is subtle:
#      it needs the left checkbox, and a plain cell-click does nothing). A picker + button always works. ----
by_id = {r["item_id"]: r for r in rows}
labels = {
    r["item_id"]: f"{r['item_id']} · {(r.get('item_description') or '')[:38]} · "
                  f"{money(r.get('stockout_risk_usd'))} at risk"
    for r in rows
}
st.markdown("#### Act on an item")
pick_col, btn_col = st.columns([4, 1])
chosen_id = pick_col.selectbox(
    "Pick an item to analyze", options=list(by_id.keys()),
    format_func=lambda i: labels.get(i, i), label_visibility="collapsed", key="pick_item",
)
open_clicked = btn_col.button("Analyze ▸", type="primary", use_container_width=True)

st.caption(f"Action queue · {len(rows)} items · pick above and hit **Analyze ▸**, "
           f"or tick a row's checkbox, to open AI analysis + recommended action.")

# render the queue table; ticking a row's checkbox ALSO opens the detail (bonus path)
df = pd.DataFrame(rows)
disp = pd.DataFrame({
    "Item": df["item_id"],
    "Description": df.get("item_description"),
    "ABC": df.get("abc"),
    "Gap (u)": df.get("stockout_gap_units"),
    "$ at risk": df.get("stockout_risk_usd"),
    "Chronic": df.get("is_chronic").map({1: "chronic", 0: "ok"}) if "is_chronic" in df else "",
    "Planner": df.get("planner_name"),
    "Status": df.get("action_status").fillna("open") if "action_status" in df else "open",
})
event = st.dataframe(
    disp, use_container_width=True, hide_index=True, height=460,
    on_select="rerun", selection_mode="single-row",
    column_config={
        "$ at risk": st.column_config.NumberColumn(format="$%d"),
        "Gap (u)": st.column_config.NumberColumn(format="%d"),
    },
)
sel = event.selection.rows if event and event.selection else []
# open the detail from EITHER path: the button, or a ticked row.
if open_clicked and chosen_id in by_id:
    _detail(by_id[chosen_id])
elif sel:
    _detail(rows[sel[0]])
