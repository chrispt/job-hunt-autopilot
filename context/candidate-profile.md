# Candidate Profile & Job-Search Strategy (single source of truth)

This file is the ONLY place your facts, scoring guardrails, hard screens, and salary floor are
defined. Every skill reads it instead of restating any of it. Fill it in once; the `/setup-job-search`
command walks you through it. Two layers:

1. **Facts**: roles, dates, education, certifications. Your master resume wins on any conflict
   (path and read recipe in `config.md`); this section is the fallback when the resume cannot
   be read and is where you record things the resume does not carry (mailing address, phone).
2. **Strategy**: target roles, scoring guardrails, hard screens, salary floor, location rules.
   Not in the resume; always applied on top of the resume facts.

## Facts (fallback snapshot; the resume wins)

- **Name**: <Your Name>, <City, ST>, <you@example.com>, <linkedin.com/in/your-handle>
- **Mailing address (used on ATS forms)**: <street, city, ST, zip>. Phone <digits>. Recording
  it here is what lets the agent fill address fields without asking each time; never let it
  invent one if this line is missing.
- **Current / most recent role**: <Company> (<start> to <end>): <Title>. One or two lines on
  what you actually owned versus supported. Be exact about scope; every generated document
  inherits this framing (see `accuracy-rules.md`).
- **Earlier roles**: <Company> (<dates>): <Title>. Repeat as needed.
- **Education**: <degree, school, year>; anything in progress with expected completion.
- **Certifications**: <exact names as they appear on the certificate>.

## Strategy (always applied; not in the resume)

- **Target roles** (the "pivot targets" the sweep scores against): e.g. AI Product Manager,
  Technical PM, Customer Success Leader, Enablement. Say which are primary and which are
  acceptable in familiar domains only.
- **Hard screens** (create no row at all; role-level keywords live in `data/screens.json`,
  company-level passes in `data/exclusions.md`): e.g. "no contact-center deployment roles",
  "no roles requiring an active security clearance I do not hold".
- **Scoring guardrails**: where you are strongest (score up) and which stated minimums have
  rejected you before (score down). Example shape: "PM tenure is ~3 years inside a 20-year
  career, so postings gated on 8+ years of dedicated PM experience drop a tier; customer
  success tenure is 7 years continuous, so a 7-10 year CS minimum is cleared, not a stretch."
- **Experience gate thresholds** (used by apply-assist step 5): stated minimum years of the
  primary discipline at or above <N> = full tier drop; <N-3 to N-1> years = neutral when the
  posting is framed in transformation / change-management language, tier drop when framed as
  dedicated ownership; stated people-management minimum at or above <M> years = tier drop.
  An unstated minimum is never a fail.
- **Seniority screen**: titles the sweep discards outright (Director, Head of, VP, ...) and
  titles that only drop a tier (Principal, Staff). Patterns live in `data/screens.json`; put
  the reasoning here (for most candidates: Director-and-above postings screen on
  people-management scope that an individual contributor cannot show).
- **Location modifier**: home base, remote preference, which metros carry no penalty, how many
  points hybrid/on-site elsewhere loses. Do not filter by location; score it.
- **Salary floor**: <$N base>. Below-floor postings are flagged as bridge options, never
  silently scored on fit; `apply-prep` builds no packet for a clearly below-floor posting
  without your say-so. Sources with a hard intake filter (LinkedIn digests) discard them.
- **Standout rule**: a new role scoring at or above <80>%, or at a company where you know
  someone (connections roster, `config.md`), jumps the queue for the next packet run.

## Learning roadmap (read by cert-nudge)

Ordered list of courses / certifications you are working through, with status:
1. ✅ <done>
2. 🔄 <in progress>
3. ⏭️ <next>
