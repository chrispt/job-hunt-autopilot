import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import audit
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "queries.json")
REAL = os.path.expanduser("~/.claude/projects/C--Users-user-OneDrive-SoftwareDevelopment-Job-Application-Tool/0d937232-7da1-47b9-a215-3b43d244a4c0.jsonl")


def rec(kind, blocks, ts):
    return {"type": kind, "timestamp": ts, "message": {"content": blocks}}


def queries():
    with open(Q, encoding="utf-8") as fh:
        return json.load(fh)


def synthetic():
    q = queries()
    recs, t = [], 0

    def tick():
        nonlocal t
        t += 1
        return f"2026-09-09T12:00:{t:02d}Z"
    n = 0
    for x in q["queries"]:
        for loc in q["locations"]:
            n += 1
            if n == 5:
                continue  # deliberately skip one search
            uid = f"tu{n}"
            recs.append(rec("assistant", [{"type": "tool_use", "id": uid, "name": "mcp__x__search_jobs", "input": {"search": x["search"], "location": loc}}], tick()))
            body = "**Job Title:** T\n**Job Id:** JOBSEARCH_%d\n**Company:** C\n**Posted on:** September 08, 2026\n**Compensation:** N/A\n**View Job URL:** https://to.indeed.com/aa%05d\n" % (n, n)
            recs.append(rec("user", [{"type": "tool_result", "tool_use_id": uid, "content": json.dumps({"result": body})}], tick()))
    recs.append(rec("assistant", [{"type": "tool_use", "id": "st", "name": "mcp__g__search_threads", "input": {"query": "x"}}], tick()))
    recs.append(rec("user", [{"type": "tool_result", "tool_use_id": "st", "content": json.dumps({"threads": [
        {"id": "d1", "messages": [{"sender": "jobalerts-noreply@linkedin.com", "subject": "“AI Product Manager”: Foo - AI PM posted on LinkedIn"}]},
        {"id": "d2", "messages": [{"sender": "jobalerts-noreply@linkedin.com", "subject": "“AI Product Manager”: Bar - AI PM posted on LinkedIn"}]},
        {"id": "s1", "messages": [{"sender": "jobalerts-noreply@linkedin.com", "subject": "You may be a fit for Baz's Head of AI role"}]},
        {"id": "other", "messages": [{"sender": "careers@acme.com", "subject": "Thanks for applying"}]}]})}], tick()))
    recs.append(rec("assistant", [{"type": "tool_use", "id": "gt", "name": "mcp__g__get_thread", "input": {"threadId": "d1"}}], tick()))
    recs.append(rec("user", [{"type": "tool_result", "tool_use_id": "gt", "content": json.dumps({"messages": [{"plaintextBody": "AI PM\nFoo\nRemote\nView job: https://www.linkedin.com/comm/jobs/view/777/?x\n"}]})}], tick()))
    recs.append(rec("assistant", [{"type": "tool_use", "id": "qq", "name": "mcp__n__notion-query-data-sources", "input": {"data": {"mode": "sql", "query": "x"}}}], tick()))
    recs.append(rec("user", [{"type": "tool_result", "tool_use_id": "qq", "is_error": True, "content": "Your workspace has reached the usage limit for Query Data Source."}], tick()))
    recs.append(rec("assistant", [{"type": "tool_use", "id": "nt", "name": "mcp__n__notion-query-data-sources", "input": {}}], tick()))
    recs.append(rec("user", [{"type": "tool_result", "tool_use_id": "nt", "is_error": True, "content": "<tool_use_error>Error: No such tool available: mcp__n__notion-query-data-sources</tool_use_error>"}], tick()))
    recs.append(rec("assistant", [{"type": "tool_use", "id": "cp", "name": "mcp__n__notion-create-pages", "input": {"pages": [
        {"properties": {"Company": "Foo", "Role": "AI PM", "Status": "To Apply", "Job URL": "https://www.linkedin.com/jobs/view/777"}},
        {"properties": {"Company": "C", "Role": "T", "Status": "To Apply", "Job URL": "https://to.indeed.com/aa00003"}},
        {"properties": {"Company": "Ghost", "Role": "Invented", "Job URL": "https://www.linkedin.com/jobs/view/999999"}}]}}], tick()))
    recs.append(rec("user", [{"type": "tool_result", "tool_use_id": "cp", "content": "{\"pages\":[]}"}], tick()))
    return recs


