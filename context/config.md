# Environment Bindings & File Conventions (single source of truth)

Tool identifiers, file paths, and naming conventions live here and ONLY here. Skills reference
this file instead of inlining ids or paths. `/setup-job-search` fills in the placeholders.

## Runtime: paths, scripts, run directory

| Binding | Value |
|---|---|
| Python | `<path to python 3.11+>` (Git Bash form too, e.g. `/c/Python314/python`). Always run with `PYTHONIOENCODING=utf-8`; pipeline text carries `❌` and `™` characters that break the default Windows console codec |
| Plugin root at runtime | `${CLAUDE_PLUGIN_ROOT}`; if empty, the installed plugin path under `~/.claude/plugins/cache/<marketplace>/job-search-agent/<version>/` |
| Scripts | `${CLAUDE_PLUGIN_ROOT}/scripts/`: `audit.py`, `discover.py`, `candidates.py`, `screen.py`, `dedup_query.py`, `parse_linkedin_digest.py`, `normalize.py`, `notion_rows.py`, `lock.py`, `snapshot_build.py`; tests in `scripts/tests/` |
| Run files | `${CLAUDE_PLUGIN_ROOT}/runs/<date>/` (ephemeral) |
| Locks | `${CLAUDE_PLUGIN_ROOT}/data/locks/<task>.lock`, 3 h staleness |
| Pipeline snapshot | `data/pipeline-snapshot.json`, refreshed weekly by `funnel-review` |
| Session transcript | `~/.claude/projects/<cwd slug>/$CLAUDE_CODE_SESSION_ID.jsonl`; `audit.py` locates it itself |
| Discovery queries and gate | `data/queries.json` |
| Intake screens | `data/screens.json` + `data/exclusions.md` |
| Notion ids | `data/notion.json` (written by setup) and the view catalogue in `notion-schema.md` |

## Source vs installed copy

The installed copy under the plugin cache is what executes. After editing source: bump the
version in `.claude-plugin/plugin.json` and `marketplace.json`, reinstall, confirm the new
version directory contains `scripts/`. `scripts/audit.py` on the next scheduled run proves
which instructions ran.

## Tool bindings

| Binding | Value | Notes |
|---|---|---|
| Indeed job search | `mcp__<indeed server id>__search_jobs` | Find the id with a tool search for `search_jobs`; pin the full name here so the right server answers |
| Indeed job details | `mcp__<indeed server id>__get_job_details` | Takes the `JOBSEARCH_...` id from a search result, not the short link. First rung of the JD read ladder |
| LinkedIn alert sender | `jobalerts-noreply@linkedin.com` | Also in `data/queries.json` for `audit.py`. Set up LinkedIn job alerts (email, daily) for each of your queries |

Board quirks: Indeed has no posted-date parameter, so `screen.py` post-filters on the
"Posted on" field; neither board pages beyond ~10 results per query.

## Master resume

- **Path**: `<your documents folder>\<Lastname_Firstname>_Resume.docx` (a local copy that syncs
  to cloud storage). Tailoring always starts from this file, never from a previously tailored
  version.
- **Live-read recipe**: if a cloud-drive connector is available, read the master by file id
  (record the id here) for scoring; otherwise read the local file. Reuse within a session.

## Tailored-document naming & save location

| Type | Filename |
|---|---|
| Tailored resume | `<Lastname_Firstname>_Resume.docx` (+ `.pdf`) |
| Cover letter | `<Lastname_Firstname>_CoverLetter.docx` (+ `.pdf`) |

Save to `<your documents folder>\<Company> - <Role>\`. The company name never appears in the
filename: the uploaded file is what the employer receives. A PDF is generated alongside each
`.docx` at build time (some ATSes accept PDF only). The attach step cannot be automated by the
browser tools; you attach from the folder when the file picker opens.

## LinkedIn connections roster

- **Path**: `<your documents folder>\network\Connections.csv`, exported yourself via LinkedIn's
  "Get a copy of your data" (never a scrape). Used by `referral-match`, the standout rule, and
  `apply-prep`.

## JD read ladder (used by apply-prep and apply-assist step 3)

Anonymous fetches of LinkedIn and `to.indeed.com` URLs never return the posting. Read a JD
through the first rung that works and record which one:

1. **Indeed row**: `get_job_details` with the `JOBSEARCH_...` id (the sweep writes it into
   Notes as `Indeed id: ...`).
2. **Employer / ATS URL** via `WebFetch` on the platform's JSON endpoint:
   Greenhouse `https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?content=true`;
   Lever `https://api.lever.co/v0/postings/<company>/<id>`; Ashby
   `https://api.ashbyhq.com/posting-api/job-board/<org>`; Workday
   `https://<tenant>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/job/<path>`. A bare shell
   render is inconclusive, never a closed signal.
3. **LinkedIn URL, or rung 2 inconclusive**: the Claude in Chrome extension (logged in). A page
   reading "No longer accepting applications" is a positive closed signal.
4. **Nothing rendered**: flag "JD unreadable by every path, possibly expired, not withdrawn"
   and move on. Never withdraw a row on an empty render.

## Referral-site policy

If you use a cold-referral marketplace, keep it manual: its terms typically forbid scraping and
unsolicited messaging of referrers. `referral-match` only lists candidates for you to act on.
