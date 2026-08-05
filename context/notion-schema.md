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
| ATS | select | Greenhouse · Ashby · Workday · LinkedIn · Lever · Direct · (add options as you
  encounter new platforms rather than leaving the field blank — see the note below) |
| Easy Apply | checkbox | — |
| Rejected | checkbox | — |
| Application Confirmed | checkbox | — (set when an ATS sends a "we've received your
  application" email, before any human status update arrives) |
| Date Applied | date | — |
| Follow Up Date | date | — |
| Interview Date | date | — |
| Outreach Sent | date | — |
| Recruiter Name | text | — |
| Recruiter LinkedIn | url | — |
| Resume URL | url | — |
| Cover Letter URL | url | — |

**Keep select-field option lists current.** If an application goes through a platform not yet
in the `ATS` (or `Source`) option list, add the option rather than forcing the nearest wrong
value or leaving the field blank — a blank field silently drops that row out of any
segmentation by that field later. Fetch the data source first to read the current options
before altering the list, since most "set options" API calls replace the whole list rather
than appending to it.

**Status does NOT auto-default on create — verify this against your own connector before
relying on it.** It's a reasonable assumption that a select field with an obvious "first"
option (like `Status = "To Apply"`) gets applied automatically when a new page is created via
the API, the way a UI default would. At least one common Notion connector does **not** do
this: any UI default configured on the database simply does not apply to API-created rows,
so an omitted Status silently writes as null. A null-Status row looks complete in the Notion
UI and is otherwise indistinguishable from a healthy row, but any skill or view that filters
on `Status = "To Apply"` will never surface it again — the roles most in need of surfacing
are exactly the ones silently dropped. **Set Status explicitly, in the same create call as
every other field, on every row, every run** — and confirm empirically (create one test row
without setting it, then check whether it actually came back with your intended default)
before trusting otherwise for your own connector. If it doesn't auto-default, treat "verify
the field you assumed was set actually got set" as a standing practice worth applying to any
other field you're tempted to assume a default for, and consider a periodic check (e.g. a
saved view or a `COUNT(*) WHERE Status IS NULL` query) that a discovery skill runs after every
create batch and reports even when the count is zero — a check that only speaks up on
failure is indistinguishable from a check that never ran.

## SQL-mode query quirks (verified against Notion's API — check these still hold for you)

When using a SQL-mode Notion query tool:
- Date properties are addressed as `"date:<Property>:start"` (e.g. `"date:Date Applied:start"`),
  not the bare property name.
- Created time is the camelCase built-in `createdTime`.
- Result pages cap at ~100 rows — paginate with LIMIT/OFFSET for full-table pulls once your
  pipeline grows past that.
- **`has_more: false` is not necessarily trustworthy as an end-of-table signal** for a raw
  `SELECT ... LIMIT 100 OFFSET 0` pull — test this against your own connector before trusting
  a single page as "the whole table." If a single-page pull ever returns `has_more: false`
  against a table you know is larger, that's a bug in the connector's pagination metadata, and
  trusting it means silently checking only a fraction of your rows (e.g. missing duplicates a
  dedup pass was supposed to catch). If you must do a full-table pull: run `SELECT COUNT(*)`
  first, then fetch `ceil(count/100)` pages by incrementing OFFSET by 100 each time, stopping
  only when you've collected that many rows — never stop early because `has_more` said so.
- **Prefer a targeted pull over a full-table pull** once your pipeline grows past a few
  hundred rows. A `WHERE Company IN ('Name1', 'Name2', ...)` query covering just the
  candidates from one run is cheap regardless of table size and sidesteps the pagination trap
  above entirely. Reserve full-table pulls for cases that genuinely need the whole table (a
  duplicate-density audit, say), not routine dedup.
- SQL-mode query tools sometimes carry their own per-session or per-day query-count cap,
  separate from any plan-level gate — budget queries per run, and prefer the targeted-pull
  pattern above, which also helps here by replacing many paginated calls with one.

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
