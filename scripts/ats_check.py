#!/usr/bin/env python3
"""ATS screen-proofing checks for a tailored resume. A reporter, never a gate: exit code is 0
unless the arguments themselves are wrong.

  coverage  How many of the JD's own terms the resume carries, and in which section.
            Choosing the terms is a judgment call made in the skill (apply-assist step 5b);
            this only counts them, so the number is reproducible.
  parse     Extracts the PDF text the way a plain ATS parser would (pypdf) and checks that
            contact details, section headings, employers, titles and date ranges survive, and
            that each role's dates sit next to its title (the parser role-merge trap).
            pypdf is optional: without it the check reports SKIPPED and exits 0.
  pages     Page count only, for documents with no expect file (the cover letter must
            stay on one page; a signature spilled onto page 2 on 2026-09-22).

Usage:
  ats_check.py coverage --terms terms.json --text resume.(txt|docx|pdf)
                        [--baseline master.(txt|docx|pdf)] [--json]
  ats_check.py parse --pdf resume.pdf --expect data/resume-expect.json [--json]
  ats_check.py pages --pdf cover-letter.pdf [--max 1] [--json]

terms.json: a list of {"term": "...", "tier": "required|preferred|title", "aliases": [...]}.
expect.json: {"name", "email", "phone", "headings": [...], "max_pages": 2,
              "roles": [{"employer", "title", "dates"}]}
"""
import argparse
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree

TIERS = ("required", "preferred", "title")

# Section headings recognised when attributing a term to a part of the resume. Anything above
# the first recognised heading is "top" (name, headline, summary): where rankers look for title.
KNOWN_HEADINGS = {
    "summary": "summary", "professional summary": "summary", "profile": "summary",
    "core competencies": "competencies", "competencies": "competencies", "skills": "competencies",
    "technical skills": "competencies", "key skills": "competencies",
    "professional experience": "experience", "experience": "experience",
    "work experience": "experience",
    "education": "education",
    "independent project": "projects", "independent projects": "projects", "projects": "projects",
    "certifications": "certifications", "certification": "certifications",
}

MONTHS = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
          r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
DATE_RANGE = re.compile(MONTHS + r"\.?\s+(?:19|20)\d\d\s*(\S+?|to)\s*(?:" + MONTHS +
                        r"\.?\s+(?:19|20)\d\d|present|current)", re.I)
SAFE_SEPARATORS = {"-", "to"}

# glyph -> (severity, why)
GLYPHS = {
    "│": ("WARN", "box-drawing bar (U+2502); some parsers drop or garble it"),
    "―": ("WARN", "horizontal bar (U+2015); date parsers may not read it as a range"),
    "�": ("FAIL", "replacement character: text did not extract cleanly"),
    "(cid:": ("FAIL", "unmapped font glyphs (cid:...): text did not extract cleanly"),
}
LIGATURES = re.compile("[ﬀ-ﬆ]")


# ---------- text loading ----------

def read_docx(path):
    """Paragraph text from a .docx with the stdlib: body first, headers excluded."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    lines = []
    for p in root.iter(ns + "p"):
        parts = []
        for node in p.iter():
            if node.tag == ns + "t" and node.text:
                parts.append(node.text)
            elif node.tag == ns + "tab":
                parts.append("\t")
            elif node.tag in (ns + "br", ns + "cr"):
                parts.append("\n")
        lines.append("".join(parts))
    return "\n".join(lines)


def extract_pdf(path):
    """List of page texts, or None when pypdf is not installed."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    reader = PdfReader(path)
    return [(page.extract_text() or "") for page in reader.pages]


def load_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return read_docx(path)
    if ext == ".pdf":
        pages = extract_pdf(path)
        if pages is None:
            sys.exit("pypdf is not installed; pass a .txt or .docx, or pip install pypdf")
        return "\n".join(pages)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------- term matching ----------

