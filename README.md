# job-search-agent (template)

A Claude Code plugin that automates the mechanical parts of a job search — board discovery,
Notion pipeline tracking, email status reconciliation, JD-verified application prep, and a
weekly funnel review — while keeping attestation, salary/EEO fields, logins, outreach
sending, and the final Submit button in the candidate's hands.

**This is a fork-and-customize template, not a drop-in tool.** It was built for one person's
job search and generalized afterward; every piece of personal data (name, resume path,
Notion database, target roles, scoring rules) has been pulled into a handful of files you're
expected to edit. Read [`SETUP.md`](SETUP.md) before doing anything else — it walks through
exactly what to fill in and in what order.

## What's inside

| Piece | What it does |
|---|---|
| `agents/job-agent.md` | The conversational front door. Talk to it about the pipeline, what to apply to, or the week's results — it routes to the right skill. |
| `skills/apply-assist/` | Takes a "To Apply" role through JD re-verification, resume/cover-letter tailoring, outreach drafts, and ATS form-fill up to Submit. |
| `skills/daily-sweep/` | Job-board discovery, email reconciliation, and an aging-queue/follow-up/ghosting report. |
| `skills/funnel-review/` | Weekly funnel metrics and a rejection-pattern analysis that proposes concrete scoring/exclusion adjustments. |
| `skills/cert-nudge/` | Example: a weekly check-in on a certification roadmap. Fully personal content — rewrite or delete. |
| `commands/apply.md`, `commands/sweep.md`, `commands/job-status.md` | Slash-command shortcuts into the skills above. |
| `context/` | Shared reference the agent and skills all read from — candidate profile & scoring strategy, environment/tool bindings, accuracy rules, the Notion schema, and ATS form-fill learnings. Single source of truth, so rules never drift between files. **This is where your personalization lives.** |
| `data/exclusions.md` | Companies deliberately passed on after real evaluation — checked before any discovery or apply-assist effort. Starts empty. |

## Required connectors (not bundled — see `.mcp.json`)

This plugin depends on remote MCP connectors it cannot ship, because a plugin's `.mcp.json`
only launches local stdio servers, and these are all OAuth-based:

- **Notion** — the pipeline database (you'll create your own — schema in
  `context/notion-schema.md`)
- **Google Drive** (or wherever your resume lives) — live master-resume reads
- **Gmail** — read-only email reconciliation
- **A job-board search MCP** (Indeed, Dice, or similar) — discovery
- **Chrome MCP** (with Playwright and the Claude Chrome extension as fallbacks) — JD reading
  and ATS form-fill

Connect each via claude.ai connector settings, or `claude mcp` / `/mcp` in an interactive
Claude Code session, before relying on the skills that need them. `job-agent` will tell you
plainly if one is missing rather than guessing.

## Install

```
claude --plugin-dir "/path/to/your/fork/of/job-search-agent"
```

Or register your fork as a personal plugin marketplace and `/plugin install job-search-agent`
from any Claude Code session.

## Scheduled tasks (live outside this plugin)

Claude Code plugins can't bundle scheduled tasks — they live in
`~/.claude/scheduled-tasks/`. Each one is a thin wrapper that just invokes the matching
plugin skill, so the actual logic lives once, here. Set up your own wrappers pointing at
your fork; see `SETUP.md`.

| Suggested task | Suggested schedule | Invokes |
|---|---|---|
| daily-job-sweep | Weekdays morning | `job-search-agent` skill `daily-sweep` |
| weekly-funnel-review | Once a week | `job-search-agent` skill `funnel-review` |
| cert-weekly-nudge (optional) | Once a week | `job-search-agent` skill `cert-nudge` |

## The automation boundary

The canonical statement lives at the bottom of `context/ats-learnings.md`: attestation,
self-ID, salary/EEO fields, logins, sending outreach, and the final Submit always stay with
the candidate. This plugin never crosses that line — keep it that way if you extend it.
