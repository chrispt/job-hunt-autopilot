# Setup

This plugin was built for one person's job search and generalized into a template
afterward — it will not do anything useful until you fill in your own details. This is a
fork-and-customize project, not an install-and-go tool: budget an evening, not five minutes.

You'll need [Claude Code](https://claude.com/claude-code) and a comfortable working knowledge
of it (running it, connecting MCP servers, editing plugin files) — this isn't aimed at
first-time users.

## 0. Fork it

Copy this whole folder somewhere you control (or fork the repo, if it's on GitHub). Don't
edit in place inside someone else's copy — this is meant to become *your* fork with *your*
data in it.

## 1. Connect the required MCP servers

Every skill in this plugin depends on external connectors it can't bundle (see `.mcp.json`
and the README for why). Connect these before anything else — via claude.ai connector
settings, or `claude mcp` / `/mcp` in an interactive Claude Code session:

1. **Notion** — you'll point this at your own database (step 2 below).
2. **Wherever your résumé lives** — Google Drive is what the original author used; any MCP
   that can read a live file works (Dropbox, a local filesystem MCP, etc.).
3. **Email** (Gmail or similar) — read-only, used for status reconciliation. The plugin never
   sends, replies, or deletes.
4. **At least one job-board search MCP** — Indeed and Dice are what's referenced by name in
   this template; use whatever you can actually connect. Check the MCP registry
   (`mcp-registry` tools, if you have them) or search for one.
5. **Chrome MCP** (with Playwright and the Claude Chrome extension as fallbacks) — for reading
   job descriptions and filling ATS forms.

Test each connector works with a trivial call before moving on — debugging a broken
connector *and* a half-filled template at the same time is a bad time.

## 2. Create your Notion database

Create a new Notion database (or duplicate one if you have a template link) with the field
schema in `context/notion-schema.md`. Match the field names and types exactly — every skill
references them by exact name.

Once created:
1. Open the database, copy its URL.
2. Query it once with your Notion MCP's search or list tool to get the data source
   (collection) ID from the response.
3. Paste both IDs (and the URL) into `context/notion-schema.md`, replacing the placeholders.

Adjust the `Priority`, `Track`, and `Source` select options to match your own targeting and
the boards you actually use — the placeholders are examples, not requirements.

## 3. Fill in `context/candidate-profile.md`

This is the single most important file. Write your real facts (roles, dates, education,
certs — matching your actual resume) and your real strategy (pivot targets, scoring
guardrails, salary floor, location rules). Every skill reads this file rather than
hardcoding any of it, so getting this right once means you never have to repeat yourself in
a prompt again.

## 4. Fill in `context/config.md`

Replace every placeholder with your real values:
- Your job-board MCP tool bindings (the fully-qualified `mcp__<server>__<tool>` names — ask
  Claude Code to list your connected tools if you're not sure of the exact binding).
- Your résumé's real path and how to fetch it live.
- Your preferred tailored-document naming and save location.
- Your local staging folder for ATS file uploads.

## 5. Fill in `context/accuracy-rules.md`

This file exists to stop an AI-tailoring pass from quietly overclaiming something you
couldn't defend in an interview. Walk through your own resume and write down:
- Any role where your actual scope is easy to overstate (e.g. you drove strategy but didn't
  own a roadmap).
- Phrases you don't want a tailoring pass to reach for (a "hyperbole blacklist").
- Any domain where your knowledge is adjacent, not practitioner-level.
- Any job title or company-name quirk that shouldn't get "cleaned up" by an AI pass.

The example content in the template shows the shape; replace the substance.

## 6. Decide what to do with `skills/cert-nudge/`

This skill is a worked example of one person's specific certification roadmap. If you have
your own certification or skill-building plan that supports your pivot, rewrite the sequence
in `skills/cert-nudge/SKILL.md`. If not, delete the skill folder, remove its scheduled-task
wrapper (step 8), and remove the two references to it in `agents/job-agent.md` and
`CLAUDE.md`.

## 7. Review `skills/daily-sweep/SKILL.md`'s Part 1

Replace the example search-query list and the two example locations with your own pivot
targets and geography from `candidate-profile.md`.

## 8. Install the plugin

```
claude --plugin-dir "/path/to/your/fork"
```

Or register your fork as a personal plugin marketplace (edit
`.claude-plugin/marketplace.json` — it's already set up as an example) and
`/plugin install job-search-agent` from any session.

## 9. Set up scheduled tasks (optional)

Scheduled tasks live outside the plugin, in `~/.claude/scheduled-tasks/`, because plugins
can't bundle them. Create thin wrapper tasks that invoke the plugin skills — see the
Scheduled Tasks section of the README for the suggested schedule. Each wrapper just needs to
tell Claude Code to run `/sweep`, `/apply-assist`, etc. against your plugin install.

## 10. Take it for a test drive

Before trusting it with real applications:
1. Run `/sweep` manually and check the roles it finds and how it scores them make sense.
2. Run `/apply-assist` on one low-stakes role and watch it stop at the automation boundary
   (it should hand you the Submit button, not click it).
3. Read the tailored resume it produces against `accuracy-rules.md` yourself — the first few
   times, verify it isn't overclaiming anything before you trust the gate to catch it alone.

## What NOT to expect

This template gets you the mechanics (tracking, discovery, drafting, form-fill). It does not
know your industry's norms, your specific negotiating position, or whether a role is
actually a good idea for you — that judgment stays yours. The automation boundary in
`context/ats-learnings.md` is deliberate, not a limitation to work around.
