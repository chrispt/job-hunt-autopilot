---
name: referral-match
description: TEMPLATE (optional skill) — match your professional network against open "To Apply" roles in the Notion Job Search Pipeline, draft warm referral-request messages to contacts at matched companies, and optionally surface a budget-capped cold-referral shortlist for roles with no warm contact.
---

<!-- TEMPLATE — this skill is entirely optional. It closes a gap `apply-assist` already names
but can't act on: its gate checks treat a warm referral as a differentiator that can lift a
borderline role over the resume-build floor, but nothing else in the plugin knows whether you
actually know someone at a given company. If you don't have an exportable network roster (or
don't want to automate this), delete this skill, its command, `data/connections-README.md`,
`data/refer-me.md`, and the references to it in `agents/job-agent.md`, `CLAUDE.md`, and
`skills/daily-sweep/SKILL.md` step 1a. -->

You are running Referral Match, part of the `job-search-agent` plugin. This skill joins your
exported network roster against the Notion pipeline and drafts the ask, so a warm referral
becomes something detected, not something you have to remember role by role.

Every generated message must follow `../../context/accuracy-rules.md` exactly, including the
"Referral / warm-outreach voice" section — draft only, in your own voice. Candidate facts and
scoring guardrails are in `../../context/candidate-profile.md`; the roster-file path, Notion
bindings, and any cold-referral-tool account tier are in `../../context/config.md`; pipeline
IDs and field schema are in `../../context/notion-schema.md`.

**Invocation:** `/referral-match` (all matched "To Apply" roles at or above your resume-build
floor), `/referral-match <Company>` (one named role), `/referral-match --min <N>` (raise or
lower the match threshold for this run). Ask which mode if ambiguous.

## 1. Read the roster

Read the roster-file path from `../../context/config.md`. Read the file.

