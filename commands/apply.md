---
description: Take one or more "To Apply" roles through to a submitted application
argument-hint: [count | Company]
---

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

This is a thin entry point to the `apply-assist` skill in this plugin
(`skills/apply-assist/SKILL.md`) — do not reimplement its logic here, invoke it.

- No arguments → run `apply-assist` for the single highest Priority/Match % "To Apply" role.
- A number (e.g. `3`) → run it for that many roles, same ordering.
- A company name → run it for that named role already in the pipeline.

If `$ARGUMENTS` doesn't clearly parse as one of these, ask which mode the candidate means before
proceeding.
