# Platform Gotchas — Know Them Before You Use Anything

For **everything** we use, know the gotchas: a working URL/demo does not prove it embeds
securely, deploys reproducibly, is authorized correctly, or is safe under retry. Maintain a
gotcha register per product/library/model/prompt/tool.

> Related: `frontend-fullstack.md` covers building the React/FastAPI/Apps stack (probe, walking
> skeleton, UI states, API contracts, SP/resource wiring, deployment gates); this file is the
> embedding/limits/gotcha catalogue. `lessons-and-evidence.md` covers the failure patterns that
> make these gotchas bite.

## Gotcha register (per component)

| Field | Meaning |
|---|---|
| Component | Product, API, model, prompt, agent, judge, tool, index, endpoint |
| Status | Proposed / Validated / Accepted-risk / Blocked / Retired |
| Limitation | The specific behavior or constraint |
| Trigger | Conditions that expose it |
| Impact | Accuracy / security / latency / cost / action safety |
| Detection | Test, scorer, alert, or operational signal |
| Mitigation | Design or runbook response |
| Owner | Responsible role |
| Evidence | Trace, eval run, test, incident, doc |
| Revalidation | Version/date requiring retest |

## Databricks Apps

- The App **service principal must be granted `CAN USE`/`CAN MANAGE` manually**, and **resources
  (SQL warehouse, Lakebase, model-serving endpoints, secrets, UC objects) must be explicitly
  added to the App** for anything to work — these are manual wiring steps, not automatic.
- Embedding an App does not make it public or bypass its `CAN USE` ACL; every viewer must be an
  authenticated Databricks user with permission. The host portal's login does not create a usable
  Databricks login inside the iframe.
- Third-party-cookie restrictions, IdP redirects, corporate browser policies, PrivateLink, VPN,
  proxy, DNS must all be tested; provide a full-page fallback link when embedded auth fails.
- FastAPI must independently authorize **every** read, writeback, approval, and live action —
  even inside an iframe. Never treat a frontend button state as an authorization control.
- Don't run heavy Spark, long training, or fragile background loops in App web workers; a browser
  request must not stay open while a long investigation/training job runs — start a durable Job/
  work item and return a status ID.

## Dashboard embedding (AI/BI)

- Admin must enable embedding and set the policy (allow-all / approved-domains / deny); parent
  domain must be approved. Basic embedding requires Databricks auth + third-party cookies.
- Draft dashboards aren't the supported embedding surface; viewers still need dashboard + data
  access; embedded dashboards render in **light mode only**; the iframe UI can't be restyled like
  a native component; hosts like SharePoint need their own iframe allowlisting; external embedding
  has limits (e.g. ~20 dashboard loads/sec) — lazy-load/stagger many frames.
- If you need coordinated filters, writebacks, agent context, action buttons, or custom drill,
  prefer native React + governed APIs over embedding several dashboard frames.

## Genie embedding

- Admin must approve the surface; author needs ≥ `CAN MANAGE`; end users need access to the Genie
  Agent AND the underlying data; unauthenticated users are prompted to sign in; clipboard needs
  iframe `allow="clipboard-write"`.
- Embedded frame is fine when its standard UI is acceptable; for custom tool-progress, MLflow
  trace correlation, Lakebase conversation state, typed action proposals, or approval gates, have
  FastAPI call supported Agent APIs while React renders the experience.

## Cross-frame / postMessage / CORS

- React can't reach inside a cross-origin iframe to modify DOM, read state, or sync controls;
  scraping a Databricks iframe is brittle and depends on undocumented UI.
- If `postMessage` is mutually supported: validate `event.origin`; target a specific origin (never
  `*`); validate every message against a versioned schema; never transmit tokens/credentials/
  secrets/unrestricted action commands; never accept a live-action instruction just because it
  arrived via `postMessage`.
- **CORS, iframe policy, and CSRF solve different problems; none substitutes for server-side
  authorization.** CORS config cannot override anti-framing headers.

## External content in an iframe

The child system (ERP/WMS/planning/portal) may block framing via CSP `frame-ancestors`,
`X-Frame-Options`, third-party-cookie restrictions, auth redirects, licensing, or browser
policy. It must *officially* support the embedding scenario.

## iframe security for consequential actions

For forecast overrides, inventory transfers, PO changes, ERP/WMS submissions: prefer an
unmistakable trusted approval screen; reauthorize and revalidate server-side; verify record
version immediately before execution; require step-up/dual approval when warranted; record actor,
proposed action, approval, origin, evidence, result; never expose live-action APIs to
unrestricted iframe messaging. iframes carry clickjacking / confused-deputy risk.

## Notebook displayHTML

Runs inside an iframe served from `databricksusercontent.com` — corporate networks must allow
that domain or output appears blank. Fine for exploration/demos; not a production foundation for
durable sessions, writebacks, agent conversations, approvals, auth-sensitive interactions,
persistent telemetry, or live actions.

## iframe selection rule

| Requirement | Preferred design |
|---|---|
| Standard published dashboard in a portal | Dashboard iframe |
| Standard Genie experience in a portal | Genie iframe |
| Entire App inside an internal portal | App iframe, after auth testing |
| Integrated agent + writeback + approval | Native React + FastAPI |
| Tight chart↔app-state sync | Native React visualization |
| Public anonymous app | Do not assume a Databricks App iframe |
| Third-party operational system | Only if the vendor officially supports framing |
| Temporary interactive content | `displayHTML`, dev only |

For every proposed iframe verify: official support, parent-domain policy, auth, permissions,
cookies, CSP, sandbox attributes, networking, messaging, clickjacking exposure, performance,
accessibility, fallback.

## Lakebase gotchas

- A Lakebase DB exposed through Unity Catalog is **read-only via UC queries** and requires a
  **serverless SQL warehouse** — writes go through Postgres/App transactions, analytical reads via
  governed UC access. Don't make it a second EDW; don't write directly to production source
  systems without the governed action flow.

## Federation gotchas

- Read-only; no Databricks result/disk caching; can load the remote system; possible performance/
  memory limits on large results; **pushdown depends on remote engine + query shape** — inspect
  the physical plan rather than assuming a filter/join executes remotely.

## SDP / pipeline gotchas

- Dataset definitions are evaluated multiple times and must principally return DataFrames — no
  arbitrary side effects/writes; a dataset normally has one defining operation; `pivot()`
  unsupported; materialized views don't support time-travel queries.

## Cross-cutting

- Pin and compatibility-test client / MLflow / Databricks Runtime / serving-env / agent-library
  versions. Prefer serverless where it fits; check region/edition limits. If a design bounds
  coverage (top-N, no-retry, sampling), say so — silent truncation reads as "covered everything."
