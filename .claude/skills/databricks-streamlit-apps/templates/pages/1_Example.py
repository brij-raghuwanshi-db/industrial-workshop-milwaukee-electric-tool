"""Example page — the full see -> explain -> act loop in Streamlit idioms.

Demonstrates: KPI tiles, a ranked table with clickable rows (dataframe selection = "click"),
a detail dialog with a streaming rules/LLM explanation + engine toggle, and a write-back that
reruns to cascade the change. Replace the placeholder SQL/logic with your domain's.
"""
import pandas as pd
import streamlit as st

from lib import lakebase, serving, config, identity

st.set_page_config(page_title="Example", page_icon="➡️", layout="wide")


@st.cache_resource
def _caps():
    return lakebase.capabilities()


# ---------- reads (put real queries in a lib/domain.py in a real app) ----------
def queue(limit: int = 200) -> list[dict]:
    return lakebase.query(
        f"SELECT * FROM {config.PG_SCHEMA}.<your_table> ORDER BY <rank_col> DESC LIMIT %s", (limit,)
    )


def kpis() -> dict:
    r = lakebase.query(f"SELECT COUNT(*)::int AS items FROM {config.PG_SCHEMA}.<your_table>")
    return r[0] if r else {}


# ---------- detail dialog: streaming explanation + engine toggle + write-back ----------
@st.dialog("Record analysis & action", width="large")
def detail(row: dict):
    st.markdown(f"### {row.get('<id_col>')}")
    facts = {"id": row.get("<id_col>"), **row}  # shape facts for the explain engine

    engine = st.radio("engine", ["Auto", "LLM", "Rules"], horizontal=True,
                      label_visibility="collapsed", key=f"eng_{facts['id']}")
    key = f"explain_{facts['id']}_{engine.lower()}"
    if key not in st.session_state or st.button("↻ Re-run live", key=f"re_{facts['id']}"):
        with st.spinner(f"Analyzing ({engine})…"):
            result = serving.explain(facts, engine.lower())
        holder = st.empty(); acc = ""
        for tok in serving.stream_words(result["explanation"]):
            acc += tok; holder.markdown(acc + " ▌")
        holder.markdown(acc)
        st.session_state[key] = result
    result = st.session_state[key]
    st.success(f"**Recommends `{result['recommended_action']}`** · {result['confidence']} — "
               f"{result['reason']} · engine: {result['source']}")

    reason = st.text_input("Reason (if overriding)")
    if st.button(f"✓ Approve & execute {result['recommended_action']}", type="primary",
                 use_container_width=True):
        who = identity.user_email()
        with lakebase.Tx() as cur:
            # ONE transaction: flip status, stamp OBO approver, append audit, simulated push, decision capture
            cur.execute(
                f"INSERT INTO {config.PG_SCHEMA}.action_request "
                f"(id,record_id,action_type,status,approved_by,reason) "
                f"VALUES (%s,%s,%s,'executed',%s,%s)",
                (f"act-{facts['id']}", facts["id"], result["recommended_action"], who, reason or None),
            )
            # cur.execute("INSERT INTO ...audit..."); cur.execute("INSERT INTO ...outbox (simulated)...")
        st.session_state["flash"] = f"Executed {result['recommended_action']} on {facts['id']}."
        st.rerun()  # the live cascade — KPIs/queue re-query on rerun
    st.caption(config.GUARDRAIL_NOTE)


# ============================= page body =============================
st.title("➡️ Example worklist")
if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"), icon="✅")

k = kpis()
st.metric("Items", k.get("items", "—"))

rows = queue()
if not rows:
    st.info("No items. (If unexpected, the table may be empty or the query needs your columns.)")
    st.stop()

# Explicit open-detail control. st.dataframe row-select needs the left checkbox (a cell click does
# nothing) — so a picker + button is the reliable primary path; the checkbox is a bonus.
by_id = {r["<id_col>"]: r for r in rows}
st.markdown("#### Act on an item")
c1, c2 = st.columns([4, 1])
picked = c1.selectbox("Pick an item", list(by_id), label_visibility="collapsed")
open_clicked = c2.button("Analyze ▸", type="primary", use_container_width=True)
st.caption("Pick above and hit **Analyze ▸**, or tick a row's checkbox, to open the analysis.")

df = pd.DataFrame(rows)
event = st.dataframe(df, use_container_width=True, hide_index=True, height=460,
                     on_select="rerun", selection_mode="single-row")
sel = event.selection.rows if event and event.selection else []
if open_clicked and picked in by_id:
    detail(by_id[picked])
elif sel:
    detail(rows[sel[0]])
