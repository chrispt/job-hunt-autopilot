#!/usr/bin/env python3
"""Age-out pass for the "To Apply" queue: the hybrid split productized from the 2026-09-10
one-off run (see runs/2026-09-10/ageout_hybrid_result.json for the run this replaces).

Policy (data/screens.json "age_out", mirrored in context/notion-schema.md): a "To Apply" row
is aged-out eligible if Created <= today-<aged_out_days> (default 60), OR Created <=
today-<borderline_days> (default 45) AND Match % < <borderline_match_floor> (default 70). The
"⚙ Age-out candidates" saved view (data/notion.json "age_out_candidates") already applies that
OR filter server-side; the funnel-review skill is responsible for keeping its two absolute
dates current via notion-update-view before querying it (view DSL has no relative dates -- see
notion-schema.md), the same way daily-sweep refreshes "⚙ Fresh queue" each run.

This script does no Notion I/O and calls no MCP tool. It is pure JSON-in, JSON-out, in two
phases:

Phase 1 (split) -- given the view's export, split by Match %:
  - < borderline_match_floor  -> aged_out_direct: safe to write Status=Aged Out immediately,
    no Notes annotation needed (self-describing, per the existing Aged Out convention).
  - >= borderline_match_floor -> borderline: the view's OR clause only lets a
    >=floor-match row through via the "60+ days old" branch (the 45-day branch requires
    match < floor), so every borderline row is old but well-matched -- worth a live JD check
    before a date rule kills it. Run the JD read ladder (context/config.md) on these; that
    step needs live tools this script does not have, so it belongs to the calling skill, not
    here.

Phase 2 (apply-verdicts) -- once the skill has a verdict per borderline row from the JD
ladder, feed those back to classify the final write:
  - closed / confirmed_dead -> propose_withdrawn: batch for the candidate's confirmation (never
    auto-written) with the evidence, per the "propose, never auto-apply" convention.
  - open / still_open       -> left_untouched: no write; reported so the candidate sees it was
    checked and cleared, not silently skipped.
  - inconclusive (or anything else, including a missing verdict) -> aged_out_fallback:
    write Status=Aged Out (self-describing, no Notes). Matches the JD ladder's own rule that
    an empty/unreadable render is never a closed signal and must never produce a Withdrawn.

Usage:
  age_out.py candidates.json [--policy data/screens.json] [--today YYYY-MM-DD] [--json]
      Phase 1. candidates.json is scripts/notion_rows.py output (or a bare list / {"rows":
      [...]}) queried from the "⚙ Age-out candidates" view. Needs Company, Role, Match %,
      Job URL, url per row (Created/days_old are carried through for the report but not
      re-derived here -- notion_rows.py already computed days_old).

  age_out.py --verdicts verdicts.json [--json]
      Phase 2. verdicts.json is a list of {company, role, match (or match_pct), job_url,
      notion_url (or url), verdict, evidence, rung} records, one per borderline row Phase 1
      emitted, filled in by the skill after running the JD read ladder.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_POLICY = {"aged_out_days": 60, "borderline_days": 45, "borderline_match_floor": 70}
CLOSED_VERDICTS = {"closed", "confirmed_dead", "dead"}
OPEN_VERDICTS = {"open", "still_open"}


def load_policy(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return {**DEFAULT_POLICY, **(json.load(fh).get("age_out") or {})}
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_POLICY)


def load_rows(path):
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    if isinstance(obj, dict):
        obj = obj.get("rows") or obj.get("results") or []
    return obj


def _get(row, *names):
    for n in names:
        v = row.get(n)
        if v not in (None, ""):
            return v
    return None


def split(rows, match_floor):
    """Phase 1: bucket the (already policy-filtered) view export by Match %."""
    direct, borderline = [], []
    for r in rows:
        match = _get(r, "Match %", "match", "match_pct") or 0
        rec = {
            "company": _get(r, "Company", "company"),
            "role": _get(r, "Role", "role"),
            "match_pct": match,
            "job_url": _get(r, "Job URL", "job_url"),
            "notion_url": _get(r, "url", "notion_url"),
            "days_old": _get(r, "days_old", "Days Old"),
        }
        if match < match_floor:
            rec["action"] = "aged_out_direct"
            direct.append(rec)
        else:
            rec["action"] = "needs_jd_ladder"
            borderline.append(rec)
    return direct, borderline


def apply_verdicts(verdicts):
    """Phase 2: turn the skill's JD-ladder findings into the three write buckets."""
    withdraw, left_open, fallback = [], [], []
    for v in verdicts:
        verdict = (v.get("verdict") or "").strip().lower()
        rec = {
            "company": v.get("company"),
            "role": v.get("role"),
            "match_pct": _get(v, "match", "match_pct"),
            "job_url": v.get("job_url"),
            "notion_url": _get(v, "notion_url", "url"),
            "evidence": v.get("evidence"),
            "rung": v.get("rung"),
        }
        if verdict in CLOSED_VERDICTS:
            rec["action"] = "propose_withdrawn"
            withdraw.append(rec)
        elif verdict in OPEN_VERDICTS:
            rec["action"] = "leave_untouched"
            left_open.append(rec)
        else:  # inconclusive, unrecognized, or missing -- never treated as a closed signal
            rec["action"] = "aged_out_fallback"
            fallback.append(rec)
    return withdraw, left_open, fallback


