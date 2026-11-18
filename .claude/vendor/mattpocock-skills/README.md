# Vendored: mattpocock/skills

Matt Pocock's [Skills For Real Engineers](https://github.com/mattpocock/skills), copied into `.claude/skills/` at the commit pinned in [`upstream.json`](./upstream.json). MIT licensed, see [`LICENSE`](./LICENSE).

## Rules

- **Don't edit the copied skill folders.** `scripts/update-mattpocock-skills.sh` deletes and re-copies every folder listed in `upstream.json` on each update, so local edits are lost.
- **Customise from the outside.** Bellosoft behaviour goes in files we own. Example: Jira support is the tracker file in `bellosoft-jira/references/matt-issue-tracker-jira.md`, which each project copies into `docs/agents/issue-tracker.md` (the extension point Matt's skills read).
- **To change a Matt skill's behaviour for good,** write our own skill under a different name instead of patching his.

## Updating

A weekly GitHub Action (`.github/workflows/update-mattpocock-skills.yml`) opens a PR when upstream has a new release. Review the diff and merge it when you want the update.

To update by hand, or to pin a specific tag, branch or commit:

```bash
scripts/update-mattpocock-skills.sh            # latest release tag
scripts/update-mattpocock-skills.sh v1.3.2     # specific ref
```

The script refuses to overwrite a skill Bellosoft owns that happens to share a name with a new upstream skill.
