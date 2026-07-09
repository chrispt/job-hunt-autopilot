# Job Search Exclusion List

Companies deliberately passed on — never resurface in `skills/daily-sweep` discovery (Part 1)
or in `skills/apply-assist`. Checked by company name (case-insensitive, ignore legal
suffixes like Inc./LLC/Corp), same normalization the dedup step already uses against Notion.

This list is for **deliberate strategic passes** (domain mismatch, comp floor, bad fit
found after real evaluation) — it is NOT the same as `Status = Rejected` in Notion, which
means an application went in and got turned down. An excluded company should never even
generate a "To Apply" entry.

| Company | Excluded on | Reason | Revisit condition |
|---|---|---|---|

**How to add an entry:** whenever a manual or automated evaluation results in "pass on this
company entirely" (not just "pass on this one posting"), add a row here with the date,
the concrete reason, and — if there is one — a condition under which it's worth revisiting.
Keep reasons specific enough that a future run can tell whether the revisit condition has
been met, rather than re-litigating the whole decision from scratch.

Starts empty — this fills in over time as you evaluate and pass on companies.
