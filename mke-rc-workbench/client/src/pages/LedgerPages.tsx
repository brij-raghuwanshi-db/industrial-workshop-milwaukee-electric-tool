import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { useAnalyticsQuery, Skeleton, Alert, AlertDescription } from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { useStore } from '../lib/store';
import { Prov, usd, num, Stamp } from '../lib/workbench';

const usdOrPending = (v: number | null | undefined) => (v == null ? '—' : usd(v));

function Kpi({ lab, val, meta, cls }: { lab: string; val: string; meta?: string; cls?: string }) {
  return <div className={`wb-kpi ${cls ?? ''}`}><div className="lab">{lab}</div><div className="val">{val}</div>{meta && <div className="meta">{meta}</div>}</div>;
}

// Shared live-table shell: loading / error / empty states around a serving-layer query.
function LiveTable({ loading, error, rows, head, children, source, empty }: {
  loading: boolean; error?: string | null; rows: number;
  head: ReactNode; children: ReactNode; source: string; empty?: string;
}) {
  return (
    <div className="wb-panel">
      <div className="wb-panel-h"><h2>Live rows</h2><span className="wb-prov">{source}</span></div>
      {loading && <div style={{ padding: 14 }}>{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8" style={{ marginBottom: 6 }} />)}</div>}
      {error && <div style={{ padding: 14 }}><Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert></div>}
      {!loading && !error && rows === 0 && <div style={{ padding: 20, color: '#6f6a60' }}>{empty ?? 'No rows at this snapshot.'}</div>}
      {!loading && !error && rows > 0 && (
        <div style={{ maxHeight: 560, overflow: 'auto' }}>
          <table><thead>{head}</thead><tbody>{children}</tbody></table>
        </div>
      )}
    </div>
  );
}

function stateLabel(s?: string): string {
  if (s === 'projected') return '🔵 projected';
  if (s === 'not-acted') return '⚪ not-acted';
  if (s === 'loss-avoided') return '🟥 loss-avoided';
  return s ?? '—';
}

// Feeds the store's baseline from the live value_baseline query (at-risk committed $ this snapshot).
function useLiveBaseline() {
  const { setBaseline } = useStore();
  const q = useAnalyticsQuery('value_baseline', {});
  const b = q.data?.[0];
  useEffect(() => { if (b?.at_risk_dollars != null) setBaseline(Number(b.at_risk_dollars)); }, [b, setBaseline]);
  return b;
}

export function LedgerPage() {
  const { ledger: L, log } = useStore();
  const b = useLiveBaseline();
  const baseTxt = L.baseline == null ? '…' : usd(L.baseline);
  return (
    <div>
      <p className="wb-kicker">Screen G · DK-21</p>
      <h1 className="wb-title">Today froze {baseTxt} at risk. The tape moves only when you act — and stays honest.</h1>
      <p className="wb-lede">Nothing is “saved” at the click — only <strong>projected</strong>. Realized needs a next-snapshot read-back (not published yet, shown as —). Baseline is live from the serving layer. <Prov tier="VALIDATED" /> · interactions persisted in Lakebase.</p>
      <div className="wb-kpirow">
        <Kpi lab="🔵 Projected today" val={usdOrPending(L.projected)} meta="modeled at click" />
        <Kpi lab="✅ Realized this week" val={usdOrPending(L.realized)} meta="read-back — pending 2nd acted snapshot" />
        <Kpi lab="⚪ Correctly not-acted" val={usdOrPending(L.notActed)} meta="DISMISS avoided over-order" cls="quiet" />
        <Kpi lab="🟥 Loss avoided" val={usdOrPending(L.lossAvoided)} meta="unrecoverable — never “saved”" cls="lost" />
        <Kpi lab="Residual risk" val={usdOrPending(L.residual)} meta={`from ${baseTxt} baseline${b?.at_risk_sku_count ? ` · ${num(b.at_risk_sku_count)} SKUs` : ''}`} />
      </div>
      <div className="wb-panel">
        <div className="wb-panel-h"><h2>Action tape</h2><span className="wb-prov">rc_app.action_request (Lakebase)</span></div>
        <table>
          <thead><tr><th>Time</th><th>SKU</th><th>Suggested → actual</th><th>State</th><th className="num">Δ$</th></tr></thead>
          <tbody>
            {log.length === 0
              ? <tr><td colSpan={5} style={{ color: '#6f6a60' }}>No actions logged — baseline {baseTxt} at risk. Open a case and use the recommended playbook.</td></tr>
              : log.map((r, i) => (
                <tr key={i}><td>{r.when}</td><td className="sku">{r.sku}</td><td>{r.suggested} → {r.actual}{r.diverged ? ' (div)' : ''}</td><td>{stateLabel(r.savings_state)}</td><td className="num">{r.delta ? usd(r.delta) : '—'}</td></tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function EscalationPage() {
  const { sku, evidence } = useStore();
  const live = useAnalyticsQuery('case_evidence', { item_id: sql.string(sku) });
  const c = live.data?.[0];
  const shortfall = c ? Number(c.shortfall_units) : null;
  return (
    <div>
      <p className="wb-kicker">Escalation · structured handoff</p>
      <h1 className="wb-title">The two-bullet letter writes itself from the evidence locker.</h1>
      <div className="wb-letter">
        <h2>Re: {sku}{c?.likely_cause ? ` — ${String(c.likely_cause)} root cause` : ''}</h2>
        <p>Team — {sku} is {shortfall != null ? <><strong>{num(shortfall)}u below safety stock</strong> at its forward low point</> : 'flagged in the current snapshot'}. Root cause and recommended action:</p>
        <ul>
          {evidence.length > 0
            ? evidence.map((e, i) => <li key={i}><strong>{e.cause}:</strong> {e.text}</li>)
            : c
            ? <>
                <li><strong>Likely cause:</strong> {String(c.likely_cause)}</li>
                <li><strong>Holds:</strong> {num(c.recent_holds)} recent events{c.max_hold_lag_hrs != null ? `, max lag ${num(c.max_hold_lag_hrs)}h` : ''}</li>
              </>
            : <li>Open the case file and click the trial stations to build the evidence list.</li>}
        </ul>
        <p>Send routes to a Lakebase action request. <Prov tier="VALIDATED" /> live from rc_case_evidence.</p>
      </div>
    </div>
  );
}

export function ValuePage() {
  const { ledger: L } = useStore();
  const b = useLiveBaseline();
  const { dismiss } = usePortfolio();
  const baseTxt = L.baseline == null ? '…' : usd(L.baseline);
  const unrecov = b?.unrecoverable_dollars != null ? Number(b.unrecoverable_dollars) : null;
  return (
    <div>
      <p className="wb-kicker">Screen F · quantify the stakes</p>
      <h1 className="wb-title">One snapshot, {baseTxt} committed at risk — and {dismiss == null ? '…' : num(dismiss)} times the verdict is correctly “do nothing”.</h1>
      <div className="wb-kpirow">
        <Kpi lab="At-risk committed $" val={baseTxt} meta="flagged book, live baseline" />
        <Kpi lab="Locked-in (unrecoverable)" val={usdOrPending(unrecov)} meta="inside lead-time fence" cls="lost" />
        <Kpi lab="Correctly not-acted" val={dismiss == null ? '…' : num(dismiss)} meta="DISMISS verdicts" cls="quiet" />
        <Kpi lab="Projected this session" val={usdOrPending(L.projected)} meta="modeled at click" />
        <Kpi lab="Realized" val={usdOrPending(L.realized)} meta="pending read-back" />
      </div>
      <div className="wb-exhibit">
        <h3>Stakes ladder — live from the serving layer <Prov tier="VALIDATED" /></h3>
        <div className="wb-wf">
          <div className="wb-wfrow"><span>At risk (committed)</span><div className="wb-wftrack"><div className="wb-wffill refresh" style={{ width: '100%' }} /></div><span className="num">{baseTxt}</span></div>
          <div className="wb-wfrow"><span>Locked-in loss</span><div className="wb-wftrack"><div className="wb-wffill gap" style={{ width: unrecov != null && L.baseline ? `${Math.min(100, Math.round((unrecov / L.baseline) * 100))}%` : '4%' }} /></div><span className="num">{usdOrPending(unrecov)}</span></div>
          <div className="wb-wfrow"><span>Projected saved (session)</span><div className="wb-wftrack"><div className="wb-wffill ss" style={{ width: L.projected && L.baseline ? `${Math.min(100, Math.round((L.projected / L.baseline) * 100))}%` : '4%' }} /></div><span className="num">{usdOrPending(L.projected)}</span></div>
        </div>
        <p className="wb-ghostnote">Realized is intentionally not shown as a number until a two-snapshot read-back exists — the ladder never claims savings early.</p>
      </div>
    </div>
  );
}

// live portfolio headline counts (dismiss etc.), shared by Value + others
function usePortfolio() {
  const q = useAnalyticsQuery('portfolio_headline', {});
  const p = q.data?.[0];
  return {
    dismiss: p?.dismiss_skus == null ? null : Number(p.dismiss_skus),
    excessDollars: p?.excess_dollars == null ? null : Number(p.excess_dollars),
    unrecoverableDollars: p?.unrecoverable_dollars == null ? null : Number(p.unrecoverable_dollars),
    rebalanceRows: p?.rebalance_rows == null ? null : Number(p.rebalance_rows),
  };
}

// ── live scenario lenses — full book from the serving layer ──
export function ExcessPage() {
  const q = useAnalyticsQuery('excess', {});
  const rows = q.data ?? [];
  const { excessDollars } = usePortfolio();
  return (
    <div>
      <p className="wb-kicker">The other half of the book</p>
      <h1 className="wb-title">{excessDollars == null ? '…' : usd(excessDollars)} excess across {num(rows.length)} SKUs.</h1>
      <p className="wb-lede">Value not moving — projected balance parked well above target. <Prov tier="VALIDATED" /> live from the serving layer.</p>
      <LiveTable loading={q.loading} error={q.error} rows={rows.length} source="rc_excess"
        empty="No excess above 3× safety stock at this snapshot."
        head={<tr><th>SKU</th><th className="num">Low PAB</th><th className="num">SS</th><th>Crit</th><th className="num">Surplus</th><th className="num">Weeks cover</th><th>Driver</th><th className="num">$ excess</th></tr>}>
        {rows.map((r) => (
          <tr key={String(r.item_id)}><td className="sku">{String(r.item_id)}</td><td className="num">{num(r.min_pab)}</td><td className="num">{num(r.safety_stock)}</td><td>{String(r.criticality_class)}</td><td className="num">{num(r.surplus_units)}</td><td className="num">{r.weeks_cover == null ? '—' : num(r.weeks_cover)}</td><td>{String(r.driver)}</td><td className="num">{usd(r.dollars as number)}</td></tr>
        ))}
      </LiveTable>
    </div>
  );
}

export function RebalancePage() {
  const q = useAnalyticsQuery('rebalance', {});
  const rows = q.data ?? [];
  return (
    <div>
      <p className="wb-kicker">Transfer before you buy</p>
      <h1 className="wb-title">{num(rows.length)} SKUs are short in one org with in-network cover in another.</h1>
      <p className="wb-lede">Best excess org picked per short SKU. <Prov tier="VALIDATED" /> live from the serving layer.</p>
      <LiveTable loading={q.loading} error={q.error} rows={rows.length} source="rc_rebalance"
        empty="No in-network rebalance opportunities at this snapshot."
        head={<tr><th>SKU</th><th>Short org</th><th className="num">Short</th><th>Excess org</th><th className="num">Excess</th><th className="num">Coverable</th></tr>}>
        {rows.map((r, i) => (
          <tr key={String(r.item_id) + i}><td className="sku">{String(r.item_id)}</td><td>{num(r.short_org)}</td><td className="num">{num(r.short_units)}</td><td>{num(r.excess_org)}</td><td className="num">{num(r.excess_units)}</td><td className="num">{num(r.coverable)} ({num(r.pct_covered)}%)</td></tr>
        ))}
      </LiveTable>
    </div>
  );
}

export function BiasPage() {
  const q = useAnalyticsQuery('bias', {});
  const rows = q.data ?? [];
  return (
    <div>
      <p className="wb-kicker">Fix the root — forecast bias / FVA</p>
      <h1 className="wb-title">Where the planner override <em>adds</em> error versus the system.</h1>
      <p className="wb-lede"><Prov tier="VALIDATED" /> from the governed forecast-accuracy fact.</p>
      <LiveTable loading={q.loading} error={q.error} rows={rows.length} source="rc_bias"
        empty="No DG5 channels with measurable bias in the window."
        head={<tr><th>Channel (DG5)</th><th className="num">Planner bias</th><th className="num">System bias</th><th className="num">Abs error</th><th className="num">Error $</th><th>Flag</th></tr>}>
        {rows.map((r) => (
          <tr key={String(r.dg5)}><td>{String(r.dg5)}</td><td className="num">{num(r.planner_bias)}</td><td className="num">{num(r.system_bias)}</td><td className="num">{num(r.abs_error)}</td><td className="num">{usd(r.error_cost as number)}</td><td>{String(r.flag) === 'OVERRIDE adds error' ? <Stamp kind="act">{String(r.flag)}</Stamp> : String(r.flag)}</td></tr>
        ))}
      </LiveTable>
    </div>
  );
}

export function ConstraintsPage() {
  const q = useAnalyticsQuery('constraints', {});
  const rows = q.data ?? [];
  return (
    <div>
      <p className="wb-kicker">Convergence · one defendant, many fires</p>
      <h1 className="wb-title">One supplier, many fires — concentration made visible.</h1>
      <p className="wb-lede">Flagged SKUs and $ rolled up by supplier. One sourcing action, not thousands of tickets. <Prov tier="VALIDATED" /> live.</p>
      <LiveTable loading={q.loading} error={q.error} rows={rows.length} source="rc_pattern_rollup"
        empty="No supplier concentration at this snapshot."
        head={<tr><th>Supplier</th><th>Dominant cause</th><th className="num">Flagged SKUs</th><th className="num">$ at risk</th></tr>}>
        {rows.map((r, i) => (
          <tr key={String(r.supplier) + i}><td>{String(r.supplier)}</td><td>{String(r.likely_cause)}</td><td className="num">{num(r.sku_count)}</td><td className="num">{usd(r.dollars_at_risk as number)}</td></tr>
        ))}
      </LiveTable>
    </div>
  );
}

export function DormantPage() {
  const q = useAnalyticsQuery('dormant', {});
  const rows = q.data ?? [];
  return (
    <div>
      <p className="wb-kicker">Dormant / E&O</p>
      <h1 className="wb-title">Value that hasn’t moved — and which of it is intentional.</h1>
      <p className="wb-lede">Managed reserves flagged intentional, excluded from E&O. <Prov tier="VALIDATED" /> live from shipment recency.</p>
      <LiveTable loading={q.loading} error={q.error} rows={rows.length} source="rc_dormant"
        empty="No dormant items at this snapshot."
        head={<tr><th>SKU</th><th>ABC</th><th>Last ship</th><th>Status</th><th>Verdict</th></tr>}>
        {rows.map((r) => (
          <tr key={String(r.item_id)}><td className="sku">{String(r.item_id)}</td><td>{String(r.abc)}</td><td>{r.last_ship_week == null ? 'never' : String(r.last_ship_week)}</td><td>{String(r.status)}</td><td>{String(r.verdict) === 'intentional' ? <Stamp kind="c">intentional</Stamp> : <Stamp kind="watch">review E&O</Stamp>}</td></tr>
        ))}
      </LiveTable>
    </div>
  );
}