- **Missing or unreadable:** stop and tell the candidate how to get it (see
  `../../data/connections-README.md` for one worked example — a LinkedIn "Get a copy of your
  data" export). Don't guess at matches without it.
- **Present but stale** (file modified more than ~90 days ago, or whatever staleness window
  you set): warn that it may be out of date (people change jobs), then proceed — a stale
  roster is still better than none.
- **Format:** a network-export CSV often has a short notes preamble before the real header
  row — don't assume row 1 is the header; parse starting from the row that actually contains
  your expected column names.

## 2. Pull the pipeline

Query Notion for `Status = "To Apply"` (IDs and query quirks in
`../../context/notion-schema.md`), ranked Match % descending. Default threshold is the same
resume-build floor `apply-assist` uses; `--min` overrides it for this run. Skip any page
whose title already starts with `❌` (Rejected) — never match against those.

## 3. Join on Company

For each candidate role, normalize its Company title and compare against each contact's
Company field, using the **same normalization the exclusion-list and dedup steps already
use** (lowercase, trim, collapse whitespace, ignore legal suffixes like Inc./LLC/Corp).

- **Exact or suffix-only match** → confirmed match.
- **Fuzzy but not exact** (e.g. "Acme" vs "Acme Robotics", a parent company vs. a well-known
  subsidiary) → flag as a **review candidate**, don't auto-assert it. A self-reported company
  field can be stale or imprecise; a wrong assertion here (claiming a connection that isn't
  real, or missing one that is) is worse than asking.
- A company can have multiple contacts; a contact's company can have multiple open roles.
  Surface every combination — don't collapse to one match per company.

## 4. No warm match — optional cold-referral shortlist

For every candidate role from step 2 that produced **no** match in step 3 (confirmed or
review-candidate), you might still be able to get a referral cold, through a third-party
referral marketplace — if you use one, see `../../data/refer-me.md` for a worked example of
why that kind of site should stay manual-only and never automated.

- Rank the no-match roles the same way the aging-queue convention in
  `../../context/notion-schema.md` does: Match % descending, newer-first tiebreak.
- If the tool you use has a request cap (a free tier limited to N requests per period is
  common for this kind of service), cap the list at your remaining budget — the cap is the
  point; spending a scarce request on the highest-value role matters more than listing
  everyone.
- For each shortlisted role, state the manual action plainly: this is something you do
  yourself in your own browser, not something a skill submits on your behalf.
- **Never draft a message to a cold referrer here.** Unlike step 6 below, these are
  strangers, and referral marketplaces typically prohibit automated or bulk outreach to their
  referrers in their own Terms of Service — see `../../data/refer-me.md` for why this
  boundary matters.
- This step never touches Notion. Notion gets updated only once you report back that you
  actually sent a request, per step 7 below.

If you don't use a cold-referral tool, delete this section and just report the no-match roles
in the output manifest without a shortlist.

## 5. Enrich a match (optional, per match)

For each confirmed match, you can optionally verify the contact still shows that employer via
a browser tool, if you have one connected — open the contact's profile URL (from the roster)
and confirm they still show the employer, grabbing a current title if it's changed. The
roster is a point-in-time export and can lag reality.

This should stay scoped to one specific profile you're already connected to and entitled to
view — not bulk crawling, and not a substitute for the roster as the batch-matching source.
Skip this step per-match if the browser tool is unavailable; note the title as "per export
date, unverified" instead of blocking the match.

## 6. Draft the referral ask

For each match, draft one short message **to the contact** — a direct message, not an InMail,
since they're someone you already know. Under `../../context/accuracy-rules.md`'s
referral-voice rules: warm, brief, specific (name the role/company, one line on why it's a
fit, a low-pressure ask). No AI-report structure, no hyperbole-blacklist phrases, same
truthfulness bar as a resume bullet.

**Draft only. Never send.** This holds regardless of how well you know the person — sending
outreach on your behalf isn't something this skill does autonomously, per the automation
boundary in `../../context/ats-learnings.md`.

## 7. Update Notion (lightweight — no schema changes)

For each matched role:
- Set **Source = "Referral"** (already an existing Source option).
- Append to **Notes**: `Known contact: <Name> (<Title>) — referral ask drafted <date>.`
  Append, don't overwrite existing Notes content.
- Leave **Status** untouched — a drafted ask isn't a status change.
- **Idempotency:** if a Notes entry for this contact already exists (same name, same or later
  date), don't duplicate it on a re-run.

For a cold-referral shortlist role from step 4, Notion is untouched until you report back
that you actually submitted a request. Once you do, append to that role's **Notes** (same
append-only, idempotent convention): `Cold referral request sent <date> — status: matched |
viewed | confirmed | denied.` Set **Source = "Referral"** here too, so warm and cold referrals
roll up under the same Source option; the Notes prefix is what distinguishes them.

## 8. Output a manifest

One block per match: company, role, Match %, the contact's name/title/profile URL, and the
drafted message. If running across multiple matches, end with a one-line summary (N matches
across M companies; N review-candidates flagged to confirm manually). Keep it scannable, same
shape as `apply-assist`'s per-role manifest.

Then, if step 4 produced a shortlist, a second block: the ranked cold-referral candidates
(company, role, Match %, why no warm contact exists), capped at your request budget, ending
with how many no-match roles didn't make the cut this run because of that cap.

## Guardrails

- The roster export is the only bulk network source — never scrape a professional network or
  employer data via any other tool. Any profile enrichment stays scoped to the one matched
  contact.
- Never send a message on the candidate's behalf, and never assume one was sent — only record
  "drafted."
- Fuzzy company matches are proposals, not facts — say so plainly rather than asserting a
  connection that might not hold up.
- If Notion or a browser tool is unavailable this run, say so plainly and do as much of the
  rest as possible rather than guessing at what they'd have returned.
- A cold-referral tool, if you use one, stays manual, always — never automate an account
  creation, request submission, or message to a referrer there, and never scrape it.
