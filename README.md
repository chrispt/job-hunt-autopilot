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

- **A Claude account that can run Claude Code:** a paid Claude subscription or an
  Anthropic Console account. The desktop app requires the subscription. Anthropic's
  [Claude Code overview](https://code.claude.com/docs/en/overview) lists which plans include
  Claude Code today.
- **Claude Code**, in either form:
  - the **Claude desktop app** (macOS and Windows, Linux in beta). Claude Code is built in:
    sign in and open the **Code** tab. Download from the overview page above.
  - the **terminal CLI**. macOS, Linux and WSL: `curl -fsSL https://claude.ai/install.sh | bash`.
    Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`.
- **The desktop app, if you want the weekday schedule to run by itself.** The three scheduled
  tasks are local desktop tasks: they run on your computer and only fire while the app is open
  and the computer is awake (turn on **Keep computer awake** in Settings if you want 8 AM
  runs). A run missed while the computer slept is made up once, when the app opens or the
  computer wakes. With the terminal CLI alone everything still works, but you start `/sweep`
  and `/apply-prep` yourself.
- **Python 3.11 or newer** (no third-party packages).
- **Connectors you connect yourself:** Notion (required), Gmail (required for status updates
  and LinkedIn alert digests), an Indeed job-search connector (recommended), Google Drive
  (optional), the Claude in Chrome extension (recommended for LinkedIn postings and ATS forms).
  In the desktop app, use **+ > Connectors** next to the prompt box in the Code tab. For
  terminal setups see Anthropic's [MCP guide](https://code.claude.com/docs/en/mcp).
- **A Notion workspace** (free plan works; the plugin routes routine reads through saved views,
  which are not quota-limited).

## Install

1. Install Claude Code (above) and sign in.
2. Add this repository as a plugin marketplace and install the plugin. Use whichever fits how
   you run Claude Code. The terminal, the desktop app's local sessions and the VS Code
   extension read the same user settings, so installing one way makes it available in all.
   - **Terminal:**
     ```
     claude plugin marketplace add chrispt/job-hunt-autopilot
     claude plugin install job-search-agent@job-hunt-autopilot
     ```
   - **Inside a Claude Code session:** one command adds the marketplace and starts the install
     (needs Claude Code 2.1.275 or later). Choose **Install for you (user scope)**:
     ```
     /plugin install job-search-agent --marketplace chrispt/job-hunt-autopilot
     ```
   - **Desktop app:** add the marketplace once (run the first terminal command, or ask Claude in
     a Code session to run it for you), then click **+ > Plugins > Add plugin** next to the
     prompt box, pick `job-search-agent`, and choose your user account as the scope. If you
     have no terminal CLI, ask Claude in a Code session to run the two terminal commands above.
   - **From a clone** (to read or change the code): `claude plugin marketplace add <path to
     your clone>`, then the same install command.
3. Restart Claude Code, or run `/reload-plugins`. Check that it loaded: `claude plugin list`
   shows `job-search-agent@job-hunt-autopilot`, and typing `/` lists its skills.
4. Connect the connectors above.
5. Run `/setup-job-search` (it may be listed as `/job-search-agent:setup-job-search`). It
   checks connectors and Python, creates the Notion database and its saved views, writes the
   ids into `data/notion.json`, and walks you through your profile
   (`context/candidate-profile.md`), accuracy rules, search queries (`data/queries.json`),
   screens (`data/screens.json`), and the three scheduled tasks.
6. Run `/sweep` once with you watching, then `/apply-prep 1`.

If `claude` is not found after installing the CLI, open a new terminal window. If the
marketplace will not clone, try the full URL, `https://github.com/chrispt/job-hunt-autopilot.git`.
If the plugin does not appear, run `/reload-plugins` and check the **Errors** tab in `/plugin`.

## Where your settings live, and updating

Your profile, Notion ids, queries, screens and config are saved automatically in Claude Code's
persistent data folder for this plugin, which survives updates:
`~/.claude/plugins/data/job-search-agent-job-hunt-autopilot/` (on Windows,
`C:\Users\<you>\.claude\plugins\data\...`). Two small hooks do it: at session start your
saved files are restored into the plugin folder, and when a turn ends anything you changed is
saved. The saved files are `context/candidate-profile.md`, `context/accuracy-rules.md`,
`context/config.md`, `data/notion.json`, `data/queries.json`, `data/screens.json`,
`data/exclusions.md` and the pipeline snapshot. Uninstalling the plugin removes that folder
unless you pass `--keep-data`.

To update:

```
claude plugin marketplace update job-hunt-autopilot
claude plugin update job-search-agent@job-hunt-autopilot
```

Restart Claude Code. Your saved files are restored into the new version folder. If a release
changed a data file you have customized (for example `data/screens.json` in 0.2.7), the first
session after the update tells you; your copy stays in use, so read `CHANGELOG.md` and merge the
new defaults by hand if they matter to you. Marketplaces added from GitHub do not auto-update by
default, so nothing changes until you run the update. The scheduled tasks live outside the
plugin folder, in `~/.claude/scheduled-tasks/`, and survive updates.

**Coming from 0.2.x:** your setup is in the old version folder, not the data folder. After
updating, your first session prints the exact command; or run it yourself, with the old folder
under `~/.claude/plugins/cache/job-hunt-autopilot/job-search-agent/`:

```
python <plugin folder>/scripts/userdata.py import <old version folder>
```

To check what is saved at any time: `python <plugin folder>/scripts/userdata.py status`. The
hooks need `python`, `python3` or `py` on your PATH; if saving is not happening, `status` says
the folder is not restored, and running `userdata.py apply` once by hand fixes it.

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
