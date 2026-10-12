# Front-End & Full-Stack Patterns (React / FastAPI / Databricks Apps)

The Milwaukee App is an **actionable control tower**, not a one-way dashboard. Full-stack shape:

```
React UI  →  FastAPI backend-for-frontend  →  Lakebase / Databricks SQL / serving / Genie
          (validates identity, policy, transactions; owns every read/write/approval/action)
```

For iframe / embedding / CORS-vs-CSP / postMessage / clickjacking specifics, see
`platform-gotchas.md`. This file covers how to *build and verify* the full stack so it doesn't
repeat the failure patterns in `lessons-and-evidence.md`.

## Build order: probe → walking skeleton → one vertical slice

> **Probe → Walking skeleton → One vertical business slice → Validate → Add intelligence →
> Add live actions → Harden and promote.**

Do not build horizontal platform assets (many tables, dashboards, Genie, ML, search, reverse
ETL) before one end-to-end user journey is proven.

**Platform probe (before feature work):** confirm workspace auth; confirm the approved source
folder; identify the acting user AND the App service principal; run one SQL Warehouse query; do
one Lakebase read and one write; invoke one serving endpoint if needed; ask one Genie question if
needed; verify permissions, env vars, networking, and resource bindings. This keeps auth/config
defects from surfacing later as "frontend bugs."

**Walking skeleton (first App version, only):** `/health/live`; `/health/ready`; a non-secret
resource-binding diagnostic; one analytical read; one Lakebase write; one read-back confirmation;
correlation IDs across UI → API → DB → logs. *An App process being alive does not prove Lakebase,
SQL, Genie, or Model Serving is ready.*

**First vertical slice (example):** show the largest PO receipt exception from last week, explain
planned vs actual, let the planner assign a root cause and approve a follow-up action, store the
decision in Lakebase, display the new state + audit record. Needs only: one governed dataset, one
exception API, one Lakebase workflow schema, one details page, one approval/writeback, one audit
trail. No forecasting/search/reverse-ETL/broad-agent until this works.

## Required UI states (every operation)

Loading · valid empty · input validation · authorization failure · dependency-unavailable ·
unexpected-error **with correlation ID** · durable success confirmation · updated data after
mutation · action history & provenance.

**A button is not complete because it renders.** Completion means:

> Click → API executes **once** → Lakebase commits → UI reads back the state → audit appears →
> downstream metric/status updates.

## Provenance markers (surface the origin of every intelligent result)

Tag results in the UI/response so a real endpoint is never confused with a heuristic or static
data: `DETERMINISTIC_RULE`, `SQL_METRIC`, `FORECAST_MODEL`, `MODEL_SERVING`, `GENIE`,
`BM25_SEARCH`, `HYBRID_SEARCH`, `AGENT`, `CACHED`, `DEMO_FALLBACK`. Never let the UI imply a real
model/Genie response when it used a fallback.

## API contract (per endpoint)

Request/response schemas · authentication actor · authorization rule · error codes · idempotency
behavior · transaction & concurrency behavior · timeout & retry policy · audit fields ·
representative success / empty / conflict / permission / unavailable responses.

Keep the backend simple: `HTTP route → domain service → platform client`. No microservices,
generic integration framework, GraphQL, or event infrastructure unless scale and team ownership
prove the need. Every route independently authorizes — never trust frontend button state, iframe
origin, or a portal login as an authorization control.

## Databricks Apps manual wiring (easy to miss)

- The App **service principal must be granted `CAN USE`/`CAN MANAGE` manually.**
- **Resources must be explicitly declared and bound to the App** — SQL Warehouse, Lakebase,
  Model Serving endpoints, Genie Agents, Jobs, secrets, volumes. Declare dependencies before app
  code assumes them; workspace resources are bound at deployment. Don't hardcode resource IDs
  throughout the source.
- Don't let the PostgreSQL/Lakebase client silently default to `localhost`.
- Don't report "healthy" when a mandatory resource is absent — readiness must check dependencies.
- Auth: prefer the App/user identity model and OBO where applicable; secrets/OAuth via approved
  Databricks mechanisms, never pasted into code. A model-endpoint permission does not grant the
  underlying UC / Lakebase / external-system permission.

## CORS / auth / networking

- CORS, iframe policy (CSP `frame-ancestors` / `X-Frame-Options`), and CSRF solve **different**
  problems; none replaces server-side authorization. CORS config cannot override anti-framing
  headers on a framed child system.
- Browser→Databricks REST calls commonly hit CORS; route through the FastAPI BFF rather than
  calling Databricks APIs directly from React.
