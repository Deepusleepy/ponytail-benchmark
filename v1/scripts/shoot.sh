#!/usr/bin/env bash
# Screenshot frontend builds with headless Chrome.
set -u
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
ROOT="."
OUT="$ROOT/screenshots"
mkdir -p "$OUT"

shot () {
  local html="$1" png="$2" w="$3" h="$4"
  if [ -f "$html" ]; then
    # convert /c/... to C:/... file URL
    local winpath
    winpath=$(echo "$html" | sed -E 's#^/c/#C:/#')
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
      --screenshot="$png" --window-size=${w},${h} "file:///${winpath}" >/dev/null 2>&1
    if [ -f "$png" ]; then echo "OK  $png"; else echo "FAIL $png"; fi
  else
    echo "MISSING $html"
  fi
}

for tid in task-04 task-05 task-06; do
  for arm in A B; do
    shot "$ROOT/builds/$tid/$arm/index.html" "$OUT/${tid}-${arm}-desktop.png" 1280 900
  done
done
# mobile responsiveness shots for the pricing page
for arm in A B; do
  shot "$ROOT/builds/task-04/$arm/index.html" "$OUT/task-04-${arm}-mobile.png" 420 900
done
echo "--- screenshots ---"
ls -1 "$OUT" 2>/dev/null
