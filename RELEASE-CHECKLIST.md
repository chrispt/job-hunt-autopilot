# Release checklist (maintainer only)

This tree is generated from the private source edition by `packaging/build_community.py`.
Never edit it by hand; edit the source, rebuild, and re-run the leak scan.

## History note

On 2026-10-06 the public history was squashed to a single commit after a sanitization pass
(employer names had reached the incident log and test data). Older tags and releases were
removed. Do not restore them from any local backup.

## Check a release the way a new user installs it

Before announcing a release, install it from the public repo into a throwaway Claude config so
your own setup is untouched (PowerShell shown; use `export` on macOS and Linux):

```
$env:CLAUDE_CONFIG_DIR = "$env:TEMP\claude-install-test"
claude plugin marketplace add chrispt/job-hunt-autopilot
claude plugin install job-search-agent@job-hunt-autopilot
claude plugin list
Remove-Item Env:CLAUDE_CONFIG_DIR
```

`claude plugin list` must show the new version. For a release that touches `scripts/userdata.py`, also simulate an update in the throwaway config (edit a personal file, bump the version, `claude plugin update`) and run `userdata.py apply` from the new folder: the edit must come back, and `userdata.py status` must report it saved. Then run `/setup-job-search` once on a clean
profile and fix anything it trips on. Donations go through Buy Me a Coffee (`DONATING.md` and
`.github/FUNDING.yml`); open https://buymeacoffee.com/chrispt once per release to confirm it
still resolves.

## Every later release

1. In the source edition: make the change, run `python -m unittest discover -s scripts/tests`,
   bump `version` in both `.claude-plugin/*.json` files (source and templates), add a
   `CHANGELOG.md` entry in the templates, commit.
2. `python packaging/build_community.py --out ../job-search-agent-community --zip`
   (fails on any leak; fix the redaction, never the output).
3. In this directory: review `git diff`, commit, tag `vX.Y.Z`, push with tags, attach the zip
   to the release.

## What never ships

`data/notion.json`, `data/pipeline-snapshot.json`, `runs/`, `data/locks/`, anything under
`~/.claude/`, the personal `context/candidate-profile.md`, and any transcript. The scan in
the builder is the last line of defence, not the first: keep personal facts in the personal
context files and `data/exclusions.md`, which the build replaces with templates.
