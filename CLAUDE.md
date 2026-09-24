# job-search-agent (community edition): plugin instructions

Talk to it via the `job-agent` subagent (`agents/job-agent.md`), the front door that routes to
the skills. Logic lives once, in `skills/`; scheduled-task wrappers (`scheduled-tasks/`)
and slash commands only call in.

## Reference context (read by the agent and skills, never duplicated into them)

- `context/candidate-profile.md`: your facts, target roles, screens, guardrails, salary floor.
- `context/config.md`: tool bindings, paths, naming conventions, the JD read ladder.
- `context/accuracy-rules.md`: MANDATORY for any generated document.
- `context/notion-schema.md`: database schema, saved views, conventions; ids in `data/notion.json`.
- `context/ats-learnings.md`: platform patterns and the canonical automation boundary.
- `context/incident-log.md`: the dated reasons behind the rules.

## Scripts

`scripts/` does the mechanical work: `audit.py` (what a run actually did, from the transcript),
`discover.py` (transcript → screened, deduped candidates), `screen.py`, `dedup_query.py`,
`parse_linkedin_digest.py`, `normalize.py`, `notion_rows.py`, `lock.py`, `snapshot_build.py`.
Stdlib only; run `python -m unittest discover -s scripts/tests` after any change. Rules the
scripts apply live in `data/queries.json`, `data/screens.json`, `data/exclusions.md`.

## Skills

`setup` (first run), `daily-sweep`, `apply-prep`, `apply-assist`, `referral-match`,
`funnel-review`, `cert-nudge`.

## Automation boundary (do not weaken this while extending the plugin)

Canonical statement at the bottom of `context/ats-learnings.md`: the agent fills only what the
user's profile and standing answers cover, attaches files and sets up outreach; attestations,
logins, consent agreements, uncovered questions, the final Submit and clicking Send always stay
with the user;
nothing here fabricates a qualification to clear a gate.
