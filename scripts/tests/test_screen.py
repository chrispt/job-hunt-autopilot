import json, os, sys, tempfile, unittest
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from screen import Screener, parse_salary, load_exclusions
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def screener(excl=None):
    with open(os.path.join(ROOT, "data", "screens.json"), encoding="utf-8") as fh:
        s = json.load(fh)
    return Screener(s, excl or set(), today=date(2026, 9, 8))


class Salary(unittest.TestCase):
    def test_shapes(self):
        cases = {
            "$50 - $100 an hour": 208000,
            "$120,000 - $150,000 a year": 150000,
            "$94K-$135K / year": 135000,
            "USD 400,000.00 - 640,000.00 per year": 640000,
            "$60 - $70": 145600,            # bare numbers under 1000 read as hourly
            "From $110,000 a year": 110000,
            "$8,000 a month": 96000,
            "$500 a day": 130000,
            "$70 - $80 an hour (~$166K annualized)": 166400,
        }
        for text, annual in cases.items():
            self.assertEqual(parse_salary(text)["annual_high"], annual, text)

    def test_non_numeric(self):
        self.assertIsNone(parse_salary("N/A"))
        self.assertIsNone(parse_salary("Depends on Experience"))
        self.assertIsNone(parse_salary(""))


class Seniority(unittest.TestCase):
    def test_director_discarded(self):
        r = screener().screen({"title": "Director, AI Product Ops", "company": "Thomson Reuters"})
        self.assertEqual(r["bucket"], "discard")
        self.assertTrue(r["rules"][0].startswith("seniority-discard"))

    def test_head_of_and_vice_president_discarded(self):
        for t in ("Head of Customer Success Transformation", "Vice President of AI Transformation", "Managing Principal, AI"):
            self.assertEqual(screener().screen({"title": t, "company": "Acme"})["bucket"], "discard", t)

    def test_department_name_rank_word_kept(self):
        r = screener().screen({"title": "Program Manager, Americas Chief of Staff Office", "company": "Cisco"})
        self.assertEqual(r["bucket"], "keep")

    def test_bank_vp_is_flagged_not_discarded(self):
        r = screener().screen({"title": "Vice President, Data Governance", "company": "JPMorganChase"})
        self.assertEqual(r["bucket"], "flag")
        r = screener().screen({"title": "VP, AI Product", "company": "Startup Inc."})
        self.assertEqual(r["bucket"], "flag")  # abbreviated VP is ambiguous everywhere

    def test_parenthetical_rank_flagged(self):
        r = screener().screen({"title": "Product Manager (Director)", "company": "Peraton"})
        self.assertEqual(r["bucket"], "flag")

    def test_referral_override_flags_instead_of_discarding(self):
        r = screener().screen({"title": "Director, AI Enablement", "company": "Patriot Growth", "referral": True})
        self.assertEqual(r["bucket"], "flag")

    def test_tier_drop_note(self):
        r = screener().screen({"title": "Principal Product Manager, AI", "company": "Acme"})
        self.assertEqual(r["bucket"], "keep")
        self.assertTrue(any("tier-drop" in n for n in r["notes"]))

    def test_plain_title_kept(self):
        r = screener().screen({"title": "AI Product Manager", "company": "Granicus"})
        self.assertEqual((r["bucket"], r["rules"], r["notes"]), ("keep", [], []))


class ContactCenter(unittest.TestCase):
    def test_role_keyword(self):
        r = screener().screen({"title": "Product Manager, Contact Center AI", "company": "Florida Blue"})
        self.assertEqual(r["bucket"], "discard")
        self.assertTrue(r["rules"][0].startswith("contact-center"))

    def test_exclusion_list_company(self):
        excl = load_exclusions(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "exclusions.md"))
        self.assertIn("five9", excl)
        self.assertIn("nice", excl)
        r = screener(excl).screen({"title": "AI Product Manager", "company": "Five9, Inc."})
        self.assertEqual(r["rules"], ["exclusion-list"])


class Comp(unittest.TestCase):
    def test_linkedin_below_floor_discarded_indeed_flagged(self):
        li = screener().screen({"title": "AI PM", "company": "A", "salary": "$94K-$135K / year", "source": "LinkedIn"})
        self.assertEqual(li["bucket"], "discard")
        ind = screener().screen({"title": "AI PM", "company": "A", "salary": "$120,000 - $150,000 a year", "source": "Indeed"})
        self.assertEqual(ind["bucket"], "keep")
        self.assertEqual(ind["notes"], [])  # exactly at floor is not below it
        ind2 = screener().screen({"title": "AI PM", "company": "A", "salary": "$100,000 - $140,000 a year", "source": "Indeed"})
        self.assertTrue(any("below salary floor" in n for n in ind2["notes"]))

    def test_band_out_of_range(self):
        r = screener().screen({"title": "AI PM", "company": "A", "salary": "$180,200 - $355,100 a year", "source": "Indeed"})
        self.assertTrue(any("out of range" in n for n in r["notes"]))

    def test_hourly_trainer_spam_annualizes_above_floor_but_is_part_time(self):
        r = screener().screen({"title": "Retail Banking Product Manager - AI Trainer", "company": "DataAnnotation", "salary": "$50 - $100 an hour", "source": "Indeed"})
        self.assertEqual(r["bucket"], "keep")


class Recency(unittest.TestCase):
    def test_stale_indeed_posting_discarded(self):
        r = screener().screen({"title": "AI PM", "company": "A", "source": "Indeed", "posted": "June 18, 2026"})
        self.assertEqual(r["bucket"], "discard")
        self.assertTrue(r["rules"][0].startswith("stale-posting"))

    def test_fresh_indeed_posting_kept(self):
        r = screener().screen({"title": "AI PM", "company": "A", "source": "Indeed", "posted": "September 06, 2026"})
        self.assertEqual(r["bucket"], "keep")


class Standout(unittest.TestCase):
    def test_referral_and_high_match_noted(self):
        r = screener().screen({"title": "AI PM", "company": "A", "referral": True, "match": 82})
        self.assertEqual(sum("STANDOUT" in n for n in r["notes"]), 2)


if __name__ == "__main__":
    unittest.main()
