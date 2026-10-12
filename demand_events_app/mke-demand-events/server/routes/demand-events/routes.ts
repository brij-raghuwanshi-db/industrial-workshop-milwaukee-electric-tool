// Demand Events API — all writes land in Lakebase (schema `demand_events`).
// Reads of prod_edw happen via the analytics plugin (config/queries/*.sql), never here.
// Publication writes conceptually target sandbox_operations.po_management (Delta) —
// here we record the acknowledgement; the actual Delta MERGE is a separate Job.

import { z } from 'zod';
import type { Application, Request } from 'express';
import { SCHEMA, initDemandEventsSchema } from './schema';

interface AppKitWithLakebase {
  lakebase: {
    query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }>;
    pool: { connect(): Promise<PoolClient> };
  };
  server: { extend(fn: (app: Application) => void): void };
}
interface PoolClient {
  query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[]; rowCount: number | null }>;
  release(): void;
}

const actor = (req: Request): string =>
  (req.headers['x-forwarded-email'] as string) || 'local-dev';

const LOCK_MINUTES = 30;

// ---- validation payloads ------------------------------------------------
const CreateEvent = z.object({
  event_name: z.string().min(1),
  event_type: z.enum(['non_repeating', 'repeating', 'both']).default('non_repeating'),
  organization_code: z.string().default('2012'),
});
const CustomersBody = z.object({
  customers: z.array(z.object({ mkedg5: z.string(), input_level: z.string().optional() })).min(1),
});
const ItemsBody = z.object({
  items: z.array(z.object({
    item_number: z.string(),
    item_id: z.string().optional(),
    validation_flag: z.string().optional(),
    validation_rule_version: z.string().optional(),
    item_status: z.string().optional(),
  })).min(1),
});
const CellsBody = z.object({
  cells: z.array(z.object({
    item_number: z.string(),
    mkedg5: z.string(),
    month: z.string(),          // YYYY-MM-01
    value: z.coerce.number(),   // coerce: UI/pg values may arrive as strings
    source: z.enum(['DIRECT', 'BUILDER', 'DISAGGREGATED', 'OVERRIDE', 'SEED']).default('DIRECT'),
  })).min(1),
});
// Disaggregate a total at a hierarchy level into mkedg5 cells using supplied base-measure shares.
const DisaggregateBody = z.object({
  item_number: z.string(),
  month: z.string(),
  total_input: z.coerce.number(),
  base: z.array(z.object({ mkedg5: z.string(), base_measure: z.coerce.number() })).min(1),
  source: z.enum(['DISAGGREGATED', 'BUILDER']).default('DISAGGREGATED'),
});
// Bulk edit by category — the specifically requested feature.
const BulkEditBody = z.object({
  batch_id: z.string().min(1),                    // idempotency key
  category_type: z.enum(['EVENT', 'CUSTOMER', 'TAG', 'ITEM', 'STATUS', 'ORG']),
  category_selector: z.record(z.string(), z.unknown()),
  operation: z.enum(['SET_STATUS', 'CLOSE', 'ADJUST_VALUE', 'APPLY_LIFT']),
  op_value: z.record(z.string(), z.unknown()).optional(),
  // exp_id/new_value coerce: node-postgres returns BIGINT/NUMERIC as strings,
  // so the UI round-trips them back as strings — accept both.
  rows: z.array(z.object({
    exp_id: z.coerce.number(),
    item_number: z.string().optional(),
    mkedg5: z.string().optional(),
    month: z.string().optional(),
    new_value: z.coerce.number().optional(),
    new_status: z.string().optional(),
  })).min(1),
});

async function audit(
  lb: AppKitWithLakebase['lakebase'], expId: number | null, who: string,
  type: string, field: string | null, before: unknown, after: unknown, batchId?: string,
) {
  await lb.query(
    `INSERT INTO ${SCHEMA}.event_audit_event (exp_id, actor, event_type, field, before_state, after_state, batch_id)
     VALUES ($1,$2,$3,$4,$5,$6,$7)`,
    [expId, who, type, field, JSON.stringify(before ?? null), JSON.stringify(after ?? null), batchId ?? null],
  );
}

