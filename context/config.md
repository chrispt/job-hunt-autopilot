# Environment Bindings & File Conventions (single source of truth)

<!-- TEMPLATE — every value below is a placeholder. Tool identifiers, file paths, and naming
conventions live here and ONLY here; skills reference this file instead of inlining UUIDs or
paths, so this is the only place you need to update when a binding changes. -->

## Edit the source repo, never an installed plugin cache

If you install this plugin from a marketplace rather than running it straight out of your
fork, Claude Code keeps an installed copy separate from your git-tracked source (typically
under `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`). **Always edit the
source.** The cache is disposable and is exactly what a reinstall or version bump overwrites.

The two can drift in *both* directions if you ever edit the cache directly (e.g. quick-fixing
something mid-session) — a rule written straight into the cache never makes it back to
source, while source gains changes the cache never picked up. **If the two have diverged,
diff per file and reconcile by hand before copying anything in either direction.** Never
bulk-copy one tree over the other; a blanket copy in either direction silently destroys
whichever side you didn't check first. A session reading a stale cache follows superseded
instructions with full confidence and no error, which is a hard failure mode to notice after
the fact.

## Tool bindings

| Binding | Value | If it rotates / to disambiguate |
|---|---|---|
| Primary job-board search | `REPLACE-WITH-YOUR-MCP-TOOL-BINDING` (e.g. `mcp__<server-id>__search_jobs`) | Note what else that server exposes (get_job_details, etc.) |
| Secondary job-board search (optional) | `REPLACE-WITH-YOUR-MCP-TOOL-BINDING` | Note any quirks (posted-date support, location string format) |
| LinkedIn alert sender (if using email-alert discovery) | `jobalerts-noreply@linkedin.com` | Verify this against a real alert email in your own inbox before relying on it |

If you connect more than one job-board MCP that exposes a same-named tool (e.g. both call it
`search_jobs`), always call the fully-qualified binding above so the right server answers.
Document any board-specific quirks you discover here (missing filters, pagination limits,
location-string format) so `daily-sweep` doesn't rediscover them every run.

**If a discovery source becomes unavailable or its ROI drops** (a connector stops resolving,
or one source is producing volume you can't realistically act on), this is the place to
record the decision and the reasoning — who decided, why, and what would justify
reconnecting it. That record is what stops a future run (or a future you) from
re-litigating "is this actually broken?" every time the source is noticeably absent, and
from quietly reporting a deliberate skip as if it were a fault.

Board quirks worth writing down here as you discover them: missing posted-date filters,
non-standard location strings for "remote," pagination caps below what you'd expect. Small
things, but they cost real effort to rediscover if they aren't recorded once.

## Master resume

- **Path:** `REPLACE-WITH-YOUR-RESUME-PATH` (wherever your resume storage MCP can read it —
  Google Drive, Dropbox, a local path, etc.)
- **File ID hint (if applicable):** `REPLACE-IF-YOUR-CONNECTOR-USES-STABLE-IDS` — if a live
  read by ID fails, match by title instead. When a title match reveals a new ID, update this
  line.

**Live-read recipe:** describe how to fetch the current resume with your connector (e.g.
"search_files with title contains '<your resume filename>', pick the .docx, then
read_file_content"). If your storage keeps per-company tailored copies alongside the master
in the same parent folder, a plain title search can return a tailored copy instead of the
master once filenames match — confirm the parent folder is your base resume folder, not a
per-company subfolder, before trusting a title-search hit as the master.

**Session reuse:** if the master resume was already read earlier in this session (e.g. a
sweep followed by `apply-assist`), reuse the in-context text — do not re-fetch it.

## Tailored-document naming & save location

| Type | Filename |
|---|---|
| Tailored resume | `<YourName>_Resume.docx` |
| Cover letter | `<YourName>_CoverLetter.docx` |

Save all output to `REPLACE-WITH-YOUR-SAVE-LOCATION/<Company> - <Role>/` (create the folder
if it doesn't exist), and **never put the company name in the filename itself** — the
uploaded file is what the employer receives, and a company-suffixed filename
(`..._Resume_Acme.pdf`) hands them a document named after them. Company goes in the folder
path, not the filename.

**Key the folder on company AND role, not company alone.** If a company can have more than
one open role in your pipeline at once (common once you're casting a wide net), a
folder keyed on company alone silently overwrites the previous tailored set the moment a
second role for that company shows up — and the Notion Resume URL / Cover Letter URL fields
recorded for the first role now point at a file that no longer holds what it held when it
was recorded. Company + role keeps every tailored set independently addressable.

Never start a tailored resume from a previously tailored version — always from the master
file (see `accuracy-rules.md`).

**Generate a PDF alongside each `.docx`**, in the same folder, at document-build time if your
document-generation tooling supports it. Several ATSes accept PDF only, and converting mid-
application with the form already open is avoidable friction.

## ATS upload — no staging copy needed

Chrome-style `file_upload` tools generally only accept files the user has explicitly shared
with that session — not arbitrary paths, and not necessarily a "staging" folder either,
depending on your browser tool's session-sharing model. If you find yourself tempted to copy
the tailored resume to a separate staging location on the theory that it'll make the upload
tool happy: test that theory once before building automation around it. It may not hold, in
which case the only working path is handing the candidate the real file location (or
delivering it directly via a file-send tool, if your environment has one) and letting them
click Attach themselves. See `ats-learnings.md` for the platform-specific patterns.

## Market-corroboration fallback (optional)

If a posting's Job URL goes dead or lists no compensation, some job-aggregator sites (e.g.
hiring.cafe, or whatever equivalent you use) can be fetched as a best-effort corroboration
source — but only via whatever URL paths their `robots.txt` actually allows, never through a
scraping workaround or an undocumented API endpoint. Check the target site's own robots.txt
and terms before wiring this in, log anything sourced this way as third-party-reported (not
read from the employer's own posting), and treat a miss as normal rather than an error — it's
not a queryable index of every role.

## LinkedIn connections roster (optional, for `referral-match`)

- **Path:** `REPLACE-WITH-YOUR-CONNECTIONS-CSV-PATH` (see `../data/connections-README.md` for
  export steps).
- Used only by `skills/referral-match` to join your network against the pipeline on Company.
  If the file is missing, that skill should stop and explain how to export it rather than
  guessing.

## refer.me account state (optional, for `referral-match`)

See `../data/refer-me.md` for why this stays manual-only and is never automated, if you use
it.

- **Tier:** record your actual tier and its request cap/rollover terms here (e.g. Basic free
  tier vs. a paid tier with a higher monthly cap).
- `skills/referral-match` reads this tier to cap the size of the cold-referral shortlist it
  proposes each run. Keep it current if your tier changes.
- No account credentials or API access should exist for this site, and none should be created
  by any skill — every action there is something you do yourself in your own browser.
