# Application Workflow — ATS Learnings

Used by `skills/apply-assist` during Phase B (live ATS form-fill). Browser tool fallback
order: **Chrome MCP** (primary) → **Playwright** → **Claude Chrome extension**.

<!-- TEMPLATE NOTE: this file is mostly reusable as-is — it documents ATS platform behavior,
not personal data. Just replace the staging path below and the outreach-voice note with your
own preference. -->

## All ATS platforms

- **Resume upload must be handed to the user.** Chrome-style `file_upload` tools generally
  only accept files the user has explicitly shared with that session, not arbitrary paths —
  and a "staging" copy in some other local folder may be rejected the same way a random path
  would be, depending on your browser tool. Test this once against your own setup rather than
  assuming a staging copy solves it (see the note in `config.md`). Point the user at wherever
  the file actually lives and ask them to click Attach; also deliver the file via
  `SendUserFile` (or your environment's equivalent) so it appears in chat regardless.
- **Check the accepted file types before generating documents.** Some ATSes accept PDF only,
  or have no cover-letter field at all — building both a `.docx` and a `.pdf` up front avoids
  converting mid-application with the form already open.
- **Always leave to the user:** any truthfulness/anti-AI attestation, voluntary self-ID,
  pronouns, salary fields, EEO disclosures, and the final Submit button. Greenhouse carries a
  penalty-of-law attestation warning specifically about AI-fabricated qualifications.
- **Account creation / login** (e.g., Workday): must be done by the user — do not attempt to
  create accounts or enter passwords.

## Greenhouse

- Dropdowns are React-selects, not native `<select>`. `form_input` sets text but does NOT
  commit the value.
  - **Pattern:** click the field → type the option text → press Return.
  - Residency/state question is a state list, not a Yes/No — pick your actual state.
  - Phone country field: type "United States" → click "United States +1" (adjust for your
    country).
- Stale "This field is required" messages linger after early validation; they clear on
  Submit. A value is committed when the field shows an ✕ clear button.

## Workday (`*.myworkdayjobs.com`)

- **"Autofill with Resume" reliably mangles work history** — it fragments jobs and shifts
  titles/dates. Do NOT use it. Fill work history manually.
- **Tenure accuracy trap:** double-check that Workday's parsed dates match your actual role
  start date, especially where you have a promotion within one employer — don't let a merged
  block imply a longer tenure in your current title than you actually have.
- Degree field is a button-dropdown (click → listbox → click option). Date fields are
  Month/Year spinbuttons.
- Screenshots may time out when the renderer gets sluggish — use `read_page` (accessibility
  tree) to verify field values.

## Post-Application Outreach (InMail) — optional, delete this section if you don't want it

Immediately after submitting an application, identify a hiring manager, a recruiter, and a
director at the company (via LinkedIn — Chrome extension search, since there's no dedicated
LinkedIn MCP) connected to that role or team.

- **Draft, don't auto-send.** Prepare three short InMail messages, one per contact, and
  present them for review — sending outreach to strangers on someone's behalf is not
  something to do autonomously.
- If a recruiter is identified, log them in the Notion **Recruiter Name** / **Recruiter
  LinkedIn** fields; once the candidate confirms they've sent the messages, set the
  **Outreach Sent** date.
- `apply-assist` does this by default as part of taking a role from "To Apply" to submitted —
  this is the standing convention it follows, and applies as-is to any manual, non-Apply-
  Assist application too.
- Draft in the candidate's own voice: plain conversational prose, no bold headers or bullet
  "findings" — it should read like they wrote it, not like an AI report.

## Employer "AI in hiring" policy language

Some employer careers sites carry a general "AI During the Hiring Process" policy statement
prohibiting AI-generated application materials unless the employer explicitly authorizes it.
This is distinct from a per-application anti-AI attestation checkbox (that one always stays
with the candidate, per the automation boundary below, unchanged).

**Generic careers-site boilerplate** (a broad statement with no specific method or disclosure
field attached) most plausibly targets AI-written interview or assessment responses, not
resume/cover-letter tailoring done ahead of applying — but this is a judgment call, not a
certainty, and reasonable people (and employers) could read it either way. Decide your own
standing position on this once, write it down here, and apply it consistently rather than
re-litigating it per application. If a policy reads as unambiguously broader than that (e.g.
it explicitly names resumes/cover letters, not just "responses" or "assessments"), don't
assume your standing position covers it — treat it as the next case below instead.

**Employer-specific candidate AI policies are a different case entirely, not covered by a
generic standing position.** Some employers publish a named, candidate-facing AI policy AND
attach a required disclosure field to the application form (e.g. a dropdown asking which AI
tools you used and how). That's categorically different from generic boilerplate:

- **Read the linked policy before filling any field.** A dropdown or checkbox named for an AI
  policy is the tell — don't answer it from assumption.
- **Tailoring the master resume is usually still fine** even under a strict policy, since it's
  the candidate's own work being retargeted — that's typically "refine," not "generate."
  Confirm this reading against the specific policy's wording, though; don't assume it.
- **Free-text essay answers are the highest-risk case.** A policy that permits "refining your
  own draft" but prohibits generating an answer from a prompt means: the candidate drafts
  first, in their own words, and any AI assistance comes after — supplying raw material
  (facts, real incidents, numbers) for someone else to draft from, then refining their draft,
  is a very different thing from writing the answer for them.
- **A cover letter written from scratch by AI likely falls on the prohibited side** of that
  same line under a strict policy. If the form has no cover-letter field, simplest is to just
  not attach one rather than test the boundary.
- The risk of getting this wrong isn't only rejection — on a role where the pitch is judgment
  about these systems, violating the employer's own stated AI policy undercuts the candidacy
  directly, not just the paperwork.

## Automation boundary (MANDATORY — this is the canonical statement; other files reference it)

"Maximize automation" up to, not through, these — the candidate always does: the
truthfulness/anti-AI attestation, voluntary self-ID, pronouns, salary fields, EEO disclosures,
account creation/login, sending the drafted outreach, and the final Submit button. Nothing in
this plugin clicks Submit or Send on the candidate's behalf, and nothing fabricates a
qualification to clear a gate — see `accuracy-rules.md`.
