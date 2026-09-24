# Changelog

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
