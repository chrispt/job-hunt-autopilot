# Environment Bindings & File Conventions (single source of truth)

<!-- TEMPLATE — every value below is a placeholder. Tool identifiers, file paths, and naming
conventions live here and ONLY here; skills reference this file instead of inlining UUIDs or
paths, so this is the only place you need to update when a binding changes. -->

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

## Master resume

- **Path:** `REPLACE-WITH-YOUR-RESUME-PATH` (wherever your resume storage MCP can read it —
  Google Drive, Dropbox, a local path, etc.)
- **File ID hint (if applicable):** `REPLACE-IF-YOUR-CONNECTOR-USES-STABLE-IDS` — if a live
  read by ID fails, match by title instead. When a title match reveals a new ID, update this
  line.

**Live-read recipe:** describe how to fetch the current resume with your connector (e.g.
"search_files with title contains '<your resume filename>', pick the .docx, then
read_file_content"). **Session reuse:** if the master resume was already read earlier in this
session (e.g. a sweep followed by `apply-assist`), reuse the in-context text — do not
re-fetch it.

## Tailored-document naming & save location

| Type | Filename |
|---|---|
| Tailored resume | `<YourName>_Resume_<Company>.docx` |
| Cover letter | `<YourName>_CoverLetter_<Company>.docx` |

Save all output to `REPLACE-WITH-YOUR-SAVE-LOCATION`. Never start a tailored resume from a
previously tailored version — always from the master file (see `accuracy-rules.md`).

## ATS upload staging

Chrome `file_upload` tools only accept session-shared files — stage a copy of the tailored
resume in `REPLACE-WITH-A-LOCAL-STAGING-FOLDER` (e.g. your Downloads folder) and let the
candidate click Attach (see `ats-learnings.md`).
