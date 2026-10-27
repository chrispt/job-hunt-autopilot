import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ats_check
from ats_check import coverage, check_parse, check_pages, tokens

try:
    import pypdf  # noqa: F401
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False

RESUME = """Jordan Example
jordan@example.com | 555-010-0199
AI ADOPTION PRODUCT MANAGER | CUSTOMER SUCCESS LEADER
Product manager focused on customer adoption and change management.
CORE COMPETENCIES
Stakeholder alignment, enablement programs, Agile delivery
PROFESSIONAL EXPERIENCE
EXAMPLE NETWORKS
Product Manager, Adoption Strategy  April 2023 - July 2026
Drove adoption frameworks across three platforms; ran the PMO intake.
Customer Success Manager  October 2019 - March 2023
EDUCATION
B.B.A., Example University
"""

MASTER = RESUME.replace("customer adoption", "usage uplift").replace("AI ADOPTION ", "AI-FOCUSED ")


def term(t, tier="required", aliases=None):
    return {"term": t, "tier": tier, "aliases": aliases or []}


class TokenTests(unittest.TestCase):
    def test_plural_and_ing_stem_to_same_token(self):
        self.assertEqual(tokens("stakeholders"), tokens("stakeholder"))
        self.assertEqual(tokens("programs"), tokens("program"))
        self.assertEqual(tokens("strategies"), tokens("strategy"))

    def test_hyphen_slash_ampersand(self):
        self.assertEqual(tokens("go-to-market"), tokens("go to market"))
        self.assertEqual(tokens("AI/ML"), tokens("ai ml"))
        self.assertEqual(tokens("R&D"), tokens("r and d"))


class CoverageTests(unittest.TestCase):
    def test_word_boundary_pm_does_not_match_pmo(self):
        r = coverage([term("PM")], "Ran the PMO intake.")
        self.assertFalse(r["terms"][0]["found"])

    def test_alias_counts_and_reports_what_matched(self):
        r = coverage([term("organizational change", aliases=["change management"])], RESUME)
        self.assertTrue(r["terms"][0]["found"])
        self.assertEqual(r["terms"][0]["matched"], "change management")

    def test_section_attribution(self):
        r = coverage([term("stakeholder"), term("adoption framework")], RESUME)
        self.assertEqual(r["terms"][0]["sections"], ["competencies"])
        self.assertEqual(r["terms"][1]["sections"], ["experience"])

    def test_title_hit_requires_top_block(self):
        hit = coverage([term("adoption product manager", "title")], RESUME)
        self.assertTrue(hit["summary"]["title"]["hit"])
        # "customer success manager" exists only as a job line in experience, not the headline
        miss = coverage([term("customer success manager", "title")], RESUME)
        self.assertFalse(miss["summary"]["title"]["hit"])

    def test_percentages_and_notes_line(self):
        terms = [term("customer adoption"), term("kubernetes"),
                 term("agile", "preferred"), term("adoption product manager", "title")]
        r = coverage(terms, RESUME)
        self.assertEqual(r["summary"]["required"], {"found": 1, "total": 2, "pct": 50})
        self.assertEqual(r["notes_line"], "ATS terms: req 1/2, pref 1/1, title hit")

    def test_baseline_delta(self):
        terms = [term("customer adoption"), term("adoption product manager", "title"),
                 term("change management")]
        r = coverage(terms, RESUME, MASTER)
        self.assertEqual(r["gained"], ["adoption product manager", "customer adoption"])
        self.assertEqual(r["lost"], [])
        self.assertEqual(r["baseline"]["required"]["found"], 1)

    def test_unknown_tier_rejected(self):
        with self.assertRaises(ValueError):
            coverage([term("x", "nice-to-have")], RESUME)


