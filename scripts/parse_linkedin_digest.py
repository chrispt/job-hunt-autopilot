#!/usr/bin/env python3
"""Parse LinkedIn job-alert digest emails into listings.

Replaces the prose parsing rules that accumulated in skills/daily-sweep/SKILL.md between
2026-08-02 and 2026-08-09 (badge shifts, thousands separators, the City-ST false positive).
See context/incident-log.md for each case.

Structure of a digest (plaintextBody): listings are blocks separated by a line of dashes.
Inside a block the non-empty lines run: title, company, location, [salary], [badge...],
"View job: <url>". The first block is preceded by header lines and later alert sections
are introduced by a <strong> line; those are stripped before indexing.

Two independent readings are taken per block: forward (title/company/location are the first
three surviving lines) and backward (the last three surviving lines before "View job" after
badge filtering). When they disagree, or a field fails a sanity check, the listing is kept
AND flagged for review. Flags are never silent discards.

CLI:
  parse_linkedin_digest.py FILE            FILE is plaintext, or the get_thread JSON result
  parse_linkedin_digest.py --transcript SESSION.jsonl   every get_thread digest in a transcript
  add --json for machine output
"""
import json
import re
import sys

SEPARATOR = re.compile(r"^-{10,}\s*$")
VIEW_JOB = re.compile(r"jobs/view/(\d+)")
HEADER_PATTERNS = [
    re.compile(p, re.I) for p in (
        r"^your job alert for ", r"new jobs? match your preferences", r"^manage (your )?(job )?alerts",
        r"^see all jobs", r"^edit alert", r"^new jobs from your other alerts", r"^<strong",
        r"^this email was intended", r"^learn why", r"^you are receiving", r"^unsubscribe",
        r"^©", r"linkedin and the linkedin logo", r"^results from the new ai-powered",
    )
]
# Badge / boilerplate lines that can sit between location and "View job". Counts may carry
# thousands separators ("1,717 company alumni"), hence [\d,]+.
BADGE_PATTERNS = [
    re.compile(p, re.I) for p in (
        r"^fast growing$", r"^actively recruiting$", r"^this company is actively hiring$",
        r"^[\d,]+\s+(company|school)\s+alum(ni)?$", r"^[\d,]+\s+connections?$",
        r"^be an early applicant$", r"^top applicant$", r"^promoted$", r"^easy apply$",
        r"^apply with resume & profile$", r"^\d+\s+applicants?$", r"^hiring now$",
    )
]
SALARY_LINE = re.compile(r"^\$[\d.,]+\s*[kK]?\s*(-|–|to)\s*\$[\d.,]+\s*[kK]?\s*/\s*(year|yr|hour|hr|month)", re.I)
US_STATES = set("""AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ
NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR VI GU""".split())
CITY_ST = re.compile(r"^(.+),\s*([A-Z]{2})$")
PLACE_WORDS = {"united states", "remote", "florida, united states", "new york, united states"}


URL_FRAGMENT = re.compile(r"^\S{30,}$")  # a long run with no whitespace
URL_TOKENS = re.compile(r"(&|=|%[0-9A-F]{2}|://|trk)", re.I)


def is_url_fragment(line: str) -> bool:
    """A wrapped continuation of a tracking URL (e.g. `5pB2bXnvTIo1&trk=eml-email_job_alert...`).
    Some digest templates wrap the header 'Manage alerts:' and 'See all jobs' links onto a
    second line; that fragment is not a header by wording and shifted every field by one
    on 2026-09-08 (6 listings across 2 digests). Also catches any bare URL line."""
    s = line.strip()
    if "://" in s and not VIEW_JOB.search(s):
        return True
    return bool(URL_FRAGMENT.match(s) and URL_TOKENS.search(s))


def is_header(line: str) -> bool:
    return any(p.search(line) for p in HEADER_PATTERNS) or is_url_fragment(line)


def is_badge(line: str) -> bool:
    return any(p.search(line) for p in BADGE_PATTERNS)


