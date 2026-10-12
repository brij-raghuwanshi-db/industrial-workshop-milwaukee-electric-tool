# UI patterns — building the screens in Streamlit idioms

The React/AppKit patterns (queue, KPI tiles, click-a-row drawer, streaming AI, charts, live cascade) all
have clean Streamlit equivalents. This maps them so the next agent doesn't reinvent them.

## Design principles (carry these — they're what make an ops app useful, not just valid)
- **Action, not state.** A tile that says "Exposure: $2.1M" is wallpaper; "$ at risk remaining, 4%
  resolved" with a progress bar provokes a move. Show change + verb + $, not levels.
- **Teach through the UI.** Every chart gets a one-line "what this shows / why it matters" caption. A new
  user should learn the domain from the app itself, not need to already know it.
- **Required states:** loading (spinner while a query/agent runs), empty ("No items — great!" not a blank),
  error (surface the REAL upstream message, not "failed"). Degrade, don't crash.
- **Trust the AI result visibly.** Show which engine produced it (LLM vs rules), the recommendation with
  its confidence + reason, and let the user re-run or override. Never a single un-sourced recommendation.

## KPI tiles
```python
c1,c2,c3,c4 = st.columns(4)
c1.metric("Stockout items", num(k["items"]), f"{k['actioned']} actioned", delta_color="off")
c2.metric("$ at risk remaining", money(remaining), f"{pct}% resolved", delta_color="off")
st.progress(min(100,pct)/100, text=f"{money(resolved)} of {money(total)}")
```
`delta_color="off"` when the sub-text is a label, not a good/bad delta.

## Ranked queue → opening the detail (the React "click a row" gap — READ THIS)
Streamlit has **no whole-row click**. `st.dataframe` row-selection fires only when the user ticks the
**left-edge checkbox**; a normal **cell click just highlights the cell and does nothing** — so a
"click a row" instruction silently fails and the detail never opens (a real bug we shipped and had to
fix). **Give an explicit, unmistakable control, and keep the checkbox as a bonus:**
```python
import pandas as pd
by_id = {r["id"]: r for r in rows}
labels = {r["id"]: f"{r['id']} · {(r.get('desc') or '')[:38]} · {money(r.get('risk'))} at risk" for r in rows}

st.markdown("#### Act on an item")
c1, c2 = st.columns([4, 1])
picked = c1.selectbox("Pick an item", list(by_id), format_func=lambda i: labels.get(i, i),
                      label_visibility="collapsed")
open_clicked = c2.button("Analyze ▸", type="primary", use_container_width=True)
st.caption("Pick above and hit **Analyze ▸**, or tick a row's checkbox, to open the analysis.")

event = st.dataframe(
    df_display, use_container_width=True, hide_index=True, height=460,
    on_select="rerun", selection_mode="single-row",
    column_config={"$ at risk": st.column_config.NumberColumn(format="$%d")},
)
sel = event.selection.rows if event and event.selection else []
if open_clicked and picked in by_id:
    open_detail(by_id[picked])          # primary, always-works path
elif sel:
    open_detail(rows[sel[0]])           # bonus: ticked-checkbox path
```
Keep a parallel list of full row dicts (`rows`); the display DataFrame is only the columns you show.
(Requires Streamlit ≥1.35 for dataframe selections. Alternative to a picker: render a per-row
`st.button` in a `st.columns` layout — reliable but heavier for long lists; the picker+button scales best.)

## Detail panel — `st.dialog` (the "drawer")
```python
@st.dialog("Item analysis & action", width="large")
def open_detail(row):
    ...  # chips, AI analysis, forecast, action verbs, what-if, decision capture, approve
```
A `@st.dialog` is the closest thing to the React side-drawer. Inside it: context chips (`st.columns` +
`st.metric`), then the AI section, forecast, action controls, decision inputs, and the approve button.

## Streaming AI analysis + engine toggle
```python
engine = st.radio("engine", ["Auto","LLM","Rules"], horizontal=True, label_visibility="collapsed")
key = f"explain_{item}_{engine.lower()}"
if key not in st.session_state or st.button("↻ Re-run live"):
    with st.spinner(f"Analyzing ({engine})…"):
        result = serving.explain(facts, engine.lower())   # rules-first w/ fallback
    holder = st.empty(); acc=""
    for tok in serving.stream_words(result["explanation"]):
        acc += tok; holder.markdown(acc + " ▌")            # blinking-cursor effect
    holder.markdown(acc)
    st.session_state[key] = result
result = st.session_state[key]
st.success(f"**Recommends `{result['recommended_action']}`** · conf {result['confidence']} — {result['reason']} · engine: {result['source']}")
```
Persist the finished result in `session_state` so reruns (from other widgets) don't re-stream or blank it.

## Charts — Plotly (ships as a Streamlit dep; reliable)
- Forecast band: `go.Scatter` upper (invisible line) + lower with `fill='tonexty'` (shaded band) + the
  forecast line + `fig.add_hline(y=floor, line=dict(dash='dash'))` for a threshold.
- Bars: `px.bar(df, x=value, y=label, orientation='h')`, `text=[money(v) …]`, `textposition='outside'`.
- Pie: `px.pie(df, names=, values=, hole=0.45)`.
- Pin semantic colors explicitly (`marker_color`, `color_discrete_sequence`) — don't let categories
  color-cycle so a "bad" series never renders as a calm color. (If you were tempted by a native chart
  that won't bind, a Plotly figure you control always renders — the same lesson as the React app's
  custom bars.)

## The live cascade
After a successful write:
```python
actions.execute(...); st.session_state["flash"]="Executed — written to Lakebase + SIMULATED push."
st.rerun()
```
On rerun the KPI row and queue re-query Lakebase and visibly update. Show the flash with
`st.success(st.session_state.pop("flash"))` at the top of the page.

## Scenarios / storytelling page
`st.expander` per scenario: **story → why it matters → live evidence (fetched lazily on open) →
recommended + probable actions**. Never hardcode the evidence — call `domain.*` so the numbers are real.

## Sidebar
Nav is automatic from `pages/`. Put global affordances (a "Reset demo" that truncates writable tables, an
org/scope selector, the guardrail note) in `st.sidebar`.
