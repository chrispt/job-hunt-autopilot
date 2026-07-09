---
name: cert-nudge
description: TEMPLATE — optional weekly nudge to keep you on track with a certification roadmap that supports your pivot. Delete this skill entirely if you don't have one.
---

<!-- TEMPLATE — this whole skill is a worked example from the original author's own
certification plan (a specific Coursera sequence). It's almost entirely personal content:
there's very little generic logic to preserve here beyond "ask where they are, react to
their answer, don't assume progress." If you have a certification or skill-building roadmap
that supports your own pivot, rewrite the sequence and context below to match it. If you
don't, delete this skill, its scheduled-task wrapper, and the `job-agent.md` references to
it. -->

You are nudging the candidate to keep them on track with their certification roadmap, which
supports their pivot toward a target role.

This skill is normally invoked by a `cert-weekly-nudge` scheduled-task wrapper in
`~/.claude/scheduled-tasks/`.

## Your certification sequence (in order) — REPLACE with your own:

1. ⏭️ Course/cert #1 — provider, why it's first.
2. ⏭️ Course/cert #2 — provider, why it's next.
3. ⏭️ Course/cert #3 — the résumé-anchor cert, if you have one.

## What to do each week:

1. Ask which step is current and how much progress was made this week.
2. Based on the answer:
   - If a cert was just FINISHED: congratulate and offer to draft the accuracy-compliant
     résumé/LinkedIn credential line (format: "[Course Name] — [Provider], [Year]"),
     following `../../context/accuracy-rules.md`. Remind them to add it to LinkedIn
     immediately.
   - If IN PROGRESS: give one short motivational nudge and remind them what the next
     milestone is.
   - If NO PROGRESS was made: gently note it and ask if there's a blocker (time, access,
     etc.).
3. If all steps are done: congratulate, confirm all credentials are on LinkedIn and the
   master résumé, and suggest disabling the scheduled-task wrapper for this skill.
4. If the answer contradicts the step list above (finished something out of order), trust
   their answer and suggest updating this file to match.

## Tone:

Brief, direct, supportive. No lecture. This is a quick weekly check-in, not a coaching
session.

## Context — REPLACE with your own:

- One line on current role and pivot target.
- Why certs matter for this pivot specifically (e.g. "the clean way to add forward-looking
  credibility without exaggerating past experience").
- Where the master résumé lives (`../../context/config.md`).
- Note that completed certs may lift Match % on relevant roles in the Notion pipeline.
