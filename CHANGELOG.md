# Changelog

## 0.6.0 (2026-10-26)

Warm-first applying. Across 166 applications, the ones with a referral or a hiring-team
contact reached an interview about 14% of the time and cold ones about 1.5%, yet only 4 of
the last 33 had a referral. A referral that arrives after you apply usually doesn't attach.

- **Referral hold (apply-assist step 5a).** When the company is in your connections roster,
  the referral ask is drafted first, the role gets a `Referral hold:` Notes line with an
  apply-by date three business days out, and Phase B waits for the referral link or that
  date. The packet is still built during the hold. apply-prep and link-list batch mode run
  the same gate; batch mode joins every link against the roster up front.
- **Standout = someone you know.** A Match % of 80+ no longer jumps the apply-prep order
  (`standout.match_threshold` is now null in `data/screens.json`; the top score band had
  never produced an interview).
- **Outreach is part of submitting.** A Phase B run isn't finished until the hiring-manager,
  recruiter and director notes are set up for you to send, hiring manager first. Skipping
  one is recorded as `Outreach skipped <date>: <reason>`.
- **Measuring it.** funnel-review reports a warm vs cold table and the warm share of
  apps-out (target: at least half); `/job-status` lists referral holds and their due dates.

## 0.5.2 (2026-10-09)

- **Liveness before any packet work.** LinkedIn's public `jobs-guest` endpoint served two
  closed postings as open, and both packets were rebuilt for nothing. It is now used for JD
  text only. apply-assist (including link-list workers) and apply-prep confirm the req on the
  employer's ATS job list or logged-in LinkedIn before building or rebuilding, check the
  workplace type against your location rule, and record the liveness source in the manifest.
- **Form-fill notes:** iCIMS iframe forms (fill via `contentDocument`, attach files yourself,
  "Submit Profile" step buttons) and dropped keystrokes when the Chrome window lacks focus.

## 0.5.1 (2026-10-09)

Lessons from the first real packet built with the 0.5.0 checks.

- **Cover letter length check.** `scripts/ats_check.py pages --pdf <file> --max 1` reports the
  page count and what spilled onto the extra page. apply-assist runs it on every cover letter.
- **Page-1 slack.** If your master resume starts page 2 with a section or page break, lines
  added to page 1 push all of page 2 onto a third page. Tailoring now keeps page-1 edits
  length-neutral and re-checks the page count after each export.
- **Exact JD wording for the term map.** `WebFetch` paraphrases pages through a summarizing
  model, so the term list is built from the raw posting text instead (fetch, then strip the
  HTML). LinkedIn's public `jobs-guest` endpoint is documented as a way to read a posting
  without the browser extension.

## 0.5.0 (2026-10-09)

Built to get more applications past the automated screen and in front of a person.

- **JD term coverage.** Before tailoring, apply-assist and apply-prep list the posting's own
  required and preferred terms and its title wording, and map each to a fact in your master
  resume. Backed terms are carried into the headline, summary, Core Competencies and bullets
  in the JD's phrasing; terms with no honest backing are reported as gaps and never inserted.
  `scripts/ats_check.py coverage` measures the result against your master.
- **PDF parse check.** `scripts/ats_check.py parse` reads each tailored PDF the way a plain ATS
  parser would and checks contact details, headings, employers, titles, date ranges, dates
  sitting next to their titles, and risky glyphs. Needs `pypdf` (`python -m pip install
  pypdf`); without it the check reports SKIPPED. Fill in `data/resume-expect.json` once.
- **Packet manifest** gains an "ATS check" section, and Notion Notes gain one greppable
  `ATS terms: req x/n, pref y/m, title hit|miss, parse ...` line per packet.
- **Accuracy rules:** new "JD vocabulary and ATS alignment" section (what rewording is allowed,
  what is not: no hidden text, no keyword dumps, no unbacked terms).
- **Standing answers:** optional years-of-experience figures in your candidate profile, so
  "how many years of X" questions can be filled honestly (never rounded up).
- Template ATS notes now carry the 0.4.0 Workday Submit safeguard, and the template version
  files match the release.

## 0.4.0 (2026-10-08)

- **Link-list batch mode for `apply-assist`.** Paste a list of job posting links (or run
  `/apply <url> <url> ...`). The pipeline check runs once up front, then one background worker
  per link does the prep: JD read, scoring, gates, Notion row, tailored packet and outreach
  drafts, at most 5 at a time. You get one summary table. Form-filling still goes one
  application at a time, since each one needs you for login, consents and Submit.
- **Workday Submit safeguard.** On the Review step, Workday's "Save and Continue" button
  becomes Submit while keeping the same element. apply-assist now re-reads the current step and
  the button text before every click on it, never clicks it in the same batch as a step you
  just did, and stops when a pre-click check comes back empty.
- **Workday notes:** upload first when a tenant makes the resume required on My Experience,
  and ask before entering an in-progress degree on an Education section that has no dates.

## 0.3.1 (2026-10-06)

- **`userdata.py status` no longer calls untouched templates "edited".** On a fresh install,
  before the first session has restored your files, it reported every template as "edited here,
  not yet saved". It now says "not restored yet" (or "saved copy will be restored" when you
  already have one). Nothing was ever at risk: saving is blocked for a folder that has not been
  restored. Display fix only.

## 0.3.0 (2026-10-06)

Your setup now survives plugin updates.

- **Personal files are kept in Claude Code's persistent plugin data folder** and restored into
  each new version folder. Before this, setup wrote your profile, Notion ids, queries, screens
  and config into the version folder, and `claude plugin update` left them behind. Two hooks
  (`hooks/hooks.json`) run `scripts/userdata.py`: `apply` at session start, `save` at the end of
  every turn. Skills and scripts read the same paths as before.
