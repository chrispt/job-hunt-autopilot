#!/usr/bin/env python3
"""Keep a user's personal plugin files across plugin updates.

Setup writes a user's profile, Notion ids, queries and screens into the plugin folder, because
that copy is the one that runs. `claude plugin update` installs a new version folder, so those
files used to be left behind. This script keeps them in Claude Code's persistent per-plugin data
folder (~/.claude/plugins/data/<plugin>-<marketplace>/, which survives updates) and puts them
back in each new version folder. Skills and scripts keep reading their usual paths.

  apply   session start: save unsaved edits, then restore the saved files into this folder
  save    end of turn: copy any personal file edited in this folder to the data folder
  status  show what is saved, what is edited and not yet saved, and what is template-only
  import  PATH   adopt personal files from an earlier install folder (a 0.2.x setup)

Which files count as personal is listed in data/userdata-files.json. An edition without that
file (the maintainer's own) is untouched: every command is then a no-op.

Safety rule: save only runs for a folder that apply has already restored. Otherwise a fresh
template, after an update whose restore step never ran, would overwrite the saved copy.
"""
import hashlib
import json
import os
import re
import shutil
import sys

LIST_REL = "data/userdata-files.json"
MANIFEST = "manifest.json"


def plugin_root():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def data_dir(root):
    """The persistent folder, or None when this copy is not an installed plugin.

    Same folder Claude Code exports to hooks as CLAUDE_PLUGIN_DATA, derived from the install path
    when that variable is absent (commands Claude runs through its Bash tool do not receive it)."""
    for var in ("JOB_SEARCH_DATA_DIR", "CLAUDE_PLUGIN_DATA"):
        if os.environ.get(var):
            return os.path.abspath(os.environ[var])
    parts = os.path.abspath(root).replace("\\", "/").split("/")
    # .../plugins/cache/<marketplace>/<plugin>/<version>
    if len(parts) >= 5 and parts[-4] == "cache" and parts[-5] == "plugins":
        ident = re.sub(r"[^A-Za-z0-9_-]", "-", f"{parts[-2]}@{parts[-3]}")
        return os.path.normpath(os.path.join("/".join(parts[:-4]), "data", ident))
    return None


def load_files(root):
    path = os.path.join(root, LIST_REL)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("files") or []


