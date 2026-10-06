# Notion Job Tracker Schema

`/setup-job-search` creates this database and its views for you and writes the ids into
`data/notion.json`. Every skill reads ids from there; this file is the human-readable
catalogue.

## Field schema

| Field | Type | Options / notes |
|---|---|---|
| Company | title | `❌ ` prefix marks a rejected company (see marker rule) |
| Role | text | exact job title |
| Job URL | url | |
| Salary Range | text | |
| Notes | text | append-only convention; `JD screen:` line written by apply-assist; `Indeed id:` line by the sweep |
| Status | select | To Apply · Applied · Interviewing · Offer · Rejected · Withdrawn · Ghosted · Aged Out |
| Source | select | LinkedIn · Indeed · Referral · Direct · Other |
| Priority | select | 🥇 Core target · 🥈 Adjacent · 🥉 General (option order = sort order; rename to your tracks) |
| Track | select | your target tracks, e.g. AI PM · Technical PM · CS Leader · Enablement |
| Match % | number | |
| ATS | select | Greenhouse · Ashby · Workday · Lever · iCIMS · Direct · Other (add as you meet them) |
| Easy Apply / Rejected / Application Confirmed / Cover Letter | checkbox | |
| Date Applied / Follow Up Date / Interview Date / Outreach Sent / Packet Ready | date | |
| Created | created time | auto; the age source for every view and script |
| Days Old | formula | `dateBetween(now(), prop("Created"), "days")`; UI only |
| Days Since Applied | formula | `dateBetween(now(), prop("Date Applied"), "days")` |
| Recruiter Name / Recruiter LinkedIn / Resume URL / Cover Letter URL | text / url | |

**Status must be set explicitly on every create.** The connector's create path applies no UI
default. The sweep verifies with the null-check view after every create batch and
`scripts/audit.py` flags any create payload without Status.

**Adding a select option:** do it in the Notion UI. `ALTER COLUMN ... SET SELECT(...)` replaces
the whole option list.

## Saved views (quota-exempt reads)

View-mode queries cost no `Query Data Source` quota; SQL and rows mode share a cap that runs
out mid-run on free and Plus plans. Every routine read goes through one of these views.
Results carry every property and spill to a file; pipe that file through
`scripts/notion_rows.py`.

| View | Key in `data/notion.json` | Filter / sort |
|---|---|---|
| ⚠ Status integrity | `status_integrity` | Status is empty |
| ⚙ Fresh queue | `fresh_queue` | To Apply, Match ≥ 55, Created ≥ today−14 (date refreshed by the sweep each run), Packet Ready empty; Priority asc, Created asc |
| ⚙ Ranked queue | `ranked_queue` | To Apply, Match ≥ 55, Packet Ready empty; Priority asc, Created asc |
| ⚙ Applied open | `applied_open` | Status = Applied; Date Applied asc |
| ⚙ Outreach owed | `outreach_owed` | Applied or Interviewing, Outreach Sent empty |
| ⚙ Packets ready | `packets_ready` | To Apply, Packet Ready not empty |
| ⚙ Added last 7 days | `added_last_7_days` | Created ≥ today−7 (date refreshed each run) |
| ⚙ Age-out candidates | `age_out_candidates` | To Apply, Packet Ready empty, (Created ≤ today−60 OR (Created ≤ today−45 AND Match < 70)) |
| ⚙ Snapshot slice | `snapshot_slice` | Created within a date window (rewritten per slice) |

The view DSL has no relative dates, so the windowed views carry an absolute date the sweep
rewrites at Step 0 with `notion-update-view`.

## The sweep aggregate (one SQL call per run)

Substitute the data source from `data/notion.json`:

```sql
SELECT
  SUM(CASE WHEN Status='To Apply' AND "Match %">=55 AND date(createdTime)>=date('now','-14 days') AND "date:Packet Ready:start" IS NULL THEN 1 ELSE 0 END) AS fresh_queue,
  SUM(CASE WHEN Status IS NULL THEN 1 ELSE 0 END) AS null_status,
  SUM(CASE WHEN Status='To Apply' AND "Match %">=70 THEN 1 ELSE 0 END) AS band_70,
  SUM(CASE WHEN Status='To Apply' AND "Match %">=55 AND "Match %"<70 THEN 1 ELSE 0 END) AS band_55,
  SUM(CASE WHEN Status='To Apply' AND ("Match %"<55 OR "Match %" IS NULL) THEN 1 ELSE 0 END) AS band_below,
  SUM(CASE WHEN Status='Applied' THEN 1 ELSE 0 END) AS applied,
  SUM(CASE WHEN "date:Packet Ready:start" IS NOT NULL AND Status='To Apply' THEN 1 ELSE 0 END) AS packets_ready
FROM "collection://<data_source_id>"
```

## SQL-mode quirks

Date properties are `"date:<Property>:start"`; created time is `createdTime`. Result pages cap
at ~100 rows and `has_more: false` on page 1 is not an end-of-table signal. Never dedup with a
full-table pull; use `scripts/dedup_query.py` plus the one confirmation `IN (...)` query it
prints. Formula properties are not queryable in SQL and come back as references in view mode;
compute age from `Created`.

## Conventions

- **Queue ranking**: read the ⚙ Ranked queue view (floor-gated, Priority then oldest). Match %
  is a floor, not a ranking signal. Packets-ready rows are listed first; standouts jump the
  order for `apply-prep`.
- **Follow-up & ghosting**: on submission set Follow Up Date = Date Applied + 5 business days.
  The sweep drafts a nudge when it arrives and sends nothing. Applied 21+ days with no reply is
  proposed as Ghosted, never set automatically.
- **Age-out**: `Aged Out` marks a To Apply row never applied to and too old for a packet (60+
  days, or 45+ days under 70%). Dedup treats it like Withdrawn. Bulk-set it from the
  ⚙ Age-out candidates view in the Notion UI.
- **Exclusion list**: `data/exclusions.md` holds company-level deliberate passes.
- **Rejection marker (MANDATORY)**: when setting Status = Rejected, in the same call set the
  Rejected checkbox and prefix the Company title with `❌ `. Never `~~strikethrough~~`.
- **No delete tool**: removal is always a Status change plus, for Withdrawn, a dated Notes line.
