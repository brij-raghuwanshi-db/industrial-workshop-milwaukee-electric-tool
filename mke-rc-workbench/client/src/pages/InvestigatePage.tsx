import { useNavigate } from 'react-router';
import { useAnalyticsQuery, Skeleton } from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { useStore } from '../lib/store';
import { Prov, VerdictStamp, RecovStamp, CritStamp, LifecycleStamp, Stamp, num } from '../lib/workbench';

// Forward position curve (PAB vs SS by week) — live from the serving layer, any SKU.
function PositionChart({ rows }: { rows: Array<{ projected_available_balance: unknown; safety_stock: unknown }> }) {
  const pts = rows.map((r) => Number(r.projected_available_balance));
  const ss = rows.length ? Number(rows[0].safety_stock) : 0;
  if (!pts.length) return <div className="wb-ghostnote">No forward path at this snapshot.</div>;
  const W = 480, H = 120, pad = 6;
  const all = [...pts, ss];
  const min = Math.min(...all), max = Math.max(...all);
  const rng = max - min || 1;
  const x = (i: number) => pad + (i / Math.max(1, pts.length - 1)) * (W - 2 * pad);
  const y = (v: number) => H - pad - ((v - min) / rng) * (H - 2 * pad);
  const path = pts.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const ssY = y(ss).toFixed(1);
  return (
    <div className="wb-chart">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        <line x1={pad} y1={ssY} x2={W - pad} y2={ssY} stroke="#6f6a60" strokeDasharray="4 3" />
        <path d={path} fill="none" stroke="#161513" strokeWidth={2} />
      </svg>
    </div>
  );
}

