#!/bin/bash
set -e

REPO="https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
TMP=$(mktemp -d)

echo "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet "$REPO" "$TMP"

for dir in "$TMP"/*/; do
  name=$(basename "$dir")
  [ "$name" = ".git" ] && continue
  echo "  → Copying $name/"
  cp -r "$dir" "./$name"
done

rm -rf "$TMP"

echo "✅ Sync complete."