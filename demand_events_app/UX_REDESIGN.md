# Demand Events App — UX Redesign & Component Plan (for sign-off)

**Status:** Design proposal. No code yet. Written after honest critique that v1 "feels like filling a form, worse than Excel."
**Method:** `databricks-app-design` skill (genre → compose → notation → bind to real AppKit components → states).
**Binds to:** live AppKit component surface confirmed this session (`DataTable`, `Table`, `Input`, `Calendar`, `Slider`, `Tabs`, `HoverCard`, `Badge`, `Skeleton`, `Empty`, `Alert`, `Card*`, `Select`, `ToggleGroup`, `Popover`).
**App is already deployed & wired** (Lakebase + analytics); this changes the *client* surface + adds read queries. Backend routes largely stand.

---

## 0. The core problem being fixed

v1 built the **plumbing** (Lakebase state, audit, lock, bulk ops, disaggregation math, publish+ack) but shipped a **form + read-only 12-row preview** as the UI. That is a database CRUD screen, not a planner's workbench. It threw away Excel's one real strength — **the grid** (see hundreds of item×month cells, paste, fill, eyeball totals) — while keeping form friction. Result: worse than the spreadsheet it replaces.

**Design intent:** keep Excel's grid; add the things Excel *can't* do (multi-customer, disaggregation, baseline context, audit, lock, submit-acknowledgement) layered *onto* the grid, not replacing it.

---

## 1. Frame

- **Audience:** ~4 demand planners (named on the call), spreadsheet-fluent, work from sales/marketing item lists.
- **Primary task:** *populate and adjust an event's values across item × customer (mkedg5) × month — seeing the whole shape at once — then submit with confidence it landed.*
- **Decision it supports:** "what incremental demand am I adding/removing, for whom, when — and how does it sit against baseline?"
- **Refresh cadence:** baseline reads are as-of ~6AM daily (Oracle export); event edits are live in Lakebase.
- **Device:** desktop, wide screen (grid-first). No mobile priority.

## 2. Genre

**Analytic workbench with an editable grid** (not static form, not dashboard). Per `dashboard-patterns.md`: analytic genre, **stratified layout** (assumptions/summary on top → editable grid as hero → context rail), **detail-on-demand** for provenance/audit, **filter-and-focus** for the events browser.

---

## 3. Information architecture (3 surfaces, replacing today's Events/BulkEdit forms)

