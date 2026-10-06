#!/usr/bin/env python3
"""Merge compacted view pages (notion_rows.py --json output) into data/pipeline-snapshot.json.

Usage: snapshot_build.py PAGE.json [PAGE.json ...] [--out data/pipeline-snapshot.json]
Dedups by page url, reports row count and the Created date range covered, and keeps any
existing snapshot rows whose url is not in the new pages (so a partial refresh never shrinks
coverage).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "pipeline-snapshot.json"))
    ap.add_argument("--replace", action="store_true", help="drop existing snapshot rows instead of merging")
    a = ap.parse_args(argv)
    rows = {}
    if os.path.exists(a.out) and not a.replace:
        with open(a.out, encoding="utf-8") as fh:
            for r in json.load(fh).get("rows", []):
                rows[r.get("url")] = r
    added = 0
    for p in a.pages:
        with open(p, encoding="utf-8") as fh:
            for r in json.load(fh).get("rows", []):
                rec = {k: r.get(k) for k in ("Company", "Role", "Status", "Job URL", "url", "Created")}
                if rec["url"] not in rows:
                    added += 1
                rows[rec["url"]] = rec
    out = sorted(rows.values(), key=lambda r: r.get("Created") or "")
    created = [r["Created"] for r in out if r.get("Created")]
    meta = {"rows": len(out), "created_min": min(created) if created else None, "created_max": max(created) if created else None,
            "built": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "rows": out}, fh, ensure_ascii=False)
    print(f"snapshot: {meta['rows']} rows ({added} new), Created {meta['created_min']} .. {meta['created_max']} -> {os.path.abspath(a.out)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
