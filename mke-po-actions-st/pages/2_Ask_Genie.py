"""Ask (Genie) — natural-language Q&A over the SDP gold tables.

Uses the SDK Genie conversation API: start-conversation → poll to terminal → render the
text answer + the generated SQL's result table. Same Genie space the React app links to.
"""
import time
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient

from lib import config

st.set_page_config(page_title="Ask (Genie) · MKE PO Actions", page_icon="💬", layout="wide")
st.title("💬 Ask the data (Genie)")
st.caption("Natural-language questions over the SDP plan-vs-actual tables. Genie writes the SQL, "
           "runs it on the warehouse, and pins the answer to the underlying records.")

STARTERS = [
    "Which items are furthest below safety stock at org 2012, ranked by dollars at risk?",
    "How many chronic-supplier items are there and what is their total exposure?",
    "What is the plan accuracy (MAPE) and bias for org 2012 vs 2120?",
    "Show the top 10 planners by dollars at risk.",
]


@st.cache_resource
def _w():
    return WorkspaceClient()


def _ask(question: str):
    w = _w()
    conv = w.genie.start_conversation(space_id=config.GENIE_SPACE_ID, content=question)
    conv_id = conv.conversation_id
    msg_id = conv.message_id
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}
    status = None
    for _ in range(150):  # ~5 min budget @ 2s
        m = w.genie.get_message(space_id=config.GENIE_SPACE_ID,
                                conversation_id=conv_id, message_id=msg_id)
        status = str(getattr(m, "status", "") or "")
        if any(t in status for t in terminal):
            break
        time.sleep(2)
    return w, conv_id, msg_id, m, status


def _render(w, conv_id, msg_id, m, status):
    if "FAILED" in status or "CANCELLED" in status:
        err = getattr(m, "error", None)
        st.error(f"Genie could not answer ({status}). {getattr(err, 'error', '') if err else ''}")
        return
    attachments = getattr(m, "attachments", None) or []
    answered = False
    for att in attachments:
        text = getattr(att, "text", None)
        if text and getattr(text, "content", None):
            st.markdown(text.content)
            answered = True
        query = getattr(att, "query", None)
        if query:
            desc = getattr(query, "description", None)
            if desc:
                st.caption(desc)
            gen_sql = getattr(query, "query", None)
            if gen_sql:
                with st.expander("Generated SQL"):
                    st.code(gen_sql, language="sql")
            try:
                res = w.genie.get_message_attachment_query_result(
                    space_id=config.GENIE_SPACE_ID, conversation_id=conv_id,
                    message_id=msg_id, attachment_id=getattr(att, "attachment_id", None))
                sr = getattr(res, "statement_response", None)
                if sr and sr.result and sr.result.data_array:
                    cols = [c.name for c in sr.manifest.schema.columns]
                    st.dataframe(pd.DataFrame(sr.result.data_array, columns=cols),
                                 use_container_width=True, hide_index=True)
                    answered = True
            except Exception:
                pass
    if not answered:
        st.info("Genie returned no answer content for that question. Try rephrasing.")


if "genie_q" not in st.session_state:
    st.session_state.genie_q = ""

st.write("**Try one:**")
cols = st.columns(2)
for i, s in enumerate(STARTERS):
    if cols[i % 2].button(s, use_container_width=True, key=f"starter_{i}"):
        st.session_state.genie_q = s

q = st.chat_input("Ask about plan vs actual, exposure, chronic suppliers, planners…")
if q:
    st.session_state.genie_q = q

if st.session_state.genie_q:
    st.chat_message("user").write(st.session_state.genie_q)
    with st.chat_message("assistant"):
        with st.spinner("Genie is investigating…"):
            try:
                w, conv_id, msg_id, m, status = _ask(st.session_state.genie_q)
                _render(w, conv_id, msg_id, m, status)
            except Exception as e:
                st.error(f"Genie request failed: {e}")
