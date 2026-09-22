# Release checklist (maintainer only)

This tree is generated from the private source edition by `packaging/build_community.py`.
Never edit it by hand; edit the source, rebuild, and re-run the leak scan.

## First release

The public repository `chrispt/job-hunt-autopilot` already exists and holds the older
hand-made 0.1.0 template. This tree replaces its contents without rewriting its history.

1. From this directory: `git remote add origin https://github.com/chrispt/job-hunt-autopilot.git`,
   `git fetch origin`, then `git merge --allow-unrelated-histories -s ours origin/master`.
   The merge keeps this tree's files exactly and makes the public history an ancestor, so
   the push is a plain fast-forward (no force push).
2. `git push -u origin master --tags`. Update the repository description on GitHub to match
   `.claude-plugin/plugin.json`.
3. Enable GitHub Sponsors on the account (Settings → Sponsorship) so the link in
   `DONATING.md` resolves; add a one-time tier. If you prefer Ko-fi or Buy Me a Coffee,
   add the link to `DONATING.md` in the source templates and rebuild.
4. Create the GitHub release for the current tag and attach
   `job-search-agent-community-<version>.zip` (built by `build_community.py --zip`).
5. Paste `docs/LISTING.md` as the release description and, if you list it elsewhere
   (Gumroad "pay what you want", a personal site), as the product page.
6. Install it yourself from the public repo on a clean profile once:
   `/plugin marketplace add chrispt/job-hunt-autopilot`, then
   `/plugin install job-search-agent@job-hunt-autopilot`, then `/setup-job-search`.
   Fix anything the setup skill trips on before announcing it.

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
