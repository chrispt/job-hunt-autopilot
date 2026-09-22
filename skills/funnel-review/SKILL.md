---
name: funnel-review
description: Weekly review of the Notion Job Search Pipeline — funnel metrics, apps-out velocity, and a rejection-pattern analysis that turns each week's outcomes into concrete positioning/targeting adjustments; re-screens the standing queue whenever a screening rule changes, since screens otherwise run only at intake; runs the hybrid Aged Out pass every week (bulk date/match write plus a small batched-and-confirmed JD check on old-but-well-matched rows); monthly market-calibration check against hiring.cafe's live listings
---

You are producing the candidate's weekly job-search funnel review from their Notion
"Job Search Pipeline" database (see `../../context/notion-schema.md` for IDs and field
schema). This task exists to close a gap `daily-sweep` doesn't: rejections get marked but
nothing ever looks across them for a pattern. Point of this review is to turn last week's
outcomes into a specific adjustment for next week, not just to report a scoreboard.

This skill is normally invoked by the `weekly-funnel-review` scheduled-task wrapper in
`~/.claude/scheduled-tasks/`.

## 1. Pull the data

Query all pages in the pipeline. For each, you need: Status, Priority, Track, Match %,
Salary Range, Date Applied, Follow Up Date, Interview Date, Rejected checkbox, Outreach Sent,
and created time.

Budget for this: the pipeline is around two thousand rows and `notion-query-data-sources`
SQL mode is quota-capped, unpredictably (1 call in one session, ~12 in another, and it does
not recover once exhausted). Spend SQL calls on aggregates only (`GROUP BY Status`, the
rejection set, the apps-out window), and read rows through the saved views in
`../../context/notion-schema.md`, which are quota-exempt. Since 2026-09-08 every row carries
a `Created` property (created time), returned in view mode, so row age is `Created`; the
page-ID age derivation is retired. Pipe spilled view results through
`scripts/notion_rows.py` (path conventions in `../../context/config.md`) and read only its
output.

**Refresh the local pipeline snapshot** (added 2026-09-08). While the rows are in hand,
write `data/pipeline-snapshot.json` (a list of `{Company, Role, Status, Job URL, url}` for
every row) so `daily-sweep` can dedup locally against it plus the "⚙ Added last 7 days"
view, with zero quota. Procedure (about 25 tool calls for ~2,000 rows, quota-free): set the "⚙ Snapshot slice"
view's filter to a 10-14 day `Created` window with `notion-update-view`, page it at 100 rows
(each page spills to a file), run `notion_rows.py <file> --json --fields Company,Role,Status,Job URL,url,Created > pN.json`
per page, then `scripts/snapshot_build.py p*.json` merges them (dedup by url, keeps older
rows, prints the Created range covered). Only slices newer than the previous snapshot's
`created_max` need re-paging. Copy the result into the installed plugin's `data/` as well,
because that is the copy `discover.py` reads at runtime. If the full table cannot be paged this week, leave the
previous snapshot in place and say so; a stale snapshot plus the 7-day view still covers
everything except rows older than the snapshot that a later run somehow lost.

## 2. Funnel metrics

Report, this week vs. the prior week where meaningful:
- **Counts by Status** (To Apply / Applied / Interviewing / Offer / Rejected / Withdrawn / Ghosted / Aged Out).
- **Packets built vs submitted** (added 2026-09-08): rows with a Packet Ready date this week,
  how many of those reached Applied, and the oldest unsubmitted packet. This is the new
  leading indicator: `apply-prep` builds packets on Mon/Wed/Fri, and a packet that sits is
  the throughput problem made visible one step earlier than queue age.
- **Coverage** (added 2026-09-08): run `scripts/audit.py --transcript <file> --until-text "Daily Job Sweep"`
  over this week's sweep transcripts (find them with `list_sessions` titles or the
  `~/.claude/projects/<cwd slug>/` directory by date) and report how many runs were OK vs
  INCOMPLETE and why. An INCOMPLETE week is a tooling problem, not a market signal.
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
the scoring guardrails already care about (8+-yr-PM-tenure screens, security-adjacent gaps,
non-FL hybrid/on-site — see `../../context/candidate-profile.md`). Name anything systematic
you find, e.g.:
- "3 of the last 4 rejections were Staff/Principal-titled roles — the 8+-yr-PM screen guard
  in `daily-sweep` may need to score these lower still, or they should be deprioritized."
- "Rejections are concentrated in security-adjacent Tracks — worth being more conservative
  about those roles' Match % until there's a counter-example."

Don't force a pattern if the sample is too thin (say so if it is) — a single week of 2-3
rejections isn't a trend. When a real pattern emerges, propose a **concrete, specific**
change: an adjustment to `daily-sweep`'s scoring guidance, a query to drop or add, or a
company/domain to add to `../../data/exclusions.md`. Frame these as proposals for the candidate to
confirm — don't edit `daily-sweep`'s SKILL.md yourself.

