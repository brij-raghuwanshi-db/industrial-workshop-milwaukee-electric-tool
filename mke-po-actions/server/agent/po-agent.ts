// The PO-actions agent: a tool-calling assistant that investigates why an item is off-plan,
// forecasts its future (ai_forecast), simulates a what-if for a candidate action, ranks actions,
// drafts a rationale, and — behind a HARD human-approval gate — executes the action.
// Discover -> Draft -> Act. execute_action is annotated effect:'destructive' so the AppKit agents
// plugin fires the HITL approval SSE before it runs. No real Oracle: the write is the Lakebase txn.
import { createAgent, tool } from '@databricks/appkit/beta';
import { z } from 'zod';
import { SCHEMA } from '../db/schema-sql';

// Warehouse-run helper for ai_forecast (analytics plugin executes SQL on the warehouse).
async function warehouseQuery(sql: string): Promise<Record<string, unknown>[]> {
  let host = (process.env.DATABRICKS_HOST || '').replace(/\/$/, '');
  if (host && !/^https?:\/\//.test(host)) host = `https://${host}`;
  const token = process.env.DATABRICKS_TOKEN || '';
  const warehouseId = process.env.DATABRICKS_WAREHOUSE_ID || '';
  const resp = await fetch(`${host}/api/2.0/sql/statements`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ statement: sql, warehouse_id: warehouseId, wait_timeout: '30s',
                           disposition: 'INLINE', format: 'JSON_ARRAY' }),
  });
  const data = (await resp.json()) as {
    status?: { state?: string }; result?: { data_array?: unknown[][] };
    manifest?: { schema?: { columns?: { name: string }[] } };
  };
  if (data.status?.state !== 'SUCCEEDED') return [];
  const cols = data.manifest?.schema?.columns?.map((c) => c.name) || [];
  return (data.result?.data_array || []).map((row) =>
    Object.fromEntries(cols.map((c, i) => [c, row[i]])));
}

const CAT = 'sandbox_operations.po_management';

// Lakebase handle is injected via the agents plugin's tool context at setup; but for simplicity we
// re-query through a small module-level ref set by the route wiring (see po-actions.ts registerAgent()).
export type LB = { query(t: string, p?: unknown[]): Promise<{ rows: Record<string, unknown>[] }> };
let lb: LB | null = null;
export function bindLakebase(handle: LB) { lb = handle; }

