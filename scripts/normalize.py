#!/usr/bin/env python3
"""Shared name normalization for the job-search-agent plugin.

One implementation for every consumer (daily-sweep dedup, exclusion check, referral-match
join, apply-assist referral lookup). The rules used to be restated in prose in four files
and drifted; see context/incident-log.md#2026-08-09 (SHI International vs SHI International
Corp. duplicate).

CLI:  python normalize.py [--title] NAME [NAME ...]      (or names on stdin, one per line)
Lib:  from normalize import normalize_company, normalize_title, title_core
"""
import re
import sys

LEGAL_SUFFIXES = {
    "inc", "llc", "corp", "corporation", "co", "company", "ltd", "limited", "plc",
    "gmbh", "pty", "holdings", "lp", "llp", "sa", "ag", "nv", "bv",
}
# Tokens that describe level, not function. Dropped when comparing two titles for the
# SAME posting ("Senior AI Product Manager" == "AI Product Manager, Senior"). They are NOT
# dropped by screen.py, which needs them.
LEVEL_TOKENS = {"senior", "sr", "jr", "junior", "staff", "principal", "lead", "ii", "iii", "iv", "l4", "l5", "l6"}
REJECTION_PREFIX = "❌"  # the red X the pipeline prefixes onto rejected companies
_PUNCT = re.compile(r"[.,&™®'\"!?:;()\[\]{}/\|+*#@$%^~`<>=]")
_WS = re.compile(r"\s+")


def _basic(s: str) -> str:
    s = s.replace(REJECTION_PREFIX, " ")
    s = s.lower().strip()
    s = _PUNCT.sub(" ", s)
    s = s.replace("-", " ").replace("–", " ").replace(",", " ")
    return _WS.sub(" ", s).strip()


def normalize_company(name: str) -> str:
    """lowercase, strip the rejection prefix, drop punctuation, strip legal suffixes repeatedly."""
    if not name:
        return ""
    tokens = _basic(name).split(" ")
    while len(tokens) > 1 and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    # "the acme" == "acme"
    if len(tokens) > 1 and tokens[0] == "the":
        tokens = tokens[1:]
    return " ".join(tokens)


def normalize_title(title: str) -> str:
    """lowercase, drop punctuation, drop level tokens. Same function == same posting."""
    if not title:
        return ""
    tokens = [t for t in _basic(title).split(" ") if t and t not in LEVEL_TOKENS]
    return " ".join(tokens)


def title_core(title: str) -> str:
    """normalize_title with any trailing ', team' / ' - location' / '(qualifier)' segment removed.
    Two titles with the same core are PROBABLE duplicates (location/team variants of one
    function); callers should flag them for review, not auto-skip."""
    if not title:
        return ""
    t = re.sub(r"\([^)]*\)", " ", title)
    t = re.split(r"\s[-–,|]\s|,", t, maxsplit=1)[0]
    return normalize_title(t)


def same_company(a: str, b: str) -> bool:
    return normalize_company(a) == normalize_company(b)


def _main(argv):
    mode_title = "--title" in argv
    names = [a for a in argv if not a.startswith("--")]
    if not names:
        names = [line.rstrip("\n") for line in sys.stdin if line.strip()]
    fn = normalize_title if mode_title else normalize_company
    for n in names:
        print(fn(n))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    _main(sys.argv[1:])
