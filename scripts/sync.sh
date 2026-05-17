#!/bin/bash

REPO="https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
TMP=$(mktemp -d)
CWD=$(cygpath -u "${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" 2>/dev/null || echo "${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}")
FILELIST=$(mktemp)
LINKLIST=$(mktemp)

SYNC_FOLDERS=(
    ".github"
    ".agents"
    ".claude"
    ".kilo"
    "_bmad"
    ".vscode"
)

PROTECTED_PREFIXES=(
    ".github/skills/bmad-tea"
    ".github/skills/reports"
    ".github/CODEOWNERS"
)

files_equal() {
    cmp -s <(tr -d '\r' < "$1") <(tr -d '\r' < "$2")
    return $?
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

sync_symlinks() {
    local src_base="$1"
    local dest_base="$2"
    local log_label="$3"
    [ -d "$src_base" ] || return 0

    find "$src_base" -maxdepth 1 -type l > "$LINKLIST"

    while IFS= read -r src; do
        rel="${src#$src_base/}"
        dest="$dest_base/$rel"
        rel_norm="$log_label/$rel"
        target=$(readlink "$src")

        if [ -e "$dest" ] || [ -L "$dest" ]; then
            echo "     ⏭ Skipping symlink $rel_norm (already exists)"
            continue
        fi

        mkdir -p "$(dirname "$dest")"
        ln -s "$target" "$dest"
        echo "     🔗 $rel_norm -> $target"
    done < "$LINKLIST"
}

sync_folder() {
    local src_base="$1"
    local dest_base="$2"
    local log_label="$3"
    [ -d "$src_base" ] || return 0

    local symlinks=()
    find "$src_base" -maxdepth 1 -type l > "$LINKLIST"
    while IFS= read -r s; do
        symlinks+=("$(basename "$s")")
    done < "$LINKLIST"

    find "$src_base" -type f > "$FILELIST"

    while IFS= read -r src; do
        rel="${src#$src_base/}"
        local top="${rel%%/*}"
        local skip=false
        for s in "${symlinks[@]}"; do
            [[ "$top" == "$s" ]] && skip=true && break
        done
        $skip && continue

        dest="$dest_base/$rel"
        rel_norm="$log_label/$rel"

        if is_protected "$rel_norm"; then
            echo "     ⏭ Skipping $rel_norm (protected)"
            continue
        fi

        local equal=false
        if [ -f "$dest" ]; then
            files_equal "$src" "$dest" && equal=true
        fi

        if $equal; then
            echo "     ⏭ Skipping $rel_norm (unchanged)"
            continue
        fi

        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
        echo "     ✅ $rel_norm"
    done < "$FILELIST"
}

echo "🔄 Syncing Bellosoft project defaults into: $CWD"

git clone --depth=1 --quiet "$REPO" "$TMP" || { echo "❌ git clone failed"; exit 1; }

for folder in "${SYNC_FOLDERS[@]}"; do
    src="$TMP/$folder"
    dest="$CWD/$folder"
    { [ -d "$src" ] || [ -L "$src" ]; } || continue
    echo "  → $folder/"
    sync_symlinks "$src" "$dest" "$folder"
    sync_folder "$src" "$dest" "$folder"
done

rm -f "$FILELIST" "$LINKLIST"
rm -rf "$TMP"

echo "✅ Sync complete."