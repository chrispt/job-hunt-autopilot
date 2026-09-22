#!/usr/bin/env python3
"""Extract discovery candidates from the session transcript (Indeed search results, LinkedIn
digest listings, LinkedIn single-job recommendation subjects). The model never transcribes
results by hand; this reads what the tools actually returned.

Usage: candidates.py [--transcript X.jsonl | auto-located] [--until-text TEXT] [--json]
Output records: {source, title, company, location, salary, url, posted, job_type, job_id,
                 alert, thread_id, needs_open}
"""
import argparse
import json
import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audit import default_transcript, load_transcript, iter_tool_results, classify_alert_subject  # noqa: E402
from parse_linkedin_digest import bodies_from_text, parse_digest  # noqa: E402

FIELD = re.compile(r"\*\*(Job Title|Job Id|Company|Location|Posted on|Job Type|Compensation|View Job URL):\*\*\s*(.*)")
# Only the "You may be a fit for X's Y role" shape is a real single-job recommendation, and
# audit.classify_alert_subject uses the same rule, so this is the only subject form that ever
# reaches parse_single_subject. A second, looser "<Role> at <Company>" pattern lived here until
# 2026-09-18; it matched multi-listing digests too and handed back the first listing as if it
# were the whole email, which is how those digests passed as fully-described singles.
SINGLE_SUBJECT = re.compile(r"^You may be a fit for (.+?)[’‘']s (.+?) role", re.I)


def parse_indeed(txt):
    try:
        body = json.loads(txt).get("result", "")
    except Exception:
        body = txt
    out, cur = [], {}
    for line in body.splitlines():
        m = FIELD.search(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if k == "Job Title" and cur:
            out.append(cur)
            cur = {}
        cur[k] = v
    if cur:
        out.append(cur)
    recs = []
    for r in out:
        recs.append({
            "source": "Indeed", "title": r.get("Job Title", ""), "company": r.get("Company", ""),
            "location": r.get("Location", ""), "salary": r.get("Compensation") if r.get("Compensation", "N/A") != "N/A" else None,
            "url": r.get("View Job URL", ""), "posted": r.get("Posted on"), "job_type": r.get("Job Type"),
            "job_id": r.get("Job Id"),
        })
    return recs


def parse_single_subject(subject):
    m = SINGLE_SUBJECT.match(subject or "")
    return {"company": m.group(1).strip(), "title": m.group(2).strip()} if m else None


def extract(recs, until_text=None, alert_sender="jobalerts-noreply@linkedin.com"):
    cands, seen = [], set()
    singles = {}
    opened = set()
    for name, inp, txt, ts, err in iter_tool_results(recs, until_text):
        if name.endswith("search_jobs"):
            for r in parse_indeed(txt):
                r["query"] = inp.get("search")
                r["query_location"] = inp.get("location")
                key = r["url"] or (r["company"], r["title"], r["location"])
                if key in seen:
                    continue
                seen.add(key)
                cands.append(r)
        elif name.endswith("search_threads"):
            try:
                for t in json.loads(txt).get("threads", []):
                    msgs = t.get("messages") or []
                    if not any(alert_sender in (m.get("sender") or "") for m in msgs):
                        continue
                    subj = msgs[0].get("subject") if msgs else ""
                    if classify_alert_subject(subj) == "single":
                        singles[t.get("id")] = subj
            except Exception:
                pass
        elif name.endswith("get_thread") and "jobs/view/" in txt:
            tid = inp.get("threadId")
            opened.add(tid)
            for body in bodies_from_text(txt):
                for l in parse_digest(body)["listings"]:
                    if l["job_id"] in seen:
                        continue
                    seen.add(l["job_id"])
                    rec = {"source": "LinkedIn", "title": l["title"], "company": l["company"], "location": l["location"],
                           "salary": l["salary"], "url": l["url"], "job_id": l["job_id"], "alert": l["alert"],
                           "thread_id": tid, "posted": None}
                    if l.get("flags"):
                        rec["parse_flags"] = l["flags"]
                    cands.append(rec)
    for tid, subj in singles.items():
        if tid in opened:
            continue
        p = parse_single_subject(subj)
        if p:
            cands.append({"source": "LinkedIn", "title": p["title"], "company": p["company"], "location": "", "salary": None,
                          "url": "", "thread_id": tid, "needs_open": True, "subject": subj, "posted": None})
    return cands


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--until-text")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    path = a.transcript or default_transcript()
    cands = extract(load_transcript(path), a.until_text)
    if a.json:
        print(json.dumps(cands, ensure_ascii=False, indent=1))
    else:
        by = {}
        for c in cands:
            by[c["source"]] = by.get(c["source"], 0) + 1
        print(f"# {len(cands)} candidates: " + ", ".join(f"{k} {v}" for k, v in by.items()))
        for c in cands:
            print(f"- [{c['source']}] {c['title']} | {c['company']} | {c['location']} | {c.get('salary') or ''} | {c.get('url') or ('thread ' + str(c.get('thread_id')))}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