def looks_like_place(s: str) -> bool:
    s2 = s.strip()
    if s2.lower() in PLACE_WORDS or s2.lower().endswith(", united states"):
        return True
    m = CITY_ST.match(s2)
    return bool(m and m.group(2) in US_STATES)


def looks_like_badge_or_junk(s: str) -> bool:
    s2 = s.strip()
    return is_badge(s2) or bool(re.match(r"^\d", s2)) or s2.lower().startswith("apply with") or bool(SALARY_LINE.match(s2))


def alert_name_from(line: str):
    m = re.match(r"^your job alert for (.+?) in ", line, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"<strong[^>]*>(.+?)</strong>", line, re.I)
    if m:
        return m.group(1).strip()
    return None


def parse_digest(body: str) -> dict:
    listings, flagged, seen = [], [], set()
    alert = None
    blocks, cur = [], []
    for raw in body.splitlines():
        if SEPARATOR.match(raw):
            blocks.append(cur)
            cur = []
        else:
            cur.append(raw)
    blocks.append(cur)
    for block in blocks:
        lines = [l.strip() for l in block]
        for l in lines:
            n = alert_name_from(l)
            if n:
                alert = n
        view_idx = next((i for i, l in enumerate(lines) if VIEW_JOB.search(l)), None)
        if view_idx is None:
            continue
        m = VIEW_JOB.search(lines[view_idx])
        job_id = m.group(1)
        pre = [l for l in lines[:view_idx] if l and not is_header(l)]
        salary = next((l for l in pre if SALARY_LINE.match(l)), None)
        # forward reading
        fwd = (pre + ["", "", ""])[:3]
        # backward reading: drop badges and salary, take last three
        core = [l for l in pre if not is_badge(l) and not SALARY_LINE.match(l)]
        bwd = (["", "", ""] + core)[-3:]
        title, company, location = fwd
        reasons = []
        if fwd != bwd:
            reasons.append(f"forward/backward disagree: fwd={fwd} bwd={bwd}")
        if looks_like_place(title):
            reasons.append("title looks like a place")
        if company.lower() in PLACE_WORDS or company.lower().startswith("apply with"):
            reasons.append("company looks like a place/badge")
        if looks_like_badge_or_junk(location):
            reasons.append("location looks like a badge")
        if not (title and company and location):
            reasons.append("fewer than three fields")
        rec = {
            "job_id": job_id,
            "url": f"https://www.linkedin.com/jobs/view/{job_id}",
            "title": title, "company": company, "location": location,
            "salary": salary, "alert": alert, "source": "LinkedIn",
        }
        if job_id in seen:
            continue
        seen.add(job_id)
        if reasons:
            rec["flags"] = reasons
            flagged.append(rec)
        listings.append(rec)
    return {"listings": listings, "flagged": flagged, "count": len(listings)}


def bodies_from_text(txt: str):
    """Yield plaintext digest bodies from raw text or a get_thread JSON result."""
    try:
        obj = json.loads(txt)
    except Exception:
        yield txt
        return
    found = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "plaintextBody" and isinstance(v, str):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    if not found:
        yield txt
    for b in found:
        if "jobs/view/" in b:
            yield b


def _main(argv):
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if "--transcript" in argv:
        from audit import load_transcript, iter_tool_results  # local import keeps CLI light
        out = []
        for name, inp, txt, ts, err in iter_tool_results(load_transcript(args[0])):
            if "get_thread" in name and "jobs/view/" in txt:
                for body in bodies_from_text(txt):
                    r = parse_digest(body)
                    r["threadId"] = inp.get("threadId")
                    out.append(r)
        result = out
    else:
        txt = open(args[0], encoding="utf-8").read()
        result = [parse_digest(b) for b in bodies_from_text(txt)]
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        for r in result:
            print(f"# {r.get('threadId','')} {r['count']} listings, {len(r['flagged'])} flagged")
            for l in r["listings"]:
                flag = " [FLAG: " + "; ".join(l["flags"]) + "]" if l.get("flags") else ""
                print(f"- {l['title']} | {l['company']} | {l['location']} | {l['salary'] or ''} | {l['url']}{flag}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    _main(sys.argv[1:])
