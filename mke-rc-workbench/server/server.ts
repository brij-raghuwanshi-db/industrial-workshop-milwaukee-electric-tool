import { createApp, analytics, genie, lakebase, server } from '@databricks/appkit';

// Value-ledger honesty rule (DK-21): projected on click; DISMISS → not-acted;
// unrecoverable → loss-avoided (never "saved"). The action-log sums are live from Lakebase.
// baseline/residual are composed CLIENT-side from the live value_baseline analytics query;
// realized requires a two-snapshot read-back that the Job does not publish yet → reported as null.

createApp({
  plugins: [
    analytics(),
    genie(),
    lakebase(),
    server(),
  ],
  async onPluginsReady(appkit) {
    const q = (text: string, params?: unknown[]) => appkit.lakebase.query(text, params as never);

    // ── schema + tables (SP owns rc_app) ──
    await q(`CREATE SCHEMA IF NOT EXISTS rc_app`);
    await q(`CREATE TABLE IF NOT EXISTS rc_app.action_request (
      id SERIAL PRIMARY KEY,
      item_id VARCHAR(64) NOT NULL,
      suggested_action TEXT,
      actual_action TEXT,
      reasoning TEXT,
      override_reason_code VARCHAR(64),
      diverged BOOLEAN DEFAULT false,
      savings_state VARCHAR(32) NOT NULL,
      delta NUMERIC DEFAULT 0,
      created_by VARCHAR(255),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);
    await q(`CREATE TABLE IF NOT EXISTS rc_app.evidence_item (
      id SERIAL PRIMARY KEY,
      case_id VARCHAR(64) NOT NULL,
      cause VARCHAR(32) NOT NULL,
      text TEXT NOT NULL,
      inserted_by VARCHAR(255),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE (case_id, cause)
    )`);

    // ── server-computed ledger from the append-only action log ──
    async function ledger() {
      const r = await q(`SELECT
        COALESCE(SUM(CASE WHEN savings_state='projected'    THEN delta ELSE 0 END),0)::numeric AS projected,
        COALESCE(SUM(CASE WHEN savings_state='not-acted'    THEN delta ELSE 0 END),0)::numeric AS not_acted,
        COALESCE(SUM(CASE WHEN savings_state='loss-avoided' THEN delta ELSE 0 END),0)::numeric AS loss_avoided
        FROM rc_app.action_request`);
      const row = (r.rows?.[0] ?? {}) as Record<string, unknown>;
      const projected = Number(row.projected ?? 0);
      return {
        projected,                                  // live: sum of projected deltas from the action log
        realized: null,                             // no two-snapshot read-back published yet → honest null
        notActed: Number(row.not_acted ?? 0),       // live
        lossAvoided: Number(row.loss_avoided ?? 0), // live
        // baseline + residual are composed client-side from the live value_baseline analytics query
      };
    }

    appkit.server.extend((app) => {
      // identity (Genie trust #1)
      app.get('/api/whoami', (req, res) => {
        res.json({ email: req.header('x-forwarded-email') ?? null, user: req.header('x-forwarded-user') ?? null });
      });

      app.get('/api/ledger', async (_req, res) => { res.json(await ledger()); });

      app.get('/api/log', async (_req, res) => {
        const r = await q(`SELECT to_char(created_at,'HH24:MI') AS when, item_id AS sku,
          suggested_action AS suggested, actual_action AS actual, diverged,
          savings_state, delta FROM rc_app.action_request ORDER BY created_at DESC LIMIT 200`);
        res.json(r.rows ?? []);
      });

      app.get('/api/evidence', async (req, res) => {
        const caseId = String(req.query.case_id ?? '');
        const r = await q(`SELECT cause, text FROM rc_app.evidence_item WHERE case_id=$1 ORDER BY created_at`, [caseId]);
        res.json(r.rows ?? []);
      });

      app.post('/api/evidence', async (req, res) => {
        const { case_id, cause, text } = req.body ?? {};
        if (!case_id || !cause || !text) { res.status(400).json({ error: 'case_id, cause, text required' }); return; }
        const who = req.header('x-forwarded-email') ?? null;
        await q(`INSERT INTO rc_app.evidence_item (case_id, cause, text, inserted_by) VALUES ($1,$2,$3,$4)
                 ON CONFLICT (case_id, cause) DO UPDATE SET text=EXCLUDED.text`, [case_id, cause, text, who]);
        const r = await q(`SELECT cause, text FROM rc_app.evidence_item WHERE case_id=$1 ORDER BY created_at`, [case_id]);
        res.json(r.rows ?? []);
      });

      app.post('/api/action', async (req, res) => {
        const { item_id, kind, suggested, actual, reasoning, override_reason_code, delta } = req.body ?? {};
        if (!item_id || !kind) { res.status(400).json({ error: 'item_id, kind required' }); return; }
        const state = kind === 'transfer' ? 'projected' : kind === 'dismiss' ? 'not-acted' : 'loss-avoided';
        const eff = kind === 'dismiss' ? 0 : Number(delta ?? 0);
        const who = req.header('x-forwarded-email') ?? null;
        const diverged = actual && suggested && actual !== suggested;
        await q(`INSERT INTO rc_app.action_request
          (item_id, suggested_action, actual_action, reasoning, override_reason_code, diverged, savings_state, delta, created_by)
          VALUES ($1,$2,$3,$4,$5,$6,$7,$8::numeric,$9)`,
          [item_id, suggested ?? null, actual ?? suggested ?? null, reasoning ?? null, override_reason_code ?? null, !!diverged, state, eff, who]);
        res.json(await ledger());
      });
    });
  },
}).catch(console.error);
