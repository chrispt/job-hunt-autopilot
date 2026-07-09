---
description: Manually run the daily job-board sweep (discovery, email reconciliation, throughput report)
---

This is a thin entry point to the `daily-sweep` skill in this plugin
(`skills/daily-sweep/SKILL.md`) — do not reimplement its logic here, invoke it and return its
report.

This is the same skill a `daily-job-sweep` scheduled task can run every weekday morning — use
this command for a fresh run outside that schedule (e.g. new job-alert emails were just set
up, or it's been a while since the last automated run).
