import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normalize import normalize_company, normalize_title, title_core, same_company


class CompanyTests(unittest.TestCase):
    def test_legal_suffix_variants_collapse(self):
        # the 2026-08-09 duplicate: same employer, two spellings
        self.assertEqual(normalize_company("SHI International Corp."), normalize_company("SHI International"))
        self.assertEqual(normalize_company("Foo Holdings Inc."), "foo")
        self.assertEqual(normalize_company("Acme, LLC"), "acme")

    def test_rejection_prefix_stripped(self):
        self.assertEqual(normalize_company("❌ GitLab"), "gitlab")

    def test_trademark_and_case(self):
        self.assertEqual(normalize_company("VODA.ai™"), "voda ai")
        self.assertTrue(same_company("Capital One", "CAPITAL ONE"))

    def test_single_token_suffix_word_is_kept(self):
        # a company literally named "Company" or "Co" must not normalize to empty
        self.assertEqual(normalize_company("Co"), "co")

    def test_leading_the(self):
        self.assertEqual(normalize_company("The Hartford"), "hartford")

    def test_empty(self):
        self.assertEqual(normalize_company(""), "")


class TitleTests(unittest.TestCase):
    def test_level_noise_ignored(self):
        self.assertEqual(normalize_title("Senior AI Product Manager"), normalize_title("AI Product Manager, Senior"))
        self.assertEqual(normalize_title("Product Manager II"), "product manager")

    def test_different_functions_stay_different(self):
        self.assertNotEqual(normalize_title("AI Product Manager"), normalize_title("Customer Success Manager"))

    def test_director_is_not_level_noise(self):
        # screen.py needs Director to survive; dedup must not erase it either
        self.assertIn("director", normalize_title("Director of Product"))

    def test_title_core_strips_location_and_team(self):
        self.assertEqual(title_core("Deployment Manager, NYC"), title_core("Deployment Manager, EDU"))
        self.assertEqual(title_core("Product Manager - Remote (US)"), "product manager")


if __name__ == "__main__":
    unittest.main()
