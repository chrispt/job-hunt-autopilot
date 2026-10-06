---
description: Quick read of the job search pipeline, packets ready, what's aging, what's due for follow-up, what to apply to today
---

Give the candidate a quick, conversational status read on their Notion Job Search Pipeline (schema and
saved views in `context/notion-schema.md`) without running a full sweep or funnel review.
Use the saved views (quota-exempt) and `scripts/notion_rows.py` to compact the results:

- **Packets ready** ("⚙ Packets ready" view): roles with a tailored packet waiting for them
  to submit, with days since the packet was built.
- **Outreach owed** ("⚙ Outreach owed" view): applications with no outreach recorded.
- **Top 3 to apply** from the "⚙ Ranked queue" view (already floor-gated, Priority then
  oldest), then the ≥ 70% tier.
- **Follow-ups due** from "⚙ Applied open": Follow Up Date on or before today; Applied 21+
  days with no reply (propose Ghosted, low confidence).
- Counts by Status (To Apply / Applied / Interviewing / Offer / Rejected / Withdrawn /
  Ghosted / Aged Out) if a single SQL aggregate is affordable; otherwise skip the counts
  rather than paging views for them.

Read-only: change nothing from this command. To act on anything, hand off to
`apply-assist` (or `apply-prep`), `daily-sweep`, or `referral-match`.
