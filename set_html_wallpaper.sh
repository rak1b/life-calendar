#!/bin/bash
# Convert `lifecalendar.html` → PNG and set it as wallpaper on Linux Mint.
#
# Why this exists:
# - You use it in crontab (@reboot / daily) to refresh your wallpaper on this PC.
# - Uses headless Chromium/Chrome to render the HTML exactly like the API does.
#
# Usage:
#   ./set_html_wallpaper.sh
#
# Optional env vars:
#   WIDTH=1920 HEIGHT=1080 OUTPUT=/path/to/out.png ./set_html_wallpaper.sh
#
# Notes:
# - Requires a Chromium/Chrome browser available on PATH.
# - Requires `Pillow` to fix the occasional bottom strip (optional but recommended).

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="${BASE_DIR}/lifecalendar.html"

WIDTH="${WIDTH:-1920}"
HEIGHT="${HEIGHT:-1080}"
OUTPUT="${OUTPUT:-${BASE_DIR}/lifecalendar_wallpaper.png}"

if [[ ! -f "$HTML_FILE" ]]; then
  echo "Error: HTML file not found: $HTML_FILE" >&2
  exit 1
fi

# Find a browser
if command -v chromium >/dev/null 2>&1; then
  BROWSER="chromium"
elif command -v google-chrome >/dev/null 2>&1; then
  BROWSER="google-chrome"
elif command -v chromium-browser >/dev/null 2>&1; then
  BROWSER="chromium-browser"
elif command -v chrome >/dev/null 2>&1; then
  BROWSER="chrome"
else
  echo "Error: No Chromium/Chrome found on PATH." >&2
  echo "Install one of: chromium, chromium-browser, google-chrome" >&2
  exit 1
fi

echo "Rendering $HTML_FILE → $OUTPUT (${WIDTH}x${HEIGHT}) using $BROWSER"

# Render HTML → PNG
"$BROWSER" \
  --headless \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-software-rasterizer \
  --hide-scrollbars \
  --disable-web-security \
  --disable-features=VizDisplayCompositor \
  --window-size="${WIDTH},${HEIGHT}" \
  --screenshot="${OUTPUT}" \
  --virtual-time-budget=3000 \
  "file://${HTML_FILE}" >/dev/null 2>&1 || true

if [[ ! -f "$OUTPUT" ]]; then
  echo "Error: Failed to generate wallpaper image at: $OUTPUT" >&2
  exit 1
fi

# Fix any solid color strip at bottom (optional)
python3 - <<'PY' || true
import os
from PIL import Image

output = os.environ.get("OUTPUT")
if not output or not os.path.exists(output):
    raise SystemExit(0)

img = Image.open(output)
width, height = img.size

def is_solid_row(im, y):
    first_pixel = im.getpixel((width // 2, y))
    # pure white or pure black tends to be the issue
    if first_pixel in ((255, 255, 255), (0, 0, 0)):
        return True
    for x in range(0, width, 50):
        if im.getpixel((x, y)) != first_pixel:
            return False
    return True

strip_start = height
for y in range(height - 1, max(0, height - 250), -1):
    if is_solid_row(img, y):
        strip_start = y
    else:
        break

if strip_start < height:
    good_row = max(0, strip_start - 1)
    for y in range(strip_start, height):
        for x in range(width):
            img.putpixel((x, y), img.getpixel((x, good_row)))
    img.save(output)
PY

# Set wallpaper (Mint / Cinnamon default)
desktop_env="$(echo "${XDG_CURRENT_DESKTOP:-}" | tr '[:upper:]' '[:lower:]')"

if [[ "$desktop_env" == *"cinnamon"* ]]; then
  gsettings set org.cinnamon.desktop.background picture-uri "file://${OUTPUT}"
  gsettings set org.cinnamon.desktop.background picture-options "scaled"
elif [[ "$desktop_env" == *"mate"* ]]; then
  gsettings set org.mate.background picture-filename "${OUTPUT}"
elif [[ "$desktop_env" == *"xfce"* ]]; then
  xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image -s "${OUTPUT}"
else
  # GNOME fallback
  gsettings set org.gnome.desktop.background picture-uri "file://${OUTPUT}" || true
fi

echo "Wallpaper set: ${OUTPUT}"