EXPECT = {
    "name": "Jordan Example", "email": "jordan@example.com", "phone": "555-010-0199",
    "headings": ["CORE COMPETENCIES", "PROFESSIONAL EXPERIENCE", "EDUCATION"],
    "roles": [
        {"employer": "Example Networks", "title": "Product Manager, Adoption Strategy",
         "dates": "April 2023 - July 2026"},
        {"employer": "Example Networks", "title": "Customer Success Manager",
         "dates": "October 2019 - March 2023"},
    ],
    "max_pages": 2,
}


class ParseCheckTests(unittest.TestCase):
    def test_clean_resume_passes(self):
        r = check_parse([RESUME], EXPECT)
        self.assertEqual(r["overall"], "PASS", r["checks"])

    def test_box_bar_and_horizontal_bar_warn(self):
        text = RESUME.replace("AI ADOPTION PRODUCT MANAGER |", "AI ADOPTION PRODUCT MANAGER │")
        text = text.replace("April 2023 - July 2026", "April 2023 ― July 2026")
        r = check_parse([text], EXPECT)
        self.assertEqual(r["overall"], "WARN")
        details = " ".join(c["detail"] for c in r["checks"])
        self.assertIn("U+2502", details)
        self.assertIn("U+2015", details)
        # the horizontal-bar range still matches the expected dates after normalization
        self.assertFalse(any(c["check"] == "dates" and c["status"] == "FAIL" for c in r["checks"]))

    def test_missing_heading_and_garbled_text_fail(self):
        text = RESUME.replace("EDUCATION", "SCHOOLING") + "(cid:12)(cid:7)"
        r = check_parse([text], EXPECT)
        self.assertEqual(r["overall"], "FAIL")
        self.assertTrue(any(c["detail"] == "missing: EDUCATION" for c in r["checks"]))

    def test_merged_roles_flagged(self):
        # the parser-merge trap: second title survives but its dates float away from it
        text = RESUME.replace("Customer Success Manager  October 2019 - March 2023",
                              "Customer Success Manager\n\n\n\nfiller\nfiller\nOctober 2019 - March 2023")
        r = check_parse([text], EXPECT)
        self.assertTrue(any(c["check"] == "dates" and c["status"] == "WARN" for c in r["checks"]))

    def test_contact_missing_from_page_one(self):
        body = RESUME.replace("jordan@example.com | 555-010-0199\n", "")
        r = check_parse([body, "jordan@example.com | 555-010-0199"], EXPECT)
        self.assertEqual({c["check"] for c in r["checks"] if c["status"] == "FAIL"}, {"email", "phone"})

    def test_page_limit(self):
        r = check_parse([RESUME, "", ""], EXPECT)
        self.assertTrue(any(c["check"] == "pages" for c in r["checks"]))


class PagesTests(unittest.TestCase):
    def test_one_page_passes(self):
        self.assertEqual(check_pages(["Dear team,"], 1)["overall"], "PASS")

    def test_spilled_signature_warns_and_names_it(self):
        r = check_pages(["Dear team, ... I would welcome a conversation.", "Sincerely,\nJordan Example"], 1)
        self.assertEqual(r["overall"], "WARN")
        self.assertIn("Sincerely", r["checks"][0]["detail"])


def _write_pdf(path, lines):
    """Minimal single-page PDF with Helvetica text, one line per Td, valid xref offsets."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    ops = ["BT", "/F1 10 Tf", "14 TL", "50 750 Td"]
    for line in lines:
        ops += ["(%s) Tj" % esc(line), "T*"]
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path, "wb") as f:
        f.write(out)


@unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
class PdfRoundTripTests(unittest.TestCase):
    def test_real_pdf_extracts_and_passes(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.pdf")
            _write_pdf(path, [l for l in RESUME.splitlines()])
            pages = ats_check.extract_pdf(path)
            self.assertEqual(len(pages), 1)
            r = check_parse(pages, EXPECT)
            self.assertEqual(r["overall"], "PASS", r["checks"])


if __name__ == "__main__":
    unittest.main()