export function InvestigatePage() {
  const { sku, evidence, addEvidence, highlight } = useStore();
  const navigate = useNavigate();

  // Everything on this page is live for the selected SKU.
  const metaq = useAnalyticsQuery('hero_meta', { item_id: sql.string(sku) });
  const posq = useAnalyticsQuery('hero_waterfall', { item_id: sql.string(sku) });
  const splitq = useAnalyticsQuery('hero_split', { item_id: sql.string(sku) });
  const evq = useAnalyticsQuery('case_evidence', { item_id: sql.string(sku) });

  const loading = metaq.loading || evq.loading;
  const m = metaq.data?.[0];
  const ev = evq.data?.[0];
  const split = splitq.data?.[0];
  const pos = posq.data ?? [];

  if (loading) return <div className="wb-lede"><Skeleton className="h-8" style={{ width: 280, marginBottom: 10 }} /><Skeleton className="h-24" /></div>;
  if (!m && !ev) return <div className="wb-lede">No live record for {sku} at this snapshot. Return to the <button className="wb-linkbtn" onClick={() => navigate('/')}>worklist</button>.</div>;

  const verdict = String(m?.action_verdict ?? 'WATCH');
  const recov = String(m?.recoverability_class ?? 'RECOVERABLE');
  const crit = String(m?.criticality_class ?? 'UNCLASSIFIED');
  const lifecycle = String(m?.lifecycle_class ?? 'mature');
  const temporal = String(m?.temporal_class ?? 'acute');
  const likely = String(ev?.likely_cause ?? m?.likely_cause ?? 'Supply');
  const dollars = 0; // committed$ per-SKU is on the spine; headline $ lives on the worklist row
  const locked = recov === 'UNRECOVERABLE';
  const dismiss = verdict === 'DISMISS' && !locked;
  const twoTone = highlight === 'twotone';

  // Live waterfall from rc_snapshot_history at the SKU's worst week (fallback: derive from spine position).
  const worstPab = pos.length ? Math.min(...pos.map((r) => Number(r.projected_available_balance))) : 0;
  const ssAtLt = split ? Number(split.ss_at_lt) : (pos.length ? Number(pos[0].safety_stock) : 0);
  const gap = split ? Number(split.gap) : Math.round(worstPab - ssAtLt);
  const consumption = split ? Number(split.consumption) : 0;
  const targetRefresh = split ? Number(split.target_refresh) : 0;
  const shortfall = ev ? Number(ev.shortfall_units) : Math.max(0, -gap);
  const holdsUnits = ev ? Number(ev.recent_holds) : 0;
  const demandPressure = ev ? Number(ev.demand_pressure_units) : 0;
  const tot = Math.max(Math.abs(ssAtLt), Math.abs(gap), 1);
  const w = (n: number) => Math.max(4, (Math.abs(n) / tot) * 100);

  // Trial stations from the live cause split (demand pressure / supply shortfall / holds).
  const stations = [
    { cause: 'Demand', units: demandPressure, tag: 'DERIVED from plan split' },
    { cause: 'Supply', units: shortfall, tag: 'shortfall at low point' },
    { cause: 'Holds', units: holdsUnits, tag: 'recent hold events' },
  ];

  const insertEvidence = (cause: string) => {
    const line = cause === 'Demand'
      ? `Demand pressure ${num(demandPressure)}u (DERIVED from plan demand-vs-supply split)`
      : cause === 'Supply'
      ? `Shortfall ${num(shortfall)}u below safety stock at the low point (${likely})`
      : `${num(holdsUnits)} recent hold events${ev?.max_hold_lag_hrs != null ? `, max lag ${num(ev.max_hold_lag_hrs)}h` : ''}`;
    addEvidence({ cause, text: line });
  };

  // Recommended playbook derived from the live classifier verdict + recoverability.
  const recommended = locked
    ? [
        { rank: 1, action: 'ALLOCATE scarce supply', detail: 'committed customers first — inside the lead-time fence' },
        { rank: 2, action: 'Notify affected customers early', detail: 'damage control, not an expedite' },
        { rank: 3, action: 'Log as committed loss', detail: 'then full RCA to prevent recurrence' },
      ]
    : dismiss
    ? [{ rank: 1, action: 'DISMISS + close flag', detail: 'below target but PAB stays positive — safety stock is doing its job' }]
    : [
        { rank: 1, action: 'Check in-network transfer', detail: 'cover the short org from an excess org before buying' },
        { rank: 2, action: 'Request supplier pull-in', detail: 'if a PO is in flight and lead time allows' },
        { rank: 3, action: 'Flag residual to demand', detail: 're-baseline the over-consuming channel' },
      ];

  return (
    <div className="wb-case">
      <div>
        <div className="wb-filehead">
          <div className="wb-crumbs"><button onClick={() => navigate('/')}>‹ Worklist</button> · Case file · live</div>
          <div className="wb-stamps">
            <VerdictStamp verdict={verdict} recov={recov} />
            <RecovStamp recov={recov} />
            <Stamp kind="demand">{temporal}</Stamp>
            <CritStamp crit={crit} />
            <LifecycleStamp life={lifecycle} />
            <Prov tier="VALIDATED" />
          </div>
          <p className="wb-kicker">{sku} · likely cause: {likely}{shortfall ? ` · ${num(shortfall)}u short at low point` : ''}</p>
          <p className="wb-finding">
            {sku} carries live classifier tags from the serving layer: <strong>{verdict}</strong> · {recov.toLowerCase()} · {temporal}.
            {targetRefresh > 0 && ` Note: ${num(targetRefresh)}u of the gap is the safety-stock target refreshing on higher demand, not a physical drop.`}
          </p>
        </div>

        <div className="wb-trial">
          {stations.map((t, i) => (
            <div className="wb-station" key={t.cause} data-cause={t.cause} onClick={() => insertEvidence(t.cause)}>
              <div className="n">Trial {i + 1}{t.cause === 'Demand' ? ' · most likely' : t.cause === 'Holds' ? ' · long tail' : ''}</div>
              <h3>{t.cause}</h3>
              <div className="st">{num(t.units)}u · {t.tag}</div>
              <div className="bar" />
            </div>
          ))}
        </div>

        <div className="wb-split">
          <div className="wb-exhibit">
            <h3>Exhibit — waterfall from SS @ lead time <Prov tier={split ? 'VALIDATED' : 'SYNTHETIC_MEASURE'} /></h3>
            {split ? (
              <div className="wb-wf">
                <div className="wb-wfrow"><span>SS @ LT</span><div className="wb-wftrack"><div className="wb-wffill ss" style={{ width: '100%' }} /></div><span className="num">{num(ssAtLt)}</span></div>
                <div className={`wb-wfrow ${twoTone ? 'twotone' : ''}`}><span>Target refresh</span><div className="wb-wftrack"><div className="wb-wffill refresh" style={{ width: `${w(targetRefresh)}%` }} /></div><span className="num">{targetRefresh >= 0 ? '+' : ''}{num(targetRefresh)}</span></div>
                <div className="wb-wfrow"><span>Consumption</span><div className="wb-wftrack"><div className="wb-wffill demand" style={{ width: `${w(consumption)}%` }} /></div><span className="num">{num(consumption)}</span></div>
                <div className="wb-wfrow"><span>Gap vs SS</span><div className="wb-wftrack"><div className="wb-wffill gap" style={{ width: `${w(gap)}%` }} /></div><span className="num">{num(gap)}</span></div>
              </div>
            ) : (
              <p className="wb-ghostnote">No prior-vintage decomposition for this SKU (needs two plan snapshots). Showing shortfall {num(shortfall)}u vs SS {num(ssAtLt)} from the current snapshot.</p>
            )}
            {targetRefresh > 0 && <div className="wb-callout"><strong>DK-12 trap.</strong> +{num(targetRefresh)}u of this gap is the safety-stock <em>target</em> refreshing on higher demand — not a physical drop. Do not over-buy the full gap.</div>}
            {dismiss && <div className="wb-callout"><strong>Do nothing.</strong> Below target but PAB stays positive. Close the flag with evidence.</div>}
            {locked && <div className="wb-callout"><strong>Unrecoverable.</strong> Breach inside the lead-time fence. Do not expedite a PO. Damage control: allocate / notify / log.</div>}
          </div>
          <div className="wb-exhibit">
            <h3>Position over time · SS dashed <Prov tier="VALIDATED" /></h3>
            <PositionChart rows={pos} />
            <p className="wb-ghostnote">Dashed = safety stock. Solid = pooled network position (worst PAB per week). Live from rc_serving_sku_week.</p>
            <div className="wb-livecase">
              <h4>Live evidence <Prov tier="VALIDATED" /></h4>
              {ev ? (
                <ul>
                  <li><strong>Likely cause:</strong> {likely}</li>
                  <li><strong>Shortfall:</strong> {num(shortfall)}u{crit !== 'UNCLASSIFIED' ? ` · crit ${crit}` : ''}</li>
                  <li><strong>Recent holds:</strong> {num(holdsUnits)}{ev.max_hold_lag_hrs != null ? ` · max lag ${num(ev.max_hold_lag_hrs)}h` : ''}</li>
                  <li><strong>Demand pressure:</strong> {num(demandPressure)}u <Prov tier="SYNTHETIC_MEASURE" /> (DERIVED from plan split)</li>
                </ul>
              ) : <span className="wb-ghostnote">This SKU isn’t in the flagged book — no case evidence rows.</span>}
            </div>
            <div className="wb-honesty">
              <span className="s">Classifier + shortfall — live spine</span>
              <span className="r">Holds — live recency</span>
              <span className="n">PO who-moved: sentinel originals, absent</span>
            </div>
          </div>
        </div>

        <div className="wb-recbar" style={highlight === 'recommend' ? { outline: '2px solid #e8b4ae' } : undefined}>
          <h3>Recommended — verdict-gated playbook <Prov tier="VALIDATED" /></h3>
          {recommended.map((r) => (
            <div className="wb-recitem" key={r.rank}>
              <span className="rk">{r.rank}</span>
              <div><strong>{r.action}</strong><div style={{ opacity: 0.75, fontSize: 12 }}>{r.detail}</div></div>
              <RecButton sku={sku} action={r.action} recov={recov} verdict={verdict} dollars={dollars} />
            </div>
          ))}
        </div>
      </div>

      <aside className="wb-locker">
        <h3>Evidence locker · the letter</h3>
        {evidence.length === 0
          ? <div className="empty">Empty. Click a trial station — Demand, then Supply, then Holds — to insert what belongs in the two-bullet letter.</div>
          : evidence.map((e, i) => <div className="wb-lockitem" key={i}><div className="c">{e.cause}</div>{e.text}</div>)}
        <button className="wb-go" onClick={() => { navigate('/escalation'); }}>Draft escalation</button>
      </aside>
    </div>
  );
}

function RecButton({ sku, action, recov, verdict, dollars }: { sku: string; action: string; recov: string; verdict: string; dollars: number }) {
  const { applyAction } = useStore();
  const kind = recov === 'UNRECOVERABLE' ? 'allocate' : verdict === 'DISMISS' ? 'dismiss' : 'transfer';
  const delta = Math.round(dollars * 0.3);
  return <button onClick={() => applyAction(kind, sku, action, delta)}>Do this</button>;
}