export async function setupDemandEventsRoutes(appkit: AppKitWithLakebase) {
  await initDemandEventsSchema(appkit.lakebase);
  const lb = appkit.lakebase;

  appkit.server.extend((app) => {
    // ---- list / read events -------------------------------------------
    app.get('/api/events', async (req, res) => {
      try {
        const status = req.query.status as string | undefined;
        const q = status
          ? `SELECT * FROM ${SCHEMA}.event WHERE status = $1 ORDER BY exp_id DESC`
          : `SELECT * FROM ${SCHEMA}.event ORDER BY exp_id DESC`;
        const { rows } = await lb.query(q, status ? [status] : []);
        res.json(rows);
      } catch (e) { console.error(e); res.status(500).json({ error: 'list failed' }); }
    });

    app.get('/api/events/:id', async (req, res) => {
      try {
        const id = Number(req.params.id);
        const [ev, hdr, cust, items, cells, lock] = await Promise.all([
          lb.query(`SELECT * FROM ${SCHEMA}.event WHERE exp_id=$1`, [id]),
          lb.query(`SELECT * FROM ${SCHEMA}.event_header WHERE exp_id=$1 ORDER BY tranche_index`, [id]),
          lb.query(`SELECT * FROM ${SCHEMA}.event_customer WHERE exp_id=$1`, [id]),
          lb.query(`SELECT * FROM ${SCHEMA}.event_item WHERE exp_id=$1`, [id]),
          lb.query(`SELECT * FROM ${SCHEMA}.event_cell WHERE exp_id=$1 ORDER BY item_number, mkedg5, month`, [id]),
          lb.query(`SELECT * FROM ${SCHEMA}.event_lock WHERE exp_id=$1`, [id]),
        ]);
        if (ev.rows.length === 0) { res.status(404).json({ error: 'not found' }); return; }
        res.json({ event: ev.rows[0], headers: hdr.rows, customers: cust.rows, items: items.rows, cells: cells.rows, lock: lock.rows[0] ?? null });
      } catch (e) { console.error(e); res.status(500).json({ error: 'get failed' }); }
    });

    // ---- create event (auto EXP ID = max+1) ---------------------------
    app.post('/api/events', async (req, res) => {
      const parsed = CreateEvent.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      const who = actor(req);
      try {
        const seq = await lb.query(
          `UPDATE ${SCHEMA}.exp_id_seq SET next_id = next_id + 1 RETURNING next_id - 1 AS exp_id`,
        );
        const expId = Number(seq.rows[0].exp_id);
        const { rows } = await lb.query(
          `INSERT INTO ${SCHEMA}.event (exp_id, event_name, event_type, organization_code, created_by, last_modified_by)
           VALUES ($1,$2,$3,$4,$5,$5) RETURNING *`,
          [expId, parsed.data.event_name, parsed.data.event_type, parsed.data.organization_code, who],
        );
        await audit(lb, expId, who, 'CREATED', null, null, rows[0]);
        res.status(201).json(rows[0]);
      } catch (e) { console.error(e); res.status(500).json({ error: 'create failed' }); }
    });

    // ---- lock / unlock -------------------------------------------------
    app.post('/api/events/:id/lock', async (req, res) => {
      const id = Number(req.params.id); const who = actor(req);
      try {
        const existing = await lb.query(
          `SELECT * FROM ${SCHEMA}.event_lock WHERE exp_id=$1 AND expires_at > now()`, [id]);
        if (existing.rows.length && existing.rows[0].locked_by !== who) {
          res.status(409).json({ error: 'locked', locked_by: existing.rows[0].locked_by }); return;
        }
        const { rows } = await lb.query(
          `INSERT INTO ${SCHEMA}.event_lock (exp_id, locked_by, expires_at)
           VALUES ($1,$2, now() + interval '${LOCK_MINUTES} minutes')
           ON CONFLICT (exp_id) DO UPDATE SET locked_by=$2, locked_at=now(),
             expires_at = now() + interval '${LOCK_MINUTES} minutes' RETURNING *`,
          [id, who]);
        res.json(rows[0]);
      } catch (e) { console.error(e); res.status(500).json({ error: 'lock failed' }); }
    });
    app.delete('/api/events/:id/lock', async (req, res) => {
      try { await lb.query(`DELETE FROM ${SCHEMA}.event_lock WHERE exp_id=$1`, [Number(req.params.id)]); res.status(204).send(); }
      catch (e) { console.error(e); res.status(500).json({ error: 'unlock failed' }); }
    });

    // ---- customers / items (bulk paste from Excel) --------------------
    app.post('/api/events/:id/customers', async (req, res) => {
      const id = Number(req.params.id);
      const parsed = CustomersBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      try {
        for (const c of parsed.data.customers) {
          await lb.query(
            `INSERT INTO ${SCHEMA}.event_customer (exp_id, mkedg5, input_level) VALUES ($1,$2,$3)
             ON CONFLICT (exp_id, mkedg5) DO UPDATE SET input_level=EXCLUDED.input_level`,
            [id, c.mkedg5, c.input_level ?? null]);
        }
        await audit(lb, id, actor(req), 'EDITED', 'customers', null, parsed.data.customers);
        res.status(201).json({ added: parsed.data.customers.length });
      } catch (e) { console.error(e); res.status(500).json({ error: 'customers failed' }); }
    });

    app.post('/api/events/:id/items', async (req, res) => {
      const id = Number(req.params.id);
      const parsed = ItemsBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      try {
        for (const it of parsed.data.items) {
          await lb.query(
            `INSERT INTO ${SCHEMA}.event_item (exp_id, item_number, item_id, validation_flag, validation_rule_version, item_status)
             VALUES ($1,$2,$3,$4,$5,$6)
             ON CONFLICT (exp_id, item_number) DO UPDATE SET
               item_id=EXCLUDED.item_id, validation_flag=EXCLUDED.validation_flag,
               validation_rule_version=EXCLUDED.validation_rule_version, item_status=EXCLUDED.item_status`,
            [id, it.item_number, it.item_id ?? null, it.validation_flag ?? null, it.validation_rule_version ?? null, it.item_status ?? null]);
        }
        await audit(lb, id, actor(req), 'EDITED', 'items', null, { count: parsed.data.items.length });
        res.status(201).json({ added: parsed.data.items.length });
      } catch (e) { console.error(e); res.status(500).json({ error: 'items failed' }); }
    });

    // ---- direct cell edits (units, signed) ----------------------------
    app.post('/api/events/:id/cells', async (req, res) => {
      const id = Number(req.params.id);
      const parsed = CellsBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      try {
        for (const c of parsed.data.cells) {
          await lb.query(
            `INSERT INTO ${SCHEMA}.event_cell (exp_id, item_number, mkedg5, month, value, source)
             VALUES ($1,$2,$3,$4,$5,$6)
             ON CONFLICT (exp_id, item_number, mkedg5, month)
             DO UPDATE SET value=EXCLUDED.value, source=EXCLUDED.source, updated_at=now()`,
            [id, c.item_number, c.mkedg5, c.month, c.value, c.source]);
        }
        await audit(lb, id, actor(req), 'EDITED', 'cells', null, { count: parsed.data.cells.length });
        res.status(201).json({ upserted: parsed.data.cells.length });
      } catch (e) { console.error(e); res.status(500).json({ error: 'cells failed' }); }
    });

    // ---- ratio disaggregation (deterministic; LLM never does this) ----
    app.post('/api/events/:id/disaggregate', async (req, res) => {
      const id = Number(req.params.id);
      const parsed = DisaggregateBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      const { item_number, month, total_input, base, source } = parsed.data;
      const totalBase = base.reduce((s, b) => s + b.base_measure, 0);
      try {
        const out: { mkedg5: string; value: number }[] = [];
        for (const b of base) {
          // Ratio share; even-split fallback when base sums to zero (the "50/50" MVP start).
          const share = totalBase !== 0 ? b.base_measure / totalBase : 1 / base.length;
          const value = Math.round(total_input * share);
          out.push({ mkedg5: b.mkedg5, value });
          await lb.query(
            `INSERT INTO ${SCHEMA}.event_cell (exp_id, item_number, mkedg5, month, value, source)
             VALUES ($1,$2,$3,$4,$5,$6)
             ON CONFLICT (exp_id, item_number, mkedg5, month)
             DO UPDATE SET value=EXCLUDED.value, source=EXCLUDED.source, updated_at=now()`,
            [id, item_number, b.mkedg5, month, value, source]);
        }
        await audit(lb, id, actor(req), 'DISAGGREGATED', item_number,
          { total_input, base_sum: totalBase }, out);
        res.json({ item_number, month, total_input, fallback_even_split: totalBase === 0, cells: out });
      } catch (e) { console.error(e); res.status(500).json({ error: 'disaggregate failed' }); }
    });

    // ---- BULK EDIT by category (stage -> one set-based apply) ----------
    app.post('/api/bulk-edit', async (req, res) => {
      const parsed = BulkEditBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: parsed.error.message }); return; }
      const b = parsed.data; const who = actor(req);

      // Idempotency: if this batch_id already applied, return its result.
      const prior = await lb.query(
        `SELECT * FROM ${SCHEMA}.bulk_edit_batch WHERE batch_id=$1`, [b.batch_id]);
      if (prior.rows.length && prior.rows[0].status === 'APPLIED') {
        res.json({ idempotent: true, ...prior.rows[0] }); return;
      }

      const client = await lb.pool.connect();
      try {
        await client.query('BEGIN');
        await client.query(
          `INSERT INTO ${SCHEMA}.bulk_edit_batch
             (batch_id, category_type, category_selector, operation, op_value, requested_by)
           VALUES ($1,$2,$3,$4,$5,$6)
           ON CONFLICT (batch_id) DO NOTHING`,
          [b.batch_id, b.category_type, JSON.stringify(b.category_selector), b.operation,
           JSON.stringify(b.op_value ?? {}), who]);

        // Stage rows (dedup by business key: keep last submitted).
        const seen = new Set<string>();
        for (const r of [...b.rows].reverse()) {
          const key = `${r.exp_id}|${r.item_number ?? ''}|${r.mkedg5 ?? ''}|${r.month ?? ''}`;
          if (seen.has(key)) continue;
          seen.add(key);
          await client.query(
            `INSERT INTO ${SCHEMA}.bulk_edit_stage
               (batch_id, exp_id, item_number, mkedg5, month, new_value, new_status)
             VALUES ($1,$2,$3,$4,$5,$6,$7)`,
            [b.batch_id, r.exp_id, r.item_number ?? null, r.mkedg5 ?? null, r.month ?? null,
             r.new_value ?? null, r.new_status ?? null]);
        }

        // One set-based apply per operation type.
        let changed = 0;
        if (b.operation === 'SET_STATUS' || b.operation === 'CLOSE') {
          const statusVal = b.op_value?.status;
          const newStatus = b.operation === 'CLOSE'
            ? 'CLOSED'
            : (typeof statusVal === 'string' ? statusVal : 'DEACTIVATED');
          if (b.category_type === 'CUSTOMER') {
            const r = await client.query(
              `UPDATE ${SCHEMA}.event_customer c SET status=$1
               FROM ${SCHEMA}.bulk_edit_stage s
               WHERE s.batch_id=$2 AND c.exp_id=s.exp_id AND c.mkedg5=s.mkedg5`,
              [newStatus === 'CLOSED' ? 'CLOSED' : 'ACTIVE', b.batch_id]);
            changed = r.rowCount ?? 0;
          } else {
            const r = await client.query(
              `UPDATE ${SCHEMA}.event e SET status=$1, record_version=record_version+1, last_modified_by=$3, last_modified_at=now()
               FROM ${SCHEMA}.bulk_edit_stage s
               WHERE s.batch_id=$2 AND e.exp_id=s.exp_id`,
              [newStatus, b.batch_id, who]);
            changed = r.rowCount ?? 0;
          }
        } else if (b.operation === 'ADJUST_VALUE') {
          const r = await client.query(
            `UPDATE ${SCHEMA}.event_cell c SET value=s.new_value, source='OVERRIDE', updated_at=now()
             FROM ${SCHEMA}.bulk_edit_stage s
             WHERE s.batch_id=$1 AND c.exp_id=s.exp_id AND c.item_number=s.item_number
               AND c.mkedg5=s.mkedg5 AND c.month=s.month AND s.new_value IS NOT NULL`,
            [b.batch_id]);
          changed = r.rowCount ?? 0;
        } else if (b.operation === 'APPLY_LIFT') {
          const pct = Number(b.op_value?.lift_pct ?? 0);
          const r = await client.query(
            `UPDATE ${SCHEMA}.event_cell c SET value = ROUND(value * (1 + $1::numeric)), source='OVERRIDE', updated_at=now()
             FROM ${SCHEMA}.bulk_edit_stage s
             WHERE s.batch_id=$2 AND c.exp_id=s.exp_id
               AND (s.item_number IS NULL OR c.item_number=s.item_number)`,
            [pct, b.batch_id]);
          changed = r.rowCount ?? 0;
        }

        const matched = b.rows.length;
        await client.query(
          `UPDATE ${SCHEMA}.bulk_edit_batch SET status='APPLIED', matched=$2, changed=$3 WHERE batch_id=$1`,
          [b.batch_id, matched, changed]);
        await client.query(
          `INSERT INTO ${SCHEMA}.event_audit_event (exp_id, actor, event_type, field, after_state, batch_id)
           VALUES (NULL,$1,'BULK',$2,$3,$4)`,
          [who, `${b.category_type}:${b.operation}`, JSON.stringify({ matched, changed }), b.batch_id]);
        await client.query('COMMIT');
        res.json({ batch_id: b.batch_id, status: 'APPLIED', matched, changed });
      } catch (e) {
        await client.query('ROLLBACK');
        console.error('bulk-edit failed', e);
        await lb.query(`UPDATE ${SCHEMA}.bulk_edit_batch SET status='FAILED' WHERE batch_id=$1`, [b.batch_id]).catch(() => {});
        res.status(500).json({ error: 'bulk edit failed' });
      } finally {
        client.release();
      }
    });

    // ---- audit trail for an event -------------------------------------
    app.get('/api/events/:id/audit', async (req, res) => {
      try {
        const { rows } = await lb.query(
          `SELECT * FROM ${SCHEMA}.event_audit_event WHERE exp_id=$1 ORDER BY occurred_at DESC LIMIT 200`,
          [Number(req.params.id)]);
        res.json(rows);
      } catch (e) { console.error(e); res.status(500).json({ error: 'audit failed' }); }
    });

    // ---- publish Active events (records ack; Delta MERGE is a Job) -----
    app.post('/api/publish', async (req, res) => {
      const who = actor(req);
      const runId = `run-${Date.now()}`;
      try {
        const active = await lb.query(`SELECT COUNT(*)::int AS n FROM ${SCHEMA}.event WHERE status='ACTIVE'`);
        const cells = await lb.query(
          `SELECT COUNT(*)::int AS n FROM ${SCHEMA}.event_cell c
           JOIN ${SCHEMA}.event e ON e.exp_id=c.exp_id
           JOIN ${SCHEMA}.event_customer cu ON cu.exp_id=c.exp_id AND cu.mkedg5=c.mkedg5
           WHERE e.status='ACTIVE' AND cu.status='ACTIVE' AND c.value <> 0`);
        const nEvents = Number(active.rows[0].n);
        const nRows = Number(cells.rows[0].n);
        const { rows } = await lb.query(
          `INSERT INTO ${SCHEMA}.publication_ack (run_id, active_events, rows_published, status, note)
           VALUES ($1,$2,$3,'SUCCEEDED',$4) RETURNING *`,
          [runId, nEvents, nRows, 'Recorded in Lakebase. Delta MERGE into sandbox_operations.po_management.demand_events_published is a separate Job.']);
        await audit(lb, null, who, 'PUBLISHED', 'publish', null, rows[0]);
        res.json(rows[0]);
      } catch (e) { console.error(e); res.status(500).json({ error: 'publish failed' }); }
    });

    app.get('/api/publish/history', async (_req, res) => {
      try {
        const { rows } = await lb.query(`SELECT * FROM ${SCHEMA}.publication_ack ORDER BY published_at DESC LIMIT 50`);
        res.json(rows);
      } catch (e) { console.error(e); res.status(500).json({ error: 'history failed' }); }
    });
  });
}
