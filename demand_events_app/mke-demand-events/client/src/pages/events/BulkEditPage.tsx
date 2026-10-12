import { useState, useEffect } from 'react';
import {
  Button, Card, CardContent, CardHeader, CardTitle, Input, Badge,
} from '@databricks/appkit-ui/react';

interface EventRow { exp_id: number; event_name: string; status: string; }
interface BulkResult { batch_id: string; status: string; matched: number; changed: number; idempotent?: boolean; }

async function api<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}
const errMsg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

// The requested capability: bulk edit on a category → staged set-based apply to Lakebase.
export function BulkEditPage() {
  const [events, setEvents] = useState<EventRow[]>([]);
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [operation, setOperation] = useState<'SET_STATUS' | 'CLOSE' | 'APPLY_LIFT'>('SET_STATUS');
  const [status, setStatusVal] = useState('DEACTIVATED');
  const [liftPct, setLiftPct] = useState('20');
  const [result, setResult] = useState<BulkResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api<EventRow[]>('/api/events').then(setEvents).catch((e: unknown) => setError(errMsg(e))); }, [result]);

  const toggle = (id: number) => setPicked((p) => {
    const n = new Set(p);
    if (n.has(id)) n.delete(id); else n.add(id);
    return n;
  });

  const apply = async () => {
    if (picked.size === 0) { setError('Select at least one event.'); return; }
    setBusy(true); setError(null); setResult(null);
    const ids = [...picked];
    const op_value = operation === 'APPLY_LIFT' ? { lift_pct: Number(liftPct) / 100 }
      : operation === 'CLOSE' ? {} : { status };
    try {
      const r = await api<BulkResult>('/api/bulk-edit', {
        method: 'POST',
        body: JSON.stringify({
          batch_id: `bulk-${operation}-${Date.now()}`,
          category_type: 'EVENT',
          category_selector: { exp_ids: ids },
          operation,
          op_value,
          rows: ids.map((exp_id) => ({ exp_id })),
        }),
      });
      setResult(r); setPicked(new Set());
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Bulk Edit by Category</h2>
        <p className="text-sm text-muted-foreground">Select a category, choose an operation, apply as one staged set-based write to Lakebase (idempotent, audited).</p>
      </div>

      {error && <div className="rounded-md bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">{error}</div>}
      {result && (
        <div className="rounded-md bg-green-50 border border-green-200 text-green-800 text-sm px-3 py-2">
          ✅ Batch <span className="font-mono">{result.batch_id}</span> {result.idempotent ? '(idempotent replay)' : ''} — status {result.status}, matched {result.matched}, changed {result.changed}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>1 · Category: Events ({picked.size} selected)</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-64 overflow-auto">
          {events.map((e) => (
            <label key={e.exp_id} className="flex items-center gap-2 border rounded-md px-3 py-2 cursor-pointer hover:bg-muted">
              <input type="checkbox" checked={picked.has(e.exp_id)} onChange={() => toggle(e.exp_id)} />
              <span className="font-mono text-xs text-muted-foreground">EXP{e.exp_id}</span>
              <span className="flex-1 text-sm truncate">{e.event_name}</span>
              <Badge>{e.status}</Badge>
            </label>
          ))}
          {events.length === 0 && <p className="text-sm text-muted-foreground">No events. Create some on the Events page.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>2 · Operation</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            {(['SET_STATUS', 'CLOSE', 'APPLY_LIFT'] as const).map((op) => (
              <Button key={op} variant={operation === op ? 'default' : 'outline'} size="sm" onClick={() => setOperation(op)}>{op}</Button>
            ))}
          </div>
          {operation === 'SET_STATUS' && (
            <div className="flex gap-2 items-center">
              <span className="text-sm text-muted-foreground">New status:</span>
              {['IN_PROGRESS', 'ACTIVE', 'DEACTIVATED'].map((s) => (
                <Button key={s} size="sm" variant={status === s ? 'default' : 'outline'} onClick={() => setStatusVal(s)}>{s}</Button>
              ))}
            </div>
          )}
          {operation === 'CLOSE' && <p className="text-sm text-muted-foreground">Sets selected events to CLOSED → published output becomes zero, record retained.</p>}
          {operation === 'APPLY_LIFT' && (
            <div className="flex gap-2 items-center">
              <span className="text-sm text-muted-foreground">Lift %:</span>
              <Input className="w-24" value={liftPct} onChange={(e) => setLiftPct(e.target.value)} />
              <span className="text-sm text-muted-foreground">applies to all cells of the selected events (units recomputed).</span>
            </div>
          )}
        </CardContent>
      </Card>

      <Button onClick={() => { void apply(); }} disabled={busy || picked.size === 0}>
        {busy ? 'Applying…' : `Apply to ${picked.size} event(s)`}
      </Button>
    </div>
  );
}
