---
name: mke-worklog-practice
description: "Standing practice: after every accepted piece of work, append the decision trail to WORKLOG.md"
metadata:
  type: feedback
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

After every accepted piece of work, append an entry to `WORKLOG.md` (repo root) — an append-only work log &
decision journal. Entry = **date · the ask in the user's own words · decision & why · artifacts (paths/IDs) ·
evidence/reconcile result · corrections · follow-ups.**

**Why:** the user asked for this explicitly ("after every acceptable work, you need to log it so history of
the work is not lost — I can't find my very first question and the trails in this chat"). The chat transcript
is NOT a durable record: this session already lost its earliest turns to compaction. Build logs
(RUNG2/P1FLOW/P1_SLICE _BUILDLOG.md) capture *how a thing was built*; WORKLOG.md captures the *trail of intent
and decisions*; memory files hold durable cross-session facts. All three are needed.

**How to apply:** don't wait to be reminded — when a deliverable is accepted/reconciled, log it before moving
on. Keep build-mechanics in the matching BUILDLOG, intent/decisions in WORKLOG.md. Reconstruct from the
compaction summary + artifacts if history was lost.

**Backups (user asked explicitly):** after appending a WORKLOG.md entry, copy it to
`worklog_backups/WORKLOG_<YYYYMMDD_HHMMSS>.md` — timestamped, append-only, never edited — so the single root
file isn't a single point of failure. First backup taken 2026-08-31. See [[mke-lessons-learnt]],
[[mke-project-guardrails]].
