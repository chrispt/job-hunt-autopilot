# Cold-referral tools — evaluated, kept manual (never automated)

<!-- TEMPLATE — this file is a worked example (based on a real referral-marketplace site, one
of several that exist) of why a plugin might deliberately choose NOT to automate a particular
third-party tool, so a future session doesn't "helpfully" build a scraper or an auto-submit
path against it. It sits alongside `exclusions.md` (which records deliberate company passes)
as the same kind of record, but for a site-level decision. Delete this file if you don't use
`skills/referral-match`'s optional cold-referral shortlist, or replace the specifics with
whatever tool you actually use. -->

If you're using `skills/referral-match`'s optional cold-referral shortlist (step 4), it likely
points at some kind of referral marketplace — a service where verified employees at target
companies refer job seekers into their employer's internal referral process, earning a bonus
on a successful hire. Before wiring any automation against a service like this, check:

## Why this kind of site typically stays manual

- **Terms of Service often explicitly prohibit** bulk-downloading platform data and
  "harassing or spamming" the referrers who use the service. Both would be violated by any
  automated request-generation loop over your pipeline.
- **`robots.txt` commonly disallows API-shaped paths**, and there's often no public API, no
  documented endpoint, and no maintained third-party wrapper — check before assuming one
  exists.
- **Core functionality is usually account-gated** (signup, resume upload, email
  verification), which itself argues against automating around it.
- **The automatable action is contacting real strangers.** Even setting the technical
  restrictions aside, mass-generating referral requests to people who don't know you is the
  same failure mode as volume-over-quality cold applying — and here it also burns goodwill
  with the referrers themselves.

## What the plugin does instead

`skills/referral-match` step 4 surfaces a prioritized, budget-capped shortlist of "To Apply"
roles with no warm-network match — see that skill for the ranking and cap logic, and
`context/config.md` for the account-tier/request-budget convention it reads. You do the actual
search, request submission, and any resulting conversation yourself, in your own browser. No
skill drafts a message to a referrer on a site like this; that's the one boundary this
document exists to hold.

## Revisit condition

If the specific service you use ever ships a documented API with its own terms permitting
programmatic use, re-evaluate. Absent that, treat this as a standing decision rather than
something to re-litigate every time the topic comes up.
