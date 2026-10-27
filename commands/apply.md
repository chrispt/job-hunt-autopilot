---
description: Take one or more "To Apply" roles through to a submitted application
argument-hint: [count | Company | url ...]
---

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

This is a thin entry point to the `apply-assist` skill in this plugin
(`skills/apply-assist/SKILL.md`) — do not reimplement its logic here, invoke it.

- No arguments → run `apply-assist` for the single highest Priority/Match % "To Apply" role.
- A number (e.g. `3`) → run it for that many roles, same ordering.
- A company name → run it for that named role already in the pipeline.
- One or more job posting URLs → link-list batch mode: Phase A for every link in parallel,
  then Phase B one application at a time (see the skill's "Link-list batch mode" section).
  Roles at a company where the candidate knows someone go on a referral hold (skill step 5a): the
  referral ask goes out first and Phase B waits for the link or 3 business days.

If `$ARGUMENTS` doesn't clearly parse as one of these, ask which mode the candidate means before
proceeding.
