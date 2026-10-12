---
name: prefer-latest-databricks-skills
description: Always use the latest/live Claude Code plugin version of the Databricks skills
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ece56b9e-b854-41db-b23e-6affa632c669
---

When Databricks skill/plugin versions differ across channels, always use the **latest** — specifically the Claude Code plugin version that is live in the session, not the older `databricks aitools` raw-file version.

**Why:** User explicitly said "remember to use the latest one." The two channels drift and the in-session plugin is the newer, authoritative one for Claude Code work.

**How to apply:** Default to the plugin skills already loaded in-session. If unsure whether something is current, `claude plugin update databricks@claude-plugins-official` (and `claude plugin marketplace update`) before relying on it. See [[databricks-agent-skills-install]].
