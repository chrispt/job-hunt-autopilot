#!/usr/bin/env python3
"""Compact rows out of a Notion query result (inline JSON or a spilled tool-result file).

Why: view-mode results return every property including multi-kilobyte Notes, and SHOW does
not shrink the payload, so a 100-row page is ~100-300K characters. The harness spills
oversized results to a file; this script reads that file and prints only the fields a
skill needs, plus `days_old` computed from `Created` (formula values come back as opaque
formulaResult:// references in view mode, so age is derived here instead).

Usage: notion_rows.py FILE [--fields Company,Role,...] [--limit N] [--json] [--count]
       [--today YYYY-MM-DD]
"""
import argparse
import json
import re
import sys
from datetime import date, datetime

DEFAULT_FIELDS = ["Company", "Role", "Status", "Priority", "Match %", "Source", "Job URL", "Created", "Packet Ready",
                  "Date Applied", "Follow Up Date", "Outreach Sent", "Application Confirmed", "url"]


def load_result(path):
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    # spilled files may carry a preamble line before the JSON
    start = txt.find("{")
    obj = json.loads(txt[start:]) if start >= 0 else {}
    return obj


def flatten(row):
    out = {}
    for k, v in row.items():
        if k.startswith("date:") and k.endswith(":start"):
            out[k[5:-6]] = v
        elif k.startswith("date:"):
            continue
        else:
            out[k] = v
    return out


def days_old(created, today):
    if not created:
        return None
    try:
        d = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
    except ValueError:
        return None
    return (today - d).days


def compact(obj, fields, today, limit=None):
    rows = obj.get("results") or obj.get("rows") or []
    out = []
    for r in rows[: limit or len(rows)]:
        f = flatten(r)
        rec = {k: f.get(k) for k in fields if k in f}
        rec["days_old"] = days_old(f.get("Created"), today)
        if isinstance(rec.get("Notes"), str):
            rec["Notes"] = re.sub(r"\s+", " ", rec["Notes"])[:300]
        out.append(rec)
    return out, obj.get("has_more"), obj.get("next_cursor")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--fields", default=",".join(DEFAULT_FIELDS))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--today")
    a = ap.parse_args(argv)
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else date.today()
    obj = load_result(a.file)
    rows, more, cursor = compact(obj, [x.strip() for x in a.fields.split(",")], today, a.limit)
    if a.count:
        print(json.dumps({"rows": len(obj.get("results") or []), "has_more": more, "next_cursor": cursor}))
        return
    if a.json:
        print(json.dumps({"rows": rows, "has_more": more, "next_cursor": cursor}, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(" | ".join(f"{k}={r[k]}" for k in r if r[k] not in (None, "", "__NO__")))
        print(f"# {len(rows)} rows shown; has_more={more}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
