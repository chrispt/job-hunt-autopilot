# job-search-agent: a self-auditing job search for Claude Code

**Pay what you want. Free is a valid price.**

You do not need more job postings. You need the ones you already found turned into finished
applications, on a schedule, without the tool quietly skipping steps and telling you it did
everything. That is what this plugin does.

## What it does

- **Finds roles on weekday mornings** from Indeed and your own LinkedIn alert emails, screens
  them against rules you wrote down (titles to skip, salary floor, deal-breaker domains),
  dedups them, and files them in a Notion pipeline it keeps honest.
- **Gates discovery on your queue.** When you already have more fresh roles than you can apply
  to, it searches less and prepares more. It never stops reading your alerts, so a great
  posting still surfaces.
- **Builds application packets three mornings a week:** reads the real job description,
  re-scores the fit, tailors your resume and cover letter from your master file, makes PDFs,
  drafts three outreach messages, and writes a manifest that lists exactly which claims
  changed so you review a diff, not a document.
- **Reconciles your inbox** (rejections, interviews, confirmations) into the pipeline and
  tells you what follow-up is due, with the one-line nudge already drafted.
- **Audits itself from the session transcript.** Every run ends with a coverage block derived
  from what the tools actually returned, not from the model's summary. A skipped search or an
  unopened digest shows up as such.
- **Reviews the week on Fridays:** applications out, packets built vs submitted, rejection
  patterns, and one concrete adjustment for next week.

You do the last mile every time: login, attach, attestation, Submit, and any message that
goes to a human. Nothing here sends or submits on your behalf.

## What you get

A Claude Code plugin (skills, commands, an agent, nine Python scripts with tests), a setup
skill that creates the Notion database and views for you, templates for your profile and
rules, wrapper prompts for the scheduled tasks, and an incident log that explains why every
rule exists.

## What you need

Claude Code (desktop app or CLI) with scheduled tasks; Python 3.11+; a Notion workspace
(free plan is fine); Gmail; an Indeed job-search connector; optionally Google Drive and the
Claude in Chrome extension. Windows, macOS and Linux; the PDF step uses Word on Windows and
degrades to .docx elsewhere.

## Install

1. `/plugin marketplace add chrispt/job-hunt-autopilot`
2. `/plugin install job-search-agent@job-hunt-autopilot`
3. `/setup-job-search`

## Honest limits

It is opinionated: it assumes a Notion pipeline, a master resume you keep truthful, and that
you will do a ten-minute last mile per application. It is not a mass-apply bot and will not
become one. ATS platforms change; the ATS notes cover Greenhouse, Workday, Oracle HCM, iCIMS
and Lever as of September 2026.

## Support and donations

No support contract; issues and pull requests on GitHub are welcome. If it helps, see
`DONATING.md`. Licence: MIT.

Built by Chris Pohlad-Thomas during his own search, after being laid off in July 2026.