## 4. Hygiene flags

- **Applied roles missing outreach**: Status = Applied, Date Applied more than 3 days ago,
  Outreach Sent still blank. List them — these are candidates for a quick `/apply-assist`
  outreach-only follow-up.
- **Stuck roles**: anything sitting in the same Status for an unusually long time relative
  to its stage (e.g., Interviewing with no Interview Date set, or no update in 3+ weeks).
- Any new candidate for `../../data/exclusions.md` based on this week's evaluations.

## 5. Standing-queue re-screen (added 2026-08-04)

Every screening rule this plugin has ever added runs **only at intake**, inside `daily-sweep`
Part 1. Nothing re-checks roles that were already sitting in the queue when the rule landed.
So each new rule silently applies to future discoveries and leaves the existing backlog
untouched, and the backlog is where most of the queue lives. This step closes that gap.

This is not hypothetical. The seniority screen was added 2026-07-27. On 2026-08-04, 142 rows
carrying outright-discard titles were still sitting in a 935-row "To Apply" queue, about 15%
of it, more than a week after the rule existed. Two of them (Zoom "Head of Customer Success
Transformation", GoodLeap "Director of Customer Success") were only caught because a
CS-tenure re-score happened to walk past them.

**When to run:** whenever step 3 proposes a new or changed screening rule, whenever the candidate
adopted one since the last review, and as a backstop in the first week of the month alongside
step 6. Skip it silently otherwise.

**Scope it to the actionable band.** Only re-screen rows at or above the 55% grade floor in
`../../context/candidate-profile.md`. Below-floor rows are inert: they never reach an
`apply-assist` run, so withdrawing them is churn that buys nothing. On 2026-08-04, 98 of the
142 matches were below floor and were deliberately left alone; the real work was 44 rows.

**Use `scripts/screen.py` for the match, never an ad-hoc regex** (added 2026-09-08): export
the actionable band's rows as `{title, company, source, salary}` JSON and run
`screen.py rows.json`; its `discard` bucket is the candidate list and its `flag` bucket is
the false-positive review list. Then hand-check every discard against what the role actually
is. Two false-positive classes are confirmed:
- **Department names that contain a rank word.** Cisco "Program Manager, Americas Chief of
  Staff Office" matched the Chief rule and was the highest-scoring row in the entire matched
  set at 74%. It is a Program Manager req; "Chief of Staff Office" is an org unit.
- **Rank words used as pay grades rather than scope.** "VP" at banks (JPMorganChase) is
  routinely an individual-contributor grade, and defense contractors post titles like Peraton's
  "Product Manager (Director)" where the leading noun is the actual job.

**Honour the documented overrides.** The seniority screen explicitly allows a warm referral or
other differentiator to override it, so a row is exempt when either holds:
- a **named referral contact** is recorded in Notes (three rows qualified on 2026-08-04:
  Capital One, Zscaler, Mastercard), or
- the **JD has already been read and cleared the gate**. Patriot Growth "Director, AI
  Enablement" carried an `apply-assist` note confirming the stated bar was "8+ years in
  technology", not dedicated PM/Director tenure, and ended "no hard structural gate found".
  A blind sweep would have deleted a role the pipeline had already validated and was building
  documents for.

**Propose, never auto-apply.** Same rule as step 3, and Notion has no delete tool, so removal
is always Status to "Withdrawn" plus a dated Notes annotation per `../../context/notion-schema.md`.
Preserve the existing scoring rationale and append; do not overwrite it. State in the
annotation which rule fired and that the row was withdrawn on title rather than on verified
posting status.

**Report what the re-screen caught and what it spared**, including the false positives and
exemptions by name. A bare count reads as routine cleanup; the exceptions are the part that
tells the candidate whether the rule is calibrated or is quietly eating good roles. If a spared row
was a strong functional fit, say so plainly: Ignite Visibility "Senior Director, Product & AI
Enablement" was described in its own notes as a near-mirror of the candidate's current role and was
still withdrawn on title, which is the clearest evidence available that the Director+ screen
has a real cost. Revisit the whole screen if a Director-and-above application ever converts.

**Query note:** the pipeline is well past the point where SQL mode can carry this (see the
quota and pagination traps in `../../context/notion-schema.md`). Prefer view mode; row age is
the `Created` property, which view mode returns.

### 5a. Age-out pass (added 2026-09-10)

This is the same re-screen pattern as the rest of step 5 — collect candidates, batch, get
the candidate's confirmation before any Withdrawn write — applied to date/match staleness instead of
a title-based screening rule. It productizes the one-off hybrid pass documented in
`../../context/notion-schema.md`'s age-out convention (`runs/2026-09-10/ageout_hybrid_result.json`
is the run it replaces). **Run every week** — unlike the title re-screen above, this doesn't
need a triggering rule change; the queue ages every day.

