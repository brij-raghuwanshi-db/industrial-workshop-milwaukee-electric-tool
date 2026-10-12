<div align="center">

# V12 · Do-Nothing / False-Alarm Scenarios — Validation

### When the tool should show the root cause and then recommend **doing nothing** — or **watching, not acting**

</div>

**Why this exists:** a tool that *only* ever says "act" trains planners to distrust it — and the transcript said
so directly: *"if we have in our safety stock some of that variation already covered, then I don't want to
trigger."* The most trust-building output is often **"flagged, but here's why the right move is to do nothing (or
just watch)."** Tested every do-nothing situation I could find, live.

**Key idea — a *three-way* action verdict, not act/ignore:**
```
   ACT            WATCH (do nothing now, but be aware)        DISMISS (do nothing — it's fine)
   real, near-term,   real but not-yet / may self-correct /       cushion doing its job / transient /
   physical risk      target-driven → monitor, don't spend        artifact → close the flag
```

---

## The do-nothing / watch populations (live, next quarter, `20 Global`)

| # | Situation | Count | of what | Verdict |
|---|---|---|---|---|
| **T1** | Flagged **below safety stock but PAB never goes negative** — dips into the cushion and recovers | **7,066** | **66%** of 10,700 below-SS flags | 🟢 **DISMISS** — safety stock is *doing its job* |
| **T2** | Below SS for **only 1 week** of a 14-week horizon (transient blip) | **1,603** | 15% of flags | 🟢 **DISMISS / WATCH** — self-heals next week |
| **T3** | Flagged "worse" but **position didn't drop — the SS target rose** under it (Carter artifact) | **420** | of 4,982 currently-below | 🟡 **WATCH** — physically unchanged; don't buy |
| **T4** | Flagged **excess** but only 5–6 weeks of cover (high demand) — not truly overstocked *(from V7)* | ~2/10 sampled | — | 🟢 **DISMISS** — ×SS false-positive |
| **T5** | Crosses below SS **beyond the ~8-week window** (far-out, may self-correct in later snapshots) | **884** | 8% of flags | 🟡 **WATCH** — too far to act, re-check next snapshot |
| — | **Near-term, physical, act-worthy** | **8,749** *(and of these only 3,634 ever go PAB-negative)* | — | 🔴 **ACT** |

> Put together: of **10,700 "below safety stock" flags, only ~3,634 (34%) ever actually stock out.** A tool that
> shouts "act" on all 10,700 is wrong **two-thirds of the time** — and that's precisely how planners learn to
> ignore an alerting tool.

---

## 📖 The story the data tells

This is the counter-intuitive validation, and it may be the most important one for adoption. The instinct is
that a supply tool exists to find problems and push actions. **The data says the bigger risk is over-flagging.**
Two-thirds of "below safety stock" never becomes a physical shortage — because **that's what safety stock is
for.** The cushion absorbs the dip and the position recovers. Firing an alert (or worse, triggering a buy) on
those 7,066 SKUs would be the tool actively *causing* the over-ordering the transcript explicitly warned
against ("I don't want to trigger").