export const poAgent = createAgent({
  model: process.env.DATABRICKS_SERVING_ENDPOINT_NAME || 'databricks-gpt-oss-120b',
  instructions: [
    'You are the Milwaukee Tool PO-actions copilot for supply planners at DC org 2012.',
    'The dashboard shows WHAT is off-plan; your job is to help the planner ACT.',
    'Follow a strict 3-phase chain: (1) DISCOVER — use ask_data / find_record / forecast_item to explain',
    'why an item is flagged and what its future looks like; (2) DRAFT — use what_if to simulate the',
    'candidate PO action, rank_actions to compare options, and draft_note to write a short rationale with',
    'the $ at risk and the projected stockout impact; then STOP and present the recommendation and ask the',
    'planner to approve. (3) ACT — only after the planner explicitly approves, call execute_action.',
    'NEVER call execute_action without explicit approval. After an action, STOP — do not auto-advance.',
    'Always cite the concrete records (item_id, week, $). Money is ranked by $ at risk, never unit-miss.',
    'On-hand is point-in-time — never sum it across weeks. If a forecast is unavailable, say so and use the',
    'naive trend, labeled as such. This engagement performs a SIMULATED Oracle push only — never a real one.',
  ].join(' '),
  tools(plugins) {
    return {
      // DISCOVER: natural-language "why" over the sdp_* gold via our Genie space
      ...(plugins as { genie?: { toolkit: () => Record<string, unknown> } }).genie?.toolkit?.() ?? {},

      find_record: tool({
        description: 'Get one item\'s recent plan-vs-actual trajectory + current exception context at org 2012.',
        schema: z.object({ item_id: z.string().describe('the SKU / item_id, e.g. 48111881X') }),
        annotations: { effect: 'read' },
        execute: async ({ item_id }) => {
          if (!lb) return 'Lakebase not ready';
          const exc = await lb.query(
            `SELECT item_description, planner_name, stockout_risk_usd, planned_safety_stock,
                    actual_end_on_hand, is_chronic, exception_type
               FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`, [item_id]);
          const traj = await lb.query(
            `SELECT week_start, planned_pab, actual_end_on_hand, onhand_variance_pct, onhand_status,
                    actual_po_received, actual_shipped, planned_safety_stock
               FROM ${SCHEMA}.mirror_trajectory WHERE item_id=$1 AND organization_code='2012'
              ORDER BY week_start DESC LIMIT 12`, [item_id]);
          return JSON.stringify({ context: exc.rows[0] ?? null, trajectory: traj.rows });
        },
      }),

      forecast_item: tool({
        description: 'Live forecast of an item\'s weekly on-hand for the next ~8 weeks using ai_forecast, ' +
          'with the safety-stock floor, to project whether/when it breaches safety stock.',
        schema: z.object({ item_id: z.string().describe('the SKU / item_id') }),
        annotations: { effect: 'read' },
        execute: async ({ item_id }) => {
          const sql = `SELECT ds, ROUND(y_forecast,0) y_forecast, ROUND(y_lower,0) y_lower, ROUND(y_upper,0) y_upper
            FROM ai_forecast(
              TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
                    FROM ${CAT}.sdp_plan_vs_actual
                    WHERE item_id='${item_id.replace(/'/g, "''")}' AND organization_code='2012'
                      AND actual_end_on_hand IS NOT NULL),
              horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y') ORDER BY ds`;
          try {
            const rows = await warehouseQuery(sql);
            if (!rows.length) return 'Forecast unavailable (insufficient history) — use the naive last-value trend.';
            return JSON.stringify({ method: 'ai_forecast', horizon_weeks: 8, forecast: rows });
          } catch (e) {
            return `Forecast error (${(e as Error).message}); fall back to naive trend, labeled as such.`;
          }
        },
      }),

      what_if: tool({
        description: 'Simulate a candidate PO action for an item and compare the forecast: baseline vs ' +
          'the action applied to future supply. Returns the projected stockout-week shift and $ delta. ' +
          'action one of EXPEDITE, PULL_IN, PUSH_OUT, CANCEL, NEW_PO, REBALANCE.',
        schema: z.object({
          item_id: z.string(),
          action: z.string().describe('EXPEDITE | PULL_IN | PUSH_OUT | CANCEL | NEW_PO | REBALANCE'),
          qty: z.number().nullable().describe('units to add/remove/expedite; null = use planned gap'),
        }),
        annotations: { effect: 'read' },
        execute: async ({ item_id, action, qty }) => {
          // baseline forecast
          const base = `SELECT ROUND(AVG(y_forecast),0) avg_fc, ROUND(MIN(y_forecast),0) min_fc FROM ai_forecast(
              TABLE(SELECT to_timestamp(week_start) AS ds, CAST(actual_end_on_hand AS DOUBLE) AS y
                    FROM ${CAT}.sdp_plan_vs_actual
                    WHERE item_id='${item_id.replace(/'/g, "''")}' AND organization_code='2012'
                      AND actual_end_on_hand IS NOT NULL),
              horizon => date_add(current_date(), 56), time_col => 'ds', value_col => 'y')`;
          try {
            const b = await warehouseQuery(base);
            const ss = lb ? await lb.query(
              `SELECT planned_safety_stock, actual_end_on_hand, applied_standard_cost FROM ${SCHEMA}.mirror_exceptions
                 WHERE item_id=$1 AND organization_code='2012'`, [item_id]) : { rows: [] };
            const ctx = (ss.rows[0] ?? {}) as Record<string, number>;
            // apply the action to the forecast as a level shift (simple, transparent simulation)
            const gap = qty ?? Math.max(0, (ctx.planned_safety_stock ?? 0) - (ctx.actual_end_on_hand ?? 0));
            const dir = ['EXPEDITE', 'PULL_IN', 'NEW_PO'].includes(action) ? 1
                      : ['CANCEL', 'PUSH_OUT'].includes(action) ? -1 : 0;
            const baseMin = Number((b[0] as { min_fc?: number })?.min_fc ?? 0);
            const simMin = baseMin + dir * gap;
            const floor = ctx.planned_safety_stock ?? 0;
            const cost = ctx.applied_standard_cost ?? 0;
            return JSON.stringify({
              action, simulated_units: gap,
              baseline_min_onhand: baseMin, simulated_min_onhand: simMin, safety_stock_floor: floor,
              baseline_breaches_ss: baseMin < floor, simulated_breaches_ss: simMin < floor,
              exposure_delta_usd: Math.round((simMin - baseMin) * cost),
              read: dir === 1 ? 'action adds cover' : dir === -1 ? 'action reduces cover' : 'no on-hand effect',
              note: 'Transparent level-shift simulation over the ai_forecast baseline; not a full re-plan.',
            });
          } catch (e) {
            return `What-if error (${(e as Error).message}).`;
          }
        },
      }),

      rank_actions: tool({
        description: 'Rank candidate actions for an item by fit given its stockout gap, chronic-supplier ' +
          'status and $ at risk. Returns an ordered recommendation with reasons.',
        schema: z.object({ item_id: z.string() }),
        annotations: { effect: 'read' },
        execute: async ({ item_id }) => {
          if (!lb) return 'Lakebase not ready';
          const r = await lb.query(
            `SELECT stockout_risk_usd, planned_safety_stock, actual_end_on_hand, is_chronic
               FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`, [item_id]);
          const c = (r.rows[0] ?? {}) as Record<string, number>;
          const below = (c.actual_end_on_hand ?? 0) < (c.planned_safety_stock ?? 0);
          const chronic = c.is_chronic === 1;
          const ranked = below
            ? (chronic
                ? [['FIX_SUPPLIER', 'chronically-late supplier — fixing the source beats repeated expedites'],
                   ['EXPEDITE', 'pull the next inbound in to cover the safety-stock breach'],
                   ['NEW_PO', 'if no open PO covers the gap']]
                : [['EXPEDITE', 'below safety stock, one-off — pull inbound in'],
                   ['PULL_IN', 'move the nearest PO earlier'],
                   ['NEW_PO', 'if coverage gap remains']])
            : [['REVIEW', 'not below safety stock — confirm before acting'],
               ['PUSH_OUT', 'if overstocked, delay inbound']];
          return JSON.stringify({ item_id, dollar_at_risk: c.stockout_risk_usd, chronic, ranked });
        },
      }),

      draft_note: tool({
        description: 'Draft a short (1-2 sentence) rationale for a chosen action, citing $ at risk and the ' +
          'projected impact. Returned to be shown to the planner before approval.',
        schema: z.object({ item_id: z.string(), action: z.string(), rationale: z.string() }),
        annotations: { effect: 'read' },
        execute: async ({ item_id, action, rationale }) =>
          `Proposed ${action} for ${item_id}: ${rationale}`,
      }),

      execute_action: tool({
        description: 'Execute (approve) a PO action for an item. THE WRITE. Only call after the planner ' +
          'explicitly approves. Captures BOTH what you recommended and what the planner finally committed ' +
          '(plus an override reason if they changed it) — this feeds the MLflow evaluation dataset. Writes ' +
          'to Lakebase with an audit trail + a SIMULATED Oracle push. Verbs: EXPEDITE, PULL_IN, PUSH_OUT, ' +
          'CANCEL, NEW_PO, INCREASE_QTY, DECREASE_QTY, WAIT_HOLD, SPLIT_SHIPMENT, REBALANCE, SUBSTITUTE, ESCALATE, REVIEW.',
        schema: z.object({
          item_id: z.string(),
          recommended_action: z.string().describe('the verb YOU recommended'),
          recommended_qty: z.number().nullable().describe('the quantity you recommended, e.g. 100'),
          final_action: z.string().describe('the verb the planner committed (often == recommended)'),
          final_qty: z.number().nullable().describe('the quantity the planner committed, e.g. 75'),
          override_reason: z.string().nullable().describe('if the planner changed the rec, why'),
          drafted_note: z.string().nullable(),
        }),
        annotations: { effect: 'destructive' }, // triggers the HITL approval gate
        execute: async (a) => {
          if (!lb) return 'Lakebase not ready';
          const id = 'act-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
          const overridden = a.recommended_action !== a.final_action ||
            (a.recommended_qty ?? null) !== (a.final_qty ?? null);
          const ctx = await lb.query(
            `SELECT item_description, week_start, planner_name, stockout_risk_usd, is_chronic, exception_type
               FROM ${SCHEMA}.mirror_exceptions WHERE item_id=$1 AND organization_code='2012'`, [a.item_id]);
          const c = (ctx.rows[0] ?? {}) as Record<string, unknown>;
          const systemic = c.is_chronic === 1 ? 'Systemic (chronic supplier)' : 'One-off';
          await lb.query(
            `INSERT INTO ${SCHEMA}.action_request
               (id,item_id,item_description,organization_code,week_start,exception_type,action_type,
                dollar_at_risk,systemic_flag,planner_name,drafted_note,requested_qty,
                recommended_action,recommended_qty,final_action,final_qty,override_reason,was_overridden,
                status,approved_by,audit_trail)
             VALUES ($1,$2,$3,'2012',$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,'executed','agent-approved',$18::jsonb)`,
            [id, a.item_id, c.item_description ?? null, c.week_start ?? null,
             c.exception_type ?? 'Stockout / below safety stock', a.final_action, c.stockout_risk_usd ?? null,
             systemic, c.planner_name ?? null, a.drafted_note, a.final_qty,
             a.recommended_action, a.recommended_qty, a.final_action, a.final_qty, a.override_reason, overridden,
             JSON.stringify([{ at: new Date().toISOString(), by: 'agent', action: 'executed',
               recommended: a.recommended_action, final: a.final_action, tool: 'execute_action' }])]);
          // decision-eval row (learning loop / MLflow dataset)
          await lb.query(
            `INSERT INTO ${SCHEMA}.decision_eval
               (action_id,item_id,organization_code,recommended_action,recommended_qty,final_action,final_qty,
                was_overridden,override_reason,decided_by)
             VALUES ($1,$2,'2012',$3,$4,$5,$6,$7,$8,'agent-approved')`,
            [id, a.item_id, a.recommended_action, a.recommended_qty, a.final_action, a.final_qty,
             overridden, a.override_reason]);
          await lb.query(
            `INSERT INTO ${SCHEMA}.integration_outbox (action_id, payload, status)
             VALUES ($1,$2::jsonb,'simulated_sent')`,
            [id, JSON.stringify({ system: 'ORACLE_FUSION_SIMULATED', po_action: a.final_action, item_id: a.item_id,
              org: '2012', qty: a.final_qty, simulated: true })]);
          return JSON.stringify({ ok: true, action_id: id, final_action: a.final_action, item_id: a.item_id,
            was_overridden: overridden, dataMutated: true,
            note: 'Executed to Lakebase + SIMULATED Oracle push; decision captured for MLflow eval.' });
        },
      }),
    };
  },
});
