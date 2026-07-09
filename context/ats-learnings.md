# Application Workflow — ATS Learnings

Used by `skills/apply-assist` during Phase B (live ATS form-fill). Browser tool fallback
order: **Chrome MCP** (primary) → **Playwright** → **Claude Chrome extension**.

<!-- TEMPLATE NOTE: this file is mostly reusable as-is — it documents ATS platform behavior,
not personal data. Just replace the staging path below and the outreach-voice note with your
own preference. -->

## All ATS platforms

- **Resume upload must be handed to the user.** The Chrome `file_upload` tool only accepts
  session-shared files, not arbitrary paths. Workaround: stage a copy in
  `REPLACE-WITH-YOUR-LOCAL-STAGING-FOLDER` (see `config.md`) and ask the user to click Attach.
  Also deliver the file via `SendUserFile` so it appears in chat.
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

## Automation boundary (MANDATORY — this is the canonical statement; other files reference it)

"Maximize automation" up to, not through, these — the candidate always does: the
truthfulness/anti-AI attestation, voluntary self-ID, pronouns, salary fields, EEO disclosures,
account creation/login, sending the drafted outreach, and the final Submit button. Nothing in
this plugin clicks Submit or Send on the candidate's behalf, and nothing fabricates a
qualification to clear a gate — see `accuracy-rules.md`.
