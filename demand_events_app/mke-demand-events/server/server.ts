import { createApp, analytics, lakebase, server } from '@databricks/appkit';
import { setupDemandEventsRoutes } from './routes/demand-events/routes';

createApp({
  plugins: [
    analytics(),
    lakebase(),
    server(),
  ],
  async onPluginsReady(appkit) {
    await setupDemandEventsRoutes(appkit);
  },
}).catch(console.error);
