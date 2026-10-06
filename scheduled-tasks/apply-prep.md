Scheduled task prompt for `apply-prep` (Mon/Wed/Fri 09:00, cron `0 9 * * 1,3,5`). Create it
with `create_scheduled_task`; this file is the prompt body.

---

This scheduled task is a thin wrapper. The logic lives in the `job-search-agent` plugin,
`skills/apply-prep/SKILL.md` (the installed copy under the plugin cache is what executes).

## Step 0: single-instance lock (BEFORE any other tool call)

```
export PYTHONIOENCODING=utf-8
<python> "${CLAUDE_PLUGIN_ROOT}/scripts/lock.py" acquire apply-prep --stale-hours 3
```

- Prints `held: ...` → stop now. Write nothing, notify nothing, return that single line.
- Prints `acquired: ...` → continue, and report the line in the output.

## The run

Run the `job-search-agent` plugin's `apply-prep` skill now with its default of 3 packets, and
return its report as this task's output: the "paths tried" table, the environment lines
(documents folder, Chrome extension, Word), packets built, packets skipped with reasons.
Release the lock at the end (`lock.py release apply-prep`).

The user is not present. Do not ask questions. Where the skill says a decision needs the
user, skip that role and list it as "needs your call". Never click Submit, never send
outreach, never enter attestation, self-ID, salary or EEO fields, never create accounts or
log in.
