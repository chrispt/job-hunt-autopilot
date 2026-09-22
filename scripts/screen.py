#!/usr/bin/env python3
"""Intake screen for discovered roles: exclusion list, seniority, contact-center, comp floor,
Indeed recency. Rules live in data/screens.json and data/exclusions.md, not in prose.

Emits three buckets, each record carrying the rule ids that fired:
  keep     create the row (may carry notes such as tier-drop or below-floor-flag)
  flag     create the row but mark for a human glance: the seniority regex hit one of the
           documented false-positive classes (bank pay-grade VP, department name containing
           a rank word, "(Director)" suffix after the real job title), or a referral override
           applies. Never auto-discarded.
  discard  create no row; the report lists these with the rule so the guardrail stays auditable

Usage:  screen.py candidates.json [--screens data/screens.json] [--exclusions data/exclusions.md]
                  [--today YYYY-MM-DD] [--json]
Input record fields (all optional except title): title, company, location, salary, url,
source, posted (Indeed "Posted on" text), snippet, referral (bool), match (number).
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from normalize import normalize_company  # noqa: E402

MONEY = re.compile(r"\$?\s*([\d][\d,]*(?:\.\d+)?)\s*([kK])?")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_exclusions(path):
    """Company names from the markdown table in data/exclusions.md (first column of each row)."""
    names = set()
    if not path or not os.path.exists(path):
        return names
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or cells[0].lower() in ("company", "") or set(cells[0]) <= set("-: "):
                continue
            names.add(normalize_company(cells[0]))
    return names


def parse_salary(text):
    """Return (low, high, annual_high, unit) or None. Handles the shapes seen in Indeed results,
    Dice results and LinkedIn digest lines: `$50 - $100 an hour`, `$120,000 - $150,000 a year`,
    `$94K-$135K / year`, `USD 400,000.00 - 640,000.00 per year`, `From $X`, `Up to $X`,
    `$X a month`, `$X a day`, `N/A`."""
    if not text:
        return None
    t = text.replace("USD", "$").replace("–", "-")
    low = t.lower()
    if "n/a" in low and "$" not in low:
        return None
    nums = []
    for m in MONEY.finditer(t):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if m.group(2):
            v *= 1000
        if v < 10:  # stray digits, e.g. "5 days"
            continue
        nums.append(v)
    if not nums:
        return None
    nums = nums[:2]
    lo, hi = (nums[0], nums[-1]) if len(nums) == 2 else (nums[0], nums[0])
    if "hour" in low or "/hr" in low or " hr" in low:
        unit, mult = "hour", 2080
    elif "day" in low:
        unit, mult = "day", 260
    elif "month" in low:
        unit, mult = "month", 12
    elif "week" in low:
        unit, mult = "week", 52
    else:
        unit, mult = "year", 1
        # bare numbers under 1000 with no unit are almost certainly hourly ("$70 - $80")
        if hi < 1000:
            unit, mult = "hour", 2080
    return {"low": lo, "high": hi, "annual_high": hi * mult, "annual_low": lo * mult, "unit": unit}


def parse_posted(text):
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


class Screener:
    def __init__(self, screens, exclusions, today=None):
        self.s = screens
        self.excl = exclusions
        self.today = today or date.today()
        sen = screens["seniority"]
        self.discard_re = [re.compile(p, re.I) for p in sen["discard_patterns"]]
        self.flag_re = [re.compile(p, re.I) for p in sen["flag_patterns"]]
        self.keep_override_re = [re.compile(p, re.I) for p in sen["keep_override_patterns"]]
        self.paren_re = re.compile(sen["parenthetical_rank"], re.I)
        self.tier_re = [re.compile(p, re.I) for p in sen["tier_drop_patterns"]]
        self.pay_grade = set(sen["pay_grade_companies"])
        self.cc_kw = [k.lower() for k in screens["contact_center"]["keywords"]]

    def screen(self, c):
        title = (c.get("title") or "").strip()
        company = c.get("company") or ""
        ncomp = normalize_company(company)
        rules, notes = [], []
        bucket = "keep"

        def discard(rule):
            nonlocal bucket
            rules.append(rule)
            bucket = "discard"

        def flag(rule):
            nonlocal bucket
            rules.append(rule)
            if bucket != "discard":
                bucket = "flag"

        # 1. exclusion list (company-level deliberate passes)
        if ncomp and ncomp in self.excl:
            discard("exclusion-list")
        # 2. contact-center role keywords
        text = f"{title} {c.get('snippet') or ''}".lower()
        hit = next((k for k in self.cc_kw if k in text), None)
        if hit:
            discard(f"contact-center:{hit}")
        # 3. seniority
        if any(p.search(title) for p in self.keep_override_re):
            notes.append("rank word is a department name, kept")
        else:
            paren = self.paren_re.search(title)
            hard = [p.pattern for p in self.discard_re if p.search(title)]
            soft = [p.pattern for p in self.flag_re if p.search(title)]
            if paren:
                flag("seniority-parenthetical-rank")
            elif hard:
                if c.get("referral"):
                    flag("seniority-discard-referral-override")
                elif ncomp in self.pay_grade:
                    flag("seniority-pay-grade-company")
                else:
                    discard("seniority-discard:" + hard[0])
            elif soft:
                flag("seniority-ambiguous:" + soft[0])
            if any(p.search(title) for p in self.tier_re) and bucket != "discard":
                notes.append("tier-drop: title carries Principal/Staff/Group level; score 5-8 lower")
        # 4. comp
        sal = parse_salary(c.get("salary"))
        comp = self.s["comp"]
        if sal:
            c["salary_parsed"] = sal
            if sal["annual_high"] < comp["floor_annual"]:
                if (c.get("source") or "") in comp["hard_floor_sources"]:
                    discard(f"below-floor:{int(sal['annual_high'])}")
                else:
                    notes.append(f"below salary floor (top ~${int(sal['annual_high']):,}): bridge/foot-in-door, not a target match")
            elif sal["annual_high"] > comp["band_top_out_of_range"]:
                notes.append(f"band top ~${int(sal['annual_high']):,} is above ${comp['band_top_out_of_range']:,}: treat as out of range, score down")
            elif sal["annual_high"] >= comp["band_top_tier_drop"]:
                notes.append(f"band top ~${int(sal['annual_high']):,} is in the ${comp['band_top_tier_drop']:,}-{comp['band_top_out_of_range']:,} tier-drop range")
        # 5. Indeed recency (results can be months old; there is no posted-date parameter)
        if (c.get("source") or "") == "Indeed" and c.get("posted"):
            d = parse_posted(c["posted"])
            if d is not None:
                age = (self.today - d).days
                c["posted_age_days"] = age
                if age > self.s["recency"]["indeed_max_age_days"]:
                    discard(f"stale-posting:{age}d")
        # 6. standout (reported, never changes the bucket)
        if bucket != "discard":
            if c.get("referral"):
                notes.append("STANDOUT: referral contact at this company")
            if (c.get("match") or 0) >= self.s["standout"]["match_threshold"]:
                notes.append(f"STANDOUT: match {c.get('match')}% >= {self.s['standout']['match_threshold']}")
        out = dict(c)
        out["bucket"] = bucket
        out["rules"] = rules
        out["notes"] = notes
        return out

    def screen_all(self, cands):
        res = {"keep": [], "flag": [], "discard": []}
        for c in cands:
            r = self.screen(c)
            res[r["bucket"]].append(r)
        res["counts"] = {k: len(res[k]) for k in ("keep", "flag", "discard")}
        return res


def render(res):
    L = [f"## Intake screen: {res['counts']['keep']} keep, {res['counts']['flag']} flag for review, {res['counts']['discard']} discarded"]
    for r in res["discard"]:
        L.append(f"- DISCARD {r.get('company')} | {r.get('title')} | {', '.join(r['rules'])}")
    for r in res["flag"]:
        L.append(f"- FLAG {r.get('company')} | {r.get('title')} | {', '.join(r['rules'])} | {'; '.join(r['notes'])}")
    for r in res["keep"]:
        if r["notes"]:
            L.append(f"- keep {r.get('company')} | {r.get('title')} | {'; '.join(r['notes'])}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--screens", default=os.path.join(HERE, "..", "data", "screens.json"))
    ap.add_argument("--exclusions", default=os.path.join(HERE, "..", "data", "exclusions.md"))
    ap.add_argument("--today")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else None
    cands = load_json(a.candidates)
    if isinstance(cands, dict):
        cands = cands.get("candidates") or cands.get("listings") or []
    res = Screener(load_json(a.screens), load_exclusions(a.exclusions), today).screen_all(cands)
    print(json.dumps(res, ensure_ascii=False, indent=1) if a.json else render(res))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
