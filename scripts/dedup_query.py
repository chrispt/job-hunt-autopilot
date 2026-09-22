#!/usr/bin/env python3
"""Dedup discovered candidates against the pipeline, and build the SQL fallback.

Two local sources are joined first (zero Notion quota):
  - data/pipeline-snapshot.json   whole-table snapshot {company, role, status, url, id},
                                  refreshed by funnel-review (weekly)
  - a recent-rows file            output of notion_rows.py --json on the "⚙ Added last 7 days"
                                  view, covering rows newer than the snapshot
Then the script emits the one SQL query the skill runs to confirm anything still marked new
(every raw spelling plus the normalized base in the IN list, with the count assertion the
prose used to describe). Status is deliberately NOT filtered: Withdrawn, Rejected and Aged Out
rows still block a re-add.

Match rules (same as the prose they replace):
  same LinkedIn job id / same URL                     -> duplicate
  same company AND same normalized title              -> duplicate
  same company AND same title core (location/team
      variant of one function)                        -> duplicate
  same company, genuinely different function          -> new (note the sibling row)

Usage: dedup_query.py candidates.json [--snapshot data/pipeline-snapshot.json] [--recent recent.json] [--json]
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from normalize import normalize_company, normalize_title, title_core  # noqa: E402

LI_ID = re.compile(r"jobs/view/(\d+)")


def load(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    if isinstance(obj, dict):
        obj = obj.get("rows") or obj.get("results") or obj.get("candidates") or obj.get("listings") or []
    return obj


def key_url(u):
    if not u:
        return None
    m = LI_ID.search(u)
    return f"li:{m.group(1)}" if m else u.strip().rstrip("/").lower()


def index_rows(rows):
    by_url, by_company = {}, {}
    for r in rows:
        company = r.get("Company") or r.get("company") or ""
        role = r.get("Role") or r.get("role") or r.get("title") or ""
        url = r.get("Job URL") or r.get("url") or r.get("job_url") or ""
        status = r.get("Status") or r.get("status") or ""
        rec = {"company": company, "role": role, "url": url, "status": status, "id": r.get("id") or r.get("url")}
        k = key_url(url)
        if k:
            by_url[k] = rec
        by_company.setdefault(normalize_company(company), []).append(rec)
    return by_url, by_company


def dedup(cands, rows):
    by_url, by_company = index_rows(rows)
    out = {"new": [], "duplicate": [], "unverified": []}
    for c in cands:
        title = c.get("title") or c.get("role") or ""
        company = c.get("company") or ""
        k = key_url(c.get("url"))
        hit, why = None, None
        if k and k in by_url:
            hit, why = by_url[k], "same url"
        else:
            for r in by_company.get(normalize_company(company), []):
                if normalize_title(r["role"]) == normalize_title(title):
                    hit, why = r, "same company + title"
                    break
                if title_core(r["role"]) and title_core(r["role"]) == title_core(title):
                    hit, why = r, "same company + title core (location/team variant)"
                    break
        rec = dict(c)
        if hit:
            rec["duplicate_of"] = {"company": hit["company"], "role": hit["role"], "status": hit["status"], "id": hit["id"]}
            rec["why"] = why
            out["duplicate"].append(rec)
        else:
            sib = by_company.get(normalize_company(company), [])
            if sib:
                rec["sibling_rows"] = [f"{s['role']} ({s['status']})" for s in sib[:5]]
            out["new"].append(rec)
    return out


def default_data_source():
    """collection:// URL from data/notion.json (single source for Notion ids)."""
    p = os.path.join(HERE, "..", "data", "notion.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return "collection://" + json.load(fh)["data_source_id"]
    except Exception:
        return "collection://<data_source_id from data/notion.json>"


def sql_for(cands, data_source=None):
    """Fallback/confirmation query covering every candidate company under every known spelling."""
    data_source = data_source or default_data_source()
    names = []
    for c in cands:
        raw = (c.get("company") or "").strip()
        if not raw:
            continue
        for v in (raw, normalize_company(raw), normalize_company(raw).title()):
            if v and v not in names:
                names.append(v)
    quoted = ", ".join("'" + n.replace("'", "''") + "'" for n in names)
    sql = (f'SELECT Company, Role, Status, "Job URL" FROM "{data_source}" '
           f"WHERE LOWER(TRIM(REPLACE(Company, '❌', ''))) IN ({', '.join('LOWER(' + repr(n) + ')' for n in names)})")
    return {"in_list": names, "distinct_companies": len({normalize_company(c.get('company') or '') for c in cands if c.get('company')}),
            "in_list_size": len(names), "sql": sql, "simple_in": quoted}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--snapshot", default=os.path.join(HERE, "..", "data", "pipeline-snapshot.json"))
    ap.add_argument("--recent")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cands = load(a.candidates)
    rows = load(a.snapshot) + load(a.recent)
    res = dedup(cands, rows)
    res["sources"] = {"snapshot_rows": len(load(a.snapshot)), "recent_rows": len(load(a.recent))}
    res["sql"] = sql_for(res["new"])
    res["counts"] = {"candidates": len(cands), "new": len(res["new"]), "duplicate": len(res["duplicate"])}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"## Dedup: {res['counts']['candidates']} candidates, {res['counts']['new']} new, {res['counts']['duplicate']} duplicates "
              f"(joined against {res['sources']['snapshot_rows']} snapshot + {res['sources']['recent_rows']} recent rows)")
        if not rows:
            print("- WARNING: no local rows to join against; every candidate is 'new' until the SQL confirmation runs. No dedup read, no creates.")
        for d in res["duplicate"]:
            print(f"- dup {d.get('company')} | {d.get('title')} == {d['duplicate_of']['role']} [{d['duplicate_of']['status']}] ({d['why']})")
        for n in res["new"]:
            sib = f"  (sibling rows: {'; '.join(n['sibling_rows'])})" if n.get("sibling_rows") else ""
            print(f"- new {n.get('company')} | {n.get('title')}{sib}")
        s = res["sql"]
        print(f"\nConfirmation SQL covers {s['distinct_companies']} distinct companies with {s['in_list_size']} spellings:\n{s['sql']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