class Synthetic(unittest.TestCase):
    def setUp(self):
        self.out = audit.audit(synthetic(), queries(), mode="full")

    def test_missing_search_detected(self):
        self.assertEqual(self.out["indeed_expected"], 22)
        self.assertEqual(len(self.out["indeed"]), 21)
        self.assertEqual(len(self.out["indeed_missing"]), 1)

    def test_unopened_digest_detected(self):
        self.assertEqual(self.out["digests_returned"], 2)
        self.assertEqual(self.out["digests_opened"], 1)
        self.assertEqual(len(self.out["digests_unopened"]), 1)
        self.assertEqual(self.out["digests"]["d1"]["listings"], 1)
        # single-job recommendation mail is counted separately and does not fail coverage
        self.assertEqual(self.out["singles_returned"], 1)
        self.assertEqual(self.out["singles_opened"], 0)

    def test_provenance_and_null_status(self):
        self.assertEqual(self.out["creates_total"], 3)
        self.assertEqual([c["company"] for c in self.out["creates_no_provenance"]], ["Ghost"])
        self.assertEqual([c["company"] for c in self.out["creates_null_status"]], ["Ghost"])
        self.assertEqual(self.out["creates"][1]["provenance"], "indeed:https://to.indeed.com/aa00003")

    def test_error_classes(self):
        classes = sorted(e["class"] for e in self.out["errors"])
        self.assertEqual(classes, ["no-such-tool", "notion-query-quota"])

    def test_not_ok_and_render(self):
        self.assertFalse(self.out["ok"])
        txt = audit.render(self.out)
        self.assertIn("coverage-digest:", txt)
        self.assertIn("NO PROVENANCE", txt)
        self.assertIn("MISSING 1", txt)

    def test_reworded_search_counts_as_issued_but_is_reported(self):
        recs = synthetic()
        # replace the first search's wording with the 2026-09-07 style (quotes and OR dropped, order changed)
        for r in recs:
            for b in r["message"]["content"]:
                if b.get("type") == "tool_use" and b["name"].endswith("search_jobs") and "Governance" in b["input"]["search"]:
                    b["input"]["search"] = "ai governance responsible ai policy"
        out = audit.audit(recs, queries(), mode="full")
        self.assertEqual(len(out["indeed_missing"]), 1)  # only the deliberately skipped one
        self.assertEqual(out["indeed_unexpected"], [])
        self.assertEqual(len(out["wording_differs"]), 1)  # the Remote variant is the deliberately skipped search
        self.assertIn("wording that differs", audit.render(out))

    def test_light_mode_expectation(self):
        out = audit.audit(synthetic(), queries(), mode="light")
        self.assertEqual(out["indeed_expected"], 3)
        self.assertEqual(out["indeed_missing"], [])
        self.assertEqual(len(out["indeed_unexpected"]), 18)


def metadata_only():
    """2026-09-15 shape: a paged search_threads call with view THREAD_VIEW_METADATA_ONLY returns
    alert threads with no subject or snippet, after an earlier full call already returned some of
    them with subjects. It crashed the unopened-list formatting (subject=None sliced) and, because
    the later record overwrote the subject and None classified as 'single', moved 7 digests into
    the single-job count."""
    S = "jobalerts-noreply@linkedin.com"
    recs = [
        rec("assistant", [{"type": "tool_use", "id": "st1", "name": "mcp__g__search_threads", "input": {"query": "from:" + S}}], "2026-09-15T12:10:53Z"),
        rec("user", [{"type": "tool_result", "tool_use_id": "st1", "content": json.dumps({"threads": [
            {"id": "d3", "messages": [{"sender": S, "subject": "“Customer Success Manager”: Workday - Sr CSM posted on LinkedIn"}]},
            {"id": "s2", "messages": [{"sender": S, "subject": "You may be a fit for TE Connectivity’s Sr Dr, AI Transformation role"}]},
            {"id": "d6", "messages": [{"sender": S, "subject": "TE Connectivity is hiring a Sr Dr, AI Transformation"}]}]})}], "2026-09-15T12:10:54Z"),
        rec("assistant", [{"type": "tool_use", "id": "st2", "name": "mcp__g__search_threads", "input": {"query": "from:" + S, "view": "THREAD_VIEW_METADATA_ONLY", "pageToken": "p2"}}], "2026-09-15T12:12:18Z"),
        rec("user", [{"type": "tool_result", "tool_use_id": "st2", "content": json.dumps({"threads": [
            {"id": "d3", "messages": [{"sender": S}]},
            {"id": "s2", "messages": [{"sender": S}]},
            {"id": "d6", "messages": [{"sender": S}]},
            {"id": "d4", "messages": [{"sender": S}]},
            {"id": "d5", "messages": [{"sender": S}]}]})}], "2026-09-15T12:12:19Z"),
        rec("assistant", [{"type": "tool_use", "id": "gt5", "name": "mcp__g__get_thread", "input": {"threadId": "d5"}}], "2026-09-15T12:12:30Z"),
        rec("user", [{"type": "tool_result", "tool_use_id": "gt5", "content": json.dumps({"messages": [{"plaintextBody":
            "Your job alert for AI Product Manager in United States\n30+ new jobs match your preferences.\n\nAI PM\nFoo\nRemote\nView job: https://www.linkedin.com/comm/jobs/view/555/?x\n"}]})}], "2026-09-15T12:12:31Z"),
    ]
    return recs


