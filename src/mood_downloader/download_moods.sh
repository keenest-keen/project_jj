#!/usr/bin/env bash
set -euo pipefail

MOODS=(
  angry blah confused cynical devious drunk energetic good high
  okay sad shock sick smile thinking tired wink
)

BASE_URL="https://l-stat.livejournal.net/img/mood/classic"
OUT_DIR="mood"
mkdir -p "$OUT_DIR"

UA="Mozilla/5.0 (mood-downloader)"

for m in "${MOODS[@]}"; do
  url="$BASE_URL/$m.gif"
  out="$OUT_DIR/$m.gif"
  printf '[%s] %s\n' "$m" "$url"
  if curl -fsSL --compressed --max-time 15 -A "$UA" -o "$out" "$url"; then
    printf '  ✓ %s\n' "$(du -h "$out" | cut -f1)"
  else
    printf '  ✗ не удалось скачать %s\n' "$url" >&2
    rm -f "$out"
  fi
done