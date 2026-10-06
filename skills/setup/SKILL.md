---
name: setup
description: First-run setup for the job-search-agent plugin. Checks connectors and Python, creates the Notion pipeline database and its saved views, writes the ids into data/notion.json, and walks the user through the profile, queries, and scheduled tasks.
---

You are setting up the `job-search-agent` plugin for a new user. Work through the steps in
order, report what you did after each, and stop at any step that needs the user's input. Do
not skip a step silently; a half-configured plugin fails quietly on its first scheduled run.

## 1. Prerequisites

- **Python 3.11+**: run `python --version` (and `/c/Python314/python` style paths on Windows).
  Record the working path in `context/config.md` under Runtime. Run the script tests:
  `python -m unittest discover -s scripts/tests`. All must pass.
- **Connectors** (each is a claude.ai connector or an MCP server the user connects
  themselves): Notion (required), Gmail (required for email reconciliation and LinkedIn
  digests), Google Drive (optional), an Indeed job-search MCP (recommended), the Claude in
  Chrome extension (recommended). Check each with a tool search and list what is missing;
  explain what degrades without it.
- Pin the Indeed tool names in `context/config.md` (search for `search_jobs` and
  `get_job_details`).

## 2. Notion database

Create the "Job Search Pipeline" database with `notion-create-database` using the schema in
`../../context/notion-schema.md` (every field, every select option, both formulas). Then
create the saved views listed there with `notion-create-view` (exact names, filters, sorts).
Copy `data/notion.example.json` to `data/notion.json` (gitignored) and write the database id, data source id, and every view id into it.

Verify: query the ⚙ Ranked queue view in view mode (it returns zero rows and no error), and
run the sweep aggregate SQL once with the data source substituted.

## 3. Profile and rules

Walk the user through `context/candidate-profile.md`: facts, target roles, hard screens,
scoring guardrails, experience-gate thresholds, seniority screen reasoning, location modifier,
salary floor, learning roadmap. Ask whether they want standing application answers (work
authorization, sponsorship, self-ID, pronouns) and the salary-field rule filled in; both are
optional, and anything left blank stays theirs on every form. Then `context/accuracy-rules.md` ("your rules" sections).
Then `data/queries.json` (target titles and locations; recommend they create a daily LinkedIn
job alert per query, delivered by email). Then `data/screens.json` (adjust seniority discard
patterns, contact-center keywords or remove them, comp thresholds).

Ask for the master resume path and the documents folder; record both in `config.md`.

## 4. Scheduled tasks

Create three scheduled tasks with `create_scheduled_task`, using the prompts in
`scheduled-tasks/` verbatim (they are thin wrappers that take a lock and invoke the
skill): `daily-job-sweep` (weekdays 08:00), `apply-prep` (Mon/Wed/Fri 09:00),
`weekly-funnel-review` (Fridays 16:00). Optionally `cert-nudge` (Mondays). Tell the user to
click "Run now" once on each so tool approvals are stored on the task.

## 5. First run

Run `/sweep` once with the user present. Confirm the report ends with the `audit.py` coverage
block reading OK, the null-check count, and a Top 3. Then run `/apply-prep 1` with the user
present and confirm a packet folder, manifest, and the Packet Ready date land.

## 6. Privacy and the automation boundary

Remind the user: everything runs in their own accounts; the agent fills forms and sets up
outreach only from what they recorded, and nothing here sends, submits, or fabricates; `data/notion.json`, the pipeline snapshot, and their profile are personal and
gitignored in this edition. Point them at `context/ats-learnings.md` for the canonical
boundary statement and at `DONATING.md` if the tool helps them.
