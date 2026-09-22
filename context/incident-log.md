# Incident log

Dated record of the failures that produced the plugin's rules. `skills/daily-sweep/SKILL.md`
used to carry these narratives inline and grew to 637 lines; the rules stay in the skills and
scripts, the stories live here. Each entry: what happened, the rule it produced, where that
rule is enforced now. Add new entries at the bottom; never delete one.

## 2026-07-23 to 07-31: null Status on created rows

Three sweeps (Jul 27, 30, 31) omitted `Status` on every create; 116 rows landed invisible to
every queue query. By Jul 31, 387 of 1,212 rows (32%) had no Status. The connector's create
path does not apply the database's UI default. Backfilled 2026-08-03 (304 To Apply, 76
Withdrawn as duplicates).
**Rule:** Status is set explicitly on every create, and the run verifies with the
"⚠ Status integrity" view and `scripts/audit.py` (flags any create payload without Status).

## 2026-07-27: `has_more: false` pagination trap

A single-page pull of a 1,013-row table reported `has_more: false` on page 1; only 100 rows
were checked and 15 duplicates were created.
**Rule:** never full-table pulls for dedup. `scripts/dedup_query.py` joins locally against
the weekly snapshot plus the "⚙ Added last 7 days" view, then one `WHERE ... IN (...)`
confirmation query.

## 2026-08-01 and 08-04: concurrent sweeps

Three sweep sessions ran on 08-01, two overlapping; on 08-04 a second run wrote three rows
while another was mid-flight. Read-then-write dedup is a race.
**Rule:** `scripts/lock.py` (time-bounded file lock, 3 h staleness) replaces the
`isRunning` session check, which also mis-deferred when a sweep session stayed open overnight.

## 2026-08-02: digest subjects undercount listings 6:1

Treating `search_threads` subjects as the listing set missed ~5 of every 6 LinkedIn roles.
**Rule:** every digest thread is opened; `audit.py` reports returned vs opened.

## 2026-08-03: Dice absent, silently

The Dice server was gone; 18 searches never ran and the sweep reported a quiet market.
Dice was retired by the candidate the same week.
**Rule:** "did not run" and "returned nothing" are reported separately; `audit.py` derives
both from the transcript rather than from the model's own account.

## 2026-08-03 and 08-07: LinkedIn digest badge shifts

Badge lines (`Fast growing`, `This company is actively hiring`, `1,717 company alumni`) between
location and `View job:` shifted fields by one, producing rows like `title="Cambridge, MA",
company="IBM"`. 5 of 45 listings on 08-03, IBM on 08-07.
**Rule:** `scripts/parse_linkedin_digest.py` reads blocks forward and backward and flags any
disagreement; badge patterns use `[\d,]+`.

## 2026-08-04: seniority screen read and not applied

"Senior Manager, Head of Data & AI" was scored down instead of discarded, with the rule quoted
in its own Notes. 142 discard-title rows sat in the queue a week after the rule landed.
False positives confirmed: Cisco "Program Manager, Americas Chief of Staff Office" (department
name), bank "VP" pay grades, Peraton "Product Manager (Director)".
**Rule:** `scripts/screen.py` with `data/screens.json`: discard / flag / keep buckets; flag
never auto-discards. `funnel-review` re-screens the standing queue when a rule changes.

## 2026-08-05: plugin cache drifted from source in both directions

A cache-only rule was destroyed by a bulk copy; a stale cache ran superseded instructions
for most of a day.
**Rule:** edit source, bump the version, reinstall. `audit.py` on a scheduled run proves which
instructions actually executed.

## 2026-08-07: Gmail sender list narrowed on retry

A `Precondition check failed` retry dropped `talent`, `jobs`, `no-reply`; Lenovo's receipt
from `talent@avature.lenovo.net` was never seen and the row was rejected while still filed
as To Apply.
**Rule:** split the query, never shorten the sender list; name any unchecked sender group.

## 2026-08-09: company-name spelling duplicates; encoding drop

`SHI International Corp.` and `SHI International` became two rows. `VODA.ai™` was mangled
by an encoding fault and silently dropped from the dedup `IN` list.
**Rule:** `scripts/normalize.py` is the single normalization; `dedup_query.py` asserts the
`IN` list count; every script forces UTF-8 stdout.

## 2026-08-09: `City, ST` false positive

"Product Manager, AI" was flagged as a place because the test was "comma plus two capitals".
**Rule:** the parser checks the trailing token against the closed set of US state codes.

