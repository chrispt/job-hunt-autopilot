#!/usr/bin/env python3
"""Audit a sweep run from its own session transcript.

The transcript (~/.claude/projects/<project>/<session>.jsonl) is written per tool call by
the harness and cannot be edited by the model, so it is ground truth for what a run did.
This script derives, with zero model involvement:
  - which Indeed (query, location) searches were issued and how many results each returned,
    against the expected set in data/queries.json for the run mode (full | light | skip)
  - LinkedIn alert digests returned by search_threads vs actually opened by get_thread, and
    how many listings each opened digest parsed to
  - every Notion create-pages payload, with a provenance check: the row's Job URL (LinkedIn
    job id or Indeed short link) must appear in an earlier tool result in this transcript
  - Notion read call counts by mode (quota exposure) and every quota / missing-tool error
It prints the "Discovery coverage" block for the report with a digest line so a hand-written
block is detectable, and exits non-zero when coverage is incomplete or a create lacks
provenance.

Usage (inside a run):   python audit.py --mode full            (transcript auto-located)
Historical:             python audit.py --transcript X.jsonl --until-text "Daily Job Sweep" --json
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parse_linkedin_digest import bodies_from_text, parse_digest  # noqa: E402

QUOTA_RE = re.compile(r"usage limit for Query Data Source|used all of your plan.s free data source queries|reached the usage limit", re.I)
NO_TOOL_RE = re.compile(r"No such tool available", re.I)
PRECOND_RE = re.compile(r"Precondition check failed", re.I)
BLOCK_QUOTA_RE = re.compile(r"keep creating content with Notion MCP through|block limit|Upgrade your plan before", re.I)
LI_ID = re.compile(r"jobs/view/(\d+)")
INDEED_LINK = re.compile(r"to\.indeed\.com/([A-Za-z0-9]+)")
INDEED_JOBID = re.compile(r"\*\*Job Id:\*\*\s*(\S+)")


def project_slug(cwd: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def default_transcript() -> str:
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        raise SystemExit("CLAUDE_CODE_SESSION_ID not set; pass --transcript")
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects", project_slug(os.getcwd()))
    path = os.path.join(base, sid + ".jsonl")
    if not os.path.exists(path):
        hits = glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl"))
        if hits:
            return hits[0]
        raise SystemExit(f"transcript not found: {path}")
    return path


def load_transcript(path: str, include_subagents: bool = True):
    recs = []
    paths = [path]
    if include_subagents:
        sid = os.path.splitext(os.path.basename(path))[0]
        paths += sorted(glob.glob(os.path.join(os.path.dirname(path), sid, "**", "*.jsonl"), recursive=True))
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                try:
                    recs.append(json.loads(line))
                except Exception:
                    continue
    recs.sort(key=lambda r: r.get("timestamp") or "")
    return recs


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def iter_tool_results(recs, until_text=None):
    """Yield (tool_name, input, result_text, timestamp, is_error) in transcript order."""
    pending = {}
    for r in recs:
        msg = r.get("message") or {}
        content = msg.get("content")
        if r.get("type") == "assistant" and isinstance(content, list) and until_text:
            for b in content:
                if b.get("type") == "text" and until_text in b.get("text", "") and len(b.get("text", "")) > 1200:
                    return
        if not isinstance(content, list):
            continue
        for b in content:
            if b.get("type") == "tool_use":
                pending[b["id"]] = (b.get("name", "?"), b.get("input") or {}, r.get("timestamp"))
            elif b.get("type") == "tool_result":
                name, inp, ts = pending.get(b.get("tool_use_id"), ("?", {}, r.get("timestamp")))
                yield name, inp, text_of(b.get("content")), r.get("timestamp") or ts, bool(b.get("is_error"))


def load_queries(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def expected_pairs(q, mode):
    if mode == "skip":
        return set()
    if mode == "light":
        ids = set(q["light_mode"]["query_ids"])
        locs = q["light_mode"]["locations"]
        return {norm_pair(x["search"], loc) for x in q["queries"] if x["id"] in ids for loc in locs}
    return {norm_pair(x["search"], loc) for x in q["queries"] for loc in q["locations"]}


def norm_search(search):
    s = re.sub(r"[\"“”']", "", search or "")
    return re.sub(r"\s+", " ", s).strip().lower()


def search_key(search):
    """Order-insensitive token set with the OR operator removed. Used to MATCH an issued
    search to its expected query even when the model reworded it. Wording drift is still
    reported (see `wording_differs`): on 2026-09-07 the model issued
    `ai enablement ai adoption` for `"AI Enablement" OR "AI Adoption"`; Indeed reads plain
    words as AND, and that search returned 1 result instead of the usual ~10."""
    toks = [t for t in re.findall(r"[a-z0-9]+", norm_search(search)) if t != "or"]
    return frozenset(toks)


def norm_pair(search, location):
    return (norm_search(search), (location or "").strip().lower())


SINGLE_SUBJECT = re.compile(r"^You may be a fit for .+?[’‘']s .+? role", re.I)


def classify_alert_subject(subject) -> str:
    """'single' = a one-job recommendation ("You may be a fit for X's Y role"), fully described
    by its subject, so it can be screened without opening. EVERYTHING ELSE is a 'digest': a
    multi-listing alert email that must be opened, because its subject names only the first of
    six or so listings. A missing subject (search_threads with view THREAD_VIEW_METADATA_ONLY
    omits it) lands here too, and is flagged rather than trusted.

    The default is deliberately 'digest' (inverted 2026-09-18). It used to be 'single': anything
    that did not look like a digest was assumed to be fully described by its subject. LinkedIn
    then started sending digests titled "<Company> is hiring a <Role>" and "<Role> at <Company>";
    21 arrived in one sweep, every one was classified single, none was opened, and ~75% of that
    day's listings were lost while audit.py still printed OK. Misreading a digest as a single
    loses listings silently. Misreading a single as a digest costs one get_thread and parses
    correctly anyway. So when in doubt, open it."""
    return "single" if subject and SINGLE_SUBJECT.search(subject) else "digest"


def merge_subject(known: dict, tid, subject) -> None:
    """Record a thread's subject without letting a later subject-less record (a metadata-only
    page) erase a known one; a later record that does carry a subject fills the gap."""
    if subject or tid not in known:
        known[tid] = subject


def count_indeed_results(txt: str) -> int:
    if "No job results found" in txt:
        return 0
    return len(re.findall(r"\*\*Job Title:\*\*", txt))


def audit(recs, queries, mode="full", until_text=None, alert_sender=None):
    alert_sender = alert_sender or queries.get("linkedin_alert_sender", "jobalerts-noreply@linkedin.com")
    out = {
        "mode": mode, "indeed": {}, "indeed_unexpected": [], "digests": {}, "creates": [],
        "notion_reads": {"sql": 0, "rows": 0, "view": 0, "database_view": 0}, "notion_writes": 0,
        "errors": [], "first_ts": None, "last_ts": None,
    }
    seen_li_ids, seen_indeed = set(), set()
    returned_digests = {}
    thread_subjects = {}  # subjects from get_thread, to fill ones a metadata-only search omitted
    for name, inp, txt, ts, is_err in iter_tool_results(recs, until_text):
        out["first_ts"] = out["first_ts"] or ts
        out["last_ts"] = ts
        low = txt[:600]
        if QUOTA_RE.search(low):
            out["errors"].append({"class": "notion-query-quota", "tool": name, "ts": ts, "text": txt[:160]})
        elif BLOCK_QUOTA_RE.search(low):
            out["errors"].append({"class": "notion-block-quota", "tool": name, "ts": ts, "text": txt[:160]})
        elif NO_TOOL_RE.search(low):
            out["errors"].append({"class": "no-such-tool", "tool": name, "ts": ts, "text": txt[:160]})
        elif PRECOND_RE.search(low):
            out["errors"].append({"class": "gmail-precondition", "tool": name, "ts": ts, "text": txt[:160]})
        elif is_err:
            out["errors"].append({"class": "other", "tool": name, "ts": ts, "text": txt[:160]})
        if name.endswith("search_jobs"):
            key = norm_pair(inp.get("search"), inp.get("location"))
            n = count_indeed_results(txt)
            rec = out["indeed"].setdefault("|".join(key), {"search": key[0], "location": key[1], "calls": 0, "results": 0, "error": False})
            rec["calls"] += 1
            rec["results"] = max(rec["results"], n)
            rec["error"] = rec["error"] or is_err
            seen_indeed.update(INDEED_LINK.findall(txt))
            seen_indeed.update(INDEED_JOBID.findall(txt))
            for m in re.finditer(r"\*\*View Job URL:\*\*\s*(\S+)", txt):
                seen_indeed.add(m.group(1))
        elif name.endswith("search_threads"):
            try:
                obj = json.loads(txt)
                for t in obj.get("threads", []):
                    msgs = t.get("messages") or []
                    if any(alert_sender in (m.get("sender") or "") for m in msgs):
                        merge_subject(returned_digests, t.get("id"), next((m.get("subject") for m in msgs if m.get("subject")), None))
            except Exception:
                pass
        elif name.endswith("get_thread"):
            tid = inp.get("threadId")
            try:
                msgs = json.loads(txt).get("messages") or []
                merge_subject(thread_subjects, tid, next((m.get("subject") for m in msgs if m.get("subject")), None))
            except Exception:
                pass
            if "jobs/view/" in txt:
                n_list, n_flag = 0, 0
                for body in bodies_from_text(txt):
                    r = parse_digest(body)
                    n_list += r["count"]
                    n_flag += len(r["flagged"])
                    seen_li_ids.update(l["job_id"] for l in r["listings"])
                out["digests"][tid] = {"opened": True, "listings": n_list, "flagged": n_flag, "ts": ts}
            seen_li_ids.update(LI_ID.findall(txt))
        elif "notion-query-data-sources" in name:
            data = inp.get("data")
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            m = ((data or {}).get("mode") if isinstance(data, dict) else None) or "sql"
            out["notion_reads"][m if m in out["notion_reads"] else "sql"] += 1
        elif "notion-query-database-view" in name:
            out["notion_reads"]["database_view"] += 1
        elif "notion-create-pages" in name:
            for p in (inp.get("pages") or []):
                props = p.get("properties") or {}
                url = props.get("Job URL") or ""
                prov = None
                m = LI_ID.search(url)
                if m and m.group(1) in seen_li_ids:
                    prov = f"linkedin:{m.group(1)}"
                elif url and (url in seen_indeed or any(k and k in url for k in seen_indeed)):
                    prov = "indeed:" + url
                out["creates"].append({
                    "company": props.get("Company"), "role": props.get("Role"), "status": props.get("Status"),
                    "source": props.get("Source"), "url": url, "provenance": prov, "ts": ts,
                })
            out["notion_writes"] += len(inp.get("pages") or [])
        elif "notion-update-page" in name:
            out["notion_writes"] += 1
    # second pass for generic URL provenance (employer/ATS URLs surfaced inside digests or search results)
    unresolved = [c for c in out["creates"] if c["url"] and not c["provenance"]]
    if unresolved:
        blob = []
        for name, inp, txt, ts, is_err in iter_tool_results(recs, until_text):
            if name.endswith("search_jobs") or name.endswith("get_thread") or "get_job_details" in name:
                blob.append(txt)
        blob = "\n".join(blob)
        for c in unresolved:
            if c["url"] in blob:
                c["provenance"] = "url-in-result"
    for tid, subj in returned_digests.items():
        subj = subj or thread_subjects.get(tid)
        out["digests"].setdefault(tid, {"opened": False, "listings": 0, "flagged": 0, "ts": None})
        out["digests"][tid]["subject"] = subj
        out["digests"][tid]["kind"] = classify_alert_subject(subj)
    for d in out["digests"].values():
        d.setdefault("kind", "digest")
    # coverage vs expected: match on token set, then note any wording drift
    exp = expected_pairs(queries, mode)
    exp_by_key = {(search_key(s), l): (s, l) for (s, l) in exp}
    matched, wording = set(), []
    for v in out["indeed"].values():
        k = (search_key(v["search"]), v["location"])
        if k in exp_by_key:
            matched.add(exp_by_key[k])
            v["expected_search"] = exp_by_key[k][0]
            if v["search"] != exp_by_key[k][0]:
                wording.append(f"issued `{v['search']}` for `{exp_by_key[k][0]}` @ {v['location']} ({v['results']} results)")
    out["indeed_expected"] = len(exp)
    out["indeed_missing"] = sorted(f"{s} @ {l}" for (s, l) in exp - matched)
    out["indeed_unexpected"] = sorted(f"{v['search']} @ {v['location']}" for v in out["indeed"].values() if (search_key(v["search"]), v["location"]) not in exp_by_key)
    out["wording_differs"] = wording
    out["digests_returned"] = sum(1 for d in out["digests"].values() if d["kind"] == "digest")
    out["digests_opened"] = sum(1 for d in out["digests"].values() if d["opened"] and d["kind"] == "digest")
    out["digests_unopened"] = [f"{tid} ({(d.get('subject') or 'no subject')[:60]})" for tid, d in out["digests"].items() if not d["opened"] and d["kind"] == "digest"]
    out["singles_returned"] = sum(1 for d in out["digests"].values() if d["kind"] == "single")
    out["singles_opened"] = sum(1 for d in out["digests"].values() if d["opened"] and d["kind"] == "single")
    out["singles_unopened"] = [f"{tid} ({(d.get('subject') or 'no subject')[:70]})" for tid, d in out["digests"].items() if not d["opened"] and d["kind"] == "single"]
    out["creates_total"] = len(out["creates"])
    out["creates_no_provenance"] = [c for c in out["creates"] if not c["provenance"]]
    out["creates_null_status"] = [c for c in out["creates"] if not c["status"]]
    canon = json.dumps({
        "mode": mode, "indeed": sorted((v["search"], v["location"]) for v in out["indeed"].values()), "digests_opened": sorted(t for t, d in out["digests"].items() if d["opened"]),
        "creates": [c["url"] for c in out["creates"]],
    }, sort_keys=True)
    out["digest"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:8]
    out["ok"] = not out["indeed_missing"] and not out["digests_unopened"] and not out["creates_no_provenance"] and not out["creates_null_status"]
    return out


def render(out) -> str:
    L = []
    L.append("## Discovery coverage (generated by scripts/audit.py, do not hand-edit)")
    L.append(f"- Mode: **{out['mode']}**. Indeed searches issued: {len(out['indeed'])} of {out['indeed_expected']} expected"
             + (" (all present)" if not out["indeed_missing"] else f"; **MISSING {len(out['indeed_missing'])}**"))
    for m in out["indeed_missing"]:
        L.append(f"  - missing: {m}")
    for u in out["indeed_unexpected"]:
        L.append(f"  - unexpected (not in queries.json): {u}")
    if out.get("wording_differs"):
        L.append(f"  - **{len(out['wording_differs'])} searches issued with wording that differs from queries.json** (OR dropped or reordered; Indeed reads plain words as AND, which narrows results). Issue the query text verbatim.")
        for w in out["wording_differs"]:
            L.append(f"    - {w}")
    zero = [f"{v['search']} @ {v['location']}" for v in out["indeed"].values() if v["results"] == 0]
    if zero:
        L.append(f"  - {len(zero)} searches returned 0 results: " + "; ".join(zero))
    errs = [f"{v['search']} @ {v['location']}" for v in out["indeed"].values() if v["error"]]
    if errs:
        L.append("  - searches that errored: " + "; ".join(errs))
    L.append(f"- LinkedIn alert digests: {out['digests_returned']} returned by search_threads, {out['digests_opened']} opened, "
             f"{sum(d['listings'] for d in out['digests'].values())} listings parsed, "
             f"{sum(d['flagged'] for d in out['digests'].values())} flagged for review"
             + ("" if not out["digests_unopened"] else f"; **UNOPENED {len(out['digests_unopened'])}**"))
    for u in out["digests_unopened"]:
        L.append(f"  - unopened: {u}")
    if out.get("singles_returned"):
        L.append(f"- LinkedIn single-job recommendation emails: {out['singles_returned']} returned, {out['singles_opened']} opened "
                 f"(the subject names the role and company; screen from the subject, open only survivors)")
        for u in out["singles_unopened"]:
            L.append(f"  - not opened: {u}")
    L.append(f"- Rows created: {out['creates_total']}; without provenance: {len(out['creates_no_provenance'])}; null Status: {len(out['creates_null_status'])}")
    for c in out["creates_no_provenance"]:
        L.append(f"  - **NO PROVENANCE**: {c['company']} | {c['role']} | {c['url']}")
    for c in out["creates_null_status"]:
        L.append(f"  - **NULL STATUS**: {c['company']} | {c['role']}")
    nr = out["notion_reads"]
    L.append(f"- Notion reads: sql {nr['sql']}, rows {nr['rows']}, view {nr['view'] + nr['database_view']} (quota-exempt); writes {out['notion_writes']}")
    by = {}
    for e in out["errors"]:
        by.setdefault(e["class"], []).append(e)
    if by:
        L.append("- Errors: " + "; ".join(f"{k} x{len(v)} (first {v[0]['ts']})" for k, v in by.items()))
    else:
        L.append("- Errors: none")
    L.append(f"- coverage-digest: {out['digest']}  {'OK' if out['ok'] else 'INCOMPLETE'}  ({out['first_ts']} → {out['last_ts']})")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--mode", default="full", choices=["full", "light", "skip"])
    ap.add_argument("--queries", default=os.path.join(HERE, "..", "data", "queries.json"))
    ap.add_argument("--until-text", default=None, help="stop at the first long assistant message containing this text")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-subagents", action="store_true")
    a = ap.parse_args(argv)
    path = a.transcript or default_transcript()
    recs = load_transcript(path, include_subagents=not a.no_subagents)
    out = audit(recs, load_queries(a.queries), mode=a.mode, until_text=a.until_text)
    out["transcript"] = path
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    else:
        print(render(out))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
