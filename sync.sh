#!/bin/bash
set -e

REPO="https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
TMP=$(mktemp -d)

# Files that should never be overwritten if they already exist
PROTECTED_FILES=("config.yaml" "config.yml" ".env")

echo "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet "$REPO" "$TMP"

for dir in "$TMP"/*/; do
  name=$(basename "$dir")
  [ "$name" = ".git" ] && continue
  echo "  → Copying $name/"
  mkdir -p "./$name"

  find "$dir" -type f | while read -r src; do
    rel="${src#$dir}"
    dest="./$name/$rel"
    filename=$(basename "$rel")

    # Skip protected files if they already exist
    if [[ " ${PROTECTED_FILES[@]} " =~ " ${filename} " ]] && [ -f "$dest" ]; then
      echo "     ⏭ Skipping $name/$rel (protected, already exists)"
      continue
    fi

    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
  done
done

rm -rf "$TMP"

echo "✅ Sync complete."