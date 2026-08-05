# Network Roster (optional, for `skills/referral-match`)

<!-- TEMPLATE — this file documents the contract `skills/referral-match` expects from a
network-export CSV. The example below walks through a LinkedIn export since that's a common
case, but any professional-network export (or a manually maintained contacts spreadsheet)
works as long as it has Company/Position-equivalent columns. Delete this file if you don't
use `referral-match`. -->

`skills/referral-match` matches your professional network against open pipeline roles. Like
`data/exclusions.md`, the roster documented here is **not itself committed** to a public
fork — it's personal data about other people, and belongs only in your own private storage
(local file, your own private Drive folder, etc.), read directly by the skill. This file just
documents the contract: where the file is expected to live, its shape, and how to refresh it.

## Where the file lives

Path is pinned in `../context/config.md`. Point it at wherever you keep your own export —
your resume storage, a local folder, etc. **Never commit the actual roster file to a
repository**, even a private one, without thinking through the privacy implications for the
people in it.

## One worked example: exporting from LinkedIn

1. LinkedIn → **Settings & Privacy** → **Data Privacy** → **Get a copy of your data**.
2. Use the "download a larger archive" option (connections, invitations, etc.) rather than
   any narrower option — LinkedIn's UI for a connections-only export has moved around over
   time and may not reliably offer just what you need.
3. `Connections.csv` (or your platform's equivalent) sits at the top level of the resulting
   archive alongside other files you can ignore.
4. Request the archive; it'll typically arrive by email when ready.
5. Download it, extract the connections file, and save it to the path pinned in `config.md`.

This is your own data, exported through the platform's own tooling — not a scrape. Never
substitute a third-party scraper or similar tool for this step; most professional networks'
Terms of Service prohibit scraping connection data, and that boundary is deliberate (see the
source-policy note in `../skills/daily-sweep/SKILL.md`).

## Refresh cadence

Monthly or quarterly is usually enough — contacts don't change jobs that often.
`referral-match` should warn (but still run) if the file is older than your chosen staleness
window, since the company/title columns are a point-in-time snapshot and can lag reality.

## Expected shape

A typical export: a short preamble (a few notes lines) followed by a header row and one row
per contact. Columns `referral-match` needs: name, profile URL, current company, current
title. Other columns present in the export but unused here can be ignored.

## Privacy note

This file contains personal data about people who are not you — treat it the way the rest of
this plugin treats any personal data: read it to do the matching job, never copy it into a
committed file, never use it for anything beyond the referral-match join it exists for.
