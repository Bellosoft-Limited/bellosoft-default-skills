#!/bin/bash
set -e

REPO="https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
TMP=$(mktemp -d)

PROTECTED_FILES=("config.yaml" "config.yml" ".env")

files_equal() {
    local a=$(tr -d '\r' < "$1" | md5sum)
    local b=$(tr -d '\r' < "$2" | md5sum)
    [ "$a" = "$b" ]
}

echo "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet "$REPO" "$TMP"

for dir in "$TMP"/*/ "$TMP"/.*/; do
  name=$(basename "$dir")
  [[ "$name" == ".git" || "$name" == "." || "$name" == ".." ]] && continue
  [ ! -d "$dir" ] && continue
  echo "  → Copying $name/"
  mkdir -p "./$name"

  find "$dir" -type f | while read -r src; do
    rel="${src#$dir}"
    dest="./$name/$rel"
    filename=$(basename "$rel")

    if [[ " ${PROTECTED_FILES[@]} " =~ " ${filename} " ]] && [ -f "$dest" ]; then
      echo "     ⏭ Skipping $name/$rel (protected)"
      continue
    fi

    if [ -f "$dest" ] && files_equal "$src" "$dest"; then
      echo "     ⏭ Skipping $name/$rel (unchanged)"
      continue
    fi

    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo "     ✅ $name/$rel"
  done
done

rm -rf "$TMP"

echo "✅ Sync complete."