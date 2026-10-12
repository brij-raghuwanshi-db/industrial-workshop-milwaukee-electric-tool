---
name: databricks-agent-skills-install
description: Databricks agent skills are installed for Claude Code; two update channels and which version is authoritative
metadata: 
  node_type: memory
  type: reference
  originSessionId: ece56b9e-b854-41db-b23e-6affa632c669
---

Databricks **agent skills** are installed and enabled for Claude Code (the old "AI Dev Kit skills" are deprecated; content folded into these). Plugin: `databricks@claude-plugins-official`, enabled in `~/.claude/settings.json`. They auto-trigger by task and are driven by the `databricks` CLI.

**There are two independent distribution channels — always prefer the Claude Code plugin version (the one live in-session):**
- Claude Code plugin (marketplace): manage with `claude plugin update databricks@claude-plugins-official` and `claude plugin marketplace update`. This is the authoritative one for work done inside Claude Code (currently v0.2.12, 32 skills incl. databricks-genie-agents, doctor, setup).
- `databricks aitools` CLI (raw skill files for Codex/Cursor/etc.): manage with `databricks aitools update` / `list`. Publishes on its own slower cadence (was v0.2.10).

The two version numbers legitimately differ — neither command can pull the other channel forward. Not a bug; don't try to "reconcile" them. For anything in Claude Code, the plugin (higher) version is what matters.

To update everything: run BOTH `claude plugin update databricks@claude-plugins-official` and `databricks aitools update`.

Workspace this pairs with: [[mke-rsc-workspace-access]].