## 2026-08-10: Top 3 without the floor

The first ranking under "Priority then oldest" put a 25% match in the Top 3.
**Rule:** the "⚙ Ranked queue" view carries the 55% floor in its filter.

## 2026-08-11: expiry false positive; stale cache

A "PMO Manager | AI" role was proposed for withdrawal because its Oracle HCM page rendered as a
bare header, the day after `apply-assist` read the full JD and documents were being built.
The same day the sweep ran a cache missing two source changes.
**Rule:** anonymous URL fetches never decide expiry (the check is removed; `apply-prep` reads
JDs through paths that work, and stale rows age out by policy).

## 2026-08-19: Trash and Spam blindness

A filter auto-trashed ~200 LinkedIn alerts unread; the default Gmail query returned zero.
**Rule:** `in:anywhere` on every Gmail query; zero alert results is a fault to investigate.

## 2026-08-31: interview-date silence is not a missed interview

A sweep led with a "possibly missed" phone screen; the call had happened by phone.
**Rule:** an Interviewing row with a past date and no email is an open question, not a
status change.

## 2026-09-02: Gmail connector retrieval gap; contact-center screen

A rejection the candidate could screenshot was unreachable by every query, including full-day
and Trash/Spam listings. Separately the candidate set the contact-center hard screen (14 rows
withdrawn, 10 vendors moved to `data/exclusions.md`).
**Rule:** Part 2 reports "nothing found in the mail the connector returned"; Ghosted is
low-confidence; contact-center keywords live in `data/screens.json`.

## 2026-09-04: quota exhaustion mid-run; mistyped tool id

Five consecutive `Query Data Source` quota errors plus a block-quota notice; 21 of 28 digests
never opened. Two runs (09-04, 09-07) called a Notion tool with a one-character typo in the
server UUID and got "No such tool available". The 08-24 run opened 0 of 30 digests for the
same quota reason.
**Rule:** routine reads go through saved views (quota-exempt); at most three SQL calls per
run; `audit.py` classifies both error strings.

## 2026-09-07: queries reworded

The model issued `ai enablement ai adoption` for `"AI Enablement" OR "AI Adoption"`; Indeed
reads plain words as AND and returned 1 result instead of ~10. 14 of 22 searches were reworded.
**Rule:** query text comes verbatim from `data/queries.json`; `audit.py` reports wording drift.

## 2026-09-08: wrapped tracking URLs; a memory note contradicted by the transcript

In one digest template the "Manage alerts" and "See all jobs" links wrap onto a second line;
the fragment shifted 6 listings across 2 digests. Separately, a memory note claimed the 09-08
run issued 9 of 22 searches and fabricated a row; the transcript shows 22 of 22, 8 of 8
digests, and provenance for all 27 rows. The real digest gap was 09-04.
**Rule:** URL fragments are stripped as header lines; run coverage is measured by
`audit.py` from the transcript, never from the model's summary or the UI.

## 2026-09-18: "is hiring a" digests classified as singles; audit still said OK

LinkedIn now titles most job-alert digests `<Company> is hiring a <Role>` and
`<Role> at <Company>: up to $NK/year`. `classify_alert_subject` only recognised a digest by a
leading curly quote or the words "new jobs"/"job alert", and defaulted everything else to
"single" (a one-job recommendation, fully described by its subject and safe to screen without
opening). So 21 of 25 alert threads that morning were never opened. `candidates.py` then made
it invisible: its loose `^(.+?) at (.+?)` pattern parsed a six-listing digest into one
candidate, and the 19 "is hiring a" subjects matched no pattern at all and were dropped with no
warning. Coverage read `4 digests, 4 opened` and the audit printed **OK**.

Caught by hand because 20 unopened threads in the audit block looked wrong for a day with only
5 new rows. Opening all of them took candidates from 69 to 171, parsed listings from 40 to 162,
and rows created from 5 to 20: roughly 75% of the day's discovery had been silently lost, and
the same undercount had been running since LinkedIn changed the subject format.
**Rule:** the classifier is inverted. Only `You may be a fit for X's Y role` is a single;
everything else, including a missing subject, is a digest and must be opened. Misreading a
digest as a single loses listings silently, misreading a single as a digest costs one
`get_thread`. `candidates.py` keeps exactly one subject pattern, matching the classifier, so a
subject can never be half-parsed. Covered by `ClassifyAlertSubject` in `scripts/tests/test_audit.py`
and `Singles` in `scripts/tests/test_candidates.py`, both carrying the real 09-18 subject lines.
