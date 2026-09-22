---
name: referral-match
description: Match the candidate's LinkedIn network against open "To Apply" roles in the Notion Job Search Pipeline, draft warm referral-request messages to friends at matched companies, and surface a budget-capped refer.me cold-referral shortlist for roles with no warm contact.
---

You are running Referral Match for the candidate, part of the `job-search-agent` plugin.
This skill closes a gap `apply-assist` already names but can't act on: its gate checks treat a
warm referral as a differentiator that can lift a borderline role over the resume-build floor,
but nothing in the plugin has ever known *whether the candidate actually knows someone* at a given
company. This skill is that missing data source — it joins the candidate's LinkedIn connections against
the pipeline and drafts the ask, so a warm referral becomes something detected, not something
the candidate has to remember role by role.

Added 2026-07-29: for roles with no warm contact, this skill also surfaces a prioritized,
budget-capped refer.me shortlist (step 4) — a cold-referral fallback, not a warm one, and
deliberately manual (see `../../data/refer-me.md`).

Every generated message must follow `../../context/accuracy-rules.md` exactly, including the
"Referral / warm-outreach voice" section — draft only, in the candidate's own voice, no em dashes.
Candidate facts and scoring guardrails are in `../../context/candidate-profile.md`; the
connections-file path, Notion bindings, and refer.me account tier are in
`../../context/config.md`; pipeline IDs and field schema are in
`../../context/notion-schema.md`.

**Invocation:** `/referral-match` (all matched "To Apply" roles at or above the 55% floor),
`/referral-match <Company>` (one named role), `/referral-match --min <N>` (raise or lower the
match threshold for this run). Ask which mode if ambiguous.

## 1. Read the roster

Read the connections-CSV path from `../../context/config.md`. Read the file.

- **Missing or unreadable:** stop and tell the candidate how to get it (LinkedIn → Settings & Privacy →
  Data Privacy → "Get a copy of your data" → Connections → request → download, usually ready in
  ~10 minutes; save to the configured path). Don't guess at matches without it.
- **Present but stale** (file modified more than ~90 days ago): warn the candidate it may be out of date
  (people change jobs), then proceed — a stale roster is still better than none.
- **Format:** a LinkedIn Connections export has a 2-3 line notes preamble before the real header
  row. Parse starting from the row that contains `First Name`, `Last Name`, `Company`, `Position`
  — don't assume row 1 is the header. Expected columns: First Name, Last Name, URL, Email
  Address (often blank), Company, Position, Connected On.

## 2. Pull the pipeline

Query Notion for `Status = "To Apply"` (IDs and query quirks in `../../context/notion-schema.md`),
ranked Match % descending. Default threshold is the same **55% resume-build floor** `apply-assist`
uses; `--min` overrides it for this run. Skip any page whose title already starts with `❌`
(Rejected) — never match against those.

## 3. Join on Company

For each candidate role, normalize its Company title and compare against each connection's
`Company` column, using **`scripts/normalize.py`** (`normalize_company`; CLI: pipe names on
stdin), the single normalization every skill shares. Do not restate the rules in prose here.

