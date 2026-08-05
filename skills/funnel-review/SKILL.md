---
name: funnel-review
description: Weekly review of the Notion Job Search Pipeline — funnel metrics, apps-out velocity, and a rejection-pattern analysis that turns each week's outcomes into concrete positioning/targeting adjustments; optionally re-screens the standing queue whenever a screening rule changes, and runs a periodic market-calibration check against live listings
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

## 5. Standing-queue re-screen (if `daily-sweep` uses an intake-time screen)

Any screening rule `daily-sweep` adds runs **only at intake**. Nothing re-checks roles that
were already sitting in the queue when the rule landed, so a new rule silently applies to
future discoveries and leaves the existing backlog untouched — and the backlog is usually
where most of the queue lives.

**When to run:** whenever step 3 proposes a new or changed screening rule, whenever one was
adopted since the last review, and as a periodic backstop (e.g. monthly, alongside step 6).
Skip it silently otherwise.

**Scope it to the actionable band** — only re-screen rows at or above your resume-build floor
in `../../context/candidate-profile.md`. Below-floor rows are inert; they never reach an
`apply-assist` run, so withdrawing them is churn that buys nothing.

**Never sweep on a title match alone.** These screens are string heuristics and they misfire
in ways that are invisible in aggregate — hand-check every match against what the role
actually is (see the false-positive classes noted in `daily-sweep`'s seniority-screen
section). **Honour the documented overrides** the screen allows (a named referral contact, or
a JD already read and confirmed not to gate on the rank) — a blind re-sweep would undo a role
the pipeline already validated.

**Propose, never auto-apply.** Same rule as step 3: removal is Status → "Withdrawn" plus a
dated Notes annotation, never a delete. Preserve the existing scoring rationale and append;
don't overwrite it.

**Report what the re-screen caught and what it spared**, including the false positives and
exemptions by name. A bare count reads as routine cleanup; the exceptions are what tells you
whether the rule is calibrated or is quietly eating good roles.

## 6. Market calibration (optional, e.g. monthly)

This answers a question the pipeline can't answer from its own data: what share of your
actual target market screens above your real experience level, and what share pays above your
floor. If most of the market demands more years than you have, a stretch of rejections is a
targeting problem, not a resume problem — worth knowing before proposing another scoring
tweak in step 3.

If you've set up a market-corroboration fallback source (`../../context/config.md`), fetch a
small fixed set of listing pages for your pivot-target queries and report the **distribution**
across them, not individual roles: share stating an experience minimum at or above your gate
in `candidate-profile.md` vs. below it vs. not stated, and share stating a base at or above
your salary floor vs. below vs. not stated. This is read-only market context — it doesn't
touch Notion or any individual pipeline page. If a fetch is blocked, skip that page, note it,
and continue with the rest. Any resulting adjustment is a **proposal**, never a self-edit to
`daily-sweep`.

## 7. Output

Write the review in plain, direct prose — like a short note you'd write to yourself, not a
formatted AI report. Skip heavy bold-header/bullet-cascade structure; a few short paragraphs
plus a couple of concrete numbers and one or two named recommendations beats a dashboard. End
with the single most useful thing to focus on next week — usually either "clear N aging To
Apply roles" or a specific pattern-driven adjustment.
