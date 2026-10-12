# 05 — Frontend

React 18 SPA (Vite build, `react-router-dom`, `recharts`), served as static assets by the Express
backend with an SPA catch-all. A left sidebar navigates pages; a right-hand **chat dock** (or
full-page chat) is available on every page. The defining behavior is the **`dataMutated` live-refresh
cascade** — the moment the agent's write commits, data-bearing views refetch and visibly update.

## Page inventory

| Route | Page | Purpose | Backing |
|-------|------|---------|---------|
| `/` | **Home** | Narrative landing: persona badge, headline + situation + goal, journey diagram, starter chips (click → opens chat with that question), featured-action card, activity feed, KPI snapshot | `config/app.json` + `/api/kpis`, `/api/capacity`, `/api/actions`, `/api/records?risk_band=critical` |
| `/panel` | **Record Panel** | The core operator surface: KPI cards ($-exposure / open items / critical count), a risk × recency **scatter** (or map), an at-risk **queue table** with filters + full-text **search box**, a **detail drawer** (record tab, ranked actions with Approve/Override, activity timeline) | Lakebase via `/api/records`, `/api/records/:id`, `/api/kpis`, `/api/search`, `/api/actions` |
| `/analytics` | **Analytics** | Warehouse-backed charts: risk trend on the affected cohort, worst records, per-category risk mix, action mix; + a **unit-economics P&L** (cumulative savings vs cost, ROI, outcomes) | `/api/analytics/:q`, `/api/value/summary|trend|ledger` |
| `/dashboard` | **Dashboard / Workflows** | Embedded **AI/BI dashboard** iframe (SSO) AND/OR a workflow pipeline view (triggers, action status pipeline, staff alerts) | iframe + `/api/dashboard-data` |
| `/ops` | **Ops** (optional) | Platform/architecture map + a live **app health score** (Lakebase latency, sync freshness, search index, workflow freshness, gateway) + AI-spend/value summary | `/api/health-score`, `/api/ops-health`, `/api/value/summary` |
| `/beds`, `/schedule` | **Operational sub-domains** (optional) | Domain-specific interactive grids (occupancy, provider schedule booking, AI-predicted needs) — every mutating action records a value-ledger event | `/api/beds*`, `/api/schedule*` |

## The chat surface

Two form factors, one brain (same `/api/chat/stream` endpoint):
- **Floating dock** — a right-hand panel toggled from the sidebar; used for quick questions from any
  page.
- **Full-page chat** — richer view with conversation list, thinking panel, feedback row.

Chat behaviors to implement:
- **Streaming render.** Open `POST /api/chat/stream`, read the SSE stream, append tokens to a
  placeholder assistant message as they arrive. Fall back to non-streaming `POST /api/chat` if the
  stream fails silently (no tokens but tool events seen).
- **Thinking panel.** Render tool calls / reasoning / sub-agent activity live ("🔧 Calling
  rank_actions…", Genie investigation narration). Persist as `thinking[]` JSONB so reload shows
  "▸ Reasoning · N tools".
- **Inline approval affordances.** When the assistant's last message asks for confirmation, render
  action buttons under it — **Approve** / **Try Different** / **Compare** / **Skip** — each of which
  sends a canned follow-up ("Yes, approve the action for X", "Compare all options for X"). Extract
  the record id from the message text to target the buttons.
- **Starter chips.** From `config/app.json` `starter_chips` — clicking one opens the dock and sends
  that question.
- **Feedback row.** Thumbs up/down under each assistant message → `POST /api/feedback` → MLflow
  assessment; carries the `trace_id` for a "View trace" deep-link.
- **Abort.** A Stop button aborts the fetch (server binds `res` `'close'` to abort the agent run).

## The live-cascade bus (`lib/events.ts`)

A tiny event emitter is the spine of the "watch it update live" moment:

```ts
// lib/events.ts — a minimal typed emitter (or just window CustomEvents)
export const dataMutated = { emit() { window.dispatchEvent(new Event('dataMutated')); } };
```

- **Producer:** the chat turn emits `dataMutated` on turn-end **when the write landed** (the SSE
  `done` event carries `dataMutated: true`, or the agent-stream sets it). Panel/UI action buttons
  that write also emit it.
- **Consumers:** every data-bearing view subscribes and refetches:

```tsx
useEffect(() => {
  const loadAll = () => { fetch('/api/kpis')...; fetch('/api/records?risk_band=critical')...; };
  loadAll();
  const interval = setInterval(loadAll, 15000);         // gentle poll as a backstop
  window.addEventListener('dataMutated', loadAll);       // instant on write
  return () => { clearInterval(interval); window.removeEventListener('dataMutated', loadAll); };
}, []);
```

Result: on approval → the at-risk KPI ticks down, the record row flips to "action assigned" with a
badge, the scatter dot turns neutral, the exposure KPI drops, the drawer's Activity tab gains the
recorded action — **no reload**. If the cascade doesn't fire, verify `dataMutated.emit()` runs on
turn-end and the write actually committed.

## Charts (Recharts)

- KPI tiles: change + verb + $ (an operational screen shows *what changed and what to do*, not just
  levels). Use `usePulseOnChange` to flash a tile when its value moves.
- Trends: `AreaChart`/`LineChart` (cumulative savings vs cost); mix: `BarChart`/`PieChart` with a
  fixed status/severity/risk color map; worst-N tables.
- Wrap in `ResponsiveContainer`. Keep a shared color map (`critical:#E5484D`, `elevated/watch:#FFB020`,
  `stable:#3C6997`, action-status colors) so every surface reads consistently.

## Theming

Drive brand from `config/app.json` `theme` (primary/accent/warning/critical/success/text/background).
Inject as CSS variables or pass to components. Keep semantic colors (risk band, action status)
consistent across the queue, scatter, KPIs, and charts.

## SPA serving

The Express server serves the Vite build (`dist/client`) statically with a catch-all
(`app.get('*', → index.html)`) for client-side routing. If the build is missing, return a 503 with a
clear "client build failed" message rather than a blank page.