The three do-nothing reasons are distinct and each needs its own honest label:
- **DISMISS** — the flag is a *false alarm by design*: cushion dip (T1), one-week blip (T2), ×SS-artifact
  excess (T4). The tool should show the root cause **and then close the flag with the evidence** ("dips to 200
  below target wk38, recovers wk39, never negative — no action").
- **WATCH** — the flag is *real but not actionable now*: target-refresh artifact (T3, physically unchanged),
  far-out crossing (T5, beyond lead time / may self-correct). The tool should say **"monitor — re-check next
  snapshot,"** and *remember* it so if it worsens it escalates automatically.
- **ACT** — near-term, physical, within reach. Only ~34% of the flags.

The deepest point: **"do nothing" is a *recommendation*, not an absence of one.** The planner spent nothing, but
the tool did the work — it proved the non-action was correct, with the waterfall/recovery evidence attached. That
is the difference between a tool that saves time and a tool that just generates more queue. And "watch, don't
act" is the honest middle the current binary design has no room for.

## Verdict: 🔴 GAP — the design has no "do-nothing / watch" verdict; it should

Every screen so far implies "here's the problem → act." **There is no explicit *no-action-warranted* or *watch*
state**, yet the data says that's the correct answer for ~66% of shortage flags. This is a capability gap on par
with convergence (V11) — and it's a *trust* gap: without it, the tool cries wolf.

## 🔍 Root causes

| Situation | Root cause of the false/deferrable flag |
|---|---|
| Cushion dip (T1) | "below safety stock" ≠ "stockout" — SS is a buffer *meant* to be dipped into (transcript: "safety stock is an imaginary target") |
| One-week blip (T2) | a single timing mismatch (a receipt one week late) recovers when the next supply lands |
| Target-refresh (T3) | forward-DOC recomputes SS upward on higher demand → "worse" without any physical change (DK-12) |
| ×SS excess (T4) | 3×(small SS) is trivial for a high-demand SKU → false excess (V7) |
| Far-out crossing (T5) | beyond lead time; later snapshots often self-correct as supply/demand firm up |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **three-way action verdict** — `ACT` / `WATCH` / `DISMISS` — to every flagged SKU; make it a serving column (`action_verdict`) | build | 🔴 must (trust) |
| 2 | **DISMISS with evidence**: show the root cause *and* the recovery ("dips to −200 wk38, recovers wk39, never negative") — a closed flag, not a silent drop | build | 🔴 must |
| 3 | **WATCH = deferred + remembered**: monitor, re-check next snapshot, auto-escalate if it worsens (don't lose it) | build | 🔴 must |
| 4 | Gate `ACT` to **near-term + physically-negative PAB (or within tolerance breach)** — not "below target" alone | build | 🔴 must |
| 5 | Track a **"do-nothing / suppressed" count** on the Value page — proving the tool *saved* wasted actions is as valuable as proving it drove them | build | 🟡 should |
| 6 | Confirm the **tolerance band** (how far below SS, for how long, is genuinely OK) with a planner — the DISMISS threshold is a business rule | planner | 🟡 should |

> **Ties to convergence (V11):** the ACT/WATCH/DISMISS verdict + the temporal class (acute/chronic/nervous, V10)
> together tell the planner not just *what's wrong* but *whether it's even theirs to act on now* — the two
> filters that turn a 10,700-row alarm into a ~3,600-row real worklist.

---

## ✅ Logged successful queries

```sql
-- V12 T1: below SS but PAB never negative (cushion dip → DISMISS). READ-ONLY.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
agg AS (SELECT product_bigint_key po, inventory_organization_bigint_key io,
    MIN(projected_available_balance - safety_stock) min_gap, MIN(projected_available_balance) min_pab
  FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0
  GROUP BY 1,2 HAVING MIN(projected_available_balance - safety_stock)<0)
SELECT COUNT(*) flagged_below_ss,
       SUM(CASE WHEN min_pab>=0 THEN 1 ELSE 0 END) never_negative_pab,
       SUM(CASE WHEN min_pab<0 THEN 1 ELSE 0 END) true_stockout,
       ROUND(SUM(CASE WHEN min_pab>=0 THEN 1 ELSE 0 END)/COUNT(*)*100,0) pct_cushion_only
FROM agg;
```
```sql
-- V12 T2: transient (below only 1 week) vs persistent. READ-ONLY.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
perwk AS (SELECT product_bigint_key po, inventory_organization_bigint_key io, date_key,
    MAX(CASE WHEN projected_available_balance<safety_stock THEN 1 ELSE 0 END) below
  FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0 GROUP BY 1,2,3),
agg AS (SELECT po, io, SUM(below) weeks_below, COUNT(*) tot_weeks FROM perwk GROUP BY 1,2 HAVING SUM(below)>0)
SELECT COUNT(*) flagged, SUM(CASE WHEN weeks_below=1 THEN 1 ELSE 0 END) only_one_week,
       SUM(CASE WHEN weeks_below>=tot_weeks*0.8 THEN 1 ELSE 0 END) persistent_80pct,
       ROUND(AVG(weeks_below),1) avg_weeks_below FROM agg;
```
```sql
-- V12 T3: flagged "worse" but position not down — target rose (WATCH, Carter artifact). READ-ONLY.
WITH s2 AS (SELECT DISTINCT process_date FROM prod_edw.fact.`20_supply_daily` ORDER BY process_date DESC LIMIT 8),
b AS (SELECT MAX(process_date) now_pd, MIN(process_date) old_pd FROM s2),
nowd AS (SELECT product_bigint_key po, inventory_organization_bigint_key io, MAX(safety_stock) ss, MAX(projected_available_balance) pab
  FROM prod_edw.fact.`20_supply_daily`,b WHERE process_date=now_pd AND plan_name='20 Global Supply Plan' AND date_key=20261012 AND safety_stock>0 AND projected_available_balance<safety_stock GROUP BY 1,2),
oldd AS (SELECT product_bigint_key po, inventory_organization_bigint_key io, MAX(safety_stock) ss, MAX(projected_available_balance) pab
  FROM prod_edw.fact.`20_supply_daily`,b WHERE process_date=old_pd AND plan_name='20 Global Supply Plan' AND date_key=20261012 AND safety_stock>0 GROUP BY 1,2)
SELECT COUNT(*) now_below,
       SUM(CASE WHEN nowd.pab>=oldd.pab AND nowd.ss>oldd.ss THEN 1 ELSE 0 END) worse_only_due_to_target_rise
FROM nowd JOIN oldd ON nowd.po=oldd.po AND nowd.io=oldd.io;
```
```sql
-- V12 T5: far-out crossing (beyond ~8wk) = WATCH not ACT. READ-ONLY.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
agg AS (SELECT product_bigint_key po, inventory_organization_bigint_key io,
    MIN(CASE WHEN projected_available_balance<safety_stock THEN date_key END) first_cross
  FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0
  GROUP BY 1,2 HAVING MIN(CASE WHEN projected_available_balance<safety_stock THEN date_key END) IS NOT NULL)
SELECT COUNT(*) flagged,
       SUM(CASE WHEN first_cross>20261102 THEN 1 ELSE 0 END) crosses_beyond_8wk_watch,
       SUM(CASE WHEN first_cross<=20261005 THEN 1 ELSE 0 END) near_term_act
FROM agg;
```
