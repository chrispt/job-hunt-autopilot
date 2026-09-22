# Application Workflow: ATS Learnings

Used by `skills/apply-assist` during Phase B (live ATS form-fill) and by `apply-prep` when
writing the "What you must do" section of a manifest. Add your own findings as you meet new
platforms; keep entries factual and dated.

**Browser tool order:** the Claude in Chrome extension first (it carries your logged-in
sessions: LinkedIn, ATS candidate portals), Playwright second, the in-app browser last. The
in-app browser renders authenticated pages as logged-out, which looks like an empty page or a
dead posting rather than an error.

## All ATS platforms

- **Resume upload is yours.** The browser tools cannot attach arbitrary local files. The agent
  points you at the packet folder and you click Attach.
- **The uploaded filename never contains the company name.** Generic filename, company in the
  folder (see `config.md`).
- **Check accepted file types before staging.** Some ATSes accept PDF only; a PDF is built
  alongside every `.docx` for this reason.
- **Always yours:** truthfulness / anti-AI attestations, voluntary self-identification,
  pronouns, salary fields, EEO disclosures, account creation and login, and the final Submit.
- **Diff parsed work history against your master resume** before advancing a step. Resume
  parsers merge consecutive roles at one employer and date the later title from the earlier
  start, which silently inflates tenure. Where the ATS stores a candidate profile, fix it
  there so the correction covers every future application at that employer.
- **Prune auto-extracted skill tags** against `accuracy-rules.md`; parsers invent tags from
  fragments of phrases.
- **Screening questions are a verified set, never a default.** Visa sponsorship, work
  authorization, and any criminal-history question you have pre-answered in
  `candidate-profile.md` get answered explicitly and then confirmed on a fresh screenshot or
  accessibility read, before Save and again on the Review page. Sponsorship questions have been
  seen with "Yes" pre-selected by the widget; a wrong answer there disqualifies the application
  silently and immediately, with no error and no human review. Anything outside what the
  profile covers (misdemeanors, pending charges, background-check consent wording) goes to you.

## Work Experience and Education: always fill them in

Fill both sections whenever the form offers them, **even when they are not marked required**.
Structured fields are what recruiters search and screen on, and "the resume PDF covers it" is
not a safe trade: on Workday an application cannot be amended after Submit.

- Enter every role by hand, one entry each, from the master resume (live read per
  `config.md`). Never use "Autofill with Resume"; see the tenure trap above.
- Descriptions: copy or lightly trim the resume's own bullets for that role. Add no new
  claims; `accuracy-rules.md` applies to form fields exactly as it does to documents.
- Skills: leave blank unless you say otherwise (auto-tagging invents claims).
- On Workday, save the My Experience step after the entries are in and **before** the resume
  upload (the upload reloads the page).
- **Gate:** check at the My Experience step and again on the Review page. "No Response" under
  either section is a blocker; fill it before calling the review clean or handing over Submit.
- The only reasons to leave a section empty: the form has no such section, or you say to skip
  it on this application. If a tenant's school lookup is empty and rejects free text, delete
  only the Education sub-entry, keep Work Experience, and note it.

## Greenhouse

- Dropdowns are React selects: `form_input` sets text without committing. Click the field,
  type the option, press Return. A value is committed when the field shows a clear (✕) button.
- Stale "This field is required" messages linger after early validation; they clear on Submit.

## Workday (`*.myworkdayjobs.com`)

- "Autofill with Resume" fragments work history; fill it manually.
- Step 1 is usually account creation or sign-in; nothing is reachable before it. That step is
  yours.
- **Save the step before handing over the resume upload.** The upload reloads the page and
  discards everything unsaved on the current step.
- `form_input` does not commit Workday text inputs (React `onChange` never fires). Use real
  keystrokes: click the field by `ref`, triple-click to select, type.
- Click by `ref`, never by coordinate: the page auto-scrolls on focus, so coordinates go stale
  inside a batch.
- **Select dropdown options by clicking the option, not by typing and pressing Return.**
  Keyboard selection can commit to a different question than the list you opened (it has
  flipped a neighbouring screening answer). Open the list, read the options fresh, click the
  option by `ref`, then verify on a screenshot. Option refs go stale once the list closes, so
  re-open and re-read rather than reuse them. Verify checkbox grids visually too.
- A tenant's reference lists (schools, certifications) can be empty, making a required
  sub-entry unsatisfiable; delete the sub-entry rather than leave it half-filled.

## Oracle Cloud HCM, iCIMS, single-page careers sites

- Postings render client-side; an anonymous fetch returns a bare header. Treat that as
  inconclusive, never as expired.
- Oracle keeps a server-side draft across session timeouts; check what survived before
  re-entering.

## Post-application outreach (LinkedIn)

- Draft, never auto-send: one message each to a likely hiring manager, a recruiter, and a
  director connected to the team. Presented to you for review.
- **Read the actual thread before drafting.** A blank Outreach Sent field is not proof nothing
  was sent; re-introducing yourself to someone you already messaged reads worse than silence.
- 1st-degree connections: a normal message, no limit. 2nd/3rd degree: a connection-request
  note capped at 300 characters (count them, do not eyeball), or an InMail if you have
  credits. Prepare the long version too for after acceptance.
- Log the recruiter's name and profile in Notion; set Outreach Sent only after you confirm you
  sent something.

## Automation boundary (MANDATORY; the canonical statement)

Maximize automation up to, not through, these; you always do them: the truthfulness /
anti-AI attestation, voluntary self-ID, pronouns, salary fields, EEO disclosures, account
creation and login, sending any outreach, and the final Submit. Nothing in this plugin clicks
Submit or Send on your behalf, and nothing fabricates a qualification to clear a gate.