class ClassifyAlertSubject(unittest.TestCase):
    """Every subject shape seen on the 2026-09-18 sweep, where 21 of 25 alert threads were
    misclassified as singles and never opened."""

    def test_only_you_may_be_a_fit_is_single(self):
        self.assertEqual(audit.classify_alert_subject(
            "You may be a fit for AHEAD‘s Principal Consultant, Internal AI role"), "single")
        self.assertEqual(audit.classify_alert_subject(
            "You may be a fit for TE Connectivity’s Sr Dr, AI Transformation role"), "single")

    def test_everything_else_is_a_digest(self):
        for subject in (
            "“Technical Enablement OR Sales…”: Janus Henderson Investors - AI Enablement Partner posted on 9/14/26",
            "MUFG is hiring a AI Risk Governance Director",
            "Nutanix is hiring a Sr. Customer Experience Manager",
            "Field Enablement, Principal at Snowflake Computing, Inc.: up to $247K/year",
            "Customer Success Manager at Swooped: up to $190K/year",
            "Director, Transformation AI Architect at Microsoft",
            "Your job alert for AI Product Manager in United States",
            "something LinkedIn has not invented yet",
        ):
            with self.subTest(subject=subject):
                self.assertEqual(audit.classify_alert_subject(subject), "digest")

    def test_missing_subject_fails_closed_as_digest(self):
        self.assertEqual(audit.classify_alert_subject(None), "digest")
        self.assertEqual(audit.classify_alert_subject(""), "digest")


class MetadataOnlyThreads(unittest.TestCase):
    def setUp(self):
        self.out = audit.audit(metadata_only(), queries(), mode="skip")

    def test_later_subjectless_record_keeps_known_subject_and_kind(self):
        self.assertTrue(self.out["digests"]["d3"]["subject"].startswith("“Customer Success Manager”"))
        self.assertEqual(self.out["digests"]["d3"]["kind"], "digest")
        self.assertEqual(self.out["digests"]["s2"]["kind"], "single")

    def test_is_hiring_a_subject_is_a_digest(self):
        """2026-09-18: "<Company> is hiring a <Role>" is a six-listing digest, not a single-job
        recommendation. It classified as 'single' until then, so it was never opened."""
        self.assertEqual(self.out["digests"]["d6"]["kind"], "digest")
        self.assertTrue(any(u.startswith("d6 ") for u in self.out["digests_unopened"]))

    def test_never_subjected_thread_fails_closed_as_digest(self):
        # no subject ever seen and never opened: count it as a digest so coverage flags it
        self.assertEqual(self.out["digests"]["d4"]["kind"], "digest")
        self.assertTrue(any(u.startswith("d4 ") for u in self.out["digests_unopened"]))
        # opened with a digest body: classified from the body, and counted as opened
        self.assertEqual(self.out["digests"]["d5"]["kind"], "digest")
        self.assertTrue(self.out["digests"]["d5"]["opened"])

    def test_counts_and_render_do_not_crash(self):
        self.assertEqual(self.out["digests_returned"], 4)
        self.assertEqual(self.out["digests_opened"], 1)
        self.assertEqual(self.out["singles_returned"], 1)
        self.assertEqual(len(self.out["singles_unopened"]), 1)
        self.assertIn("UNOPENED 3", audit.render(self.out))


@unittest.skipUnless(os.path.exists(REAL), "real 2026-09-08 transcript not present")
class RealRun(unittest.TestCase):
    def test_reproduces_measured_counts(self):
        recs = audit.load_transcript(REAL)
        out = audit.audit(recs, queries(), mode="full", until_text="Daily Job Sweep")
        self.assertEqual(len(out["indeed"]), 22)
        self.assertEqual(out["indeed_missing"], [])
        self.assertEqual(out["indeed_unexpected"], [])
        # 12/0, not the 8/4 measured when this test was written: the 2026-09-18 classifier fix
        # moved this run's four "<Role> at <Company>" threads from single to digest. That run
        # had opened all of them anyway, so it stays OK and lost nothing; only the labels moved.
        self.assertEqual(out["digests_returned"], 12)
        self.assertEqual(out["digests_opened"], 12)
        self.assertEqual(out["digests_unopened"], [])
        self.assertEqual(out["singles_returned"], 0)
        self.assertTrue(out["ok"])
        self.assertEqual(out["creates_total"], 27)
        self.assertEqual(out["creates_no_provenance"], [])
        self.assertEqual(out["creates_null_status"], [])


if __name__ == "__main__":
    unittest.main()
