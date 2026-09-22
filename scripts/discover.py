#!/usr/bin/env python3
"""One-shot discovery pipeline: transcript -> candidates -> screen -> dedup -> run files.

The sweep skill calls this ONCE after the Indeed searches and the LinkedIn digest reads have
been issued. It writes everything under <plugin>/runs/<date>/ and prints a single report
plus the one SQL confirmation query the skill runs next. Nothing here calls Notion.

  runs/<date>/candidates.json   every result the tools returned (Indeed + LinkedIn)
  runs/<date>/screened.json     keep / flag / discard with rule ids
  runs/<date>/dedup.json        new / duplicate after the local join, plus the SQL
  runs/<date>/to_score.json     the rows the model must score and create (keep + flag, new)

Usage: discover.py [--transcript X.jsonl] [--recent recent_rows.json] [--today YYYY-MM-DD] [--run-dir DIR]
"""
import argparse
import json
import os
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audit import default_transcript, load_transcript  # noqa: E402
from candidates import extract  # noqa: E402
from screen import Screener, load_exclusions, load_json  # noqa: E402
import dedup_query  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--until-text")
    ap.add_argument("--recent", help="notion_rows.py --json output for the 'Added last 7 days' view")
    ap.add_argument("--snapshot", default=os.path.join(HERE, "..", "data", "pipeline-snapshot.json"))
    ap.add_argument("--screens", default=os.path.join(HERE, "..", "data", "screens.json"))
    ap.add_argument("--exclusions", default=os.path.join(HERE, "..", "data", "exclusions.md"))
    ap.add_argument("--today")
    ap.add_argument("--run-dir")
    a = ap.parse_args(argv)
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else date.today()
    run_dir = a.run_dir or os.path.join(HERE, "..", "runs", today.isoformat())
    os.makedirs(run_dir, exist_ok=True)

    path = a.transcript or default_transcript()
    cands = extract(load_transcript(path), a.until_text)
    with open(os.path.join(run_dir, "candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(cands, fh, ensure_ascii=False, indent=1)

    screened = Screener(load_json(a.screens), load_exclusions(a.exclusions), today).screen_all(cands)
    with open(os.path.join(run_dir, "screened.json"), "w", encoding="utf-8") as fh:
        json.dump(screened, fh, ensure_ascii=False, indent=1)

    rows = dedup_query.load(a.snapshot) + dedup_query.load(a.recent)
    # collapse the same posting repeated per city (Indeed lists one req under several locations)
    survivors, seen = [], {}
    for r in screened["keep"] + screened["flag"]:
        k = (dedup_query.normalize_company(r.get("company") or ""), dedup_query.title_core(r.get("title") or ""))
        if k in seen:
            seen[k].setdefault("also_locations", []).append(r.get("location"))
            continue
        seen[k] = r
        survivors.append(r)
    dd = dedup_query.dedup(survivors, rows)
    dd["sql"] = dedup_query.sql_for(dd["new"])
    dd["sources"] = {"snapshot_rows": len(dedup_query.load(a.snapshot)), "recent_rows": len(dedup_query.load(a.recent))}
    with open(os.path.join(run_dir, "dedup.json"), "w", encoding="utf-8") as fh:
        json.dump(dd, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(run_dir, "to_score.json"), "w", encoding="utf-8") as fh:
        json.dump(dd["new"], fh, ensure_ascii=False, indent=1)

    by = {}
    for c in cands:
        by[c["source"]] = by.get(c["source"], 0) + 1
    print(f"## Discovery pipeline ({today.isoformat()}, run dir {os.path.abspath(run_dir)})")
    print(f"- Candidates from tool results: {len(cands)} (" + ", ".join(f"{k} {v}" for k, v in by.items()) + ")")
    print(f"- Screen: keep {screened['counts']['keep']}, flag {screened['counts']['flag']}, discard {screened['counts']['discard']}; "
          f"{len(survivors)} distinct survivors after collapsing repeated postings")
    stale = [r for r in screened["discard"] if all(x.startswith("stale-posting") for x in r["rules"])]
    if stale:
        print(f"  - {len(stale)} Indeed results discarded only for age (posted more than {load_json(a.screens)['recency']['indeed_max_age_days']} days ago); "
              f"full list in screened.json")
    for r in screened["discard"]:
        rules = [x for x in r["rules"] if not x.startswith("stale-posting")]
        if rules:
            print(f"  - DISCARD {r.get('company')} | {r.get('title')} | {', '.join(rules)}")
    for r in screened["flag"]:
        print(f"  - FLAG (create, but confirm) {r.get('company')} | {r.get('title')} | {', '.join(r['rules'])} | {'; '.join(r['notes'])}")
    print(f"- Dedup against {dd['sources']['snapshot_rows']} snapshot + {dd['sources']['recent_rows']} recent rows: "
          f"{len(dd['duplicate'])} duplicates, {len(dd['new'])} still new")
    if not rows:
        print("  - WARNING: no local pipeline rows were available (snapshot missing and no --recent file). "
              "Every survivor is unverified until the confirmation SQL below succeeds. NO DEDUP READ, NO CREATES.")
    for d in dd["duplicate"]:
        print(f"  - dup {d.get('company')} | {d.get('title')} == {d['duplicate_of']['role']} [{d['duplicate_of']['status']}]")
    needs_open = [n for n in dd["new"] if n.get("needs_open")]
    if needs_open:
        print(f"- {len(needs_open)} single-job alert emails passed the subject screen and must be opened (get_thread) for their URL before scoring:")
        for n in needs_open:
            print(f"  - thread {n['thread_id']}: {n['title']} | {n['company']}")
    print(f"- To score and create: {len(dd['new'])} rows -> {os.path.join(os.path.abspath(run_dir), 'to_score.json')}")
    for n in dd["new"]:
        sal = f" | {n.get('salary')}" if n.get("salary") else ""
        notes = f" | {'; '.join(n['notes'])}" if n.get("notes") else ""
        print(f"  - {n.get('company')} | {n.get('title')} | {n.get('location')}{sal} | {n.get('url') or 'needs_open'}{notes}")
    s = dd["sql"]
    print(f"\nConfirmation SQL ({s['distinct_companies']} companies, {s['in_list_size']} spellings). Run it ONCE; any returned row whose "
          f"normalized company+title matches a to_score row is a duplicate and must not be created:\n{s['sql']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
