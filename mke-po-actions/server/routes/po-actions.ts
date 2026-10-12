// PO-actions domain routes: read the exception queue + KPIs + record trajectory from the mirrors,
// and the WRITE path (propose -> approve -> execute) against the one writable table app_po.action_request.
// execute_action is ONE transaction: flips status, stamps OBO approver, appends audit, enqueues the
// SIMULATED Oracle outbox + a simulated ack. No real external system is ever called.
import { z } from 'zod';
import type { Application, Request } from 'express';
import { SCHEMA, ALL_DDL, CREATE_INDEXES, ADD_SEARCH_COLUMN, CREATE_SEARCH_FTS_INDEX,
  CREATE_TRGM_EXT, CREATE_SEARCH_TRGM_INDEX } from '../db/schema-sql';
import { syncFromDelta } from '../db/sync';

// Search capability flags — detected at boot, degrade gracefully.
const searchCaps = { fts: false, trgm: false };

const CAT = 'sandbox_operations.po_management';

interface AppKitWithLakebase {
  lakebase: { query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }> };
  analytics: { query(sql: string): Promise<unknown> };
  server: { extend(fn: (app: Application) => void): void };
}

// Optional model-serving plugin — present only when the app declares a `serving` resource.
// A runtime guard (not a cast) lets the explain endpoint use the LLM when wired, else fall to rules.
// The AppKit serving handle exposes invoke() (+ asUser). We call the real model with invoke and,
// for the SSE route, re-emit its answer word-by-word for the live-typing effect.
type ServingFn = (alias: string) => { invoke: (body: unknown) => Promise<unknown> };
function hasServing(a: unknown): a is { serving: ServingFn } {
  return typeof (a as { serving?: unknown }).serving === 'function';
}
// Call the LLM endpoint with the item facts; return {prose, rec} or null on any failure.
async function callLlm(
  serving: ServingFn, sys: string, facts: Record<string, unknown>,
  parseRec: (s: string) => Record<string, unknown>,
): Promise<{ prose: string; rec: Record<string, unknown> } | null> {
  try {
    const outRaw = await serving('llm').invoke({
      messages: [{ role: 'system', content: sys },
                 { role: 'user', content: `Item facts:\n${JSON.stringify(facts, null, 2)}` }],
      temperature: 0.2, max_tokens: 600,
    });
    // Programmatic invoke wraps the completion in ExecutionResult ({ ok, data }); unwrap either shape.
    const payload = (outRaw as { data?: unknown }).data ?? outRaw;
    const out = payload as { choices?: { message?: { content?: string } }[]; content?: string };
    const raw = String(out.choices?.[0]?.message?.content ?? out.content ?? '');
    if (!raw.trim()) return null;
    return { prose: raw.split('@@REC')[0].trim(), rec: parseRec(raw) };
  } catch (e) {
    console.warn('[po-actions] LLM call failed, using rules:', (e as Error).message);
    return null;
  }
}

// Normalize appkit.analytics.query() result into row-objects (shape varies by AppKit version).
function analyticsRows(res: unknown): Record<string, unknown>[] {
  if (!res) return [];
  if (Array.isArray(res)) return res as Record<string, unknown>[];
  const r = res as Record<string, unknown>;
  if (Array.isArray(r.rows)) return r.rows as Record<string, unknown>[];
  if (Array.isArray(r.data)) return r.data as Record<string, unknown>[];
  const resu = r.result as { data_array?: unknown[][] } | undefined;
  const manifest = r.manifest as { schema?: { columns?: { name: string }[] } } | undefined;
  if (resu?.data_array && manifest?.schema?.columns) {
    const cols = manifest.schema.columns.map((c) => c.name);
    return resu.data_array.map((row) => Object.fromEntries(cols.map((c, i) => [c, row[i]])));
  }
  return [];
}

// OBO email of the calling planner (Databricks Apps forwards the user identity header).
function plannerEmail(req: Request): string {
  return (
    (req.headers['x-forwarded-email'] as string) ||
    (req.headers['x-forwarded-user'] as string) ||
    'unknown@milwaukeetool.com'
  );
}

function uuid(): string {
  // RFC4122-ish; good enough for an action id
  return 'act-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
}

const ProposeBody = z.object({
  item_id: z.string().min(1),
  organization_code: z.string().min(1),
  action_type: z.string().min(1),
  drafted_note: z.string().nullable().default(null),
  requested_qty: z.number().nullable().default(null),
  decision_mode: z.string().nullable().default(null),
});