```
┌─ Events Browser ───────────────────────────────────────────────┐
│ DataTable over in-app + pulled-in expansion_* events            │
│ search/filter/sort/paginate · status chips · "open" / "adjust"  │
│ bulk-select → bulk actions bar (status / close / lift)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ open
┌─ Event Workspace (THE HERO) ─▼──────────────────────────────────┐
│ Header/assumptions bar (stores, load/store, ASPV, %lift, org,   │
│   tags, type)   ·   lock badge   ·   status control   ·  Publish │
├─────────────────────────────────────────────────────────────────┤
│ Toolbar: [+ items paste] [+ customers] [Disaggregate ▸] [Fill ▾] │
│          measure: planner_baseline ▾   |  show baseline: on/off  │
├─────────────────────────────────────────────────────────────────┤
│ EDITABLE GRID   rows = item × mkedg5   cols = months             │
│   • editable unit cells (signed), baseline shown faint beneath   │
│   • sticky first cols (item, mkedg5) + sticky header (months)    │
│   • sticky TOTALS row + per-row totals col                       │
│   • paste-from-Excel, fill-down, keyboard nav                    │
│   • per-cell provenance dot (direct/builder/disaggregated/ovr)   │
├──────────────────────────────┬──────────────────────────────────┤
│                              │ Context rail:                     │
│                              │  • Event total vs baseline (Δ, %) │
│                              │  • Day-over-day delta (vs last    │
│                              │    publish) — the wanted report   │
│                              │  • Validation warnings (n) + list │
│                              │  • Audit feed (who/what/when)     │
└──────────────────────────────┴──────────────────────────────────┘
┌─ Forecast Builder (Sheet/drawer over the workspace) ────────────┐
│ stores × load-per-store → non-repeating on start month          │
│ stores × ASPV → repeating spread across months                  │
│ preview → "push to grid" (override-protected)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. The hero: editable value grid (design + honest constraint)

**AppKit ships NO editable data-grid primitive.** Confirmed: `DataTable` (read, query-driven, auto columns, filter/sort/paginate) and `Table` (structured primitive) exist; neither is cell-editable. So the editable grid is a **composite we build**: `Table` markup + controlled `Input`/contentEditable cells + a local edit model, committing changed cells to `POST /api/events/:id/cells` (debounced/batched).

**What it must do (Excel parity + more):**
| Capability | How |
|---|---|
| See the whole shape | `Table`; sticky header (months) + sticky first cols (item, mkedg5); virtualized rows if large |
| Edit a cell | controlled `Input` (numeric, **signed**) per cell; Enter/Tab/arrow nav |
| Paste from Excel | paste handler on grid → parse TSV clipboard → map to item×mkedg5×month → batch upsert |
| Fill down / across | selection + `Fill` toolbar action |
| Totals | sticky totals row + per-row total col (client-computed, labeled) |
| Baseline context | faint secondary number under each cell (`--muted-foreground`); toggle on/off; the requirements' "baseline comparison" |
| Provenance | tiny `Badge`/dot: DIRECT / BUILDER / DISAGGREGATED / OVERRIDE (`HoverCard` explains) |
| Negatives | rendered with `--destructive` token + a legend ("negative = reduce forecast") |

**Risk & tradeoff:** a full editable grid is the biggest build item. Mitigation — ship it in two steps: (4a) render the grid **read/whole-shape + single-cell edit + totals + baseline** first (kills "can't see records"); (4b) add paste/fill/multi-select next. Both are real progress; 4a alone already beats the form.

---

## 5. Component plan (every element → a real AppKit primitive)

| Element | Component (published) | Data / props | Token | States |
|---|---|---|---|---|
| Events browser | **`DataTable`** | `queryKey="events_browser"`, `filterColumn`, `pageSize` | status→semantic badges | built-in loading/empty/error |
| Bulk actions bar | `ToggleGroup`+`Button`+`Select` | selection → `POST /api/bulk-edit` | `--primary` | disabled until selection |
| Event header/assumptions | `Card`+`Field`+`Input`+`Select`+`Slider` | stores, load/store, ASPV, %lift, org, type | `--foreground` | inline validation |
| Lock indicator | `Badge` + `Button` | `POST/DELETE /api/events/:id/lock` | `--warning` when locked by other | 409-locked handling |
| Status control | `ToggleGroup` (4 states) | bulk-edit SET_STATUS | semantic per state | busy/disabled |
| **Editable grid** | **composite: `Table` + `Input`** | cells ← `event_cells` read; commit → `/cells` | `--foreground`/`--destructive`/`--muted-foreground` | `Skeleton`/`Empty`/`Alert` |
| Baseline underlay | text in cell | `queryKey="event_baseline"` (planner_baseline by item×mkedg5×month) | `--muted-foreground` | freshness note "as of 6AM" |
| Disaggregate | `Button`+`Popover` (measure/amount) | `POST /api/events/:id/disaggregate` + diff preview | `--primary` | preview before commit |
| Forecast Builder | `Sheet` + `Field`/`Input` | computes → push to grid | `--primary` | override-protect warning |
| Item paste | `Sheet`+`Textarea` | parse → `/items`; validation via `queryKey="validate_items"` | warnings `--warning` | WARN list, non-blocking |
| Customer picker | `Sheet`+`Table`+`Checkbox` | `queryKey="customer_hierarchy"`; level `Select` | — | search/empty |
| Total vs baseline | composite `Card` (KPI) | client agg + baseline query | Δ good/bad semantic | freshness |
| **Day-over-day delta** | composite `Card`+`BarChart` | `queryKey="publish_delta"` (publish_history) | diverging palette | empty until first publish |
| Validation summary | `Card`+list+`Badge` | validate_items WARN count | `--warning` | zero-state ok |
| Audit feed | `Table`/list | `GET /api/events/:id/audit` | `--muted-foreground` | empty ok |
| Publish | `Button`+`AlertDialog`+ack `Alert` | `POST /api/publish` | `--success` on ack | confirm→ack→history |

**New read queries to add** (`config/queries/`, READ-ONLY prod_edw / sandbox):
- `events_browser.sql` — union of in-app events + pulled-in `expansion_*` summaries (for the DataTable).
- `event_baseline.sql` — `planner_baseline` by item × mkedg5 × month for the open event (grid underlay + total).
- `publish_delta.sql` — day-over-day from `sandbox…demand_events_publish_history`.

## 6. Notation (IBCS/`ibcs-notation.md`)
- **Message-in-title** on context cards ("Event adds 10,000 u; +2.5% over baseline"), not bare numbers.
- **Scenario marks:** actual/event = solid `--foreground`; baseline = faint `--muted-foreground` (comparison); no green-is-good on neutral movement.
- **Semantic color via tokens only** — replace v1's raw `bg-green-600`/`text-red-600` with `--success`/`--destructive`/`--warning`. (v1 color-rule violation, fixed here.)
- **Honest scales** on the delta chart; label percentage-points vs percent.
- **Freshness/source** on every baseline-derived number ("planner_baseline, as of ~6AM").

## 7. Required states (non-negotiable, mostly missing in v1)
Every view: **loading → `Skeleton`**, **empty → `Empty` + next action**, **error → `Alert`/inline**, **partial/stale → show + freshness note**. Grid: per-cell save state (saving/saved/failed). Publish: confirm → durable ack → appears in history.

---

## 8. Scope & sequencing (so this doesn't become a horizontal rebuild)

**Wave 1 — kill "worse than Excel" (the hero):**
1. Event Workspace shell (header bar + status + lock).
2. **Editable grid 4a**: whole-shape render + single-cell edit + totals + **baseline underlay** + provenance + semantic tokens + states.
3. Disaggregate action wired into the grid (with preview).

**Wave 2 — Excel-parity + context:**
4. Grid 4b: paste-from-Excel, fill, multi-select.
5. Context rail: total-vs-baseline, day-over-day delta, validation summary, audit feed.
6. Item-paste + customer-picker sheets.

**Wave 3 — browse & builder:**
7. Events Browser (`DataTable`) incl. pulled-in `expansion_*`.
8. Forecast Builder sheet.

Each wave is independently demoable. Wave 1 alone makes it a workbench, not a form.

## 9. What I deliberately will NOT do
- Not hand-roll SVG/canvas grids or an external data-grid lib — compose on `Table`/`Input` per the AppKit rule (no inventing components).
- Not add store/regional granularity, promo, NPD (out of scope, per call).
- Not build all three waves before showing you Wave 1.
- Not use raw hex/Tailwind colors — semantic tokens only.

## 10. Decisions (locked with user, 2026-09-01)
1. **Grid depth:** ✅ **single-cell edit first** in Wave 1; paste-from-Excel in Wave 2.
2. **First surface:** ✅ **the editable grid** (the hero/spine).
3. **Baseline underlay measure:** ✅ **`planner_baseline`** (faint beneath each cell).
4. **Existing events:** ✅ **pull in the 1,462 `expansion_*` events** to open & adjust — so Wave 1 needs the
   normalize/seed pass (Excel-serial→date, tranche aggregation, dash-normalize) into Lakebase, and the
   Events Browser is **promoted into Wave 1** (planners must find a real event to open into the grid).

### Wave 1 — FINAL scope (build target)
- **Seed job/route:** normalize + import `expansion_*` → `demand_events` (event, event_customer, event_item,
  event_cell with source='SEED') so the grid opens real events. One-time/idempotent.
- **Events Browser** (`DataTable`, `events_browser.sql`): search/filter/sort/paginate real + in-app events;
  open → workspace.
- **Event Workspace shell:** header/assumptions bar + status control + lock badge + Publish.
- **Editable grid 4a** (composite `Table`+`Input`): whole-shape (item×mkedg5 rows × month cols),
  single-cell signed edit committing to `/cells`, sticky totals row/col, **`planner_baseline` underlay**
  (`event_baseline.sql`, freshness note), provenance dots, negatives via `--destructive`, semantic tokens,
  full `Skeleton`/`Empty`/`Alert` states + per-cell save state.
- **Disaggregate** action wired into the grid with a preview-before-commit.

Deferred to Wave 2/3 (unchanged): paste/fill/multi-select, context rail (total-vs-baseline card,
day-over-day delta chart, validation summary, audit feed), item-paste & customer-picker sheets, Forecast
Builder drawer.
