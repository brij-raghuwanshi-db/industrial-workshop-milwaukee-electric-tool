import { useState, useEffect, useCallback } from 'react';
import {
  Button, Card, CardContent, CardHeader, CardTitle, Input, Badge,
} from '@databricks/appkit-ui/react';

// ---- types (mirror server payloads) ------------------------------------
interface EventRow {
  exp_id: number; event_name: string; event_type: string; status: string;
  organization_code: string; record_version: number; created_by: string | null;
}
interface Cell { item_number: string; mkedg5: string; month: string; value: number; source: string; }
interface EventDetail {
  event: EventRow;
  customers: { mkedg5: string; status: string }[];
  items: { item_number: string; item_id: string | null; validation_flag: string | null; item_status: string | null }[];
  cells: Cell[];
  lock: { locked_by: string } | null;
}
interface Ack { run_id: string; active_events: number; rows_published: number; status: string; published_at: string; }

const statusColor: Record<string, string> = {
  IN_PROGRESS: 'bg-muted text-foreground', ACTIVE: 'bg-green-600 text-white',
  DEACTIVATED: 'bg-amber-500 text-white', CLOSED: 'bg-red-600 text-white',
};

async function api<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
const errMsg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

export function EventsPage() {
  const [events, setEvents] = useState<EventRow[]>([]);
  const [selected, setSelected] = useState<EventDetail | null>(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ack, setAck] = useState<Ack | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    try { setEvents(await api<EventRow[]>('/api/events')); }
    catch (e) { setError(errMsg(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  const open = async (id: number) => {
    try { setSelected(await api<EventDetail>(`/api/events/${id}`)); }
    catch (e) { setError(errMsg(e)); }
  };

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true); setError(null);
    try {
      const ev = await api<EventRow>('/api/events', { method: 'POST', body: JSON.stringify({ event_name: name.trim() }) });
      setName(''); await refresh(); await open(ev.exp_id);
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };

  const setStatus = async (id: number, status: string) => {
    setBusy(true);
    try {
      await api(`/api/bulk-edit`, { method: 'POST', body: JSON.stringify({
        batch_id: `status-${id}-${status}-${Date.now()}`, category_type: 'EVENT',
        category_selector: { exp_id: id }, operation: 'SET_STATUS', op_value: { status },
        rows: [{ exp_id: id, new_status: status }],
      }) });
      await refresh(); if (selected?.event.exp_id === id) await open(id);
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };

  const publish = async () => {
    setBusy(true); setError(null);
    try { setAck(await api<Ack>('/api/publish', { method: 'POST', body: '{}' })); await refresh(); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Demand Events</h2>
          <p className="text-sm text-muted-foreground">Incremental demand above baseline · writes to Lakebase · publishes to sandbox Delta</p>
        </div>
        <Button onClick={() => { void publish(); }} disabled={busy}>Publish Active → Delta</Button>
      </div>

      {error && <div className="rounded-md bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">{error}</div>}
      {ack && (
        <div className="rounded-md bg-green-50 border border-green-200 text-green-800 text-sm px-3 py-2">
          ✅ Submitted <span className="font-mono">{ack.run_id}</span> — {ack.active_events} active events, {ack.rows_published} rows. Status: {ack.status}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>Create event</CardTitle></CardHeader>
        <CardContent className="flex gap-2">
          <Input placeholder="Event name (e.g. TOL THD 2026 HDC 4 Bay)" value={name}
                 onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') void create(); }} />
          <Button onClick={() => { void create(); }} disabled={busy || !name.trim()}>Create</Button>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Events ({events.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
            {!loading && events.length === 0 && <p className="text-sm text-muted-foreground">No events yet. Create one above.</p>}
            {events.map((e) => (
              <button key={e.exp_id} onClick={() => { void open(e.exp_id); }}
                className="w-full text-left border rounded-md px-3 py-2 hover:bg-muted flex items-center justify-between">
                <span><span className="font-mono text-xs text-muted-foreground mr-2">EXP{e.exp_id}</span>{e.event_name}</span>
                <Badge className={statusColor[e.status] ?? ''}>{e.status}</Badge>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{selected ? `EXP${selected.event.exp_id} — ${selected.event.event_name}` : 'Detail'}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {!selected && <p className="text-sm text-muted-foreground">Select an event.</p>}
            {selected && (
              <>
                <div className="flex flex-wrap gap-2">
                  {['IN_PROGRESS', 'ACTIVE', 'DEACTIVATED', 'CLOSED'].map((s) => (
                    <Button key={s} size="sm" variant={selected.event.status === s ? 'default' : 'outline'}
                      disabled={busy} onClick={() => { void setStatus(selected.event.exp_id, s); }}>{s}</Button>
                  ))}
                </div>
                <div className="text-sm">
                  <p className="text-muted-foreground">Customers: {selected.customers.length} · Items: {selected.items.length} · Cells: {selected.cells.length}</p>
                  {selected.lock && <p className="text-amber-600">🔒 locked by {selected.lock.locked_by}</p>}
                </div>
                {selected.items.length > 0 && (
                  <div className="text-xs border rounded-md overflow-hidden">
                    <div className="grid grid-cols-3 gap-1 bg-muted px-2 py-1 font-medium"><span>Item</span><span>Status</span><span>Flag</span></div>
                    {selected.items.slice(0, 8).map((it) => (
                      <div key={it.item_number} className="grid grid-cols-3 gap-1 px-2 py-1 border-t">
                        <span className="font-mono">{it.item_number}</span>
                        <span>{it.item_status ?? '—'}</span>
                        <span className={it.validation_flag?.startsWith('WARN') ? 'text-amber-600' : 'text-green-600'}>{it.validation_flag ?? '—'}</span>
                      </div>
                    ))}
                  </div>
                )}
                {selected.cells.length > 0 && (
                  <div className="text-xs border rounded-md overflow-hidden">
                    <div className="grid grid-cols-4 gap-1 bg-muted px-2 py-1 font-medium"><span>Item</span><span>mkedg5</span><span>Month</span><span className="text-right">Units</span></div>
                    {selected.cells.slice(0, 12).map((c) => (
                      <div key={`${c.item_number}|${c.mkedg5}|${String(c.month)}`} className="grid grid-cols-4 gap-1 px-2 py-1 border-t">
                        <span className="font-mono">{c.item_number}</span><span>{c.mkedg5}</span>
                        <span>{String(c.month).slice(0, 10)}</span>
                        <span className={`text-right font-mono ${c.value < 0 ? 'text-red-600' : ''}`}>{c.value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
