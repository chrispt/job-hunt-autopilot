# Notion Job Tracker Schema

<!-- TEMPLATE — the Page ID / Data source ID below are placeholders. Create your own Notion
database with the field schema below (a straight copy works fine as a starting point), then
replace the IDs here with yours. Every skill in this plugin reads this file for the IDs
rather than hardcoding them, so this is the only place you need to update. -->

Every skill in this plugin that reads or writes the pipeline uses these exact IDs and field
names.

**Database:** Job Search Pipeline
- Page ID: `REPLACE-WITH-YOUR-NOTION-PAGE-ID`
- Data source (collection) ID: `REPLACE-WITH-YOUR-NOTION-DATA-SOURCE-ID`
- URL: `REPLACE-WITH-YOUR-NOTION-DATABASE-URL`

**How to find these:** open your database in Notion, copy the page URL — the 32-character
hex string in it is the Page ID (Notion displays it with dashes inserted, e.g.
`a1b2c3d4-5e6f-7890-abcd-ef1234567890`). The data source ID is returned by your Notion MCP's
search/query tools the first time you query the database; grab it from that response and
paste it here.

## Field schema

| Field | Type | Options |
|---|---|---|
| Company | title | — |
| Role | text | — |
| Job URL | url | — |
| Salary Range | text | — |
| Notes | text | — |
| Status | select | To Apply · Applied · Interviewing · Offer · Rejected · Withdrawn · Ghosted |
| Source | select | LinkedIn · Indeed · Dice · Wellfound · Builtin · Referral · Direct · Himalayas · We Work Remotely · FlexJobs (edit to match the boards you actually use) |
| Priority | select | 🥇 High · 🥈 Medium · 🥉 Low (rename tiers to fit your own targeting) |
| Track | select | your own role-family buckets, e.g. one select option per pivot target in `candidate-profile.md` |
| Match % | number | — |
| ATS | select | — |
| Easy Apply | checkbox | — |
| Rejected | checkbox | — |
| Date Applied | date | — |
| Follow Up Date | date | — |
| Interview Date | date | — |
| Outreach Sent | date | — |
| Recruiter Name | text | — |
| Recruiter LinkedIn | url | — |
| Resume URL | url | — |
| Cover Letter URL | url | — |

New entries auto-set to Status = "To Apply".

## SQL-mode query quirks (verified against Notion's API — check these still hold for you)

When using a SQL-mode Notion query tool:
- Date properties are addressed as `"date:<Property>:start"` (e.g. `"date:Date Applied:start"`),
  not the bare property name.
- Created time is the camelCase built-in `createdTime`.
- Result pages cap at ~100 rows — paginate with LIMIT/OFFSET for full-table pulls once your
  pipeline grows past that.
- For dedup sweeps, one paginated full-table pull of Company/Role/Status is usually cheaper
  than per-company search calls; either is acceptable.

## Queue ranking convention

Wherever the "To Apply" queue is listed (`daily-sweep` Part 3, `/job-status`): sort by
**Match % descending**, break ties by more-recently-added first (Notion `created time`),
exclude expiry-flagged roles from the ranked list (surface those separately), and lead with
a **"Top 3 to apply today"** callout.

## Follow-up & ghosting convention

When an application is submitted (via `apply-assist` or manually), set **Follow Up Date =
Date Applied + 5 business days** (adjust the interval to your preference). The `daily-sweep`
skill's throughput step surfaces roles whose Follow Up Date has arrived and drafts a one-line
nudge — it does not send anything on its own. Roles sitting at Status = "Applied" for more
than 21 days with no reply (adjust to your preference) are surfaced as likely-ghosted for you
to confirm before flipping Status to "Ghosted" — never set that status automatically.

## Exclusion list (deliberate company passes)

`data/exclusions.md` (in this plugin) tracks companies deliberately passed on after real
evaluation (domain mismatch, comp floor, etc.), distinct from a plain application rejection.
`daily-sweep` and `apply-assist` both check it before spending any effort on a company; add a
row (with reason and revisit condition) whenever a "pass on this company entirely" decision
is made.

## Rejection marker rule (MANDATORY)

When setting Status = "Rejected", **in the same API call** also: (1) check the **Rejected**
checkbox = true, and (2) update the Company title to `❌ Company Name` (e.g., "Acme Corp" →
"❌ Acme Corp"). The checkbox is the sortable/filterable signal; the ❌ prefix is the visual
cue — both are kept in sync.
- If the title already starts with `❌ `, skip the title change but still ensure the checkbox
  is set (idempotent either way).
- **Do NOT use** `~~strikethrough~~` — that stores literal tilde characters; it doesn't render
  as strikethrough in Notion.
- This applies in manual sessions AND in automated `daily-sweep` runs.

## No delete tool

Most Notion MCP connectors don't expose a delete tool. Removing a stale/expired posting is
always Status → "Withdrawn" plus a dated Notes annotation, never a true delete — if your
connector does support delete, you can loosen this, but it isn't the default assumption here.
