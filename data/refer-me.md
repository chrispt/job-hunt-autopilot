# refer.me — evaluated, kept manual (never automated)

Evaluated 2026-07-29 after the candidate's career coach recommended it alongside hiring.cafe. This
records why no skill in this plugin automates refer.me, so a future session doesn't
"helpfully" build a scraper or an auto-submit path against it. It sits alongside
`exclusions.md` (which records deliberate company passes) as the same kind of record for a
deliberate site-level decision.

## What it is

A referral marketplace: verified employees at target companies refer job seekers into their
employer's internal referral process, earning a bonus on a successful hire. Job seekers get
matched to a referrer, submit a request (against either an in-network posting or an
externally pasted job URL), and track it through matched → viewed → confirmed/denied.

## Why it stays manual

- **Terms of Service, Section 5, explicit:** prohibits "scrape or bulk-download platform
  data" and to "harass or spam Referrers." Both would be violated by any automated
  request-generation loop over the pipeline.
- **`robots.txt` disallows `/api/`.** There is no public API, no documented endpoint, no
  npm/PyPI package, no MCP server, and no third-party wrapper of any kind — confirmed by
  search, 2026-07-29.
- **Core functionality is account-gated.** Referral requests, the marketplace profile, and
  every AI tool require signup with a resume upload and email verification.
- **The automatable action is contacting real strangers.** Even if the technical block
  weren't there, mass-generating referral requests to people who don't know the candidate is the same
  failure mode the funnel review already diagnosed in volume-over-quality cold applying — and
  here it would also burn goodwill with the referrers themselves.

This is a stricter case than LinkedIn's exclusion (LinkedIn's User Agreement bans scraping;
refer.me's ToS bans scraping *and* names spamming referrers as a separate violation), so it's
held to at least the same bar.

## What the plugin does instead

`skills/referral-match` step 4 surfaces a prioritized, budget-capped shortlist of "To Apply"
roles with no warm-network match — see that file for the ranking and cap logic, and
`context/config.md` for the account-tier/request-budget convention it reads. The candidate does the
actual search, request submission, and any resulting conversation themselves, in their own
browser. No skill drafts a message to a refer.me referrer; that's the one boundary this
document exists to hold.

## Revisit condition

If refer.me ever ships a documented API with its own terms permitting programmatic use, or
partners with a job board the candidate's other tools already touch, re-evaluate. Absent that, this
decision doesn't need re-litigating each time the topic comes up.
