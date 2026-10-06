---
description: Manually run the daily job-board sweep (discovery, email reconciliation, throughput report)
---

This is a thin entry point to the `daily-sweep` skill in this plugin
(`skills/daily-sweep/SKILL.md`) — do not reimplement its logic here, invoke it and return its
report.

This is the same skill the `daily-job-sweep` scheduled task runs every weekday morning — use
this command when the candidate wants a fresh run outside that schedule (e.g. they just set up new
LinkedIn alerts, or it's been a while since the last automated run).
