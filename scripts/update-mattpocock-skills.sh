#!/usr/bin/env bash
# Copy Matt Pocock's skills (https://github.com/mattpocock/skills) into .claude/skills/.
#
# Usage:
#   scripts/update-mattpocock-skills.sh          # latest upstream release tag
#   scripts/update-mattpocock-skills.sh v1.3.2   # a specific tag, branch or commit
#
# Takes exactly the skills listed in upstream's .claude-plugin/plugin.json (the
# engineering/ and productivity/ buckets), copies each one flat into
# .claude/skills/<name>/, and records the pinned commit in
# .claude/vendor/mattpocock-skills/upstream.json.
#
# Never edit the copied skill folders by hand: the next run overwrites them.
# Bellosoft customisation lives in our own skills (e.g. bellosoft-jira).
set -euo pipefail

UPSTREAM_URL="https://github.com/mattpocock/skills.git"
ROOT="$(git rev-parse --show-toplevel)"
SKILLS_DIR="$ROOT/.claude/skills"
VENDOR_DIR="$ROOT/.claude/vendor/mattpocock-skills"
LOCK="$VENDOR_DIR/upstream.json"

REF="${1:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SRC="$TMP/upstream"

echo "Fetching $UPSTREAM_URL ..."
git clone --quiet --filter=blob:none "$UPSTREAM_URL" "$SRC"

if [ -z "$REF" ]; then
    REF="$(git -C "$SRC" tag --list 'v*' --sort=-v:refname | head -n1)"
    if [ -z "$REF" ]; then
        echo "No release tags upstream; pass a ref explicitly." >&2
        exit 1
    fi
fi
git -C "$SRC" -c advice.detachedHead=false checkout --quiet "$REF"
COMMIT="$(git -C "$SRC" rev-parse HEAD)"

# Upstream's plugin manifest is the list of promoted skills. Validate every
# entry: it's data from another repo, and it decides which folders we write.
NEW_SKILLS="$(python3 -I - "$SRC/.claude-plugin/plugin.json" <<'PY'
import json, re, sys
manifest = json.load(open(sys.argv[1]))
for path in manifest["skills"]:
    m = re.fullmatch(r"\./skills/(engineering|productivity)/([a-z0-9][a-z0-9-]*)", path)
    if not m:
        sys.exit(f"Unexpected skill path in upstream plugin.json: {path!r}")
    print(f"{m.group(2)}\t{path[2:]}")
PY
)"
VERSION="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$SRC/.claude-plugin/plugin.json")"

OLD_SKILLS=""
if [ -f "$LOCK" ]; then
    OLD_SKILLS="$(python3 -I -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1]))["skills"]))' "$LOCK")"
fi

# Refuse to overwrite a skill we own that happens to share a name upstream.
while IFS=$'\t' read -r name _; do
    if [ -e "$SKILLS_DIR/$name" ] && ! grep -qxF "$name" <<<"$OLD_SKILLS"; then
        echo "Conflict: .claude/skills/$name already exists and is not a vendored skill." >&2
        echo "Rename one of them before updating." >&2
        exit 1
    fi
done <<<"$NEW_SKILLS"

# Remove the previous copy, so skills dropped upstream disappear here too.
while read -r name; do
    [ -n "$name" ] && rm -rf "${SKILLS_DIR:?}/$name"
done <<<"$OLD_SKILLS"

while IFS=$'\t' read -r name path; do
    cp -R "$SRC/$path" "$SKILLS_DIR/$name"
done <<<"$NEW_SKILLS"

mkdir -p "$VENDOR_DIR"
cp "$SRC/LICENSE" "$VENDOR_DIR/LICENSE"
cut -f1 <<<"$NEW_SKILLS" | python3 -I -c '
import json, sys
ref, commit, version, lock = sys.argv[1:5]
skills = [line.strip() for line in sys.stdin if line.strip()]
data = {
    "repository": "https://github.com/mattpocock/skills",
    "ref": ref,
    "commit": commit,
    "version": version,
    "skills": skills,
}
with open(lock, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
' "$REF" "$COMMIT" "$VERSION" "$LOCK"

echo "Vendored mattpocock/skills $REF (${COMMIT:0:7}, plugin v$VERSION): $(wc -l <<<"$NEW_SKILLS") skills."
echo "Review with: git status .claude/ && git diff --stat"