- Test the real network path: third-party-cookie policy, IdP redirects, PrivateLink/VPN/proxy,
  DNS. Provide a full-page fallback link when embedded auth fails.

## Deployment gates

**Before deploy:** verify canonical source folder → locked dependency install → build & type-check
FE+BE → unit & API tests → validate `app.yaml` → confirm declared resources & workspace bindings →
confirm identity & permissions → run locally → browser smoke test → record the version.

**After deploy:** check deployment/build status → inspect runtime logs & environment → call
**readiness** (not just liveness) → run a real representative read → run one safe synthetic write →
verify the DB record + audit trail → confirm the UI reflects the result. Test Apps **locally
before** workspace deployment; deployment is not the test loop.

## Authentication & identity (architecture, not last-minute troubleshooting)

| Scenario | Default authentication |
|---|---|
| Interactive CLI/SDK development | OAuth user-to-machine (U2M) |
| Automated jobs & services | OAuth machine-to-machine (M2M) |
| CI/CD | Workload identity federation / OIDC where available |
| App acting as itself | Injected App service-principal identity |
| App respecting end-user permissions | On-behalf-of-user (OBO) OAuth |
| Lakebase from a Databricks App | OAuth database role with credential rotation |
| External app to Lakebase | Databricks SDK-generated database credentials |
| Model endpoint invocation | Databricks OAuth/token with endpoint permission |
| Foundation-model provider | Databricks auth through Unity AI Gateway |
| Cloud-resource access | Workspace/serverless cloud identity, not embedded cloud keys |

PATs are not the default for new automation (only where no supported OAuth exists and security
permits). A successful login proves **authentication only** — not authorization to use a
warehouse, query a model, read UC data, connect to Lakebase, or invoke a live action.

## Methodical login troubleshooting (never random credential changes)

1. Identify the **target** (account / workspace / SQL warehouse / serving endpoint / Lakebase /
   cloud resource / external API).
2. Identify the **actor** (user / SP / App SP / CI workload / job runtime / OBO identity).
3. Identify the **protocol** (U2M / M2M / OIDC federation / App OAuth / database OAuth / native
   PostgreSQL).
4. Confirm the **host** (account URL vs workspace URL vs Lakebase hostname).
5. Confirm workspace assignment & entitlements.
6. Confirm object permissions (`CAN USE`, `CAN QUERY`, catalog privileges, endpoint perms, DB role).
7. Confirm token audience, issuer, expiry.
8. Confirm the correct CLI/SDK profile and env-var precedence.
9. Confirm network reachability — DNS, ports, proxies, firewalls, PrivateLink.
10. Test with the smallest supported call before debugging app code.
11. Record the working identity/config without exposing secrets.

## Networking — check end-to-end, as first-class architecture

```
Browser → Databricks workspace/App ingress → App runtime → Unity AI Gateway/Model Serving
        → SQL warehouse/Unity Catalog → Lakebase → EDW & operational DBs → ERP/WMS/TMS action APIs
```

Serverless private connectivity uses account-level, regional **Network Connectivity
Configurations (NCC)** attachable to multiple workspaces. For AWS PrivateLink examine: workspace
vs VPC region; inbound vs outbound PrivateLink; NCC attachment; private-endpoint rule status; NLB
endpoint services; resource policies & security groups; routes & firewall; private DNS; required
FQDNs & ports; proxy/egress allowlists; cross-region behavior; connectivity cost. Use the Azure/
GCP equivalents rather than applying AWS terms blindly. For **App ingress** on AWS, DNS must
resolve `databricksapps.com` through the private route — wrong conditional DNS forwarding makes an
App URL resolve publicly or fail from the corporate network. Validate with direct TCP to Lakebase
:5432 and HTTPS :443 platform access. Document a per-dependency connectivity matrix
(`Source | Destination | Protocol/port | Identity | Network path`).

Auth, identity, permissions, and networking are **mandatory deliverables** for an Agentic App —
not afterthoughts.

## Long-running work

A browser request must not stay open while a long investigation or training job runs. FastAPI
starts a durable Job/work item and returns a status ID; the UI polls or subscribes. Don't run
heavy Spark, long training, or fragile background loops in App web workers.

## Anti-overengineering (front-end/app scope)

One business workflow at a time · one canonical application source (no duplicated source dirs) ·
one frontend framework · one backend process initially · one transactional database · no AI for
deterministic calculations · no vector search when SQL/BM25 suffices · no reverse ETL without a
genuine serving need · no real-time endpoint for weekly batch predictions · no Genie for
transactional writebacks · no duplicating whole dashboards inside the App without a workflow need
· no "done" without deployed evidence and user acceptance (see `lessons-and-evidence.md`).
