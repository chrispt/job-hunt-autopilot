#!/usr/bin/env python3
"""Single-instance lock for scheduled runs, replacing the `isRunning` session check.

The old guard deferred whenever another "Daily job sweep" session was running, but sweep
sessions stay open for hours while the candidate works in them, so a session left open overnight
deferred the next morning's run. This lock is time-bounded instead: a lock older than
--stale-hours is treated as abandoned.

Usage:
  lock.py acquire <task> --session <id> [--stale-hours 3]   exit 0 = acquired, exit 1 = held
  lock.py release <task> --session <id>
  lock.py status  <task>
Lock files live in <plugin>/data/locks/<task>.lock (gitignored).
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK_DIR = os.path.join(HERE, "..", "data", "locks")


def path_for(task):
    os.makedirs(LOCK_DIR, exist_ok=True)
    return os.path.join(LOCK_DIR, f"{task}.lock")


def read(task):
    p = path_for(task)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def acquire(task, session, stale_hours):
    now = datetime.now(timezone.utc)
    cur = read(task)
    if cur:
        try:
            ts = datetime.fromisoformat(cur["acquired_at"])
        except Exception:
            ts = now - timedelta(hours=stale_hours + 1)
        if cur.get("session") != session and now - ts < timedelta(hours=stale_hours):
            print(f"held: {task} locked by session {cur.get('session')} since {cur['acquired_at']} (stale after {stale_hours}h)")
            return 1
        if cur.get("session") != session:
            print(f"note: stale lock from session {cur.get('session')} at {cur['acquired_at']} replaced")
    with open(path_for(task), "w", encoding="utf-8") as fh:
        json.dump({"task": task, "session": session, "acquired_at": now.isoformat()}, fh)
    print(f"acquired: {task} by {session} at {now.isoformat()}")
    return 0


def release(task, session):
    cur = read(task)
    if cur and cur.get("session") not in (None, session):
        print(f"not released: {task} is held by {cur.get('session')}, not {session}")
        return 1
    try:
        os.remove(path_for(task))
    except FileNotFoundError:
        pass
    print(f"released: {task}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["acquire", "release", "status"])
    ap.add_argument("task")
    ap.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown"))
    ap.add_argument("--stale-hours", type=float, default=3)
    a = ap.parse_args(argv)
    if a.action == "acquire":
        return acquire(a.task, a.session, a.stale_hours)
    if a.action == "release":
        return release(a.task, a.session)
    cur = read(a.task)
    print(json.dumps(cur) if cur else f"free: {a.task}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
