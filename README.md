# job-search-agent (community edition)

A Claude Code plugin that runs a job search the way a disciplined assistant would: it finds
roles on a schedule, screens them against rules you wrote down, keeps a Notion pipeline
honest, reconciles your inbox, builds ready-to-submit application packets three times a
week, and audits its own runs from the session transcript so it cannot overstate what it did.
When you apply, it fills the form (files attached), sets up the LinkedIn outreach, and reads
the review back to you. You do the last mile: login, attestations, Submit, and Send.

It was built for one job seeker's search over four months and then generalized. Every rule
in it exists because something went wrong once; `context/incident-log.md` keeps the stories
(names removed) so you can judge whether a rule applies to you.

**Free to use, pay what you want. If it helps you land something, see `DONATING.md`.**

Built by Chris Pohlad-Thomas (https://github.com/chrispt) during his own search. Source and issues:
https://github.com/chrispt/job-hunt-autopilot

## What you need

- Claude Code (desktop app or CLI) with scheduled tasks
- Python 3.11 or newer (no third-party packages)
- Connectors you connect yourself: Notion (required), Gmail (required for status updates and
  LinkedIn alert digests), an Indeed job-search MCP (recommended), Google Drive (optional),
  the Claude in Chrome extension (recommended for LinkedIn postings and ATS forms)
- A Notion workspace (free plan works; the plugin routes routine reads through saved views,
  which are not quota-limited)

## Install

1. Clone this repo somewhere permanent.
2. Register it as a plugin marketplace and install, either from GitHub:
   `/plugin marketplace add chrispt/job-hunt-autopilot`, or from the clone:
   `/plugin marketplace add <path to your clone>`; then
   `/plugin install job-search-agent@job-hunt-autopilot`.
3. Run `/setup-job-search`. It checks connectors and Python, creates the Notion database and
   its saved views, writes the ids into `data/notion.json`, and walks you through your
   profile (`context/candidate-profile.md`), accuracy rules, search queries
   (`data/queries.json`), screens (`data/screens.json`), and the three scheduled tasks.
4. Run `/sweep` once with you watching, then `/apply-prep 1`.

## How a day runs

1. **Weekday mornings, `daily-sweep`.** Takes a lock, refreshes two date-windowed views,
   reads the queue and applied views, and decides a discovery gate from one SQL aggregate:
   under the threshold of fresh above-floor roles → full mode (every query × location plus
   every LinkedIn alert digest); over it → light mode (digests plus a few core Remote
   searches). `scripts/discover.py` turns the session transcript into screened, deduped
   candidates; the model scores and creates rows; `scripts/audit.py` prints a coverage block
   derived from the transcript. Then email reconciliation, then the report: packets ready,
   standouts, Top 3, outreach owed with drafts, follow-ups due.
2. **Mon/Wed/Fri, `apply-prep`.** Reads the ranked queue, prefers standouts (high score or a
   company where you know someone), reads the JD through a ladder that works unattended,
   re-scores, gates, tailors your resume and cover letter from your master file, makes PDFs,
   drafts outreach, writes a manifest with a "claims changed vs master" section, and sets
   `Packet Ready`.
3. **You and the agent, `/apply <Company>`:** it fills the application from your profile and
   standing answers, attaches the packet's PDFs, and stops at Submit for your check; after you
   submit, it opens one LinkedIn tab per contact with the note typed in, and you click Send.
4. **Fridays, `funnel-review`.** Funnel metrics, packets built vs submitted, a coverage audit
   of the week's sweeps, rejection patterns, a standing-queue re-screen when a rule changed,
   and the pipeline snapshot refresh.

## What is in the box

| Piece | What it does |
|---|---|
| `skills/` | `daily-sweep`, `apply-prep`, `apply-assist`, `referral-match`, `funnel-review`, `cert-nudge`, `setup` |
| `commands/` | `/sweep`, `/apply`, `/apply-prep`, `/job-status`, `/referral-match`, `/setup-job-search` |
| `agents/job-agent.md` | The conversational front door |
| `scripts/` | Transcript audit, discovery pipeline, digest parser, intake screen, dedup, row compaction, lock, snapshot merge; tests in `scripts/tests` |
| `context/` | Your profile and rules (templates), Notion schema and views, ATS learnings, the incident log |
| `data/` | Queries and gate, screen rules, exclusions, Notion ids (gitignored) |
| `scheduled-tasks/` | The three wrapper prompts the setup skill installs |

## Principles this tool holds

- **Nothing submits, sends, or fabricates.** The automation boundary is in
  `context/ats-learnings.md`. The agent fills only what your profile and standing answers
  cover; attestations, logins, uncovered questions, Submit and Send are yours.
- **Coverage claims come from the transcript,** never from the model's own summary.
- **Rules live in data files** (`queries.json`, `screens.json`, `exclusions.md`), not in prose.
- **The daily output is something you can act on in ten minutes,** not a longer list.
- **Only TOS-clean sources:** job-board MCPs and your own LinkedIn alert emails and
  connections export. No scrapers.

## Privacy

Everything runs inside your own accounts and machine. `data/notion.json`, the pipeline
snapshot, run files, and locks are gitignored. Your profile and rules are files you own;
do not publish a fork without scrubbing them.

## License

MIT. See `LICENSE`. Donations welcome, never required: `DONATING.md`. Release notes in
`CHANGELOG.md`; the product page text is `docs/LISTING.md`.