- **Exact or suffix-only match** → confirmed match.
- **Fuzzy but not exact** (e.g. "Google" vs "Google DeepMind", "Cisco" vs "Cisco Meraki") →
  flag as a **review candidate**, don't auto-assert it. The CSV `Company` field is self-reported
  free text and can be stale or imprecise; a wrong assertion here (telling the candidate they know someone
  they don't, or missing that they do) is worse than asking.
- A company can have multiple connections; a connection's company can have multiple open roles.
  Surface every combination — don't collapse to one match per company.

## 4. No warm match — the refer.me cold-referral shortlist

Added 2026-07-29. `referral-match` used to go silent on a role with no connection match; that
silence was the gap. For every candidate role from step 2 that produced **no** match in step
3 (confirmed or review-candidate), the candidate still might be able to get a referral cold, through
refer.me — see `../../data/refer-me.md` for why that site is manual-only and never automated.

- Rank the no-match roles the same way the aging-queue convention in
  `../../context/notion-schema.md` does: Match % descending, newer-first tiebreak.
- Cap the list at the remaining request budget from the refer.me tier in
  `../../context/config.md` (Basic = 1/week, Premium = 40/month) — the cap is the point;
  spending a scarce request on the highest-value role matters more than listing everyone.
  If the candidate hasn't said how many they're already used this period, ask rather than guessing, or
  cap conservatively and say so.
- For each shortlisted role, state the manual action plainly: open refer.me, search the
  company, and if a verified referrer exists there, submit the request against that role's
  Job URL (refer.me accepts an externally pasted job link — the role doesn't need to already
  be in its own inventory).
- **Never draft a message to the referrer here.** Unlike step 5 below, these are strangers,
  and refer.me's Terms of Service prohibit "harassing or spamming Referrers" — the entire
  reason this step exists instead of automating a message. Drafting one would defeat the
  reason refer.me was kept manual in the first place.
- This step never touches Notion. Notion gets updated only once the candidate reports back that they
  actually sent a request, per step 6 below.

## 5. Enrich a match (optional, per match)

For each confirmed match, the candidate has chosen to enrich via the Claude Chrome extension: open the
connection's profile URL (from the CSV) and confirm they still show that employer, grabbing a
current title if it's changed. The CSV is a point-in-time export and can lag reality.

This is interactive browsing of one specific profile the candidate is already connected to and entitled
to view — not bulk crawling, and not a substitute for the CSV as the batch-matching source. Skip
this step per-match if the extension is unavailable; note the title as "per <export date> export,
unverified" instead of blocking the match.

## 6. Draft the referral ask

For each match, draft one short message **to the friend** — a direct message, not an InMail,
since they're a 1st-degree connection the candidate already knows. Under
`../../context/accuracy-rules.md`'s referral-voice rules: warm, brief, specific (name the
role/company, one line on why it's a fit, a low-pressure ask — "would you be open to referring me
/ putting in a good word?"). No em dashes, no AI-report structure, no hyperbole-blacklist phrases,
same truthfulness bar as a resume bullet.

**Draft only. Never send.** This holds regardless of how well the candidate knows the person — sending
outreach on their behalf isn't something this skill does autonomously, per the automation boundary
in `../../context/ats-learnings.md`.

## 7. Update Notion (lightweight — no schema changes)

For each matched role:
- Set **Source = "Referral"** (already an existing Source option).
- Append to **Notes**: `Known contact: <Name> (<Title>) — referral ask drafted <date>.` Append,
  don't overwrite existing Notes content.
- Leave **Status** untouched — a drafted ask isn't a status change.
- **Idempotency:** if a Notes entry for this contact already exists (same name, same or later
  date), don't duplicate it on a re-run.

For a refer.me shortlist role from step 4, Notion is untouched until the candidate reports back that
they actually submitted a request. Once they do, append to that role's **Notes** (same append-
only, idempotent convention): `Refer.me request sent <date> — status: matched | viewed |
confirmed | denied.` Set **Source = "Referral"** here too, so warm and cold referrals roll up
under the same Source option; the Notes prefix (`Known contact:` vs `Refer.me request sent`)
is what distinguishes them. If the candidate later reports a status change (viewed, confirmed,
denied), append a new dated line rather than editing the old one.

## 8. Output a manifest

One block per match: company, role, Match %, the friend's name/title/profile URL, and the
drafted message. If running across multiple matches, end with a one-line summary (N matches
across M companies; N review-candidates flagged for the candidate to confirm manually). Keep it scannable,
same shape as `apply-assist`'s per-role manifest.

Then, if step 4 produced a shortlist, a second block: the ranked refer.me candidates (company,
role, Match %, why no warm contact exists), capped at the request budget, ending with how many
no-match roles didn't make the cut this run because of that cap.

## Guardrails

- The CSV export is the only bulk network source — never scrape LinkedIn connections or
  employers via any other tool. Chrome enrichment stays scoped to the one matched profile.
- Never send a message on the candidate's behalf, and never assume they're sent one — only record "drafted."
- Fuzzy company matches are proposals, not facts — say so plainly rather than asserting a
  connection that might not hold up.
- If Notion or the Chrome extension is unavailable this run, say so plainly and do as much of
  the rest as possible rather than guessing at what they'd have returned.
- refer.me stays manual, always — never automate an account creation, request submission, or
  message to a referrer there, and never scrape it. See `../../data/refer-me.md` for why.
