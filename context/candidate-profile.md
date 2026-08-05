# Candidate Profile & Job-Search Strategy (single source of truth)

<!-- TEMPLATE — this whole file is an example. Replace every fact and strategy line below
with your own before using this plugin. Keep the two-layer structure; it's what keeps
"what's true" separate from "what I'm optimizing for," and lets skills reference one file
instead of restating any of it. -->

This file is the ONLY place candidate facts, scoring guardrails, and the salary floor are
defined. Skills reference this file instead of restating any of it. Two layers:

1. **Facts** (roles, dates, education, certs) — the live master resume wins on any conflict
   (read it per the recipe in `config.md`); this section is the fallback when your resume
   storage is unavailable, and should be kept roughly in sync with the real resume.
2. **Strategy** (pivot targets, scoring guardrails, salary floor, location rules) — NOT in
   the resume; always applied on top of the live resume facts.

## Facts (fallback snapshot — resume wins)

_Example shape — replace with your own:_

- **Your Name** — City, State · you@example.com · linkedin.com/in/you
- **Mailing address / phone for ATS forms (optional):** some ATS forms require a mailing
  address and phone number as required fields, not just a resume upload. If you're
  comfortable having these entered automatically, record them here once and say so
  explicitly — otherwise leave this blank and expect to be asked each time one is needed.
  Never let a skill invent an address or phone number if this line is blank or stale.
- **Most Recent Employer** (start–present): Title (date range), promoted from/started as
  ... . What you actually own vs. don't (e.g., "drives adoption strategy, not core
  product-roadmap ownership" — be precise here, this framing gets reused verbatim in
  generated documents).
  - **If a promotion happened within this employer**, decide up front whether the tenure
    clock for a given qualification (e.g. "years in customer success") should span both
    roles or just the current one, and say so explicitly here. A promotion within one
    employer is continuous tenure in the broader function, not a restart — getting this
    wrong can understate you against a posting's stated experience minimum.
- **Prior Employer** (date range): Title(s) and focus area.
- **Education:** degrees, in-progress programs with expected completion.
- **Certifications:** exact names as they appear on your real resume — don't paraphrase
  cert names, ATS keyword-matching and interviewers both care about exact wording.

## Strategy (always applied — not in the resume)

_Example shape — replace with your own:_

- **Pivot targets:** the 2-4 role families you're actually aiming for, and how they build on
  your background. Note any adjacent role type that's OK in familiar sub-domains but risky
  in unfamiliar ones (e.g. "X roles are fine in domain A, avoid domain B where I'm not
  current").
- **Scoring guardrails:** where you're strongest, and any screen that reliably rejects you
  (e.g. a tenure-length gate) so discovery can score those roles lower rather than repeatedly
  wasting effort on them. Note any domain where your knowledge is adjacent rather than
  practitioner-level, so generated documents don't overclaim it.
- **Experience gate (structural screens):** if postings in your target roles commonly state
  a hard minimum (years of experience in a role, years of people management, a specific
  required certification), name the exact thresholds here so `apply-assist` can check the
  posting's stated number against them and drop a tier when it's met or exceeded — rather
  than relying on a vague impression of "this looks senior." Treat an **unstated** minimum as
  no signal at all; only an explicit number at or above your threshold should trigger the
  drop. A warm referral or other differentiator can still override this gate — say so if you
  want that judgment call available.
- **Location modifier:** your base location, relocation willingness, and how remote vs.
  hybrid vs. on-site should affect scoring (e.g. "remote = no penalty; hybrid outside my
  metro = score N points lower").
- **Salary floor:** your real floor. Postings below it shouldn't be silently scored on fit
  alone — decide whether they get flagged as a bridge option or discarded outright, and say
  so here so `daily-sweep` and `apply-assist` apply it consistently.