def stem(token):
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith(("ches", "shes", "sses", "xes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def tokens(text):
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[\-‐-―/_|│]", " ", text)
    return [stem(t.rstrip(".")) for t in re.findall(r"[a-z0-9][a-z0-9+#.]*", text)]


def contains(haystack, needle):
    n = len(needle)
    if not n:
        return False
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def split_sections(text):
    """[(section, tokens)] in document order; the part before any known heading is 'top'."""
    sections, current, buf = [], "top", []
    for line in text.splitlines():
        key = re.sub(r"\s+", " ", line).strip().strip(":").lower()
        if key in KNOWN_HEADINGS:
            sections.append((current, tokens("\n".join(buf))))
            current, buf = KNOWN_HEADINGS[key], []
        else:
            buf.append(line)
    sections.append((current, tokens("\n".join(buf))))
    return sections


def match_terms(terms, text):
    sections = split_sections(text)
    results = []
    for t in terms:
        variants = [t["term"]] + list(t.get("aliases") or [])
        hit_sections, matched = [], None
        for v in variants:
            vt = tokens(v)
            for name, toks in sections:
                if contains(toks, vt):
                    matched = matched or v
                    if name not in hit_sections:
                        hit_sections.append(name)
        results.append({"term": t["term"], "tier": t.get("tier", "required"),
                        "found": bool(hit_sections), "matched": matched,
                        "sections": hit_sections})
    return results


def summarize(results):
    out = {}
    for tier in TIERS:
        rows = [r for r in results if r["tier"] == tier]
        found = sum(r["found"] for r in rows)
        out[tier] = {"found": found, "total": len(rows),
                     "pct": round(100 * found / len(rows)) if rows else None}
    titles = [r for r in results if r["tier"] == "title"]
    # Title wording counts only where a ranker reads it as a title: the top block (headline).
    out["title"]["hit"] = bool(titles) and all("top" in r["sections"] for r in titles)
    return out


def coverage(terms, text, baseline_text=None):
    for t in terms:
        if t.get("tier", "required") not in TIERS:
            raise ValueError("unknown tier %r for term %r" % (t.get("tier"), t.get("term")))
    results = match_terms(terms, text)
    report = {"summary": summarize(results), "terms": results}
    if baseline_text is not None:
        base = match_terms(terms, baseline_text)
        report["baseline"] = summarize(base)
        before = {r["term"] for r in base if r["found"]}
        after = {r["term"] for r in results if r["found"]}
        report["gained"] = sorted(after - before)
        report["lost"] = sorted(before - after)
    s = report["summary"]
    report["notes_line"] = "ATS terms: req %d/%d, pref %d/%d, title %s" % (
        s["required"]["found"], s["required"]["total"],
        s["preferred"]["found"], s["preferred"]["total"],
        "hit" if s["title"]["hit"] else "miss")
    return report


# ---------- parse check ----------

def _norm(s):
    s = s.lower()
    s = re.sub(r"[‐-―│|]", "-", s)
    s = re.sub(r"\s*-\s*", " - ", s)
    return re.sub(r"\s+", " ", s).strip()


def _digits(s):
    return re.sub(r"\D", "", s)


def check_parse(pages, expect):
    checks = []

    def add(status, check, detail):
        checks.append({"status": status, "check": check, "detail": detail})

    full = "\n".join(pages)
    nfull = _norm(full)
    lines = [l for l in full.splitlines() if l.strip()]
    nlines = [_norm(l) for l in lines]
    page1 = pages[0] if pages else ""

    # (a) contact details on page 1, name near the top
    top = " ".join(_norm(l) for l in page1.splitlines()[:6])
    if expect.get("name"):
        add("PASS" if _norm(expect["name"]) in top else "FAIL", "name",
            "name in the first lines of page 1" if _norm(expect["name"]) in top
            else "name not in the first lines of page 1 (header-only contact info is often dropped)")
    if expect.get("email"):
        ok = expect["email"].lower() in page1.lower().replace(" ", "")
        add("PASS" if ok else "FAIL", "email", "on page 1" if ok else "not found on page 1")
    if expect.get("phone"):
        ok = _digits(expect["phone"])[-10:] in _digits(page1)
        add("PASS" if ok else "FAIL", "phone", "on page 1" if ok else "not found on page 1")

    # (b) headings present. Order is not checked: tailoring may legitimately move a section
    # (one 2026-09-30 tailoring put INDEPENDENT PROJECT above experience); a scrambled layout shows up
    # in (c) as dates drifting away from their titles instead.
    missing = [h for h in expect.get("headings", []) if _norm(h) not in nfull]
    for h in missing:
        add("FAIL", "heading", "missing: %s" % h)
    if expect.get("headings") and not missing:
        add("PASS", "headings", "%d headings present" % len(expect["headings"]))

    # (c) each role's employer, title and dates, with the dates next to the title
    for role in expect.get("roles", []):
        label = "%s / %s" % (role.get("employer", "?"), role.get("title", "?"))
        if role.get("employer") and _norm(role["employer"]) not in nfull:
            add("FAIL", "employer", "missing: %s" % role["employer"])
        title = _norm(role.get("title", ""))
        idx = [i for i, l in enumerate(nlines) if title and title in l]
        if title and not idx:
            add("FAIL", "title", "missing: %s" % role["title"])
            continue
        dates = _norm(role.get("dates", ""))
        if not dates:
            continue
        if dates not in nfull:
            add("FAIL", "dates", "%s: date range '%s' not found" % (label, role["dates"]))
        elif idx and not any(dates in " ".join(nlines[max(0, i - 1):i + 3]) for i in idx):
            add("WARN", "dates", "%s: dates not adjacent to the title, a parser may pair them "
                "with the wrong role" % label)
        else:
            add("PASS", "role", label)

    # (d) date-range separators
    seps = sorted({m.group(1) for m in DATE_RANGE.finditer(full)
                   if m.group(1).lower() not in SAFE_SEPARATORS})
    if seps:
        add("WARN", "date separators", "non-hyphen date-range separators: %s (prefer a plain "
            "'-')" % ", ".join("%r U+%04X" % (s, ord(s[0])) for s in seps))

    # (e) suspicious glyphs
    for glyph, (sev, why) in GLYPHS.items():
        n = full.count(glyph)
        if n:
            add(sev, "glyph", "%s, %d occurrence(s)" % (why, n))
    lig = LIGATURES.findall(full)
    if lig:
        add("WARN", "glyph", "typographic ligatures (%d); words like 'office' may not match" % len(lig))

    # (f) page count
    max_pages = expect.get("max_pages", 2)
    if len(pages) > max_pages:
        add("WARN", "pages", "%d pages (expected at most %d)" % (len(pages), max_pages))

    statuses = {c["status"] for c in checks}
    overall = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"
    return {"overall": overall, "pages": len(pages), "checks": checks}


def check_pages(pages, max_pages):
    n = len(pages)
    if n > max_pages:
        tail = pages[-1].strip().splitlines()
        detail = "%d pages (expected at most %d); last page starts: %s" % (
            n, max_pages, tail[0][:60] if tail else "(blank)")
        return {"overall": "WARN", "pages": n, "checks": [{"status": "WARN", "check": "pages", "detail": detail}]}
    return {"overall": "PASS", "pages": n, "checks": [{"status": "PASS", "check": "pages", "detail": "%d page(s)" % n}]}


# ---------- CLI ----------

def print_coverage(r):
    s = r["summary"]
    for tier in TIERS:
        if s[tier]["total"]:
            line = "%-9s %d/%d (%s%%)" % (tier, s[tier]["found"], s[tier]["total"], s[tier]["pct"])
            if "baseline" in r:
                b = r["baseline"][tier]
                line += "   master %d/%d" % (b["found"], b["total"])
            print(line)
    if s["title"]["total"]:
        print("title in headline: %s" % ("hit" if s["title"]["hit"] else "miss"))
    missing = [t for t in r["terms"] if not t["found"]]
    for t in missing:
        print("  missing [%s] %s" % (t["tier"], t["term"]))
    if r.get("gained"):
        print("gained vs master: " + ", ".join(r["gained"]))
    if r.get("lost"):
        print("LOST vs master: " + ", ".join(r["lost"]))
    print(r["notes_line"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("coverage")
    c.add_argument("--terms", required=True)
    c.add_argument("--text", required=True)
    c.add_argument("--baseline")
    c.add_argument("--json", action="store_true")
    p = sub.add_parser("parse")
    p.add_argument("--pdf", required=True)
    p.add_argument("--expect", required=True)
    p.add_argument("--json", action="store_true")
    g = sub.add_parser("pages")
    g.add_argument("--pdf", required=True)
    g.add_argument("--max", type=int, default=1)
    g.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "coverage":
        with open(a.terms, encoding="utf-8") as f:
            terms = json.load(f)
        report = coverage(terms, load_text(a.text),
                          load_text(a.baseline) if a.baseline else None)
        print(json.dumps(report, indent=2, ensure_ascii=False)) if a.json else print_coverage(report)
        return 0

    expect = None
    if a.cmd == "parse":
        with open(a.expect, encoding="utf-8") as f:
            expect = json.load(f)
    pages = extract_pdf(a.pdf)
    if pages is None:
        report = {"overall": "SKIPPED", "pages": None,
                  "checks": [{"status": "SKIPPED", "check": "pypdf", "detail": "pypdf not installed"}]}
    elif a.cmd == "pages":
        report = check_pages(pages, a.max)
    else:
        report = check_parse(pages, expect)
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for chk in report["checks"]:
            if chk["status"] != "PASS":
                print("%-7s %-16s %s" % (chk["status"], chk["check"], chk["detail"]))
        print("%s %s (%s pages)" % (a.cmd, report["overall"], report["pages"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
