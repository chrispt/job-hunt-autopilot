# job-search-agent — plugin instructions

This plugin is a personal job search agent. It replaces a loose collection of a project
`CLAUDE.md`, one global skill, and scheduled tasks with one versioned, portable unit. See
`README.md` for what's included, required connectors, and — most importantly — `SETUP.md`
for what to fill in before this plugin will work for you.

**Talk to it via the `job-agent` subagent** (`agents/job-agent.md`) — that's the front door
and knows the whole workflow. The logic itself lives in `skills/`, so it's never duplicated
between the subagent, the slash commands, and the scheduled-task wrappers that call in from
`~/.claude/scheduled-tasks/`.

## Reference context (read by the agent and skills, not duplicated into them)

- [`context/candidate-profile.md`](context/candidate-profile.md) — candidate facts, pivot
  targets, scoring guardrails, salary floor. The single source of truth for all of these.
  **Fill this in first — see `SETUP.md`.**
- [`context/config.md`](context/config.md) — tool bindings (job-board MCP identifiers),
  master-resume path/recipe, file naming and staging conventions. **Yours will differ from
  the placeholders — see `SETUP.md`.**
- [`context/accuracy-rules.md`](context/accuracy-rules.md) — resume/cover-letter/outreach
  accuracy rules. MANDATORY for any generated document. The structure (no-lies rule,
  hyperbole blacklist, framing rules) is reusable; the specific rules are examples to replace
  with your own.
- [`context/notion-schema.md`](context/notion-schema.md) — Job Search Pipeline database IDs,
  field schema, and pipeline conventions (queue ranking, rejection marker, follow-up timing).
  The field schema is reusable as a Notion database template; the IDs must be your own.
- [`context/ats-learnings.md`](context/ats-learnings.md) — Greenhouse/Workday form-fill
  patterns and the canonical automation-boundary statement. Mostly reusable as-is; it's
  platform behavior, not personal data.

## Skills

- [`skills/apply-assist/`](skills/apply-assist/SKILL.md) — takes "To Apply" roles through to
  a submitted application. `/apply-assist`.
- [`skills/daily-sweep/`](skills/daily-sweep/SKILL.md) — job-board discovery, email
  reconciliation, and throughput surfacing. Invoked daily by the scheduled-task wrapper, or
  manually via `/sweep`. **The discovery query list is an example — replace it with your own
  pivot targets.**
- [`skills/referral-match/`](skills/referral-match/SKILL.md) — optional: matches your
  professional network against open pipeline roles and drafts warm referral asks; also
  surfaces a cold-referral shortlist for roles with no warm contact. `/referral-match`.
  Delete this skill entirely if you don't have an exportable network roster.
- [`skills/funnel-review/`](skills/funnel-review/SKILL.md) — weekly funnel metrics and
  rejection-pattern analysis. Invoked weekly by the scheduled-task wrapper.

## Data

- [`data/exclusions.md`](data/exclusions.md) — companies deliberately passed on; checked by
  `daily-sweep` and `apply-assist` before spending any effort on a company. Starts empty.
- [`data/connections-README.md`](data/connections-README.md) — optional: documents the
  network-export CSV `referral-match` reads; the roster itself lives in your own storage, not
  committed here. Delete alongside `referral-match` if you don't use it.
- [`data/refer-me.md`](data/refer-me.md) — optional: a worked example of why a cold-referral
  tool should stay manual-only rather than automated, if `referral-match` surfaces one for
  you. Delete alongside `referral-match` if you don't use it.

## Automation boundary (do not weaken this while extending the plugin)

The canonical statement lives at the bottom of `context/ats-learnings.md`: attestation,
self-ID, salary/EEO fields, logins, sending outreach, and the final Submit always stay with
the candidate; nothing here fabricates a qualification to clear a gate.
