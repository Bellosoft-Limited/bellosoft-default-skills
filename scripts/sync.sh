#!/bin/bash
set -e

REPO="https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
TMP=$(mktemp -d)

# Folders to sync from company core into each client repo.
# NOTE: .github/core/ and .github/stack/ are subfolders of .github/ and synced automatically.
SYNC_FOLDERS=(
    ".github"           # Copilot instructions, agents, prompts, skills, hooks, workflows, core, stack
    "_bmad"             # BMAD methodology config
    ".vscode"           # VS Code settings (chat.* configs)
)

# Path prefixes that the sync script will NEVER overwrite.
PROTECTED_PREFIXES=(
    ".github/skills/bmad-tea"
    ".github/skills/reports"
    ".github/CODEOWNERS"          # Each client may have their own
)

files_equal() {
    local a b
    a=$(tr -d '\r' < "$1" | md5sum)
    b=$(tr -d '\r' < "$2" | md5sum)
    [ "$a" = "$b" ]
}

is_protected() {
    local rel_norm="$1"
    for prefix in "${PROTECTED_PREFIXES[@]}"; do
        if [[ "$rel_norm" == "$prefix" || "$rel_norm" == "$prefix/"* ]]; then
            return 0
        fi
    done
    return 1
}

sync_folder() {
    local src_base="$1"
    local dest_base="$2"
    local log_label="$3"
    [ -d "$src_base" ] || return 0

    find "$src_base" -type f | while read -r src; do
        rel="${src#$src_base/}"
        dest="$dest_base/$rel"
        rel_norm="$log_label/$rel"

        if is_protected "$rel_norm"; then
            echo "     ⏭ Skipping $rel_norm (protected)"
            continue
        fi

        if [ -f "$dest" ] && files_equal "$src" "$dest"; then
            echo "     ⏭ Skipping $rel_norm (unchanged)"
            continue
        fi

        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
        echo "     ✅ $rel_norm"
    done
}

echo "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet "$REPO" "$TMP"

# Sync top-level allow-listed folders
for folder in "${SYNC_FOLDERS[@]}"; do
    src="$TMP/$folder"
    dest="./$folder"
    [ -d "$src" ] || continue
    echo "  → $folder/"
    mkdir -p "$dest"
    sync_folder "$src" "$dest" "$folder"
done

rm -rf "$TMP"

echo "✅ Sync complete."