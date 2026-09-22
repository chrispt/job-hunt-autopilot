import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import candidates, audit
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
REAL = os.path.expanduser("~/.claude/projects/C--Users-user-OneDrive-SoftwareDevelopment-Job-Application-Tool/0d937232-7da1-47b9-a215-3b43d244a4c0.jsonl")


class Indeed(unittest.TestCase):
    def test_fixture_parses_all_fields(self):
        with open(os.path.join(FIX, "indeed_result_sample.json"), encoding="utf-8") as fh:
            recs = candidates.parse_indeed(fh.read())
        self.assertGreaterEqual(len(recs), 5)
        r = recs[0]
        self.assertEqual(r["company"], "DataAnnotation")
        self.assertEqual(r["salary"], "$50 - $100 an hour")
        self.assertEqual(r["posted"], "June 18, 2026")
        self.assertTrue(r["url"].startswith("https://to.indeed.com/"))
        self.assertEqual(r["source"], "Indeed")

    def test_na_compensation_is_none(self):
        txt = json.dumps({"result": "**Job Title:** X\n**Job Id:** J1\n**Company:** C\n**Location:** Remote\n**Posted on:** September 01, 2026\n**Job Type:** Full-time\n**Compensation:** N/A\n**View Job URL:** https://to.indeed.com/abc\n"})
        self.assertIsNone(candidates.parse_indeed(txt)[0]["salary"])


class Singles(unittest.TestCase):
    def test_only_the_you_may_be_a_fit_shape_parses(self):
        self.assertEqual(candidates.parse_single_subject("You may be a fit for AHEAD‘s Principal Consultant, Internal AI role"),
                         {"company": "AHEAD", "title": "Principal Consultant, Internal AI"})
        self.assertIsNone(candidates.parse_single_subject("“AI Product Manager”: Foo - AI PM posted on LinkedIn"))

    def test_digest_shapes_do_not_parse_as_singles(self):
        """2026-09-18: these are multi-listing digests whose subject names only the first
        listing. A looser "<Role> at <Company>" pattern used to parse them, which made a
        six-listing email look like one fully-described job and dropped the other five."""
        for subject in ("Head of Artificial Intelligence at Elios AI: up to $300K/year",
                        "Field Enablement, Principal at Snowflake Computing, Inc.: up to $247K/year",
                        "MUFG is hiring a AI Risk Governance Director",
                        "Nutanix is hiring a Sr. Customer Experience Manager"):
            with self.subTest(subject=subject):
                self.assertIsNone(candidates.parse_single_subject(subject))


@unittest.skipUnless(os.path.exists(REAL), "real transcript not present")
class RealExtract(unittest.TestCase):
    def test_counts(self):
        cands = candidates.extract(audit.load_transcript(REAL), until_text="Daily Job Sweep")
        by = {}
        for c in cands:
            by[c["source"]] = by.get(c["source"], 0) + 1
        self.assertGreater(by.get("Indeed", 0), 50)
        self.assertGreaterEqual(by.get("LinkedIn", 0), 100)
        # every created row from that run must be findable among the candidates
        urls = {c["url"] for c in cands if c["url"]}
        self.assertIn("https://www.linkedin.com/jobs/view/4462775297", urls)  # Granicus, first created row


if __name__ == "__main__":
    unittest.main()
