import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from age_out import apply_verdicts, split  # noqa: E402

FLOOR = 70


class Split(unittest.TestCase):
    def test_low_match_goes_direct(self):
        rows = [{"Company": "A", "Role": "PM", "Match %": 62, "Job URL": "u", "url": "n"}]
        direct, borderline = split(rows, FLOOR)
        self.assertEqual(len(direct), 1)
        self.assertEqual(len(borderline), 0)
        self.assertEqual(direct[0]["action"], "aged_out_direct")

    def test_high_match_goes_borderline(self):
        rows = [{"Company": "Reddit", "Role": "Lead Product Adoption Strategist", "Match %": 76, "Job URL": "u", "url": "n"}]
        direct, borderline = split(rows, FLOOR)
        self.assertEqual(len(direct), 0)
        self.assertEqual(len(borderline), 1)
        self.assertEqual(borderline[0]["action"], "needs_jd_ladder")

    def test_exactly_at_floor_is_borderline_not_direct(self):
        rows = [{"Company": "A", "Role": "PM", "Match %": FLOOR, "Job URL": "u", "url": "n"}]
        direct, borderline = split(rows, FLOOR)
        self.assertEqual(len(borderline), 1)
        self.assertEqual(len(direct), 0)

    def test_missing_match_treated_as_zero_goes_direct(self):
        rows = [{"Company": "A", "Role": "PM", "Job URL": "u", "url": "n"}]
        direct, borderline = split(rows, FLOOR)
        self.assertEqual(len(direct), 1)

    def test_lowercase_keys_supported(self):
        rows = [{"company": "A", "role": "PM", "match": 80, "job_url": "u", "notion_url": "n"}]
        direct, borderline = split(rows, FLOOR)
        self.assertEqual(len(borderline), 1)
        self.assertEqual(borderline[0]["company"], "A")


class Verdicts(unittest.TestCase):
    def test_closed_verdict_proposes_withdrawn(self):
        v = [{"company": "Reddit", "role": "Lead Product Adoption Strategist", "verdict": "confirmed_dead",
              "evidence": "Greenhouse board omits the role"}]
        withdraw, left_open, fallback = apply_verdicts(v)
        self.assertEqual(len(withdraw), 1)
        self.assertEqual(withdraw[0]["action"], "propose_withdrawn")
        self.assertEqual(len(left_open), 0)
        self.assertEqual(len(fallback), 0)

    def test_open_verdict_left_untouched(self):
        v = [{"company": "A", "role": "PM", "verdict": "still_open"}]
        withdraw, left_open, fallback = apply_verdicts(v)
        self.assertEqual(len(left_open), 1)
        self.assertEqual(left_open[0]["action"], "leave_untouched")

    def test_inconclusive_falls_back_to_aged_out(self):
        v = [{"company": "A", "role": "PM", "verdict": "inconclusive"}]
        withdraw, left_open, fallback = apply_verdicts(v)
        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0]["action"], "aged_out_fallback")

    def test_missing_verdict_never_treated_as_closed(self):
        v = [{"company": "A", "role": "PM"}]
        withdraw, left_open, fallback = apply_verdicts(v)
        self.assertEqual(len(withdraw), 0)
        self.assertEqual(len(fallback), 1)

    def test_unrecognized_verdict_is_conservative_fallback_not_withdraw(self):
        v = [{"company": "A", "role": "PM", "verdict": "maybe??"}]
        withdraw, left_open, fallback = apply_verdicts(v)
        self.assertEqual(len(withdraw), 0)
        self.assertEqual(len(fallback), 1)


if __name__ == "__main__":
    unittest.main()
