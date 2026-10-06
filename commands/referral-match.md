---
description: Match the candidate's LinkedIn network against open pipeline roles and draft referral asks
argument-hint: [Company | --min N]
---

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

This is a thin entry point to the `referral-match` skill in this plugin
(`skills/referral-match/SKILL.md`) — do not reimplement its logic here, invoke it.

- No arguments → run `referral-match` for all "To Apply" roles at or above the default 55%
  match floor.
- A company name → run it for that one named role already in the pipeline.
- `--min <N>` → override the match-percentage floor for this run.

If `$ARGUMENTS` doesn't clearly parse as one of these, ask which mode the candidate means before
proceeding.
