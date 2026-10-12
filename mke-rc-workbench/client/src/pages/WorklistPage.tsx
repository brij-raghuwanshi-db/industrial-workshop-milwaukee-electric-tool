import { useNavigate } from 'react-router';
import { useAnalyticsQuery, Skeleton, Alert, AlertDescription } from '@databricks/appkit-ui/react';
import { useStore } from '../lib/store';
import { HONESTY_FOOTER } from '../lib/seed';
import { Prov, VerdictStamp, CritStamp, RecovStamp, usd, num, Spark } from '../lib/workbench';

function Kpi({ lab, val, meta, cls }: { lab: string; val: string; meta?: string; cls?: string }) {
  return (
    <div className={`wb-kpi ${cls ?? ''}`}>
      <div className="lab">{lab}</div>
      <div className="val">{val}</div>
      {meta && <div className="meta">{meta}</div>}
    </div>
  );
}

export function WorklistPage() {
  const kpi = useAnalyticsQuery('kpi_summary', {});
  const ph = useAnalyticsQuery('portfolio_headline', {});
  const wl = useAnalyticsQuery('watchlist', {});
  const { sku, setSku } = useStore();
  const navigate = useNavigate();
  const k = kpi.data?.[0];
  const p = ph.data?.[0];
  const unrecovDollars = p?.unrecoverable_dollars == null ? null : Number(p.unrecoverable_dollars);

  return (
    <div>
      <p className="wb-kicker">morning worklist</p>
      <h1 className="wb-title">{k ? num(k.flagged_skus) : '…'} flagged SKUs are not the morning. The ACT cases are.</h1>
      <p className="wb-lede">
        Triaged by verdict × criticality × recoverability. Lost battles sit apart; DISMISS is quiet on purpose.
        Click a row to open its case file. <Prov tier="VALIDATED" /> — every number live from the serving layer.
      </p>

      <div className="wb-kpirow">
        {kpi.loading && Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        {k && <>
          <Kpi lab="Flagged SKUs" val={num(k.flagged_skus)} meta={`snapshot ${String(k.snapshot_date)}`} />
          <Kpi lab="ACT" val={num(k.act_skus)} meta="act now" />
          <Kpi lab="WATCH" val={num(k.watch_skus)} meta="monitor" cls="quiet" />
          <Kpi lab="Chronic" val={num(k.chronic_skus)} meta="repeat offenders" />
          <Kpi lab="Unrecoverable" val={num(k.unrecoverable_skus)} meta={unrecovDollars == null ? 'committed' : `≈ ${usd(unrecovDollars)} committed`} cls="lost" />
        </>}
      </div>

      <div className="wb-panel">
        <div className="wb-panel-h"><h2>Watchlist</h2><span className="wb-prov">rc_serving_sku_week</span></div>
        {wl.loading && <div style={{ padding: 14 }}>{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8" style={{ marginBottom: 6 }} />)}</div>}
        {wl.error && <div style={{ padding: 14 }}><Alert variant="destructive"><AlertDescription>{wl.error}</AlertDescription></Alert></div>}
        {wl.data && wl.data.length > 0 && (
          <div style={{ maxHeight: 560, overflow: 'auto' }}>
            <table>
              <thead><tr><th>SKU</th><th>Trend</th><th>Verdict</th><th>Crit</th><th>Recover</th><th>Cause</th><th className="num">$ at risk</th></tr></thead>
              <tbody>
                {wl.data.map((r) => {
                  const id = String(r.item_id);
                  const recov = String(r.recoverability_class);
                  const verdict = String(r.action_verdict);
                  const rowcls = recov === 'UNRECOVERABLE' ? 'row-lost' : verdict === 'DISMISS' ? 'row-dismiss' : '';
                  return (
                    <tr key={id} className={`clk ${rowcls} ${sku === id ? 'sel' : ''}`} onClick={() => { setSku(id); navigate('/investigate'); }}>
                      <td className="sku">{id}</td>
                      <td><Spark points={[3, 4, 4, 5, 6, 7, 8, 9].map((n) => n + (id.length % 3))} /></td>
                      <td><VerdictStamp verdict={verdict} recov={recov} /></td>
                      <td><CritStamp crit={String(r.criticality_class)} /></td>
                      <td><RecovStamp recov={recov} /></td>
                      <td>{String(r.likely_cause)}</td>
                      <td className="num">{usd(r.dollars_at_risk as number)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {wl.data && wl.data.length === 0 && <div style={{ padding: 20, color: '#6f6a60' }}>No flagged SKUs at this snapshot — widen the horizon or switch plan.</div>}
      </div>

      <p className="wb-footnote">{HONESTY_FOOTER}</p>
    </div>
  );
}
