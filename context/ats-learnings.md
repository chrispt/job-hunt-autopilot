# Application Workflow: ATS Learnings

Used by `skills/apply-assist` during Phase B (live ATS form-fill) and by `apply-prep` when
writing the "What you must do" section of a manifest. Add your own findings as you meet new
platforms; keep entries factual and dated.

**Browser tool order:** the Claude in Chrome extension first (it carries your logged-in
sessions: LinkedIn, ATS candidate portals), Playwright second, the in-app browser last. The
in-app browser renders authenticated pages as logged-out, which looks like an empty page or a
dead posting rather than an error.

## All ATS platforms

- **The agent attaches the resume and cover letter.** The Chrome extension's `file_upload`
  rejects arbitrary local paths (your documents folder, Downloads) but accepts files in the
  session's scratchpad directory. So the agent copies the role's PDFs from the packet folder
  into `<scratchpad>/upload/<company>/` (generic filenames unchanged), uploads from there, and
  verifies: the copy's sha256 matches the original, the cover letter's salutation names this
  company, and the form shows both filenames. The packet folder stays the record. If you
  upload a file yourself, the agent confirms it is this role's version by its content.
- **The uploaded filename never contains the company name.** Generic filename, company in the
  folder (see `config.md`).
- **Check accepted file types before staging.** Some ATSes accept PDF only; a PDF is built
  alongside every `.docx` for this reason.
- **Fill what your standing answers cover, leave the rest.** Voluntary self-ID, EEO,
  disability and pronouns are filled only from the "Standing application answers" you
  recorded in `candidate-profile.md`; if that section is empty, those fields stay yours.
  Salary-expectation text uses the salary-field rule there and is always called out for your
  check. **Always yours:** truthfulness / anti-AI attestations and certifications (including
  ones you sign by typing your name), account creation and login, consent/privacy agreements,
  any question your standing answers don't cover, and the final Submit.
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
- **Refs go stale after a file upload.** The form re-renders, so clicks and typing by `ref`
  land nowhere with no error. Focus the field by its stable id through `javascript_tool`
  (`document.getElementById('first_name').focus()`), then type real keystrokes, and read the
  value back by id.
- **React selects by id:** focus the input, press a real Down key to open it, then click the
  option inside the element named by the input's `aria-controls`. Synthetic key events do not
  open the list. Options can be whole sentences, so match on a prefix.
- **School lookups are async:** type a short term, wait a few seconds, then click the option.
- **Employer-hosted wrappers can hang.** When a company's own apply page (a wrapper around
  Greenhouse) never finishes loading, the embed form is the same requisition and loads
  directly: `https://boards.greenhouse.io/embed/job_app?for=<board>&token=<job id>`.

## Phenom front ends (university and enterprise careers sites over Workday)

- The resume-parse upload and some Next clicks can freeze the browser tab for minutes. Wait,
  retry, and if it stays dead, reload.
- `element.focus()` may not take keystrokes. Scroll the field to the centre with
  `scrollIntoView({block:'center'})`, then click its screen coordinates and type.
- Month/year pickers only accept clicks on the month grid, not typing.
- The Review page may omit the questions and voluntary-disclosure steps; verify those on
  their own steps.

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

- Set up, never send: one message each to a likely hiring manager, a recruiter, and a
  director connected to the team. After you confirm the application is submitted, the agent
  opens one browser tab per contact, clicks Connect (often under More), clicks Add a note,
  types the note and checks the character counter. You click Send in each tab.
- The invitation dialog is usually missing from the accessibility tree, so the agent works it
  by screenshot and coordinates. Glance at each profile's Experience first: it sometimes shows
  the person runs the exact program, which is worth one line in the note.
- **Read the actual thread before drafting.** A blank Outreach Sent field is not proof nothing
  was sent; re-introducing yourself to someone you already messaged reads worse than silence.
- 1st-degree connections: a normal message, no limit. 2nd/3rd degree: a connection-request
  note capped at 300 characters (count them, do not eyeball), or an InMail if you have
  credits. Prepare the long version too for after acceptance.
- Log the recruiter's name and profile in Notion; set Outreach Sent only after you confirm you
  sent something.

## Automation boundary (MANDATORY; the canonical statement)

**The agent fills, then you check:** every form field your recorded facts and standing
answers cover, including attaching the resume and cover letter, self-ID/EEO/pronouns (only
from `candidate-profile.md`), and proposed salary-expectation text (always flagged). It also
sets up LinkedIn outreach, one tab per contact, and reads the Review page back to you.

**You always do:** the final Submit; clicking Send on every message; any truthfulness, anti-AI
or certification attestation; account creation, login and passwords; consent/privacy
agreements; and any question your standing answers don't cover. Nothing in this plugin clicks
Submit or Send on your behalf, and nothing fabricates a qualification to clear a gate.

If you would rather keep self-ID, EEO and salary fields to yourself, leave the standing
answers section in `candidate-profile.md` empty and delete its salary-field rule; the agent
then leaves those fields alone.
