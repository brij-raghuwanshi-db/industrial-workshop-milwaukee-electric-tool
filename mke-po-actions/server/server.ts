import { createApp, analytics, genie, lakebase, server, serving } from '@databricks/appkit';
import { agents } from '@databricks/appkit/beta';
import { setupPoActionRoutes } from './routes/po-actions';
import { poAgent, bindLakebase, type LB } from './agent/po-agent';

createApp({
  plugins: [
    analytics(),
    genie(),
    lakebase(),
    server(),
    // LLM model-serving (alias 'llm' → a foundation-model endpoint). Powers the LIVE generative
    // explanation; the rules engine remains the guaranteed fallback so the feature never hard-depends on it.
    serving({ endpoints: { llm: { env: 'DATABRICKS_SERVING_ENDPOINT_NAME' } } }),
    // the tool-calling PO copilot; execute_action is effect:'destructive' → HITL approval gate fires
    agents({ agents: { po: poAgent } }),
  ],
  async onPluginsReady(appkit) {
    // give the agent's tools a Lakebase handle (same pool the routes use)
    const lakebaseHandle: LB = { query: (t, p) => appkit.lakebase.query(t, p) };
    bindLakebase(lakebaseHandle);
    await setupPoActionRoutes(appkit);
  },
}).catch(console.error);
