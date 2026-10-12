// Session store — now backed by Lakebase via /api routes (persists across refresh).
// Same interface the pages use; fetches replace pure useState.
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

export interface LogRow { when: string; sku: string; suggested: string; actual?: string; diverged?: boolean; savings_state?: string; delta?: number; }
export interface EvidenceItem { cause: string; text: string; }
// realized is null until a two-snapshot read-back exists; baseline/residual are set from the live value_baseline query.
export interface Ledger { projected: number; realized: number | null; notActed: number; lossAvoided: number; residual: number | null; baseline: number | null; }

interface Store {
  sku: string; setSku: (s: string) => void;
  evidence: EvidenceItem[]; addEvidence: (e: EvidenceItem) => void;
  log: LogRow[];
  ledger: Ledger;
  setBaseline: (v: number) => void;   // fed by the live value_baseline analytics query
  applyAction: (kind: 'transfer' | 'dismiss' | 'allocate', sku: string, suggested: string, delta: number) => void;
  tour: number; setTour: (n: number) => void;
  highlight: string | null; setHighlight: (h: string | null) => void;
}

const Ctx = createContext<Store | null>(null);
const EMPTY_LEDGER: Ledger = { projected: 0, realized: null, notActed: 0, lossAvoided: 0, residual: null, baseline: null };

// Normalize server ledger (snake_case + numeric strings). baseline/residual come from the live
// value_baseline query and are injected by setBaseline(); realized stays null until a read-back exists.
function normLedger(d: Record<string, unknown>): Omit<Ledger, 'baseline' | 'residual'> & { realized: number | null } {
  const rv = (d as { realized?: unknown }).realized;
  return {
    projected: Number(d.projected ?? 0),
    realized: rv == null ? null : Number(rv),
    notActed: Number((d as { notActed?: unknown; not_acted?: unknown }).notActed ?? (d as { not_acted?: unknown }).not_acted ?? 0),
    lossAvoided: Number((d as { lossAvoided?: unknown; loss_avoided?: unknown }).lossAvoided ?? (d as { loss_avoided?: unknown }).loss_avoided ?? 0),
  };
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [sku, setSku] = useState('3697-22');
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [log, setLog] = useState<LogRow[]>([]);
  const [ledger, setLedger] = useState<Ledger>(EMPTY_LEDGER);
  const [tour, setTour] = useState(-1);
  const [highlight, setHighlight] = useState<string | null>(null);

  // Merge server action-log sums with the client-injected live baseline; recompute residual.
  const mergeLedger = useCallback((partial: Omit<Ledger, 'baseline' | 'residual'>) => {
    setLedger((prev) => {
      const baseline = prev.baseline;
      return { ...partial, baseline, residual: baseline == null ? null : Math.max(0, baseline - partial.projected) };
    });
  }, []);

  const setBaseline = useCallback((v: number) => {
    setLedger((prev) => ({ ...prev, baseline: v, residual: Math.max(0, v - prev.projected) }));
  }, []);

  const refreshLedger = useCallback(() => {
    fetch('/api/ledger').then((r) => (r.ok ? r.json() : null)).then((d) => d && mergeLedger(normLedger(d))).catch(() => {});
    fetch('/api/log').then((r) => (r.ok ? r.json() : [])).then((rows: LogRow[]) => setLog(Array.isArray(rows) ? rows : [])).catch(() => {});
  }, [mergeLedger]);

  useEffect(() => { refreshLedger(); }, [refreshLedger]);

  // load persisted evidence when the case changes
  useEffect(() => {
    fetch(`/api/evidence?case_id=${encodeURIComponent(sku)}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: EvidenceItem[]) => setEvidence(Array.isArray(rows) ? rows : []))
      .catch(() => setEvidence([]));
  }, [sku]);

  const addEvidence = (e: EvidenceItem) => {
    setEvidence((prev) => (prev.some((p) => p.cause === e.cause) ? prev : [...prev, e])); // optimistic
    fetch('/api/evidence', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: sku, cause: e.cause, text: e.text }),
    }).then((r) => (r.ok ? r.json() : null)).then((rows: EvidenceItem[] | null) => { if (rows) setEvidence(rows); }).catch(() => {});
  };

  const applyAction = (kind: 'transfer' | 'dismiss' | 'allocate', s: string, suggested: string, delta: number) => {
    fetch('/api/action', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: s, kind, suggested, actual: suggested, delta }),
    }).then((r) => (r.ok ? r.json() : null)).then((d) => { if (d) mergeLedger(normLedger(d)); refreshLedger(); }).catch(() => {});
  };

  return (
    <Ctx.Provider value={{ sku, setSku, evidence, addEvidence, log, ledger, setBaseline, applyAction, tour, setTour, highlight, setHighlight }}>
      {children}
    </Ctx.Provider>
  );
}

export function useStore(): Store {
  const c = useContext(Ctx);
  if (!c) throw new Error('useStore outside provider');
  return c;
}
