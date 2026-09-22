import json, os, sys, tempfile, unittest
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dedup_query, lock, notion_rows


class Dedup(unittest.TestCase):
    rows = [
        {"Company": "SHI International", "Role": "AI Change Enablement Consultant", "Status": "To Apply", "Job URL": "https://www.linkedin.com/jobs/view/111"},
        {"Company": "❌ GitLab", "Role": "Senior Product Manager, AI", "Status": "Rejected", "Job URL": "https://x/gitlab"},
        {"Company": "Acme", "Role": "Deployment Manager, NYC", "Status": "Withdrawn", "Job URL": ""},
        {"Company": "Acme", "Role": "Customer Success Manager", "Status": "Aged Out", "Job URL": ""},
    ]

    def test_suffix_variant_and_url(self):
        res = dedup_query.dedup([
            {"company": "SHI International Corp.", "title": "AI Change Enablement Consultant", "url": "https://www.linkedin.com/jobs/view/999"},
            {"company": "Someone", "title": "X", "url": "https://www.linkedin.com/comm/jobs/view/111/?trk=abc"},
        ], self.rows)
        self.assertEqual(len(res["duplicate"]), 2)
        self.assertEqual(res["duplicate"][0]["why"], "same company + title")
        self.assertEqual(res["duplicate"][1]["why"], "same url")

    def test_rejected_and_aged_out_still_block(self):
        res = dedup_query.dedup([
            {"company": "GitLab", "title": "Product Manager, AI, Senior"},
            {"company": "Acme Inc", "title": "Customer Success Manager"},
        ], self.rows)
        self.assertEqual(len(res["duplicate"]), 2)

    def test_location_variant_is_duplicate_but_different_function_is_new(self):
        res = dedup_query.dedup([
            {"company": "Acme", "title": "Deployment Manager, EDU"},
            {"company": "Acme", "title": "AI Product Manager"},
        ], self.rows)
        self.assertEqual(len(res["duplicate"]), 1)
        self.assertEqual(len(res["new"]), 1)
        self.assertTrue(res["new"][0]["sibling_rows"])

    def test_sql_covers_every_spelling(self):
        s = dedup_query.sql_for([{"company": "VODA.ai™"}, {"company": "SHI International Corp."}])
        self.assertEqual(s["distinct_companies"], 2)
        self.assertIn("VODA.ai™", s["in_list"])
        self.assertIn("voda ai", s["in_list"])
        self.assertIn("REPLACE(Company, '❌', '')", s["sql"])


class Lock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        lock.LOCK_DIR = self.tmp

    def test_acquire_release_and_hold(self):
        self.assertEqual(lock.acquire("t", "s1", 3), 0)
        self.assertEqual(lock.acquire("t", "s2", 3), 1)
        self.assertEqual(lock.acquire("t", "s1", 3), 0)  # re-entrant for the holder
        self.assertEqual(lock.release("t", "s2"), 1)
        self.assertEqual(lock.release("t", "s1"), 0)
        self.assertEqual(lock.acquire("t", "s2", 3), 0)

    def test_stale_lock_replaced(self):
        self.assertEqual(lock.acquire("t", "old", 3), 0)
        self.assertEqual(lock.acquire("t", "new", 0), 0)  # stale immediately


class Rows(unittest.TestCase):
    def test_compact_and_days_old(self):
        obj = {"results": [{"Company": "A", "Role": "R", "Status": "To Apply", "Created": "2026-08-28T14:38:46.608Z",
                            "date:Packet Ready:start": None, "date:Date Applied:start": "2026-08-12", "Notes": "x" * 1000,
                            "Days Old": "formulaResult://x"}], "has_more": True, "next_cursor": "c1"}
        rows, more, cur = notion_rows.compact(obj, ["Company", "Role", "Date Applied", "Notes"], date(2026, 9, 8))
        self.assertEqual(rows[0]["days_old"], 11)
        self.assertEqual(rows[0]["Date Applied"], "2026-08-12")
        self.assertEqual(len(rows[0]["Notes"]), 300)
        self.assertTrue(more)
        self.assertEqual(cur, "c1")


if __name__ == "__main__":
    unittest.main()
