import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider, Outlet, useNavigate, useLocation } from 'react-router';
import { useAnalyticsQuery } from '@databricks/appkit-ui/react';
import { StoreProvider, useStore } from './lib/store';
import { TOUR } from './lib/seed';
import { WorklistPage } from './pages/WorklistPage';
import { InvestigatePage } from './pages/InvestigatePage';
import { ScenariosPage } from './pages/scenarios/ScenariosPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { GeniePage } from './pages/genie/GeniePage';
import { LedgerPage, EscalationPage, ValuePage, ExcessPage, RebalancePage, BiasPage, ConstraintsPage, DormantPage } from './pages/LedgerPages';

const NAV: [string, string][] = [
  ['/', 'Worklist'],
  ['/investigate', 'Case'],
  ['/coming', 'Coming risk'],
  ['/constraints', 'Constraints'],
  ['/excess', 'Excess'],
  ['/rebalance', 'Rebalance'],
  ['/bias', 'Bias / FVA'],
  ['/dormant', 'Dormant'],
  ['/scenarios', 'Scenarios'],
  ['/portfolio', 'Portfolio'],
  ['/escalation', 'Escalation'],
  ['/ledger', 'Ledger'],
  ['/value', 'Value'],
  ['/ask', 'Ask'],
];

// YYYYMMDD int → YYYY-MM-DD
function fmtKey(k: number | string | null | undefined): string {
  const s = String(k ?? '');
  return s.length === 8 ? `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}` : s || '—';
}

function Mast() {
  const navigate = useNavigate();
  const loc = useLocation();
  const { setTour, tour } = useStore();
  const [who, setWho] = useState<string | null>(null);
  useEffect(() => {
    fetch('/api/whoami').then((r) => (r.ok ? r.json() : null)).then((d) => setWho(d?.email ?? d?.user ?? null)).catch(() => {});
  }, []);
  return (
    <>
      <header className="wb-mast">
        <div className="wb-wordmark">Supply Root-Cause <span>Workbench</span></div>
        <nav className="wb-nav">
          {NAV.map(([path, label]) => (
            <button key={path} className={loc.pathname === path ? 'on' : ''} onClick={() => navigate(path)}>{label}</button>
          ))}
        </nav>
        <button className="wb-play" onClick={() => setTour(tour < 0 ? 0 : -1)}>{tour < 0 ? "Play Leo’s day" : 'End tour'}</button>
        <div className="wb-who"><span className="wb-dot" /> {who ?? 'signed-in user'}</div>
      </header>
      <TourBar />
      <FreshBar />
    </>
  );
}

// Live freshness stamp from rc_run_control — snapshot dates, forward window, build time.
function FreshBar() {
  const q = useAnalyticsQuery('freshness', {});
  const f = q.data?.[0];
  return (
    <div className="wb-fresh" style={{ padding: '6px 20px', background: '#faf8f3', borderBottom: '1px solid #d4cec0' }}>
      {f ? (
        <>
          Snapshot <strong>{fmtKey(f.supply_process_date)}</strong> · forward through {fmtKey(f.forward_window_end)} ·{' '}
          {String(f.supply_plan_name)}
          {f.prior_vintage ? <> · prior plan {fmtKey(f.prior_vintage)} (nervousness baseline)</> : null}
          {' '}· built {String(f.build_ts).slice(0, 10)} · READ-ONLY source
        </>
      ) : (
        <>Loading snapshot freshness…</>
      )}
    </div>
  );
}

function TourBar() {
  const { tour, setTour, setSku, setHighlight } = useStore();
  const navigate = useNavigate();
  if (tour < 0) return null;
  const step = TOUR[tour];
  const go = (n: number) => {
    if (n < 0 || n >= TOUR.length) { setTour(-1); setHighlight(null); return; }
    const s = TOUR[n];
    setTour(n);
    if (s.sku) setSku(s.sku);
    setHighlight(s.highlight ?? null);
    navigate(s.view === 'investigate' ? '/investigate' : s.view === 'worklist' ? '/' : `/${s.view}`);
  };
  return (
    <div className="wb-tour">
      <span className="t">{step.t}</span>
      <span className="say">{step.title} — {step.say}</span>
      <button onClick={() => go(tour - 1)}>Back</button>
      <button onClick={() => go(tour + 1)}>Next</button>
      <button onClick={() => { setTour(-1); setHighlight(null); }}>End</button>
    </div>
  );
}

function Layout() {
  return (
    <div className="wb">
      <Mast />
      <main className="wb-stage"><Outlet /></main>
    </div>
  );
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <WorklistPage /> },
      { path: '/investigate', element: <InvestigatePage /> },
      { path: '/coming', element: <AnalyticsPage /> },
      { path: '/constraints', element: <ConstraintsPage /> },
      { path: '/excess', element: <ExcessPage /> },
      { path: '/rebalance', element: <RebalancePage /> },
      { path: '/bias', element: <BiasPage /> },
      { path: '/dormant', element: <DormantPage /> },
      { path: '/scenarios', element: <ScenariosPage /> },
      { path: '/portfolio', element: <AnalyticsPage /> },
      { path: '/escalation', element: <EscalationPage /> },
      { path: '/ledger', element: <LedgerPage /> },
      { path: '/value', element: <ValuePage /> },
      { path: '/ask', element: <GeniePage /> },
    ],
  },
]);

export default function App() {
  return (
    <StoreProvider>
      <RouterProvider router={router} />
    </StoreProvider>
  );
}
