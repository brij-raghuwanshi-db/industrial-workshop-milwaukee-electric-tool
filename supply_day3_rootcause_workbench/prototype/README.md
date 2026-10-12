# Supply Root-Cause Workbench — HTML visual spec

Clickable prototype of the **designed** product (UX v1–v3 + Leo’s day-in-the-life), not the four-tab AppKit app that shipped.

## Open

Open `index.html` in a browser (double-click, or from this folder):

```bash
open index.html
```

No build step. No warehouse connection. Demo writes stay in the page session.

## What to click first

1. **Play Leo’s day** (mast) — 8:00 worklist → 16:45 value, through the root-cause trials.
2. Or jump via the mast: Worklist · Case · Coming risk · Constraints · Excess · Rebalance · Bias · Portfolio · Heatmap · Log · Ledger · Value.
3. On a case file: click **Demand / Supply / Holds** stations → **Insert into escalation** → **Draft escalation** → **Send**.
4. Recommended bar: **TRANSFER** (increments the 🔵 ledger), **DISMISS** (⚪ not-acted), lost-battle **ALLOCATE** (🟥 never in savings).
5. **Ask** opens the Genie rail (identity + generated SQL + disclaimer).

## Data contract

| Chip | Meaning |
|---|---|
| `VALIDATED` | IDs and figures from Day-3 live probes (`day_in_the_life`, V1–V26, scenarios) |
| `CATALOG_ID` | Real Milwaukee `item` IDs from the 1,560-ID catalog; some measures filled to fit the scenario |
| `DEMO_FALLBACK` | Structural cells the docs never published (some PO digits, sparkline points) |

Hero cases: **3697-22** ($6.98M, HD 251 vs 150, transfer from 2013), **296720** (DISMISS), **345020** (unrecoverable), **2941-21Z** (catalog), **273421** / **290920** (excess), **Techtronic 3,035**.

## Files

- `index.html` — shell
- `css/workbench.css` — industrial case-file visual system
- `js/data.js` — seeded data
- `js/app.js` — routing, drawers, modals, tour, ledger

Production rebuild of `mke-rc-workbench` should match this information architecture, not the current four-page dashboard.
