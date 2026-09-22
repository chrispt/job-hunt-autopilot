Scheduled task prompt for `daily-job-sweep` (weekdays 08:00, cron `0 8 * * 1-5`). Create it with
`create_scheduled_task`; this file is the prompt body.

---

This scheduled task is a thin wrapper. The logic lives in the `job-search-agent` plugin,
`skills/daily-sweep/SKILL.md` (the installed copy under the plugin cache is what executes).

## Step 0: single-instance lock (BEFORE any other tool call)

```
export PYTHONIOENCODING=utf-8
<python> "${CLAUDE_PLUGIN_ROOT}/scripts/lock.py" acquire daily-sweep --stale-hours 3
```

(Python path from the plugin's `context/config.md`; if `CLAUDE_PLUGIN_ROOT` is empty, use the
installed plugin path from that file.)

- Prints `held: ...` → stop now. Write nothing, notify nothing, return that single line.
- Prints `acquired: ...` → continue, and report the line in the output.

A weekend run is not by itself a problem: missed weekday runs execute on next app launch. The
lock only prevents two sweeps at once.

## The run

Run the `job-search-agent` plugin's `daily-sweep` skill now and return its report as this
task's output. Release the lock at the end (`lock.py release daily-sweep`). If the plugin
isn't loaded in this session, say so plainly rather than reconstructing the logic from memory.
