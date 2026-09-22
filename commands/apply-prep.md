---
description: Build ready-to-submit application packets for the top queue roles (unattended Phase A)
argument-hint: [count | Company]
---

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

This is a thin entry point to the `apply-prep` skill in this plugin
(`skills/apply-prep/SKILL.md`), the same skill the Mon/Wed/Fri `apply-prep` scheduled task
runs. Do not reimplement its logic here; invoke it.

- No arguments → 3 packets from the top of the ranked queue (standouts first).
- A number → that many packets.
- A company name → a packet for that named role.

If `$ARGUMENTS` doesn't clearly parse as one of these, ask which mode the candidate means.
