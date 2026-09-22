import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parse_linkedin_digest import parse_digest, looks_like_place, is_badge
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class RealDigest(unittest.TestCase):
    def setUp(self):
        self.r = parse_digest(_read(os.path.join(FIX, "digest_2026-09-07.txt")))

    def test_count_and_first(self):
        self.assertEqual(self.r["count"], 10)
        first = self.r["listings"][0]
        self.assertEqual((first["title"], first["company"], first["location"]), ("Policy Communications", "Anthropic", "San Francisco, CA"))
        self.assertEqual(first["url"], "https://www.linkedin.com/jobs/view/4426658185")
        self.assertEqual(first["alert"], "AI Governance OR AI Policy OR Responsible AI")

    def test_salary_line_captured_not_mistaken_for_location(self):
        kong = next(l for l in self.r["listings"] if l["company"] == "Kong")
        self.assertEqual(kong["location"], "United States")
        self.assertEqual(kong["salary"], "$94K-$135K / year")

    def test_blank_line_inside_block(self):
        rwe = next(l for l in self.r["listings"] if l["company"] == "RWE")
        self.assertEqual(rwe["location"], "Austin, TX")

    def test_alert_section_switch(self):
        evlo = [l for l in self.r["listings"] if l["company"] == "Evlo AI"]
        self.assertEqual(len(evlo), 2)
        self.assertEqual(evlo[0]["alert"], "AI Product Manager")

    def test_nothing_flagged_on_clean_digest(self):
        self.assertEqual(self.r["flagged"], [])


class BadgeShifts(unittest.TestCase):
    def test_thousands_separator_badge(self):
        body = "AI Foundations - Technical Product Manager\nIBM\nCambridge, MA\n1,717 company alumni\nView job: https://www.linkedin.com/comm/jobs/view/1/?x\n"
        r = parse_digest(body)
        l = r["listings"][0]
        self.assertEqual((l["title"], l["company"], l["location"]), ("AI Foundations - Technical Product Manager", "IBM", "Cambridge, MA"))
        self.assertEqual(r["flagged"], [])

    def test_unknown_badge_is_flagged_not_silently_shifted(self):
        body = "Product Manager\nAcme\nDenver, CO\nBrand new badge string\nView job: https://www.linkedin.com/comm/jobs/view/2/?x\n"
        r = parse_digest(body)
        l = r["listings"][0]
        # forward reading is still right, but backward disagrees, so it is flagged for a human glance
        self.assertEqual(l["location"], "Denver, CO")
        self.assertTrue(l.get("flags"))

    def test_title_ending_in_acronym_is_not_a_place(self):
        self.assertFalse(looks_like_place("Product Manager, AI"))
        self.assertFalse(looks_like_place("Director of Product Management, AI"))
        self.assertTrue(looks_like_place("Cambridge, MA"))
        self.assertTrue(looks_like_place("United States"))

    def test_badge_patterns(self):
        for s in ["Fast growing", "This company is actively hiring", "Actively recruiting", "2 connections", "1 school alum", "Apply with resume & profile", "Top applicant"]:
            self.assertTrue(is_badge(s), s)

    def test_wrapped_header_url_continuation_is_not_a_field(self):
        # 2026-09-08 template: the 'Manage alerts' link wraps, leaving a bare tracking fragment
        # immediately before the first listing; the same happens after 'See all jobs' links.
        body = (
            "Your job alert for AI Product Manager in United States\n"
            "30+ new jobs match your preferences.\n"
            "Manage alerts: https://www.linkedin.com/comm/jobs/alerts?lipi=urn%3Ali%3Apage%3Aemail_email_job_alert_digest_01%3B\n"
            "5pB2bXnvTIo1&trk=eml-email_job_alert_digest_01-primary_job_list-0-manage_alerts_text_ssid_8721102594_fmid_857wm~mtokj6gn~3x&trkEmail=eml-null\n"
            "\n"
            "Director, AI Product Ops\n"
            "Thomson Reuters\n"
            "Frisco, TX\n"
            "\n"
            "This company is actively hiring\n"
            "View job: https://www.linkedin.com/comm/jobs/view/4461900512/?trackingId=FsEw%2FG6ke10hMAgyP8uNyw%3D%3D&refId=NEk9\n"
            "5pB2bXnvTIo1&trk=eml-email_job_alert_digest_01-primary_job_list-0-jobcard_body_text_0_jobid_4461900512_ssid_8721102594&trkEmail=x\n"
            "\n"
            "---------------------------------------------------------\n"
            "\n"
            "See all jobs on LinkedIn: https://www.linkedin.com/comm/jobs/search-results/?keywords=AI+Product+Manager\n"
            "5pB2bXnvTIo1&trk=eml-email_job_alert_digest_01-primary_job_list-0-see_all_jobs_text_ssid_8721102594_fmid_857wm~mtokj6gn~3x&trkEmail=eml-null\n"
            "\n"
            "<strong class=\"font-bold\" style=\"font-weight: 600;\">AI Enablement OR AI Adoption</strong>\n"
            "\n"
            "AI Consulting Manager\n"
            "EisnerAmper\n"
            "Fort Myers, FL\n"
            "Top applicant\n"
            "View job: https://www.linkedin.com/comm/jobs/view/4452032583/?trackingId=KCLeCqeYEJsJtQV4hTcwbg%3D%3D\n"
            "5pB2bXnvTIo1&trk=eml-email_job_alert_digest_01-secondary_job_list_0-0-jobcard_body_text_ssid_16000073172&trkEmail=x\n"
        )
        r = parse_digest(body)
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["flagged"], [])
        a, b = r["listings"]
        self.assertEqual((a["title"], a["company"], a["location"]), ("Director, AI Product Ops", "Thomson Reuters", "Frisco, TX"))
        self.assertEqual((b["title"], b["company"], b["location"]), ("AI Consulting Manager", "EisnerAmper", "Fort Myers, FL"))
        self.assertEqual(b["alert"], "AI Enablement OR AI Adoption")

    def test_dedupe_same_job_id(self):
        body = "A\nB\nC, TX\nView job: https://www.linkedin.com/comm/jobs/view/9/?a\n----------\nA\nB\nC, TX\nView job: https://www.linkedin.com/comm/jobs/view/9/?b\n"
        self.assertEqual(parse_digest(body)["count"], 1)


if __name__ == "__main__":
    unittest.main()