def sha(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".tmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def load_manifest(data):
    try:
        with open(os.path.join(data, MANIFEST), encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        m = {}
    m.setdefault("files", {})
    return m


def write_manifest(data, m):
    os.makedirs(data, exist_ok=True)
    tmp = os.path.join(data, MANIFEST + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(data, MANIFEST))


def _same(a, b):
    return os.path.normcase(os.path.abspath(a or "")) == os.path.normcase(os.path.abspath(b or ""))


def _save(root, data, files, m):
    saved = []
    for rel in files:
        cur = sha(os.path.join(root, rel))
        rec = m["files"].setdefault(rel, {})
        if cur and cur != rec.get("applied_sha"):
            copy(os.path.join(root, rel), os.path.join(data, rel))
            rec["applied_sha"] = cur
            saved.append(rel)
    return saved


def save(root=None):
    """Copy personal files edited in this folder to the data folder. Returns what was saved."""
    root = root or plugin_root()
    files, data = load_files(root), data_dir(root)
    if files is None or not data:
        return []
    m = load_manifest(data)
    if not _same(m.get("applied_root"), root):
        return []  # apply has not restored this folder yet; saving now could clobber saved files
    saved = _save(root, data, files, m)
    if saved:
        write_manifest(data, m)
    return saved


def _earlier_installs(root):
    parent = os.path.dirname(os.path.abspath(root))
    try:
        sibs = [os.path.join(parent, d) for d in os.listdir(parent)]
    except OSError:
        return []
    sibs = [s for s in sibs if os.path.isdir(s) and not _same(s, root)]
    return sorted(sibs, key=lambda s: os.path.getmtime(s), reverse=True)


def apply(root=None):
    """Restore saved personal files into this folder. Returns notices worth showing the user."""
    root = root or plugin_root()
    files, data = load_files(root), data_dir(root)
    if files is None or not data:
        return []
    notes = []
    os.makedirs(data, exist_ok=True)
    first_ever = not os.path.exists(os.path.join(data, MANIFEST))
    m = load_manifest(data)
    if _same(m.get("applied_root"), root):
        _save(root, data, files, m)            # a new session in the same folder: keep unsaved edits
        for rel in files:                      # then pick up anything changed in the data folder
            user = os.path.join(data, rel)
            if sha(user) and sha(user) != sha(os.path.join(root, rel)):
                copy(user, os.path.join(root, rel))
                m["files"].setdefault(rel, {})["applied_sha"] = sha(os.path.join(root, rel))
    else:                                      # first run, or a new version folder after an update
        changed = []
        for rel in files:
            rec = m["files"].setdefault(rel, {})
            template_now = sha(os.path.join(root, rel))
            user = os.path.join(data, rel)
            if sha(user):
                if rec.get("template_sha") and template_now and rec["template_sha"] != template_now:
                    changed.append(rel)
                copy(user, os.path.join(root, rel))
            rec["template_sha"] = template_now
            rec["applied_sha"] = sha(os.path.join(root, rel))
        m["applied_root"] = os.path.abspath(root)
        if changed:
            notes.append("userdata: this release changed " + ", ".join(changed) + " (your saved copies are in use; "
                         "read CHANGELOG.md and merge the new defaults by hand if they matter to you).")
    if first_ever and not m.get("notified_import"):
        earlier = _earlier_installs(root)
        if earlier:
            m["notified_import"] = True
            notes.append("userdata: earlier install folders exist (" + ", ".join(os.path.basename(e) for e in earlier[:3])
                         + "). If you set this plugin up in one of them, run: python \"" + os.path.join(root, "scripts", "userdata.py")
                         + "\" import \"" + earlier[0] + "\"")
    write_manifest(data, m)
    return notes


def import_from(root, src):
    """Adopt personal files from an earlier install folder. Only files that differ from this
    folder's current copy are taken, so untouched templates are not mistaken for personal data."""
    files, data = load_files(root), data_dir(root)
    if files is None or not data:
        return []
    imported = []
    for rel in files:
        s = os.path.join(src, rel)
        if sha(s) and sha(s) != sha(os.path.join(root, rel)):
            copy(s, os.path.join(data, rel))
            imported.append(rel)
    apply(root)
    return imported


def status(root=None):
    root = root or plugin_root()
    files, data = load_files(root), data_dir(root)
    if files is None:
        return "userdata: inactive (this edition keeps personal files in the plugin folder itself)"
    if not data:
        return "userdata: inactive (this folder is not an installed plugin copy)"
    m = load_manifest(data)
    lines = [f"userdata: data folder {data}",
             f"userdata: restored into this folder: {'yes' if _same(m.get('applied_root'), root) else 'NO (run apply)'}"]
    for rel in files:
        r, d = sha(os.path.join(root, rel)), sha(os.path.join(data, rel))
        applied = m["files"].get(rel, {}).get("applied_sha")
        if not d and r and r != applied:
            state = "edited here, not yet saved"
        elif not d:
            state = "template only (no personal copy yet)"
        elif r and r != applied:
            state = "edited here, not yet saved"
        elif r == d:
            state = "saved and in sync"
        else:
            state = "data folder is newer (run apply)"
        lines.append(f"  {rel}: {state}")
    return "\n".join(lines)


def main(argv):
    cmd = argv[0] if argv else "status"
    root = plugin_root()
    if cmd == "apply":
        for n in apply(root):
            print(n)
    elif cmd == "save":
        for rel in save(root):
            print(f"userdata: saved {rel}", file=sys.stderr)
    elif cmd == "status":
        print(status(root))
    elif cmd == "import" and len(argv) > 1:
        done = import_from(root, argv[1])
        print("userdata: imported " + (", ".join(done) if done else "nothing (no differing personal files found)"))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
