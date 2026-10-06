# LinkedIn connections export (`Connections.csv`)

`skills/referral-match`, the sweep's standout rule and `apply-prep` join your own LinkedIn
connections against the pipeline on Company. The roster is never scraped: you export it
yourself.

**How to export:** LinkedIn → Settings & Privacy → Data Privacy → "Get a copy of your data" →
Connections → Request archive. It is usually ready in about ten minutes. Save it to the path
in `context/config.md` (default `<your documents folder>\network\Connections.csv`).

**Format:** a 2-3 line notes preamble precedes the real header row (`First Name`, `Last Name`,
`URL`, `Email Address`, `Company`, `Position`, `Connected On`). The skills parse from the
header row, not row 1.

**Refresh** every ~90 days; people change jobs. The skills warn when the file is older than
that and proceed anyway.
