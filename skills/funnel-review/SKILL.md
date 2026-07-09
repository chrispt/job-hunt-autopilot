---
name: funnel-review
description: Weekly review of the Notion Job Search Pipeline — funnel metrics, apps-out velocity, and a rejection-pattern analysis that turns each week's outcomes into concrete positioning/targeting adjustments
---

You are producing a weekly job-search funnel review from the Notion "Job Search Pipeline"
database (see `../../context/notion-schema.md` for IDs and field schema). This task exists
to close a gap `daily-sweep` doesn't: rejections get marked but nothing ever looks across
them for a pattern. The point of this review is to turn last week's outcomes into a specific
adjustment for next week, not just to report a scoreboard.

This skill is normally invoked by a `weekly-funnel-review` scheduled-task wrapper in
`~/.claude/scheduled-tasks/`.

## 1. Pull the data

Query all pages in the pipeline. For each, you need: Status, Priority, Track, Match %,
Salary Range, Date Applied, Follow Up Date, Interview Date, Rejected checkbox, Outreach Sent,
and created time.

## 2. Funnel metrics

Report, this week vs. the prior week where meaningful:
- **Counts by Status** (To Apply / Applied / Interviewing / Offer / Rejected / Withdrawn / Ghosted).
- **Apps-out this week** — count of pages where Date Applied falls in the last 7 days. This
  is the North Star number for this review: the whole point of `apply-assist` and
  `daily-sweep`'s throughput step is to keep this moving. Call out the trend (up/down/flat vs.
  recent weeks) plainly.
- **Queue age** — for "To Apply" pages, the distribution of days-since-added (e.g., "6 roles
  under a week old, 4 over two weeks old"). Old queue age is the throughput bottleneck made
  visible; don't bury it.
- **Response rate** — of roles Applied more than 7 days ago, what fraction moved to any of
  Interviewing/Offer/Rejected vs. still sitting at Applied with no reply.
- **Interview rate** — fraction of Applied roles that reached Interviewing or Offer.

## 3. Rejection-pattern analysis (the learning loop)

Pull every page with `Rejected = true`. Look for patterns across Track, Priority, seniority
language in the Role field, salary band, and location/hybrid-vs-remote — the same dimensions
the scoring guardrails already care about (see `../../context/candidate-profile.md`). Name
anything systematic you find, e.g.:
- "3 of the last 4 rejections were Staff/Principal-titled roles — the tenure-screen guard in
  `daily-sweep` may need to score these lower still, or they should be deprioritized."
- "Rejections are concentrated in one Track — worth being more conservative about those
  roles' Match % until there's a counter-example."

Don't force a pattern if the sample is too thin (say so if it is) — a single week of 2-3
rejections isn't a trend. When a real pattern emerges, propose a **concrete, specific**
change: an adjustment to `daily-sweep`'s scoring guidance, a query to drop or add, or a
company/domain to add to `../../data/exclusions.md`. Frame these as proposals to confirm —
don't edit `daily-sweep`'s SKILL.md yourself.

## 4. Hygiene flags

- **Applied roles missing outreach**: Status = Applied, Date Applied more than 3 days ago,
  Outreach Sent still blank. List them — these are candidates for a quick `/apply-assist`
  outreach-only follow-up.
- **Stuck roles**: anything sitting in the same Status for an unusually long time relative
  to its stage (e.g., Interviewing with no Interview Date set, or no update in 3+ weeks).
- Any new candidate for `../../data/exclusions.md` based on this week's evaluations.

## 5. Output

Write the review in plain, direct prose — like a short note you'd write to yourself, not a
formatted AI report. Skip heavy bold-header/bullet-cascade structure; a few short paragraphs
plus a couple of concrete numbers and one or two named recommendations beats a dashboard. End
with the single most useful thing to focus on next week — usually either "clear N aging To
Apply roles" or a specific pattern-driven adjustment.
