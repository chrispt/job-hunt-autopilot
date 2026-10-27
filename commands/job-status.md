---
description: Quick read of the job search pipeline, packets ready, what's aging, what's due for follow-up, what to apply to today
---

Give the candidate a quick, conversational status read on their Notion Job Search Pipeline (schema and
saved views in `context/notion-schema.md`) without running a full sweep or funnel review.
Use the saved views (quota-exempt) and `scripts/notion_rows.py` to compact the results:

- **Packets ready** ("⚙ Packets ready" view): roles with a tailored packet waiting for them
  to submit, with days since the packet was built.
- **Referral asks and holds** (added 2026-10-26): rows whose Notes carry an open `Referral
  hold:` line (no later `Referral received` / `Referral not received` line). Show the
  contact and the apply-by date; flag any due today or past due, since those are ready to
  apply now. Find them in the "⚙ Packets ready" and "⚙ Ranked queue" results already pulled
  above (packets are built during the hold), not with a new query.
- **Warm share:** of the applications in "⚙ Applied open" with a Date Applied in the last 7
  days, how many were warm (Source = Referral, or a `Known contact:` / `Referral hold:` Notes
  line). Target is at least half; say plainly when the week is below it.
- **Outreach owed** ("⚙ Outreach owed" view): applications with no outreach recorded,
  leaving out rows whose Notes carry `Outreach skipped`.
- **Top 3 to apply** from the "⚙ Ranked queue" view (already floor-gated, Priority then
  oldest), then the ≥ 70% tier.
- **Follow-ups due** from "⚙ Applied open": Follow Up Date on or before today; Applied 21+
  days with no reply (propose Ghosted, low confidence).
- Counts by Status (To Apply / Applied / Interviewing / Offer / Rejected / Withdrawn /
  Ghosted / Aged Out) if a single SQL aggregate is affordable; otherwise skip the counts
  rather than paging views for them.

Read-only: change nothing from this command. To act on anything, hand off to
`apply-assist` (or `apply-prep`), `daily-sweep`, or `referral-match`.