1. Refresh "⚙ Age-out candidates" (quota-free, `notion-update-view`) so its two absolute
   dates match today: `Created` ≤ today − `age_out.aged_out_days` (60) OR (`Created` ≤ today
   − `age_out.borderline_days` (45) AND `Match %` < `age_out.borderline_match_floor` (70)) —
   values from `../../data/screens.json`. Keep every other clause as-is.
2. Page the view, pipe each page through `scripts/notion_rows.py --json`, then run
   `scripts/age_out.py <export>.json --json`. It splits the (already policy-filtered) rows
   by Match %: **< 70% → `aged_out_direct`**, safe to write `Status = Aged Out` immediately
   with no Notes annotation (self-describing, per the existing convention) — do this now, no
   review needed. **≥ 70% → `borderline`**: every row here got into the view via the 60+-day
   branch (the 45-day branch requires <70 match), so these are old-but-well-matched roles
   that deserve a look before a date rule kills them.
3. For each `borderline` row, run the JD read ladder (`../../context/config.md`) exactly as
   `apply-prep`/`apply-assist` do per-role at packaging time — this is the same read, just
   triggered by staleness instead of by "about to apply." Record which rung answered and the
   verdict: a positive closed signal (404/410, "no longer accepting," an ATS board that no
   longer lists the role) is `closed`; a live posting is `open`; nothing rendering on any
   rung is `inconclusive` — never treat an empty render as closed (the incident this rule
   exists to prevent is logged in `../../context/incident-log.md`, 2026-08-11).
4. Feed those verdicts back through `scripts/age_out.py --verdicts <verdicts>.json --json`.
   `closed` → **batch and confirm with the candidate** before writing anything, same as the rest of
   step 5: `Status = Withdrawn` + a dated Notes annotation citing the evidence, appended to
   existing Notes, never overwritten. `open` → leave untouched, but report it so the candidate sees
   it was checked. `inconclusive` → write `Status = Aged Out` directly (self-describing, no
   Notes), same as the direct bucket.
5. Report the split and, for the borderline slice, the reasoning per row — same principle as
   the rest of step 5: a bare count reads as routine cleanup, and the borderline rows are
   exactly the ones a blind date-based sweep would have gotten wrong.

**Stays cheap on a weekly cadence.** This is deliberately not a full-queue liveness sweep —
see the reasoning in `../../context/config.md`'s JD read ladder note and the decision logged
2026-09-10 against scoping one. The borderline slice needing a live check is normally small:
2 rows out of 202 eligible in the 2026-09-10 run. If that ratio changes dramatically (a lot
more high-match rows going stale at once), say so rather than quietly absorbing a bigger
live-check bill into this step.

## 6. Market calibration (monthly, added 2026-07-29)

This runs **only in the first week of the calendar month** (today's day-of-month ≤ 7) —
skip it silently on the other three weekly runs, no need to mention the skip in the output.
It answers a question the pipeline can't answer from its own data: what share of the candidate's
actual target market screens above their real PM tenure, and what share pays above their floor.
If most of the market demands 5+ years, a stretch of rejections is a targeting problem, not a
resume problem, and that's worth knowing before proposing another scoring tweak in step 3.

Fetch a small fixed set of `https://hiringcafe.com/jobs/<slug>` pages — the robots-Allowed
path only, never `?searchState=` or `?page=` (see `../../context/config.md` for the fetch
constraints): `remote-ai-product-manager`, `remote-technical-product-manager`,
`remote-product-manager`, `ai-product-manager`, `product-manager`. Across the roughly 20
listings each page renders, report the **distribution**, not individual roles:
- Share stating a PM/product-experience minimum at or above the 8-year gate in
  `../../context/candidate-profile.md`, vs. below it, vs. not stated.
- Share stating a base at or above the salary floor, vs. below, vs. not stated.

This is read-only market context, not a per-role lookup — it doesn't touch Notion or any
individual pipeline page. If a fetch is blocked (403, challenge, empty shell), skip that slug,
note it, and continue with the rest rather than treating one miss as a reason to drop the
whole section. Per `funnel-review`'s existing rule, any resulting adjustment is a **proposal**
for the candidate to confirm, never a self-edit to `daily-sweep`.

## 7. Output

Write the review in plain, direct prose — like a short note the candidate would write to themselves,
not a formatted AI report. Skip heavy bold-header/bullet-cascade structure; a few short
paragraphs plus a couple of concrete numbers and one or two named recommendations beats a
dashboard. End with the single most useful thing to focus on next week — usually either
"clear N aging To Apply roles" or a specific pattern-driven adjustment.