def render_split(direct, borderline, floor):
    L = [f"## Age-out split: {len(direct)} direct (Match % < {floor}), "
         f"{len(borderline)} borderline (needs JD read ladder before any write)"]
    for r in direct:
        L.append(f"- AGED OUT (direct) {r['company']} | {r['role']} | {r['match_pct']}%")
    for r in borderline:
        L.append(f"- CHECK JD {r['company']} | {r['role']} | {r['match_pct']}% | {r['job_url']}")
    return "\n".join(L)


def render_verdicts(withdraw, left_open, fallback):
    L = [f"## Verdicts applied: {len(withdraw)} propose Withdrawn, {len(left_open)} left open, "
         f"{len(fallback)} inconclusive -> Aged Out fallback"]
    for r in withdraw:
        L.append(f"- WITHDRAW? {r['company']} | {r['role']} | {r['evidence']}")
    for r in left_open:
        L.append(f"- still open {r['company']} | {r['role']}")
    for r in fallback:
        L.append(f"- AGED OUT (fallback, inconclusive) {r['company']} | {r['role']}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", nargs="?", help="notion_rows.py export of the Age-out candidates view")
    ap.add_argument("--verdicts", help="phase 2: JD-ladder verdicts for the borderline rows from phase 1")
    ap.add_argument("--policy", default=os.path.join(HERE, "..", "data", "screens.json"))
    ap.add_argument("--today", help="unused by the split itself (the view is pre-filtered); kept for parity with the other scripts' --today flag")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    policy = load_policy(a.policy)

    if a.verdicts:
        withdraw, left_open, fallback = apply_verdicts(load_rows(a.verdicts))
        out = {
            "propose_withdrawn": withdraw,
            "left_untouched": left_open,
            "aged_out_fallback": fallback,
            "counts": {"withdraw": len(withdraw), "left_open": len(left_open), "fallback": len(fallback)},
        }
        print(json.dumps(out, ensure_ascii=False, indent=1) if a.json else render_verdicts(withdraw, left_open, fallback))
        return

    if not a.candidates:
        ap.error("candidates.json is required unless --verdicts is given")
    rows = load_rows(a.candidates)
    floor = policy["borderline_match_floor"]
    direct, borderline = split(rows, floor)
    out = {
        "aged_out_direct": direct,
        "borderline": borderline,
        "policy": policy,
        "counts": {"total": len(rows), "direct": len(direct), "borderline": len(borderline)},
    }
    print(json.dumps(out, ensure_ascii=False, indent=1) if a.json else render_split(direct, borderline, floor))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
