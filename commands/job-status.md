---
description: Quick read of the job search pipeline — what's aging, what's due for follow-up, what to apply to today
---

Give a quick, conversational status read on the Notion Job Search Pipeline (schema in
`context/notion-schema.md`) without running a full sweep or funnel review:

- Counts by Status (To Apply / Applied / Interviewing / Offer).
- The aging "To Apply" queue, ranked per the **Queue ranking convention** in
  `context/notion-schema.md` (same ranking `skills/daily-sweep` Part 3 produces).
- Any `Follow Up Date` that has arrived or passed.
- Anything that looks like it's been sitting too long (Applied 21+ days with no reply).

This is a read-only snapshot — don't change any Notion pages from this command. If the
candidate wants to act on what you find (apply to something, mark a role ghosted, run the
full sweep), hand off to the relevant skill (`apply-assist`, `daily-sweep`) rather than doing
it inline here.