- **Safe by construction:** a folder that has not been restored never saves, so a fresh
  template can not overwrite your saved copy. Unsaved edits survive a new session.
- **Release notices:** when an update changes a data file you have customized, the first session
  says which one. Your copy stays in use.
- **Coming from 0.2.x:** run `userdata.py import <old version folder>` once. The first session
  after the update prints the command. `userdata.py status` shows what is saved.

## 0.2.9 (2026-10-06)

Two fixes found by the first sweep after Director titles were allowed through.

- **Dedup no longer merges different Director roles.** A title like "Director, AI Governance"
  used to reduce to just "director" and match any other Director role at the same company.
  When the part before the comma is only a rank word, the whole title is compared instead.
  Location and team variants of a functional title (for example "Product Manager, Growth" vs
  "Product Manager, Payments") still dedupe as before.
- **`daily-sweep` no longer tells the agent to skip digests.** Step 2 listed "<Role> at
  <Company>" as a single-job email. Only "You may be a fit for X's Y role" is a single; every
  other alert subject is a multi-listing digest and is opened. A test now guards the wording.

## 0.2.8 (2026-10-06)

Examples and test data only, no behavior change. Replaced real employer names in the incident
log, skill examples and test fixtures with generic placeholders, and strengthened the release
builder's leak check so those names cannot come back.

## 0.2.7 (2026-10-06)

Director titles are flagged for a look instead of discarded.

- **Director and Associate Director now flag, not discard,** at intake. The row is created,
  scored normally with no title penalty, and noted as Director-level so you can glance at it.
  Head of, Vice President, SVP, EVP, CXO and Chief Officer titles are still discarded. If
  Director-and-above scope is a real mismatch for you, move those two patterns back to
  `discard_patterns` in `data/screens.json`.
- The stated-minimum gates (for example 5+ years of people management) still apply whatever
  the title.
- `funnel-review` proposes Director rows that were withdrawn on title alone for a second look,
  and keeps tracking Director-titled outcomes so you can judge the change on evidence.

## 0.2.6 (2026-10-05)

No change to the public edition (a personal-profile update only). Version kept in step with the source.

## 0.2.5 (2026-09-24)

`apply-assist` now does most of the last mile with you, and stops at Submit and Send.

- **Attaches the resume and cover letter itself.** The browser upload tool accepts files in
  the session's scratchpad folder, so the agent copies the packet's PDFs there, uploads them,
  and verifies them (sha256 against the originals, cover-letter salutation, filenames read
  back from the form).
- **Fills self-ID, EEO and pronoun fields only from answers you record** in the new optional
  "Standing application answers" section of `candidate-profile.md`, and proposes
  salary-expectation text from an optional salary-field rule. Leave either blank and those
  fields stay yours.
- **Sets up LinkedIn outreach after you submit:** one tab per contact with Connect, Add a note
  and the note typed in, so you only click Send.
- Reads the Review page back before handing over Submit.
- ATS notes: Greenhouse refs going stale after an upload (focus by id instead), the Greenhouse
  embed URL for employer wrappers that hang, and Phenom careers sites that freeze on resume
  parsing.
- The automation boundary is restated to match: the agent never clicks Submit or Send, never
  signs an attestation, and never answers a question your recorded answers don't cover.

## 0.2.4 (2026-09-22)

First release of the generated edition in this repository. It replaces the hand-made 0.1.0
fork-and-customize template published here in July and August 2026. Setup is now guided by
`/setup-job-search` instead of `SETUP.md`.

- `scripts/age_out.py` (with tests): the weekly `funnel-review` now runs the Aged Out policy
  pass itself. It bulk-ages stale rows by date and match, and runs a small, batched,
  confirm-first job-description check on old rows that are still well matched.
- `audit.py`: tolerates Gmail search results that carry only metadata, and counts every
  LinkedIn alert email as a digest unless it is proven to be a single-job alert. Both
  previously under-reported coverage.
- ATS notes: always fill Work Experience and Education, even when optional. Treat visa
  sponsorship, work authorization and pre-answered criminal-history questions as a verified
  set, because sponsorship widgets can arrive pre-set to "Yes". On Workday, select dropdown
  options by clicking them, never by typing and pressing Return.
- Screening rules, `apply-assist` and `funnel-review` updated from another two weeks of daily
  use.

## 0.2.0 (2026-09-08)

First generated edition, built from the author's personal plugin after four months of daily
use. Tagged locally, never published on its own; its contents ship as part of 0.2.4.

- Gated discovery (full / light, never off) driven by the size of the fresh queue.
- Transcript-based run audit (`scripts/audit.py`): coverage claims come from what the tools
  returned, never from the model's summary.
- Discovery pipeline in scripts (`discover.py`, `candidates.py`, `screen.py`,
  `dedup_query.py`, `parse_linkedin_digest.py`, `normalize.py`, `notion_rows.py`, `lock.py`,
  `snapshot_build.py`), stdlib only, with tests.
- Saved Notion views for every routine read (quota-exempt); at most three SQL calls per run.
- `apply-prep`: unattended application packets Mon/Wed/Fri with a JD read ladder, PDFs, outreach
  drafts, and a claims-changed-vs-master manifest.
- `setup` skill and `/setup-job-search` command: connectors, Notion database and views,
  profile, queries, scheduled tasks.
- `Aged Out` convention for stale queue rows; outreach-owed and packets-ready reporting.
- Incident log with the reasons behind every rule (names removed).
