Scheduled task prompt for `weekly-funnel-review` (Fridays 16:00, cron `0 16 * * 5`). Create it
with `create_scheduled_task`; this file is the prompt body.

---

This scheduled task is a thin wrapper. The logic lives in the `job-search-agent` plugin,
`skills/funnel-review/SKILL.md` (the installed copy under the plugin cache is what executes).

Run the `job-search-agent` plugin's `funnel-review` skill now and return its output as this
task's output, including the weekly coverage audit and the pipeline snapshot refresh. If the
plugin isn't loaded in this session, say so plainly rather than reconstructing the logic
from memory.