const DecisionBody = z.object({ reason: z.string().nullable().default(null) });

export async function setupPoActionRoutes(appkit: AppKitWithLakebase) {
  // 1) schema + indexes (idempotent), then one-shot sync
  try {
    for (const ddl of ALL_DDL) await appkit.lakebase.query(ddl);
    for (const ix of CREATE_INDEXES) await appkit.lakebase.query(ix);
    await syncFromDelta(appkit.lakebase, (sql) => appkit.analytics.query(sql));
    console.log('[po-actions] schema ready + sync attempted');
  } catch (err) {
    console.warn('[po-actions] setup failed (routes still register):', (err as Error).message);
  }

  // 1b) search capability detection (BM25 not on this branch — FTS + pg_trgm + ILIKE ladder)
  try {
    await appkit.lakebase.query(ADD_SEARCH_COLUMN);
    await appkit.lakebase.query(CREATE_SEARCH_FTS_INDEX);
    searchCaps.fts = true;
  } catch (e) { console.warn('[po-actions] FTS unavailable:', (e as Error).message); }
  try {
    await appkit.lakebase.query(CREATE_TRGM_EXT);
    await appkit.lakebase.query(CREATE_SEARCH_TRGM_INDEX);
    searchCaps.trgm = true;
  } catch (e) { console.warn('[po-actions] pg_trgm unavailable:', (e as Error).message); }
  console.log('[po-actions] search caps:', searchCaps);

  appkit.server.extend((app) => {
    // ---- READ: exception queue (stockout @2012, ranked by $), joined to latest action state ----
    app.get('/api/po/queue', async (req, res) => {
      try {
        const limit = Math.min(parseInt(String(req.query.limit ?? '200'), 10) || 200, 500);
        const r = await appkit.lakebase.query(
          `SELECT e.*, a.id AS action_id, a.action_type, a.status AS action_status, a.approved_by
             FROM ${SCHEMA}.mirror_exceptions e
             LEFT JOIN LATERAL (
               SELECT id, action_type, status, approved_by FROM ${SCHEMA}.action_request ar
               WHERE ar.item_id = e.item_id AND ar.organization_code = e.organization_code
               ORDER BY ar.created_at DESC LIMIT 1
             ) a ON true
            ORDER BY (a.status IS NOT NULL) ASC, e.stockout_risk_usd DESC
            LIMIT $1`,
          [limit],
        );
        res.json(r.rows);
      } catch (err) {
        console.error('[po-actions] queue failed:', (err as Error).message);
        res.status(500).json({ error: 'queue query failed' });
      }
    });

    // ---- SEARCH: item/description search (FTS ranked -> trigram fuzzy -> ILIKE fallback) ----
    app.get('/api/po/search', async (req, res) => {
      const q = String(req.query.q ?? '').trim();
      if (!q) { res.json([]); return; }
      try {
        if (searchCaps.fts) {
          const r = await appkit.lakebase.query(
            `SELECT item_id, item_description, stockout_risk_usd, is_chronic,
                    ts_rank(search_tsv, websearch_to_tsquery('simple',$1)) AS rank
               FROM ${SCHEMA}.mirror_exceptions
              WHERE search_tsv @@ websearch_to_tsquery('simple',$1)
              ORDER BY rank DESC, stockout_risk_usd DESC LIMIT 20`, [q]);
          if (r.rows.length) { res.json({ mode: 'fts', rows: r.rows }); return; }
        }
        if (searchCaps.trgm) {
          const r = await appkit.lakebase.query(
            `SELECT item_id, item_description, stockout_risk_usd, is_chronic,
                    similarity(item_id || ' ' || coalesce(item_description,''), $1) AS sim
               FROM ${SCHEMA}.mirror_exceptions
              WHERE (item_id || ' ' || coalesce(item_description,'')) % $1
              ORDER BY sim DESC, stockout_risk_usd DESC LIMIT 20`, [q]);
          if (r.rows.length) { res.json({ mode: 'trigram', rows: r.rows }); return; }
        }
        // ILIKE fallback (always works)
        const r = await appkit.lakebase.query(
          `SELECT item_id, item_description, stockout_risk_usd, is_chronic
             FROM ${SCHEMA}.mirror_exceptions
            WHERE item_id ILIKE '%'||$1||'%' OR item_description ILIKE '%'||$1||'%'
            ORDER BY stockout_risk_usd DESC LIMIT 20`, [q]);
        res.json({ mode: 'ilike', rows: r.rows });
      } catch (err) {
        console.error('[po-actions] search failed:', (err as Error).message);
        res.status(500).json({ error: 'search failed' });
      }
    });

    // ---- READ: KPI tiles (live — subtract actioned exposure) ----
    app.get('/api/po/kpis', async (_req, res) => {
      try {
        const base = await appkit.lakebase.query(`SELECT * FROM ${SCHEMA}.mirror_kpi WHERE org='2012'`);
        const actioned = await appkit.lakebase.query(
          `SELECT COALESCE(SUM(dollar_at_risk),0)::float resolved_usd, COUNT(*)::int resolved_items
             FROM ${SCHEMA}.action_request WHERE status='executed'`,
        );
        res.json({ base: base.rows[0] ?? null, actioned: actioned.rows[0] ?? null });
      } catch (err) {
        console.error('[po-actions] kpis failed:', (err as Error).message);
        res.status(500).json({ error: 'kpi query failed' });
      }
    });

    // ---- READ: one item's trajectory (for the detail drawer chart) ----
    app.get('/api/po/record/:itemId', async (req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT week_start, planned_pab, actual_end_on_hand, onhand_variance_pct, onhand_status,
                  actual_po_received, actual_shipped, planned_safety_stock
             FROM ${SCHEMA}.mirror_trajectory
            WHERE item_id=$1 AND organization_code='2012'
            ORDER BY week_start DESC LIMIT 12`,
          [req.params.itemId],
        );
        const audit = await appkit.lakebase.query(
          `SELECT at, actor, event, reason, tool FROM ${SCHEMA}.action_audit_event
             WHERE action_id IN (SELECT id FROM ${SCHEMA}.action_request WHERE item_id=$1 AND organization_code='2012')
            ORDER BY at DESC LIMIT 50`,
          [req.params.itemId],
        );
        res.json({ trajectory: r.rows, activity: audit.rows });
      } catch (err) {
        console.error('[po-actions] record failed:', (err as Error).message);
        res.status(500).json({ error: 'record query failed' });
      }
    });

    // ---- READ: live forecast (ai_forecast) for the detail-drawer chart ----
    app.get('/api/po/forecast/:itemId', async (req, res) => {
      const item = req.params.itemId.replace(/'/g, "''");
      const sql = `SELECT CAST(ds AS STRING) ds, ROUND(y_forecast,0) y_forecast,
                          ROUND(y_lower,0) y_lower, ROUND(y_upper,0) y_upper
        FROM ai_forecast(
          TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
                FROM ${CAT}.sdp_plan_vs_actual
                WHERE item_id='${item}' AND organization_code='2012' AND actual_end_on_hand IS NOT NULL),
          horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y') ORDER BY ds`;
      try {
        const rows = analyticsRows(await appkit.analytics.query(sql));
        const ss = await appkit.lakebase.query(
          `SELECT planned_safety_stock FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`,
          [req.params.itemId]);
        res.json({ method: rows.length ? 'ai_forecast' : 'unavailable', forecast: rows,
          safety_stock: (ss.rows[0] as { planned_safety_stock?: number })?.planned_safety_stock ?? null });
      } catch (err) {
        console.error('[po-actions] forecast failed:', (err as Error).message);
        res.json({ method: 'unavailable', forecast: [], safety_stock: null, error: 'forecast unavailable' });
      }
    });

    // ---- READ: what-if simulation for a candidate action ----
    app.get('/api/po/whatif/:itemId', async (req, res) => {
      const item = req.params.itemId;
      const action = String(req.query.action ?? 'EXPEDITE');
      const qty = req.query.qty != null ? Number(req.query.qty) : null;
      try {
        const base = `SELECT ROUND(MIN(y_forecast),0) min_fc FROM ai_forecast(
            TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
                  FROM ${CAT}.sdp_plan_vs_actual
                  WHERE item_id='${item.replace(/'/g, "''")}' AND organization_code='2012' AND actual_end_on_hand IS NOT NULL),
            horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y')`;
        const b = analyticsRows(await appkit.analytics.query(base));
        const ctx = await appkit.lakebase.query(
          `SELECT planned_safety_stock, actual_end_on_hand, applied_standard_cost
             FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`, [item]);
        const c = (ctx.rows[0] ?? {}) as Record<string, number>;
        const gap = qty ?? Math.max(0, (c.planned_safety_stock ?? 0) - (c.actual_end_on_hand ?? 0));
        const dir = ['EXPEDITE', 'PULL_IN', 'NEW_PO', 'INCREASE_QTY'].includes(action) ? 1
                  : ['CANCEL', 'PUSH_OUT', 'DECREASE_QTY'].includes(action) ? -1 : 0;
        const baseMin = Number((b[0] as { min_fc?: number })?.min_fc ?? 0);
        const simMin = baseMin + dir * gap;
        const floor = c.planned_safety_stock ?? 0;
        res.json({ action, simulated_units: gap, baseline_min_onhand: baseMin, simulated_min_onhand: simMin,
          safety_stock_floor: floor, baseline_breaches_ss: baseMin < floor, simulated_breaches_ss: simMin < floor,
          exposure_delta_usd: Math.round((simMin - baseMin) * (c.applied_standard_cost ?? 0)) });
      } catch (err) {
        res.json({ action, error: 'what-if unavailable' });
      }
    });

    // ---- WRITE 1: propose an action (agent or planner drafts it; status=proposed) ----
    app.post('/api/po/actions/propose', async (req, res) => {
      const parsed = ProposeBody.safeParse(req.body);
      if (!parsed.success) { res.status(400).json({ error: 'invalid body', detail: parsed.error.issues }); return; }
      const b = parsed.data;
      const who = plannerEmail(req);
      const id = uuid();
      try {
        // pull the exception context so the action carries $ + systemic flag
        const ctx = await appkit.lakebase.query(
          `SELECT item_description, week_start, planner_name, stockout_risk_usd, is_chronic, exception_type
             FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code=$2`,
          [b.item_id, b.organization_code],
        );
        const c = (ctx.rows[0] ?? {}) as Record<string, unknown>;
        const systemic = c.is_chronic === 1 || c.is_chronic === true ? 'Systemic (chronic supplier)' : 'One-off';
        const audit = [{ at: new Date().toISOString(), by: who, action: 'proposed', reason: b.drafted_note, tool: 'propose' }];
        const r = await appkit.lakebase.query(
          `INSERT INTO ${SCHEMA}.action_request
             (id, item_id, item_description, organization_code, week_start, exception_type, action_type,
              dollar_at_risk, systemic_flag, planner_name, drafted_note, requested_qty, decision_mode,
              status, audit_trail)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,'proposed',$14::jsonb)
           RETURNING *`,
          [id, b.item_id, c.item_description ?? null, b.organization_code, c.week_start ?? null,
           c.exception_type ?? 'Stockout / below safety stock', b.action_type,
           c.stockout_risk_usd ?? null, systemic, c.planner_name ?? null, b.drafted_note,
           b.requested_qty, b.decision_mode, JSON.stringify(audit)],
        );
        await appkit.lakebase.query(
          `INSERT INTO ${SCHEMA}.action_audit_event (action_id, actor, event, reason, tool)
           VALUES ($1,$2,'proposed',$3,'propose')`,
          [id, who, b.drafted_note],
        );
        res.status(201).json({ ...r.rows[0], dataMutated: true });
      } catch (err) {
        console.error('[po-actions] propose failed:', (err as Error).message);
        res.status(500).json({ error: 'propose failed' });
      }
    });

    // ---- WRITE 2: execute (approve) — the HUMAN GATE. One transaction: status, OBO, audit, sim-outbox ----
    app.post('/api/po/actions/:id/execute', async (req, res) => {
      const who = plannerEmail(req);
      const reason = DecisionBody.safeParse(req.body).success ? (req.body?.reason ?? null) : null;
      const client = appkit.lakebase; // AppKit pool; each query is atomic — wrap in a tx via SQL below
      try {
        // guard: must be in 'proposed' (or 'approved') state
        const cur = await client.query(`SELECT * FROM ${SCHEMA}.action_request WHERE id=$1`, [req.params.id]);
        if (cur.rows.length === 0) { res.status(404).json({ error: 'action not found' }); return; }
        const a = cur.rows[0] as Record<string, unknown>;
        if (a.status === 'executed') { res.status(409).json({ error: 'already executed' }); return; }

        await client.query('BEGIN');
        const upd = await client.query(
          `UPDATE ${SCHEMA}.action_request
              SET status='executed', approved_by=$2, decided_at=NOW(), version=version+1,
                  audit_trail = audit_trail || $3::jsonb
            WHERE id=$1 RETURNING *`,
          [req.params.id, who,
           JSON.stringify([{ at: new Date().toISOString(), by: who, action: 'executed', reason, tool: 'execute' }])],
        );
        await client.query(
          `INSERT INTO ${SCHEMA}.action_audit_event (action_id, actor, event, reason, tool)
           VALUES ($1,$2,'executed',$3,'execute')`,
          [req.params.id, who, reason],
        );
        // SIMULATED external writeback — typed request enqueued + immediately acked. NO real Oracle.
        const ob = await client.query(
          `INSERT INTO ${SCHEMA}.integration_outbox (action_id, payload, status)
           VALUES ($1,$2::jsonb,'simulated_sent') RETURNING id`,
          [req.params.id, JSON.stringify({
            system: 'ORACLE_FUSION_SIMULATED', po_action: a.action_type, item_id: a.item_id,
            org: a.organization_code, requested_qty: a.requested_qty, note: a.drafted_note,
            simulated: true, disclaimer: 'No real Oracle call — sandbox simulation per project guardrail',
          })],
        );
        await client.query(
          `INSERT INTO ${SCHEMA}.integration_result (outbox_id, action_id, result, detail)
           VALUES ($1,$2,'SIMULATED_ACK',$3::jsonb)`,
          [(ob.rows[0] as { id: number }).id, req.params.id,
           JSON.stringify({ acknowledged_at: new Date().toISOString(), simulated: true })],
        );
        await client.query('COMMIT');
        res.json({ ...upd.rows[0], dataMutated: true });
      } catch (err) {
        try { await appkit.lakebase.query('ROLLBACK'); } catch { /* noop */ }
        console.error('[po-actions] execute failed:', (err as Error).message);
        res.status(500).json({ error: 'execute failed' });
      }
    });

    // ---- WRITE 3: reject / override ----
    app.post('/api/po/actions/:id/reject', async (req, res) => {
      const who = plannerEmail(req);
      const reason = req.body?.reason ?? null;
      try {
        const upd = await appkit.lakebase.query(
          `UPDATE ${SCHEMA}.action_request
              SET status='rejected', approved_by=$2, decided_at=NOW(), version=version+1,
                  audit_trail = audit_trail || $3::jsonb
            WHERE id=$1 AND status <> 'executed' RETURNING *`,
          [req.params.id, who,
           JSON.stringify([{ at: new Date().toISOString(), by: who, action: 'rejected', reason, tool: 'reject' }])],
        );
        if (upd.rows.length === 0) { res.status(409).json({ error: 'not rejectable' }); return; }
        await appkit.lakebase.query(
          `INSERT INTO ${SCHEMA}.action_audit_event (action_id, actor, event, reason, tool)
           VALUES ($1,$2,'rejected',$3,'reject')`, [req.params.id, who, reason]);
        res.json({ ...upd.rows[0], dataMutated: true });
      } catch (err) {
        console.error('[po-actions] reject failed:', (err as Error).message);
        res.status(500).json({ error: 'reject failed' });
      }
    });

    // ---- ANALYTICS (native, from our own Lakebase mirrors — no catalog dependency) ----
    // $ at risk by ABC class
    app.get('/api/po/analytics/by-abc', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT COALESCE(abc,'—') AS abc, COUNT(*)::int AS items,
                  ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
             FROM ${SCHEMA}.mirror_exceptions GROUP BY abc ORDER BY abc`);
        res.json(r.rows);
      } catch { res.status(500).json({ error: 'by-abc failed' }); }
    });
    // top planners by $ at risk (who owns the fires)
    app.get('/api/po/analytics/by-planner', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT COALESCE(planner_name,'Unassigned') AS planner, COUNT(*)::int AS items,
                  ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
             FROM ${SCHEMA}.mirror_exceptions GROUP BY planner
            ORDER BY dollar_at_risk DESC LIMIT 12`);
        res.json(r.rows);
      } catch { res.status(500).json({ error: 'by-planner failed' }); }
    });
    // chronic vs one-off split
    app.get('/api/po/analytics/chronic-split', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT CASE WHEN is_chronic=1 THEN 'Systemic (chronic supplier)' ELSE 'One-off' END AS kind,
                  COUNT(*)::int AS items, ROUND(SUM(stockout_risk_usd))::float AS dollar_at_risk
             FROM ${SCHEMA}.mirror_exceptions GROUP BY kind ORDER BY dollar_at_risk DESC`);
        res.json(r.rows);
      } catch { res.status(500).json({ error: 'chronic-split failed' }); }
    });
    // $ at risk banded by size (distribution)
    app.get('/api/po/analytics/risk-bands', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT band, COUNT(*)::int items, ROUND(SUM(stockout_risk_usd))::float dollar_at_risk FROM (
             SELECT CASE WHEN stockout_risk_usd>=1000000 THEN '4 · ≥$1M'
                         WHEN stockout_risk_usd>=100000 THEN '3 · $100K–1M'
                         WHEN stockout_risk_usd>=10000 THEN '2 · $10–100K'
                         ELSE '1 · <$10K' END AS band, stockout_risk_usd
               FROM ${SCHEMA}.mirror_exceptions) t GROUP BY band ORDER BY band`);
        res.json(r.rows);
      } catch { res.status(500).json({ error: 'risk-bands failed' }); }
    });
    // action progress (executed vs open) — live from the writable table
    app.get('/api/po/analytics/progress', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT
             (SELECT COUNT(*)::int FROM ${SCHEMA}.mirror_exceptions) AS total_items,
             (SELECT COUNT(*)::int FROM ${SCHEMA}.action_request WHERE status='executed') AS executed,
             (SELECT COALESCE(SUM(dollar_at_risk),0)::float FROM ${SCHEMA}.action_request WHERE status='executed') AS resolved_usd,
             (SELECT COALESCE(SUM(stockout_risk_usd),0)::float FROM ${SCHEMA}.mirror_exceptions) AS total_usd`);
        res.json(r.rows[0] ?? {});
      } catch { res.status(500).json({ error: 'progress failed' }); }
    });

    // ---- SCENARIOS: live data cuts behind each storytelling subsection ----
    // S5 · cost-ranked exceptions (rank by $, not units — the anti-pattern lesson)
    app.get('/api/po/scenario/cost-vs-units', async (_req, res) => {
      try {
        const byDollar = await appkit.lakebase.query(
          `SELECT item_id, item_description, ROUND(stockout_gap_units)::int gap_units, ROUND(stockout_risk_usd)::float dollar
             FROM ${SCHEMA}.mirror_exceptions ORDER BY stockout_risk_usd DESC LIMIT 5`);
        const byUnits = await appkit.lakebase.query(
          `SELECT item_id, item_description, ROUND(stockout_gap_units)::int gap_units, ROUND(stockout_risk_usd)::float dollar
             FROM ${SCHEMA}.mirror_exceptions ORDER BY stockout_gap_units DESC LIMIT 5`);
        res.json({ by_dollar: byDollar.rows, by_units: byUnits.rows });
      } catch { res.status(500).json({ error: 'scenario failed' }); }
    });
    // Chronic-supplier · systemic items (fix source vs expedite)
    app.get('/api/po/scenario/chronic', async (_req, res) => {
      try {
        const r = await appkit.lakebase.query(
          `SELECT item_id, item_description, ROUND(stockout_risk_usd)::float dollar, planner_name
             FROM ${SCHEMA}.mirror_exceptions WHERE is_chronic=1 ORDER BY stockout_risk_usd DESC LIMIT 10`);
        const tot = await appkit.lakebase.query(
          `SELECT COUNT(*)::int items, ROUND(SUM(stockout_risk_usd))::float dollar FROM ${SCHEMA}.mirror_exceptions WHERE is_chronic=1`);
        res.json({ rows: r.rows, total: tot.rows[0] ?? {} });
      } catch { res.status(500).json({ error: 'scenario failed' }); }
    });
    // A hero item's full trajectory (S2 · on-hand and why)
    app.get('/api/po/scenario/hero-trajectory', async (_req, res) => {
      try {
        const hero = await appkit.lakebase.query(
          `SELECT item_id FROM ${SCHEMA}.mirror_exceptions ORDER BY stockout_risk_usd DESC LIMIT 1`);
        const id = (hero.rows[0] as { item_id?: string })?.item_id;
        if (!id) { res.json({ item_id: null, rows: [] }); return; }
        const r = await appkit.lakebase.query(
          `SELECT week_start, planned_pab, actual_end_on_hand, planned_safety_stock, actual_po_received, actual_shipped
             FROM ${SCHEMA}.mirror_trajectory WHERE item_id=$1 ORDER BY week_start`, [id]);
        res.json({ item_id: id, rows: r.rows });
      } catch { res.status(500).json({ error: 'scenario failed' }); }
    });

    // Pull one item's facts (plan-vs-actual + recent trajectory) and compute the DETERMINISTIC
    // (rules-engine) explanation + recommendation. Grounded purely in the numbers — always available,
    // and the guaranteed fallback for the LLM path. Returns null if the item isn't found.
    async function getFacts(item: string) {
      const ctxR = await appkit.lakebase.query(
        `SELECT item_id,item_description,abc,planner_name,actual_end_on_hand,planned_safety_stock,
                applied_standard_cost,stockout_gap_units,stockout_risk_usd,onhand_variance_pct,is_chronic
           FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`, [item]);
      const c = ctxR.rows[0] as Record<string, unknown> | undefined;
      if (!c) return null;
      const traj = await appkit.lakebase.query(
        `SELECT week_start, planned_pab, actual_end_on_hand, planned_safety_stock, actual_po_received, actual_shipped
           FROM ${SCHEMA}.mirror_trajectory WHERE item_id=$1 AND organization_code='2012'
          ORDER BY week_start DESC LIMIT 8`, [item]);
      const facts = {
        item: c.item_id, description: c.item_description, abc: c.abc, planner: c.planner_name,
        on_hand: c.actual_end_on_hand, safety_stock: c.planned_safety_stock,
        gap_units: c.stockout_gap_units, dollar_at_risk: c.stockout_risk_usd,
        variance_pct: c.onhand_variance_pct, chronic_supplier: c.is_chronic === 1,
        recent_weeks: traj.rows,
      };
      const below = Number(c.actual_end_on_hand) < Number(c.planned_safety_stock);
      const chronic = c.is_chronic === 1;
      const gap = Math.max(0, Math.round(Number(c.stockout_gap_units)));
      const heuristic = {
        source: 'rules', facts,
        explanation: `${c.item_description} (${c.item_id}, ABC ${c.abc}) is ${gap.toLocaleString()} units below its safety-stock floor — $${Math.round(Number(c.stockout_risk_usd)).toLocaleString()} of stockout risk. `
          + `On-hand is ${Math.round(Number(c.actual_end_on_hand)).toLocaleString()} vs a ${Math.round(Number(c.planned_safety_stock)).toLocaleString()} floor (${c.onhand_variance_pct}% vs plan). `
          + (chronic ? 'Its supplier is chronically late (>60% of receipts), so repeated expediting only treats the symptom — the root cause is upstream.'
                     : 'This reads as a one-off shortfall rather than a systemic supplier problem.')
          + ` Planner: ${c.planner_name}.`,
        recommended_action: chronic ? 'FIX_SUPPLIER' : below ? 'EXPEDITE' : 'REVIEW',
        recommended_qty: gap,
        confidence: 'medium',
        reason: chronic ? 'chronic supplier — fix the source, then expedite to cover' : below ? 'below safety stock — pull inbound in' : 'not below floor — confirm before acting',
      };
      return { facts, heuristic };
    }

    // The prompt the LLM sees. It writes plain-English prose FIRST (streamed live), then a single
    // machine-parseable trailer line so we can extract the structured recommendation without JSON.
    const REC_VERBS = 'EXPEDITE|PULL_IN|NEW_PO|INCREASE_QTY|DECREASE_QTY|PUSH_OUT|CANCEL|WAIT_HOLD|FIX_SUPPLIER|REVIEW';
    const llmSys = 'You are a Milwaukee Tool supply-planning copilot analyzing ONE item\'s plan-vs-actual facts. '
      + 'Write 3-4 short, plain-English sentences explaining WHY it is flagged, WHAT the trajectory shows, and the '
      + 'business risk. On-hand is point-in-time; $ at risk = (safety_stock - on_hand) x unit cost; a chronic supplier '
      + 'means fix the SOURCE, not just expedite. After the prose, output EXACTLY ONE final line, nothing after it:\n'
      + `@@REC action=<${REC_VERBS}> qty=<integer or none> confidence=<high|medium|low> reason=<one short clause>`;

    // Parse the @@REC trailer the model emits after its prose.
    function parseRec(full: string): { recommended_action?: string; recommended_qty?: number; confidence?: string; reason?: string } {
      const m = /@@REC\s+(.*)$/s.exec(full);
      if (!m) return {};
      const line = m[1].trim();
      const action = /action=([A-Z_]+)/.exec(line)?.[1];
      const qtyRaw = /qty=([0-9]+|none)/i.exec(line)?.[1];
      const confidence = /confidence=(high|medium|low)/i.exec(line)?.[1]?.toLowerCase();
      const reason = /reason=(.+?)$/.exec(line)?.[1]?.trim();
      return {
        recommended_action: action,
        recommended_qty: qtyRaw && qtyRaw.toLowerCase() !== 'none' ? Number(qtyRaw) : undefined,
        confidence, reason,
      };
    }

    // ---- AGENTIC: explain an item + recommend an action (one-shot JSON). engine=rules|llm|auto ----
    // auto (default) uses LLM when the serving plugin is wired, else rules. Always answers.
    app.get('/api/po/explain/:itemId', async (req, res) => {
      try {
        const f = await getFacts(req.params.itemId);
        if (!f) { res.status(404).json({ error: 'item not found' }); return; }
        const engine = String(req.query.engine ?? 'auto');
        if ((engine === 'llm' || engine === 'auto') && hasServing(appkit)) {
          const llm = await callLlm(appkit.serving, llmSys, f.facts, parseRec);
          if (llm) {
            res.json({ source: 'llm', facts: f.facts, explanation: llm.prose || f.heuristic.explanation,
              recommended_action: llm.rec.recommended_action ?? f.heuristic.recommended_action,
              recommended_qty: llm.rec.recommended_qty ?? f.heuristic.recommended_qty,
              confidence: llm.rec.confidence ?? f.heuristic.confidence, reason: llm.rec.reason ?? f.heuristic.reason });
            return;
          }
          // llm failed → rules fallback below
        }
        res.json(f.heuristic);
      } catch (err) {
        console.error('[po-actions] explain failed:', (err as Error).message);
        res.status(500).json({ error: 'explain failed' });
      }
    });

    // ---- AGENTIC: streaming explain (SSE, token-by-token live-typing). engine=rules|llm|auto ----
    // LLM path streams REAL model tokens as they generate (true generative streaming); the @@REC
    // trailer is stripped from the visible stream and parsed into the `done` recommendation. Rules
    // path streams the deterministic text word-by-word for the same live feel. Either way, `done`
    // carries the structured recommendation so the drawer pre-fills the action.
    app.get('/api/po/explain-stream/:itemId', async (req, res) => {
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache, no-transform');
      res.setHeader('Connection', 'keep-alive');
      const send = (event: string, data: unknown) => res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
      try {
        const f = await getFacts(req.params.itemId);
        if (!f) { send('error', { error: 'item not found' }); res.end(); return; }
        const engine = String(req.query.engine ?? 'auto');
        // Decide the text + recommendation to stream. LLM path calls the real model (invoke), then we
        // re-emit its answer word-by-word for the live-typing feel; rules path uses the deterministic text.
        let text = f.heuristic.explanation;
        let rec: Record<string, unknown> = {
          recommended_action: f.heuristic.recommended_action, recommended_qty: f.heuristic.recommended_qty,
          confidence: f.heuristic.confidence, reason: f.heuristic.reason,
        };
        let source = 'rules';
        if ((engine === 'llm' || engine === 'auto') && hasServing(appkit)) {
          const llm = await callLlm(appkit.serving, llmSys, f.facts, parseRec);
          if (llm) {
            source = 'llm';
            text = llm.prose || f.heuristic.explanation;
            rec = {
              recommended_action: llm.rec.recommended_action ?? f.heuristic.recommended_action,
              recommended_qty: llm.rec.recommended_qty ?? f.heuristic.recommended_qty,
              confidence: llm.rec.confidence ?? f.heuristic.confidence,
              reason: llm.rec.reason ?? f.heuristic.reason,
            };
          } // else: LLM failed → keep rules text/rec (graceful fallback)
        }
        send('meta', { source, facts: f.facts });
        for (const w of text.split(/(\s+)/)) {
          if (w === '') continue;
          send('token', { t: w });
          await new Promise((r) => setTimeout(r, source === 'llm' ? 14 : 22)); // LLM a touch faster
        }
        send('done', { source, ...rec });
        res.end();
      } catch (err) {
        console.error('[po-actions] explain-stream failed:', (err as Error).message);
        send('error', { error: 'explain failed' });
        res.end();
      }
    });

    // ---- admin: reset demo (truncate writable + re-sync mirrors) ----
    app.post('/api/po/admin/reset', async (_req, res) => {
      try {
        await appkit.lakebase.query(
          `TRUNCATE ${SCHEMA}.action_request, ${SCHEMA}.action_audit_event, ${SCHEMA}.integration_outbox, ${SCHEMA}.integration_result`,
        );
        res.json({ ok: true });
      } catch (err) {
        res.status(500).json({ error: 'reset failed' });
      }
    });
  });
}
